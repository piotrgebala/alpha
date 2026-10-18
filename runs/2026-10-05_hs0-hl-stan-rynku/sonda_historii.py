"""HS0 — sonda historii publicznego API Hyperliquid (`fundingHistory`, `candleSnapshot`) i kontrola
pozytywna K1/K2 na żywo. Jednorazowa. Pre-rejestracja: README tej rundy (commit `a6f0fbc`) — pytania P1–P5,
tolerancje K1/K2, budżet wag, reguła BRAK DANYCH.

Kolejność: P1 (spis `meta`, `perpDexs`) i P5 (koszyk → nazwy HL) → kontrola pozytywna K1/K2 na najbliższej
pełnej godzinie (migawka `metaAndAssetCtxs` w [HH:59:00, HH:59:40], porównanie po H + 30 s) → P3 (głębokość
świec BTC) → P2/P3/P4 per moneta zestawu S → druga droga najstarszego fundingu BTC → podsumowanie.

Sieć: tylko `https://api.hyperliquid.xyz/info` przez `data.collect_hl_stan._post` (https, weryfikacja
certyfikatu, bez przekierowań, limit rozmiaru). Budżet: waga 20 + ⌈n/20⌉ (ostrożnie dla obu endpointów),
odstęp w·0,12 s po każdym zapytaniu (≤ 500 wagi/min średnio), 429/5xx → 5·2^k s (k = 0…4), potem BRAK DANYCH.
Koszyk: `dziennik/koszyk.csv` — WYŁĄCZNIE kolumny `symbol` i `czlonek_top20`.

Uruchomienie (z katalogu repo):
    PYTHONUTF8=1 .venv/bin/python runs/2026-10-05_hs0-hl-stan-rynku/sonda_historii.py \
        > runs/2026-10-05_hs0-hl-stan-rynku/raw_output.txt 2>&1
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import statistics
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from data.collect_hl_stan import INFO_URL, _post, parsuj  # noqa: E402

S_NA_WAGE = 0.12
RETRY = (429, 500, 502, 503, 504)
Z_DOPLATA = ("fundingHistory", "candleSnapshot")
GODZ = 3_600_000
DZIEN = 86_400_000
ROK = 365.25 * DZIEN
IV_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": GODZ, "4h": 4 * GODZ, "1d": DZIEN}
MAX_WYCOFANYCH = 40
TRZY = ("BTC", "ETH", "SOL")
K1_ABS, K1_WZGL = 1e-6, 0.25
K2_PASMO = 0.002
PROG_RESZTY = 0.80


def iso(ms) -> str:
    if ms is None:
        return "-"
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def lata(a, b) -> str:
    return "-" if a is None or b is None else f"{(b - a) / ROK:.2f}"


class Budzet:
    """Zapytania z budżetem wag (ostrożnie liczona waga, odstęp w·0,12 s) i ponowieniami po 429/5xx."""

    def __init__(self) -> None:
        self.waga = 0
        self.zapytan = 0
        self.n429 = 0
        self.n5xx = 0
        self.brak = 0
        self.start = time.monotonic()
        self.odbior_ms: int | None = None  # czas odbioru ostatniej udanej odpowiedzi (przed odstępem)

    def zapytaj(self, body: dict):
        for k in range(5):
            try:
                odp = parsuj(_post(INFO_URL, body))
                self.odbior_ms = int(time.time() * 1000)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    self.n429 += 1
                elif e.code in RETRY:
                    self.n5xx += 1
                else:
                    self.brak += 1
                    print(f"  HTTP {e.code} dla {json.dumps(body)} — BRAK DANYCH", flush=True)
                    return None
                print(f"  HTTP {e.code} (próba {k + 1}/5) dla {body.get('type')}", flush=True)
            except (OSError, ValueError) as e:  # sieć, ucięty JSON, za duża odpowiedź
                print(f"  błąd {type(e).__name__}: {str(e)[:120]} (próba {k + 1}/5)", flush=True)
            time.sleep(5 * 2**k)
        else:
            self.brak += 1
            print(f"  5 nieudanych prób: {json.dumps(body)} — BRAK DANYCH", flush=True)
            return None
        self.zapytan += 1
        n = len(odp) if isinstance(odp, list) else 0
        w = 20 + (math.ceil(n / 20) if body["type"] in Z_DOPLATA else 0)
        self.waga += w
        time.sleep(w * S_NA_WAGE)
        return odp

    def tempo(self) -> float:
        minuty = (time.monotonic() - self.start) / 60.0
        return self.waga / minuty if minuty > 0 else 0.0


def funding(b: Budzet, coin: str, start: int, end: int | None = None):
    body = {"type": "fundingHistory", "coin": coin, "startTime": int(start)}
    if end is not None:
        body["endTime"] = int(end)
    return b.zapytaj(body)


def swiece(b: Budzet, coin: str, iv: str, start: int, end: int):
    return b.zapytaj(
        {
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": iv, "startTime": int(start), "endTime": int(end)},
        }
    )


def nazwa_hl(symbol: str) -> str | None:
    """Reguła z pre-rejestracji: XUSDT → X; 1000X (X z samych liter) → kX; inaczej brak."""
    if not symbol.endswith("USDT"):
        return None
    base = symbol[: -len("USDT")]
    if base.startswith("1000") and base[4:].isalpha():
        return "k" + base[4:]
    return base


def czekaj_do(ts_s: float) -> None:
    while (zostalo := ts_s - time.time()) > 0:
        time.sleep(min(30.0, zostalo))


def opis_odstepow(czasy: list[int]) -> dict:
    u = sorted(set(czasy))
    d = [b - a for a, b in zip(u, u[1:])]
    dziury = [(a, b) for a, b in zip(u, u[1:]) if b - a > 1.5 * GODZ]
    return {
        "n": len(czasy),
        "duplikaty": len(czasy) - len(u),
        "mediana_h": statistics.median(d) / GODZ if d else None,
        "inne_niz_1h": sum(1 for x in d if abs(x - GODZ) > 60_000),
        "dziury": dziury,
        "nie_na_pelnej_godzinie": sum(1 for t in u if min(t % GODZ, GODZ - t % GODZ) > 60_000),
    }


def caly_funding(b: Budzet, coin: str, teraz: int, max_stron: int = 1000):
    """Pełne stronicowanie od startTime = 0 (następny start = ostatni czas + 1 ms) do pustej strony."""
    rek, start, strony, rozmiary = [], 0, 0, []
    while strony < max_stron:
        strona = funding(b, coin, start, teraz)
        if strona is None:
            return None, strony, rozmiary
        strony += 1
        rozmiary.append(len(strona))
        if not strona:
            return rek, strony, rozmiary
        rek.extend(strona)
        ost = max(r["time"] for r in strona)
        if ost + 1 <= start:
            print(f"  {coin}: brak postępu stronicowania przy {start} — przerywam", flush=True)
            return None, strony, rozmiary
        start = ost + 1
    print(f"  {coin}: limit {max_stron} stron — przerywam", flush=True)
    return None, strony, rozmiary


# ---------------------------------------------------------------------------------------------- K1/K2
def kontrola(b: Budzet, monety: list[str]) -> None:
    print("\n=== Kontrola pozytywna K1 (funding) i K2 (świeca 1m) ===", flush=True)
    teraz = time.time()
    h_s = (math.floor(teraz / 3600) + 1) * 3600
    if teraz > h_s - 20:  # po HH:59:40 — następna godzina
        h_s += 3600
    print(f"czekam na migawkę o {iso((h_s - 55) * 1000)} UTC (pełna godzina H = {iso(h_s * 1000)})", flush=True)
    czekaj_do(h_s - 55)
    ctx = b.zapytaj({"type": "metaAndAssetCtxs"})
    czas_ms = b.odbior_ms if ctx is not None else int(time.time() * 1000)
    if ctx is None:
        print("migawka metaAndAssetCtxs: BRAK DANYCH — kontrola NIEZALICZONA (brak odczytu na żywo)", flush=True)
        return
    w_oknie = h_s * 1000 - 60_000 <= czas_ms <= h_s * 1000 - 20_000
    print(f"migawka odebrana {iso(czas_ms)}.{czas_ms % 1000:03d} UTC; w oknie [HH:59:00, HH:59:40]: {w_oknie}", flush=True)
    surowo = json.dumps(ctx, separators=(",", ":")).encode("ascii")
    gz = gzip.compress(surowo, compresslevel=9, mtime=0)
    print(
        f"rozmiar migawki: {len(surowo)} B surowo, {len(gz)} B gzip (poziom 9) → × 1 440 = "
        f"{len(gz) * 1440 / 1e6:.1f} MB/dobę (druga droga szacunku kolektora)",
        flush=True,
    )
    uni, ctxs = ctx[0]["universe"], ctx[1]
    po_nazwie = {u["name"]: c for u, c in zip(uni, ctxs)}
    m_ms = (czas_ms // 60_000) * 60_000
    h_ms = h_s * 1000
    czekaj_do(h_s + 30)
    wyniki = []
    for coin in monety:
        c = po_nazwie.get(coin)
        if c is None:
            print(f"{coin:>8}: brak w migawce — BRAK DANYCH", flush=True)
            wyniki.append((coin, None, None))
            continue
        r_ctx = float(c["funding"])
        r_hist = None
        while True:
            rek = funding(b, coin, h_ms - 600_000, h_ms + 600_000)
            pasujace = [r for r in (rek or []) if abs(r["time"] - h_ms) <= 60_000]
            if pasujace:
                r_hist = float(pasujace[0]["fundingRate"])
                t_hist = pasujace[0]["time"]
                break
            if time.time() > h_s + 300:
                break
            time.sleep(30)
        k1 = None
        if r_hist is not None:
            tol = K1_ABS + K1_WZGL * abs(r_ctx)
            k1 = abs(r_hist - r_ctx) <= tol
            k1_txt = (
                f"K1 r_ctx {r_ctx:+.8f} r_hist {r_hist:+.8f} (czas {iso(t_hist)}.{t_hist % 1000:03d}) "
                f"|Δ| {abs(r_hist - r_ctx):.2e} tol {tol:.2e} → {'zgodna' if k1 else 'NIEZGODNA'}"
            )
        else:
            k1_txt = f"K1 r_ctx {r_ctx:+.8f} r_hist BRAK DANYCH (do H + 5 min)"
        mid = c.get("midPx")
        px = float(mid) if mid is not None else float(c["markPx"])
        sw = swiece(b, coin, "1m", m_ms, m_ms + 59_999) or []
        swieca = [s for s in sw if s.get("t") == m_ms]
        k2 = None
        if swieca:
            s = swieca[0]
            lo, hi, cl = float(s["l"]), float(s["h"]), float(s["c"])
            k2 = lo * (1 - K2_PASMO) <= px <= hi * (1 + K2_PASMO)
            k2_txt = (
                f"K2 {'midPx' if mid is not None else 'markPx'} {px:.6g} świeca {iso(m_ms)} l {lo:.6g} h {hi:.6g} "
                f"c {cl:.6g} |c/px−1| {abs(cl / px - 1) * 1e4:.1f} pb → {'zgodna' if k2 else 'NIEZGODNA'}"
            )
            wyniki.append((coin, k1, k2, abs(cl / px - 1)))
        else:
            k2_txt = f"K2 świeca 1m {iso(m_ms)}: BRAK DANYCH"
            wyniki.append((coin, k1, None, None))
        print(f"{coin:>8}: {k1_txt}; {k2_txt}", flush=True)
    trzy = [w for w in wyniki if w[0] in TRZY]
    reszta = [w for w in wyniki if w[0] not in TRZY]
    trzy_ok = len(trzy) == 3 and all(w[1] is True and w[2] is True for w in trzy)
    u1 = sum(1 for w in reszta if w[1] is True) / len(reszta) if reszta else 1.0
    u2 = sum(1 for w in reszta if w[2] is True) / len(reszta) if reszta else 1.0
    dev = [w[3] for w in wyniki if len(w) > 3 and w[3] is not None]
    dev_txt = (
        f"|c/px−1| mediana {statistics.median(dev) * 1e4:.1f} pb, maks. {max(dev) * 1e4:.1f} pb (n {len(dev)})"
        if dev
        else "|c/px−1|: brak świec do porównania"
    )
    print(
        f"BTC/ETH/SOL zgodne w K1 i K2: {trzy_ok}; pozostałe ({len(reszta)}): K1 {u1:.0%}, K2 {u2:.0%} "
        f"(próg {PROG_RESZTY:.0%}); {dev_txt}",
        flush=True,
    )
    zal = trzy_ok and u1 >= PROG_RESZTY and u2 >= PROG_RESZTY
    print(f"KONTROLA POZYTYWNA: {'ZALICZONA' if zal else 'NIEZALICZONA'}", flush=True)


# ---------------------------------------------------------------------------------------------- main
def main() -> int:
    b = Budzet()
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        commit = "?"
    print(f"HS0 sonda historii Hyperliquid — start {iso(int(time.time() * 1000))} UTC; commit {commit}; "
          f"python {sys.version.split()[0]}; źródło {INFO_URL}", flush=True)

    # P1 — spis
    print("\n=== P1 — spis perpetuali głównej giełdy ===", flush=True)
    meta = b.zapytaj({"type": "meta"})
    if meta is None:
        print("meta: BRAK DANYCH — koniec sondy", flush=True)
        return 1
    uni = meta["universe"]
    wycofane = sorted(u["name"] for u in uni if u.get("isDelisted"))
    notowane = [u["name"] for u in uni if not u.get("isDelisted")]
    status_hl = {u["name"]: ("wycofana" if u.get("isDelisted") else "notowana") for u in uni}
    print(f"monet w meta: {len(uni)}; notowane {len(notowane)}; wycofane (isDelisted) {len(wycofane)}", flush=True)
    print("wycofane: " + " ".join(wycofane), flush=True)
    dexy = b.zapytaj({"type": "perpDexs"})
    if isinstance(dexy, list):
        nazwy_dex = [d.get("name") for d in dexy if isinstance(d, dict)]
        print(f"perpDexs: {len(dexy)} pozycji (null = główna giełda: {dexy[0] is None if dexy else '-'}); "
              f"rynki HIP-3 poza zbiorem: "
              + " ".join(str(n) for n in nazwy_dex), flush=True)
    else:
        print("perpDexs: BRAK DANYCH", flush=True)

    # P5 — koszyk
    print("\n=== P5 — koszyk top-20 (dziennik/koszyk.csv: tylko symbol, czlonek_top20) ===", flush=True)
    kosz = pd.read_csv(REPO / "dziennik" / "koszyk.csv", usecols=["symbol", "czlonek_top20"])
    top = list(dict.fromkeys(kosz.loc[kosz["czlonek_top20"].astype(str).str.lower() == "true", "symbol"]))
    print(f"symboli z czlonek_top20 = True: {len(top)}", flush=True)
    koszyk_hl = []
    for s in top:
        n = nazwa_hl(s)
        st = status_hl.get(n, "brak na HL") if n else "brak dopasowania nazwy"
        print(f"  {s:>16} → {n or '-':>10}: {st}", flush=True)
        if n in status_hl:
            koszyk_hl.append(n)
    na_hl = len(koszyk_hl)
    print(f"koszyk na HL: {na_hl}/{len(top)} (notowane {sum(status_hl[n] == 'notowana' for n in koszyk_hl)}, "
          f"wycofane {sum(status_hl[n] == 'wycofana' for n in koszyk_hl)})", flush=True)

    # Kontrola pozytywna (najbliższa pełna godzina)
    kontrolne = list(TRZY) + [n for n in koszyk_hl if n not in TRZY and status_hl[n] == "notowana"]
    kontrola(b, kontrolne)
    print(f"[budżet] wag {b.waga}, zapytań {b.zapytan}, 429: {b.n429}, 5xx: {b.n5xx}, BRAK DANYCH: {b.brak}; "
          f"średnio {b.tempo():.0f} wagi/min", flush=True)

    teraz = int(time.time() * 1000)
    # P3 — głębokość świec BTC
    print(f"\n=== P3 — świece BTC: [0, teraz] i okno starsze niż 5 000 świec (teraz = {iso(teraz)}) ===", flush=True)
    for iv, ms in IV_MS.items():
        s = swiece(b, "BTC", iv, 0, teraz)
        if s is None:
            print(f"{iv:>4}: BRAK DANYCH", flush=True)
            continue
        t = [x["t"] for x in s]
        opis = f"{iv:>4}: [0, teraz] → {len(s)} świec, pierwsza {iso(min(t)) if t else '-'}, ostatnia {iso(max(t)) if t else '-'}"
        if t:
            opis += f", głębokość {(max(t) - min(t)) / DZIEN:.1f} dnia"
        if iv != "1d":
            stare = swiece(b, "BTC", iv, teraz - 6000 * ms, teraz - 5500 * ms)
            opis += (f"; okno [teraz − 6 000, teraz − 5 500 świec] ({iso(teraz - 6000 * ms)} … {iso(teraz - 5500 * ms)}) → "
                     f"{'BRAK DANYCH (błąd zapytania)' if stare is None else len(stare)} świec")
        else:
            opis += "; okno starsze niż 5 000 dni nie dotyczy (przed startem HL)"
        print(opis, flush=True)

    # Zestaw S
    wyc_probka = wycofane[:MAX_WYCOFANYCH]
    S = list(TRZY) + [n for n in koszyk_hl if n not in TRZY] + [n for n in wyc_probka if n not in koszyk_hl]
    print(f"\n=== P2/P3/P4 — per moneta zestawu S ({len(S)}: 3 + koszyk {len([n for n in koszyk_hl if n not in TRZY])} "
          f"+ wycofane {len([n for n in wyc_probka if n not in koszyk_hl])} z {len(wycofane)}) ===", flush=True)
    tabela = []
    pierwsza_strona_btc = None
    for coin in S:
        st = status_hl.get(coin, "brak na HL")
        sw = swiece(b, coin, "1d", 0, teraz)
        ts = [x["t"] for x in sw] if sw else []
        s_first, s_last = (min(ts), max(ts)) if ts else (None, None)
        f1 = funding(b, coin, 0, teraz)
        f_first = min(r["time"] for r in f1) if f1 else None
        if coin == "BTC":
            pierwsza_strona_btc = f1
        if st == "notowana":
            f2 = funding(b, coin, teraz - 2 * DZIEN, teraz)
        elif s_last is not None:
            f2 = funding(b, coin, s_last - 3 * DZIEN, s_last + 2 * DZIEN)
        else:
            f2 = funding(b, coin, teraz - 2 * DZIEN, teraz)
        f_last = max(r["time"] for r in f2) if f2 else None
        if f_last is None and f1:
            f_last = max(r["time"] for r in f1)  # cała historia mieści się na pierwszej stronie
        odst = opis_odstepow([r["time"] for r in f1]) if f1 else None
        linia = (
            f"{coin:>8} [{st}] funding: {'BRAK DANYCH' if not f1 else iso(f_first)} → {iso(f_last)} "
            f"({lata(f_first, f_last)} r.; 1. strona {len(f1) if f1 is not None else '-'} rek., "
            f"mediana odstępu {odst['mediana_h'] if odst and odst['mediana_h'] is not None else '-'} h); "
            f"świece 1d: {'BRAK DANYCH' if not ts else iso(s_first)} → {iso(s_last)} ({lata(s_first, s_last)} r., {len(ts)} świec)"
        )
        print(linia, flush=True)
        tabela.append((coin, st, f_first, f_last, s_first, s_last, len(f1) if f1 else 0))
    print(f"[budżet] wag {b.waga}, zapytań {b.zapytan}, 429: {b.n429}, 5xx: {b.n5xx}, BRAK DANYCH: {b.brak}; "
          f"średnio {b.tempo():.0f} wagi/min", flush=True)

    # Pełne stronicowanie BTC/ETH/SOL
    print("\n=== P2 — pełne stronicowanie fundingu BTC, ETH, SOL ===", flush=True)
    pelne = {}
    for coin in TRZY:
        rek, strony, rozmiary = caly_funding(b, coin, teraz)
        if rek is None:
            print(f"{coin}: BRAK DANYCH (po {strony} stronach)", flush=True)
            continue
        if not rek:
            print(f"{coin}: 0 rekordów — BRAK DANYCH (pusta pierwsza strona)", flush=True)
            continue
        o = opis_odstepow([r["time"] for r in rek])
        t = sorted(r["time"] for r in rek)
        oczek = (t[-1] - t[0]) // GODZ + 1 if t else 0
        zle = sum(1 for r in rek if not isinstance(r.get("fundingRate"), str))
        print(
            f"{coin}: {o['n']} rekordów na {strony} stronach (rozmiary stron: maks {max(rozmiary)}, "
            f"ostatnie {rozmiary[-3:]}); {iso(t[0])} → {iso(t[-1])} ({lata(t[0], t[-1])} r.); "
            f"oczekiwanych godzin {oczek}; duplikaty {o['duplikaty']}; mediana odstępu {o['mediana_h']} h; "
            f"odstępów ≠ 1 h (±1 min): {o['inne_niz_1h']}; dziur > 1,5 h: {len(o['dziury'])}; "
            f"czasów poza pełną godziną (> 1 min): {o['nie_na_pelnej_godzinie']}; fundingRate nie-tekst: {zle}",
            flush=True,
        )
        for a, bb in sorted(o["dziury"], key=lambda x: x[1] - x[0], reverse=True)[:5]:
            print(f"    dziura {iso(a)} → {iso(bb)} ({(bb - a) / GODZ:.1f} h)", flush=True)
        pelne[coin] = t

    # Druga droga: najstarszy funding BTC
    print("\n=== Druga droga — najstarszy funding BTC ===", flush=True)
    if pierwsza_strona_btc:
        t0 = min(r["time"] for r in pierwsza_strona_btc)
        przed = funding(b, "BTC", t0 - 60 * DZIEN, t0 - 1)
        print(f"(a) pierwsza strona od startTime = 0: najstarszy rekord {iso(t0)} ({t0} ms)", flush=True)
        print(f"(b) okno [t0 − 60 dni, t0 − 1 ms] → {'BRAK DANYCH' if przed is None else len(przed)} rekordów "
              f"(oczekiwane 0)", flush=True)
        if "BTC" in pelne:
            print(f"(c) pełne stronicowanie: najstarszy {iso(pelne['BTC'][0])} — "
                  f"{'zgodny' if pelne['BTC'][0] == t0 else 'NIEZGODNY'} z (a)", flush=True)
        btc = next((x for x in tabela if x[0] == "BTC"), None)
        if btc and btc[4] is not None:
            print(f"(d) pierwsza świeca 1d BTC (start notowań) {iso(btc[4])}; funding zaczyna się "
                  f"{(t0 - btc[4]) / DZIEN:+.1f} dnia względem niej", flush=True)
    else:
        print("BRAK DANYCH (pierwsza strona fundingu BTC pusta albo nieodczytana)", flush=True)

    # Podsumowanie
    print("\n=== Podsumowanie ===", flush=True)
    for grupa, nazwy in (("BTC/ETH/SOL", list(TRZY)),
                         ("koszyk top-20 na HL (bez BTC/ETH/SOL)", [n for n in koszyk_hl if n not in TRZY]),
                         ("wycofane (próbka)", [n for n in wyc_probka if n not in koszyk_hl])):
        wiersze = [x for x in tabela if x[0] in nazwy]
        lf = [(x[3] - x[2]) / ROK for x in wiersze if x[2] is not None and x[3] is not None]
        ls = [(x[5] - x[4]) / ROK for x in wiersze if x[4] is not None and x[5] is not None]
        brak_f = [x[0] for x in wiersze if x[2] is None]
        brak_s = [x[0] for x in wiersze if x[4] is None]
        print(
            f"{grupa}: monet {len(wiersze)}; lata fundingu min {min(lf):.2f} / mediana {statistics.median(lf):.2f} / "
            f"maks {max(lf):.2f}" if lf else f"{grupa}: monet {len(wiersze)}; funding BRAK DANYCH dla wszystkich",
            flush=True,
        )
        if ls:
            print(f"    lata świec 1d min {min(ls):.2f} / mediana {statistics.median(ls):.2f} / maks {max(ls):.2f}", flush=True)
        print(f"    BRAK DANYCH funding: {brak_f or 'brak'}; świece 1d: {brak_s or 'brak'}", flush=True)
    najstarszy = [x for x in tabela if x[2] is not None]
    if najstarszy:
        x = min(najstarszy, key=lambda r: r[2])
        print(f"najstarszy funding w zestawie S: {x[0]} {iso(x[2])}", flush=True)
    print(f"koszyk top-20: na HL {na_hl}/{len(top)}; poza HL: "
          f"{[s for s in top if nazwa_hl(s) not in status_hl]}", flush=True)
    print(f"[budżet końcowy] wag {b.waga}, zapytań {b.zapytan}, 429: {b.n429}, 5xx: {b.n5xx}, "
          f"BRAK DANYCH: {b.brak}; średnio {b.tempo():.0f} wagi/min; koniec {iso(int(time.time() * 1000))} UTC",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
