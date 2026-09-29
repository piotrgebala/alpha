"""
run_pt1_tradfi.py — NEUTRALNY reporter rundy PT1: perpetuale TradFi na Bybit i Binance (spis, funding,
koszty, zamknięty rynek bazowy, zgodność z FRED). Liczy wyłącznie to, co zapisała pre-rejestracja
``runs/2026-09-28_pt1-perpy-tradfi/README.md``; ocenę wyników pisze sesja w README rundy.

Wejście (``data.fetch_tradfi_perps``): ``data/raw/tradfi_perps/`` — ``spis_*.parquet``,
``funding_*.parquet``, ``swiece_*_{last,index,mark}_1h.parquet``, ``premia_bybit_1m.parquet``,
``rdzen.json``, ``migawki/*.json.gz``. FRED przez ``data.fetch_external.fetch_fred`` do domyślnego
katalogu ``data/raw/external`` (istniejący plik NIE jest nadpisywany; data ostatniej obserwacji
jest drukowana). Wyjście: tabele na stdout + CSV w katalogu rundy (spis, funding, funding_wzor,
koszty, zamkniety_rynek, zgodnosc).

DEFINICJE (zapisane w kodzie przed pierwszym przebiegiem na danych):

Klasy: waluty, surowce, ETF, ETF_oblig (TLT/TBT/TMF), akcje (region US/HK/KR/CN), przed_IPO,
BTC_kontrola — ``fetch_tradfi_perps.klasa_bybit`` / ``klasa_binance``.

P1 — per klasa i giełda: liczba instrumentów, najwcześniejszy/najpóźniejszy start, mediana i maksimum
dni historii (do chwili ``teraz`` = najpóźniejszy odczyt fundingu w danych), interwał fundingu
ze spisu i z danych (najczęstszy odstęp odczytów), cap/floor, maks. dźwignia (Bybit; Binance publikuje
ją tylko z kluczem API).

P2 — funding płacony przez DŁUGĄ pozycję (stawka dodatnia = długa płaci), okno od 2025-12-01 (albo od
startu instrumentu) do ostatniego odczytu:
- odczyty/rok ``K = 8760 / Δ̄``, ``Δ̄ = (t_n − t_1)/(n − 1)`` godzin (średni odstęp odczytów; obejmuje
  interwały 4 h i 8 h, zmianę interwału w oknie i brakujące odczyty); ``f̂ = średnia · K`` (= suma
  stawek / (n · Δ̄) wyrażone w latach), w % rocznie;
- 95 % CI: ``(średnia ± 1,96 · sd / √N_eff) · K``; ``N_eff`` = kanoniczne ``effective_sample_size``
  (agents.labeling, importowane przez checkpoint_lib), ograniczone do ``[1, n]``;
- dziury = odstępy > 1,5 × lokalna mediana 7 sąsiednich odstępów;
  mediana · K; wartość modalna = najczęstsza stawka (zaokrąglona do 1e-10) i jej udział; modalna
  roczna = modalna · 8760 / Δ_mod (Δ_mod = najczęstszy odstęp odczytów);
- waluty, modele rocznego fundingu długiej (% rocznie): A = modalna roczna BTCUSDT tej samej giełdy;
  B = r(waluta kwotowana) − r(waluta bazowa) (EURUSD: r_USD − r_EUR, USDJPY: r_JPY − r_USD itd.)
  ze średniej dziennej (wartość obowiązująca danego dnia, as-of) stóp FRED w oknie fundingu pary —
  seria starsza niż 92 dni od końca okna → zamiennik ``IR3TIB01..``; C = 0;
  „CI zawiera” = modele z wartością w ``[ci_low, ci_high]`` (włącznie, tolerancja 1e-9 pkt proc.);
- pozostałe klasy: obok f̂ średnia ``DFF`` (r_USD) z okna instrumentu;
- Binance ``interestRate`` z ``premiumIndex`` w migawkach: wartość najczęstsza per symbol;
- druga droga (Bybit, ``PREMIA_SYMBOLE``): ``F̂ = P̄ + clamp(I − P̄, −0,05 %, +0,05 %)``, ``P̄`` =
  średnia minutowych zamknięć indeksu premii w ``[T − Δ, T)``, Δ = odstęp od poprzedniego odczytu
  (pierwszy: Δ_mod), ``I = 0,01 % · Δ / 8 h`` albo ``I = 0``; ``F̂`` przycięte do [floor, cap] ze spisu;
  odczyt liczony, gdy ≥ 90 % minut okna ma indeks premii. Warianty dodatkowe: ``waz_*`` — P̄ ważone
  liniowo (waga minuty 1, 2, …, n; średnia z dokumentacji Bybit „Introduction to Funding Rate”);
  ``twap_*`` — TWAP minutowych F (zacisk na każdej minucie, potem średnia). Zgodność: |F̂ − F| ≤ 0,00005 (= 0,005 % = 0,5 pb)
  i ≤ 0,000005 (0,05 pb), średni błąd F̂ − F, mediana |F̂ − F|.

P3 — z migawek: pełny spread ``(ask − bid) / mid · 1e4`` pb (kwotowanie bez ceny, zerowe albo
odwrócone = anomalia, poza medianą); mediana po migawkach — wszystkie, w sesji USA (kalendarz
``akcje_usa``: dziś 13:30–20:00 UTC) i poza; obrót 24 h (mediana po migawkach); koszt strony =
mediana spreadu / 2 + taker — oficjalna stawka TradFi (``TAKER_TRADFI``; BTCUSDT: ``TAKER_STANDARD``),
obok koszt przy stawce standardowej; stosunek do KO1 (0,07 %).

P4 — rdzeń; kalendarze stałe (``przedzialy_otwarcia``), czas letni USA 2025-03-09 07:00 –
2025-11-02 06:00 UTC i 2026-03-08 07:00 – 2026-11-01 06:00 UTC (dane poza zakresem tablic —
``ZAKRES_DST_USA``, ``ZAKRES_SWIAT_NYSE`` — → ``ValueError``, nie ciche przesunięcie o 1 h):
- ``akcje_usa`` (akcje, ETF, ETF_oblig; BTC_kontrola jako kontrola): pn–pt 13:30–20:00 UTC latem,
  14:30–21:00 zimą; święta NYSE ``SWIETA_NYSE`` zamknięte;
- ``waluty``: zamknięte pt 21:00 → nd 21:00 UTC latem (zimą 22:00 → 22:00);
- ``surowce``: zamknięte pt 21:00 → nd 22:00 UTC latem + codzienna przerwa pn–czw 21:00–22:00
  (zimą wszystko +1 h).
Świeca 1 h ``[t, t+1h)`` jest „otwarta”, gdy cała leży w godzinach otwarcia, „zamknięta”, gdy cała
poza nimi; mieszane pomijane. (a) udział świec indeksu bez zmiany (high == low); (b) |bazis| =
|close ceny ostatniej / close indeksu − 1|: mediana i p95; (c) zamknięcie ``[c, o)`` (c, o z kalendarza):
``R = ln(last_close(świeca od floor_h(o) − 1h) / last_close(świeca od c − 1h))`` — perp od zamknięcia
do ostatniej pełnej godziny przed otwarciem; ``G = ln(index_close(świeca od floor_h(o)) /
index_close(świeca od c − 1h))`` — indeks od zamknięcia do końca pierwszej godziny po otwarciu
(akcje latem: R = pt 19:00 → pn 12:00, G = pt 19:00 → pn 13:00 wg czasu otwarcia świec; zimą +1 h);
MNK ``G = α + β R``, R², n; typy: „weekend” (zamknięcie obejmujące dzień bez sesji, także święta),
„noc” (akcje/ETF: kolejne dni sesji), „przerwa” (surowce, ≤ 2 h — poza pomiarem);
(d) średni funding (roczny, ·K jak w P2): (d1, główna — dosłownie „odczyty przy zamkniętym vs otwartym
rynku”) wg stanu rynku w chwili rozliczenia T; (d2, dodatkowo) wg przedziału naliczania ``[T − Δ, T)``:
w całości zamknięty / w całości otwarty / częściowo (przy interwale 8 h i sesji akcji 6,5 h kategoria
„w całości otwarty” jest pusta z konstrukcji).

P5 — dzienne serie FRED vs indeks giełdy o 16:00 UTC (czas letni USA; zimą 17:00) = close świecy
indeksu kończącej się o tej godzinie; dni z obiema wartościami; korelacja dziennych zwrotów log
(kolejne wspólne dni), mediana |poziom / FRED − 1| (waluty, ropa), n. Wariant dodatkowy (poza
pre-rejestracją): SPY/QQQ o zamknięciu NYSE (20:00 UTC latem, 21:00 zimą), bo SP500/NASDAQ100 to
kursy zamknięcia.

    PYTHONUTF8=1 py -m backtest.run_pt1_tradfi 2>&1 | tee runs/2026-09-28_pt1-perpy-tradfi/raw_output.txt
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import warnings
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.checkpoint_lib import effective_sample_size
from data import fetch_external as fe
from data import fetch_tradfi_perps as ft

DANE = ft.OUT
RUNDA = Path("runs/2026-09-28_pt1-perpy-tradfi")
FRED_DIR = Path(fe.DEFAULT_OUT_DIR)
FRED_START = fe.DEFAULT_START
H = pd.Timedelta(hours=1)
H_NS = 3_600_000_000_000
GODZIN_ROK = 365 * 24
Z95 = 1.959964
TOL_CI = 1e-9  # pkt proc. rocznie
MAX_STAROSC_DNI = 92  # seria stóp „nieaktualna > 3 mies.”
# Opłaty taker (ułamek nominału), sprawdzone 2026-09-28 na stronach giełd. Standard perpetuali USDT:
# Bybit 0,055 %, Binance 0,05 % (tu: BTCUSDT). Oficjalne stawki TradFi (promocje „do odwołania”):
# Bybit 0,0275 % (VIP0, harmonogram TradFi od 2026-06-16; announcements.bybit.com — „TradFi
# Perpetuals: Lower Fees Across All Tiers”), Binance 0,04 % (regular; promocja od 2026-03-31,
# binance.com/en/support/announcement/detail/a4c3f1957f2b4e69902985154235c3b1).
TAKER_STANDARD = {"bybit": 0.00055, "binance": 0.0005}
TAKER_TRADFI = {"bybit": 0.000275, "binance": 0.0004}
KO1_KOSZT = 0.0007
I_8H = 0.0001
ZACISK = 0.0005
TOL_WZOR = 0.00005
TOL_WZOR_SCISLA = 0.000005
MIN_POKRYCIE = 0.9

DST_USA = (
    (pd.Timestamp("2025-03-09 07:00", tz="UTC"), pd.Timestamp("2025-11-02 06:00", tz="UTC")),
    (pd.Timestamp("2026-03-08 07:00", tz="UTC"), pd.Timestamp("2026-11-01 06:00", tz="UTC")),
)
SWIETA_NYSE = frozenset(
    dt.date.fromisoformat(d)
    for d in (
        "2025-12-25",
        "2026-01-01",
        "2026-01-19",
        "2026-02-16",
        "2026-04-03",
        "2026-05-25",
        "2026-06-19",
        "2026-07-03",
        "2026-09-07",
    )
)
# Zakresy, w których tablice rozstrzygają POPRAWNIE ([od, do), UTC). Kalendarz poza nimi → ValueError
# zamiast cichego błędu (godziny sesji przesunięte o 1 h, święto liczone jako dzień sesji); nowy okres
# = dopisać tablice. DST_USA: między zmianami czasu spoza tablicy — koniec lata 2024 (2024-11-03
# 06:00) i początek lata 2027 (2027-03-14 07:00; obie granice zgodne z tzdata America/New_York).
# SWIETA_NYSE: między świętami spoza tablicy — 2025-11-27 i 2026-11-26 (Święto Dziękczynienia).
ZAKRES_DST_USA = (
    pd.Timestamp("2024-11-03 06:00", tz="UTC"),
    pd.Timestamp("2027-03-14 07:00", tz="UTC"),
)
ZAKRES_SWIAT_NYSE = (pd.Timestamp("2025-11-28", tz="UTC"), pd.Timestamp("2026-11-26", tz="UTC"))
KALENDARZ_KLASY = {
    "akcje": "akcje_usa",
    "ETF": "akcje_usa",
    "ETF_oblig": "akcje_usa",
    "waluty": "waluty",
    "surowce": "surowce",
    "BTC_kontrola": "akcje_usa",
}
STOPY = {  # waluta → (seria główna FRED, zamiennik)
    "USD": ("DFF", None),
    "EUR": ("ECBDFR", "IR3TIB01EZM156N"),
    "GBP": ("IUDSOIA", "IR3TIB01GBM156N"),
    "JPY": ("IRSTCI01JPM156N", "IR3TIB01JPM156N"),
    # BRL bez zamiennika: IR3TIB01BRM156N nie istnieje we FRED (HTTP 404 przy pobieraniu 2026-09-28)
    "BRL": ("IRSTCI01BRM156N", None),
}
ZGODNOSC = {  # symbol perpa → (seria FRED, czy porównywać poziom)
    "EURUSDUSDT": ("DEXUSEU", True),
    "GBPUSDUSDT": ("DEXUSUK", True),
    "USDJPYUSDT": ("DEXJPUS", True),
    "USDBRLUSDT": ("DEXBZUS", True),
    "BZUSDT": ("DCOILBRENTEU", True),
    "CLUSDT": ("DCOILWTICO", True),
    "SPYUSDT": ("SP500", False),
    "QQQUSDT": ("NASDAQ100", False),
}
KOLEJNOSC_KLAS = ("waluty", "surowce", "ETF", "ETF_oblig", "akcje", "przed_IPO", "BTC_kontrola")


# ------------------------------------------------------------------ kalendarze (czyste)
def czas_letni_usa(ts) -> bool:
    """
    Czy chwila ``ts`` (UTC) wypada w czasie letnim USA (granice ``DST_USA``, lewostronnie
    domknięte). Chwila poza ``ZAKRES_DST_USA`` → ``ValueError`` (tablica nie mówi nic o innych
    latach).
    """
    ts = pd.Timestamp(ts)
    lo, hi = ZAKRES_DST_USA
    if not lo <= ts < hi:
        raise ValueError(
            f"czas letni USA: {ts} poza zakresem tablicy DST_USA [{lo}, {hi}) "
            "(kalendarze liczone z zapasem 8 dni) — dopisz granice czasu letniego na kolejny rok; "
            "bez tego godziny sesji przesunęłyby się o 1 h"
        )
    return any(a <= ts < b for a, b in DST_USA)


def _letnia(t: pd.Timestamp) -> pd.Timestamp:
    """Godzina podana w czasie letnim → ta sama godzina zimą przesunięta o +1 h."""
    return t if czas_letni_usa(t) else t + H


def przedzialy_otwarcia(kalendarz: str, od, do) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Przedziały otwarcia rynku bazowego ``[start, koniec)`` (UTC) pokrywające ``[od, do]`` z zapasem
    8 dni. ``akcje_usa``: ``[od, do]`` poza ``ZAKRES_SWIAT_NYSE`` → ``ValueError``; czas letni
    sprawdza ``czas_letni_usa`` (każdy kalendarz, łącznie z zapasem).
    """
    if kalendarz == "akcje_usa":
        lo, hi = ZAKRES_SWIAT_NYSE
        if pd.Timestamp(od) < lo or pd.Timestamp(do) >= hi:
            raise ValueError(
                f"kalendarz akcje_usa: dane {od} … {do} poza zakresem tablicy SWIETA_NYSE "
                f"[{lo.date()}, {hi.date()}) UTC — dopisz święta NYSE; bez tego święto liczyłoby "
                "się jako dzień sesji"
            )
    dni = pd.date_range(
        pd.Timestamp(od).normalize() - pd.Timedelta(days=8),
        pd.Timestamp(do).normalize() + pd.Timedelta(days=8),
        freq="D",
    )
    out: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    if kalendarz == "akcje_usa":
        for d in dni:
            if d.weekday() >= 5 or d.date() in SWIETA_NYSE:
                continue
            s = _letnia(d + pd.Timedelta(hours=13, minutes=30))
            out.append((s, s + pd.Timedelta(hours=6, minutes=30)))
    elif kalendarz == "waluty":
        for d in dni:
            if d.weekday() == 6:  # niedziela → piątek
                out.append(
                    (
                        _letnia(d + pd.Timedelta(hours=21)),
                        _letnia(d + pd.Timedelta(days=5, hours=21)),
                    )
                )
    elif kalendarz == "surowce":
        for d in dni:
            if d.weekday() != 6:
                continue
            s = _letnia(d + pd.Timedelta(hours=22))
            for k in range(1, 6):  # pn..pt: zamknięcie 21:00, pn..czw: wznowienie 22:00
                dzien = d + pd.Timedelta(days=k)
                out.append((s, _letnia(dzien + pd.Timedelta(hours=21))))
                s = _letnia(dzien + pd.Timedelta(hours=22))
    else:
        raise ValueError(f"nieznany kalendarz {kalendarz!r}")
    return out


def _ns(t) -> np.ndarray:
    """Znaczniki czasu (skalar, lista, Series, DatetimeIndex) → int64 ns UTC."""
    idx = pd.DatetimeIndex(pd.to_datetime(pd.Series(np.atleast_1d(t)), utc=True))
    return idx.as_unit("ns").asi8


class Kalendarz:
    """Przedziały otwarcia jako tablice ns; udział otwarcia dowolnego przedziału i lista zamknięć."""

    def __init__(self, nazwa: str, od, do) -> None:
        self.nazwa = nazwa
        prz = przedzialy_otwarcia(nazwa, od, do)
        self.s = np.array([a.value for a, _ in prz], dtype=np.int64)
        self.e = np.array([b.value for _, b in prz], dtype=np.int64)
        if len(self.s) and (np.any(self.e <= self.s) or np.any(self.s[1:] < self.e[:-1])):
            raise ValueError(f"kalendarz {nazwa}: przedziały nachodzą na siebie")
        self.cum = np.concatenate([[0], np.cumsum(self.e - self.s)])

    def _otwarte_do(self, t: np.ndarray) -> np.ndarray:
        i = np.searchsorted(self.s, t, side="right") - 1
        out = np.zeros(len(t), dtype=float)
        ok = i >= 0
        ii = i[ok]
        out[ok] = self.cum[ii] + np.minimum(t[ok], self.e[ii]) - self.s[ii]
        return out

    def udzial(self, t0, t1) -> np.ndarray:
        """Udział czasu otwarcia w przedziałach ``[t0, t1)`` (wektorowo)."""
        a, b = _ns(t0), _ns(t1)
        return (self._otwarte_do(b) - self._otwarte_do(a)) / (b - a)

    def otwarty(self, t) -> np.ndarray:
        """Czy rynek jest otwarty w chwili ``t`` (wektorowo)."""
        x = _ns(t)
        i = np.searchsorted(self.s, x, side="right") - 1
        return (i >= 0) & (x < self.e[np.clip(i, 0, None)])

    def zamkniecia(self) -> list[tuple[pd.Timestamp, pd.Timestamp, str]]:
        """Zamknięcia ``[c, o)`` między kolejnymi przedziałami otwarcia z typem weekend/noc/przerwa."""
        out = []
        for c, o in zip(self.e[:-1], self.s[1:], strict=True):
            c_t, o_t = pd.Timestamp(c, tz="UTC"), pd.Timestamp(o, tz="UTC")
            if o_t - c_t <= pd.Timedelta(hours=2):
                typ = "przerwa"
            elif self.nazwa == "akcje_usa" and (o_t.normalize() - c_t.normalize()).days == 1:
                typ = "noc"
            else:
                typ = "weekend"
            out.append((c_t, o_t, typ))
        return out


def stan_godzin(kal: Kalendarz, starty) -> np.ndarray:
    """Świece 1 h od ``starty``: 1 = cała otwarta, 0 = cała zamknięta, NaN = mieszana."""
    t0 = pd.DatetimeIndex(pd.to_datetime(pd.Series(starty), utc=True))
    u = kal.udzial(t0, t0 + H)
    return np.where(u >= 1 - 1e-12, 1.0, np.where(u <= 1e-12, 0.0, np.nan))


# ------------------------------------------------------------------ P2 (czyste)
def statystyki_fundingu(czasy, stawki) -> dict:
    """Statystyki fundingu jednego instrumentu (definicje P2 w docstringu modułu); roczne w % rocznie."""
    t = pd.DatetimeIndex(pd.to_datetime(pd.Series(czasy), utc=True)).as_unit("ns")
    x = pd.Series(np.asarray(stawki, dtype=float))
    order = np.argsort(t.asi8, kind="stable")  # asi8 w ns dzięki as_unit
    t, x = t[order], x.iloc[order].reset_index(drop=True)
    n = len(x)
    wynik = {"n": n, "pierwszy": t[0] if n else pd.NaT, "ostatni": t[-1] if n else pd.NaT}
    if n < 2:
        return wynik | {k: float("nan") for k in _KLUCZE_P2}
    dt_h = np.diff(t.asi8) / H_NS
    interwal_sr = float((t.asi8[-1] - t.asi8[0]) / H_NS / (n - 1))
    odstepy = pd.Series(np.round(dt_h, 2))
    interwal_mod = float(odstepy.value_counts().sort_index().idxmax())
    k = GODZIN_ROK / interwal_sr
    # dziura = odstęp > 1,5 × lokalna mediana 7 sąsiednich odstępów (zmiana interwału 8 h → 4 h
    # nie jest dziurą; brakujący odczyt albo pominięty weekend — jest)
    lokalny = pd.Series(dt_h).rolling(7, center=True, min_periods=1).median().to_numpy()
    with warnings.catch_warnings():
        # autokorelacja stałej (np. same zera) albo krótkiej serii → NaN z ostrzeżeniem numpy;
        # funkcja kanoniczna pomija takie opóźnienia (N_eff = n przy braku autokorelacji)
        warnings.simplefilter("ignore", RuntimeWarning)
        n_eff = max(1.0, min(float(effective_sample_size(x)["n_eff"]), float(n)))
    m, sd = float(x.mean()), float(x.std(ddof=1))
    se = sd / math.sqrt(n_eff)
    licz = x.round(10).value_counts()
    najczestsza = licz.max()
    modalna = float(min(v for v, c in licz.items() if c == najczestsza))
    return wynik | {
        "n_eff": n_eff,
        "interwal_mod_h": interwal_mod,
        "interwal_sr_h": interwal_sr,
        "odczyty_rok": k,
        "f_rok": m * k * 100,
        "ci_low": (m - Z95 * se) * k * 100,
        "ci_high": (m + Z95 * se) * k * 100,
        "mediana_rok": float(x.median()) * k * 100,
        "modalna": modalna,
        "modalna_udzial": float(najczestsza / n),
        "modalna_rok": modalna * GODZIN_ROK / interwal_mod * 100,
        "dziury": int((dt_h > 1.5 * lokalny).sum()),
        "odstepy_krotsze": int((dt_h < 0.5 * lokalny).sum()),
    }


_KLUCZE_P2 = (
    "n_eff",
    "interwal_mod_h",
    "interwal_sr_h",
    "odczyty_rok",
    "f_rok",
    "ci_low",
    "ci_high",
    "mediana_rok",
    "modalna",
    "modalna_udzial",
    "modalna_rok",
    "dziury",
    "odstepy_krotsze",
)


def ci_zawiera(lo: float, hi: float, modele: dict[str, float], tol: float = TOL_CI) -> str:
    """Modele, których wartość leży w ``[lo, hi]`` (włącznie, z tolerancją); „żaden” / „brak danych”."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "brak danych"
    w = [k for k, v in modele.items() if math.isfinite(v) and lo - tol <= v <= hi + tol]
    return ",".join(w) if w else "żaden"


def stopa_srednia(seria: pd.DataFrame, od, do) -> float:
    """Średnia dzienna (as-of: ostatnia obserwacja ≤ dzień) serii FRED ``date, value`` w ``[od, do]`` (dni UTC)."""
    s = seria.dropna(subset=["value"]).set_index("date")["value"].sort_index()
    dni = pd.date_range(pd.Timestamp(od).normalize(), pd.Timestamp(do).normalize(), freq="D")
    wart = s.reindex(s.index.union(dni)).ffill().reindex(dni)
    return float(wart.mean()) if wart.notna().any() else float("nan")


def wybierz_stope(
    waluta: str, fred: dict[str, pd.DataFrame], koniec
) -> tuple[str, pd.DataFrame | None]:
    """Seria stopy waluty: główna, a gdy jej ostatnia obserwacja jest starsza niż 92 dni od ``koniec`` — zamiennik."""
    glowna, zamiennik = STOPY[waluta]
    df = fred.get(glowna)
    if df is not None and df["value"].notna().any():
        ostatnia = df.dropna(subset=["value"])["date"].max()
        if (pd.Timestamp(koniec) - ostatnia).days <= MAX_STAROSC_DNI or zamiennik is None:
            return glowna, df
    if zamiennik is not None and fred.get(zamiennik) is not None:
        return zamiennik, fred[zamiennik]
    return glowna, df


def model_b(baza: str, fred: dict[str, pd.DataFrame], od, do) -> tuple[float, str]:
    """Model B dla pary ``BAZAKWOT`` (np. EURUSD): r(kwotowana) − r(bazowa) w % rocznie + opis serii."""
    b, q = baza[:3], baza[3:6]
    nb, sb = wybierz_stope(b, fred, do)
    nq, sq = wybierz_stope(q, fred, do)
    if sb is None or sq is None:
        return float("nan"), f"{nq}−{nb} (brak serii)"
    return stopa_srednia(sq, od, do) - stopa_srednia(sb, od, do), f"{nq}−{nb}"


# ------------------------------------------------------------------ druga droga P2 (czyste)
def funding_ze_wzoru(
    p_sr, interwal_h, i_8h: float = I_8H, zacisk: float = ZACISK, cap=np.inf, floor=-np.inf
):
    """``F = P̄ + clamp(I − P̄, −zacisk, +zacisk)``, ``I = i_8h · interwał/8 h``, potem przycięcie do [floor, cap]."""
    i = i_8h * np.asarray(interwal_h, dtype=float) / 8.0
    p = np.asarray(p_sr, dtype=float)
    return np.clip(p + np.clip(i - p, -zacisk, zacisk), floor, cap)


def odtworz_funding(
    funding: pd.DataFrame, premia: pd.DataFrame, cap: float = np.inf, floor: float = -np.inf
) -> pd.DataFrame:
    """
    Odczyty ``funding`` (czas, fundingRate) jednego symbolu vs wzór z minutowego indeksu premii
    ``premia`` (czas = otwarcie minuty, close). Kolumny wariantów (I = 0,01 %/8 h skalowane albo 0):
    ``wzor_*`` (P̄ = zwykła średnia), ``waz_*`` (P̄ ważone liniowo 1…n), ``twap_*`` (średnia minutowych F).
    """
    f = funding.sort_values("czas").reset_index(drop=True)
    pm = premia.sort_values("czas")
    pt, pv = _ns(pm["czas"]), pm["close"].to_numpy(dtype=float)
    t = _ns(f["czas"])
    st = statystyki_fundingu(f["czas"], f["fundingRate"]) if len(f) >= 2 else {}
    delta_h = np.diff(t, prepend=t[0] - int(st.get("interwal_mod_h", 8.0) * H_NS)) / H_NS
    wiersze = []
    for ti, dh, fr in zip(t, delta_h, f["fundingRate"].to_numpy(dtype=float), strict=True):
        a, b = np.searchsorted(pt, ti - int(dh * H_NS), side="left"), np.searchsorted(
            pt, ti, side="left"
        )
        okno = pv[a:b]
        pokrycie = len(okno) / (dh * 60) if dh > 0 else 0.0
        rek = {"czas": pd.Timestamp(ti, tz="UTC"), "interwal_h": dh, "pokrycie": pokrycie, "F": fr}
        p_sr = float(okno.mean()) if len(okno) else float("nan")
        wagi = np.arange(1, len(okno) + 1, dtype=float)
        p_waz = float((okno * wagi).sum() / wagi.sum()) if len(okno) else float("nan")
        rek["p_sr"], rek["p_waz"] = p_sr, p_waz
        for nazwa, i8 in (("I", I_8H), ("0", 0.0)):
            rek[f"wzor_{nazwa}"] = float(funding_ze_wzoru(p_sr, dh, i8, cap=cap, floor=floor))
            rek[f"waz_{nazwa}"] = float(funding_ze_wzoru(p_waz, dh, i8, cap=cap, floor=floor))
            twap = funding_ze_wzoru(okno, dh, i8) if len(okno) else np.array([np.nan])
            rek[f"twap_{nazwa}"] = float(np.clip(np.mean(twap), floor, cap))
        wiersze.append(rek)
    return pd.DataFrame(wiersze)


def zgodnosc_wzoru(odtw: pd.DataFrame, wariant: str) -> dict:
    """Zgodność wariantu wzoru z odczytami (tylko odczyty z pokryciem ≥ ``MIN_POKRYCIE``)."""
    d = odtw.loc[odtw["pokrycie"] >= MIN_POKRYCIE]
    err = (d[wariant] - d["F"]).dropna()
    n = len(err)
    return {
        "n": n,
        "zgodne_0_5pb": float((err.abs() <= TOL_WZOR).mean()) if n else float("nan"),
        "zgodne_0_05pb": float((err.abs() <= TOL_WZOR_SCISLA).mean()) if n else float("nan"),
        "sredni_blad": float(err.mean()) if n else float("nan"),
        "mediana_abs_bledu": float(err.abs().median()) if n else float("nan"),
    }


# ------------------------------------------------------------------ P3 (czyste)
def spread_pb(bid, ask) -> np.ndarray:
    """Pełny spread w pb; brak ceny, zero albo ask < bid → NaN."""
    b, a = np.asarray(bid, dtype=float), np.asarray(ask, dtype=float)
    ok = (b > 0) & (a > 0) & (a >= b)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(ok, (a - b) / ((a + b) / 2) * 1e4, np.nan)


# ------------------------------------------------------------------ P4 (czyste)
def luki_zamkniec(
    zamkniecia, last: pd.Series, index: pd.Series, typy=("weekend", "noc")
) -> pd.DataFrame:
    """
    R i G dla każdego zamknięcia ``[c, o)`` (definicja w docstringu modułu); ``last``/``index`` =
    close świec 1 h indeksowane czasem OTWARCIA świecy (UTC). Brak którejkolwiek świecy → pominięte.
    """
    wiersze = []
    for c, o, typ in zamkniecia:
        if typ not in typy:
            continue
        b_c, b_g = c - H, o.floor("h")
        b_r = b_g - H
        try:
            lc, lr, ic, ig = last[b_c], last[b_r], index[b_c], index[b_g]
        except KeyError:
            continue
        if min(lc, lr, ic, ig) <= 0 or not all(map(math.isfinite, (lc, lr, ic, ig))):
            continue
        wiersze.append({"c": c, "o": o, "typ": typ, "R": math.log(lr / lc), "G": math.log(ig / ic)})
    return pd.DataFrame(wiersze, columns=["c", "o", "typ", "R", "G"])


def mnk(r, g) -> dict:
    """MNK ``g = α + β r``: β, α, R², n (β NaN, gdy n < 3 albo r stałe)."""
    r, g = np.asarray(r, dtype=float), np.asarray(g, dtype=float)
    n = len(r)
    if n < 3 or np.var(r) == 0:
        return {"n": n, "beta": float("nan"), "alfa": float("nan"), "r2": float("nan")}
    beta = float(np.cov(r, g, ddof=1)[0, 1] / np.var(r, ddof=1))
    alfa = float(g.mean() - beta * r.mean())
    r2 = float(np.corrcoef(r, g)[0, 1] ** 2) if np.var(g) > 0 else float("nan")
    return {"n": n, "beta": beta, "alfa": alfa, "r2": r2}


# ------------------------------------------------------------------ P5 (czyste)
def indeks_o_godzinie(index: pd.Series, daty, godz_lato: int = 16) -> pd.Series:
    """Close świecy indeksu kończącej się o ``godz_lato`` UTC (czas letni USA) albo godzinę później (zimą)."""
    out = {}
    for d in pd.DatetimeIndex(daty):
        t = _letnia(d.normalize() + pd.Timedelta(hours=godz_lato))
        out[d.normalize()] = index.get(t - H, np.nan)
    return pd.Series(out, dtype=float)


def zgodnosc_z_fred(
    index: pd.Series, fred: pd.DataFrame, poziom: bool, godz_lato: int = 16
) -> dict:
    """Korelacja dziennych zwrotów log (kolejne wspólne dni) i mediana |poziom/FRED − 1| (gdy ``poziom``)."""
    f = fred.dropna(subset=["value"]).set_index("date")["value"]
    f.index = pd.DatetimeIndex(f.index).normalize()
    if index.empty:
        return {"n_dni": 0, "n_zwrotow": 0, "korelacja": float("nan"), "mediana_odch": float("nan")}
    lo, hi = index.index.min().normalize(), index.index.max().normalize()
    f = f[(f.index >= lo) & (f.index <= hi)]
    ix = indeks_o_godzinie(index, f.index, godz_lato)
    razem = pd.DataFrame({"perp": ix, "fred": f}).dropna()
    razem = razem[(razem["perp"] > 0) & (razem["fred"] > 0)]
    zw = np.log(razem).diff().dropna()
    kor = float(zw["perp"].corr(zw["fred"])) if len(zw) >= 3 else float("nan")
    odch = (
        float((razem["perp"] / razem["fred"] - 1).abs().median())
        if poziom and len(razem)
        else float("nan")
    )
    return {"n_dni": len(razem), "n_zwrotow": len(zw), "korelacja": kor, "mediana_odch": odch}


# ------------------------------------------------------------------ wczytanie danych
KOLUMNY_MIGAWEK = ("czas", "gielda", "symbol", "bid", "ask", "obrot24h", "interestRate")
# uszkodzony plik migawki: ucięty/zły gzip (OSError, EOFError, zlib.error), zły JSON albo zła treść
# (ValueError), brak klucza (KeyError), zły typ (TypeError)
BLEDY_MIGAWKI = (OSError, EOFError, zlib.error, ValueError, KeyError, TypeError)


def _wiersze_migawki(p: Path, symbole: dict[str, set[str]]) -> list[dict]:
    """Jedna migawka → wiersze; plik uszkodzony albo zła treść → wyjątek (cały plik odpada)."""
    num = ft._liczba_lub_nan
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    if not isinstance(d, dict):
        raise ValueError(f"migawka: oczekiwano obiektu JSON, jest {type(d).__name__}")
    ft.sprawdz_migawke(d)
    czas = pd.Timestamp(d["czas_utc"])
    if pd.isna(czas) or czas.tzinfo is None:
        raise ValueError(f"migawka: zły czas_utc {d['czas_utc']!r}")
    wiersze = []
    for r in ft._wynik_bybit(d["bybit_tickers"])["list"]:
        if r.get("symbol") in symbole["bybit"]:
            wiersze.append(
                {
                    "czas": czas,
                    "gielda": "bybit",
                    "symbol": r["symbol"],
                    "bid": num(r.get("bid1Price")),
                    "ask": num(r.get("ask1Price")),
                    "obrot24h": num(r.get("turnover24h")),
                    "interestRate": float("nan"),
                }
            )
    book = {r["symbol"]: r for r in d["binance_book"]}
    h24 = {r["symbol"]: r for r in d["binance_24h"]}
    prem = {r["symbol"]: r for r in d["binance_premium"]}
    for s in sorted(symbole["binance"]):
        b, h, pr = book.get(s, {}), h24.get(s, {}), prem.get(s, {})
        wiersze.append(
            {
                "czas": czas,
                "gielda": "binance",
                "symbol": s,
                "bid": num(b.get("bidPrice")),
                "ask": num(b.get("askPrice")),
                "obrot24h": num(h.get("quoteVolume")),
                "interestRate": num(pr.get("interestRate")),
            }
        )
    return wiersze


def wczytaj_migawki(katalog: Path, symbole: dict[str, set[str]]) -> pd.DataFrame:
    """
    Migawki → wiersze (czas, giełda, symbol, bid, ask, obrót 24 h, interestRate Binance). Plik
    uszkodzony (ucięty gzip, zły JSON) albo ze złą treścią (błąd Bybit w odpowiedzi HTTP 200,
    słownik zamiast listy u Binance) jest pomijany w całości; nazwy i licznik pominiętych idą
    na stdout.
    """
    pliki = sorted(katalog.glob("*.json.gz"))
    wiersze, pominiete = [], []
    for p in pliki:
        try:
            wiersze += _wiersze_migawki(p, symbole)
        except BLEDY_MIGAWKI as exc:
            pominiete.append(p.name)
            print(f"[pt1] migawka pominięta (uszkodzona): {p.name}: {exc!r}")
    print(
        f"[pt1] migawki: wczytane {len(pliki) - len(pominiete)} z {len(pliki)}, "
        f"pominięte (uszkodzone): {len(pominiete)}"
    )
    return pd.DataFrame(wiersze, columns=list(KOLUMNY_MIGAWEK))


def wczytaj_fred(serie, katalog: Path = FRED_DIR) -> dict[str, pd.DataFrame]:
    """Serie FRED przez ``fetch_fred`` (pobiera tylko brakujące pliki; istniejących nie nadpisuje)."""
    out = {}
    for s in serie:
        path = fe.target_path(katalog, f"fred_{s}_1d")
        if not path.exists():
            try:
                fe.fetch_fred(s, FRED_START, katalog)
            except Exception as exc:  # noqa: BLE001 — brak serii = NaN w tabeli, nie przerwanie
                print(f"[pt1] FRED {s}: błąd pobierania {exc!r}")
        if path.exists():
            out[s] = pd.read_parquet(path)
    return out


# ------------------------------------------------------------------ pomocnicze do druku
def _druk(tytul: str, df: pd.DataFrame, nd: int | None = None) -> None:
    """Tabela z tytułem; ``nd`` = zaokrąglenie tylko kolumn liczbowych."""
    print(f"\n=== {tytul} ===")
    if nd is not None and len(df):
        df = df.copy()
        num = df.select_dtypes("number").columns
        df[num] = df[num].round(nd)
    print(df.to_string(index=False) if len(df) else "(brak wierszy)")


def _licz(seria: pd.Series, maks: int = 4) -> str:
    """Rozkład wartości jako tekst „wartość:liczba” (najczęstsze najpierw)."""
    vc = seria.dropna().value_counts()
    txt = ", ".join(f"{_fmt(k)}:{v}" for k, v in vc.head(maks).items())
    return txt + (f", … ({len(vc)} wartości)" if len(vc) > maks else "")


def _fmt(x) -> str:
    if isinstance(x, float):
        return f"{x:g}"
    return str(x)


def _klasy_sort(df: pd.DataFrame) -> pd.DataFrame:
    kol = {k: i for i, k in enumerate(KOLEJNOSC_KLAS)}
    return df.sort_values(["gielda", "klasa"], key=lambda s: s.map(kol) if s.name == "klasa" else s)


# ------------------------------------------------------------------ P1 + P2
def tabela_funding(spis: dict, funding: dict, fred: dict, interest: pd.Series) -> pd.DataFrame:
    """Wiersz na instrument: statystyki P2, modele A/B/C (waluty), r_USD z okna, interestRate Binance."""
    wiersze = []
    modele_a = {}
    for g in ("bybit", "binance"):
        f = funding[g]
        btc = f[f["symbol"] == ft.KONTROLA]
        modele_a[g] = statystyki_fundingu(btc["czas"], btc["fundingRate"]).get(
            "modalna_rok", np.nan
        )
        for _, w in spis[g].iterrows():
            fs = f[f["symbol"] == w["symbol"]]
            st = statystyki_fundingu(fs["czas"], fs["fundingRate"])
            rek = {
                "gielda": g,
                "symbol": w["symbol"],
                "klasa": w["klasa"],
                "region": w["region"],
                "interwal_h_spis": w["interwal_h"],
                **st,
            }
            od, do = st["pierwszy"], st["ostatni"]
            if st["n"] >= 2:
                rek["r_usd"] = stopa_srednia(fred["DFF"], od, do) if "DFF" in fred else np.nan
            if w["klasa"] == "waluty" and st["n"] >= 2:
                b, opis = model_b(w["baza"], fred, od, do)
                rek |= {"model_A": modele_a[g], "model_B": b, "model_B_serie": opis, "model_C": 0.0}
                rek["ci_zawiera"] = ci_zawiera(
                    st["ci_low"], st["ci_high"], {"A": modele_a[g], "B": b, "C": 0.0}
                )
            if g == "binance":
                rek["interestRate"] = interest.get(w["symbol"], np.nan)
            wiersze.append(rek)
    return pd.DataFrame(wiersze)


def tabela_spisu(spis: dict, tf: pd.DataFrame, rdzen: dict, teraz: pd.Timestamp) -> pd.DataFrame:
    wiersze = []
    for g in ("bybit", "binance"):
        interwal = tf[tf["gielda"] == g].set_index("symbol")["interwal_mod_h"]
        for _, w in spis[g].iterrows():
            wiersze.append(
                {
                    "gielda": g,
                    "symbol": w["symbol"],
                    "klasa": w["klasa"],
                    "region": w["region"],
                    "klasa_zrodlo": w["klasa_zrodlo"],
                    "start": w["start"],
                    "dni_historii": (teraz - w["start"]) / pd.Timedelta(days=1),
                    "interwal_h_spis": w["interwal_h"],
                    "interwal_h_dane": interwal.get(w["symbol"], np.nan),
                    "cap": w["cap"],
                    "floor": w["floor"],
                    "max_dzwignia": w["max_dzwignia"],
                    "w_rdzeniu": w["symbol"] in rdzen.get(g, []),
                }
            )
    return pd.DataFrame(wiersze)


def druk_p1(ts: pd.DataFrame) -> None:
    rows = []
    for (g, k), d in ts.groupby(["gielda", "klasa"]):
        naj = d.loc[d["dni_historii"].idxmax()]
        rows.append(
            {
                "gielda": g,
                "klasa": k,
                "n": len(d),
                "regiony": _licz(d["region"].replace("", "—")),
                "start_min": d["start"].min().date(),
                "start_max": d["start"].max().date(),
                "dni_med": round(d["dni_historii"].median(), 1),
                "dni_max": round(d["dni_historii"].max(), 1),
                "najdluzszy": naj["symbol"],
                "interwal_spis_h": _licz(d["interwal_h_spis"]),
                "interwal_dane_h": _licz(d["interwal_h_dane"]),
                "cap": _licz(d["cap"], 3),
                "max_dzwignia": _licz(d["max_dzwignia"], 3) or "brak w publicznym API",
            }
        )
    _druk("P1 — spis per klasa i giełda", _klasy_sort(pd.DataFrame(rows)))
    tradfi = ts[ts["klasa"] != "BTC_kontrola"]
    naj = tradfi.loc[tradfi.groupby("gielda")["dni_historii"].idxmax()]
    naj = naj.assign(miesiace=(naj["dni_historii"] / 30.44).round(2))
    _druk(
        "P1 — najdłuższa historia TradFi per giełda (dni, miesiące po 30,44 dnia)",
        naj[["gielda", "symbol", "klasa", "start", "dni_historii", "miesiace"]],
        nd=1,
    )


def druk_p2(tf: pd.DataFrame, interest: pd.DataFrame, spis: dict, rdzen: dict) -> None:
    kol = [
        "gielda",
        "symbol",
        "n",
        "n_eff",
        "interwal_mod_h",
        "odczyty_rok",
        "f_rok",
        "ci_low",
        "ci_high",
        "mediana_rok",
        "modalna_proc",
        "modalna_udzial",
    ]
    tf = tf.assign(modalna_proc=tf["modalna"] * 100)
    waluty = tf[tf["klasa"] == "waluty"]
    _druk(
        "P2 — waluty: funding roczny płacony przez długą (% rocznie), 95 % CI z N_eff; "
        "modalna_proc = stawka modalna w % na odczyt",
        waluty[kol].round(4),
    )
    _druk(
        "P2 — waluty: modele A (modalna BTCUSDT tej giełdy, rocznie), B (r_kwot − r_baz, FRED), "
        "C (0) i które mieszczą się w 95 % CI",
        waluty[
            [
                "gielda",
                "symbol",
                "ci_low",
                "ci_high",
                "model_A",
                "model_B",
                "model_B_serie",
                "model_C",
                "ci_zawiera",
            ]
        ].round(4),
    )
    _druk(
        "P2 — kontrola BTCUSDT (oczekiwana masa punktowa 0,01 % / 8 h = 10,95 % rocznie)",
        tf[tf["klasa"] == "BTC_kontrola"][kol + ["modalna_rok", "dziury"]].round(4),
    )
    w_rdzeniu = tf.apply(lambda w: w["symbol"] in rdzen.get(w["gielda"], []), axis=1)
    pozostale = tf[w_rdzeniu & ~tf["klasa"].isin(["waluty", "BTC_kontrola"])]
    _druk(
        "P2 — rdzeń poza walutami: f̂ (% rocznie) z 95 % CI obok r_USD (średnia DFF z okna instrumentu)",
        pozostale[["gielda", "symbol", "klasa"] + kol[2:] + ["dziury", "r_usd"]],
        nd=4,
    )
    rows = []
    for (g, k), d in tf[tf["n"] >= 2].groupby(["gielda", "klasa"]):
        modalne = d["modalna"].round(10)
        top = modalne.value_counts()
        rows.append(
            {
                "gielda": g,
                "klasa": k,
                "n_instr": len(d),
                "odczyty_med": d["n"].median(),
                "f_rok_med": d["f_rok"].median(),
                "f_rok_p25": d["f_rok"].quantile(0.25),
                "f_rok_p75": d["f_rok"].quantile(0.75),
                "modalna_najczestsza_proc": top.index[0] * 100,
                "instr_z_ta_modalna": int(top.iloc[0]),
                "udzial_modalnej_med": d["modalna_udzial"].median(),
                "ci_zawiera_0": int(((d["ci_low"] <= TOL_CI) & (d["ci_high"] >= -TOL_CI)).sum()),
                "r_usd_sr": d["r_usd"].mean(),
            }
        )
    _druk(
        "P2 — per klasa: mediana po instrumentach f̂ (% rocznie), najczęstsza stawka modalna, "
        "liczba instrumentów z CI obejmującym 0, średnia DFF w oknach (r_USD, % rocznie)",
        _klasy_sort(pd.DataFrame(rows)).round(4),
    )
    ir = interest.merge(spis["binance"][["symbol", "klasa"]], on="symbol", how="left")
    rows = [
        {
            "klasa": k,
            "n_symboli": len(d),
            "interestRate (wartość:liczba symboli)": _licz(d["interestRate"], 6),
        }
        for k, d in ir.groupby("klasa")
    ]
    _druk(
        "P2 — Binance interestRate z premiumIndex (migawki; wartość najczęstsza per symbol)",
        pd.DataFrame(rows),
    )


def tabela_wzoru(
    funding: pd.DataFrame, premia: pd.DataFrame, spis: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Druga droga P2 (Bybit): odczyty w oknie danych premii vs warianty wzoru."""
    odczyty, zbior = [], []
    s_idx = spis.set_index("symbol")
    for sym in ft.PREMIA_SYMBOLE:
        pm = premia[premia["symbol"] == sym]
        if pm.empty or sym not in s_idx.index:
            continue
        od = pm["czas"].min()
        f = funding[(funding["symbol"] == sym) & (funding["czas"] > od)]
        o = odtworz_funding(f, pm, cap=s_idx.loc[sym, "cap"], floor=s_idx.loc[sym, "floor"])
        o.insert(0, "symbol", sym)
        odczyty.append(o)
        for wariant in ("wzor_I", "wzor_0", "waz_I", "waz_0", "twap_I", "twap_0"):
            zbior.append({"symbol": sym, "wariant": wariant, **zgodnosc_wzoru(o, wariant)})
    return (pd.concat(odczyty, ignore_index=True) if odczyty else pd.DataFrame()), pd.DataFrame(
        zbior
    )


# ------------------------------------------------------------------ P3
def tabela_kosztow(
    mig: pd.DataFrame,
    spis: dict,
    rdzen: dict,
    taker_tradfi: dict = TAKER_TRADFI,
    taker_standard: dict = TAKER_STANDARD,
) -> pd.DataFrame:
    """P3 per instrument: mediany spreadu (wszystkie / sesja USA / poza), koszt strony przy oficjalnej
    stawce TradFi (BTCUSDT: standard) i przy stawce standardowej."""
    kal = Kalendarz("akcje_usa", mig["czas"].min(), mig["czas"].max())
    mig = mig.assign(spread_pb=spread_pb(mig["bid"], mig["ask"]), sesja=kal.otwarty(mig["czas"]))
    wiersze = []
    for (g, sym), d in mig.groupby(["gielda", "symbol"]):
        w = spis[g].set_index("symbol").loc[sym]
        med = d["spread_pb"].median()
        med_s = d.loc[d["sesja"], "spread_pb"].median()
        med_p = d.loc[~d["sesja"], "spread_pb"].median()
        rek = {
            "gielda": g,
            "symbol": sym,
            "klasa": w["klasa"],
            "region": w["region"],
            "w_rdzeniu": sym in rdzen.get(g, []),
            "n_migawek": len(d),
            "n_sesja": int(d["sesja"].sum()),
            "anomalie_kwotowan": int(d["spread_pb"].isna().sum()),
            "spread_pb_med": med,
            "spread_pb_sesja": med_s,
            "spread_pb_poza": med_p,
            "obrot24h_med_usdt": d["obrot24h"].median(),
        }
        taker = taker_standard[g] if w["klasa"] == "BTC_kontrola" else taker_tradfi[g]
        rek["taker_proc"] = taker * 100
        for suf, m in (("", med), ("_sesja", med_s), ("_poza", med_p)):
            rek[f"koszt_strony_proc{suf}"] = (m / 2 / 1e4 + taker) * 100
        rek["koszt_do_KO1"] = rek["koszt_strony_proc"] / (KO1_KOSZT * 100)
        rek["koszt_strony_standard_proc"] = (med / 2 / 1e4 + taker_standard[g]) * 100
        rek["koszt_standard_do_KO1"] = rek["koszt_strony_standard_proc"] / (KO1_KOSZT * 100)
        wiersze.append(rek)
    return pd.DataFrame(wiersze)


def druk_p3(tk: pd.DataFrame) -> None:
    agg = {
        "n_instr": ("symbol", "size"),
        "spread_pb_med": ("spread_pb_med", "median"),
        "spread_pb_sesja": ("spread_pb_sesja", "median"),
        "spread_pb_poza": ("spread_pb_poza", "median"),
        "koszt_strony_proc": ("koszt_strony_proc", "median"),
        "koszt_sesja": ("koszt_strony_proc_sesja", "median"),
        "koszt_poza": ("koszt_strony_proc_poza", "median"),
        "koszt_do_KO1": ("koszt_do_KO1", "median"),
        "koszt_standard": ("koszt_strony_standard_proc", "median"),
        "standard_do_KO1": ("koszt_standard_do_KO1", "median"),
        "obrot24h_med_mln": ("obrot24h_med_usdt", "median"),
        "anomalie": ("anomalie_kwotowan", "sum"),
    }
    per_klasa = tk.groupby(["gielda", "klasa"]).agg(**agg).reset_index()
    per_klasa["obrot24h_med_mln"] /= 1e6
    _druk(
        "P3 — per klasa: mediana po instrumentach (spread pełny w pb; koszt strony = spread/2 + taker "
        "TradFi: Bybit 0,0275 %, Binance 0,04 %; BTCUSDT i koszt_standard: 0,055 % / 0,05 %; "
        "% nominału; KO1 = 0,07 %)",
        _klasy_sort(per_klasa).round(4),
    )
    rd = tk[tk["w_rdzeniu"]]
    rdz = rd.groupby("gielda").agg(**agg).reset_index()
    rdz["obrot24h_med_mln"] /= 1e6
    _druk("P3 — rdzeń: mediana po instrumentach rdzenia", rdz.round(4))
    kol = [
        "gielda",
        "symbol",
        "klasa",
        "n_migawek",
        "n_sesja",
        "spread_pb_med",
        "spread_pb_sesja",
        "spread_pb_poza",
        "koszt_strony_proc",
        "koszt_do_KO1",
        "obrot24h_mln",
    ]
    rd = rd.assign(obrot24h_mln=rd["obrot24h_med_usdt"] / 1e6)
    _druk("P3 — instrumenty rdzenia (obrót 24 h w mln USDT)", rd[kol], nd=4)


# ------------------------------------------------------------------ P4
def tabela_zamkniec(swiece: dict, funding: dict, spis: dict, rdzen: dict, tf: pd.DataFrame):
    """Wiersz na instrument rdzenia (a–d) + zebrane wartości do agregacji per klasa."""
    wiersze, luki_all, bazis_all = [], [], []
    for g in ("bybit", "binance"):
        s_idx = spis[g].set_index("symbol")
        for sym in rdzen.get(g, []):
            klasa = s_idx.loc[sym, "klasa"]
            kal_nazwa = KALENDARZ_KLASY.get(klasa)
            ix = swiece[(g, "index")].query("symbol == @sym").set_index("czas").sort_index()
            ls = swiece[(g, "last")].query("symbol == @sym").set_index("czas").sort_index()
            if kal_nazwa is None or ix.empty or ls.empty:
                continue
            kal = Kalendarz(kal_nazwa, ix.index.min(), ix.index.max())
            stan = pd.Series(stan_godzin(kal, ix.index), index=ix.index)
            niezm = ix["high"] == ix["low"]
            rek = {
                "gielda": g,
                "symbol": sym,
                "klasa": klasa,
                "kalendarz": kal_nazwa,
                "godzin": len(ix),
            }
            for nazwa, v in (("otw", 1.0), ("zam", 0.0)):
                m = stan == v
                rek[f"n_godz_{nazwa}"] = int(m.sum())
                rek[f"niezm_{nazwa}"] = float(niezm[m].mean()) if m.any() else np.nan
            baz = (ls["close"] / ix["close"].reindex(ls.index) - 1).abs().dropna()
            st_b = stan.reindex(baz.index)
            for nazwa, v in (("otw", 1.0), ("zam", 0.0)):
                b = baz[st_b == v]
                rek[f"bazis_med_{nazwa}"] = float(b.median()) if len(b) else np.nan
                rek[f"bazis_p95_{nazwa}"] = float(b.quantile(0.95)) if len(b) else np.nan
                bazis_all.append(
                    pd.DataFrame(
                        {"gielda": g, "klasa": klasa, "stan": nazwa, "bazis": b.to_numpy()}
                    )
                )
            rek["p95_zam_do_otw"] = rek["bazis_p95_zam"] / rek["bazis_p95_otw"]
            lk = luki_zamkniec(kal.zamkniecia(), ls["close"], ix["close"])
            lk = lk.assign(gielda=g, symbol=sym, klasa=klasa)
            luki_all.append(lk)
            for typ in ("weekend", "noc"):
                d = lk[lk["typ"] == typ]
                r = mnk(d["R"], d["G"])
                rek |= {
                    f"{typ}_n": r["n"],
                    f"{typ}_beta": r["beta"],
                    f"{typ}_r2": r["r2"],
                    f"{typ}_alfa": r["alfa"],
                }
            rek |= stan_fundingu(kal, funding[g].query("symbol == @sym"), tf, g, sym)
            wiersze.append(rek)
    luki = pd.concat(luki_all, ignore_index=True) if luki_all else pd.DataFrame()
    bazis = pd.concat(bazis_all, ignore_index=True) if bazis_all else pd.DataFrame()
    return pd.DataFrame(wiersze), luki, bazis


def stan_fundingu(kal: Kalendarz, f: pd.DataFrame, tf: pd.DataFrame, g: str, sym: str) -> dict:
    """(d) średni funding roczny (·K instrumentu, % rocznie): wg stanu rynku w chwili T (``T_*``) i wg udziału
    otwarcia w przedziale naliczania ``[T − Δ, T)`` (``prz_*``)."""
    f = f.sort_values("czas")
    st = tf[(tf["gielda"] == g) & (tf["symbol"] == sym)].iloc[0]
    if len(f) < 2 or not math.isfinite(st["odczyty_rok"]):
        return {}
    t_ns = _ns(f["czas"])
    delta = np.diff(t_ns, prepend=t_ns[0] - int(st["interwal_mod_h"] * H_NS))
    u = kal.udzial(
        pd.to_datetime(t_ns - delta, unit="ns", utc=True), pd.to_datetime(t_ns, unit="ns", utc=True)
    )
    x = f["fundingRate"].to_numpy(dtype=float)
    otw_t = kal.otwarty(pd.to_datetime(t_ns, unit="ns", utc=True))
    out = {}
    for nazwa, m in (
        ("T_otw", otw_t),
        ("T_zam", ~otw_t),
        ("prz_otw", u >= 1 - 1e-12),
        ("prz_czesc", (u > 1e-12) & (u < 1 - 1e-12)),
        ("prz_zam", u <= 1e-12),
    ):
        out[f"f_{nazwa}_n"] = int(m.sum())
        out[f"f_{nazwa}_rok"] = float(x[m].mean() * st["odczyty_rok"] * 100) if m.any() else np.nan
    return out


def druk_p4(tz: pd.DataFrame, luki: pd.DataFrame, bazis: pd.DataFrame) -> None:
    kol_a = ["gielda", "symbol", "klasa", "n_godz_otw", "n_godz_zam", "niezm_otw", "niezm_zam"]
    kol_b = [
        "gielda",
        "symbol",
        "bazis_med_otw",
        "bazis_p95_otw",
        "bazis_med_zam",
        "bazis_p95_zam",
        "p95_zam_do_otw",
    ]
    kol_c = [
        "gielda",
        "symbol",
        "weekend_n",
        "weekend_beta",
        "weekend_r2",
        "noc_n",
        "noc_beta",
        "noc_r2",
    ]
    kol_d = ["gielda", "symbol"] + [
        f"f_{st}_{m}"
        for st in ("T_otw", "T_zam", "prz_otw", "prz_czesc", "prz_zam")
        for m in ("n", "rok")
    ]
    _druk(
        "P4 (a) — udział godzin z niezmienionym indeksem (high == low): otwarty vs zamknięty",
        tz[kol_a].round(4),
    )
    _druk(
        "P4 (b) — |cena ostatnia / indeks − 1| (ułamek): mediana i p95, otwarty vs zamknięty",
        tz[kol_b].round(6),
    )
    _druk(
        "P4 (c) — luka: MNK G = α + β·R per instrument (weekendy; noce dni roboczych dla akcji/ETF)",
        tz[kol_c].round(4),
    )
    _druk(
        "P4 (d) — funding roczny (% rocznie): T_* = stan rynku w chwili rozliczenia (d1); "
        "prz_* = przedział naliczania w całości otwarty / częściowo / w całości zamknięty (d2)",
        tz[kol_d].round(4),
    )
    rows = []
    for (g, k), d in tz.groupby(["gielda", "klasa"]):
        rek = {"gielda": g, "klasa": k, "n_instr": len(d)}
        for nazwa in ("otw", "zam"):
            n = d[f"n_godz_{nazwa}"]
            rek[f"niezm_{nazwa}"] = (
                float((d[f"niezm_{nazwa}"] * n).sum() / n.sum()) if n.sum() else np.nan
            )
            b = bazis[(bazis["gielda"] == g) & (bazis["klasa"] == k) & (bazis["stan"] == nazwa)][
                "bazis"
            ]
            rek[f"bazis_med_{nazwa}"] = b.median()
            rek[f"bazis_p95_{nazwa}"] = b.quantile(0.95)
        rek["p95_zam_do_otw"] = rek["bazis_p95_zam"] / rek["bazis_p95_otw"]
        lk = luki[(luki["gielda"] == g) & (luki["klasa"] == k)] if len(luki) else luki
        for typ in ("weekend", "noc"):
            x = lk[lk["typ"] == typ] if len(lk) else lk
            r = mnk(x["R"], x["G"]) if len(x) else mnk([], [])
            rek |= {
                f"{typ}_n": r["n"],
                f"{typ}_zamkniec": x["c"].nunique() if len(x) else 0,
                f"{typ}_beta": r["beta"],
                f"{typ}_r2": r["r2"],
            }
        for nazwa in ("T_otw", "T_zam", "prz_otw", "prz_czesc", "prz_zam"):
            rek[f"f_{nazwa}_rok_med"] = (
                d[f"f_{nazwa}_rok"].median() if f"f_{nazwa}_rok" in d else np.nan
            )
        rows.append(rek)
    _druk(
        "P4 — per klasa (rdzeń): (a) udział niezmienionych godzin, (b) |bazis| łącznie po instrumentach, "
        "(c) MNK łącznie (n = instrument×zamknięcie; *_zamkniec = różne zamknięcia), (d) mediany po instrumentach",
        _klasy_sort(pd.DataFrame(rows)).round(6),
    )


# ------------------------------------------------------------------ P5
def tabela_zgodnosci(swiece: dict, fred: dict, rdzen: dict) -> pd.DataFrame:
    wiersze = []
    for g in ("bybit", "binance"):
        for sym, (seria, poziom) in ZGODNOSC.items():
            if sym not in rdzen.get(g, []) or seria not in fred:
                continue
            ix = (
                swiece[(g, "index")].query("symbol == @sym").set_index("czas")["close"].sort_index()
            )
            warianty = [("pre-rejestracja 16:00 UTC (zimą 17:00)", 16)]
            if not poziom:
                warianty.append(("dodatkowy: zamknięcie NYSE 20:00 UTC (zimą 21:00)", 20))
            for opis, godz in warianty:
                r = zgodnosc_z_fred(ix, fred[seria], poziom, godz)
                ost = fred[seria].dropna(subset=["value"])["date"].max()
                wiersze.append(
                    {
                        "gielda": g,
                        "symbol": sym,
                        "seria_FRED": seria,
                        "wariant": opis,
                        **r,
                        "fred_ostatnia": ost.date(),
                    }
                )
    return pd.DataFrame(wiersze)


# ------------------------------------------------------------------ main
def main(dane: Path = DANE, runda: Path = RUNDA) -> int:
    spis = {g: pd.read_parquet(dane / f"spis_{g}.parquet") for g in ("bybit", "binance")}
    funding = {g: pd.read_parquet(dane / f"funding_{g}.parquet") for g in ("bybit", "binance")}
    swiece = {
        (g, r): pd.read_parquet(dane / f"swiece_{g}_{r}_1h.parquet")
        for g in ("bybit", "binance")
        for r in ft.RODZAJE
    }
    premia = pd.read_parquet(dane / "premia_bybit_1m.parquet")
    rdzen = json.loads((dane / "rdzen.json").read_text(encoding="utf-8"))
    symbole = {g: set(spis[g]["symbol"]) for g in spis}
    mig = wczytaj_migawki(dane / "migawki", symbole)
    serie = sorted(
        {s for pary in STOPY.values() for s in pary if s} | {s for s, _ in ZGODNOSC.values()}
    )
    fred = wczytaj_fred(serie)
    teraz = max(funding[g]["czas"].max() for g in funding)

    print("PT1 — perpetuale TradFi (Bybit, Binance): neutralny raport liczb P1–P5")
    print(
        f"teraz (najpóźniejszy odczyt fundingu) = {teraz}; migawki: {mig['czas'].nunique()} "
        f"({mig['czas'].min()} … {mig['czas'].max()}); rdzeń z migawki {rdzen['migawka']}"
    )
    print("rdzeń Bybit:", ", ".join(rdzen["bybit"]))
    print("rdzeń Binance:", ", ".join(rdzen["binance"]))
    print(
        "obrót 24 h akcji w pierwszej migawce (mln USDT): "
        + "; ".join(
            f"{g}: "
            + ", ".join(f"{s} {v / 1e6:.1f}" for s, v in rdzen[f"{g}_akcje_obrot24h"].items())
            for g in ("bybit", "binance")
        )
    )
    print(
        "FRED (ostatnia obserwacja): "
        + ", ".join(
            f"{s} {fred[s].dropna(subset=['value'])['date'].max().date()}"
            for s in serie
            if s in fred
        )
        + (
            "; brak: " + ", ".join(s for s in serie if s not in fred)
            if any(s not in fred for s in serie)
            else ""
        )
    )

    interest = (
        mig[mig["gielda"] == "binance"]
        .groupby("symbol")["interestRate"]
        .agg(lambda s: s.dropna().round(10).mode().min() if s.notna().any() else np.nan)
    )
    tf = tabela_funding(spis, funding, fred, interest)
    ts = tabela_spisu(spis, tf, rdzen, teraz)
    druk_p1(ts)
    druk_p2(tf, interest.rename("interestRate").reset_index(), spis, rdzen)
    odczyty_wzoru, wzor = tabela_wzoru(funding["bybit"], premia, spis["bybit"])
    _druk(
        "P2 druga droga (Bybit): F̂ ze wzoru vs odczyt; zgodne_* = udział |F̂ − F| ≤ 0,5 pb (0,00005) "
        "i ≤ 0,05 pb; błędy w pb (1 pb = 0,0001)",
        wzor.assign(
            sredni_blad_pb=wzor["sredni_blad"] * 1e4,
            mediana_abs_bledu_pb=wzor["mediana_abs_bledu"] * 1e4,
        )
        .drop(columns=["sredni_blad", "mediana_abs_bledu"])
        .round(4),
    )
    if len(odczyty_wzoru):
        pokr = (
            odczyty_wzoru.groupby("symbol")
            .agg(
                odczytow=("F", "size"),
                pokrycie_min=("pokrycie", "min"),
                p_sr_med_pb=("p_sr", lambda s: s.median() * 1e4),
                F_med_pb=("F", lambda s: s.median() * 1e4),
                okres_od=("czas", "min"),
                okres_do=("czas", "max"),
            )
            .reset_index()
        )
        _druk("P2 druga droga — pokrycie minut indeksu premii i mediany P̄, F (pb)", pokr, nd=4)
    tk = tabela_kosztow(mig, spis, rdzen)
    druk_p3(tk)
    tz, luki, bazis = tabela_zamkniec(swiece, funding, spis, rdzen, tf)
    druk_p4(tz, luki, bazis)
    tg = tabela_zgodnosci(swiece, fred, rdzen)
    _druk(
        "P5 — zgodność indeksu giełdy z FRED (korelacja dziennych zwrotów log, mediana |poziom/FRED − 1|)",
        tg.round(5),
    )

    runda.mkdir(parents=True, exist_ok=True)
    ts.to_csv(runda / "spis.csv", index=False)
    tf.to_csv(runda / "funding.csv", index=False)
    wzor.to_csv(runda / "funding_wzor.csv", index=False)
    tk.to_csv(runda / "koszty.csv", index=False)
    tz.to_csv(runda / "zamkniety_rynek.csv", index=False)
    tg.to_csv(runda / "zgodnosc.csv", index=False)
    print(f"\nCSV: {runda}/{{spis,funding,funding_wzor,koszty,zamkniety_rynek,zgodnosc}}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
