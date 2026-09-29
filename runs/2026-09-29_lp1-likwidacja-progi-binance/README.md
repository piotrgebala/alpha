# LP1 — cena likwidacji: płaski próg dziennika wobec progów depozytu Binance i ceny mark (2026-09-29)

> **STATUS: PRE-REJESTRACJA (przed pomiarem kroku 2).** Zadanie 017 tablicy, typ `przeglad`, decyzja użytkownika
> 2026-09-29: „tak wrzuć na tablicę z zadaniami”. **0 wariantów — POZA licznikami.** Liczymy tylko progi i liczbę
> przekroczeń progu; wpływu na zwrot strategii NIE liczymy (to byłby kolejny odczyt historii).

## Metadane

- **ID:** LP1 (zadanie 017, `zadania/017-likwidacja-progi-binance.md`). Gałąź `zadanie-017-likwidacja-progi-binance`
  od `master` `43bbe4a`.
- **Sieć:** wyłącznie (1) `raw.githubusercontent.com` — migawka `freqtrade/exchange/binance_leverage_tiers.json`
  z kopii `piotrgebala/freqtrade`, commit `84b4628`; (2) `data.binance.vision` — publiczne archiwum
  `markPriceKlines` 1d. Bez `leverageBracket`, bez kluczy, bez narzędzi handlowych, bez importu freqtrade.
- **Kod (nowy, poza łańcuchem dziennika):** `backtest/liq_binance.py` (wzór Binance przepisany samodzielnie + liczniki
  przekroczeń), `data/fetch_mark_1d.py` (kolektor mark), `backtest/run_lp1_likwidacja_progi.py` (skrypt rundy),
  testy `tests/test_liq_binance.py`. Nie zmienia `backtest/live_journal.py`, `backtest/ts_momentum.py` ani MMR.
- **Dane:** skład koszyka top-20 point-in-time z `data/raw/universe_full` (`rebalance_premium.monthly_members`,
  miesiące 2021-02 … 2026-06); cena ostatnia (high/low/close 1d) z `data/raw/universe_ohlc_full/ohlc_1d.parquet`
  (ten sam kolektor co RU1); cena mark z `data/raw/mark_1d/mark_1d.parquet` (nowy). Dane od 2021-01-01 (zasada 20).
  Nie czytamy `dziennik/*.csv`.

## Poprzedzające wyniki

- **LQ1 (wniosek 76):** likwidacja izolowana przy 3× kosztuje trend ~3,6 pkt/rok, 4,75 % pozycji-tygodni; przy 2×
  ~1,6 pkt. Model LQ1 zapisał z góry dwa uproszczenia: MMR 1 % dla wszystkich monet („konserwatywnie dla altów; BTC
  ma 0,4 %”) i ekstrema ceny OSTATNIEJ („knoty — konserwatywnie wobec ceny mark”). LP1 sprawdza właśnie te dwa
  słowa „konserwatywnie” — nic więcej.
- **RU1/RU2:** pełne uniwersum (`universe_full`) i OHLC członków — z nich bierzemy skład i ceny ostatnie.
- **Wniosek 107 / `runs/odczyty_historii.csv`:** każdy nowy odczyt zwrotu podnosi poprzeczkę; dlatego LP1 nie liczy
  zwrotu, a wiersza do rejestru odczytów nie dopisujemy (liczba przekroczeń progu to nie odczyt zwrotu strategii).
- Wnioski skumulowane dotyczące tej rundy: 76 (koszt likwidacji w trendzie) i 83 (RU2: werdykty odporne na korektę
  danych) — z nich wynika, że LP1 ma powiedzieć, czy uproszczenia LQ1 przesuwają LICZBĘ likwidacji, a nie przeliczać
  wyniku trendu.

## Pre-rejestracja (0 wariantów; zapisana przed krokiem 2)

**Wzór Binance** (izolowana, jedna pozycja, tryb jednokierunkowy; `backtest/liq_binance.py`):
odległość do likwidacji jako ułamek ceny wejścia = `(1/L + cum/N − MMR) / (1 ∓ MMR)` (− long, + short), gdzie MMR
i `cum` (maintenance amount) pochodzą z progu, do którego wpada nominał N. Nasz próg: `1/L − 1 %` (2× → 49 %,
3× → 32,33 %).

**Krok 1 (progi):** zbiór monet = suma składów top-20 z miesięcy 2021-02 … 2026-06. Dla każdej monety, N ∈ {1 tys.,
10 tys., 100 tys. USDT}, L ∈ {2, 3}, long i short: MMR, cum, odległość Binance, różnica wobec naszego progu (w pkt
procentowych). Monety bez progów w migawce (wycofane) → „BRAK W MIGAWCE”, liczone osobno, nie zgadywane.
Ograniczenie: migawka to progi z 2026-06-18, nie historyczne.

**Krok 2 (przekroczenia):** komórka = (moneta, dzień wejścia t), moneta w koszyku w miesiącu dnia t. Wejście po
zamknięciu dnia t po cenie ostatniej. Okno h ∈ {1 dzień, 7 dni} (7 = trzymanie trendu TS1, `HOLD_DAYS`), dni t+1…t+h.
Long „likwidowany”, gdy min(low)/wejście − 1 ≤ −próg; short, gdy max(high)/wejście − 1 ≥ próg. Cztery zestawy na
każde (h, L, strona): próg {nasz płaski, Binance przy N = 10 tys.} × ekstremum {ostatnia, mark}. Raport: tabela 2×2
„tylko ostatnia / tylko mark / obie / żadna” dla każdego progu, liczba dni i monet, plus braki mark.
Komórki bez pełnego okna w którymkolwiek szeregu wypadają (raportowane).

**Reguła decyzji (z góry):** porównujemy liczbę likwidacji „model dziennika” (próg płaski, cena ostatnia) z „model
Binance” (próg Binance N = 10 tys., cena mark), sumarycznie long + short, przy h = 7. Jeśli różnica względna
≥ 10 % przy 2× LUB 3× — rekomendujemy użytkownikowi rozważenie Poprawki (decyzja i tak należy do niego). Poniżej 10 %
— nie warto. Kierunek (zawyża / zaniża) raportujemy zawsze. Mierzalność (zasada 18): nie dotyczy — brak trafności
i zwrotu; liczymy zdarzenia, nie estymujemy przewagi.

**Druga droga (bramka 16a):** trzy przypadki przeliczone ręcznie w README (odległość z ceny LP, ekstrema z surowych
wierszy) + przeliczenie łącznej liczby przekroczeń inną drogą (pętla po wierszach zamiast macierzy).
