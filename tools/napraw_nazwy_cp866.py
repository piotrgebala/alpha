"""napraw_nazwy_cp866.py — zadanie 024: nazwy plików danych zniekształcone przez cp866.

Po co: runda LP1 (zadanie 017) znalazła na serwerze pliki koszyka z nazwą w złym kodowaniu, np.
`х╕БхоЙф║║чФЯUSDT_1d.parquet` zamiast `币安人生USDT_1d.parquet`. Moduły czytające koszyk biorą symbol
z nazwy pliku, więc dostają zniekształcony symbol, który nie łączy się z danymi o poprawnej nazwie.

Jak powstało zniekształcenie: bajty UTF-8 nazwy (币 = e5 b8 81) odczytano jako cp866 (e5 → „х”,
b8 → „╕”, 81 → „Б”) i zapisano z powrotem w UTF-8. Odwrócenie: `nazwa.decode("utf-8")
.encode("cp866").decode("utf-8")`. cp866 przypisuje każdemu z 256 bajtów inny znak, więc odwrócenie
jest jednoznaczne. Mimo to niczego nie zgadujemy: symbol z nowej nazwy musi wystąpić w danych
referencyjnych (`--symbole`: CSV albo parquet z kolumną `symbol`, np. `data/raw/listings/events.csv`).

    PYTHONUTF8=1 py tools/napraw_nazwy_cp866.py --sprawdz KATALOG [KATALOG ...] --symbole PLIK [PLIK ...]
    PYTHONUTF8=1 py tools/napraw_nazwy_cp866.py --wykonaj KATALOG [KATALOG ...] --symbole PLIK [PLIK ...]

`--sprawdz` niczego nie zmienia. Dla każdej nazwy spoza ASCII wypisuje: starą nazwę w bajtach, nową
nazwę, sha256 treści, czy plik o nowej nazwie już istnieje (i czy ma tę samą treść), gdzie
potwierdzono symbol i status:
    DO_ZMIANY        zniekształcenie cp866, symbol potwierdzony, nowej nazwy jeszcze nie ma;
    POPRAWNA         nazwa spoza ASCII, ale nie jest zniekształceniem (np. już naprawiona) — tylko
                     informacja;
    CEL_ISTNIEJE     plik o nowej nazwie już jest (duplikat) — blokuje;
    NIEPOTWIERDZONA  symbolu z nowej nazwy nie ma w danych referencyjnych — blokuje;
    NIE_UTF8         nazwa nie jest poprawnym UTF-8 (inne kodowanie, do ręcznego przeglądu) — blokuje;
    NIE_PLIK         to nie jest zwykły plik (katalog, dowiązanie) — blokuje.
`--wykonaj` zmienia WYŁĄCZNIE nazwy pozycji DO_ZMIANY, na zasadzie „wszystko albo nic”: przy
jakiejkolwiek pozycji blokującej niczego nie rusza. Treści nie zmienia, niczego nie usuwa ani nie
nadpisuje: nowa nazwa powstaje jako dowiązanie twarde (`os.link` odmawia, gdy cel istnieje), a stara
znika dopiero potem. Po każdej zmianie liczy sha256 pod nową nazwą i porównuje z planem. Błąd
w trakcie (np. cel pojawił się po planie) zatrzymuje przebieg; wypisane linie ZMIENIONO mówią, co
zrobiono, a ponowne `--sprawdz` pokazuje resztę. Przerwanie między dowiązaniem a usunięciem starej
nazwy zostawia dwie nazwy tej samej treści (CEL_ISTNIEJE, „ta sama treść”) — do ręcznego przeglądu.

Kody wyjścia: 0 — plan wykonalny albo zmiany wykonane; 3 — w planie są pozycje blokujące (nic nie
zmieniono); 1 — błąd (brak katalogu, zły plik referencyjny, przerwana zmiana nazwy); 2 — złe
argumenty (argparse). Katalogi skanowane płasko (bez podkatalogów). Skrypt jest neutralnym
reporterem: o wykonaniu decyduje orkiestrator po przeglądzie planu.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from dataclasses import dataclass, field

DO_ZMIANY = "DO_ZMIANY"
POPRAWNA = "POPRAWNA"
CEL_ISTNIEJE = "CEL_ISTNIEJE"
NIEPOTWIERDZONA = "NIEPOTWIERDZONA"
NIE_UTF8 = "NIE_UTF8"
NIE_PLIK = "NIE_PLIK"
BLOKUJACE = (CEL_ISTNIEJE, NIEPOTWIERDZONA, NIE_UTF8, NIE_PLIK)

KOD_OK, KOD_BLAD, KOD_BLOKADA = 0, 1, 3
SUFIKSY = ("_1d.parquet", "_funding.parquet")  # <SYMBOL>_1d / <SYMBOL>_funding (fetch_universe)
KOLUMNA_SYMBOLU = "symbol"


def odwroc_cp866(nazwa: bytes) -> bytes | None:
    """Oryginalne bajty nazwy, jeśli `nazwa` to UTF-8 zapisane po odczycie jako cp866; inaczej None.

    None dla nazw ASCII, dla nazw spoza UTF-8 i dla nazw, których nie da się odwrócić do poprawnego
    UTF-8 (np. już poprawne 币安人生 — takich znaków nie ma w cp866).
    """
    if nazwa.isascii():
        return None
    try:
        oryginal = nazwa.decode("utf-8").encode("cp866")
        oryginal.decode("utf-8")
    except UnicodeError:
        return None
    return oryginal if oryginal != nazwa else None


def symbol_z_nazwy(nazwa: str) -> str:
    """`币安人生USDT_1d.parquet` → `币安人生USDT`; nieznany format → część przed ostatnim „_” rdzenia."""
    for sufiks in SUFIKSY:
        if nazwa.endswith(sufiks):
            return nazwa[: -len(sufiks)]
    rdzen = nazwa.rsplit(".", 1)[0]
    return rdzen.rsplit("_", 1)[0]


def sha256_pliku(sciezka: bytes | str) -> str:
    h = hashlib.sha256()
    with open(sciezka, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def wczytaj_symbole(pliki: list[str]) -> dict[str, list[str]]:
    """Symbol → pliki referencyjne, w których występuje (CSV lub parquet z kolumną `symbol`)."""
    import pandas as pd

    zrodla: dict[str, list[str]] = {}
    for plik in pliki:
        if plik.lower().endswith(".parquet"):
            df = pd.read_parquet(plik)
        elif plik.lower().endswith(".csv"):
            df = pd.read_csv(plik, dtype=str, encoding="utf-8-sig")  # -sig: CSV z BOM (Excel)
        else:
            raise ValueError(f"{plik}: obsługiwane tylko .csv i .parquet")
        if KOLUMNA_SYMBOLU not in df.columns:
            raise ValueError(f"{plik}: brak kolumny `{KOLUMNA_SYMBOLU}`")
        for sym in sorted(set(df[KOLUMNA_SYMBOLU].dropna().astype(str))):
            zrodla.setdefault(sym, []).append(plik)
    return zrodla


@dataclass
class Pozycja:
    katalog: str
    stara: bytes
    status: str
    nowa: bytes | None = None
    sha256: str | None = None
    cel_sha256: str | None = None
    symbol: str | None = None
    zrodla: list[str] = field(default_factory=list)

    @property
    def sciezka(self) -> bytes:
        return os.path.join(os.fsencode(self.katalog), self.stara)

    @property
    def cel(self) -> bytes | None:
        return None if self.nowa is None else os.path.join(os.fsencode(self.katalog), self.nowa)


def _zwykly_plik(sciezka: bytes) -> bool:
    return stat.S_ISREG(os.lstat(sciezka).st_mode)


def zaplanuj(katalogi: list[str], symbole: dict[str, list[str]]) -> list[Pozycja]:
    """Plan dla każdej nazwy spoza ASCII w podanych katalogach (płasko). Niczego nie zmienia."""
    plan = []
    for katalog in katalogi:
        kb = os.fsencode(katalog)
        if not os.path.isdir(kb):
            raise FileNotFoundError(f"brak katalogu: {katalog}")
        for nazwa in sorted(os.listdir(kb)):
            if nazwa.isascii():
                continue
            p = Pozycja(katalog=katalog, stara=nazwa, status=POPRAWNA)
            plan.append(p)
            if not _zwykly_plik(p.sciezka):
                p.status = NIE_PLIK
                continue
            p.sha256 = sha256_pliku(p.sciezka)
            try:
                tekst = nazwa.decode("utf-8")
            except UnicodeDecodeError:
                p.status = NIE_UTF8
                continue
            p.nowa = odwroc_cp866(nazwa)
            if p.nowa is None:  # poprawna nazwa spoza ASCII: informacja, bez zmiany
                p.symbol = symbol_z_nazwy(tekst)
                p.zrodla = symbole.get(p.symbol, [])
                continue
            p.symbol = symbol_z_nazwy(p.nowa.decode("utf-8"))
            p.zrodla = symbole.get(p.symbol, [])
            if os.path.lexists(p.cel):
                p.status = CEL_ISTNIEJE
                if _zwykly_plik(p.cel):
                    p.cel_sha256 = sha256_pliku(p.cel)
            elif not p.zrodla:
                p.status = NIEPOTWIERDZONA
            else:
                p.status = DO_ZMIANY
    return plan


def zmien_nazwe_bez_nadpisania(zrodlo: bytes, cel: bytes) -> None:
    """Nowa nazwa jako dowiązanie twarde (FileExistsError, gdy cel istnieje), potem usunięcie starej
    nazwy. Treść (i-węzeł, czas modyfikacji) zostaje ta sama; niczego się nie nadpisuje."""
    os.link(zrodlo, cel)
    os.unlink(zrodlo)


def _tekst(nazwa: bytes | None) -> str:
    return "-" if nazwa is None else nazwa.decode("utf-8", "backslashreplace")


def wypisz_plan(plan: list[Pozycja]) -> None:
    for p in plan:
        if p.status == CEL_ISTNIEJE:
            ta_sama = "ta sama treść" if p.cel_sha256 == p.sha256 else "INNA treść"
            cel = f"TAK ({ta_sama}; sha256 celu {p.cel_sha256 or '-'})"
        elif p.nowa is None:
            cel = "-"
        else:
            cel = "nie"
        print(f"[{p.status}] {p.katalog}")
        print(f"  stara (bajty):   {p.stara!r}")
        print(f"  stara (tekst):   {_tekst(p.stara)}")
        print(f"  nowa:            {_tekst(p.nowa)}")
        print(f"  sha256 treści:   {p.sha256 or '-'}")
        print(f"  cel istnieje:    {cel}")
        zrodla = ", ".join(p.zrodla) if p.zrodla else "BRAK"
        print(f"  symbol:          {p.symbol or '-'} (w danych referencyjnych: {zrodla})")
    ile = {s: sum(p.status == s for p in plan) for s in (DO_ZMIANY, POPRAWNA, *BLOKUJACE)}
    print(
        "PODSUMOWANIE: nazw spoza ASCII "
        + str(len(plan))
        + "; "
        + "; ".join(f"{s} {n}" for s, n in ile.items())
    )


def wykonaj(plan: list[Pozycja]) -> int:
    """Zmiana nazw pozycji DO_ZMIANY; wszystko albo nic wobec blokad z planu."""
    blokady = [p for p in plan if p.status in BLOKUJACE]
    if blokady:
        print(f"ODMOWA: {len(blokady)} pozycji blokujących — nic nie zmieniono.")
        return KOD_BLOKADA
    zrobione = 0
    for p in (p for p in plan if p.status == DO_ZMIANY):
        try:
            zmien_nazwe_bez_nadpisania(p.sciezka, p.cel)
        except OSError as e:
            print(f"PRZERWANO przy {p.sciezka!r}: {e!r}; wykonano {zrobione} zmian przed błędem.")
            return KOD_BLAD
        sha_po = sha256_pliku(p.cel)
        zgodne = "zgodne" if sha_po == p.sha256 else "NIEZGODNE"
        print(
            f"ZMIENIONO {p.katalog}: {_tekst(p.stara)} -> {_tekst(p.nowa)} sha256 {sha_po} {zgodne}"
        )
        if sha_po != p.sha256:
            return KOD_BLAD
        zrobione += 1
    print(f"WYKONANO: zmienionych nazw {zrobione}; sha256 treści zgodne {zrobione}/{zrobione}.")
    return KOD_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    tryb = ap.add_mutually_exclusive_group(required=True)
    tryb.add_argument("--sprawdz", action="store_true", help="tylko plan, bez zmian")
    tryb.add_argument("--wykonaj", action="store_true", help="zmiana nazw pozycji DO_ZMIANY")
    ap.add_argument("katalogi", nargs="+", help="katalogi z plikami (skan płaski)")
    ap.add_argument(
        "--symbole", nargs="+", required=True, help="CSV/parquet z kolumną `symbol` (potwierdzenie)"
    )
    args = ap.parse_args(argv)
    try:
        symbole = wczytaj_symbole(args.symbole)
        plan = zaplanuj(args.katalogi, symbole)
    except (OSError, ValueError) as e:
        print(f"BŁĄD: {e}")
        return KOD_BLAD
    wypisz_plan(plan)
    if args.wykonaj:
        return wykonaj(plan)
    return KOD_BLOKADA if any(p.status in BLOKUJACE for p in plan) else KOD_OK


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    sys.exit(main())
