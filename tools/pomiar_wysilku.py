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
Wyniki dopisywane do pliku JSONL; przerwany pomiar wznawia się od brakujących przebiegów.

    .venv/bin/python tools/pomiar_wysilku.py plan
    .venv/bin/python tools/pomiar_wysilku.py uruchom --wyniki W.jsonl --repo KOPIA --piaskownica KATALOG
    .venv/bin/python tools/pomiar_wysilku.py podsumuj --wyniki W.jsonl

`--repo` to KOPIA repo (git worktree na stałym commicie): równoległa praca w repo zmienia stan gita
w prompcie systemowym i unieważnia cache. Na serwerze brakuje polecenia `py` (CLAUDE.md je zakłada) —
przebiegi dostają podkładkę `py` → python z venv, żeby brak polecenia nie dokładał prób i błędów.
Skrypt jest neutralnym reporterem: zalecenie podpisuje Claude w docs/rag/12.
"""

from __future__ import annotations

import argparse
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


def sprawdz_kopie_repo(katalog: Path) -> None:
    """Klucz Z1 wskazuje linię 648 — kopia repo musi ją mieć w tym miejscu."""
    linie = (katalog / KLUCZ_Z1["sciezka"]).read_text(encoding="utf-8").splitlines()
    nr = KLUCZ_Z1["linie"][0]
    if len(linie) < nr or not linie[nr - 1].startswith(f"def {KLUCZ_Z1['funkcja']}("):
        raise ValueError(f"{katalog}: klucz Z1 nie pasuje do kopii repo (linia 648)")


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
    """Koszt i tokeny z wyniku `claude -p --output-format json`."""
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
        "blad_api": bool(o.get("is_error")),
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
    """Pierwsza liczba w tekście: „0,54”, „1 800”, „1,800”, „56,3 %”, „0.5631 (56,31 %)”."""
    m = re.search(r"\d[\d\u00a0\u202f ,.]*%?", s)
    if not m:
        return None
    t = re.sub(r"[\u00a0\u202f ]", "", m.group(0)).rstrip(".,")
    procent = t.endswith("%")
    t = t.rstrip("%").rstrip(".,")
    # 1,800 — separator tysięcy; 0,563 i 56,310 % — przecinek dziesiętny
    if not procent and re.fullmatch(r"[1-9]\d{0,2}(,\d{3})+", t):
        t = t.replace(",", "")
    try:
        x = float(t.replace(",", "."))
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
    wynik["werdykt"] = pola.get("werdykt", "").strip(" .").upper() == KLUCZ_Z3["werdykt"]
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


def uruchom_jeden(wpis: dict, repo: Path, piaskownica: Path, env: dict) -> dict:
    zad = wpis["zadanie"]
    prompt = ZADANIA[zad]["prompt"] if zad else ROZGRZEWKA
    cwd = piaskownica if wpis["narzedzia"] == "zapis" else repo
    if wpis["narzedzia"] == "zapis":
        zbuduj_piaskownice(piaskownica)
    rekord = dict(wpis, start=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    t0 = time.monotonic()
    try:
        r = subprocess.run(
            komenda(prompt, wpis["model"], wpis["wysilek"], wpis["narzedzia"]),
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=LIMIT_CZASU_S,
        )
    except subprocess.TimeoutExpired:
        return dict(rekord, czas_s=LIMIT_CZASU_S, kod_wyjscia=None, blad="przekroczony czas")
    rekord.update(czas_s=round(time.monotonic() - t0, 1), kod_wyjscia=r.returncode)
    try:
        rekord.update(rekord_z_json(json.loads(r.stdout)))
    except json.JSONDecodeError:
        return dict(rekord, blad=f"wyjście nie jest JSON: {(r.stdout or r.stderr)[:300]}")
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


def _udany(r: dict) -> bool:
    return r.get("kod_wyjscia") == 0 and not r.get("blad") and not r.get("blad_api")


def podsumuj(rekordy: list[dict]) -> list[dict]:
    """Wiersz na zadanie × konfigurację: poprawność, koszty przebiegów, średnie, stosunek do odniesienia."""
    grupy: dict[tuple, list[dict]] = {}
    for r in rekordy:
        if r.get("zadanie") and _udany(r):
            grupy.setdefault((r["zadanie"], r["model"], r["wysilek"]), []).append(r)
    wiersze = []
    for zad in ZADANIA:
        ref = grupy.get((zad, *ODNIESIENIE), [])
        ref_koszt = statistics.fmean(r["koszt_usd"] for r in ref) if ref else None
        for m, w in KONFIGURACJE:
            g = grupy.get((zad, m, w), [])
            if not g:
                continue
            koszt = statistics.fmean(r["koszt_usd"] for r in g)
            wiersze.append(
                {
                    "zadanie": zad,
                    "model": m,
                    "wysilek": w,
                    "n": len(g),
                    "poprawne": sum(bool(r.get("ocena", {}).get("poprawna")) for r in g),
                    "koszty": [round(r["koszt_usd"], 4) for r in g],
                    "koszt_sredni": koszt,
                    "wobec_odniesienia": koszt / ref_koszt if ref_koszt else None,
                    "odniesienie_poprawne": sum(
                        bool(r.get("ocena", {}).get("poprawna")) for r in ref
                    ),
                    "wyjscie_srednie": statistics.fmean(r["wyjscie_wszystkie_modele"] for r in g),
                    "tury_srednie": statistics.fmean(r.get("tury") or 0 for r in g),
                    "czas_sredni_s": statistics.fmean(r["czas_s"] for r in g),
                }
            )
    return wiersze


def tabela_md(wiersze: list[dict], rekordy: list[dict]) -> str:
    out = [
        "| zadanie | konfiguracja | poprawne | koszt USD (przebiegi) | średnio | wobec opus max "
        "| wyjście (tokeny) | tury | czas s |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in wiersze:
        wob = "—" if r["wobec_odniesienia"] is None else f"{r['wobec_odniesienia']:.2f}"
        if r["wobec_odniesienia"] is not None and r["wobec_odniesienia"] <= PROG_TANIEJ:
            wob += " (≤ 0.70)"
        koszty = " / ".join(f"{k:.3f}" for k in r["koszty"])
        wyj = f"{r['wyjscie_srednie']:,.0f}".replace(",", " ")
        out.append(
            f"| {r['zadanie']} | {r['model']} {r['wysilek']} | {r['poprawne']}/{r['n']} | {koszty} "
            f"| {r['koszt_sredni']:.3f} | {wob} | {wyj} | {r['tury_srednie']:.1f} "
            f"| {r['czas_sredni_s']:.0f} |"
        )
    udane = [r for r in rekordy if _udany(r)]
    razem = sum(r.get("koszt_usd", 0.0) for r in rekordy)  # z nieudanymi — tyle kosztowała seria
    rozgrz = sum(r.get("koszt_usd", 0.0) for r in rekordy if not r.get("zadanie"))
    nieudane = [r["id"] for r in rekordy if not _udany(r)]
    out.append("")
    out.append(
        f"Razem {razem:.2f} USD (w tym rozgrzewki {rozgrz:.2f}); przebiegów udanych {len(udane)}, "
        f"nieudanych {len(nieudane)}{': ' + ', '.join(nieudane) if nieudane else ''}."
    )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="tryb", required=True)
    sub.add_parser("plan", help="kolejność przebiegów")
    u = sub.add_parser("uruchom", help="wykonaj brakujące przebiegi")
    u.add_argument("--wyniki", type=Path, required=True)
    u.add_argument("--repo", type=Path, required=True, help="kopia repo (git worktree)")
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
    sprawdz_kopie_repo(a.repo)
    env = srodowisko(a.piaskownica.parent / "t5_bin")
    zrobione = {r["id"] for r in wczytaj(a.wyniki) if _udany(r)}
    wydane = sum(r.get("koszt_usd", 0.0) for r in wczytaj(a.wyniki))
    wykonane = 0
    for wpis in plan():
        if wpis["id"] in zrobione:
            continue
        if wydane >= LIMIT_SERII_USD or (a.limit and wykonane >= a.limit):
            break
        r = uruchom_jeden(wpis, a.repo, a.piaskownica, env)
        with open(a.wyniki, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        wydane += r.get("koszt_usd", 0.0)
        wykonane += 1
        ocena = r.get("ocena", {}).get("poprawna")
        print(
            f"{r['id']:28} {r.get('koszt_usd', 0):7.4f} USD  wyj {r.get('wyjscie_wszystkie_modele', 0):6} "
            f"tury {r.get('tury')}  {r.get('czas_s')} s  poprawna={ocena}  {r.get('blad') or ''}",
            flush=True,
        )
    print(f"seria: wydane {wydane:.2f} USD, wykonano teraz {wykonane}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
