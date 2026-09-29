"""Skutek zmiany nazw na prawdziwych loaderach: oryginał serwera vs kopia po --wykonaj (tylko odczyt)."""

import sys

import pandas as pd

ORYG, KOPIA, KOD = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, KOD)
from backtest import rebalance_premium as rp  # noqa: E402
from data.fetch_live import symbol_files  # noqa: E402


def fix(s):
    try:
        return s if s.isascii() else s.encode("cp866").decode("utf-8")
    except UnicodeError:  # już poprawna nazwa (znaków CJK nie ma w cp866)
        return s


def members(vol, od):
    months = list(pd.date_range(pd.Timestamp(od, tz="UTC"), vol.index.max(), freq="MS"))
    return rp.monthly_members(vol, months)


def porownaj(nazwa, mo, mk):
    rozne = 0
    for m in mo:
        a, b = sorted(fix(s) for s in mo[m]), mk[m]
        if a != b:
            rozne += 1
            print(
                f"  {nazwa} {m.date()}: tylko oryginał {sorted(set(a) - set(b))}, tylko kopia {sorted(set(b) - set(a))}"
            )
        elif any(not s.isascii() for s in b):
            print(
                f"  {nazwa} {m.date()}: ten sam skład; spoza ASCII w kopii {[s for s in b if not s.isascii()]}"
            )
    print(f"  {nazwa}: miesięcy {len(mo)}, z innym składem (po etykiecie) {rozne}")


print("== universe_full / universe_2026q3 (rebalance_premium.load_universe, bez filtra nazw)")
for d, od in (("universe_full", "2021-02-01"), ("universe_2026q3", "2025-08-01")):
    _, vo = rp.load_universe(f"{ORYG}/{d}")
    _, vk = rp.load_universe(f"{KOPIA}/{d}")
    print(
        f"  {d}: kolumny oryginał {vo.shape[1]}, kopia {vk.shape[1]}; spoza ASCII w kopii {[c for c in vk.columns if not c.isascii()]}"
    )
    porownaj(d, members(vo, od), members(vk, od))

print("== live (data.fetch_live.symbol_files — filtr SYMBOL_RE jak w dzienniku)")


def live_vol(katalog):
    fr = {}
    for s, p in symbol_files(katalog).items():
        x = pd.read_parquet(p, columns=["open_time", "quote_volume"])
        if len(x):
            fr[s] = x.set_index(pd.to_datetime(x["open_time"], utc=True))["quote_volume"]
    return pd.concat(fr, axis=1, sort=True)


lo, lk = live_vol(f"{ORYG}/live"), live_vol(f"{KOPIA}/live")
print(
    f"  symboli: oryginał {lo.shape[1]} (spoza ASCII {[c for c in lo.columns if not c.isascii()]}), kopia {lk.shape[1]} (spoza ASCII {[c for c in lk.columns if not c.isascii()]})"
)
porownaj("live", members(lo, "2025-09-01"), members(lk, "2025-09-01"))

print("== łączenie z universe_ohlc_full (jak TP1/RU1/RU2/LP1: high.reindex(columns=close.columns))")
o = pd.read_parquet(f"{ORYG}/universe_ohlc_full/ohlc_1d.parquet")
o["open_time"] = pd.to_datetime(o["open_time"], utc=True)
high = o.pivot(index="open_time", columns="symbol", values="high")
maj = (high.index >= pd.Timestamp("2026-05-01", tz="UTC")) & (
    high.index < pd.Timestamp("2026-06-01", tz="UTC")
)
for nazwa, katalog in (("oryginał", ORYG), ("kopia", KOPIA)):
    close, _ = rp.load_universe(f"{katalog}/universe_full")
    sym = [c for c in close.columns if fix(c) == "币安人生USDT"][0]
    h = high.reindex(columns=close.columns)[sym]
    print(
        f"  {nazwa}: kolumna {sym!r}: dni 2026-05 z high = {int(h[maj].notna().sum())}, z close = {int(close[sym][(close.index >= pd.Timestamp('2026-05-01', tz='UTC')) & (close.index < pd.Timestamp('2026-06-01', tz='UTC'))].notna().sum())}"
    )
