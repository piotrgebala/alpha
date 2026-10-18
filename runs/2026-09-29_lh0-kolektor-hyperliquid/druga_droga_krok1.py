"""Druga droga (bramka 16a) dla LH0 krok 1A: niezależny kod, bez importu measure_hl_weights."""
import json
import os
import statistics as st
D = os.path.expanduser("~/likwidacje_hl/pomiar_krok1/")
# 1) M1 S1: unikalne strony aktywne BTC na pełną minutę × w̄ (N=1, adresy z BTC)
ws = []; liq = []
for line in open(D + "zapytania.jsonl"):
    q = json.loads(line)
    if q.get("kind") != "probka" or q.get("status") != "ok":
        continue
    if q["N"] == 1 and q["taker"].get("BTC", [0])[0] > 0:
        ws.append(q["weight"])
    for lq in q.get("liqs", []):
        liq.append((q["addr"], lq["oid"], lq["coin"], q["N"], q["taker"]))
wbar = sum(ws) / len(ws)
cnt = []
for line in open(D + "minuty.jsonl"):
    m = json.loads(line)
    if m["ok"]:
        cnt.append(len(m["coins"]["BTC"]["takers"]))
cost = sorted(c * wbar for c in cnt)
p95 = cost[int(round(0.95 * (len(cost) - 1)))]
print(f"M1 S1: minut={len(cnt)} w̄={wbar:.2f} (n={len(ws)}) średnia={st.mean(cost):.0f} mediana={st.median(cost):.0f} p95≈{p95:.0f}")
# 2) S3 F1: udział zgubionych, per rekord i po deduplikacji (adres, oid)
def f1(t): return any(t.get(c, [0, 0, 0])[1] > 0 for c in ("BTC", "ETH", "SOL"))
lost = sum(1 for a, o, c, n, t in liq if not f1(t))
print(f"S3 F1 per rekord: likwidacji={len(liq)} zgubionych={lost} udział={100*lost/len(liq):.1f} %")
uniq = {}
for a, o, c, n, t in liq:
    if n == 1 or (a, o) not in uniq:  # preferuj okno 1-min
        uniq[(a, o)] = t
lu = sum(1 for t in uniq.values() if not f1(t))
from scipy.stats import beta
print(f"S3 F1 unikalne (adres,oid): {len(uniq)} zgubionych={lu} udział={100*lu/len(uniq):.1f} % CP95 górna={100*beta.ppf(0.95, lu+1, len(uniq)-lu):.1f} %")
print("rozkład N rekordów z likwidacją:", {n: sum(1 for x in liq if x[3] == n) for n in (1, 5, 15, 60)})
