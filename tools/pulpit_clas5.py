"""Pulpit CLAS-5 — składa jedną stronę z zakładkami Dziennik | Tokeny | Mapa | Radar (artefakt claude.ai).

Publikuje się `tools/pulpit_clas5.html`, pod adresem dawnej strony dziennika (adres w README.md,
zakładki #dziennik, #tokeny, #mapa, #radar). Powłoka `tools/pulpit_clas5_szablon.html` ma nagłówek
z zakładkami; każda zakładka to osobna strona w <iframe srcdoc>, tworzonym przy pierwszym otwarciu.
Źródła zakładek zostają samodzielnymi stronami i działają bez zmian:

    dziennik  docs/strona_dziennik.html  baza dziennik/stan (rutyna Cowork, 06:30 UTC)
    tokeny    tools/strona_tokeny.html   baza tokeny/stan (docs/rag/12)
    mapa      docs/mapa_projektu.html    statyczna
    radar     tools/strona_radar.html    baza radar/stan (zadanie zaplanowane „Radar” na koncie, codziennie)

Dokument zakładki = szkielet, którym platforma owija każdą publikowaną stronę (ustalony 2026-09-28
z opublikowanych Tokenów i Mapy), z PRELUDIUM jako pierwszym skryptem w <head>, + źródło strony.
Preludium: runtime `window.claude` od rodzica (baza strony), motyw `data-theme` rodzica, linki
(zewnętrzne w nowej karcie przez dokument rodzica, kotwice „#…” przewijane na miejscu — w dokumencie
srcdoc adres względny liczy się od adresu rodzica, więc zwykłe kliknięcie przeładowałoby ramkę).
Każdy dokument trafia do powłoki jako blok <script type="application/json" id="strona-<id>">
z JSON-em napisu, w którym każdy znak „<” jest zapisany jako \\u003c — w bloku nie może się pojawić
ani „</script”, ani „<!--”.

    python3 tools/pulpit_clas5.py             # złóż i zapisz tools/pulpit_clas5.html i instrukcję rutyny
    python3 tools/pulpit_clas5.py --sprawdz   # kod 1, gdy któryś zapisany plik różni się od złożenia

Instrukcja rutyny Cowork, która co rano zapisuje dane zakładki Dziennik (`tools/rutyna_dziennika.md`), to
szablon `tools/rutyna_dziennika_szablon.md` z WKLEJONYM `tools/strona_dziennika.py` i jego sumą SHA-256
(liczoną jak w rutynie: bajty bez końcowych białych znaków, CRLF → LF). Rutyna nie pobiera kodu z repo
(strażnik uprawnień Cowork blokuje uruchamianie kodu z repo), więc każda zmiana skryptu danych wymaga
wklejenia nowej instrukcji w Cowork — test aktualności przypomina o tym czerwonym wynikiem.

Tylko biblioteka standardowa. Wynik deterministyczny: te same źródła dają te same bajty; końce
linii czyta się jako LF (klon z CRLF na Windows daje ten sam plik). Pilnuje tests/test_pulpit_clas5.py
(także tego, że zapisany plik jest aktualny — po edycji źródła trzeba złożyć pulpit od nowa).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SZABLON = Path("tools/pulpit_clas5_szablon.html")
WYJSCIE = ROOT / "tools" / "pulpit_clas5.html"
ZAKLADKI: tuple[tuple[str, Path], ...] = (
    ("dziennik", Path("docs/strona_dziennik.html")),
    ("tokeny", Path("tools/strona_tokeny.html")),
    ("mapa", Path("docs/mapa_projektu.html")),
    ("radar", Path("tools/strona_radar.html")),
)
ZNACZNIK = "<!--@LADUNKI@-->"
SKRYPT_RUTYNY = Path("tools/strona_dziennika.py")
SZABLON_RUTYNY = Path("tools/rutyna_dziennika_szablon.md")
RUTYNA = ROOT / "tools" / "rutyna_dziennika.md"
KONIEC_SKRYPTU = "=====KONIEC SKRYPTU====="
LIMIT_STRONY = 16 * 1024 * 1024  # limit platformy dla publikowanej strony

# Szkielet platformy (bajt w bajt z opublikowanych stron): GLOWA + [preludium] + BODY + źródło + KONIEC.
SZKIELET_GLOWA = (
    "<!doctype html><html><head><meta charset=utf8><meta name=viewport "
    'content="width=device-width,initial-scale=1,viewport-fit=cover"><style>'
    ":root{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);"
    "padding-bottom:env(safe-area-inset-bottom,0px)}html{scroll-padding-top:env(safe-area-inset-top,0px)}"
    "body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#faf9f5;"
    "color:#141413}img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}"
    "</style>"
)
SZKIELET_BODY = "</head><body>\n"
SZKIELET_KONIEC = "\n</body></html>\n"

PRELUDIUM = r"""<script>
/* Preludium pulpitu CLAS-5 (tools/pulpit_clas5.py): pierwszy skrypt dokumentu zakładki. */
(function () {
  'use strict';
  var w = window, d = document, p = null;
  try { if (w.parent && w.parent !== w) p = w.parent; } catch (e) { p = null; }
  if (!p) return;
  // (a) Runtime platformy: ta sama przestrzeń nazw co u rodzica, bez opakowania. Funkcje zostają
  //     w realmie rodzica, więc odczyty bazy strony idą przez stronę-rodzica.
  try { if (!w.claude && p.claude) w.claude = p.claude; } catch (e) { /* brak dostępu do rodzica */ }
  // (b) Motyw: data-theme z <html> rodzica (brak u rodzica = brak tutaj).
  try {
    var t = p.document.documentElement.getAttribute('data-theme');
    if (t === null) d.documentElement.removeAttribute('data-theme');
    else d.documentElement.setAttribute('data-theme', t);
  } catch (e) { /* zostaje motyw systemowy */ }
  // (c) Linki. Zewnętrzny: nowa karta przez tymczasowy link w dokumencie rodzica (tam działa obsługa
  //     linków przeglądarki artefaktu), awaryjnie window.open. Kotwica „#…”: przewinięcie tutaj.
  function otworz(url) {
    try {
      var pd = p.document, a = pd.createElement('a');
      a.href = url; a.target = '_blank'; a.rel = 'noopener';
      (pd.body || pd.documentElement).appendChild(a);
      a.click();
      a.parentNode.removeChild(a);
      return;
    } catch (e) { /* awaryjnie niżej */ }
    try { w.open(url, '_blank', 'noopener'); } catch (e) { /* nic więcej się nie da */ }
  }
  function kotwica(frag) {
    var id = frag, el = null;
    try { id = decodeURIComponent(frag); } catch (e) { id = frag; }
    if (id) el = d.getElementById(id) || d.getElementsByName(id)[0] || null;
    if (!el) { if (!id || id.toLowerCase() === 'top') w.scrollTo(0, 0); return; }
    var m = parseFloat(w.getComputedStyle(el).scrollMarginTop) || 0;
    w.scrollTo(0, el.getBoundingClientRect().top + w.pageYOffset - m);
  }
  try {
    d.addEventListener('click', function (e) {
      try {
        if (e.defaultPrevented || e.button !== 0) return;
        var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
        if (!a || a.hasAttribute('download')) return;
        var href = a.getAttribute('href') || '';
        if (href.charAt(0) === '#') { e.preventDefault(); kotwica(href.slice(1)); return; }
        var url = new URL(href, d.baseURI).href;
        if (/^javascript:/i.test(url)) return;
        e.preventDefault();
        otworz(url);
      } catch (err) { /* zostaje zwykłe zachowanie linku */ }
    }, true);
  } catch (e) { /* bez przechwytywania linków */ }
})();
</script>"""


def czytaj(sciezka: Path) -> str:
    """Tekst UTF-8; tryb tekstowy zamienia CRLF na LF, więc złożenie nie zależy od klonu."""
    return sciezka.read_text(encoding="utf-8")


def dokument_zakladki(zrodlo: str) -> str:
    """Pełny dokument zakładki: szkielet platformy z preludium w <head> + źródło strony."""
    return SZKIELET_GLOWA + PRELUDIUM + SZKIELET_BODY + zrodlo + SZKIELET_KONIEC


def blok_json(ident: str, dokument: str) -> str:
    """Blok <script type="application/json"> z napisem `dokument`; żadnego surowego „<” w środku."""
    dane = json.dumps(dokument, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/json" id="strona-{ident}">{dane}</script>'


def zloz(root: Path = ROOT) -> str:
    """Treść tools/pulpit_clas5.html złożona z szablonu i źródeł zakładek (względem `root`)."""
    szablon = czytaj(root / SZABLON)
    if szablon.count(ZNACZNIK) != 1:
        raise ValueError(f"{SZABLON}: znacznik {ZNACZNIK} musi wystąpić dokładnie raz")
    bloki = "\n".join(blok_json(i, dokument_zakladki(czytaj(root / p))) for i, p in ZAKLADKI)
    return szablon.replace(ZNACZNIK, bloki)


def suma_skryptu(skrypt: str) -> str:
    """SHA-256 skryptu tak, jak liczy ją rutyna: bajty UTF-8 bez końcowych białych znaków, CRLF → LF."""
    return hashlib.sha256(skrypt.encode("utf-8").rstrip().replace(b"\r\n", b"\n")).hexdigest()


def instrukcja_rutyny(root: Path = ROOT) -> str:
    """Instrukcja rutyny zakładki Dziennik: szablon + wklejony skrypt danych + jego suma."""
    szablon = czytaj(root / SZABLON_RUTYNY)
    skrypt = czytaj(root / SKRYPT_RUTYNY).rstrip()
    for znacznik in ("@SUMA@", "@SKRYPT@", KONIEC_SKRYPTU):
        if szablon.count(znacznik) != 1:
            raise ValueError(f"{SZABLON_RUTYNY}: znacznik {znacznik} musi wystąpić dokładnie raz")
    if KONIEC_SKRYPTU in skrypt:
        raise ValueError(f"{SKRYPT_RUTYNY} zawiera znacznik końca skryptu {KONIEC_SKRYPTU}")
    # najpierw suma, potem skrypt — treść skryptu nie przechodzi już przez żadną zamianę
    return szablon.replace("@SUMA@", suma_skryptu(skrypt)).replace("@SKRYPT@", skrypt)


def rozmiary(tresc: str, root: Path = ROOT) -> list[str]:
    """Wiersze raportu: rozmiar każdego źródła i jego bloku w pulpicie oraz całej strony (bajty UTF-8)."""
    wiersze = []
    for ident, sciezka in ZAKLADKI:
        zrodlo = czytaj(root / sciezka)
        blok = blok_json(ident, dokument_zakladki(zrodlo))
        wiersze.append(
            f"{ident:9} {str(sciezka):32} źródło {len(zrodlo.encode()):>7} B, "
            f"blok w pulpicie {len(blok.encode()):>7} B"
        )
    szablon = czytaj(root / SZABLON)
    wiersze.append(f"{'powłoka':9} {str(SZABLON):32} {len(szablon.encode()):>14} B")
    razem = len(tresc.encode())
    wiersze.append(
        f"{'razem':9} {'tools/pulpit_clas5.html':32} {razem:>14} B "
        f"({razem / 1024:.1f} KiB; limit platformy 16 MiB)"
    )
    return wiersze


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Składa tools/pulpit_clas5.html (Pulpit CLAS-5).")
    ap.add_argument(
        "--sprawdz",
        action="store_true",
        help="nie zapisuj; kod 1, gdy zapisany plik różni się od świeżego złożenia",
    )
    args = ap.parse_args(argv)
    tresc, rutyna = zloz(), instrukcja_rutyny()
    for wiersz in rozmiary(tresc):
        print(wiersz)
    suma = suma_skryptu(czytaj(ROOT / SKRYPT_RUTYNY))
    print(f"rutyna    {str(SKRYPT_RUTYNY):32} suma SHA-256 {suma}")
    if len(tresc.encode()) > LIMIT_STRONY:
        print("BŁĄD: strona większa niż limit platformy (16 MiB).", file=sys.stderr)
        return 1
    pliki = ((WYJSCIE, tresc), (RUTYNA, rutyna))
    if args.sprawdz:
        stare = [p.name for p, t in pliki if not p.exists() or czytaj(p) != t]
        if stare:
            print(
                f"NIEAKTUALNY: {', '.join(stare)} różni się od złożenia. "
                "Uruchom: python3 tools/pulpit_clas5.py (nowa instrukcja rutyny = wklejenie w Cowork)",
                file=sys.stderr,
            )
            return 1
        print("OK: tools/pulpit_clas5.html i tools/rutyna_dziennika.md są aktualne.")
        return 0
    for plik, tekst in pliki:
        plik.write_text(tekst, encoding="utf-8", newline="\n")
    print("Zapisano tools/pulpit_clas5.html i tools/rutyna_dziennika.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
