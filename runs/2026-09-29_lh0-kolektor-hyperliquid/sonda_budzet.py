"""LH0 krok 0b i 0c: oszacowania, bez budowy.

0b: ile adresów ma pozycje > 100 tys. USD i jak często dałoby się odpytać `clearinghouseState`.
    Próba: losowe adresy spośród stron transakcji z nasłuchu (`sonda_trades.py`), `clearinghouseState`
    (waga 2 wg dokumentacji „Rate limits”) -> udział adresów z sumą |positionValue| > 100 tys. USD.
    Ograniczenie: widzimy tylko adresy, które handlowały w oknie nasłuchu.
0c: rozmiar zrzutu `metaAndAssetCtxs` (surowo i gzip) -> MB/dobę przy zrzucie co 60 s.

Uruchomienie: python sonda_budzet.py --trades <plik.jsonl> --sample 300
"""

import argparse
import gzip
import json
import random
import time
import urllib.request

INFO_URL = "https://api.hyperliquid.xyz/info"


def info(body):
    req = urllib.request.Request(
        INFO_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read(50_000_000))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20260929)
    a = ap.parse_args()

    # 0c: metaAndAssetCtxs
    snaps = []
    for i in range(3):
        snaps.append(json.dumps(info({"type": "metaAndAssetCtxs"}), separators=(",", ":")))
        if i < 2:
            time.sleep(30)
    raw = [len(s.encode()) for s in snaps]
    gz_all = len(gzip.compress(("\n".join(snaps) + "\n").encode(), 6))
    gz_one = len(gzip.compress((snaps[0] + "\n").encode(), 6))
    print(
        f"0c metaAndAssetCtxs: surowo bajtow/zrzut={raw} gzip jeden={gz_one} gzip trzy razem={gz_all}"
    )
    per_snap_gz = gz_all / 3
    print(
        f"0c MB/dobe (1440 zrzutow): surowo={sum(raw) / 3 * 1440 / 1e6:.1f}"
        f" gzip(ostroznie: jak jeden zrzut)={gz_one * 1440 / 1e6:.1f} gzip(srednia z 3)={per_snap_gz * 1440 / 1e6:.1f}"
    )

    # 0b: adresy
    users, first, last = set(), None, None
    for line in open(a.trades):
        rec = json.loads(line)
        if rec["ch"] != "trades":
            continue
        for t in rec["data"]:
            users.update(t["users"])
            first = t["time"] if first is None else min(first, t["time"])
            last = t["time"] if last is None else max(last, t["time"])
    print(
        f"0b unikalnych adresow stron transakcji w nasluchu: {len(users)} (okno {(last - first) / 60000:.1f} min)"
    )
    rnd = random.Random(a.seed)
    sample = rnd.sample(sorted(users), min(a.sample, len(users)))
    big, with_pos, errors = 0, 0, 0
    npos = []
    t0 = time.time()
    for i, u in enumerate(sample):
        if i and i % 250 == 0:  # 250 * waga 2 = 500 / min, pod limitem 1200
            time.sleep(max(0, 60 - (time.time() - t0)))
            t0 = time.time()
        try:
            st = info({"type": "clearinghouseState", "user": u})
        except Exception as e:  # noqa: BLE001 — sonda: liczymy błędy, nie przerywamy
            errors += 1
            print("blad:", type(e).__name__, str(e)[:100])
            continue
        pos = st.get("assetPositions", [])
        val = sum(abs(float(p["position"]["positionValue"])) for p in pos)
        if pos:
            with_pos += 1
            npos.append(len(pos))
        if val > 100_000:
            big += 1
    n = len(sample) - errors
    share = big / n if n else float("nan")
    print(
        f"0b proba={n} (bledy {errors}): z pozycjami={with_pos} z pozycjami > 100 tys. USD={big} udzial={share:.3f}"
    )
    print(
        f"0b szacunek adresow > 100 tys. USD wsrod {len(users)} adresow z nasluchu: ~{share * len(users):.0f}"
    )
    if npos:
        print(f"0b srednia liczba pozycji na adres z pozycjami: {sum(npos) / len(npos):.1f}")


if __name__ == "__main__":
    main()
