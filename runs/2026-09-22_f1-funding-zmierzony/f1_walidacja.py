"""
Walidacja wyniku F1 (CLAUDE.md zasada 16a) — druga, niezalezna droga.

1. Czy ramie A jest IDENTYCZNE z ramieniem A rundy M1 (ta sama konfiguracja, inny skrypt)?
   Jesli tak, mamy kontrole determinizmu i odtwarzalnosci miedzy rundami.
2. Trafnosc przeliczona wprost z journalu.
3. Czy ustalenie H2.1 ("funding POTRAJA liczbe decyzji") sie odtwarza?

Uruchomienie: PYTHONPATH=. py runs/2026-09-22_f1-funding-zmierzony/f1_walidacja.py
"""
import yaml

from agents.funding_features import FUNDING_COLUMN, attach_funding_rate
from agents.ml_optimizer import REVERSION_FEATURES
from backtest.checkpoint_lib import PRIMARY_SEED, run_and_summarize
from backtest.diagnose_timeframe_geometry import _load, _load_cfg
from backtest.engine import REGIME_ALL
from data.fetch_funding import get_funding_rate_history_cached

cfg = _load_cfg()
rule = yaml.safe_load(open("config/settings.yaml", encoding="utf-8"))["regime_rule"]
baza = _load(cfg, "4h")
funding = get_funding_rate_history_cached(
    symbol=cfg["primary_symbol"],
    start=(cfg.get("timeframe_start_overrides") or {}).get("4h", cfg["start"]),
    end=cfg["end"], cache_dir=cfg["cache_dir"], exchange_id=cfg["exchange_id"])
z_fundingiem = attach_funding_rate(baza, funding)

KW = dict(seed=PRIMARY_SEED, vertical_barrier_candles=3, candles_per_day=6,
          candle_minutes=240, train_days=60, test_days=28, step_days=28,
          trend_threshold=rule["trend_threshold"], range_threshold=rule["range_threshold"])


def przebieg(df, cechy):
    r = run_and_summarize(df, regime_feature_sets=[(REGIME_ALL, cechy)], **KW)
    t = r["backtest"]["trades"]
    realne = t.loc[~t["kill_switch_active"]]
    aktywne = [f for f in r["backtest"]["folds_summary"] if not f["skipped"]]
    return {
        "n": len(realne),
        "trafienia": int((realne["gross_pnl"] > 0).sum()),
        "sygnaly": sum(f["n_signals"] for f in aktywne),
        "abst": sum(f["n_signals_no_direction"] for f in aktywne),
        "z_tabeli": float(r["edge_per_regime"].iloc[0]["hit_rate"]),
    }


print("=" * 96)
print("1. KONTROLA DETERMINIZMU — ramie A liczone BEZ kolumny funding w danych")
print("=" * 96)
print("  Ramie A w F1 biegnie na ramce Z DOKLEJONA kolumna funding (choc jej nie uzywa).")
print("  M1 liczylo to samo ramie na ramce BEZ tej kolumny. Jesli wyniki sa identyczne,")
print("  dokleJenie niewykorzystanej kolumny nie wplywa na pipeline — czego wymaga zasada 4.\n")
a_bez = przebieg(baza, REVERSION_FEATURES)
a_z = przebieg(z_fundingiem, REVERSION_FEATURES)
print(f"  ramie A bez kolumny funding : n = {a_bez['n']}, trafien = {a_bez['trafienia']}, "
      f"p = {100 * a_bez['trafienia'] / a_bez['n']:.4f}%")
print(f"  ramie A z  kolumna  funding : n = {a_z['n']}, trafien = {a_z['trafienia']}, "
      f"p = {100 * a_z['trafienia'] / a_z['n']:.4f}%")
zgodne = a_bez["n"] == a_z["n"] and a_bez["trafienia"] == a_z["trafienia"]
print(f"  >>> {'IDENTYCZNE' if zgodne else 'ROZJAZD'} — "
      f"{'niewykorzystana kolumna nie wplywa na wynik' if zgodne else 'UWAGA: kolumna wplywa!'}")
print(f"  Kontrola wobec M1 (ramie A tamze): n = 8033, trafien = 4046, p = 50.3672%")

print("\n" + "=" * 96)
print("2. TRAFNOSC Z JOURNALU vs Z TABELI")
print("=" * 96)
b = przebieg(z_fundingiem, [*REVERSION_FEATURES, FUNDING_COLUMN])
for kod, w in (("A", a_z), ("B", b)):
    p = w["trafienia"] / w["n"]
    print(f"  ramie {kod}: z journalu {100 * p:.4f}%  z tabeli {100 * w['z_tabeli']:.4f}%  "
          f"roznica {100 * abs(p - w['z_tabeli']):.6f} pp")

print("\n" + "=" * 96)
print("3. CZY USTALENIE H2.1 SIE ODTWARZA? ('funding POTRAJA liczbe decyzji')")
print("=" * 96)
print(f"  H2.1 (przyrzad sprzed A1): ramie A = 35 sygnalow, ramie B = 98  ->  2.80x")
krotnosc = b["sygnaly"] / a_z["sygnaly"]
print(f"  F1   (przyrzad po   A1)  : ramie A = {a_z['sygnaly']:,} sygnalow, "
      f"ramie B = {b['sygnaly']:,}  ->  {krotnosc:.2f}x")
print(f"\n  >>> {'ODTWARZA SIE' if krotnosc > 2 else 'NIE ODTWARZA SIE'}.")
print("  Odczyt: przy abstynencji 99,3% model podejmowal 35 decyzji, wiec KAZDE drobne")
print("  zaburzenie posteriora mnozylo te liczbe wielokrotnie. Przy 8 000 decyzji ten sam")
print("  funding zmienia ja o procent. 'Potrojenie' bylo artefaktem zaglodzonej proby,")
print("  a nie miara informacyjnosci cechy.")
