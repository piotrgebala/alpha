"""LH0 krok 0a(ii): czy likwidacje da się rozpoznać w publicznym `trades` po adresach stron?

Wejście: plik z `sonda_trades.py` (surowe `WsTrade[]`). Dla wybranych monet i okna czasu:
1. zbiera adresy STRONY AKTYWNEJ (taker) każdej transakcji — przy założeniu `side` = strona agresora
   (`B` -> taker = users[0] kupujący, `A` -> taker = users[1] sprzedający); założenie sprawdzane niżej
   polem `crossed` w wypełnieniach tego adresu;
2. dla każdego adresu odpytuje `userFillsByTime` (Info API, waga 20 + 1 na 20 zwróconych pozycji wg dokumentacji
   „Rate limits”), z budżetem wagi na minutę;
3. zlicza wypełnienia z polem `liquidation` (strona likwidowana: `liquidatedUser` == adres albo `dir` zaczyna się
   od „Liquidated”/„Market Order Liquidation”) i łączy je z transakcjami po (coin, tid) — żeby sprawdzić, czy
   transakcja likwidacyjna ma w `trades` jakąś cechę odróżniającą.

Wyjście: stdout (liczniki) + lista likwidacji JSONL (--liq-out). Bez cen po likwidacji, bez żadnego odczytu E1.
"""

import argparse
import collections
import json
import math
import time
import urllib.request

INFO_URL = "https://api.hyperliquid.xyz/info"


def info(body):
    req = urllib.request.Request(
        INFO_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read(50_000_000))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    raise RuntimeError("429 pięć razy")


def load_trades(path, coins, t0, t1):
    trades = {}
    for line in open(path):
        rec = json.loads(line)
        if rec["ch"] != "trades":
            continue
        for t in rec["data"]:
            if (coins and t["coin"] not in coins) or not (t0 <= t["time"] < t1):
                continue
            trades[(t["coin"], t["tid"])] = t
    return trades


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--coins", default="BTC,ETH,SOL", help="przecinki; pusty = wszystkie")
    ap.add_argument("--t0", type=int, required=True, help="ms UTC")
    ap.add_argument("--t1", type=int, required=True, help="ms UTC")
    ap.add_argument("--weight-per-min", type=int, default=900)
    ap.add_argument("--liq-out", required=True)
    ap.add_argument("--max-users", type=int, default=0)
    a = ap.parse_args()
    coins = set(filter(None, a.coins.split(",")))
    trades = load_trades(a.trades, coins, a.t0, a.t1)
    per_coin = collections.Counter(c for c, _ in trades)
    print(f"transakcji w oknie: {len(trades)} per moneta: {dict(per_coin)}")
    takers = collections.Counter()
    for t in trades.values():
        takers[t["users"][0] if t["side"] == "B" else t["users"][1]] += 1
    all_users = {u for t in trades.values() for u in t["users"]}
    print(f"unikalnych adresow: wszystkich stron={len(all_users)} takerow={len(takers)}")
    users = [u for u, _ in takers.most_common()]
    if a.max_users:
        users = users[: a.max_users]
    weight_used, window_start = 0, time.time()
    total_weight = 0
    crossed_ok = crossed_bad = 0
    truncated = 0
    liqs = []
    t_start = time.time()
    for i, u in enumerate(users):
        if weight_used >= a.weight_per_min:
            sleep = 60 - (time.time() - window_start)
            if sleep > 0:
                time.sleep(sleep)
            weight_used, window_start = 0, time.time()
        fills = info({"type": "userFillsByTime", "user": u, "startTime": a.t0, "endTime": a.t1 - 1})
        w = 20 + math.ceil(len(fills) / 20)
        weight_used += w
        total_weight += w
        if len(fills) >= 2000:
            truncated += 1
        for f in fills:
            key = (f["coin"], f["tid"])
            if key in trades:
                t = trades[key]
                is_taker_by_side = u == (t["users"][0] if t["side"] == "B" else t["users"][1])
                if is_taker_by_side and f.get("crossed") is True:
                    crossed_ok += 1
                elif is_taker_by_side:
                    crossed_bad += 1
            lq = f.get("liquidation")
            if lq and (
                lq.get("liquidatedUser") in (None, u)
                or str(f.get("dir", "")).startswith("Liquidated")
            ):
                t = trades.get(key)
                liqs.append({"user": u, "fill": f, "trade": t})
        if i % 200 == 199:
            print(
                f"  {i + 1}/{len(users)} adresow, waga={total_weight}, likwidacji={len(liqs)}, {time.time() - t_start:.0f}s",
                flush=True,
            )
    print(
        f"odpytano adresow={len(users)} waga razem={total_weight} czas={time.time() - t_start:.0f}s obciete(2000)={truncated}"
    )
    print(
        f"sprawdzenie strony agresora: taker wg side i crossed=True: {crossed_ok}, taker wg side ale crossed!=True: {crossed_bad}"
    )
    with open(a.liq_out, "w") as out:
        for r in liqs:
            out.write(json.dumps(r) + "\n")
    in_coins = [r for r in liqs if not coins or r["fill"]["coin"] in coins]
    print(
        f"wypelnien likwidacyjnych (strona likwidowana) w monetach okna: {len(in_coins)}; wszystkich: {len(liqs)}"
    )
    by = collections.Counter(
        (r["fill"]["coin"], r["fill"]["liquidation"].get("method"), r["fill"].get("dir"))
        for r in in_coins
    )
    for k, v in sorted(by.items()):
        print("  ", k, v)
    # likwidacja = jedno zlecenie (user, oid) -> wiele wypelnien
    orders = collections.Counter((r["fill"]["coin"], r["user"], r["fill"]["oid"]) for r in in_coins)
    print(f"zlecen likwidacyjnych (user, oid) w monetach okna: {len(orders)}")
    matched = [r for r in in_coins if r["trade"]]
    print(f"wypelnien dopasowanych do transakcji z trades: {len(matched)}")
    for r in matched[:5]:
        print("   trade:", json.dumps(r["trade"]))
        print("   fill :", json.dumps(r["fill"])[:500])


if __name__ == "__main__":
    main()
