"""Testy backtest/run_pt1_tradfi.py (runda PT1) — kalendarze, annualizacja, „CI zawiera”, luka, wzór fundingu."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest import run_pt1_tradfi as pt

UTC = "UTC"


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz=UTC)


def otwarty(kal: pt.Kalendarz, s: str) -> bool:
    return bool(kal.otwarty([ts(s)])[0])


# ------------------------------------------------------------------ czas letni i kalendarze
@pytest.mark.parametrize(
    ("chwila", "lato"),
    [
        ("2025-03-09 06:59", False),
        ("2025-03-09 07:00", True),
        ("2025-11-02 05:59", True),
        ("2025-11-02 06:00", False),
        ("2026-03-08 06:59", False),
        ("2026-03-08 07:00", True),
        ("2026-11-01 05:59", True),
        ("2026-11-01 06:00", False),
    ],
)
def test_us_dst_boundaries(chwila, lato):
    assert pt.czas_letni_usa(ts(chwila)) is lato


def test_us_equities_calendar_summer_winter_weekend_holiday():
    kal = pt.Kalendarz("akcje_usa", ts("2025-12-01"), ts("2026-10-31"))
    # lato (pn 2026-09-28): 13:30–20:00 UTC
    assert not otwarty(kal, "2026-09-28 13:29") and otwarty(kal, "2026-09-28 13:30")
    assert otwarty(kal, "2026-09-28 19:59") and not otwarty(kal, "2026-09-28 20:00")
    # zima (pn 2026-01-05): 14:30–21:00 UTC
    assert not otwarty(kal, "2026-01-05 14:29") and otwarty(kal, "2026-01-05 14:30")
    assert otwarty(kal, "2026-01-05 20:59") and not otwarty(kal, "2026-01-05 21:00")
    # piątek przed zmianą czasu (2026-03-06, zima) i poniedziałek po (2026-03-09, lato)
    assert otwarty(kal, "2026-03-06 20:30") and not otwarty(kal, "2026-03-06 21:00")
    assert otwarty(kal, "2026-03-09 13:30") and not otwarty(kal, "2026-03-09 20:00")
    # sobota, niedziela, święta NYSE
    for chwila in (
        "2026-09-26 15:00",
        "2026-09-27 15:00",
        "2026-09-07 15:00",
        "2026-04-03 15:00",
        "2025-12-25 16:00",
    ):
        assert not otwarty(kal, chwila), chwila


def test_fx_calendar_friday_close_sunday_open_with_dst_switch():
    kal = pt.Kalendarz("waluty", ts("2025-12-01"), ts("2026-10-31"))
    assert otwarty(kal, "2026-09-25 20:59") and not otwarty(kal, "2026-09-25 21:00")  # pt lato
    assert not otwarty(kal, "2026-09-27 20:59") and otwarty(kal, "2026-09-27 21:00")  # nd lato
    assert otwarty(kal, "2026-01-09 21:59") and not otwarty(kal, "2026-01-09 22:00")  # pt zima
    assert not otwarty(kal, "2026-01-11 21:59") and otwarty(kal, "2026-01-11 22:00")  # nd zima
    assert not otwarty(kal, "2026-03-06 22:00")  # pt 2026-03-06: jeszcze zima → zamknięcie 22:00
    assert otwarty(kal, "2026-03-06 21:59")
    assert otwarty(kal, "2026-03-08 21:00")  # nd 2026-03-08: czas letni od 07:00 → otwarcie 21:00
    assert otwarty(kal, "2026-09-30 03:00")  # środek tygodnia: całą dobę


def test_commodity_calendar_daily_break_and_weekend():
    kal = pt.Kalendarz("surowce", ts("2025-12-01"), ts("2026-10-31"))
    # lato: przerwa pn–czw 21:00–22:00, weekend pt 21:00 → nd 22:00
    assert otwarty(kal, "2026-09-29 20:59") and not otwarty(kal, "2026-09-29 21:00")
    assert not otwarty(kal, "2026-09-29 21:59") and otwarty(kal, "2026-09-29 22:00")
    assert not otwarty(kal, "2026-09-25 21:00") and not otwarty(kal, "2026-09-27 21:59")
    assert otwarty(kal, "2026-09-27 22:00")
    # zima: +1 h
    assert otwarty(kal, "2026-01-06 21:30") and not otwarty(kal, "2026-01-06 22:00")
    assert otwarty(kal, "2026-01-06 23:00") and not otwarty(kal, "2026-01-11 22:30")
    assert otwarty(kal, "2026-01-11 23:00")


def test_closure_types_night_weekend_holiday():
    kal = pt.Kalendarz("akcje_usa", ts("2026-08-31"), ts("2026-09-15"))
    zam = {(c, o): typ for c, o, typ in kal.zamkniecia()}
    assert zam[(ts("2026-09-04 20:00"), ts("2026-09-08 13:30"))] == "weekend"  # pn 09-07 święto
    assert zam[(ts("2026-09-08 20:00"), ts("2026-09-09 13:30"))] == "noc"
    assert zam[(ts("2026-09-11 20:00"), ts("2026-09-14 13:30"))] == "weekend"
    typy = {
        typ
        for _, _, typ in pt.Kalendarz("surowce", ts("2026-09-01"), ts("2026-09-20")).zamkniecia()
    }
    assert typy == {"przerwa", "weekend"}


def test_hour_states_and_accrual_share():
    kal = pt.Kalendarz("akcje_usa", ts("2026-09-01"), ts("2026-09-30"))
    stany = pt.stan_godzin(
        kal, [ts("2026-09-28 13:00"), ts("2026-09-28 14:00"), ts("2026-09-28 20:00")]
    )
    assert math.isnan(stany[0]) and stany[1] == 1.0 and stany[2] == 0.0
    # odczyt 16:00 z interwałem 8 h: [08:00, 16:00) otwarte 13:30–16:00 = 2,5 h / 8 h
    u = kal.udzial([ts("2026-09-28 08:00")], [ts("2026-09-28 16:00")])
    assert u[0] == pytest.approx(2.5 / 8)
    assert kal.udzial([ts("2026-09-26 00:00")], [ts("2026-09-26 08:00")])[0] == 0.0  # sobota


# ------------------------------------------------------------------ annualizacja fundingu
def _odczyty(start: str, n: int, interwal_h: float) -> pd.DatetimeIndex:
    return pd.date_range(ts(start), periods=n, freq=pd.Timedelta(hours=interwal_h))


@pytest.mark.parametrize(("interwal_h", "stawka"), [(8, 0.0001), (4, 0.00005)])
def test_annualization_uses_observed_interval(interwal_h, stawka):
    st_ = pt.statystyki_fundingu(_odczyty("2026-01-01", 300, interwal_h), [stawka] * 300)
    assert st_["interwal_mod_h"] == interwal_h and st_["odczyty_rok"] == pytest.approx(
        8760 / interwal_h
    )
    assert st_["f_rok"] == pytest.approx(10.95)  # 0,01 %/8 h = 0,005 %/4 h = 10,95 % rocznie
    assert (st_["ci_low"], st_["ci_high"]) == (pytest.approx(10.95), pytest.approx(10.95))
    assert st_["modalna"] == stawka and st_["modalna_udzial"] == 1.0
    assert st_["modalna_rok"] == pytest.approx(10.95) and st_["dziury"] == 0


def test_annualization_with_interval_change_and_gap_equals_sum_over_window():
    t = _odczyty("2026-01-01", 100, 8).append(_odczyty("2026-02-03 08:00", 150, 4))
    t = t.delete(50)  # brakujący odczyt → jedna dziura
    rng = np.random.default_rng(1)
    x = rng.normal(0.0001, 0.0001, len(t))
    st_ = pt.statystyki_fundingu(t, x)
    n = len(t)
    delta_sr = (t[-1] - t[0]) / pd.Timedelta(hours=1) / (n - 1)
    assert st_["f_rok"] == pytest.approx(x.sum() / (n * delta_sr / 8760) * 100)
    assert st_["dziury"] == 1 and st_["interwal_mod_h"] == 4.0  # zmiana 8 h → 4 h to nie dziura
    assert 1.0 <= st_["n_eff"] <= n


def test_mode_is_deterministic_and_share_counts_mass_point():
    t = _odczyty("2026-01-01", 10, 8)
    st_ = pt.statystyki_fundingu(t, [0.0001] * 4 + [0.0] * 4 + [0.0002, -0.0001])
    assert st_["modalna"] == 0.0 and st_["modalna_udzial"] == 0.4  # remis → mniejsza wartość


def test_single_reading_gives_nan_statistics():
    st_ = pt.statystyki_fundingu([ts("2026-01-01")], [0.0001])
    assert st_["n"] == 1 and math.isnan(st_["f_rok"])


# ------------------------------------------------------------------ reguła „CI zawiera”
@pytest.mark.parametrize(
    ("lo", "hi", "oczek"),
    [
        (10.95, 12.0, "A"),  # wartość dokładnie na dolnej granicy — w środku
        (-1.0, 10.95, "A,B,C"),  # dokładnie na górnej
        (0.0, 0.0, "C"),  # CI zdegenerowane (stały funding 0)
        (0.5, 1.0, "żaden"),
        (-5.0, 5.0, "B,C"),
        (float("nan"), 1.0, "brak danych"),
    ],
)
def test_ci_contains_edge_cases(lo, hi, oczek):
    assert pt.ci_zawiera(lo, hi, {"A": 10.95, "B": 1.38, "C": 0.0}) == oczek


def test_ci_contains_skips_nan_model_and_tolerates_float_noise():
    assert pt.ci_zawiera(0.0, 1.0, {"A": float("nan"), "C": 0.0}) == "C"
    assert pt.ci_zawiera(1e-12, 1.0, {"C": 0.0}) == "C"


# ------------------------------------------------------------------ stopy (model B)
def _seria(pary):
    return pd.DataFrame(
        {"date": pd.to_datetime([d for d, _ in pary], utc=True), "value": [v for _, v in pary]}
    )


def test_rate_mean_is_as_of_daily_and_fallback_on_stale_series():
    miesieczna = _seria([("2026-07-01", 1.0), ("2026-08-01", 2.0)])
    # okno 2026-08-30 … 2026-09-02: 2 dni sierpnia i 2 dni września — wszystkie as-of 2,0
    assert pt.stopa_srednia(miesieczna, ts("2026-08-30"), ts("2026-09-02")) == 2.0
    assert pt.stopa_srednia(miesieczna, ts("2026-07-30"), ts("2026-08-02")) == pytest.approx(1.5)
    stara = _seria([("2026-01-01", 5.0)])
    fred = {"ECBDFR": stara, "IR3TIB01EZM156N": _seria([("2026-09-01", 2.0)])}
    assert pt.wybierz_stope("EUR", fred, ts("2026-09-28"))[0] == "IR3TIB01EZM156N"
    fred["ECBDFR"] = _seria([("2026-09-20", 2.5)])
    assert pt.wybierz_stope("EUR", fred, ts("2026-09-28"))[0] == "ECBDFR"


def test_model_b_signs_follow_preregistration():
    fred = {
        "DFF": _seria([("2026-01-01", 4.0)]),
        "ECBDFR": _seria([("2026-01-01", 2.0)]),
        "IRSTCI01JPM156N": _seria([("2026-01-01", 0.5)]),
    }
    od, do = ts("2026-01-10"), ts("2026-01-20")
    assert pt.model_b("EURUSD", fred, od, do)[0] == pytest.approx(2.0)  # r_USD − r_EUR
    assert pt.model_b("USDJPY", fred, od, do)[0] == pytest.approx(-3.5)  # r_JPY − r_USD


# ------------------------------------------------------------------ luka po zamknięciu (P4 c)
def _godziny(od: str, do: str) -> pd.DatetimeIndex:
    return pd.date_range(ts(od), ts(do), freq="h")


def test_gap_uses_preregistered_bars_for_us_equities_summer():
    idx = _godziny("2026-09-18", "2026-09-23")
    last = pd.Series(100.0, index=idx)
    index = pd.Series(100.0, index=idx)
    last[ts("2026-09-18 19:00")], last[ts("2026-09-21 12:00")] = 100.0, 110.0  # pt 19:00 → pn 12:00
    index[ts("2026-09-18 19:00")], index[ts("2026-09-21 13:00")] = (
        100.0,
        105.0,
    )  # pt 19:00 → pn 13:00
    kal = pt.Kalendarz("akcje_usa", idx[0], idx[-1])
    lk = pt.luki_zamkniec(kal.zamkniecia(), last, index, typy=("weekend",))
    w = lk.loc[lk["c"] == ts("2026-09-18 20:00")].iloc[0]
    assert w["R"] == pytest.approx(math.log(1.1)) and w["G"] == pytest.approx(math.log(1.05))


def test_gap_regression_recovers_beta_one_when_index_gaps_to_perp():
    idx = _godziny("2026-06-01", "2026-09-30")
    rng = np.random.default_rng(7)
    last = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.003, len(idx)))), index=idx)
    index = last * np.exp(rng.normal(0, 0.001, len(idx)))
    kal = pt.Kalendarz("akcje_usa", idx[0], idx[-1])
    for c, o, _typ in kal.zamkniecia():  # indeks „dogania” perpa: G = R z konstrukcji
        b_c, b_g = c - pt.H, o.floor("h")
        if b_c in index.index and b_g in index.index:
            index[b_c] = last[b_c]
            index[b_g] = last[b_g - pt.H]
    lk = pt.luki_zamkniec(kal.zamkniecia(), last, index)
    for typ in ("weekend", "noc"):
        d = lk[lk["typ"] == typ]
        r = pt.mnk(d["R"], d["G"])
        assert r["n"] >= 15 and r["beta"] == pytest.approx(1.0) and r["r2"] == pytest.approx(1.0)
        assert r["alfa"] == pytest.approx(0.0, abs=1e-12)


def test_gap_skips_closure_with_missing_bar():
    idx = _godziny("2026-09-18", "2026-09-23").drop(ts("2026-09-21 12:00"))  # brak świecy R
    s = pd.Series(1.0, index=idx)
    kal = pt.Kalendarz("akcje_usa", idx[0], idx[-1])
    lk = pt.luki_zamkniec(kal.zamkniecia(), s, s, typy=("weekend",))
    assert ts("2026-09-18 20:00") not in set(lk["c"])


def test_ols_degenerate_inputs():
    assert math.isnan(pt.mnk([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])["beta"])
    assert math.isnan(pt.mnk([0.1, 0.2], [0.1, 0.2])["beta"])


# ------------------------------------------------------------------ wzór fundingu (druga droga P2)
_p = st.floats(-0.01, 0.01, allow_nan=False)
_interwal = st.sampled_from([1.0, 2.0, 4.0, 8.0])
_i8 = st.floats(0.0, 0.001, allow_nan=False)


@settings(max_examples=300, deadline=None)
@given(_p, _interwal, _i8)
def test_funding_formula_clamp_properties(p, interwal_h, i8):
    f = float(pt.funding_ze_wzoru(p, interwal_h, i8))
    i = i8 * interwal_h / 8
    assert abs(f - p) <= pt.ZACISK + 1e-15  # F nigdy dalej od premii niż zacisk
    assert abs(f - i) == pytest.approx(max(0.0, abs(p - i) - pt.ZACISK), abs=1e-15)
    if abs(p - i) <= pt.ZACISK:  # mała premia → F = I (masa punktowa na stałej stopie)
        assert f == pytest.approx(i, abs=1e-15)


@settings(max_examples=200, deadline=None)
@given(_p, _p, _interwal)
def test_funding_formula_monotone_in_premium_and_capped(p1, p2, interwal_h):
    lo, hi = sorted((p1, p2))
    assert pt.funding_ze_wzoru(lo, interwal_h) <= pt.funding_ze_wzoru(hi, interwal_h) + 1e-15
    f = float(pt.funding_ze_wzoru(p1, interwal_h, cap=0.002, floor=-0.002))
    assert -0.002 <= f <= 0.002


def test_reconstruction_matches_formula_and_respects_coverage():
    minuty = pd.date_range(ts("2026-09-20"), ts("2026-09-22"), freq="min", inclusive="left")
    premia = pd.DataFrame({"czas": minuty, "close": 0.0002})
    odczyty = pd.date_range(ts("2026-09-20 08:00"), ts("2026-09-21 16:00"), freq="8h")
    f = pd.DataFrame({"czas": odczyty, "fundingRate": 0.0001})  # |P − I| = 0,01 % ≤ zacisk → F = I
    o = pt.odtworz_funding(f, premia)
    assert (o["pokrycie"] >= 0.99).all()
    assert pt.zgodnosc_wzoru(o, "wzor_I")["zgodne_0_05pb"] == 1.0
    assert (
        pt.zgodnosc_wzoru(o, "waz_I")["zgodne_0_05pb"] == 1.0
    )  # stała premia: ważenie bez znaczenia
    assert pt.zgodnosc_wzoru(o, "wzor_0")["sredni_blad"] == pytest.approx(
        -0.0001
    )  # I = 0, P̄ w zacisku → F̂ = 0
    dziurawa = premia[premia["czas"].dt.hour % 2 == 0]  # połowa minut → poza pomiarem
    assert pt.zgodnosc_wzoru(pt.odtworz_funding(f, dziurawa), "wzor_I")["n"] == 0


# ------------------------------------------------------------------ spread i zgodność z FRED
def test_spread_bp_and_quote_anomalies():
    s = pt.spread_pb([100.0, 100.0, 0.0, 101.0, np.nan], [100.1, 100.0, 100.0, 100.0, 1.0])
    assert s[0] == pytest.approx(0.1 / 100.05 * 1e4) and s[1] == 0.0
    assert np.isnan(s[2:]).all()  # zero, odwrócone, brak


def test_fred_agreement_uses_16utc_summer_17utc_winter():
    idx = _godziny("2026-01-05", "2026-09-30")
    rng = np.random.default_rng(3)
    close = pd.Series(1.1 * np.exp(np.cumsum(rng.normal(0, 0.001, len(idx)))), index=idx)
    daty = pd.bdate_range("2026-01-06", "2026-09-29", tz=UTC)
    wart = [close[pt._letnia(d + pd.Timedelta(hours=16)) - pt.H] * 1.001 for d in daty]
    fred = pd.DataFrame({"date": daty, "value": wart})
    r = pt.zgodnosc_z_fred(close, fred, poziom=True)
    assert r["korelacja"] == pytest.approx(1.0) and r["mediana_odch"] == pytest.approx(
        0.001 / 1.001
    )
    assert r["n_dni"] == len(daty)
    przesuniete = pt.zgodnosc_z_fred(close, fred, poziom=True, godz_lato=20)
    assert przesuniete["korelacja"] < 0.999


def test_funding_state_by_settlement_instant_and_accrual_interval():
    kal = pt.Kalendarz("akcje_usa", ts("2026-09-14"), ts("2026-09-28"))
    czasy = pd.date_range(ts("2026-09-21 00:00"), ts("2026-09-27 16:00"), freq="8h")  # pn–nd, lato
    stawki = [0.0002 if (c.hour == 16 and c.weekday() < 5) else 0.0 for c in czasy]
    f = pd.DataFrame({"czas": czasy, "fundingRate": stawki})
    tf = pd.DataFrame(
        [{"gielda": "g", "symbol": "X", "odczyty_rok": 1095.0, "interwal_mod_h": 8.0}]
    )
    out = pt.stan_fundingu(kal, f, tf, "g", "X")
    assert out["f_T_otw_n"] == 5 and out["f_T_otw_rok"] == pytest.approx(0.0002 * 1095 * 100)
    assert out["f_T_zam_n"] == len(czasy) - 5 and out["f_T_zam_rok"] == 0.0
    assert out["f_prz_otw_n"] == 0  # 8 h naliczania > 6,5 h sesji: nigdy w całości otwarty
    # [08:00, 16:00) i [16:00, 24:00) w dni sesji → częściowo; [00:00, 08:00) i weekend → zamknięty
    assert out["f_prz_czesc_n"] == 10 and out["f_prz_zam_n"] == len(czasy) - 10


def test_weighted_premium_variant_uses_linear_weights():
    minuty = pd.date_range(ts("2026-09-20"), ts("2026-09-20 08:00"), freq="min", inclusive="left")
    rampa = np.linspace(0.0, 0.0016, len(minuty))  # premia rośnie w oknie
    premia = pd.DataFrame({"czas": minuty, "close": rampa})
    f = pd.DataFrame({"czas": [ts("2026-09-20 08:00")], "fundingRate": [0.0]})
    o = pt.odtworz_funding(f, premia).iloc[0]
    w = np.arange(1, len(rampa) + 1)
    assert o["p_waz"] == pytest.approx((rampa * w).sum() / w.sum())
    assert o["p_waz"] > o["p_sr"] == pytest.approx(rampa.mean())  # późniejsze minuty ważą więcej
    assert o["waz_0"] == pytest.approx(float(pt.funding_ze_wzoru(o["p_waz"], 8.0, 0.0)))
    assert o["wzor_0"] == pytest.approx(
        o["p_sr"] - pt.ZACISK
    )  # P̄ = 0,08 % > zacisk: F = P̄ − 0,05 %


def test_costs_use_official_tradfi_taker_and_standard_for_btc():
    czas = [ts("2026-09-28 18:19"), ts("2026-09-28 21:19")]  # w sesji USA i po niej
    mig = pd.DataFrame(
        {
            "czas": czas * 2,
            "gielda": ["bybit"] * 4,
            "symbol": ["SPYUSDT", "SPYUSDT", "BTCUSDT", "BTCUSDT"],
            "bid": [100.0, 100.0, 50_000.0, 50_000.0],
            "ask": [100.02, 100.04, 50_000.1, 50_000.1],
            "obrot24h": [1e6] * 4,
        }
    )
    spis = {
        "bybit": pd.DataFrame(
            {
                "symbol": ["SPYUSDT", "BTCUSDT"],
                "klasa": ["ETF", "BTC_kontrola"],
                "region": ["US", ""],
            }
        )
    }
    tk = pt.tabela_kosztow(mig, spis, {"bybit": ["SPYUSDT"]}).set_index("symbol")
    spy, btc = tk.loc["SPYUSDT"], tk.loc["BTCUSDT"]
    assert spy["n_sesja"] == 1 and spy["spread_pb_sesja"] == pytest.approx(0.02 / 100.01 * 1e4)
    assert spy["taker_proc"] == pytest.approx(pt.TAKER_TRADFI["bybit"] * 100)
    assert btc["taker_proc"] == pytest.approx(pt.TAKER_STANDARD["bybit"] * 100)
    assert spy["koszt_strony_proc"] == pytest.approx(
        (spy["spread_pb_med"] / 2 / 1e4 + pt.TAKER_TRADFI["bybit"]) * 100
    )
    assert spy["koszt_strony_standard_proc"] > spy["koszt_strony_proc"]
