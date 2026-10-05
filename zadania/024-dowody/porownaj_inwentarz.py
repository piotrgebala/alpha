"""Inwentarz sha256sum przed i po --wykonaj na kopii: te same treści pod oczekiwanymi nazwami."""

import sys


def wczytaj(sciezka, prefiks=b""):
    out = {}
    for linia in open(sciezka, "rb"):
        suma, p = linia.rstrip(b"\n").split(b"  ", 1)
        if prefiks and p.startswith(prefiks):
            p = p[len(prefiks) :]
        out[p] = suma
    return out


przed = wczytaj(sys.argv[1])
po = wczytaj(sys.argv[2], prefiks=b"data/raw/")


def oczekiwana(p):
    katalog, nazwa = p.rsplit(b"/", 1)
    if nazwa.isascii():
        return p
    return katalog + b"/" + nazwa.decode("utf-8").encode("cp866")  # niezależne odwrócenie


mapa = {p: oczekiwana(p) for p in przed}
zmienione = sum(p != q for p, q in mapa.items())
brak = [q for q in mapa.values() if q not in po]
rozne = [p for p, q in mapa.items() if q in po and po[q] != przed[p]]
nadmiar = set(po) - set(mapa.values())
nieascii_po = sorted(p.rsplit(b"/", 1)[1].decode("utf-8") for p in po if not p.isascii())
print(f"plików przed: {len(przed)}; po: {len(po)}; nazw zmienionych wg odwrócenia: {zmienione}")
print(
    f"brakujące po: {len(brak)}; inna treść (sha256): {len(rozne)}; nadmiarowe po: {len(nadmiar)}"
)
print(f"sha256 równe dla wszystkich {len(przed) - len(brak) - len(rozne)}/{len(przed)} plików")
print(f"nazwy spoza ASCII po naprawie ({len(nieascii_po)}): {sorted(set(nieascii_po))}")
