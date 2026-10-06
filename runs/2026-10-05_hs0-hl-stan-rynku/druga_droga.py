"""HS0 — bramka 16a: kluczowe liczby drugą drogą (osobny kod i inne zapytania niż `sonda_historii.py`).

(1) Najstarszy funding BTC: okna miesięczne od 2022-01 (`startTime`/`endTime` w oknie — NIE `startTime = 0`
    jak w sondzie) → pierwszy miesiąc z danymi → najstarszy rekord w nim; dla porównania ten sam sposób dla
    ETH i SOL.
(2) Pokrycie koszyka: nazwy monet z `meta.universe` ZAPISANEJ przez kolektor w próbie (`metaAndAssetCtxs`,
    nie endpoint `meta` jak w sondzie) i reguła nazwy zapisana inaczej (wyrażenia regularne) → liczba
    symboli koszyka na HL. Koszyk: `dziennik/koszyk.csv`, WYŁĄCZNIE kolumny `symbol` i `czlonek_top20`.
(3) Rozmiar dobowy: z pliku próby kolektora — rozmiar pliku / liczba linii po rozpakowaniu (bez funkcji
    kolektora) → średni człon × 1 440 migawek.
(1b) [dopisane PO obejrzeniu wyniku sondy] Liczba rekordów fundingu BTC drugą drogą: okna PÓŁMIESIĘCZNE
    (≤ 384 godzin, poniżej limitu strony) od 2023-05 do końca okna sondy (2026-10-05 20:02:23 UTC) → suma
    wobec 29 259 z pełnego stronicowania; per miesiąc odstępy 1 h / 8 h / inne (gdzie są dziury i od kiedy
    funding jest co godzinę).
(4) [dopisane PO obejrzeniu wyniku sondy, opisowo — kontrola jakości, nie pytanie z pre-rejestracji]
    Świece 1d sprzed pierwszego fundingu (BTC od 2020-08-19, a funding od 2023-05-12): pola `n` (liczba
    transakcji) i `v` (wolumen) przed i po pierwszym fundingu — czy wczesne świece to handel na HL.

Sieć: tylko `https://api.hyperliquid.xyz/info` przez `data.collect_hl_stan._post` (https, weryfikacja
certyfikatu, bez przekierowań, limit rozmiaru); ~140 zapytań, odstęp 5 s (puste okna 240 wagi/min, okno półmiesięczne ≤ 40 wagi → ≤ 480
wagi/min).

Uruchomienie (z katalogu repo):
    PYTHONUTF8=1 .venv/bin/python runs/2026-10-05_hs0-hl-stan-rynku/druga_droga.py <plik dnia z próby kolektora>
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from data.collect_hl_stan import INFO_URL, _post, parsuj  # noqa: E402

UTC = dt.timezone.utc
DZIEN = 86_400_000
GODZ = 3_600_000
KONIEC_SONDY = int(dt.datetime(2026, 10, 5, 20, 2, 23, tzinfo=UTC).timestamp() * 1000)  # „teraz” P2 sondy


def info(body: dict):
    odp = parsuj(_post(INFO_URL, body))
    time.sleep(5.0)
    return odp


def iso(ms) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M:%S") if ms else "-"


def najstarszy_miesiacami(coin: str) -> tuple[int | None, int]:
    zapytan = 0
    rok, mies = 2022, 1
    while (rok, mies) <= (2026, 10):
        a = dt.datetime(rok, mies, 1, tzinfo=UTC)
        rok2, mies2 = (rok + 1, 1) if mies == 12 else (rok, mies + 1)
        b = dt.datetime(rok2, mies2, 1, tzinfo=UTC)
        rek = info(
            {
                "type": "fundingHistory",
                "coin": coin,
                "startTime": int(a.timestamp() * 1000),
                "endTime": int(b.timestamp() * 1000) - 1,
            }
        )
        zapytan += 1
        if rek:
            pierwszy = min(rek, key=lambda r: r["time"])
            print(f"  {coin}: pola rekordu fundingHistory {sorted(pierwszy)}; najstarszy {json.dumps(pierwszy)}",
                  flush=True)
            return pierwszy["time"], zapytan
        rok, mies = rok2, mies2
    return None, zapytan


def btc_polmiesiacami(t0: int) -> None:
    """Rekordy fundingu BTC w oknach półmiesięcznych (1.–15. i 16.–koniec) od miesiąca t0 do KONIEC_SONDY."""
    start = dt.datetime.fromtimestamp(t0 / 1000, tz=UTC)
    rok, mies = start.year, start.month
    suma, dziury_mies = 0, []
    while True:
        a = dt.datetime(rok, mies, 1, tzinfo=UTC)
        rok2, mies2 = (rok + 1, 1) if mies == 12 else (rok, mies + 1)
        b = dt.datetime(rok2, mies2, 1, tzinfo=UTC)
        a_ms = int(a.timestamp() * 1000)
        if a_ms > KONIEC_SONDY:
            break
        polowa = int(dt.datetime(rok, mies, 16, tzinfo=UTC).timestamp() * 1000)
        b_ms = min(int(b.timestamp() * 1000), KONIEC_SONDY + 1)
        rek = []
        for x, y in ((a_ms, min(polowa, b_ms)), (polowa, b_ms)):
            if x >= y:
                continue
            strona = info({"type": "fundingHistory", "coin": "BTC", "startTime": x, "endTime": y - 1})
            if len(strona) >= 500:
                print(f"  UWAGA: okno {iso(x)} zwróciło {len(strona)} rekordów — możliwe ucięcie", flush=True)
            rek.extend(strona)
        czasy = sorted({r["time"] for r in rek})
        d = [q - p for p, q in zip(czasy, czasy[1:])]
        h1 = sum(1 for v in d if abs(v - GODZ) <= 60_000)
        h8 = sum(1 for v in d if abs(v - 8 * GODZ) <= 60_000)
        inne = len(d) - h1 - h8
        godzin = (b_ms - max(a_ms, t0)) / GODZ
        suma += len(rek)
        if inne or h8 or len(rek) < int(godzin) - 1:
            dziury_mies.append(f"{rok}-{mies:02d}")
        print(f"  {rok}-{mies:02d}: {len(rek)} rek. (godzin w oknie {godzin:.0f}); odstępy 1 h: {h1}, 8 h: {h8}, "
              f"inne: {inne}" + (f" [{', '.join(f'{v / GODZ:.2f} h' for v in d if abs(v - GODZ) > 60_000 and abs(v - 8 * GODZ) > 60_000)}]" if inne else ""),
              flush=True)
        rok, mies = rok2, mies2
    print(f"  SUMA BTC (okna półmiesięczne, do {iso(KONIEC_SONDY)}): {suma} rekordów (pełne stronicowanie w sondzie: 29 259)",
          flush=True)
    print(f"  miesiące z odstępem ≠ 1 h albo z brakami: {dziury_mies}", flush=True)


def nazwa_regex(symbol: str) -> str | None:
    if m := re.fullmatch(r"1000([A-Za-z]+)USDT", symbol):
        return "k" + m.group(1)
    if m := re.fullmatch(r"(.+)USDT", symbol):
        return m.group(1)
    return None


def swiece_przed_fundingiem(coin: str, t_fund: int, teraz: int) -> None:
    sw = info({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d", "startTime": 0, "endTime": teraz}})
    sw = sorted(sw, key=lambda s: s["t"])
    przed = [s for s in sw if s["t"] + DZIEN <= t_fund]
    po = [s for s in sw if s["t"] >= t_fund]
    zero_n = sum(1 for s in przed if int(s.get("n", 0)) == 0)
    zero_v = sum(1 for s in przed if float(s.get("v", 0)) == 0.0)
    print(f"  {coin}: świec 1d {len(sw)}; przed pierwszym fundingiem ({iso(t_fund)}): {len(przed)}, "
          f"z n = 0: {zero_n}, z v = 0: {zero_v}; od fundingu: {len(po)}", flush=True)
    for s in przed[:2] + przed[-2:] + po[:2]:
        print(f"    {iso(s['t'])}: o {s['o']} c {s['c']} v {s['v']} n {s['n']}", flush=True)
    if przed:
        med_n_przed = sorted(int(s["n"]) for s in przed)[len(przed) // 2]
        med_n_po = sorted(int(s["n"]) for s in po)[len(po) // 2] if po else None
        print(f"    mediana n: przed fundingiem {med_n_przed}, od fundingu {med_n_po}", flush=True)


def main(plik_proby: str) -> int:
    print(f"HS0 druga droga — start {dt.datetime.now(tz=UTC):%Y-%m-%d %H:%M:%S} UTC", flush=True)
    print("\n(1) najstarszy funding — okna miesięczne od 2022-01 (bez startTime = 0)", flush=True)
    pierwszy = {}
    for coin in ("BTC", "ETH", "SOL"):
        t0, n = najstarszy_miesiacami(coin)
        pierwszy[coin] = t0
        print(f"  {coin}: najstarszy rekord {iso(t0) if t0 else 'BRAK DANYCH'} ({t0} ms; {n} zapytań)", flush=True)

    print("\n(1b) [po wyniku] liczba rekordów fundingu BTC oknami półmiesięcznymi; odstępy per miesiąc", flush=True)
    if pierwszy.get("BTC"):
        btc_polmiesiacami(pierwszy["BTC"])

    print("\n(2) pokrycie koszyka — meta z pliku kolektora (metaAndAssetCtxs) + reguła jako regex", flush=True)
    with gzip.open(plik_proby, "rt", encoding="ascii") as f:
        rekordy = [json.loads(linia) for linia in f if linia.strip()]
    uni = rekordy[-1]["odpowiedz"][0]["universe"]
    nazwy = {u["name"]: bool(u.get("isDelisted")) for u in uni}
    kosz = pd.read_csv(REPO / "dziennik" / "koszyk.csv", usecols=["symbol", "czlonek_top20"])
    top = sorted(set(kosz.loc[kosz["czlonek_top20"].astype(str).str.lower() == "true", "symbol"]))
    na = [s for s in top if nazwa_regex(s) in nazwy]
    notowane = [s for s in na if not nazwy[nazwa_regex(s)]]
    print(f"  monet w zapisanej migawce: {len(uni)} (wycofane {sum(nazwy.values())})", flush=True)
    print(f"  koszyk: {len(top)} symboli; na HL {len(na)} (notowane {len(notowane)}); poza HL: "
          f"{[s for s in top if s not in na]}", flush=True)

    print("\n(3) rozmiar dobowy z pliku próby kolektora", flush=True)
    surowe_gz = Path(plik_proby).read_bytes()
    rozpakowane = gzip.decompress(surowe_gz)
    linie = rozpakowane.count(b"\n")
    print(f"  plik {len(surowe_gz)} B gzip, {len(rozpakowane)} B po rozpakowaniu, linii {linie}; "
          f"średnio {len(surowe_gz) / linie:.0f} B gzip i {len(rozpakowane) / linie:.0f} B surowo na migawkę → "
          f"× 1 440 = {len(surowe_gz) / linie * 1440 / 1e6:.1f} MB/dobę gzip "
          f"({len(rozpakowane) / linie * 1440 / 1e6:.0f} MB surowo)", flush=True)
    print(f"  czasy odbioru: {[r['czas_utc'] for r in rekordy]}", flush=True)
    print(f"  opóźnienie odpowiedzi (czas_ms − wyslano_ms): {[r['czas_ms'] - r['wyslano_ms'] for r in rekordy]} ms",
          flush=True)

    print("\n(4) [po wyniku, opisowo] świece 1d sprzed pierwszego fundingu — czy to handel na HL?", flush=True)
    teraz = int(time.time() * 1000)
    if pierwszy.get("BTC"):
        swiece_przed_fundingiem("BTC", pierwszy["BTC"], teraz)
    for coin in ("ZEC", "ADA"):
        f0 = info({"type": "fundingHistory", "coin": coin, "startTime": 0, "endTime": teraz})
        if f0:
            swiece_przed_fundingiem(coin, min(r["time"] for r in f0), teraz)
        else:
            print(f"  {coin}: funding BRAK DANYCH", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
