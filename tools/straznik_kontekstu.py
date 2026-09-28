"""
straznik_kontekstu.py

Strażnik kontekstu Claude Code (`docs/rag/12`, sekcja „Zarządzanie kontekstem”). Każde wywołanie
modelu czyta cały kontekst rozmowy, więc długa sesja drożeje z każdym krokiem; zasada „nowa sesja
na zadanie” istniała, ale nic jej nie pilnowało w trakcie tury. Jeden moduł, trzy wejścia:

- hook `PostToolUse` — po każdym narzędziu GŁÓWNEJ sesji czyta z zapisu rozmowy (transcript JSONL)
  rozmiar kontekstu ostatniego wywołania modelu. Przy `PROG_UWAGI` jednorazowa uwaga dla Claude:
  domknij etap, następny duży krok w subagencie albo w nowej sesji. Przy `PROG_PRZEKAZANIA`
  polecenie: nie zaczynaj nowego etapu, zapisz notę przekazania, poproś użytkownika o `/clear`
  (plus komunikat dla użytkownika), ponawiane co `KROK_PRZYPOMNIENIA`. Bez blokady narzędzi —
  przerwanie analizy w połowie psułoby jakość;
- hook `UserPromptSubmit` — ponad `PROG_UWAGI` przy każdym poleceniu użytkownika przypomnienie,
  że pytanie niezwiązane z bieżącym zadaniem idzie do nowej sesji;
- linia statusu — model, wysiłek i rozmiar kontekstu, kolor według progu; „cache zimny”, gdy cache
  głównej rozmowy wygasł (pole `prompt_cache` od Claude Code). Claude Code sam uruchamia linię
  statusu w chwili `expires_at` ciepłego cache, także podczas bezczynności (dokumentacja statusline,
  kod 2.1.282), więc napis pojawia się, zanim użytkownik wyśle wiadomość — następna przepisałaby
  cały kontekst do cache po podwójnej cenie (docs/rag/12, T7).

Rozmiar kontekstu = wejście + zapis cache + odczyt cache (jak `context_size` w
`zuzycie_tokenow.py`). Narzędzia subagentów (pole `agent_id` w danych hooka) są pomijane: ich
hook dostaje ścieżkę zapisu GŁÓWNEJ sesji, więc uwaga trafiłaby do subagenta, który nie może
zrobić `/clear` (sprawdzone na Claude Code 2.1.282).

„Jednorazowo” pilnują pliki-znaczniki w `<temp>/clas5-straznik/<sesja>/`, tworzone atomowo (tryb
„x”), więc równoległe narzędzia nie zdublują uwagi. Spadek kontekstu poniżej `PROG_UWAGI`
(streszczenie rozmowy) kasuje znaczniki — progi działają od nowa.

Ta sama zasada bezpieczeństwa co w `skill_audit.py` i `frozen_guard.py`: hook NIGDY nie przerywa
sesji przez własny błąd — zły JSON, brak zapisu rozmowy, wyjątek → cisza i kod 0.

Użycie:
    py tools/straznik_kontekstu.py hook                  # tryb hooka (JSON zdarzenia na stdin)
    py tools/straznik_kontekstu.py status                # linia statusu (JSON Claude Code na stdin)
    py tools/straznik_kontekstu.py pomiar <zapis.jsonl>  # kontekst ostatniego wywołania modelu
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

# Progi w JEDNYM miejscu (docs/rag/12); linia statusu i oba hooki czytają je stąd.
PROG_UWAGI = 150_000  # tokenów: domknij etap, następny duży krok w subagencie / nowej sesji
PROG_PRZEKAZANIA = 250_000  # nota przekazania + prośba o /clear, bez nowego etapu
KROK_PRZYPOMNIENIA = 50_000  # ponad progiem przekazania polecenie wraca co tyle tokenów

BLOK = 64 * 1024  # zapis rozmowy czytamy od końca, blokami
MAKS_WSTECZ = 16 * 1024 * 1024  # dalej wstecz nie szukamy — hook ma być szybki
KATALOG_STANU = Path(tempfile.gettempdir()) / "clas5-straznik"

POLA_KONTEKSTU = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
KOLORY = ("\033[32m", "\033[33m", "\033[31m")  # zielony / żółty / czerwony
RESET = "\033[0m"


def tys(tokeny: int) -> int:
    return round(tokeny / 1000)


def kontekst(usage: dict) -> int:
    """Tokeny, które model przeczytał w wywołaniu: wejście + zapis cache + odczyt cache."""
    return sum(int(usage.get(pole) or 0) for pole in POLA_KONTEKSTU)


def poziom(tokeny: int) -> int:
    """0 = spokój; 1 = uwaga; 2, 3, … = przekazanie i kolejne przypomnienia co KROK."""
    if tokeny < PROG_UWAGI:
        return 0
    if tokeny < PROG_PRZEKAZANIA:
        return 1
    return 2 + (tokeny - PROG_PRZEKAZANIA) // KROK_PRZYPOMNIENIA


def _kontekst_wpisu(linia: bytes) -> int | None:
    """Kontekst z wpisu odpowiedzi modelu głównej sesji; None dla każdego innego wpisu."""
    if b'"usage"' not in linia or b'"assistant"' not in linia:
        return None  # szybkie odrzucenie: wyniki narzędzi bywają wielkie, nie parsujemy ich
    try:
        wpis = json.loads(linia)
    except ValueError:
        return None  # m.in. linia właśnie dopisywana na końcu pliku
    if not isinstance(wpis, dict) or wpis.get("type") != "assistant" or wpis.get("isSidechain"):
        return None
    wiadomosc = wpis.get("message")
    if not isinstance(wiadomosc, dict) or wiadomosc.get("model") == "<synthetic>":
        return None
    usage = wiadomosc.get("usage")
    return (kontekst(usage) or None) if isinstance(usage, dict) else None


def kontekst_z_zapisu(sciezka: str | Path, blok: int = BLOK, maks: int = MAKS_WSTECZ) -> int | None:
    """Kontekst ostatniego wywołania modelu w zapisie rozmowy (None: brak pliku / brak wywołań)."""
    if not isinstance(sciezka, (str, Path)) or not str(sciezka):
        return None  # liczba otworzyłaby cudzy deskryptor pliku, a `with` by go zamknął
    try:
        with open(sciezka, "rb") as fh:
            koniec = fh.seek(0, os.SEEK_END)
            poz, ogon = (
                koniec,
                b"",
            )  # ogon = początek linii, która zaczyna się we wcześniejszym bloku
            while poz > 0 and koniec - poz < maks:
                n = min(blok, poz)
                poz -= n
                fh.seek(poz)
                linie = (fh.read(n) + ogon).split(b"\n")
                ogon = linie.pop(0) if poz > 0 else b""
                for linia in reversed(linie):
                    wynik = _kontekst_wpisu(linia)
                    if wynik:
                        return wynik
    except (OSError, ValueError):
        return None
    return None


def katalog_stanu(sesja: str, baza: Path | None = None) -> Path:
    return (baza or KATALOG_STANU) / (re.sub(r"[^A-Za-z0-9_-]", "_", sesja) or "bez-sesji")


def pierwszy_raz(katalog: Path, poz: int) -> bool:
    """True, gdy poziom `poz` padł pierwszy raz od startu sesji lub od spadku poniżej uwagi."""
    if poz <= 0:
        if katalog.is_dir():  # streszczenie rozmowy zbiło kontekst — progi działają od nowa
            for znacznik in katalog.glob("poziom-*"):
                znacznik.unlink(missing_ok=True)
        return False
    katalog.mkdir(parents=True, exist_ok=True)
    try:
        with open(katalog / f"poziom-{poz}", "x"):  # atomowo: równoległe narzędzia nie dublują
            pass
    except FileExistsError:
        return False
    for nizszy in range(1, poz):  # skok 0 → 2 nie odpala później zaległej „uwagi”
        (katalog / f"poziom-{nizszy}").touch()
    return True


def uwaga_dla_claude(tokeny: int, poz: int) -> str:
    naglowek = f"Strażnik kontekstu (docs/rag/12): kontekst tej sesji ma {tys(tokeny)} tys. tokenów"
    if poz == 1:
        return (
            f"{naglowek} (próg uwagi {tys(PROG_UWAGI)} tys.). Domknij bieżący etap. Następny duży "
            "krok — duże pliki, przegląd, długie odczyty — zleć subagentowi, który odda ścieżkę "
            "i krótkie podsumowanie. Nową sesję proponuj tylko przy nowym, niezwiązanym zadaniu (T2). Rozpoczętej "
            "analizy nie przerywaj w połowie."
        )
    return (
        f"{naglowek} (próg przekazania {tys(PROG_PRZEKAZANIA)} tys.). Nie zaczynaj nowego etapu. "
        "Dokończ bieżący krok, zapisz notę przekazania w pamięci projektu (plik "
        "nota-przekazania.md + wiersz w MEMORY.md; ≤ 15 linii: co zrobione, pliki, decyzje, "
        "następny krok) i poproś użytkownika o /clear."
    )


def komunikat_dla_uzytkownika(tokeny: int) -> str:
    return (
        f"Kontekst sesji: {tys(tokeny)} tys. tokenów (próg {tys(PROG_PRZEKAZANIA)} tys.). "
        "Claude zapisze notę przekazania — potem wpisz /clear."
    )


def przypomnienie_na_starcie(tokeny: int) -> str:
    tekst = (
        f"Strażnik kontekstu (docs/rag/12): kontekst tej sesji ma {tys(tokeny)} tys. tokenów. "
        "Jeśli to polecenie nie dotyczy bieżącego zadania, zaproponuj użytkownikowi nową sesję "
        "(/clear; wiedza żyje w runs/INDEX.md, STATUS.md i pamięci) zamiast prowadzić je tutaj."
    )
    if tokeny >= PROG_PRZEKAZANIA:
        tekst += " Kontekst jest ponad progiem przekazania: bez nowego etapu — nota przekazania i /clear."
    return tekst


def _dane(raw: bytes | str) -> dict:
    tekst = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    dane = json.loads(tekst) if tekst.strip() else {}
    return dane if isinstance(dane, dict) else {}


def hook_main(raw: bytes | str, baza_stanu: Path | None = None) -> str:
    """Wejście hooka → tekst na stdout (JSON albo pusty). Nigdy nie rzuca wyjątku."""
    try:
        dane = _dane(raw)
        zdarzenie = dane.get("hook_event_name")
        if dane.get("agent_id") or zdarzenie not in ("PostToolUse", "UserPromptSubmit"):
            return ""
        tokeny = kontekst_z_zapisu(dane.get("transcript_path") or "")
        if not tokeny:
            return ""
        poz, wyjscie = poziom(tokeny), {}
        if zdarzenie == "UserPromptSubmit":
            if poz == 0:
                return ""
            tekst = przypomnienie_na_starcie(tokeny)
        else:
            katalog = katalog_stanu(str(dane.get("session_id") or ""), baza_stanu)
            if not pierwszy_raz(katalog, poz):
                return ""
            tekst = uwaga_dla_claude(tokeny, poz)
            if poz >= 2:
                wyjscie["systemMessage"] = komunikat_dla_uzytkownika(tokeny)
        wyjscie["hookSpecificOutput"] = {"hookEventName": zdarzenie, "additionalContext": tekst}
        return json.dumps(wyjscie, ensure_ascii=True)  # ASCII: bez kłopotu ze stroną kodową Windows
    except Exception:  # noqa: BLE001 — hook NIE MOŻE przerwać sesji, patrz docstring
        return ""


def cache_zimny(dane: dict, teraz: float | None = None) -> bool:
    """True, gdy cache głównej rozmowy wygasł: `prompt_cache.warm` fałszywe albo minął `expires_at`
    (sekundy epoki). Bez pola (przed pierwszą odpowiedzią modelu, Claude Code < 2.1.251) albo bez
    obserwacji cache (`caching_observed` fałszywe — dostawca go nie raportuje) → False."""
    stan = dane.get("prompt_cache")
    if not isinstance(stan, dict) or stan.get("caching_observed") is False:
        return False
    if stan.get("warm") is False:
        return True
    wygasa = stan.get("expires_at")
    if isinstance(wygasa, (int, float)) and not isinstance(wygasa, bool):
        return (time.time() if teraz is None else teraz) >= wygasa
    return False


def linia_statusu(raw: bytes | str) -> str:
    """Model (wysiłek) · kontekst N tys. — kolor i podpowiedź według progu; · cache zimny."""
    try:
        dane = _dane(raw)
    except ValueError:
        dane = {}
    model = dane.get("model")
    if isinstance(model, dict):
        nazwa = str(model.get("display_name") or model.get("id") or "")
    else:
        nazwa = model if isinstance(model, str) else ""
    wysilek = dane.get("effort")
    wysilek = wysilek.get("level") if isinstance(wysilek, dict) else wysilek
    if nazwa and isinstance(wysilek, str) and wysilek:
        nazwa += f" ({wysilek})"
    okno = dane.get("context_window") if isinstance(dane.get("context_window"), dict) else {}
    uzycie = okno.get("current_usage")
    tokeny = kontekst(uzycie) if isinstance(uzycie, dict) else 0
    if not tokeny and dane.get("transcript_path"):
        tokeny = kontekst_z_zapisu(dane["transcript_path"]) or 0
    if not tokeny:
        opis = "kontekst —"
    else:
        poz = min(poziom(tokeny), 2)
        podpowiedz = (
            "",
            f" · ≥ {tys(PROG_UWAGI)}: domknij etap",
            f" · ≥ {tys(PROG_PRZEKAZANIA)}: nota przekazania i /clear",
        )[poz]
        opis = f"{KOLORY[poz]}kontekst {tys(tokeny)} tys.{podpowiedz}{RESET}"
    if cache_zimny(dane):
        opis += f" · {KOLORY[1]}cache zimny: nowa sesja{RESET}"
    return f"{nazwa} · {opis}" if nazwa else opis


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    tryb = argv[0] if argv else ""
    if tryb == "hook":
        wynik = hook_main(sys.stdin.buffer.read())
    elif tryb == "status":
        try:
            wynik = linia_statusu(sys.stdin.buffer.read())
        except Exception:  # noqa: BLE001 — linia statusu też nie może psuć sesji
            wynik = "kontekst —"
    elif tryb == "pomiar" and len(argv) == 2:
        tokeny = kontekst_z_zapisu(argv[1])
        wynik = (
            f"{tokeny} (poziom {poziom(tokeny)})\n" if tokeny else "brak wywołań modelu w zapisie\n"
        )
    else:
        print("tryby: hook | status | pomiar <zapis.jsonl>", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(wynik.encode("utf-8"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
