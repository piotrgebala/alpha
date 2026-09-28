"""pomiar_wysilku.py — T5 z docs/rag/12: koszt i poprawność stałych zadań przy różnym wysiłku i modelu.

Po co (pkt B1 noty, decyzja użytkownika 2026-09-28 „T5 w nowej sesji”): czy do danego typu pracy
wystarcza niższy wysiłek (effort) albo tańszy model — przy tej samej poprawności. Rozumowanie liczy
się jak wyjście (najdroższy rodzaj tokenów), więc wysiłek może zmieniać koszt wielokrotnie.

Przebieg = `claude -p` z jednym z trzech zadań ze znaną odpowiedzią; klucz odpowiedzi jest w tym pliku,
zapisany przed pomiarem. Koszt = `total_cost_usd` z wyniku JSON (T1: pole rozkłada się co do cyfry na
tokeny × cena katalogowa). Poprawność ocenia program: Z1 i Z3 po ostatniej linii „WYNIK:”, Z2 po stanie
katalogu (testy ukryte przechodzą, dopisany test regresji łapie błąd, dawne testy zostały).

Kolejność: najpierw rozgrzewki bez oceny — każda konfiguracja (model × wysiłek × zestaw narzędzi) raz,
bo pierwsze wywołanie płaci zapis prefiksu do cache, a wysiłek zmienia część prefiksu (sonda 28.09:
ok. 3,7 tys. tokenów). Potem bloki zadanie × powtórzenie; w bloku konfiguracje w losowej kolejności
(ziarno stałe), żeby przerwa między użyciami tej samej konfiguracji nie przekraczała życia cache (1 h).
Prompt zadania kończy znacznik przebiegu: wspólny zostaje prompt systemowy z rozgrzewki, a rozmowa
jest za każdym razem nowa (seria 1: powtórzenie czytało z cache rozmowę poprzedniego).
Wyniki dopisywane do pliku JSONL; przerwany pomiar wznawia się od brakujących przebiegów. Ponawiana
jest tylko awaria bez wyniku JSON albo przejściowy błąd API (najwyżej 2 razy); wynik JSON z błędem
(limit budżetu, limit tur) i limit czasu rozstrzygają przebieg jako niepoprawny.

    .venv/bin/python tools/pomiar_wysilku.py kopia --zrodlo /home/dantey1/alpha --cel KOPIA
    .venv/bin/python tools/pomiar_wysilku.py sprawdz --repo KOPIA
    .venv/bin/python tools/pomiar_wysilku.py plan
    .venv/bin/python tools/pomiar_wysilku.py uruchom --wyniki W.jsonl --repo KOPIA --piaskownica KATALOG
    .venv/bin/python tools/pomiar_wysilku.py podsumuj --wyniki W.jsonl

`--repo` to KOPIA z podkomendy `kopia`: klon samej gałęzi master bez zdalnego `origin`. Równoległa
praca w repo zmienia stan gita w prompcie systemowym i unieważnia cache, a klucze odpowiedzi (ten
plik, pre-rejestracja w docs/rag/12) nie mogą być w zasięgu modelu — seria 1 (git worktree na
commicie pre-rejestracji) je miała. Strażnik `sprawdz_kopie_repo` pilnuje tego przed każdym
przebiegiem w kopii. Na serwerze brakuje polecenia `py` (CLAUDE.md je zakłada) — przebiegi dostają
podkładkę `py` → python z venv, żeby brak polecenia nie dokładał prób i błędów.
Skrypt jest neutralnym reporterem: zalecenie podpisuje Claude w docs/rag/12.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MODELE = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5"}
KONFIGURACJE = [
    ("opus", "low"),
    ("opus", "medium"),
    ("opus", "high"),
    ("opus", "xhigh"),
    ("opus", "max"),
    ("sonnet", "low"),
    ("sonnet", "high"),
]
ODNIESIENIE = ("opus", "max")  # ustawienie głównej sesji 28.09 (effort max w zapisie rozmowy)
POWTORZENIA = 2
ZIARNO = 20260928
PROG_TANIEJ = 0.70  # reguła T5: zalecenie, gdy koszt ≥ 30 % niższy przy tej samej poprawności
LIMIT_PRZEBIEGU_USD = 3.0
LIMIT_SERII_USD = 30.0
LIMIT_CZASU_S = 1200
ROZGRZEWKA = "Odpowiedz jednym słowem: OK"
PONOWIENIA = 2  # awaria bez wyniku JSON albo przejściowy błąd API — najwyżej tyle ponowień
BLAD_CZASU = "przekroczony czas"
BLAD_JSON = "wyjście nie jest JSON"
# Koniec promptu każdego zadania (nie rozgrzewki): prefiks rozmowy unikalny dla przebiegu
ZNACZNIK_PRZEBIEGU = "\n\n(Identyfikator techniczny przebiegu, bez znaczenia dla zadania: {nonce})"
# Strażnik kopii: narzędzie T5 i znaczniki klucza odpowiedzi. Dobór sprawdzony 28.09: każdy jest
# w drzewie 9a42f84 (worktree serii 1), żadnego nie ma w master 2ee7f1b.
PLIK_NARZEDZIA = "tools/pomiar_wysilku.py"
ZNACZNIKI_KLUCZA = (
    "KLUCZ_Z1",
    "KLUCZ_Z3",
    "pomiar_wysilku",
    "Pre-rejestracja T5",
    "metrics.py:648",
)
# Odpowiedź z takim napisem = model widział narzędzie T5, klucze albo repo spoza kopii (skażony)
ZNACZNIKI_SKAZENIA = ("pomiar_wysilku", "KLUCZ", "t5_repo", "/home/dantey1/alpha", "12_zuzycie")
ETYKIETY_BLEDOW = {
    "error_max_budget_usd": "limit budżetu",
    "error_max_turns": "limit tur",
    "error_during_execution": "błąd wykonania",
}

_ZAWSZE_ZABRONIONE = ["Skill", "Agent", "Task", "NotebookEdit", "WebFetch", "WebSearch"]
_CZYTANIE = ["Read", "Grep", "Glob"] + [
    f"Bash({p} *)"
    for p in (
        "grep",
        "rg",
        "cat",
        "head",
        "tail",
        "sed -n",
        "ls",
        "find",
        "wc",
        "git grep",
        "git log",
    )
]
NARZEDZIA = {
    # Z1 i Z3: repo tylko do odczytu, Python do rachunków; ten sam zestaw = wspólny prefiks cache
    "odczyt": {
        "tryb": "default",
        "dozwolone": _CZYTANIE + ["Bash(py *)", "Bash(python3 *)", "Bash(python *)"],
        "zabronione": _ZAWSZE_ZABRONIONE + ["Edit", "Write"],
    },
    # Z2: poprawka w piaskownicy
    "zapis": {
        "tryb": "acceptEdits",
        "dozwolone": _CZYTANIE
        + ["Edit", "Write"]
        + [
            f"Bash({p} *)"
            for p in ("python3 -m pytest", "python -m pytest", "py -m pytest", "pytest")
        ],
        "zabronione": _ZAWSZE_ZABRONIONE,
    },
}

ZADANIA = {
    "Z1": {
        "typ": "wskazanie miejsca w repo",
        "narzedzia": "odczyt",
        "prompt": (
            "Znajdź w tym repozytorium funkcję, która liczy, ile TRANSAKCJI da okno testowe (a nie ile "
            "ma świec). Podaj plik i numer linii jej definicji, nazwę funkcji oraz nazwę argumentu "
            "oznaczającego udział świec, na których model odmówi kierunku. Niczego nie zmieniaj. "
            "Ostatnia linia odpowiedzi ma mieć dokładnie format: WYNIK: <ścieżka względem katalogu "
            "repo>:<numer linii>; <nazwa funkcji>; <nazwa argumentu>"
        ),
    },
    "Z2": {
        "typ": "mała poprawka z testem regresji",
        "narzedzia": "zapis",
        "prompt": (
            "Zgłoszenie błędu: w pliku miary.py wywołanie expected_trades(1000, 0.8) zwraca 800, a przy "
            "abstynencji 80 % powinno zostać 200 transakcji. Popraw błąd w kodzie (nie zmieniaj innych "
            "funkcji), dopisz test regresji do tests/test_miary.py i uruchom testy poleceniem "
            "`python3 -m pytest -q`."
        ),
    },
    "Z3": {
        "typ": "rachunek z metodologii (mierzalność)",
        "narzedzia": "odczyt",
        "prompt": (
            "Policz mierzalność hipotezy według zasady 18 z CLAUDE.md, korzystając z funkcji "
            "w backtest/metrics.py. Dane: zakładana trafność 0,56; koszt round-trip C = 0,12 % "
            "i symetryczna bariera B = 1,5 % (próg opłacalności p* z break_even_hit_rate); 20 000 świec "
            "OOS, abstynencja 0,85, admission_rate 0,6. Podaj p*, oczekiwaną liczbę transakcji n, "
            "p_detectable i werdykt. Niczego nie zmieniaj w repozytorium. Ostatnia linia odpowiedzi ma "
            "mieć dokładnie format: WYNIK: p*=<ułamek dziesiętny>; n=<liczba>; "
            "p_det=<ułamek dziesiętny>; werdykt=<MIERZALNA albo NIEMIERZALNA>"
        ),
    },
}

# Klucze odpowiedzi (policzone przed pomiarem funkcjami repo, commit pre-rejestracji w docs/rag/12)
KLUCZ_Z1 = {
    "sciezka": "backtest/metrics.py",
    "linie": (648, 652),  # sygnatura `def expected_trades(` zajmuje linie 648–652
    "funkcja": "expected_trades",
    "argument": "abstention_rate",
}
KLUCZ_Z3 = {"p": 0.54, "n": 1800.0, "p_det": 0.563098, "werdykt": "NIEMIERZALNA"}
TOLERANCJA_Z3 = {"p": 0.0005, "n": 0.5, "p_det": 0.0005}

MIARY_Z_BLEDEM = '''"""Miary mierzalności hipotezy (uproszczona kopia funkcji z projektu)."""

import math

Z_95 = 1.959963984540054


def break_even_hit_rate(cost_fraction: float, barrier_fraction: float) -> float:
    """Trafność potrzebna do wyjścia na zero przy symetrycznych barierach ±B i koszcie C:
    p = 0,5 · (1 + C / B). NaN dla niedodatniej bariery."""
    if barrier_fraction is None or math.isnan(barrier_fraction) or barrier_fraction <= 0:
        return float("nan")
    return 0.5 * (1.0 + cost_fraction / barrier_fraction)


def wald_half_width(n_trades: float, z: float = Z_95) -> float:
    """Połowa szerokości przedziału ufności dla trafności, konserwatywnie przy p = 0,5:
    z · sqrt(0,25 / n). NaN dla n <= 0."""
    if n_trades <= 0:
        return float("nan")
    return z * math.sqrt(0.25 / n_trades)


def expected_trades(n_rows_oos: int, abstention_rate: float, admission_rate: float = 1.0) -> float:
    """Ile TRANSAKCJI da okno testowe: świece, na których model NIE odmówi kierunku, razy
    przeżywalność pozostałych bramek. NaN dla argumentów spoza zakresu."""
    if n_rows_oos < 0 or not 0.0 <= abstention_rate <= 1.0 or not 0.0 <= admission_rate <= 1.0:
        return float("nan")
    return n_rows_oos * abstention_rate * admission_rate


def measurability(assumed_hit_rate: float, break_even_p: float, n_trades_expected: float) -> str:
    """MIERZALNA, gdy zakładana trafność przekracza próg opłacalności o więcej niż połowę
    szerokości przedziału ufności przy oczekiwanej liczbie transakcji."""
    p_detectable = break_even_p + wald_half_width(n_trades_expected)
    return "MIERZALNA" if assumed_hit_rate > p_detectable else "NIEMIERZALNA"
'''

TEST_MIARY = """import math

import pytest

from miary import break_even_hit_rate, expected_trades, measurability, wald_half_width


def test_break_even_symetryczne_bariery():
    assert break_even_hit_rate(0.0012, 0.015) == pytest.approx(0.54)


def test_break_even_bez_bariery_to_nan():
    assert math.isnan(break_even_hit_rate(0.001, 0.0))


def test_wald_half_width_400():
    assert wald_half_width(400) == pytest.approx(0.049, abs=1e-4)


def test_expected_trades_polowa_abstynencji():
    assert expected_trades(1000, 0.5) == pytest.approx(500)


def test_measurability_duza_proba():
    assert measurability(0.56, 0.54, 20_000) == "MIERZALNA"
"""

PYPROJECT = """[tool.pytest.ini_options]
pythonpath = ["."]
"""

TEST_UKRYTY = """import math

import pytest

from miary import break_even_hit_rate, expected_trades, measurability, wald_half_width


def test_zgloszenie():
    assert expected_trades(1000, 0.8) == pytest.approx(200)


def test_z_admission():
    assert expected_trades(20_000, 0.85, 0.6) == pytest.approx(1800)


def test_brzegi_expected_trades():
    assert expected_trades(1000, 0.0) == pytest.approx(1000)
    assert expected_trades(1000, 1.0) == pytest.approx(0)
    assert math.isnan(expected_trades(1000, 1.5))
    assert math.isnan(expected_trades(-1, 0.5))
    assert math.isnan(expected_trades(1000, 0.5, 1.2))


def test_pozostale_funkcje_bez_zmian():
    assert break_even_hit_rate(0.0012, 0.015) == pytest.approx(0.54)
    assert math.isnan(break_even_hit_rate(0.001, -0.01))
    assert wald_half_width(1800) == pytest.approx(0.0230984, abs=1e-6)
    assert math.isnan(wald_half_width(0))
    assert measurability(0.56, 0.54, 1800) == "NIEMIERZALNA"
    assert measurability(0.57, 0.54, 1800) == "MIERZALNA"
"""


def plan(ziarno: int = ZIARNO) -> list[dict]:
    """Kolejność przebiegów: rozgrzewki, potem bloki zadanie × powtórzenie (konfiguracje losowo)."""
    rng = random.Random(ziarno)
    rozgrzewki = [
        {"id": f"R-{nz}-{m}-{w}", "zadanie": None, "narzedzia": nz, "model": m, "wysilek": w}
        for nz in NARZEDZIA
        for m, w in KONFIGURACJE
    ]
    rng.shuffle(rozgrzewki)
    wpisy = [dict(r, powtorzenie=0) for r in rozgrzewki]
    for powt in range(1, POWTORZENIA + 1):
        for zad, z in ZADANIA.items():
            blok = list(KONFIGURACJE)
            rng.shuffle(blok)
            wpisy += [
                {
                    "id": f"{zad}-{m}-{w}-{powt}",
                    "zadanie": zad,
                    "narzedzia": z["narzedzia"],
                    "model": m,
                    "wysilek": w,
                    "powtorzenie": powt,
                }
                for m, w in blok
            ]
    return wpisy


def komenda(prompt: str, model: str, wysilek: str, narzedzia: str) -> list[str]:
    n = NARZEDZIA[narzedzia]
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        MODELE[model],
        "--effort",
        wysilek,
        "--output-format",
        "json",
        "--no-session-persistence",
        "--max-budget-usd",
        str(LIMIT_PRZEBIEGU_USD),
        "--permission-mode",
        n["tryb"],
        "--allowedTools",
        *n["dozwolone"],
        "--disallowedTools",
        *n["zabronione"],
    ]


def zbuduj_piaskownice(katalog: Path) -> None:
    """Świeża piaskownica Z2 zawsze pod TĄ SAMĄ ścieżką (ścieżka jest w prompcie systemowym → cache)."""
    if katalog.exists():
        shutil.rmtree(katalog)
    (katalog / "tests").mkdir(parents=True)
    (katalog / "miary.py").write_text(MIARY_Z_BLEDEM, encoding="utf-8")
    (katalog / "tests" / "test_miary.py").write_text(TEST_MIARY, encoding="utf-8")
    (katalog / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")


class KopiaNieczysta(ValueError):
    """Kopia repo nie nadaje się do przebiegu — seria staje; kopii nikt nie czyści samoczynnie."""


def _git(katalog: Path, *args: str) -> subprocess.CompletedProcess:
    """git w katalogu, bez opcjonalnych blokad (`status` nie zapisuje indeksu — strażnik tylko czyta)."""
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(katalog), *args],
        capture_output=True,
        text=True,
    )


def sprawdz_kopie_repo(katalog: Path, historia: bool = False) -> None:
    """Strażnik kopii repo — przed każdym przebiegiem w kopii. Wszystkie znalezione problemy naraz
    w KopiaNieczysta, bez sprzątania (trzeba zobaczyć, co zostało i skąd):
    (i) klucz Z1 — linia 648 backtest/metrics.py zaczyna się od `def expected_trades(`;
    (ii) w drzewie roboczym nie ma narzędzia T5 ani znaczników klucza — pliki śledzone, nieśledzone
    i ignorowane (seria 1: 11 z 14 odpowiedzi Z1 wymienia to narzędzie);
    (iii) z `historia=True` (raz na starcie serii): historia kopii nigdy nie miała narzędzia T5,
    więc `git log` / `git show` nie dosięgną klucza;
    (iv) `git status --porcelain` pusty — model ma `Bash(python3 *)` i może zostawić plik."""
    problemy = []
    metryki = katalog / KLUCZ_Z1["sciezka"]
    linie = metryki.read_text(encoding="utf-8").splitlines() if metryki.is_file() else []
    nr = KLUCZ_Z1["linie"][0]
    if len(linie) < nr or not linie[nr - 1].startswith(f"def {KLUCZ_Z1['funkcja']}("):
        problemy.append(f"klucz Z1 nie pasuje do kopii repo (linia {nr} {KLUCZ_Z1['sciezka']})")
    if (katalog / PLIK_NARZEDZIA).exists():
        problemy.append(f"w drzewie jest {PLIK_NARZEDZIA} (klucze odpowiedzi T5)")
    znaczniki = [a for z in ZNACZNIKI_KLUCZA for a in ("-e", z)]
    r = _git(katalog, "grep", "--untracked", "--no-exclude-standard", "-I", "-l", "-F", *znaczniki)
    if r.returncode == 0:
        problemy.append(f"znaczniki klucza T5 w drzewie: {', '.join(r.stdout.splitlines()[:5])}")
    elif r.returncode != 1:
        problemy.append(f"git grep nie działa: {r.stderr.strip()[:200]}")
    if historia:
        r = _git(katalog, "log", "--all", "--format=%h", "--", PLIK_NARZEDZIA)
        if r.returncode != 0:
            problemy.append(f"git log nie działa: {r.stderr.strip()[:200]}")
        elif r.stdout.strip():
            problemy.append(
                f"historia kopii ma {PLIK_NARZEDZIA} (commity {', '.join(r.stdout.split()[:3])})"
                " — zrób nową kopię podkomendą `kopia`"
            )
    r = _git(katalog, "status", "--porcelain", "--untracked-files=all")
    if r.returncode != 0:
        problemy.append(f"git status nie działa: {r.stderr.strip()[:200]}")
    elif r.stdout.strip():
        zmiany = "; ".join(r.stdout.splitlines()[:10])
        problemy.append(f"kopia brudna (git status --porcelain): {zmiany}")
    if problemy:
        raise KopiaNieczysta(f"{katalog}: " + " | ".join(problemy))


def kopia(zrodlo: Path, cel: Path) -> str:
    """Czysta kopia repo do Z1/Z3: klon samej gałęzi master (narzędzie T5 i pre-rejestracja żyją
    na gałęzi roboczej) z `--no-local` — obiekty idą protokołem gita, tylko osiągalne z master
    (zwykły klon lokalny dowiązuje cały katalog obiektów źródła, z innymi gałęziami); potem bez
    zdalnego `origin`. Zwraca skrót HEAD kopii. Istniejącego celu nie rusza."""
    if cel.exists():
        raise FileExistsError(
            f"{cel} już istnieje — nie nadpisuję (usuń ręcznie albo podaj inny cel)"
        )
    subprocess.run(
        ["git", "clone", "-q", "--no-local", "--single-branch", "--branch", "master"]
        + [str(zrodlo), str(cel)],
        check=True,
    )
    subprocess.run(["git", "-C", str(cel), "remote", "remove", "origin"], check=True)
    return _git(cel, "rev-parse", "--short", "HEAD").stdout.strip()


def wersja_claude(env: dict) -> str:
    """`claude --version` — raz na starcie `uruchom`; wersja CLI zmienia prompt systemowy i koszty."""
    r = subprocess.run(["claude", "--version"], env=env, capture_output=True, text=True, timeout=60)
    return (r.stdout or r.stderr).strip()


def srodowisko(katalog_bin: Path, python: str = sys.executable) -> dict:
    """PATH: podkładka `py` i katalog Pythona z venv (python3, pytest) przed resztą."""
    katalog_bin.mkdir(parents=True, exist_ok=True)
    py = katalog_bin / "py"
    py.write_text(f'#!/bin/sh\nexec "{python}" "$@"\n', encoding="utf-8")
    py.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(katalog_bin), str(Path(python).parent), env.get("PATH", "")])
    return env


def rekord_z_json(o: dict) -> dict:
    """Koszt, tokeny i stan błędu z wyniku `claude -p --output-format json`. Claude Code 2.1:
    `subtype` = success / error_max_budget_usd / error_max_turns / error_during_execution; przy
    success `is_error` znaczy wiadomość z błędem API (już po ponowieniach samego CLI), a
    `api_error_status` to jej status HTTP (w serii 1 `blad_api` łączyło te przypadki)."""
    u = o.get("usage") or {}
    cc = u.get("cache_creation") or {}
    modele = o.get("modelUsage") or {}
    return {
        "koszt_usd": float(o.get("total_cost_usd") or 0.0),
        "wejscie": int(u.get("input_tokens") or 0),
        "zapis_1h": int(cc.get("ephemeral_1h_input_tokens") or 0),
        "zapis_5m": int(cc.get("ephemeral_5m_input_tokens") or 0),
        "zapis_cache": int(u.get("cache_creation_input_tokens") or 0),
        "odczyt_cache": int(u.get("cache_read_input_tokens") or 0),
        "wyjscie": int(u.get("output_tokens") or 0),
        "wyjscie_wszystkie_modele": sum(int(m.get("outputTokens") or 0) for m in modele.values()),
        "modele": {k: round(float(m.get("costUSD") or 0.0), 6) for k, m in modele.items()},
        "tury": o.get("num_turns"),
        "is_error": bool(o.get("is_error")),
        "podtyp": o.get("subtype"),
        "status_api": o.get("api_error_status"),
        "komunikaty": [str(e)[:300] for e in o.get("errors") or []],
        "odpowiedz": str(o.get("result") or ""),
    }


def linia_wyniku(tekst: str) -> str | None:
    """Treść po „WYNIK:” z OSTATNIEJ takiej linii (bez znaczników Markdown)."""
    for linia in reversed(tekst.splitlines()):
        czysta = linia.replace("`", "").replace("**", "").replace("\\", "").strip()
        m = re.search(r"WYNIK\s*:\s*(.*)$", czysta, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _liczba(s: str) -> float | None:
    """Pierwsza liczba w tekście, zapis polski albo angielski: „0,54”, „1 800”, „1,800”, „1,800.0”,
    „1.800,0”, „56,3 %”, „0.5631 (56,31 %)”. Spacje to zawsze separator tysięcy; gdy są oba znaki
    „,” i „.”, dziesiętny jest ostatni; jeden znak kilka razy = tysiące (grupy po 3 cyfry). None,
    gdy grupy się nie zgadzają („1.2.3”)."""
    m = re.search(r"\d[\d   ,.]*%?", s)
    if not m:
        return None
    t = re.sub(r"[   ]", "", m.group(0)).rstrip(".,")
    procent = t.endswith("%")
    t = t.rstrip("%").rstrip(".,")
    znaki = [c for c in t if c in ",."]
    if len(set(znaki)) == 2:  # 1,800.0 albo 1.800,0
        tysiace = "," if znaki[-1] == "." else "."
        calkowita, _, ulamek = t.rpartition(znaki[-1])
        if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(tysiace)}\d{{3}})+", calkowita):
            return None
        t = f"{calkowita.replace(tysiace, '')}.{ulamek}"
    elif len(znaki) > 1:  # 1,800,000 albo 1.800.000
        if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(znaki[0])}\d{{3}})+", t):
            return None
        t = t.replace(znaki[0], "")
    elif znaki == [","]:
        # 1,800 — separator tysięcy; 0,563 i 56,310 % — przecinek dziesiętny
        tysiace = not procent and re.fullmatch(r"[1-9]\d{0,2},\d{3}", t)
        t = t.replace(",", "" if tysiace else ".")
    try:
        x = float(t)
    except ValueError:
        return None
    return x / 100 if procent else x


def ocen_z1(tekst: str) -> dict:
    w = linia_wyniku(tekst)
    if w is None:
        return {"poprawna": False, "powod": "brak linii WYNIK"}
    czesci = [c.strip() for c in w.split(";")]
    if len(czesci) < 3 or ":" not in czesci[0]:
        return {"poprawna": False, "powod": f"format: {w[:120]}"}
    sciezka, _, linia = czesci[0].rpartition(":")
    sciezka = sciezka.strip()
    funkcja = czesci[1].removesuffix("()").strip()
    argument = czesci[2].strip()
    nr = _liczba(linia)
    lo, hi = KLUCZ_Z1["linie"]
    wynik = {
        "sciezka": sciezka == KLUCZ_Z1["sciezka"] or sciezka.endswith("/" + KLUCZ_Z1["sciezka"]),
        "linia": nr is not None and lo <= nr <= hi,
        "funkcja": funkcja == KLUCZ_Z1["funkcja"],
        "argument": argument == KLUCZ_Z1["argument"],
    }
    return {
        "poprawna": all(wynik.values()),
        "powod": "" if all(wynik.values()) else w[:120],
        **wynik,
    }


def ocen_z3(tekst: str) -> dict:
    w = linia_wyniku(tekst)
    if w is None:
        return {"poprawna": False, "powod": "brak linii WYNIK"}
    pola = {}
    for czesc in w.split(";"):
        klucz, rowna, wartosc = czesc.partition("=")
        if rowna:
            pola[klucz.strip().replace("*", "").lower()] = wartosc.strip()
    wynik = {}
    for k in ("p", "n", "p_det"):
        x = _liczba(pola.get(k, ""))
        wynik[k] = x is not None and abs(x - KLUCZ_Z3[k]) <= TOLERANCJA_Z3[k]
    m = re.search(r"[^\W\d_]+", pola.get("werdykt", ""))  # pierwsze słowo; dopisek dalej nie psuje
    wynik["werdykt"] = m is not None and m.group(0).upper() == KLUCZ_Z3["werdykt"]
    return {
        "poprawna": all(wynik.values()),
        "powod": "" if all(wynik.values()) else w[:120],
        **wynik,
    }


def _pytest(katalog: Path, cel: str, python: str) -> int:
    """Kod wyjścia pytest; -1 przy przekroczonym czasie (zawieszona „poprawka” nie przerywa serii)."""
    try:
        r = subprocess.run(
            [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", cel],
            cwd=katalog,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return -1
    return r.returncode


def ocen_z2(katalog: Path, python: str = sys.executable) -> dict:
    """(a) testy ukryte przechodzą na poprawionym kodzie; (b) testy piaskownicy przechodzą;
    (c) testy piaskownicy NIE przechodzą na kodzie z błędem (test regresji łapie błąd);
    (d) dawne testy zostały (nazwy)."""
    testy = katalog / "tests" / "test_miary.py"
    if not testy.exists() or not (katalog / "miary.py").exists():
        return {"poprawna": False, "powod": "brak plików"}
    pomin = shutil.ignore_patterns("__pycache__", ".pytest_cache")
    with tempfile.TemporaryDirectory() as tmp:
        kopia = Path(tmp) / "a"
        shutil.copytree(katalog, kopia, ignore=pomin)
        (kopia / "test_ukryty.py").write_text(TEST_UKRYTY, encoding="utf-8")
        a = _pytest(kopia, "test_ukryty.py", python) == 0
        b = _pytest(kopia, "tests/test_miary.py", python) == 0
        z_bledem = Path(tmp) / "c"
        shutil.copytree(katalog, z_bledem, ignore=pomin)
        (z_bledem / "miary.py").write_text(MIARY_Z_BLEDEM, encoding="utf-8")
        c = (
            _pytest(z_bledem, "tests/test_miary.py", python) == 1
        )  # 1 = testy nie przeszły (nie błąd importu)
    dawne = set(re.findall(r"def (test_\w+)", TEST_MIARY))
    d = dawne <= set(re.findall(r"def (test_\w+)", testy.read_text(encoding="utf-8")))
    wynik = {"ukryte": a, "wlasne": b, "regresja": c, "dawne_testy": d}
    return {"poprawna": all(wynik.values()), "powod": "", **wynik}


def nonce(id_przebiegu: str, ziarno: int = ZIARNO) -> str:
    """Znacznik przebiegu: 8 znaków hex z sha256(„id|ziarno”) — deterministyczny, inny dla każdego id."""
    return hashlib.sha256(f"{id_przebiegu}|{ziarno}".encode()).hexdigest()[:8]


def prompt_przebiegu(wpis: dict) -> str:
    """Treść zadania + znacznik przebiegu na końcu. Seria 1: powtórzenie 2 czytało z cache rozmowę
    powtórzenia 1 (np. Z1 opus low 0,111 → 0,029 USD, zapis cache 11 564 → 1 009 tokenów), a opus
    max prawie nie — to zaniżało koszt tańszych konfiguracji. Znacznik robi prefiks rozmowy
    unikalnym; rozgrzewka go nie ma, bo ma właśnie zapisać wspólny prefiks promptu systemowego."""
    if not wpis["zadanie"]:
        return ROZGRZEWKA
    return ZADANIA[wpis["zadanie"]]["prompt"] + ZNACZNIK_PRZEBIEGU.format(nonce=nonce(wpis["id"]))


def czy_skazony(odpowiedz: str) -> bool:
    """Odpowiedź wymienia narzędzie T5, klucze, starą kopię albo repo spoza kopii — model widział
    to, czego nie powinien (także w Z2: piaskownica nie broni czytania poza nią)."""
    return any(z in odpowiedz for z in ZNACZNIKI_SKAZENIA)


def uruchom_jeden(wpis: dict, repo: Path, piaskownica: Path, env: dict) -> dict:
    zad = wpis["zadanie"]
    cwd = piaskownica if wpis["narzedzia"] == "zapis" else repo
    if wpis["narzedzia"] == "zapis":
        zbuduj_piaskownice(piaskownica)  # od nowa przed KAŻDYM przebiegiem Z2 i rozgrzewką zapisu
    rekord = dict(
        wpis,
        nonce=nonce(wpis["id"]) if zad else None,
        start=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    t0 = time.monotonic()
    try:
        r = subprocess.run(
            komenda(prompt_przebiegu(wpis), wpis["model"], wpis["wysilek"], wpis["narzedzia"]),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=LIMIT_CZASU_S,
        )
    except subprocess.TimeoutExpired:
        return dict(rekord, czas_s=LIMIT_CZASU_S, kod_wyjscia=None, blad=BLAD_CZASU)
    rekord.update(czas_s=round(time.monotonic() - t0, 1), kod_wyjscia=r.returncode)
    try:
        o = json.loads(r.stdout)
    except json.JSONDecodeError:
        o = None
    if not isinstance(o, dict):
        return dict(rekord, blad=f"{BLAD_JSON}: {(r.stdout or r.stderr)[:300]}")
    rekord.update(rekord_z_json(o))
    rekord["skazony"] = czy_skazony(rekord["odpowiedz"])
    if zad == "Z1":
        rekord["ocena"] = ocen_z1(rekord["odpowiedz"])
    elif zad == "Z3":
        rekord["ocena"] = ocen_z3(rekord["odpowiedz"])
    elif zad == "Z2":
        rekord["ocena"] = ocen_z2(piaskownica)
    return rekord


def wczytaj(sciezka: Path) -> list[dict]:
    if not sciezka.exists():
        return []
    return [json.loads(x) for x in sciezka.read_text(encoding="utf-8").splitlines() if x.strip()]


def przejsciowy_blad_api(r: dict) -> bool:
    """Błąd po stronie API, który ponowienie może naprawić: `is_error` przy podtypie success i status
    429 (limit zapytań), 5xx (529 = przeciążenie) albo brak statusu (zerwane połączenie). Limit
    budżetu, limit tur i błąd wykonania mają własne podtypy — te rozstrzygają przebieg."""
    if not r.get("is_error") or r.get("podtyp") != "success":
        return False
    s = r.get("status_api")
    return s is None or (isinstance(s, int) and (s == 429 or s >= 500))


def do_ponowienia(r: dict) -> bool:
    """Próba bez rozstrzygnięcia: awaria bez wyniku JSON albo przejściowy błąd API. Wynik JSON
    (także z is_error) i limit czasu rozstrzygają przebieg — nie wraca przy wznowieniu."""
    return str(r.get("blad") or "").startswith(BLAD_JSON) or przejsciowy_blad_api(r)


def rozstrzygniecia(rekordy: list[dict]) -> dict[str, dict]:
    """Próba rozstrzygająca każdy przebieg (id): pierwsza, której się nie ponawia; bez takiej —
    ostatnia, gdy wyczerpano PONOWIENIA (przebieg niepoprawny). Przebieg w toku nie ma wpisu."""
    proby: dict[str, list[dict]] = {}
    for r in rekordy:
        proby.setdefault(r["id"], []).append(r)
    wynik = {}
    for id_, lista in proby.items():
        koncowe = [r for r in lista if not do_ponowienia(r)]
        if koncowe:
            wynik[id_] = koncowe[0]
        elif len(lista) > PONOWIENIA:
            wynik[id_] = lista[-1]
    return wynik


def opis_bledu(r: dict) -> str | None:
    """Etykieta błędu próby; None = bez błędu (o poprawności decyduje wtedy ocena)."""
    if r.get("blad") == BLAD_CZASU:
        return "limit czasu"
    if r.get("blad"):
        return "brak JSON"
    if r.get("is_error", r.get("blad_api")):  # `blad_api` — rekordy serii 1
        if r.get("podtyp") == "success":
            return f"błąd API {r.get('status_api') or 'bez statusu'}"
        return ETYKIETY_BLEDOW.get(r.get("podtyp"), r.get("podtyp") or "is_error")
    if r.get("kod_wyjscia") != 0:
        return f"kod wyjścia {r.get('kod_wyjscia')}"
    return None


def poprawny(r: dict) -> bool:
    """Bez błędu i z poprawną oceną; błędy i limity liczą się jako niepoprawne."""
    return opis_bledu(r) is None and bool((r.get("ocena") or {}).get("poprawna"))


def koszt_serii(r: dict) -> float:
    """Wydatek próby wobec limitu serii: koszt z wyniku JSON; limit czasu — cały limit przebiegu
    (proces przerwany, koszt nieznany — liczymy ostrożnie)."""
    if r.get("blad") == BLAD_CZASU:
        return LIMIT_PRZEBIEGU_USD
    return float(r.get("koszt_usd") or 0.0)


def _srednia(wartosci) -> float | None:
    w = [x for x in wartosci if x is not None]
    return statistics.fmean(w) if w else None


def _wiersz(zad: str, model: str, wysilek: str, g: list[dict]) -> dict:
    return {
        "zadanie": zad,
        "model": model,
        "wysilek": wysilek,
        "odniesienie": (model, wysilek) == ODNIESIENIE,
        "n": len(g),
        "poprawne": sum(poprawny(r) for r in g),
        "bledy": [e for e in map(opis_bledu, g) if e],
        "koszty": [round(r["koszt_usd"], 4) if "koszt_usd" in r else None for r in g],
        "koszt_sredni": _srednia(r.get("koszt_usd") for r in g),
        "zapis_cache_sredni": _srednia(r.get("zapis_cache") for r in g),
        # rekordy serii 1 nie mają pola `skazony` — wtedy ocena z treści odpowiedzi
        "skazone": sum(r.get("skazony", czy_skazony(str(r.get("odpowiedz") or ""))) for r in g),
        "wyjscie_srednie": _srednia(r.get("wyjscie_wszystkie_modele") for r in g),
        "tury_srednie": _srednia(r.get("tury") for r in g),
        "czas_sredni_s": _srednia(r.get("czas_s") for r in g),
    }


def podsumuj(rekordy: list[dict]) -> list[dict]:
    """Wiersz na zadanie × konfigurację z rozstrzygniętych przebiegów; w każdym zadaniu najpierw
    odniesienie (opus max). Błędy i limity czasu = niepoprawne, wymienione w wierszu. Kolumna
    „reguła” (reguła T5 z docs/rag/12): TAK, gdy 2/2 poprawne, zero skażonych i średni koszt
    najwyżej PROG_TANIEJ kosztu odniesienia; „—”, gdy odniesienie nie ma 2/2 poprawnych bez
    skażonych (nie ma z czym porównać); inaczej „nie”. Zalecenia skrypt nie wydaje."""
    grupy: dict[tuple, list[dict]] = {}
    for r in rozstrzygniecia(rekordy).values():
        if r.get("zadanie"):
            grupy.setdefault((r["zadanie"], r["model"], r["wysilek"]), []).append(r)
    wiersze = []
    for zad in ZADANIA:
        if not any(k[0] == zad for k in grupy):
            continue
        ref = _wiersz(zad, *ODNIESIENIE, grupy.get((zad, *ODNIESIENIE), []))
        ref_wazne = ref["n"] == ref["poprawne"] == POWTORZENIA and ref["skazone"] == 0
        wiersze.append(
            dict(ref, wobec_odniesienia=1.0 if ref["koszt_sredni"] else None, regula="odniesienie")
        )
        for m, w in KONFIGURACJE:
            if (m, w) == ODNIESIENIE or (zad, m, w) not in grupy:
                continue
            x = _wiersz(zad, m, w, grupy[(zad, m, w)])
            wob = None
            if x["koszt_sredni"] is not None and ref["koszt_sredni"]:
                wob = x["koszt_sredni"] / ref["koszt_sredni"]
            if not ref_wazne:
                regula = "—"
            elif (
                x["n"] == x["poprawne"] == POWTORZENIA
                and x["skazone"] == 0
                and wob is not None
                and wob <= PROG_TANIEJ + 1e-9
            ):
                regula = "TAK"
            else:
                regula = "nie"
            wiersze.append(dict(x, wobec_odniesienia=wob, regula=regula))
    return wiersze


def _md(x: float | None, wzor: str) -> str:
    return "—" if x is None else format(x, wzor).replace(",", " ")


def tabela_md(wiersze: list[dict], rekordy: list[dict]) -> str:
    """Tabela Markdown + stopka: koszt wszystkich prób, przebiegi z błędem, przebiegi w toku."""
    out = [
        "| zadanie | konfiguracja | poprawne | błędy | koszt USD (przebiegi) | średnio "
        f"| wobec {' '.join(ODNIESIENIE)} | zapis cache (średnio, tokeny) | skażone | reguła "
        "| wyjście (tokeny) | tury | czas s |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in wiersze:
        konf = f"{r['model']} {r['wysilek']}" + (" (odniesienie)" if r["odniesienie"] else "")
        koszty = " / ".join("?" if k is None else f"{k:.3f}" for k in r["koszty"]) or "—"
        out.append(
            f"| {r['zadanie']} | {konf} | {r['poprawne']}/{r['n']} | {', '.join(r['bledy']) or '—'} "
            f"| {koszty} | {_md(r['koszt_sredni'], '.3f')} | {_md(r['wobec_odniesienia'], '.2f')} "
            f"| {_md(r['zapis_cache_sredni'], ',.0f')} | {r['skazone']} | {r['regula']} "
            f"| {_md(r['wyjscie_srednie'], ',.0f')} | {_md(r['tury_srednie'], '.1f')} "
            f"| {_md(r['czas_sredni_s'], '.0f')} |"
        )
    rozstrzygniete = rozstrzygniecia(rekordy)
    proby = Counter(r["id"] for r in rekordy)
    znany = sum(float(r.get("koszt_usd") or 0.0) for r in rekordy)
    rozgrz = sum(float(r.get("koszt_usd") or 0.0) for r in rekordy if not r.get("zadanie"))
    do_limitu = sum(koszt_serii(r) for r in rekordy)
    z_bledem = [f"{i} ({e})" for i, r in rozstrzygniete.items() if (e := opis_bledu(r))]
    w_toku = [
        f"{i} (prób {n} z {1 + PONOWIENIA})" for i, n in proby.items() if i not in rozstrzygniete
    ]
    out += [
        "",
        f"Razem {znany:.2f} USD z wyników JSON, wszystkie próby (w tym rozgrzewki {rozgrz:.2f}); "
        f"do limitu serii {do_limitu:.2f} USD (limit czasu liczony jako {LIMIT_PRZEBIEGU_USD:.2f}).",
        f"Przebiegi z błędem (niepoprawne): {len(z_bledem)}"
        f"{': ' + ', '.join(z_bledem) if z_bledem else ''}.",
        f"Do ponowienia przy wznowieniu: {len(w_toku)}{': ' + ', '.join(w_toku) if w_toku else ''}.",
    ]
    return "\n".join(out)


def _sprawdz(repo: Path) -> int:
    try:
        sprawdz_kopie_repo(repo, historia=True)
    except KopiaNieczysta as e:
        print(f"ODRZUCONA: {e}", file=sys.stderr)
        return 2
    print(
        f"PRZYJĘTA: {repo} — klucz Z1 na miejscu; narzędzia T5 i znaczników klucza brak w drzewie "
        "i w historii; drzewo czyste"
    )
    return 0


def _uruchom(a: argparse.Namespace) -> int:
    try:
        sprawdz_kopie_repo(a.repo, historia=True)
    except KopiaNieczysta as e:
        print(f"STOP przed serią: {e}", file=sys.stderr)
        return 2
    env = srodowisko(a.piaskownica.parent / "t5_bin")
    stale = {
        "wersja_claude": wersja_claude(env),
        "commit_kopii": _git(a.repo, "rev-parse", "HEAD").stdout.strip(),
    }
    print(f"claude {stale['wersja_claude']}; kopia {a.repo} na {stale['commit_kopii'][:7]}")
    rekordy = wczytaj(a.wyniki)
    rozstrzygniete = rozstrzygniecia(rekordy)
    wydane = sum(koszt_serii(r) for r in rekordy)
    wykonane, ostatni_w_kopii = 0, None
    for wpis in plan():
        if wpis["id"] in rozstrzygniete:
            continue
        if wydane >= LIMIT_SERII_USD:
            print(f"limit serii {LIMIT_SERII_USD:.2f} USD wyczerpany — dalsze przebiegi wstrzymane")
            break
        if a.limit and wykonane >= a.limit:
            break
        if wpis["narzedzia"] == "odczyt":  # przebieg w kopii repo: Z1, Z3 i rozgrzewki odczytu
            try:
                sprawdz_kopie_repo(a.repo)
            except KopiaNieczysta as e:
                print(
                    f"STOP przed {wpis['id']} (ostatni przebieg w kopii: "
                    f"{ostatni_w_kopii or 'żaden w tym uruchomieniu'}): {e}\n"
                    "Kopii nie czyszczę: obejrzyj zmiany, rozstrzygnij los przebiegu, który je "
                    "zostawił, przywróć kopię i dopiero wtedy wznów.",
                    file=sys.stderr,
                )
                return 2
            ostatni_w_kopii = wpis["id"]
        r = dict(uruchom_jeden(wpis, a.repo, a.piaskownica, env), **stale)
        with open(a.wyniki, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        wydane += koszt_serii(r)
        wykonane += 1
        stan = (opis_bledu(r) or "") + (" (do ponowienia)" if do_ponowienia(r) else "")
        print(
            f"{r['id']:28} {r.get('koszt_usd', 0):7.4f} USD  wyj {r.get('wyjscie_wszystkie_modele', 0):6} "
            f"tury {r.get('tury')}  {r.get('czas_s')} s  "
            f"poprawna={(r.get('ocena') or {}).get('poprawna')}"
            f"{'  SKAŻONY' if r.get('skazony') else ''}  {stan}",
            flush=True,
        )
    print(
        f"seria: wydane {wydane:.2f} USD (limit {LIMIT_SERII_USD:.2f}), wykonano teraz {wykonane}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="tryb", required=True)
    k = sub.add_parser("kopia", help="czysta kopia repo do Z1/Z3 (klon master bez origin)")
    k.add_argument("--zrodlo", type=Path, required=True, help="repo projektu")
    k.add_argument("--cel", type=Path, required=True, help="katalog kopii (nie może istnieć)")
    s = sub.add_parser("sprawdz", help="strażnik kopii repo: drzewo, historia, czystość")
    s.add_argument("--repo", type=Path, required=True)
    sub.add_parser("plan", help="kolejność przebiegów")
    u = sub.add_parser("uruchom", help="wykonaj brakujące przebiegi")
    u.add_argument("--wyniki", type=Path, required=True)
    u.add_argument("--repo", type=Path, required=True, help="kopia repo z podkomendy `kopia`")
    u.add_argument("--piaskownica", type=Path, required=True, help="katalog Z2 (stała ścieżka)")
    u.add_argument("--limit", type=int, default=0, help="najwyżej tyle przebiegów (0 = wszystkie)")
    p = sub.add_parser("podsumuj", help="tabela wyników (Markdown)")
    p.add_argument("--wyniki", type=Path, required=True)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.tryb == "plan":
        for w in plan():
            print(w["id"])
        return 0
    if a.tryb == "podsumuj":
        rek = wczytaj(a.wyniki)
        print(tabela_md(podsumuj(rek), rek))
        return 0
    if a.tryb == "kopia":
        try:
            glowa = kopia(a.zrodlo, a.cel)
        except FileExistsError as e:
            print(f"ODMOWA: {e}", file=sys.stderr)
            return 2
        print(f"kopia {a.cel}: master na {glowa}, bez zdalnego origin")
        return _sprawdz(a.cel)
    if a.tryb == "sprawdz":
        return _sprawdz(a.repo)
    return _uruchom(a)


if __name__ == "__main__":
    sys.exit(main())
