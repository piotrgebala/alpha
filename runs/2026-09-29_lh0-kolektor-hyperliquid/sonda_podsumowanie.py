"""LH0 krok 0a: podsumowanie likwidacji znalezionych przez `sonda_weryfikacja.py` + druga droga liczenia.

Droga 1 (z wypełnień `userFillsByTime`): per moneta — wypełnienia, zlecenia (user, oid), unikalni zlikwidowani,
kierunek zlikwidowanej pozycji z `dir` („Close Short” = zlikwidowany short) i z `side` (B = kupno = zamknięcie shorta).
Droga 2 (niezależnie od wypełnień, z publicznego `trades`): transakcje, w których strona aktywna jest jednym
z zlikwidowanych adresów w tej samej milisekundzie i z tym samym `hash` — liczba musi się zgadzać z drogą 1.

Uruchomienie: python sonda_podsumowanie.py <liq.jsonl> <trades.jsonl> <t0_ms> <t1_ms>
"""

import collections
import json
import sys


def main():
    liq_path, trades_path, t0, t1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    rows = [json.loads(line) for line in open(liq_path)]
    rows = [r for r in rows if t0 <= r["fill"]["time"] < t1 and r["fill"]["coin"] in ("BTC", "ETH", "SOL")]
    minutes = (t1 - t0) / 60000
    print(f"droga 1 (userFillsByTime), okno {minutes:.0f} min:")
    for coin in ("BTC", "ETH", "SOL"):
        sel = [r for r in rows if r["fill"]["coin"] == coin]
        orders = {(r["user"], r["fill"]["oid"]) for r in sel}
        users = {r["user"] for r in sel}
        dirs = collections.Counter(r["fill"]["dir"] for r in sel)
        sides = collections.Counter(r["fill"]["side"] for r in sel)
        methods = collections.Counter(r["fill"]["liquidation"]["method"] for r in sel)
        ntl = sum(float(r["fill"]["sz"]) * float(r["fill"]["px"]) for r in sel)
        print(
            f"  {coin}: wypelnien={len(sel)} zlecen(user,oid)={len(orders)} zlikwidowanych adresow={len(users)}"
            f" dir={dict(dirs)} side={dict(sides)} metoda={dict(methods)} nominal~{ntl:,.0f} USD"
        )
    orders_all = {(r["user"], r["fill"]["oid"]) for r in rows}
    print(f"  razem zlecen={len(orders_all)} ({len(orders_all) / minutes:.2f}/min)")
    # droga 2
    keys = {(r["fill"]["coin"], r["user"], r["fill"]["time"], r["fill"]["hash"]) for r in rows}
    n2 = collections.Counter()
    for line in open(trades_path):
        rec = json.loads(line)
        if rec["ch"] != "trades":
            continue
        for t in rec["data"]:
            if not (t0 <= t["time"] < t1):
                continue
            tk = t["users"][0] if t["side"] == "B" else t["users"][1]
            if (t["coin"], tk, t["time"], t["hash"]) in keys:
                n2[t["coin"]] += 1
    print(f"droga 2 (publiczne trades, taker = zlikwidowany, ten sam czas i hash): {dict(n2)} razem={sum(n2.values())}")


if __name__ == "__main__":
    main()
