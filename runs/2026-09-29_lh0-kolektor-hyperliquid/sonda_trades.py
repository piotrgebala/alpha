"""LH0 krok 0a(ii): nasłuch publicznego `trades` (wszystkie perpetuale głównej giełdy Hyperliquid) + `userFills`
adresów podrzędnych HLP. Sonda jednorazowa, bez klucza; surowe wiadomości do pliku POZA repo (argument --out),
liczniki na stdout.

Źródła (dokumentacja Hyperliquid, pobrana 2026-09-29):
- WebSocket -> Subscriptions: `{"type": "trades", "coin": ...}` -> `WsTrade[]` z polem `users: [buyer, seller]`;
  `{"type": "userFills", "user": ...}` -> `WsFill` z opcjonalnym `liquidation: FillLiquidation`.
- Rate limits: maks. 1000 subskrypcji, maks. 10 unikalnych użytkowników w subskrypcjach per-user,
  maks. 2000 wiadomości wysłanych na minutę.

Uruchomienie: python sonda_trades.py --seconds 2700 --out <plik.jsonl>
"""

import argparse
import asyncio
import collections
import datetime as dt
import json
import time
import urllib.request

WS_URL = "wss://api.hyperliquid.xyz/ws"
INFO_URL = "https://api.hyperliquid.xyz/info"
HLP_DOC = "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"


def info(body):
    req = urllib.request.Request(
        INFO_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read(20_000_000))


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


async def run(seconds, out_path):
    import aiohttp

    meta = info({"type": "meta"})
    coins = [a["name"] for a in meta["universe"] if not a.get("isDelisted")]
    vd = info({"type": "vaultDetails", "vaultAddress": HLP_DOC})
    children = vd["relationship"]["data"]["childAddresses"][:9]
    print(
        f"start {now_iso()} monet={len(coins)} adresy HLP (userFills)={len(children)}", flush=True
    )
    cnt_trades = collections.Counter()
    cnt_liq_userfills = collections.Counter()
    sub_ok = sub_err = msgs = 0
    t0 = time.time()
    first_trade_ms = last_trade_ms = None
    with open(out_path, "w") as out:
        async with aiohttp.ClientSession() as s:
            async with s.ws_connect(WS_URL, heartbeat=None, max_msg_size=64 * 2**20) as ws:
                for i, c in enumerate(coins):
                    await ws.send_str(
                        json.dumps(
                            {"method": "subscribe", "subscription": {"type": "trades", "coin": c}}
                        )
                    )
                    if i % 50 == 49:
                        await asyncio.sleep(2)
                for u in children:
                    await ws.send_str(
                        json.dumps(
                            {
                                "method": "subscribe",
                                "subscription": {"type": "userFills", "user": u},
                            }
                        )
                    )
                last_ping = time.time()
                while time.time() - t0 < seconds:
                    if time.time() - last_ping > 30:
                        await ws.send_str(json.dumps({"method": "ping"}))
                        last_ping = time.time()
                    try:
                        m = await ws.receive(timeout=5)
                    except asyncio.TimeoutError:
                        continue
                    if m.type != aiohttp.WSMsgType.TEXT:
                        print(f"{now_iso()} koniec strumienia: {m.type}", flush=True)
                        break
                    msgs += 1
                    d = json.loads(m.data)
                    ch = d.get("channel")
                    if ch == "subscriptionResponse":
                        sub_ok += 1
                        continue
                    if ch == "error":
                        sub_err += 1
                        print("error:", m.data[:300], flush=True)
                        continue
                    if ch == "trades":
                        for t in d["data"]:
                            cnt_trades[t["coin"]] += 1
                            first_trade_ms = first_trade_ms or t["time"]
                            last_trade_ms = t["time"]
                        out.write(
                            json.dumps(
                                {"rcv": int(time.time() * 1000), "ch": ch, "data": d["data"]}
                            )
                            + "\n"
                        )
                    elif ch == "userFills":
                        data = d["data"]
                        if data.get("isSnapshot"):
                            continue
                        for f in data.get("fills", []):
                            if f.get("liquidation"):
                                cnt_liq_userfills[
                                    (data["user"], f["liquidation"].get("method"))
                                ] += 1
                        out.write(
                            json.dumps({"rcv": int(time.time() * 1000), "ch": ch, "data": data})
                            + "\n"
                        )
                    if msgs % 20000 == 0:
                        print(
                            f"{now_iso()} wiadomosci={msgs} trades={sum(cnt_trades.values())}",
                            flush=True,
                        )
    print(
        f"koniec {now_iso()} czas={time.time() - t0:.0f}s wiadomosci={msgs} subskrypcje ok={sub_ok} bledy={sub_err}"
    )
    print(f"okno transakcji (czas zrodla): {first_trade_ms} .. {last_trade_ms}")
    print(f"transakcji razem={sum(cnt_trades.values())} monet z transakcjami={len(cnt_trades)}")
    print("top 10 monet:", cnt_trades.most_common(10))
    print("userFills HLP z polem liquidation (adres, metoda):", dict(cnt_liq_userfills))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=2700)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    asyncio.run(run(a.seconds, a.out))


if __name__ == "__main__":
    main()
