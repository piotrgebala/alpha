"""
journal_carry.py — poprawka 12 dziennika (decyzja użytkownika 2026-09-28: „dodajemy do dziennika
strategię carry do weryfikacji”): noga carry COIN-M, osobno i TYLKO do zapisu (`dziennik/carry_wyniki.csv`).

Konstrukcja z rundy D1 (`runs/2026-09-23_d1-produkt-carry/`, wniosek 61), bez zmian i bez parametrów
do strojenia: 1 BTC zabezpieczenia (kupione na spot przy starcie) + short `BTCUSD_PERP` (inverse,
COIN-M) o nominale równym wartości zabezpieczenia, dźwignia 1×, zawsze w pozycji (bez przełączania
po znaku fundingu — C1b, wniosek 55). Wartość USD pozycji jest stała
(`carry_product.inverse_position_usd_value`), więc wynik = funding COIN-M.

Księgowanie DOKŁADNIE jak wiersz COIN-M w D1 (`backtest/run_carry_product_d1.py`, Q2): znaczniki
→ `floor_to_grid`, duplikaty po zaokrągleniu odrzucone, `inverse_carry_pnl(f, switch_cost)` z kosztem
`CarryCosts(spot_fee_rate, taker_fee_rate, slippage_bps / 10 000).switch_cost` z `config/settings.yaml`.
Jedno odstępstwo, konieczne: D1 zamyka pozycję w ostatnim okresie próby i tam dolicza koszt wyjścia;
noga dziennika jest otwarta, więc koszt wyjścia nie wchodzi do wierszy (ostatni wiersz zmieniałby
się co dzień, a plik jest append-only). Wynik D1 za okres od startu do dnia d = `netto_skum(d) − switch_cost`.

Dzień UTC d = rozliczenia o 00:00, 08:00 i 16:00 dnia d (jak `xs_momentum.daily_funding_panel`
w silniku dziennika: pozycja wchodzi na zamknięciu dnia d−1, czyli o 00:00 UTC dnia d, a koszt
wejścia obciąża pierwszy dzień). Dzień trafia do pliku dopiero, gdy jest ZAMKNIĘTY w danych: plik
ma rozliczenie z dnia następnego albo późniejsze. Wtedy liczba rozliczeń ≠ 3 to prawdziwy brak
po stronie danych, a nie „jeszcze nie pobrane”. Dzień bez żadnego rozliczenia też dostaje wiersz.

Testy: `tests/test_journal_carry.py`.
"""

from __future__ import annotations

import pandas as pd

from backtest.carry_hedged import CarryCosts
from backtest.carry_product import PERIODS_PER_DAY, floor_to_grid, inverse_carry_pnl

CARRY_SYMBOL = "BTCUSD_PERP"
CARRY_START = pd.Timestamp("2026-09-29", tz="UTC")  # pierwszy dzień wyniku carry (poprawka 12)
CARRY_FILE = (
    f"binance_cm_funding_{CARRY_SYMBOL}.parquet"  # nazwa z `fetch_external.fetch_coinm_funding`
)
CARRY_CSV = "carry_wyniki.csv"
CARRY_KEY = ["date"]
CARRY_VALUES = ["rozliczenia", "komplet", "suma_stawek", "koszt", "netto", "netto_skum"]
CARRY_COLS = [*CARRY_KEY, *CARRY_VALUES]


def carry_costs(cost_cfg: dict) -> CarryCosts:
    """Koszt wejścia jak w D1: opłata spot + opłata perp (taker) + poślizg na każdej nodze."""
    return CarryCosts(
        spot_fee=cost_cfg["spot_fee_rate"],
        perp_fee=cost_cfg["taker_fee_rate"],
        slippage=cost_cfg["slippage_bps"] / 10_000.0,
    )


def _require_columns(funding: pd.DataFrame) -> None:
    if "timestamp" not in funding.columns or "funding_rate" not in funding.columns:
        raise ValueError("funding COIN-M: wymagane kolumny timestamp i funding_rate")


def settlements(funding: pd.DataFrame, start: pd.Timestamp) -> pd.DataFrame:
    """Rozliczenia przygotowane jak w D1 (Q2): siatka 8 h, bez duplikatów, rosnąco, od `start`."""
    _require_columns(funding)
    f = funding[["timestamp", "funding_rate"]].copy()
    f["timestamp"] = floor_to_grid(f["timestamp"])
    f = f.drop_duplicates("timestamp").sort_values("timestamp")
    return f[f["timestamp"] >= start].reset_index(drop=True)


def published_per_day(funding: pd.DataFrame, start: pd.Timestamp) -> pd.Series:
    """
    Liczba rozliczeń opublikowanych przez giełdę per dzień UTC od `start` — różne znaczniki PRZED
    zaokrągleniem do siatki 8 h. Gdyby giełda zmieniła rytm (np. co 4 h), przygotowanie z D1 po cichu
    połączyłoby rekordy; ta liczba to pokaże (rozliczenia ≠ 3 → `komplet` = False).
    """
    _require_columns(funding)
    ts = pd.Series(pd.to_datetime(funding["timestamp"], utc=True)).drop_duplicates()
    grid = floor_to_grid(ts)
    return grid[grid >= start].dt.floor("D").value_counts().sort_index()


def settlement_pnl(funding: pd.DataFrame, start: pd.Timestamp, switch_cost: float) -> pd.DataFrame:
    """
    P&L per rozliczenie od `start` (ułamek nominału USD) = `inverse_carry_pnl` z D1 z tym samym kosztem,
    ale BEZ kosztu wyjścia: noga jest otwarta, więc zostaje tylko koszt wejścia w pierwszym rozliczeniu.
    """
    p = inverse_carry_pnl(settlements(funding, start), switch_cost)
    if len(p):
        p.loc[
            len(p) - 1, "cost"
        ] -= switch_cost  # D1 zamyka pozycję w ostatnim okresie — dziennik nie
        p["pnl"] = p["funding_received"] - p["cost"]
    return p


def carry_rows(funding: pd.DataFrame, start: pd.Timestamp, switch_cost: float) -> pd.DataFrame:
    """
    Wiersze `carry_wyniki.csv`: jeden na każdy dzień UTC od `start` do ostatniego dnia ZAMKNIĘTEGO
    w danych (dzień przed dniem najpóźniejszego rozliczenia). Kolumny: `rozliczenia` (opublikowane tego
    dnia, oczekiwane 3), `komplet` (3 opublikowane i wszystkie trzy w wyniku), `suma_stawek` (funding
    otrzymany przez short, ułamek nominału; ujemna = zapłacony), `koszt` (koszt wejścia — tylko pierwszy
    dzień; dodatni, jak w D1), `netto` = `suma_stawek` − `koszt`, `netto_skum` (suma od startu, bez
    procentu składanego — jak w D1).
    """
    p = settlement_pnl(funding, start, switch_cost)
    if p.empty:
        return pd.DataFrame(columns=CARRY_COLS)
    day = pd.to_datetime(p["timestamp"], utc=True).dt.floor("D")
    last_day = day.max() - pd.Timedelta(days=1)
    first_day = start.normalize()
    if last_day < first_day:
        return pd.DataFrame(columns=CARRY_COLS)
    days = pd.date_range(first_day, last_day, freq="D")
    agg = p.groupby(day).agg(
        uzyte=("pnl", "size"),
        suma_stawek=("funding_received", "sum"),
        koszt=("cost", "sum"),
        netto=("pnl", "sum"),
    )
    agg = agg.reindex(days)
    published = published_per_day(funding, start).reindex(days, fill_value=0).astype(int)
    used = agg["uzyte"].fillna(0).astype(int)
    netto = agg["netto"].fillna(0.0)
    return pd.DataFrame(
        {
            "date": days.strftime("%Y-%m-%d"),
            "rozliczenia": published.to_numpy(),
            "komplet": ((published == PERIODS_PER_DAY) & (used == PERIODS_PER_DAY)).to_numpy(),
            "suma_stawek": agg["suma_stawek"].fillna(0.0).to_numpy(),
            "koszt": agg["koszt"].fillna(0.0).to_numpy(),
            "netto": netto.to_numpy(),
            "netto_skum": netto.cumsum().to_numpy(),
        },
        columns=CARRY_COLS,
    )
