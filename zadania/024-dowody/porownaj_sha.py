"""Druga droga sha256: wynik narzędzia (plan --sprawdz) vs coreutils sha256sum (ścieżka → suma)."""

import ast
import os
import sys

plan_txt, sums_txt = sys.argv[1], sys.argv[2]

z_narzedzia = {}
katalog = stara = None
for linia in open(plan_txt, encoding="utf-8"):
    if linia.startswith("["):
        katalog = linia.split("] ", 1)[1].strip()
    elif linia.startswith("  stara (bajty):"):
        stara = ast.literal_eval(linia.split(":", 1)[1].strip())
    elif linia.startswith("  sha256 treści:"):
        z_narzedzia[os.path.join(os.fsencode(katalog), stara)] = linia.split(":", 1)[1].strip()

z_coreutils = {}
for linia in open(sums_txt, "rb"):
    suma, sciezka = linia.rstrip(b"\n").split(b"  ", 1)
    z_coreutils[sciezka] = suma.decode()

wspolne = set(z_narzedzia) & set(z_coreutils)
rowne = sum(z_narzedzia[p] == z_coreutils[p] for p in wspolne)
print(
    f"narzędzie: {len(z_narzedzia)} plików; sha256sum: {len(z_coreutils)}; wspólne ścieżki: {len(wspolne)}"
)
print(f"sumy równe: {rowne}/{len(wspolne)}")
print(
    f"tylko w narzędziu: {len(set(z_narzedzia) - set(z_coreutils))}; tylko w sha256sum: {len(set(z_coreutils) - set(z_narzedzia))}"
)
