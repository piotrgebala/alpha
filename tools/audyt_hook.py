"""
audyt_hook.py

Hook audytowy wykonawców Claude Code (zadania 002, 003, 027 i 029;
`docs/rag/13_izolacja_wykonawcow.md`). Działa na zdarzeniu `PreToolUse` dla narzędzi Bash, Read,
Write, Edit, MultiEdit, NotebookEdit, WebFetch oraz Grep i Glob (przeszukanie katalogu, np. `~/.ssh`,
to też odczyt). Każde wywołanie dopisuje JEDEN wiersz JSON do `~/.clas5_audyt/RRRR-MM-DD.jsonl`
(data UTC; katalog 0700, plik 0600, tworzone przez hook; zmienna `CLAS5_AUDYT_DIR` zmienia katalog
— testy). Wiersz ma listę `flagi`; pusta lista = nic podejrzanego. Flagi:

- `siec_poza_lista` — polecenie sieciowe (curl, wget, git push/fetch/pull/clone/ls-remote,
  pip install, python z requests/urllib/socket/…, nc, ssh, scp, sftp, rsync, telnet, `gh`
  — domyślnie `api.github.com`, WebFetch) do hosta spoza `config/audyt_hosty.yaml` (hosty
  w polu `hosty_spoza_listy`);
- `siec_host_nieznany` — polecenie sieciowe, którego hosta nie da się ustalić z tekstu polecenia
  (np. `python -c` z `requests` i adresem w zmiennej);
- `zapis_poza_repo` — zapis (Write/Edit/MultiEdit/NotebookEdit, a w Bash: `>`/`>>`, `tee`, cel
  `cp`/`mv`, `sed -i`, `curl -o`, `wget -O`; ścieżki względne liczone po `cd` w poleceniu) poza
  repozytorium bieżącego katalogu (`cwd` z wejścia hooka; dla worktree — poza worktree i poza
  `runs/` oraz `data/` głównego checkoutu). Bez flagi (R6): `~/.claude/plans/`, a w sesji głównej
  także `~/.claude/projects/<projekt>/memory/` (subagent piszący do pamięci zostaje oznaczony, bo
  pamięć wczytuje się do każdej przyszłej sesji). Ścieżka z nierozwiniętą zmienną `$…` tej flagi
  nie dostaje (R4: nie wiadomo, dokąd prowadzi);
- `zapis_tmp` — zapis w katalogu tymczasowym (`/tmp`, `$TMPDIR`): wspólny zasób wielu sesji,
  czyli możliwy boczny kanał. Bez flagi (R5) jest tylko WŁASNY scratchpad sesji
  (`/tmp/claude-<uid>/<projekt>/<session_id>/scratchpad/`); scratchpad innej sesji ma flagę;
- `poswiadczenia` — dostęp (odczyt albo zapis) do `~/.ssh`, `.env`, `*.pem`, `*.key`, plików
  z `key`/`secret`/`token`/`credentials` w nazwie, `~/.config/gh`, `~/.git-credentials`, `.netrc`…;
- `dziennik_audytu` — narzędzie CZYTA katalog audytu (np. przegląd tygodnia);
- `dziennik_audytu_zapis` — narzędzie ZMIENIA katalog audytu (R8): Write/Edit/MultiEdit/NotebookEdit,
  w Bash zapisy rozpoznawane jak przy `zapis_poza_repo`, a dla tej jednej flagi także `rm`,
  `rmdir`, `unlink`, `shred`, `truncate`, `touch`, `chmod`, `chown`, `ln`, źródła `mv`, `dd of=`
  i `find … -delete`;
- `wejscie_nieczytelne` / `blad_analizy` — hook nie zrozumiał wejścia; wiersz i tak powstaje,
  więc zły JSON nie jest sposobem na zniknięcie z dziennika.

TRYB DRUGI (od 2026-10-06, ADR-13 etap 2): OZNACZA KAŻDE WYWOŁANIE, A FLAGI Z LISTY `blokuj:`
BLOKUJE. Lista leży w `config/audyt_hosty.yaml` w repo. Nie ma zmiennej środowiskowej, która by ją
włączała albo wyłączała (decyzja użytkownika 2026-10-06 „Wszędzie”: serwer, Windows, Cowork).
Wpis to nazwa flagi (wszystkie narzędzia) albo mapa `flaga` + `narzedzia` + `decyzja` (format:
`parsuj_blokady`). Dla flagi z listy, po zawężeniu do narzędzia, hook wypisuje na stdout
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
"permissionDecisionReason": "<flaga>: <powód>; decyzja użytkownika <data>"}}` i kończy się kodem 0,
a wiersz dziennika dostaje pole `zablokowano`. Decyzje 2026-10-06: `poswiadczenia` tylko
w narzędziach plikowych (Read, Write, Edit, MultiEdit, NotebookEdit, Grep, Glob; w Bash tylko
oznacza) oraz `dziennik_audytu_zapis` we wszystkich narzędziach. Pozostałe flagi tylko oznaczają.

FAIL-OPEN: każdy własny błąd hooka — zły JSON wejścia, brak pliku konfiguracji, zepsuty YAML albo
YAML spoza obsługiwanego podzbioru, wyjątek w analizie — kończy się BEZ odmowy i z kodem 0 (tak jak
`frozen_guard.py`, `skill_audit.py` i `straznik_kontekstu.py`). Zły wpis `blokuj:` (nieznana flaga,
nieznane narzędzie, zły format) niczego nie blokuje. Błąd ZAPISU dziennika nie zdejmuje odmowy już
policzonej: decyzja nie zależy od dziennika, więc zepsuty katalog audytu nie wyłącza blokady.

Co trafia do dziennika: czas, sesja, id i typ agenta, cwd, narzędzie, skrót polecenia (maks.
`MAKS_ZNAKOW` znaków, z maskowaniem wzorców typu token/klucz/hasło/Bearer/dane w URL), ścieżka lub
adres, flagi, hosty i ścieżki, które flagi wywołały, oraz `zablokowano` (flagi, za które hook
odmówił). NIGDY treść plików (`content`, `new_string` i podobne pola nie są czytane) ani nieobcięte
polecenie.

Analiza jest tekstowa (własny, mały tokenizer powłoki): wykrywa typowe przypadki, nie jest
piaskownicą. Poprawki po tygodniu obserwacji (zadanie 029, `docs/rag/13_tydzien_obserwacji.md`):
R1 — cyfry przyklejone do `>`/`<` (`2>&1`) to numer deskryptora, nie słowo (także w `git push`);
R2 — treść heredoka to dane, nie polecenia i nie ścieżki (wyjątek: heredoc czytany przez powłokę,
np. `bash <<EOF`; dla `python - <<EOF` zostaje heurystyka bibliotek sieciowych na całym tekście);
R3 — słowo z nową linią (np. wieloliniowy kod `python -c "…"`, opis commita z `$(cat <<EOF …)`)
to nie ścieżka; R4 — `$NAZWA` z prostego przypisania w tym samym poleceniu (`S=/tmp/…; … > $S/x`,
`export S=…`) rozwija się jak `$HOME`, także w `cd $S`.
Zagnieżdżone `bash -c '…'`, `sh -c '…'` i `eval …` są analizowane tą samą funkcją (do
`MAKS_ZAGNIEZDZENIA` poziomów). Obejście przez np. `bash -c "$(echo … | base64 -d)"` nie zostanie
rozpoznane jako sieć — dlatego docelowa granica to osobny użytkownik systemu (docs/rag/13), a hook
to widoczność i dwie wąskie blokady.

Szybkość: tylko biblioteka standardowa, bez biblioteki YAML (lista hostów i `blokuj:` w prostym
formacie czytane ręcznie); podproces `git remote get-url` tylko dla `git push/fetch/pull` bez adresu
w poleceniu.

Użycie:
    py tools/audyt_hook.py hook      # tryb hooka (JSON zdarzenia PreToolUse na stdin)
"""

from __future__ import annotations

import collections
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PLIK_HOSTOW = REPO / "config" / "audyt_hosty.yaml"
MAKS_ZNAKOW = 300  # skrót polecenia / ścieżki / adresu w dzienniku

F_SIEC = "siec_poza_lista"
F_SIEC_NIEZNANY = "siec_host_nieznany"
F_ZAPIS = "zapis_poza_repo"
F_TMP = "zapis_tmp"
F_POSW = "poswiadczenia"
F_AUDYT = "dziennik_audytu"
F_AUDYT_ZAPIS = "dziennik_audytu_zapis"
F_WEJSCIE = "wejscie_nieczytelne"
F_BLAD = "blad_analizy"

NARZEDZIA_ZAPISU = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
POLE_SCIEZKI = {"NotebookEdit": "notebook_path"}  # reszta narzędzi plikowych: `file_path`
# narzędzia, na które hook jest wpięty (`.claude/settings.json`) — tylko te wolno wpisać w `narzedzia:`
NARZEDZIA_HOOKA = frozenset(
    {"Bash", "Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "WebFetch", "Grep", "Glob"}
)
# flagi, które może włączyć lista `blokuj:`; `wejscie_nieczytelne` i `blad_analizy` nigdy (fail-open)
FLAGI_BLOKOWALNE = frozenset(
    {F_SIEC, F_SIEC_NIEZNANY, F_ZAPIS, F_TMP, F_POSW, F_AUDYT, F_AUDYT_ZAPIS}
)

# --- maskowanie sekretów w skrócie polecenia ------------------------------------------------------
_MASKI = (
    # hasło przyklejone do `-p` tylko tam, gdzie `-p<coś>` znaczy hasło: mysql/mariadb i sshpass;
    # `-p` z odstępem (pytanie o hasło) i `-P` (port) zostają; psql: `-p` to port — nie maskujemy
    (
        re.compile(
            r"((?:^|[\s;&|(/])(?:mysql[a-z_-]*|mariadb[a-z_-]*)\b"
            r"(?:[^;&|\n]*?\s)?-p['\"]?)([^\s;&|'\"]+)"
        ),
        r"\1***",
    ),
    # sshpass: `-p hasło` i `-phasło` (hasło zawsze po `-p`)
    (re.compile(r"(\bsshpass\s+(?:-[^p\s]\S*\s+)*-p\s*['\"]?)([^\s'\"]+)"), r"\1***"),
    (re.compile(r"(?i)(authorization\s*:\s*)(bearer\s+|basic\s+|token\s+)?[^\s'\"]+"), r"\1\2***"),
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1***"),
    (re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@"), r"\1***:***@"),
    # curl/wget `-u user:haslo`, `--user=user:haslo`, `--proxy-user …` — maskowane tylko w formie z „:”
    (
        re.compile(r"(?i)((?:^|\s)(?:-u|-U|--user|--proxy-user)[ =]?['\"]?[^\s:'\"]*:)[^\s'\"]+"),
        r"\1***",
    ),
    (
        re.compile(
            r"(?i)(--?[a-z0-9_-]*(?:key|token|secret|password|passwd|pass|pwd)[a-z0-9_-]*[ =])"
            r"(['\"]?)[^\s'\"]+"
        ),
        r"\1\2***",
    ),
    (
        re.compile(
            r"(?i)([a-z0-9_]*(?:key|token|secret|password|passwd|pwd|signature|auth)[a-z0-9_]*"
            r"['\"]?\s*[=:]\s*)(['\"]?)[^\s'\"&,;)}]+"
        ),
        r"\1\2***",
    ),
    (
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}"
            r"|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})"
        ),
        "***",
    ),
    # długi ciąg z cyframi i literami (klucz, podpis HMAC, hash) — ścieżek z „/” i kropek nie łapie
    (
        re.compile(
            r"(?<![\w/.-])(?=[A-Za-z0-9+_-]*\d)(?=[A-Za-z0-9+_-]*[A-Za-z])[A-Za-z0-9+_-]{32,}=*"
        ),
        "***",
    ),
)


def maskuj(tekst: str, limit: int = MAKS_ZNAKOW) -> str:
    """Maskuje wzorce sekretów, POTEM obcina (sekret na granicy cięcia nie wycieka połową)."""
    for wzorzec, zamiana in _MASKI:
        tekst = wzorzec.sub(zamiana, tekst)
    return tekst if len(tekst) <= limit else tekst[:limit] + "…"


# --- lista hostów ---------------------------------------------------------------------------------
def wczytaj_hosty(sciezka: str | Path | None = None) -> frozenset[str]:
    """Hosty z listy `hosty:` pliku konfiguracyjnego (prosty podzbiór YAML). Brak pliku → pusta
    lista, czyli KAŻDE polecenie sieciowe zostanie oznaczone (bezpieczniejszy kierunek błędu)."""
    sciezka = sciezka or os.environ.get("CLAS5_AUDYT_HOSTY") or PLIK_HOSTOW
    try:
        tekst = Path(sciezka).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return frozenset()
    hosty, w_liscie = set(), False
    for linia in tekst.splitlines():
        bez = linia.split("#", 1)[0].rstrip()
        if not bez.strip():
            continue
        if not bez[0].isspace() and not bez.startswith("-"):
            w_liscie = bez.strip() == "hosty:"
            continue
        element = bez.strip()
        if w_liscie and element.startswith("- "):
            host = element[2:].strip().strip("\"'").lower()
            if host:
                hosty.add(host)
    return frozenset(hosty)


def normalizuj_host(host: str) -> str:
    return host.strip().strip("[]").rstrip(".").lower()


def host_dozwolony(host: str, hosty: frozenset[str]) -> bool:
    host = normalizuj_host(host)
    if host in hosty:
        return True
    return any(w.startswith("*.") and host.endswith(w[1:]) for w in hosty)


# --- lista blokad (ADR-13, etap 2; R7) -----------------------------------------------------------
# `collections.namedtuple`, nie `typing.NamedTuple`: import `typing` to ok. 1,5 ms na każde wywołanie
Blokada = collections.namedtuple("Blokada", "flaga narzedzia decyzja", defaults=(None, None))
Blokada.__doc__ = (
    "Wpis listy `blokuj:`: flaga, narzędzia (frozenset; None = wszystkie narzędzia hooka) i data "
    "decyzji użytkownika (None = brak w konfiguracji)."
)


class _PozaPodzbiorem(ValueError):
    """Tekst konfiguracji jest zepsuty albo wychodzi poza podzbiór YAML, który hook rozumie."""


_DATA = re.compile(r"\d{4}-\d{2}-\d{2}")
_KLUCZ_LINII = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?: +(.*))?")
_KLUCZ_FLOW = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*): +")
_ZWYKLY = re.compile(r"[A-Za-z0-9_./~][A-Za-z0-9_./~+@-]*")
# zwykłe skalary, które YAML bierze za liczbę i nie umie jej zbudować (pada cały plik)
_LICZBA_BEZ_CYFR = re.compile(r"0[bx]_+")
# tylko drukowalne znaki YAML; bez tabulatora, znaków sterujących, NEL, U+2028/U+2029 i BOM
_ZNAK_SPOZA = re.compile(r"[^\n\x20-\x7e\xa0-‧‪-퟿-﻾＀-�\U00010000-\U0010ffff]")


def _linie_yaml(tekst: str) -> list[tuple[int, str]]:
    """(wcięcie, treść) każdej linii z treścią; linie puste i same komentarze odpadają."""
    tekst = tekst.replace("\r\n", "\n").replace("\r", "\n")
    if _ZNAK_SPOZA.search(tekst):
        raise _PozaPodzbiorem("znak spoza podzbioru (tabulator, znak sterujący, BOM)")
    linie = []
    for linia in tekst.split("\n"):
        tresc = linia.strip(" ")
        if tresc and not tresc.startswith("#"):
            linie.append((len(linia) - len(linia.lstrip(" ")), tresc))
    return linie


def _element(tresc: str) -> bool:
    return tresc == "-" or tresc.startswith("- ")


def _pusta(tekst: str) -> bool:
    """Brak wartości: pusty tekst albo sam komentarz."""
    tekst = tekst.lstrip(" ")
    return not tekst or tekst.startswith("#")


def _spacje(s: str, i: int) -> int:
    while i < len(s) and s[i] == " ":
        i += 1
    return i


def _cytat(s: str, i: int) -> tuple[str, int]:
    """Skalar w cudzysłowie w jednej linii: `'…'` (z `''`) albo `"…"` bez ukośnika wstecznego."""
    if s[i] == '"':
        k = s.find('"', i + 1)
        if k < 0 or "\\" in s[i + 1 : k]:
            raise _PozaPodzbiorem("niedomknięty cudzysłów albo sekwencja z ukośnikiem")
        return s[i + 1 : k], k + 1
    czesci, j = [], i + 1
    while True:
        k = s.find("'", j)
        if k < 0:
            raise _PozaPodzbiorem("niedomknięty apostrof")
        czesci.append(s[j:k])
        if not s.startswith("''", k):
            return "".join(czesci), k + 1
        czesci.append("'")
        j = k + 2


def _skalar(s: str, i: int) -> tuple[str, int]:
    if s[i] in "'\"":
        return _cytat(s, i)
    m = _ZWYKLY.match(s, i)
    if not m:
        raise _PozaPodzbiorem("skalar spoza podzbioru")
    tekst = m.group(0)
    if _LICZBA_BEZ_CYFR.fullmatch(tekst):
        raise _PozaPodzbiorem("liczba bez cyfr")
    if _DATA.fullmatch(tekst):  # YAML buduje z tego datę — niemożliwa data psuje cały plik
        try:
            date.fromisoformat(tekst)
        except ValueError as blad:
            raise _PozaPodzbiorem("niemożliwa data") from blad
    return tekst, m.end()


def _wezel_flow(s: str, i: int, glebokosc: int = 0) -> tuple[object, int]:
    """Węzeł flow w jednej linii: `[a, b]`, `{klucz: wartość}` albo skalar."""
    if glebokosc > 20:
        raise _PozaPodzbiorem("za głębokie zagnieżdżenie")
    i = _spacje(s, i)
    if i >= len(s):
        raise _PozaPodzbiorem("brak wartości")
    if s[i] not in "[{":
        return _skalar(s, i)
    lista: list = []
    mapa: dict = {}
    zamkniecie = "]" if s[i] == "[" else "}"
    i = _spacje(s, i + 1)
    if i < len(s) and s[i] == zamkniecie:
        return (lista if zamkniecie == "]" else mapa), i + 1
    while True:
        if zamkniecie == "]":
            element, i = _wezel_flow(s, i, glebokosc + 1)
            lista.append(element)
        else:
            m = _KLUCZ_FLOW.match(s, i)
            if not m or m.group(1) in mapa:
                raise _PozaPodzbiorem("zły albo powtórzony klucz mapy")
            mapa[m.group(1)], i = _wezel_flow(s, m.end(), glebokosc + 1)
        i = _spacje(s, i)
        if i < len(s) and s[i] == ",":
            i = _spacje(s, i + 1)
        elif i < len(s) and s[i] == zamkniecie:
            return (lista if zamkniecie == "]" else mapa), i + 1
        else:
            raise _PozaPodzbiorem("oczekiwano przecinka albo zamknięcia")


def _wartosc_w_linii(tekst: str) -> object:
    """Wartość zapisana w jednej linii (po `- ` albo `klucz: `), z ewentualnym komentarzem."""
    wartosc, i = _wezel_flow(tekst, 0)
    reszta = tekst[i:]
    if reszta and not (reszta.startswith(" ") and _pusta(reszta)):
        raise _PozaPodzbiorem("tekst za wartością")
    return wartosc


def _wezel_blokowy(linie: list[tuple[int, str]]) -> object:
    """Lista `- …` albo mapa `klucz: …`; wcięcie bloku = wcięcie pierwszej linii."""
    baza = linie[0][0]
    if any(wciecie < baza for wciecie, _ in linie):
        raise _PozaPodzbiorem("linia wcięta płycej niż początek bloku")
    if _element(linie[0][1]):
        return _lista_blokowa(linie, baza)
    if _KLUCZ_LINII.fullmatch(linie[0][1]):
        return _mapa_blokowa(linie, baza)
    raise _PozaPodzbiorem("skalar w kilku liniach albo konstrukcja spoza podzbioru")


def _lista_blokowa(linie: list[tuple[int, str]], baza: int) -> list:
    wynik, i = [], 0
    while i < len(linie):
        wciecie, tresc = linie[i]
        if wciecie != baza or not _element(tresc):
            raise _PozaPodzbiorem("element listy z innym wcięciem")
        j = i + 1
        while j < len(linie) and linie[j][0] > baza:
            j += 1
        wynik.append(_element_listy(tresc[1:], baza, linie[i + 1 : j]))
        i = j
    return wynik


def _element_listy(reszta: str, baza: int, dzieci: list[tuple[int, str]]) -> object:
    tresc = reszta.lstrip(" ")
    if _pusta(tresc):
        return _wezel_blokowy(dzieci) if dzieci else None
    if _element(tresc):
        raise _PozaPodzbiorem("lista w liście w jednej linii")
    if _KLUCZ_LINII.fullmatch(tresc):  # mapa zaczęta w linii `- `: klucze w kolumnie pierwszego
        kolumna = baza + 1 + len(reszta) - len(tresc)
        return _mapa_blokowa([(kolumna, tresc), *dzieci], kolumna)
    if dzieci:
        raise _PozaPodzbiorem("wartość w kilku liniach")
    return _wartosc_w_linii(tresc)


def _mapa_blokowa(linie: list[tuple[int, str]], baza: int) -> dict:
    wynik: dict = {}
    i = 0
    while i < len(linie):
        wciecie, tresc = linie[i]
        m = _KLUCZ_LINII.fullmatch(tresc) if wciecie == baza else None
        if m is None or m.group(1) in wynik:
            raise _PozaPodzbiorem("zła linia mapy albo powtórzony klucz")
        reszta, j = m.group(2) or "", i + 1
        if _pusta(reszta):  # wartość niżej: blok wcięty albo lista `- ` w tej samej kolumnie
            while j < len(linie) and (
                linie[j][0] > baza or (linie[j][0] == baza and _element(linie[j][1]))
            ):
                j += 1
            wynik[m.group(1)] = _wezel_blokowy(linie[i + 1 : j]) if j > i + 1 else None
        elif j < len(linie) and linie[j][0] > baza:
            raise _PozaPodzbiorem("wartość w kilku liniach")
        else:
            wynik[m.group(1)] = _wartosc_w_linii(reszta)
        i = j
    return wynik


def yaml_podzbior(tekst: str) -> dict | None:
    """Mapa najwyższego poziomu z prostego podzbioru YAML albo None, gdy tekst jest zepsuty albo
    wychodzi poza podzbiór. Podzbiór: mapy i listy blokowe (wcięcie spacjami; lista `- ` może stać
    w kolumnie klucza), w jednej linii `[a, b]` i `{klucz: wartość}`, skalary zwykłe
    `[A-Za-z0-9_./~][A-Za-z0-9_./~+@-]*` albo w cudzysłowie (bez `\\`), komentarze `#`. Wszystko,
    co podzbiór przyjmuje, YAML czyta tak samo (test właściwości z PyYAML). Czego hook nie rozumie
    (tabulator, wartość w kilku liniach, kotwice, powtórzony klucz…), tego nie zgaduje: cały plik
    jest wtedy „zepsuty”, czyli bez blokad (fail-open)."""
    try:
        linie = _linie_yaml(tekst)
        dokument = _wezel_blokowy(linie) if linie else {}
    except Exception:  # noqa: BLE001 — także RecursionError; zepsuty plik = brak blokad
        return None
    return dokument if isinstance(dokument, dict) else None


def _data_ok(tekst: object) -> bool:
    if not isinstance(tekst, str) or not _DATA.fullmatch(tekst):
        return False
    try:
        date.fromisoformat(tekst)
    except ValueError:
        return False
    return True


def _blokada(wpis: object) -> Blokada | None:
    """Jeden wpis `blokuj:` → Blokada; zły wpis → None (ten wpis niczego nie blokuje)."""
    if isinstance(wpis, str):
        return Blokada(wpis) if wpis in FLAGI_BLOKOWALNE else None
    if not isinstance(wpis, dict) or not set(wpis) <= {"flaga", "narzedzia", "decyzja"}:
        return None  # nieznany klucz (np. literówka `narzedzie:`) nie rozszerza blokady
    flaga, narzedzia = wpis.get("flaga"), wpis.get("narzedzia")
    if not isinstance(flaga, str) or flaga not in FLAGI_BLOKOWALNE:
        return None
    if "narzedzia" in wpis and not (
        isinstance(narzedzia, list)
        and narzedzia
        and all(isinstance(n, str) and n in NARZEDZIA_HOOKA for n in narzedzia)
    ):
        return None
    if "decyzja" in wpis and not _data_ok(wpis["decyzja"]):
        return None
    zakres = frozenset(narzedzia) if isinstance(narzedzia, list) else None
    return Blokada(flaga, zakres, wpis.get("decyzja"))


def parsuj_blokady(tekst: str) -> tuple[Blokada, ...]:
    """Lista `blokuj:` z tekstu `config/audyt_hosty.yaml` (R7). Wpis to:

    - nazwa flagi (`- dziennik_audytu_zapis`) — blokada we wszystkich narzędziach hooka;
    - mapa `flaga:` + opcjonalnie `narzedzia: [Read, …]` (blokada tylko w tych narzędziach)
      i `decyzja: "RRRR-MM-DD"` (data decyzji użytkownika, trafia do powodu odmowy); w stylu
      blokowym albo `{flaga: …, narzedzia: […]}`.

    Fail-open: nieznana flaga (także `wejscie_nieczytelne` i `blad_analizy`), nieznane narzędzie,
    pusta lista narzędzi, nieznany klucz, zła data albo zły typ → ten wpis niczego nie blokuje,
    reszta działa. Zepsuty plik albo plik spoza podzbioru YAML (`yaml_podzbior`), brak listy,
    `blokuj: []` → żadnej blokady."""
    dokument = yaml_podzbior(tekst)
    lista = dokument.get("blokuj") if dokument is not None else None
    if not isinstance(lista, list):
        return ()
    return tuple(b for b in map(_blokada, lista) if b is not None)


def wczytaj_blokady(sciezka: str | Path | None = None) -> tuple[Blokada, ...]:
    """`blokuj:` z `config/audyt_hosty.yaml` w repo. Celowo BEZ zmiennej środowiskowej (także bez
    `CLAS5_AUDYT_HOSTY`, która zmienia tylko listę hostów): blokada zapisana w repo działa wszędzie,
    gdzie działa hook (decyzja użytkownika 2026-10-06). Brak pliku albo błąd odczytu → ()."""
    try:
        return parsuj_blokady(Path(sciezka or PLIK_HOSTOW).read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001 — fail-open: brak blokad
        return ()


def zablokowane_flagi(flagi, narzedzie: str, blokady) -> list[str]:
    """Flagi wywołania, które lista `blokuj:` blokuje w tym narzędziu (posortowane)."""
    return sorted(
        {
            b.flaga
            for b in blokady
            if b.flaga in flagi
            and b.flaga in FLAGI_BLOKOWALNE
            and (b.narzedzia is None or narzedzie in b.narzedzia)
        }
    )


# --- tokenizer powłoki ----------------------------------------------------------------------------
SEPARATORY = set(";&|()\n`")


def segmenty(polecenie: str) -> list[list[str]]:
    """Dzieli polecenie na proste polecenia (po niecytowanych ; & | ( ) ` i nowej linii) i słowa
    (z usuniętymi cudzysłowami). Przekierowania jako osobne słowa `>`, `>>`, `<`, `<<`; `>&N`
    (duplikacja deskryptora) pomijane. Cyfry przyklejone do `>`/`<` (`2>&1`, `2>/dev/null`) to
    numer deskryptora, nie słowo (R1). Nigdy nie rzuca — niedomknięty cudzysłów kończy słowo."""
    wynik: list[list[str]] = []
    slowa: list[str] = []
    bufor: list[str] = []
    jest_slowo = False
    same_cyfry = True  # słowo to dotąd same niecytowane cyfry (kandydat na numer deskryptora)
    cudzyslow = None
    i, n = 0, len(polecenie)

    def zamknij_slowo():
        nonlocal bufor, jest_slowo, same_cyfry
        if jest_slowo:
            slowa.append("".join(bufor))
        bufor, jest_slowo, same_cyfry = [], False, True

    def zamknij_segment():
        nonlocal slowa
        zamknij_slowo()
        if slowa:
            wynik.append(slowa)
        slowa = []

    while i < n:
        c = polecenie[i]
        if cudzyslow:
            if c == cudzyslow:
                cudzyslow = None
            elif c == "\\" and cudzyslow == '"' and i + 1 < n and polecenie[i + 1] in '"\\$`':
                i += 1
                bufor.append(polecenie[i])
            else:
                bufor.append(c)
        elif c in "'\"":
            cudzyslow, jest_slowo, same_cyfry = c, True, False
        elif c == "\\" and i + 1 < n:
            i += 1
            if polecenie[i] != "\n":
                bufor.append(polecenie[i])
                jest_slowo, same_cyfry = True, False
        elif c in " \t\r":
            zamknij_slowo()
        elif c in SEPARATORY:
            zamknij_segment()
        elif c in "<>":
            if jest_slowo and same_cyfry:  # `2>&1`, `2>/dev/null`: numer deskryptora (R1)
                bufor, jest_slowo = [], False
            zamknij_slowo()
            znak = c
            if i + 1 < n and polecenie[i + 1] == c:
                i += 1
                znak += c
            if c == ">" and i + 1 < n and polecenie[i + 1] == "&":  # 2>&1: nie plik
                i += 2
                while i < n and (polecenie[i].isdigit() or polecenie[i] == "-"):
                    i += 1
                continue
            if c == ">" and i + 1 < n and polecenie[i + 1] == "|":
                i += 1
            slowa.append(znak)
        else:
            bufor.append(c)
            jest_slowo = True
            same_cyfry = same_cyfry and c in "0123456789"
        i += 1
    zamknij_segment()
    return wynik


# --- heredoki (R2) --------------------------------------------------------------------------------
def _koniec_arytmetyki(s: str, j: int) -> int:
    """Indeks za `))` zamykającym `$((` (treść od `j`); bez zamknięcia — koniec tekstu."""
    glebokosc = 2
    while j < len(s) and glebokosc:
        if s[j] == "(":
            glebokosc += 1
        elif s[j] == ")":
            glebokosc -= 1
        j += 1
    return j


def _ogranicznik(s: str, j: int) -> tuple[str, int]:
    """Słowo ogranicznika heredoka od `j` (cudzysłowy zdjęte) i indeks za nim; zły → ("", j)."""
    znaki: list[str] = []
    start, cudzyslow = j, None
    while j < len(s):
        c = s[j]
        if cudzyslow:
            if c == cudzyslow:
                cudzyslow = None
            else:
                znaki.append(c)
        elif c in "'\"":
            cudzyslow = c
        elif c == "\\" and j + 1 < len(s):
            j += 1
            znaki.append(s[j])
        elif c in " \t\n;&|()<>":
            break
        else:
            znaki.append(c)
        j += 1
    if cudzyslow:
        return "", start
    return "".join(znaki), j


def _wytnij_ciala(s: str, i: int, oczekujace: list[tuple[str, bool]], ciala: list[str]) -> int:
    """Od linii `i` zbiera treść kolejnych heredoków aż do linii-ogranicznika; zwraca indeks za
    ostatnim ogranicznikiem (bez ogranicznika treść sięga do końca polecenia, jak w bash)."""
    for ogranicznik, bez_tabow in oczekujace:
        linie = []
        while i < len(s):
            k = s.find("\n", i)
            koniec = len(s) if k < 0 else k
            linia, i = s[i:koniec], koniec + 1
            if (linia.lstrip("\t") if bez_tabow else linia) == ogranicznik:
                break
            linie.append(linia)
        ciala.append("\n".join(linie))
    return min(i, len(s))


def bez_heredokow(polecenie: str) -> tuple[str, list[str]]:
    """Polecenie bez TREŚCI heredoków (R2) i lista tych treści. Operator z ogranicznikiem
    (`<<'EOF'`) zostaje, więc `cat > plik <<'EOF'` dalej daje cel zapisu. `<<` w cudzysłowie,
    w komentarzu i w arytmetyce `$(( … ))` oraz `<<<` (here-string) heredoka nie zaczynają.
    Nigdy nie rzuca."""
    wynik: list[str] = []
    ciala: list[str] = []
    oczekujace: list[tuple[str, bool]] = []
    cudzyslow = None
    i, n = 0, len(polecenie)
    while i < n:
        c = polecenie[i]
        if cudzyslow:
            if c == cudzyslow:
                cudzyslow = None
            elif c == "\\" and cudzyslow == '"' and i + 1 < n:
                wynik.append(c)
                i += 1
                c = polecenie[i]
        elif c in "'\"":
            cudzyslow = c
        elif c == "\\" and i + 1 < n:
            wynik.append(c)
            i += 1
            c = polecenie[i]
        elif c == "#" and (i == 0 or polecenie[i - 1] in " \t\n;&|()"):  # komentarz do końca linii
            koniec = polecenie.find("\n", i)
            koniec = n if koniec < 0 else koniec
            wynik.append(polecenie[i:koniec])
            i = koniec
            continue
        elif polecenie.startswith("$((", i):
            koniec = _koniec_arytmetyki(polecenie, i + 3)
            wynik.append(polecenie[i:koniec])
            i = koniec
            continue
        elif polecenie.startswith("<<<", i):  # here-string: całe `<<<` naraz, to nie heredoc
            wynik.append("<<<")
            i += 3
            continue
        elif polecenie.startswith("<<", i):
            j = i + 2
            bez_tabow = j < n and polecenie[j] == "-"  # `<<-EOF`: ogranicznik może mieć taby
            if bez_tabow:
                j += 1
            while j < n and polecenie[j] in " \t":
                j += 1
            ogranicznik, j = _ogranicznik(polecenie, j)
            if ogranicznik:
                oczekujace.append((ogranicznik, bez_tabow))
            wynik.append(polecenie[i:j])
            i = j
            continue
        elif c == "\n" and oczekujace:
            wynik.append(c)
            i = _wytnij_ciala(polecenie, i + 1, oczekujace, ciala)
            oczekujace = []
            continue
        wynik.append(c)
        i += 1
    return "".join(wynik), ciala


OPAKOWANIA = {"sudo", "env", "time", "nohup", "nice", "exec", "command", "xargs", "stdbuf", "!"}
_PRZYPISANIE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def program_i_argumenty(slowa: list[str]) -> tuple[str, list[str]]:
    """Pomija przypisania zmiennych i opakowania (sudo, env, timeout N, xargs…) → (program, args)."""
    i = 0
    while i < len(slowa):
        s = slowa[i]
        nazwa = s.replace("\\", "/").rsplit("/", 1)[-1].lower()
        if _PRZYPISANIE.match(s) or (s.startswith("-") and i > 0):
            i += 1
        elif nazwa in OPAKOWANIA:
            i += 1
        elif nazwa == "timeout":
            i += 1
            while i < len(slowa) and (slowa[i].startswith("-") or slowa[i][:1].isdigit()):
                i += 1
        else:
            return nazwa, slowa[i + 1 :]
    return "", []


# --- sieć ---------------------------------------------------------------------------------------
_URL = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://(?:[^/\s@'\"]*@)?(\[[0-9a-f:.]+\]|[a-z0-9._-]+)")
_SCP = re.compile(r"^(?:[^@/\s]+@)?([A-Za-z0-9._-]+|\[[0-9a-fA-F:.]+\]):(?!//)")
_DOMENA = re.compile(r"(?i)^(?:[a-z0-9-]+\.)+[a-z]{2,}(?::\d+)?(?:/.*)?$")
_BIBLIOTEKI_SIECI = re.compile(
    r"\b(requests|urllib|urllib3|socket|http\.client|httpx|aiohttp|websockets?|ftplib|smtplib"
    r"|ccxt|paramiko)\b"
)
PYTHON = re.compile(r"^(python(\d+(\.\d+)?)?|py|pypy3?)(\.exe)?$")
CURL_OPCJE_Z_ARG = {
    "-o", "--output", "-H", "--header", "-d", "--data", "--data-raw", "--data-binary", "-u",
    "--user", "-A", "--user-agent", "-e", "--referer", "-b", "--cookie", "-c", "--cookie-jar",
    "-T", "--upload-file", "-K", "--config", "-w", "--write-out", "-O", "-P", "-X", "--request",
    "--output-document", "--directory-prefix", "-F", "--form", "-m", "--max-time", "-r", "--range",
}  # fmt: skip
SSH_OPCJE_Z_ARG = set("-b -c -D -E -e -F -I -i -J -L -l -m -O -o -p -P -Q -R -S -W -w -B".split())


def hosty_z_tekstu(tekst: str) -> list[str]:
    return [normalizuj_host(m.group(1)) for m in _URL.finditer(tekst)]


def _pierwszy_argument(args: list[str], opcje_z_arg: set[str]) -> str | None:
    pomin = False
    for a in args:
        if pomin:
            pomin = False
        elif a in opcje_z_arg:
            pomin = True
        elif not a.startswith("-") and a not in ("<", "<<", ">", ">>"):
            return a
    return None


def _host_ssh(cel: str) -> str:
    cel = cel.split("@", 1)[-1]
    if cel.startswith("["):
        return normalizuj_host(cel.split("]", 1)[0])
    return normalizuj_host(cel.split(":", 1)[0])


def _url_zdalnego(cwd: str, nazwa: str) -> str | None:
    """Adres zdalnego repozytorium z konfiguracji gita (tylko `git remote get-url`, bez sieci)."""
    import subprocess  # leniwie: potrzebny tylko dla git push/fetch/pull bez adresu

    try:
        wynik = subprocess.run(
            ["git", "-C", cwd or ".", "remote", "get-url", nazwa],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return wynik.stdout.strip() or None if wynik.returncode == 0 else None


def _hosty_git_url(url: str) -> list[str]:
    hosty = hosty_z_tekstu(url)
    if not hosty and (m := _SCP.match(url)):
        hosty = [normalizuj_host(m.group(1))]
    return hosty


def siec_w_segmencie(
    program: str, args: list[str], cale: str, cwd: str
) -> tuple[bool, list[str]] | None:
    """None = segment nie jest poleceniem sieciowym; inaczej (host_znany, hosty)."""
    if program in ("curl", "wget"):
        hosty = hosty_z_tekstu(" ".join(args))
        if not hosty:
            poprzedni = ""
            for a in args:
                if not a.startswith("-") and poprzedni not in CURL_OPCJE_Z_ARG and _DOMENA.match(a):
                    hosty.append(normalizuj_host(a.split("/", 1)[0].split(":", 1)[0]))
                poprzedni = a
        return bool(hosty), hosty
    if program in ("nc", "ncat", "netcat", "telnet"):
        host = _pierwszy_argument(args, {"-p", "-s", "-w", "-i", "-x", "-X", "-e", "-c"})
        return (True, [normalizuj_host(host)]) if host else (False, [])
    if program in ("ssh", "sftp"):
        cel = _pierwszy_argument(args, SSH_OPCJE_Z_ARG)
        return (True, [_host_ssh(cel)]) if cel else (False, [])
    if program in ("scp", "rsync"):
        hosty = hosty_z_tekstu(" ".join(args))
        for a in args:
            if not a.startswith("-") and (m := _SCP.match(a)) and "/" not in m.group(1):
                hosty.append(normalizuj_host(m.group(1)))
        if program == "rsync" and not hosty:
            return None  # rsync lokalny
        return bool(hosty), hosty
    if program == "git":
        return _siec_git(args, cwd)
    if program == "gh":  # GitHub CLI: każde polecenie poza pomocą/wersją idzie do API GitHuba
        if not args or args[0] in ("help", "version", "--help", "-h", "--version", "completion"):
            return None
        for j, a in enumerate(args):
            if a.startswith("--hostname="):
                return True, [normalizuj_host(a.split("=", 1)[1])]
            if a == "--hostname" and j + 1 < len(args):
                return True, [normalizuj_host(args[j + 1])]
        return True, ["api.github.com"]
    if program in ("pip", "pip3") or (PYTHON.match(program) and args[:2] == ["-m", "pip"]):
        if PYTHON.match(program):
            args = args[2:]
        return _siec_pip(args)
    if program == "uv" and args[:2] == ["pip", "install"]:
        return _siec_pip(args[1:])
    if PYTHON.match(program):
        kod = None
        if "-c" in args and args.index("-c") + 1 < len(args):
            kod = args[args.index("-c") + 1]
        elif "-" in args or "<<" in args or "<" in args:
            kod = cale  # heredoc / skrypt ze stdin: treść jest w całym poleceniu
        if kod is None or not _BIBLIOTEKI_SIECI.search(kod):
            return None
        hosty = hosty_z_tekstu(kod)
        return bool(hosty), hosty
    return None


def _siec_git(args: list[str], cwd: str) -> tuple[bool, list[str]] | None:
    i, katalog = 0, cwd
    while i < len(args) and args[i].startswith("-"):
        if args[i] in ("-C", "-c", "--git-dir", "--work-tree") and i + 1 < len(args):
            if args[i] == "-C":
                katalog = os.path.join(cwd or ".", args[i + 1])
            i += 1
        i += 1
    if i >= len(args) or args[i] not in ("push", "fetch", "pull", "clone", "ls-remote"):
        return None
    reszta, pomin = [], False
    for a in args[i + 1 :]:  # bez przekierowań i ich celów (`> log.txt`) — R1
        if pomin:
            pomin = False
        elif a in _PRZEKIEROWANIA:
            pomin = True
        elif not a.startswith("-"):
            reszta.append(a)
    for a in reszta:
        if hosty := _hosty_git_url(a):
            return True, hosty
    if args[i] == "clone":
        return (False, []) if reszta else None  # clone lokalnej ścieżki nie jest siecią
    nazwa = reszta[0] if reszta and "/" not in reszta[0] else "origin"
    url = _url_zdalnego(katalog, nazwa)
    if url is None:
        return False, []
    hosty = _hosty_git_url(url)
    if not hosty and (url.startswith(("/", ".", "file:")) or os.path.isabs(url)):
        return None  # zdalne repo lokalne
    return bool(hosty), hosty


def _siec_pip(args: list[str]) -> tuple[bool, list[str]] | None:
    if not args or args[0] not in ("install", "download", "wheel"):
        return None
    hosty = hosty_z_tekstu(" ".join(args))
    if not any(a.startswith(("-i", "--index-url", "--extra-index-url")) for a in args):
        hosty.append("pypi.org")
    return True, hosty


# --- ścieżki --------------------------------------------------------------------------------------
_NAZWY_POSW = {
    ".git-credentials", ".netrc", "_netrc", ".pgpass", ".pypirc", ".npmrc", "credentials",
    "credentials.json", "credentials.yaml", "credentials.yml", "authorized_keys", "known_hosts",
}  # fmt: skip
_KATALOGI_POSW = {".ssh", ".gnupg", ".aws", ".kube", ".docker"}
_ROZSZERZENIA_POSW = (".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".ppk", ".asc", ".gpg")
_SLOWA_POSW = re.compile(
    r"(?i)(^|[._-])(api[_-]?)?(keys?|secrets?|tokens?|credentials?|passwords?)([._-]|$)"
)


def _kodowalna(sciezka: str) -> str:
    """Ścieżka, którą system plików umie zakodować. Znak spoza kodowania — np. samotny surogat
    `\\ud800` z JSON-a wejścia (Linux: UnicodeEncodeError w `expanduser` i `realpath`) — zamienia
    się na „?”: takiej nazwy i tak nie ma na dysku, a resztę ścieżki ocenia się jak każdą inną.
    Bajt zerowy zostaje (dalej ValueError → wiersz z `blad_analizy`)."""
    try:
        os.fsencode(sciezka)
        return sciezka
    except UnicodeEncodeError:
        kodowanie = sys.getfilesystemencoding()
        return sciezka.encode(kodowanie, "replace").decode(kodowanie)


_ZMIENNA = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def rozwin_zmienne(tekst: str, zmienne: dict[str, str] | None = None) -> str:
    """`$NAZWA` i `${NAZWA}` → wartość dla nazw znanych z przypisań w poleceniu (R4) oraz `HOME`;
    nieznane zostają jak są (`$…` w ścieżce znaczy „nie wiadomo, dokąd”)."""
    znane = zmienne or {}

    def zamien(m: re.Match) -> str:
        nazwa = m.group(1) or m.group(2)
        if nazwa in znane:
            return znane[nazwa]
        return os.path.expanduser("~") if nazwa == "HOME" else m.group(0)

    return _ZMIENNA.sub(zamien, tekst)


def rozwin(sciezka: str, cwd: str, zmienne: dict[str, str] | None = None) -> str:
    """Ścieżka bezwzględna z rozwiniętym `~`, `$HOME` i znanymi `$NAZWA` (R4) oraz rozwiązanymi
    dowiązaniami."""
    s = os.path.expanduser(_kodowalna(rozwin_zmienne(sciezka, zmienne)))
    if not os.path.isabs(s):
        s = os.path.join(_kodowalna(cwd or os.getcwd()), s)
    return os.path.realpath(s)


def czy_poswiadczenia(sciezka: str) -> bool:
    czesci = sciezka.replace("\\", "/").lower().split("/")
    nazwa = czesci[-1]
    if _KATALOGI_POSW & set(czesci[:-1]) or nazwa in _KATALOGI_POSW:
        return True
    if "/.config/gh" in "/".join(czesci) or nazwa in _NAZWY_POSW:
        return True
    if nazwa == ".env" or nazwa.startswith(".env.") or nazwa.endswith(".env"):
        return True
    if nazwa.endswith(_ROZSZERZENIA_POSW) or nazwa.startswith(("id_rsa", "id_ed25519", "id_ecdsa")):
        return True
    return bool(_SLOWA_POSW.search(nazwa))


def _pod(sciezka: str, katalog: str) -> bool:
    katalog = katalog.rstrip(os.sep) or os.sep
    return sciezka == katalog or sciezka.startswith(katalog + os.sep)


def katalogi_dozwolone(cwd: str) -> list[str]:
    """Korzeń repozytorium z `cwd` (szukanie `.git` w górę); dla worktree dodatkowo `runs/`
    i `data/` głównego checkoutu (plik `.git` worktree wskazuje `<główne>/.git/worktrees/<n>`)."""
    start = os.path.realpath(_kodowalna(cwd or os.getcwd()))
    korzen, sciezka = start, start
    while True:
        if os.path.exists(os.path.join(sciezka, ".git")):
            korzen = sciezka
            break
        wyzej = os.path.dirname(sciezka)
        if wyzej == sciezka:
            break
        sciezka = wyzej
    dozwolone = [korzen]
    plik_git = os.path.join(korzen, ".git")
    if os.path.isfile(plik_git):
        try:
            with open(plik_git, encoding="utf-8") as fh:
                wskaznik = fh.read(4096).strip()
        except OSError:
            wskaznik = ""
        if wskaznik.startswith("gitdir:"):
            gitdir = Path(os.path.realpath(os.path.join(korzen, wskaznik[7:].strip())))
            if gitdir.parent.name == "worktrees" and gitdir.parent.parent.name == ".git":
                glowny = gitdir.parent.parent.parent
                dozwolone += [str(glowny / "runs"), str(glowny / "data")]
    return dozwolone


def katalogi_tmp() -> list[str]:
    kandydaci = {"/tmp", "/var/tmp", os.environ.get("TMPDIR", ""), os.environ.get("TEMP", "")}
    return [os.path.realpath(k) for k in kandydaci if k]


# --- analiza jednego wywołania --------------------------------------------------------------------
class Wynik:
    def __init__(self) -> None:
        self.flagi: set[str] = set()
        self.hosty: list[str] = []
        self.sciezki: list[str] = []
        self.pierwsze: dict[str, str] = {}  # flaga → pierwsza ścieżka albo host (powód odmowy)

    def oznacz(self, flaga: str, sciezka: str | None = None, host: str | None = None) -> None:
        self.flagi.add(flaga)
        if (sciezka or host) and flaga not in self.pierwsze:
            self.pierwsze[flaga] = sciezka or host or ""
        if sciezka and sciezka not in self.sciezki and len(self.sciezki) < 20:
            self.sciezki.append(sciezka)
        if host and host not in self.hosty and len(self.hosty) < 20:
            self.hosty.append(host)


def sprawdz_siec(wynik: Wynik, znany: bool, hosty: list[str], dozwolone: frozenset[str]) -> None:
    if not znany:
        wynik.oznacz(F_SIEC_NIEZNANY)
    for h in hosty:
        if not host_dozwolony(h, dozwolone):
            wynik.oznacz(F_SIEC, host=h)


_SESJA = re.compile(r"[A-Za-z0-9_-]{1,128}")


def wlasny_scratchpad(pelna: str, sesja: str | None) -> bool:
    """R5: `pelna` leży we WŁASNYM scratchpadzie sesji
    `<tmp>/claude-<uid>/<projekt>/<sesja>/scratchpad/`. Scratchpad innej sesji i reszta katalogu
    tymczasowego — nie (dalej `zapis_tmp`). Subagent ma `session_id` sesji głównej."""
    if not sesja or not _SESJA.fullmatch(sesja):
        return False
    for tmp in katalogi_tmp():
        korzen = tmp.rstrip(os.sep)
        if not pelna.startswith(korzen + os.sep):
            continue
        czesci = pelna[len(korzen) + 1 :].split(os.sep)
        if (
            len(czesci) >= 4
            and czesci[0].startswith("claude-")
            and czesci[1]
            and czesci[2] == sesja
            and czesci[3] == "scratchpad"
        ):
            return True
    return False


def zapis_claude_bez_flagi(pelna: str, agent: str | None) -> bool:
    """R6: katalogi Claude Code. `~/.claude/plans/` (tryb planowania) — bez flagi dla każdego;
    `~/.claude/projects/<projekt>/memory/` — bez flagi tylko w sesji głównej. Subagent piszący do
    pamięci zostaje oznaczony, bo pamięć wczytuje się do każdej przyszłej sesji."""
    claude = os.path.realpath(os.path.join(os.path.expanduser("~"), ".claude"))
    if _pod(pelna, os.path.join(claude, "plans")):
        return True
    projekty = os.path.join(claude, "projects")
    if agent or not pelna.startswith(projekty + os.sep):
        return False
    czesci = pelna[len(projekty) + 1 :].split(os.sep)
    return len(czesci) >= 2 and bool(czesci[0]) and czesci[1] == "memory"


def sprawdz_sciezke(
    wynik: Wynik,
    surowa: str,
    cwd: str,
    katalog_audytu: str,
    *,
    zapis: bool,
    baza: str | None = None,
    sesja: str | None = None,
    agent: str | None = None,
    zmienne: dict[str, str] | None = None,
    modyfikacja: bool = False,
) -> None:
    """`cwd` wyznacza repozytorium (katalogi dozwolone), `baza` — katalog, względem którego
    rozwija się ścieżkę względną (po `cd` w poleceniu; domyślnie `cwd`). `zapis` — zapis treści
    (flagi zapisu); `modyfikacja` — zmiana bez zapisu treści (rm, mv, touch…), która liczy się
    tylko jako zapis do katalogu audytu (R8). `sesja` i `agent` — R5 i R6; `zmienne` — R4."""
    pelna = rozwin(surowa, baza or cwd, zmienne)
    if czy_poswiadczenia(pelna):
        wynik.oznacz(F_POSW, sciezka=pelna)
    if _pod(pelna, katalog_audytu):  # R8: odczyt i zapis katalogu audytu to osobne flagi
        wynik.oznacz(F_AUDYT_ZAPIS if zapis or modyfikacja else F_AUDYT, sciezka=pelna)
    if not zapis or pelna.startswith("/dev/"):
        return
    if any(_pod(pelna, k) for k in katalogi_dozwolone(cwd)):
        return
    if wlasny_scratchpad(pelna, sesja) or zapis_claude_bez_flagi(pelna, agent):
        return
    if any(_pod(pelna, k) for k in katalogi_tmp()):
        wynik.oznacz(F_TMP, sciezka=pelna)
    elif "$" not in pelna:  # R4: nierozwinięta zmienna — nie wiadomo, dokąd prowadzi zapis
        wynik.oznacz(F_ZAPIS, sciezka=pelna)


def _wyglada_na_sciezke(slowo: str) -> bool:
    """Słowo z `/`, `.` albo `~`; słowo z nową linią to tekst, nie ścieżka (R3)."""
    return (
        bool(slowo)
        and not slowo.startswith("-")
        and "\n" not in slowo
        and ("/" in slowo or "." in slowo or "~" in slowo)
    )


POWLOKI = {"bash", "sh", "dash", "zsh", "ksh", "ash"}
MAKS_ZAGNIEZDZENIA = 3  # bash -c 'sh -c "…"' — głębiej nie schodzimy (i nie pętlimy)
_PRZEKIEROWANIA = (">", ">>", "<", "<<")


def polecenie_powloki(program: str, args: list[str]) -> str | None:
    """Tekst wewnętrznego polecenia z `bash -c '…'`, `sh -lc '…'` albo `eval …`; inaczej None."""
    if program == "eval":
        return " ".join(args) or None
    if program not in POWLOKI:
        return None
    ma_c, pomin = False, False
    for a in args:
        if pomin:  # argument opcji `-o`/`-O`/`+o`/`+O` (np. `bash -o pipefail -c '…'`)
            pomin = False
            continue
        if a in _PRZEKIEROWANIA:
            return None
        if a in ("-o", "-O", "+o", "+O"):
            pomin = True
        elif a.startswith("-") and not a.startswith("--") and len(a) > 1:
            ma_c = ma_c or "c" in a[1:]
        elif a.startswith("--"):
            continue
        elif ma_c:
            return a
        else:
            return None  # `bash skrypt.sh` — skrypt z pliku, nie z tekstu
    return None


def _cele_sed(args: list[str]) -> list[str]:
    """Pliki zmieniane przez `sed -i` (także `-i.bak`, `-Ei`, `--in-place`); bez `-i` — brak."""
    w_miejscu, jawny_skrypt, pliki, pomin = False, False, [], False
    for a in args:
        if pomin:
            pomin = False
        elif a in _PRZEKIEROWANIA:
            break
        elif a.startswith("--"):
            w_miejscu = w_miejscu or a.startswith("--in-place")
            if a in ("--expression", "--file"):
                jawny_skrypt, pomin = True, True
            elif a.startswith(("--expression=", "--file=")):
                jawny_skrypt = True
        elif a.startswith("-") and len(a) > 1:
            litery = a[1:]
            if litery.startswith("i"):
                w_miejscu = True  # `-i` / `-i.bak`: reszta to przyrostek kopii
                continue
            for k, lit in enumerate(litery):
                if lit == "i":
                    w_miejscu = True
                if lit in "ef":
                    jawny_skrypt = True
                    pomin = k == len(litery) - 1  # `-e skrypt` — argument w następnym słowie
                    break
        else:
            pliki.append(a)
    if not w_miejscu:
        return []
    return pliki if jawny_skrypt else pliki[1:]


def _cele_pobrania(program: str, args: list[str]) -> list[str]:
    """Plik zapisywany przez `curl -o/--output` albo `wget -O/--output-document`."""
    opcje = ("-o", "--output") if program == "curl" else ("-O", "--output-document")
    cele = []
    for j, a in enumerate(args):
        if a in opcje and j + 1 < len(args):
            cele.append(args[j + 1])
        elif a.startswith(opcje[1] + "="):
            cele.append(a.split("=", 1)[1])
        elif len(a) > 2 and a.startswith(opcje[0]) and not a.startswith("--"):
            cele.append(a[2:])
    return [c for c in cele if c != "-"]


_ZMIENIAJACE = {"rm", "rmdir", "unlink", "shred", "truncate", "touch", "chmod", "chown", "chgrp"}
_FIND_WYKONANIE = ("-exec", "-execdir", "-ok", "-okdir")


def _cele_modyfikacji(program: str, args: list[str]) -> list[str]:
    """Ścieżki zmieniane BEZ zapisu treści: usunięcie, skrócenie, prawa, źródła `mv`, dowiązanie
    (`ln`), `dd of=`, `find … -delete`. Liczą się tylko dla `dziennik_audytu_zapis` (R8):
    `zapis_poza_repo` i `zapis_tmp` zostają jak przed zadaniem 029."""
    pliki = [a for a in args if not a.startswith("-") and a not in _PRZEKIEROWANIA]
    if program in _ZMIENIAJACE:
        return pliki
    if program == "mv":
        return pliki[:-1]  # źródła znikają; cel `mv` sprawdza zapis jak dotąd
    if program == "ln":
        return pliki[-1:]
    if program == "dd":
        return [a[3:] for a in args if a.startswith("of=")]
    if program == "find":
        usuwa = "-delete" in args or any(
            a in _FIND_WYKONANIE
            and j + 1 < len(args)
            and args[j + 1].replace("\\", "/").rsplit("/", 1)[-1] in _ZMIENIAJACE | {"mv"}
            for j, a in enumerate(args)
        )
        start = []
        for a in args:
            if a.startswith(("-", "(", "!")):
                break
            start.append(a)
        return start if usuwa else []
    return []


def _przypisania(program: str, args: list[str], slowa: list[str]) -> list[tuple[str, str]]:
    """Proste przypisania (R4): segment z samych `NAZWA=wartość` albo `export NAZWA=wartość`.
    Przypisanie przed poleceniem (`S=x cmd`) działa tylko w `cmd` — pomijane."""
    if program == "" and slowa and all(_PRZYPISANIE.match(s) for s in slowa):
        kandydaci = slowa
    elif program == "export":
        kandydaci = [a for a in args if _PRZYPISANIE.match(a)]
    else:
        return []
    return [(s.split("=", 1)[0], s.split("=", 1)[1]) for s in kandydaci]


def _zapamietaj(zmienne: dict[str, str], przypisania: list[tuple[str, str]]) -> None:
    """Wartość po rozwinięciu znanych zmiennych i `~` na początku. Wartość nieznana (`$(…)`,
    `` ` ``, nieznana `$X`, pusta) usuwa zmienną: zostaje nierozwinięta, czyli „nie wiadomo”."""
    for nazwa, wartosc in przypisania:
        w = _kodowalna(rozwin_zmienne(wartosc, zmienne))
        if w.startswith("~"):
            try:
                w = os.path.expanduser(w)
            except ValueError:  # np. bajt zerowy
                w = ""
        if w and "$" not in w and "`" not in w:
            zmienne[nazwa] = w
        else:
            zmienne.pop(nazwa, None)


def _powloka_ze_stdin(program: str, args: list[str]) -> bool:
    """Powłoka czyta polecenia ze stdin (`bash <<EOF`, `cat <<EOF | sh`, `sh -s`): treść heredoka
    to wtedy polecenia, nie dane (wyjątek od R2)."""
    if program not in POWLOKI:
        return False
    pomin = False
    for a in args:
        if pomin:
            pomin = False
        elif a == "<":  # skrypt z pliku, nie z heredoka
            return False
        elif a in _PRZEKIEROWANIA or a in ("-o", "-O", "+o", "+O"):
            pomin = True
        elif a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
            return False  # `-c '…'` analizuje `polecenie_powloki`
        elif not a.startswith(("-", "+")):
            return False  # `bash skrypt.sh`
    return True


def analizuj_bash(
    wynik: Wynik,
    polecenie: str,
    cwd: str,
    hosty: frozenset[str],
    katalog_audytu: str,
    baza: str | None = None,
    glebokosc: int = 0,
    *,
    sesja: str | None = None,
    agent: str | None = None,
    zmienne: dict[str, str] | None = None,
) -> None:
    """`cwd` = katalog sesji (wyznacza repozytorium); `baza` = bieżący katalog polecenia, zmieniany
    przez `cd` w kolejnych segmentach (przybliżenie: bez rozróżniania podpowłok i `||`).
    `sesja`/`agent` — R5/R6; `zmienne` — przypisania znane z polecenia zewnętrznego (R4).
    Treść heredoków nie trafia do segmentów ani ścieżek (R2); widzi ją tylko heurystyka sieci
    Pythona (`siec_w_segmencie(…, polecenie, …)`) i powłoka czytająca stdin (`bash <<EOF`)."""
    baza = baza or cwd
    zmienne = dict(zmienne or {})
    kontekst = {"sesja": sesja, "agent": agent}
    tekst, ciala = bez_heredokow(polecenie)
    for slowa in segmenty(tekst):
        program, args = program_i_argumenty(slowa)
        _zapamietaj(zmienne, _przypisania(program, args, slowa))
        if program == "cd":
            if "-" not in args:  # `cd -` (poprzedni katalog) — nieznany, baza bez zmian
                try:
                    cel = next((a for a in args if not a.startswith("-")), "~")
                    baza = rozwin(cel, baza, zmienne)
                except ValueError:  # np. bajt zerowy w ścieżce — baza bez zmian
                    pass
            continue
        if glebokosc < MAKS_ZAGNIEZDZENIA:
            wewnetrzne = polecenie_powloki(program, args)
            if wewnetrzne is not None:
                wewnetrzne_ciala = [wewnetrzne]
            elif ciala and _powloka_ze_stdin(program, args):
                wewnetrzne_ciala, ciala = ciala, []
            else:
                wewnetrzne_ciala = []
            for tekst_wewnetrzny in wewnetrzne_ciala:
                analizuj_bash(
                    wynik,
                    tekst_wewnetrzny,
                    cwd,
                    hosty,
                    katalog_audytu,
                    baza,
                    glebokosc + 1,
                    zmienne=zmienne,
                    **kontekst,
                )
        siec = siec_w_segmencie(program, args, polecenie, baza)
        if siec is not None:
            sprawdz_siec(wynik, siec[0], siec[1], hosty)
        cele: list[str] = []
        for j, s in enumerate(slowa[:-1]):
            if s in (">", ">>"):
                cele.append(slowa[j + 1])
        if program == "tee":
            cele += [a for a in args if not a.startswith("-") and a not in (">", ">>")]
        elif program in ("cp", "mv", "install") and len(args) >= 2 and not args[-1].startswith("-"):
            cele.append(args[-1])
        elif program == "sed":
            cele += _cele_sed(args)
        elif program in ("curl", "wget"):
            cele += _cele_pobrania(program, args)
        zmieniane = [m for m in _cele_modyfikacji(program, args) if m not in cele]
        opcje = {"baza": baza, "zmienne": zmienne, **kontekst}
        for cel in cele:
            sprawdz_sciezke(wynik, cel, cwd, katalog_audytu, zapis=True, **opcje)
        for cel in zmieniane:
            sprawdz_sciezke(wynik, cel, cwd, katalog_audytu, zapis=False, modyfikacja=True, **opcje)
        for s in slowa:  # odczyty i inne użycia ścieżek wrażliwych
            if s not in cele and s not in zmieniane and _wyglada_na_sciezke(s):
                sprawdz_sciezke(wynik, s, cwd, katalog_audytu, zapis=False, **opcje)


def _tekst_albo_none(wartosc: object) -> str | None:
    return wartosc if isinstance(wartosc, str) and wartosc else None


def analizuj(
    dane: dict, hosty: frozenset[str], katalog_audytu: str
) -> tuple[Wynik, dict[str, str]]:
    wynik, pola = Wynik(), {}
    narzedzie = str(dane.get("tool_name") or "")
    wejscie = dane.get("tool_input")
    wejscie = wejscie if isinstance(wejscie, dict) else {}
    cwd = str(dane.get("cwd") or os.getcwd())
    kontekst = {  # R5: scratchpad tej sesji; R6: sesja główna (bez `agent_id`) czy subagent
        "sesja": _tekst_albo_none(dane.get("session_id")),
        "agent": _tekst_albo_none(dane.get("agent_id")),
    }
    if narzedzie == "Bash":
        polecenie = str(wejscie.get("command") or "")
        pola["polecenie"] = maskuj(polecenie)
        analizuj_bash(wynik, polecenie, cwd, hosty, katalog_audytu, **kontekst)
    elif narzedzie == "WebFetch":
        url = str(wejscie.get("url") or "")
        pola["url"] = maskuj(url)
        znalezione = hosty_z_tekstu(url)
        sprawdz_siec(wynik, bool(znalezione), znalezione, hosty)
    elif narzedzie == "Read" or narzedzie in NARZEDZIA_ZAPISU:
        sciezka = str(wejscie.get(POLE_SCIEZKI.get(narzedzie, "file_path")) or "")
        pola["sciezka"] = maskuj(sciezka)
        if sciezka:
            zapis = narzedzie in NARZEDZIA_ZAPISU
            sprawdz_sciezke(wynik, sciezka, cwd, katalog_audytu, zapis=zapis, **kontekst)
    elif narzedzie in ("Grep", "Glob"):  # przeszukanie katalogu to też odczyt (np. ~/.ssh)
        sciezka = str(wejscie.get("path") or "")
        wzorzec = str(wejscie.get("pattern") or "") if narzedzie == "Glob" else ""
        pola["sciezka"] = maskuj(" ".join(x for x in (sciezka, wzorzec) if x))
        for kandydat in (sciezka, wzorzec):
            if _wyglada_na_sciezke(kandydat):
                sprawdz_sciezke(wynik, kandydat, cwd, katalog_audytu, zapis=False, **kontekst)
    return wynik, pola


# --- dziennik -------------------------------------------------------------------------------------
def katalog_audytu() -> Path:
    return Path(os.environ.get("CLAS5_AUDYT_DIR") or Path.home() / ".clas5_audyt")


def zapisz(rekord: dict, katalog: Path, teraz: datetime) -> Path:
    katalog.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(katalog, 0o700)
    except OSError:
        pass
    plik = katalog / f"{teraz:%Y-%m-%d}.jsonl"
    linia = json.dumps(rekord, ensure_ascii=True, separators=(",", ":")) + "\n"
    flagi = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(plik, flagi, 0o600)
    try:
        os.write(fd, linia.encode("ascii"))
    finally:
        os.close(fd)
    return plik


def _krotki(wartosc: object, limit: int = 200) -> str | None:
    """Identyfikatory Claude Code (sesja, agent, cwd, narzędzie): tylko obcięcie, bez maskowania —
    UUID sesji wygląda jak „długi ciąg z cyframi i literami”, a jest potrzebny do przeglądu."""
    if wartosc in (None, ""):
        return None
    tekst = str(wartosc)
    return tekst if len(tekst) <= limit else tekst[:limit] + "…"


OPIS_FLAGI = {
    F_POSW: "plik z poświadczeniami",
    F_AUDYT_ZAPIS: "zapis do katalogu dziennika audytu",
    F_AUDYT: "odczyt katalogu dziennika audytu",
    F_SIEC: "połączenie z hostem spoza listy config/audyt_hosty.yaml",
    F_SIEC_NIEZNANY: "polecenie sieciowe bez widocznego hosta",
    F_ZAPIS: "zapis poza repozytorium",
    F_TMP: "zapis w katalogu tymczasowym",
}


def powod_odmowy(zablokowane: list[str], wynik: Wynik, narzedzie: str, blokady) -> str:
    """`<flaga>: <powód>; decyzja użytkownika <data>` dla każdej zablokowanej flagi (` | ` między
    nimi). Bez treści plików i sekretów: ścieżka albo host zamaskowane jak w dzienniku."""
    czesci = []
    for flaga in zablokowane:
        opis = OPIS_FLAGI.get(flaga, flaga)
        if flaga in wynik.pierwsze:
            opis += f" ({maskuj(wynik.pierwsze[flaga], 160)})"
        daty = sorted(
            {
                b.decyzja
                for b in blokady
                if b.flaga == flaga
                and b.decyzja
                and (b.narzedzia is None or narzedzie in b.narzedzia)
            }
        )
        decyzja = "decyzja użytkownika" + (" " + ", ".join(daty) if daty else "")
        czesci.append(
            f"{flaga}: {opis} w narzędziu {_krotki(narzedzie, 40)} — blokada hooka audytowego"
            f" (config/audyt_hosty.yaml, ADR-13); {decyzja}"
        )
    return " | ".join(czesci)


def decyzja_odmowy(zablokowane: list[str], wynik: Wynik, narzedzie: str, blokady) -> dict:
    """Wyjście hooka `PreToolUse` z odmową (ADR-13, etap 2, pkt 4; format zgodny z dokumentacją
    hooków Claude Code: `hookSpecificOutput.permissionDecision` = `deny`)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": powod_odmowy(zablokowane, wynik, narzedzie, blokady),
        }
    }


def _zapisz_cicho(rekord: dict, katalog: Path, teraz: datetime) -> Path | None:
    try:
        return zapisz(rekord, katalog, teraz)
    except Exception:  # noqa: BLE001 — brak dziennika nie zatrzymuje sesji ani decyzji
        return None


def przetworz(
    raw: bytes | str,
    katalog: Path | None = None,
    hosty: frozenset[str] | None = None,
    teraz: datetime | None = None,
    blokady: tuple[Blokada, ...] | None = None,
) -> tuple[Path | None, dict | None]:
    """Wejście hooka → (plik dziennika albo None, decyzja odmowy albo None). Nigdy nie rzuca.
    Odmowa tylko po udanej analizie (fail-open); nieudany zapis dziennika jej nie zdejmuje."""
    odmowa = None
    try:
        teraz = teraz or datetime.now(timezone.utc)
        katalog = katalog or katalog_audytu()
        rekord: dict = {"czas": teraz.strftime("%Y-%m-%dT%H:%M:%SZ")}
        try:
            tekst = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
            dane = json.loads(tekst)
        except (ValueError, TypeError, RecursionError):
            dane = None
        if not isinstance(dane, dict):
            rekord["flagi"] = [F_WEJSCIE]
            return _zapisz_cicho(rekord, katalog, teraz), None
        rekord.update(
            sesja=_krotki(dane.get("session_id")),
            agent=_krotki(dane.get("agent_id")),
            agent_typ=_krotki(dane.get("agent_type")),
            cwd=_krotki(dane.get("cwd")),
            narzedzie=_krotki(dane.get("tool_name")),
        )
        try:
            lista = hosty if hosty is not None else wczytaj_hosty()
            katalog_r = os.path.realpath(str(katalog))
            wynik, pola = analizuj(dane, lista, katalog_r)
            rekord.update(pola)
            rekord["flagi"] = sorted(wynik.flagi)
            if wynik.hosty:
                rekord["hosty_spoza_listy"] = wynik.hosty
            if wynik.sciezki:
                rekord["sciezki_oznaczone"] = [maskuj(s) for s in wynik.sciezki]
            # bez flag nie ma czego blokować — konfiguracji nie trzeba czytać (większość wywołań)
            reguly = (blokady if blokady is not None else wczytaj_blokady()) if wynik.flagi else ()
            narzedzie = str(dane.get("tool_name") or "")
            zablokowane = zablokowane_flagi(wynik.flagi, narzedzie, reguly)
            if zablokowane:
                odmowa = decyzja_odmowy(zablokowane, wynik, narzedzie, reguly)
                rekord["zablokowano"] = zablokowane
        except Exception as blad:  # noqa: BLE001 — analiza padła: wiersz powstaje, bez odmowy
            odmowa = None
            rekord.pop("zablokowano", None)
            rekord["flagi"] = [F_BLAD]
            rekord["blad"] = type(blad).__name__
        return _zapisz_cicho(rekord, katalog, teraz), odmowa
    except Exception:  # noqa: BLE001 — hook NIE MOŻE przerwać sesji, patrz docstring
        return None, odmowa


def hook_main(
    raw: bytes | str,
    katalog: Path | None = None,
    hosty: frozenset[str] | None = None,
    teraz: datetime | None = None,
    blokady: tuple[Blokada, ...] | None = None,
) -> Path | None:
    """Wejście hooka → jeden wiersz dziennika. Nigdy nie rzuca wyjątku; zwraca ścieżkę pliku
    (decyzję odmowy zwraca `przetworz`)."""
    return przetworz(raw, katalog, hosty, teraz, blokady)[0]


def main(argv: list[str] | None = None) -> int:
    try:
        argv = sys.argv[1:] if argv is None else argv
        if argv[:1] == ["hook"]:
            _, odmowa = przetworz(sys.stdin.buffer.read())
            if odmowa is not None:  # ASCII: stdout w cp1252 (Windows) nie wywróci decyzji
                wyjscie = json.dumps(odmowa, ensure_ascii=True) + "\n"
                sys.stdout.buffer.write(wyjscie.encode("ascii"))
                sys.stdout.buffer.flush()
    except Exception:  # noqa: BLE001
        pass
    return 0  # zawsze 0; odmowę niesie JSON na stdout (ADR-13, etap 2)


if __name__ == "__main__":
    raise SystemExit(main())
