"""Odczyt dziennika papierowego (szczebel 3 drabiny dowodów, ADR-09) z progami zapisanymi Z GÓRY.

Po co: odczyt po ~3, 6 i 12 miesiącach (pierwszy ok. 2026-12-25) liczy się z liczb zapisanych
przed wynikiem, a nie ustalanych po nim. Umowa odczytu: `dziennik/README.md`, sekcja „Odczyt po
~3 miesiącach” → „Zmiana kryteriów odczytu (decyzja użytkownika 2026-09-27)”.

Co liczy:
- kryteria mechaniki 1–4 — TE SAME definicje co strona dziennika (`tools/strona_dziennika.build_state`),
  tu tylko porównane z progami z README (95 % dni, 0 zmian historii, depozyt 15–35 %, sufit k);
- kryterium 4b — zrealizowana zmienność R1 od pierwszego wyniku w paśmie [13; 31] %/rok (~92 dni);
- kryterium 5 — próg obalenia per noga (TS1 = r_trend, CP1 = r_coinbase, R1 = r_port, X1 = r_x1):
  średnia roczna poniżej μ − z·SE, gdzie SE = σ/√(n/365), μ i σ zakładane (stałe niżej, ze źródłami),
  z = Z_READ — jeden próg na każdym z 3 odczytów (≈ 92, 182, 365 dni), dobrany tak, by łączna
  jednostronna szansa fałszywego obalenia nogi przez 3 odczyty wynosiła 2,5 % (`simulate_z`).

Zasady: czyta WYŁĄCZNIE `<repo>@origin/master:dziennik/*` (przez `strona_dziennika`) i niczego nie
zapisuje. Jest reporterem: pisze „próg przekroczony / nieprzekroczony”; werdykt o strategii podpisuje
Claude w dokumentacji (CLAUDE.md). Brak obalenia NIE jest potwierdzeniem przewagi.
`--as-of` odtwarza stan dziennika z ostatniego commita „Dziennik: przebieg …” z datą ≤ as_of + 1 dzień.

Który wydruk wiąże (status liczony RAZ z kalendarza, wspólny dla wszystkich nóg — braki w nodze
zmniejszają tylko jej n w SE): WYŁĄCZNIE wydruk z `--as-of` równym dacie planu (PLAN_DATES:
2026-12-24, 2027-03-24, 2027-09-23), gdy migawka zawiera wynik R1 za ten dzień. Zapas: gdy migawka na
datę planu jest niepełna (przebieg nie doszedł), wiąże pierwsza data w ciągu 7 dni po planie z pełną
migawką — skrypt sprawdza to sam, więc wynik nie zależy od tego, kto i kiedy uruchomi. Ta sama
migawka daje ten sam wydruk: kolejne uruchomienia to kopie, nie nowe odczyty. Każdy inny wydruk to
„ZA WCZEŚNIE — tylko podgląd” (przed pierwszą datą planu), „podgląd” albo „NIE WIĄŻE”.

    git fetch && PYTHONUTF8=1 py -m backtest.odczyt_dziennika [--repo .] [--as-of RRRR-MM-DD] [--json]

Testy: `tests/test_odczyt_dziennika.py`. Stałe μ, σ: `backtest/odczyt_dziennika_stale.py`.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone

import numpy as np

from tools import strona_dziennika as sd

DAYS_PER_YEAR = 365
# Plan odczytów (decyzja użytkownika 2026-09-27): ~3, 6 i 12 miesięcy wyniku R1 od 2026-09-24,
# czyli ostatni dzień wyniku 2026-12-24, 2027-03-24, 2027-09-23 (odczyt dzień później).
READ_DAYS = (92, 182, 365)
R1_START = date.fromisoformat(sd.R1_START)
# daty planu = ostatni dzień wyniku R1 odczytu k: 2026-12-24, 2027-03-24, 2027-09-23 (--as-of)
PLAN_DATES = tuple(R1_START + timedelta(days=d - 1) for d in READ_DAYS)
# zapas: gdy migawka na datę planu nie zawiera tego dnia, wiąże pierwsza pełna w ciągu 7 dni po planie
READ_FALLBACK_DAYS = 7
STALE_DAYS = 2  # ostatni przebieg starszy niż 2 dni = alarm świeżości (CLAUDE.md)
ALPHA = 0.025  # łączna jednostronna szansa fałszywego obalenia jednej nogi przez 3 odczyty
# Z_READ: `simulate_z(READ_DAYS, ALPHA, n_sim=10_000_000, seed=20260927)` = 2,3102 (błądzenie losowe,
# odczyty zagnieżdżone, korelacja √(n_i/n_j)); druga droga — dokładna całka normalna 3-wymiarowa
# (scipy.stats.multivariate_normal) = 2,3113; dla porównania Bonferroni (bez korelacji) 2,394,
# a stałe 1,96 dałoby 5,67 % fałszywych obaleń (docs/rag/11 sekcja 2: „~5,7 %”).
Z_READ = 2.31
VOL_BAND = (
    0.13,
    0.31,
)  # kryterium 4b, pasmo dla ~92 dni (docs/rag/11 sekcje 2 i 8: 5,1 % okien poza)
COMPLETENESS_MIN = 0.95  # kryterium 1
TIMELINESS_MIN = 0.95  # kryterium 3
MARGIN_BAND = (0.15, 0.35)  # kryterium 4: mediana depozytu (suma faz, jak w sygnaly.csv)
K_CAP = 2.0  # kryterium 4: sufit mnożnika R1 (sizing.apply_rules, dziennik/README.md)
EPS = 1e-9


@dataclass(frozen=True)
class Leg:
    """Noga odczytu: plik i kolumna dziennika + zakładane μ, σ (roczne, ARYTMETYCZNE) ze źródłem."""

    key: str
    name: str
    file: str
    column: str
    mu: float
    sigma: float
    source: str


# μ = średnia dzienna × 365, σ = sd dzienne × √365 — konfiguracja DZIENNIKA na historii 2021–2026,
# zamrożone silniki, 0 wariantów (statystyka opisowa). Komenda: `py -m backtest.odczyt_dziennika_stale`
# (wydruk wklejony w dziennik/README.md). Sprawdzenie drugą drogą: CAGR i zmienność z tej komendy
# = runs/2026-09-24_ru1-pelne-uniwersum/raw_output_sz1.txt linie 5–8 (trend 7,1/18,2; Coinbase
# 28,2/35,1; R1 17,1/21,7) i X1 +9,5 %/rok = runs/2026-09-24_x1f-siedem-faz/raw_output.txt linia 14.
LEGS = (
    Leg(
        "TS1",
        "trend tygodniowy, likwidacja 2×",
        "wyniki.csv",
        "r_trend",
        0.1069,
        0.1812,
        "odczyt_dziennika_stale: TS1 2× pełne uniwersum 2021-02-08 → 2026-06-30, 1969 dni "
        "(silnik RU1 run_sz1; CAGR 9,5 %)",
    ),
    Leg(
        "CP1",
        "premia Coinbase na BTC, likwidacja 3×",
        "wyniki.csv",
        "r_coinbase",
        0.3104,
        0.3511,
        "odczyt_dziennika_stale: CP1 3× 2021-05-08 → 2026-06-30, 1880 dni "
        "(RU1 raw_output_sz1.txt l. 6: CAGR 28,2, zmienność 35,1)",
    ),
    Leg(
        "R1",
        "portfel R1 (trend + premia, budżet ryzyka)",
        "wyniki.csv",
        "r_port",
        0.1817,
        0.2166,
        "odczyt_dziennika_stale: R1 2021-05-08 → 2026-06-30, 1880 dni "
        "(RU1 raw_output_sz1.txt l. 8: CAGR 17,1 — to średnia GEOMETRYCZNA, stąd 18,2 ≠ 17,1)",
    ),
    Leg(
        "X1",
        "momentum przekrojowe, średnia 7 faz",
        "x1_wyniki.csv",
        "r_x1",
        0.0949,
        0.3626,
        "odczyt_dziennika_stale: X1 średnia 7 faz 2021-02-08 → 2026-06-30, 1969 dni "
        "(X1F raw_output.txt l. 14: +9,5 %/rok)",
    ),
)


# ------------------------------------------------------------------ czyste funkcje


def simulate_z(
    days: tuple[int, ...] = READ_DAYS,
    alpha: float = ALPHA,
    n_sim: int = 1_000_000,
    seed: int = 20260927,
    batch: int = 1_000_000,
) -> float:
    """Stały próg z dla odczytów zagnieżdżonych: P(min_k Z_k < −z) = alpha przy prawdziwym μ.

    Błądzenie losowe z krokami dziennymi N(0, 1): suma S_n po n dniach, Z_k = S_{n_k}/√n_k.
    Dla kroków normalnych S w chwilach odczytu to dokładnie sumy niezależnych przyrostów bloków
    (n_1, n_2 − n_1, …) o wariancji równej długości bloku — symulujemy więc bloki, nie dni.
    Wynik nie zależy od μ ani σ, tylko od dni odczytów.
    """
    if list(days) != sorted(set(days)) or days[0] <= 0:
        raise ValueError("dni odczytów muszą być rosnące i dodatnie")
    rng = np.random.default_rng(seed)
    n_arr = np.asarray(days, dtype=float)
    scale = np.sqrt(np.diff(np.concatenate([[0.0], n_arr])))
    mins = []
    left = n_sim
    while left > 0:
        m = min(batch, left)
        s = np.cumsum(rng.standard_normal((m, len(days))) * scale, axis=1)
        mins.append((s / np.sqrt(n_arr)).min(axis=1))
        left -= m
    return float(-np.quantile(np.concatenate(mins), alpha))


def clean(values) -> tuple[list[float], int]:
    """Zwroty dzienne → (liczby skończone, liczba braków: puste, tekst, NaN, ±inf)."""
    out, missing = [], 0
    for v in values:
        try:
            x = float(v)
        except (TypeError, ValueError):
            missing += 1
            continue
        if math.isfinite(x):
            out.append(x)
        else:
            missing += 1
    return out, missing


def refutation(mu: float, sigma: float, n: int, z: float = Z_READ) -> dict:
    """Próg obalenia dla n dni: SE = σ/√(n/365), próg = μ − z·SE (roczne) + lata do wykrycia μ."""
    if n <= 0:
        raise ValueError("n musi być dodatnie")
    se = sigma / math.sqrt(n / DAYS_PER_YEAR)
    ratio = 2 * sigma / mu if mu > 0 else math.inf
    return {
        "se": se,
        "threshold": mu - z * se,
        # tyle lat, by μ = 2·SE (połowa przedziału 95 % ≈ μ): (2σ/μ)²
        "years_to_detect": ratio * ratio,  # mnożenie, nie **: bardzo małe μ → inf, bez wyjątku
    }


def plan_slot(day: date) -> tuple[int, date] | None:
    """Odczyt planowy (k, data planu), do którego okna [plan; plan + 7 dni] należy `day`."""
    fallback = timedelta(days=READ_FALLBACK_DAYS)
    for k, plan in enumerate(PLAN_DATES, start=1):
        if plan <= day <= plan + fallback:
            return k, plan
    return None


def reading_status(as_of: date | None, last: str | None, bound_at: str | None = None) -> dict:
    """Status odczytu — RAZ dla całego wydruku, z kalendarza (data planu), nie z liczby dni danych.

    as_of: data z `--as-of` (None = podgląd bez obcięcia); last: ostatni dzień wyniku R1 w migawce;
    bound_at: wcześniejsza data z okna tego odczytu, dla której migawka była już pełna — wtedy odczyt
    już się odbył i bieżący wydruk go nie zastępuje. Wiąże tylko `--as-of` = data planu przy pełnej
    migawce albo (zapas) pierwsza pełna migawka w ciągu 7 dni po planie.
    """
    day = as_of if as_of is not None else (date.fromisoformat(last) if last else None)
    out = {
        "binding": False,
        "reading": 0,
        "planned_as_of": None,
        "days": (day - R1_START).days + 1 if day else 0,  # dni kalendarzowe wyniku R1
    }
    if day is None or day < PLAN_DATES[0]:
        return {**out, "label": "ZA WCZEŚNIE — tylko podgląd"}
    if as_of is None:
        return {
            **out,
            "label": "podgląd bez --as-of — nie wiąże (wiąże tylko --as-of <data planu>)",
        }
    slot = plan_slot(as_of)
    if slot is None:
        if as_of > PLAN_DATES[-1] + timedelta(days=READ_FALLBACK_DAYS):
            label = "po planie 3 odczytów — z nie kontroluje dalszych odczytów, tylko podgląd"
        else:
            label = "podgląd między odczytami planowymi — nie wiąże (z liczone na 3 odczyty)"
        return {**out, "label": label}
    k, plan = slot
    out["planned_as_of"] = plan.isoformat()
    if last != as_of.isoformat():
        label = (
            f"NIE WIĄŻE — migawka kończy się na {last}, a nie na {as_of} (git fetch albo przebieg "
            f"{as_of + timedelta(days=1)} nie doszedł); zapas: pierwsza data do "
            f"{plan + timedelta(days=READ_FALLBACK_DAYS)} z pełną migawką"
        )
    elif bound_at is not None:
        label = (
            f"NIE WIĄŻE — odczyt {k} odbył się przy --as-of {bound_at} "
            "(pierwsza pełna migawka w oknie); ten wydruk to tylko podgląd"
        )
    elif as_of == plan:
        return {**out, "binding": True, "reading": k, "label": f"odczyt wiążący {k} z 3"}
    else:
        return {
            **out,
            "binding": True,
            "reading": k,
            "label": (
                f"odczyt wiążący {k} z 3 — zapas: migawka na datę planu {plan} niepełna, "
                f"pierwsza pełna {as_of}"
            ),
        }
    return {**out, "label": label}


PREVIEW = {"binding": False, "reading": 0, "planned_as_of": None, "label": "podgląd"}


def leg_reading(leg: Leg, values, status: dict = PREVIEW, z: float = Z_READ) -> dict:
    """Kryterium 5 dla jednej nogi: średnia roczna vs próg obalenia μ − z·SE.

    `status` (z `reading_status`) jest wspólny dla wszystkich nóg wydruku; n ważnych wartości nogi
    wchodzi tylko do SE i średniej, braki są liczone osobno (`missing`).
    """
    xs, missing = clean(values)
    n = len(xs)
    keep = ("binding", "reading", "planned_as_of", "label")
    out = {**asdict(leg), "n": n, "missing": missing, "z": z, **{k: status[k] for k in keep}}
    if n == 0:
        out.update(mean=None, sd=None, ci95=None, total=None, crossed=None, verdict="brak danych")
        return out
    mean = statistics.fmean(xs) * DAYS_PER_YEAR
    sd_ann = statistics.stdev(xs) * math.sqrt(DAYS_PER_YEAR) if n > 1 else None
    ref = refutation(leg.mu, leg.sigma, n, z)
    crossed = mean < ref["threshold"]
    if out["binding"]:
        verdict = (
            "próg obalenia PRZEKROCZONY (obalona)"
            if crossed
            else "próg obalenia nieprzekroczony (brak obalenia)"
        )
    else:
        verdict = "podgląd: średnia " + ("poniżej progu" if crossed else "nad progiem")
        verdict += " (nie wiąże)"
    # przedział 95 % zrealizowanej średniej (zmienność zrealizowana, nie zakładana; bramka 16b)
    half = None if sd_ann is None else 1.96 * sd_ann / math.sqrt(n / DAYS_PER_YEAR)
    out.update(
        mean=mean,
        sd=sd_ann,
        ci95=None if half is None else [mean - half, mean + half],
        total=math.fsum(xs),  # Σ dziennych zwrotów = średnia roczna × n/365 (skala progu)
        **ref,
        threshold_period=ref["threshold"] * n / DAYS_PER_YEAR,
        crossed=crossed,
        verdict=verdict,
    )
    return out


def vol_band(values, band: tuple[float, float] = VOL_BAND) -> dict:
    """Kryterium 4b: zrealizowana zmienność R1 (sd dzienne × √365) w paśmie [lo; hi], granice włącznie."""
    xs, missing = clean(values)
    n = len(xs)
    vol = statistics.stdev(xs) * math.sqrt(DAYS_PER_YEAR) if n > 1 else None
    ok = None if vol is None else band[0] - EPS <= vol <= band[1] + EPS
    return {"n": n, "missing": missing, "vol": vol, "band": list(band), "ok": ok}


def mechanics(state: dict) -> dict:
    """Kryteria 1–4 z `build_state` (te same definicje co strona) porównane z progami z README."""
    c = state["criteria"]
    comp, tim, cons, mar, kmax = (
        c["completeness"],
        c["timeliness"],
        c["consistency"],
        c["margin"],
        c["k_max"],
    )
    share = comp["covered"] / comp["days"] if comp["days"] else None
    tshare = (tim["days"] - len(tim["late"])) / tim["days"] if tim["days"] else None
    k_ok = all(k is not None and k <= K_CAP + EPS for k in (kmax["trend"], kmax["coinbase"]))
    med = mar["median"]
    return {
        "1_kompletnosc": {
            **comp,
            "share": share,
            "ok": share is not None and share >= COMPLETENESS_MIN,
        },
        "2_spojnosc": {**cons, "ok": cons["after_first_result"] == 0},
        "3_terminowosc": {
            **tim,
            "share": tshare,
            "ok": tshare is not None and tshare >= TIMELINESS_MIN,
        },
        "4_zgodnosc_sz1": {
            "margin": mar,
            "k_max": kmax,
            "band": list(MARGIN_BAND),
            "ok": med is not None and MARGIN_BAND[0] <= med <= MARGIN_BAND[1] and k_ok,
        },
    }


# ------------------------------------------------------------------ odczyt z repo


def snapshot_ref(repo: str, as_of: date) -> str:
    """Hash ostatniego commita „Dziennik: przebieg <d>” na origin/master z d ≤ as_of + 1 dzień."""
    text = sd.git(repo, "log", sd.REF, "--grep=^Dziennik: przebieg", "--format=%H|%s", check=True)
    limit = (as_of + timedelta(days=1)).isoformat()
    for line in text.splitlines():  # od najnowszego
        sha, _, subj = line.partition("|")
        m = sd.COMMIT_RE.match(subj.strip())
        if m and m[1] <= limit:
            return sha
    raise ValueError(f"brak commita dziennika z datą ≤ {limit}")


def first_full_snapshot(repo: str, start: date, end: date) -> str | None:
    """Najwcześniejszy dzień d z [start; end), którego migawka (`snapshot_ref`) ma wynik R1 za d."""
    d = start
    while d < end:
        try:
            ref = snapshot_ref(repo, d)
        except ValueError:
            ref = None
        if ref is not None:
            with _ref(ref):
                days = {r.get("date") for r in sd.rows(repo, "wyniki.csv")}
            if d.isoformat() in days:
                return d.isoformat()
        d += timedelta(days=1)
    return None


@contextmanager
def _ref(ref: str):
    """Tymczasowo czytaj `strona_dziennika` z innego refu (tylko odczyt, przywracane zawsze)."""
    old = sd.REF
    sd.REF = ref
    try:
        yield
    finally:
        sd.REF = old


def _cut(rows: list[dict], as_of: date | None) -> list[dict]:
    if as_of is None:
        return rows
    return [r for r in rows if r.get("date", "") <= as_of.isoformat()]


def reading(repo: str = ".", as_of: date | None = None, now: datetime | None = None) -> dict:
    """Pełny odczyt: kryteria 1–4 (build_state), 4b i 5 per noga. Niczego nie zapisuje."""
    ref = sd.REF if as_of is None else snapshot_ref(repo, as_of)
    if now is None:
        now = (
            datetime.now(timezone.utc)
            if as_of is None
            else datetime.combine(as_of + timedelta(days=1), time(6, 30), tzinfo=timezone.utc)
        )
    with _ref(ref):
        state, n_runs = sd.build_state(repo, now)
        files = {name: _cut(sd.rows(repo, name), as_of) for name in {g.file for g in LEGS}}
    r1 = files["wyniki.csv"]
    first = r1[0]["date"] if r1 else None
    last = r1[-1]["date"] if r1 else None
    # status RAZ, z kalendarza; przy dacie zapasowej — czy odczyt nie odbył się już wcześniej w oknie
    slot = plan_slot(as_of) if as_of is not None else None
    bound_at = None
    if slot is not None and as_of > slot[1] and last == as_of.isoformat():
        bound_at = first_full_snapshot(repo, slot[1], as_of)
    status = reading_status(as_of, last, bound_at)
    legs = []
    for leg in LEGS:
        rows = files[leg.file]
        if not rows or leg.column not in rows[0]:
            continue  # noga nieobecna w dzienniku (np. X1 przed Poprawką 3) — pomijana
        legs.append(leg_reading(leg, [r[leg.column] for r in rows], status))
    band = vol_band([r.get("r_port") for r in r1])
    last_run = state["health"]["last_journal_date"]
    warnings = []
    if as_of is None:
        age = (now.date() - date.fromisoformat(last_run)).days if last_run else None
        if age is None or age > STALE_DAYS:
            warnings.append(
                f"dziennik starszy niż {STALE_DAYS} dni (ostatni przebieg {last_run}) "
                "— zrób git fetch"
            )
    else:
        want = (as_of + timedelta(days=1)).isoformat()
        if last_run is None or last_run < want:
            warnings.append(
                f"migawka z przebiegu {last_run}, a nie {want} — git fetch albo przebieg nie doszedł"
            )
        if as_of >= R1_START and last != as_of.isoformat():  # przed startem R1 wyników brak
            warnings.append(f"migawka kończy się na dniu {last}, a nie na {as_of}")
    return {
        "v": 1,
        "generated_at": now.isoformat(timespec="minutes"),
        "ref": ref,
        "snapshot": {"commit_ts": state["repo"]["head_ts"], "last_run": last_run},
        "as_of": as_of.isoformat() if as_of else None,
        "window": {"first": first, "last": last, "n": band["n"], "days": status["days"]},
        "status": status,
        "warnings": warnings,
        "plan": {
            "days": list(READ_DAYS),
            "as_of": [d.isoformat() for d in PLAN_DATES],
            "z": Z_READ,
            "alpha": ALPHA,
        },
        "runs": n_runs,
        "log_unparsed": state["log_unparsed"],
        "mechanics": mechanics(state),
        # pasmo [13; 31] zapisano dla odczytu 1 (~92 dni); odczyty 2 i 3 — tylko opis
        "vol_band": {**band, "binding": status["binding"] and status["reading"] == 1},
        "legs": legs,
    }


# ------------------------------------------------------------------ wydruk


def _pct(x: float | None, nd: int = 1) -> str:
    return "—" if x is None else f"{100 * x:+.{nd}f} %"


def _short(ref: str) -> str:
    """Hash commita skracany do 12 znaków; nazwa refu (origin/master) bez zmian."""
    return ref[:12] if len(ref) == 40 and all(ch in "0123456789abcdef" for ch in ref) else ref


def _yn(ok) -> str:
    return "—" if ok is None else ("TAK" if ok else "NIE")


def render(rep: dict) -> str:
    """Raport tekstowy (prosty język, zasada 17)."""
    w, st = rep["window"], rep["status"]
    m = rep["mechanics"]
    snap = rep["snapshot"]
    lines = [
        "=" * 100,
        f"ODCZYT DZIENNIKA (szczebel 3 ADR-09) — wynik R1 {w['first']} → {w['last']}, "
        f"{w['days']} dni kalendarzowych ({w['n']} z wynikiem)",
        f"STATUS: {st['label']}",
        *(f"UWAGA: {x}" for x in rep["warnings"]),
        f"migawka {_short(rep['ref'])} (commit {snap['commit_ts']}, ostatni przebieg "
        f"{snap['last_run']}), przebiegi {rep['runs']} (nieczytelne {rep['log_unparsed']})",
        f"plan: --as-of {' / '.join(rep['plan']['as_of'])} "
        f"({'/'.join(map(str, rep['plan']['days']))} dni), z = {rep['plan']['z']:.2f}",
        "=" * 100,
        "Kryteria mechaniki (definicje: tools/strona_dziennika.build_state; progi: dziennik/README.md)",
    ]
    c1, c2, c3, c4 = (
        m["1_kompletnosc"],
        m["2_spojnosc"],
        m["3_terminowosc"],
        m["4_zgodnosc_sz1"],
    )
    lines += [
        f"  1. kompletność ≥ 95 % dni: {c1['covered']}/{c1['days']} ({_pct(c1['share'])[1:]}) "
        f"→ {_yn(c1['ok'])}" + (f"; brak: {', '.join(c1['missing'][:6])}" if c1["missing"] else ""),
        f"  2. spójność, 0 zmian historii po pierwszym wyniku: {c2['after_first_result']} "
        f"(wszystkich zdarzeń {c2['events']}) → {_yn(c2['ok'])}"
        + ("" if c2["ok"] else " — każde zdarzenie wyjaśnić w dokumentacji odczytu"),
        f"  3. terminowość ≥ 95 % dni: spóźnione {len(c3['late'])} z {c3['days']} "
        f"({_pct(c3['share'])[1:]}) → {_yn(c3['ok'])}",
        f"  4. depozyt mediana w [15; 35] %: {_pct(c4['margin']['median'])[1:]} "
        f"(min {_pct(c4['margin']['min'])[1:]}, max {_pct(c4['margin']['max'])[1:]}); "
        f"k maks. trend {c4['k_max']['trend']}, premia {c4['k_max']['coinbase']} (sufit {K_CAP}) "
        f"→ {_yn(c4['ok'])}",
    ]
    vb = rep["vol_band"]
    if vb["binding"]:
        tag = ""
    elif st["binding"]:
        tag = " [tylko opis: pasmo zapisane dla odczytu 1, ~92 dni]"
    else:
        tag = " [podgląd]"
    if vb["ok"] is None:
        res = "—"
    elif vb["binding"]:
        res = _yn(vb["ok"])
    else:
        res = "w paśmie" if vb["ok"] else "poza pasmem"
    lines.append(
        f"  4b. zmienność R1 w [13; 31] %/rok: {_pct(vb['vol'])[1:]} z {vb['n']} dni → {res}{tag}"
    )
    lines += [
        "",
        "Kryterium 5 — próg obalenia: średnia roczna < μ − z·SE, SE = σ/√(n/365) "
        "(μ, σ zakładane, arytmetyczne; źródła: dziennik/README.md)",
    ]
    for g in rep["legs"]:
        if g["n"] == 0:
            lines.append(f"  {g['key']:<4} brak danych (braki {g['missing']})")
            continue
        lines += [
            f"  {g['key']:<4} {g['name']}: n {g['n']} dni (braki {g['missing']}) — {g['label']}",
            f"       średnia {_pct(g['mean'])}/rok"
            + (
                f" (przedział 95 % {_pct(g['ci95'][0])} … {_pct(g['ci95'][1])})"
                if g["ci95"]
                else ""
            )
            + f"; Σ za okres {_pct(g['total'])}; zakładane "
            f"μ {_pct(g['mu'])}, σ {100 * g['sigma']:.1f} %; SE {100 * g['se']:.1f} %/rok",
            f"       próg obalenia {_pct(g['threshold'])}/rok (Σ za okres "
            f"{_pct(g['threshold_period'])}) → {g['verdict']}",
            f"       wykrycie zakładanego μ przy 2·SE wymaga ~{g['years_to_detect']:.1f} lat danych",
        ]
    lines += [
        "",
        "Brak obalenia ≠ potwierdzenie przewagi: próg odrzuca tylko wyniki wyraźnie gorsze od "
        "założeń; zakładanego zysku 3–12 miesięcy nie są w stanie potwierdzić.",
        "Skrypt jest reporterem — werdykt o strategii podpisuje Claude w dokumentacji odczytu.",
    ]
    if not st["binding"]:
        lines.append(f"UWAGA: {st['label']}.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Odczyt dziennika papierowego (szczebel 3 ADR-09).")
    ap.add_argument("--repo", default=".", help="klon repo alpha (czytany origin/master)")
    ap.add_argument("--as-of", type=date.fromisoformat, default=None, help="obcięcie RRRR-MM-DD")
    ap.add_argument("--json", action="store_true", help="wydruk JSON zamiast tekstu")
    args = ap.parse_args(argv)
    try:
        rep = reading(args.repo, args.as_of)
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"BŁĄD: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    else:
        print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
