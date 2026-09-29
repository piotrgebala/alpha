"""LH0 krok 0a(ii) i 0c: skala z nasłuchu `trades` (bez sieci, tylko plik z `sonda_trades.py`).

- ile unikalnych adresów strony aktywnej (taker) na minutę i w całym oknie — to liczba adresów, które droga (ii)
  musiałaby sprawdzać przez `userFillsByTime`, żeby nie zgubić żadnej likwidacji rynkowej;
- ile transakcji i bajtów surowego `trades` na minutę (budżet dysku, gdyby zapisywać cały strumień).

Uruchomienie: python sonda_skala.py <plik.jsonl> <t0_ms> <t1_ms>
"""

import collections
import json
import sys


def main():
    path, t0, t1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    minutes = (t1 - t0) / 60000
    takers_per_min = collections.defaultdict(set)
    takers, users = set(), set()
    n_trades = 0
    bytes_trades = 0
    for line in open(path):
        rec = json.loads(line)
        if rec["ch"] != "trades":
            continue
        keep = [t for t in rec["data"] if t0 <= t["time"] < t1]
        if not keep:
            continue
        bytes_trades += len(json.dumps(keep, separators=(",", ":")))
        for t in keep:
            n_trades += 1
            tk = t["users"][0] if t["side"] == "B" else t["users"][1]
            takers.add(tk)
            users.update(t["users"])
            takers_per_min[(t["time"] - t0) // 60000].add(tk)
    per_min = sorted(len(v) for v in takers_per_min.values())
    print(f"okno {minutes:.0f} min: transakcji={n_trades} ({n_trades / minutes:.0f}/min)")
    print(f"unikalnych adresow: wszystkich stron={len(users)} takerow={len(takers)}")
    print(
        f"unikalnych takerow na minute: mediana={per_min[len(per_min) // 2]} min={per_min[0]} max={per_min[-1]}"
    )
    print(
        f"surowe trades (JSON bez spacji): {bytes_trades / 1e6:.1f} MB w oknie -> {bytes_trades / minutes * 1440 / 1e6:.0f} MB/dobe"
    )


if __name__ == "__main__":
    main()
