# 02 — Cechy i metodologia leakage

## Zasada: ekstrakcja z wielu repozytoriów, nigdy zależność runtime

Repozytoria takie jak freqtrade to katalog do przeglądania i przepisywania logiki wskaźników,
nigdy zależność w `requirements.txt` silnika produkcyjnego. Powody:

1. **Niekonsystencja definicji.** Różne repo liczą te same wskaźniki (RSI, ATR) różnymi
   bibliotekami (TA-Lib, pandas_ta, ręczne implementacje) z różnym wygładzaniem (Wilder vs SMA) —
   wyniki różnią się nawet dla identycznie nazwanych cech. Rozwiązanie: **jedna biblioteka
   (TA-Lib) dla wszystkich cech**, przepisane nawet jeśli źródło używało czegoś innego.
2. **Look-ahead bias kompunduje się przy scalaniu kodu z wielu źródeł.** Każde repo może mieć
   subtelnie inny sposób liczenia cech względem świecy. Każda przepisana funkcja przechodzi test
   leakage PRZED wejściem do wspólnego pipeline'u — nie tylko finalny zbiór cech.
3. **Framework wnosi swój bagaż.** Import freqtrade jako biblioteki wnosi cały jego event loop,
   DataProvider, Telegram, webserver — zwiększa attack surface i utrudnia Compliance Gate.
4. **Survivorship bias w wyborze cech.** Wskaźniki domyślnie eksponowane w publicznych repo
   przetrwały w obiegu częściowo dlatego, że ktoś na nich pokazał dobry backtest — populacja już
   przefiltrowana przez "co historycznie wyglądało dobrze". Stała czujność, nie coś do
   jednorazowego zamknięcia.

## Feature registry — źródło prawdy

Pełny manifest: `agents/feature_registry.yaml`. Każdy wpis: wzór, biblioteka, okno, rola
(`base`/`regime_filter`/`signal`), grupa testowa (`shared`/`trend`/`range`), ryzyko leakage, data
dodania.

**9 cech w Fazie 0** (zaimplementowane w `agents/feature_miner.py`):

| Cecha | Wzór | Rola |
|---|---|---|
| `atr_14` | ATR, Wilder, 14 (TA-Lib) | baza |
| `atr_pctrank_20d` | percentyl `atr_14` w trailing 20 dniach (5760 świec @ 5m) | regime_filter |
| `direction_persistence_10` | \|Σsign(return)\|/10, ostatnie 10 świec | regime_filter |
| `return_lag_1` | ln(close_t/close_t-1) | signal, shared |
| `momentum_5` | ln(close_t/close_t-5) | signal, trend |
| `ema_diff_9_21` | (EMA9-EMA21)/close_t — znormalizowane przez cenę | signal, trend |
| `volume_zscore_20` | (volume-mean20)/std20 | signal, shared |
| `rsi_14` | RSI, Wilder, 14 (TA-Lib) | signal, range |
| `price_zscore_20` | (close-mean20)/std20 | signal, range |

**Ważna poprawka zaimplementowana:** `ema_diff_9_21` MUSI być znormalizowana przez `close` —
bez tego różnica dwóch EMA w USD nie jest porównywalna między BTC przy niskiej i wysokiej cenie w
obrębie 12 miesięcy danych.

## Regime rule (thresholdy startowe, do kalibracji)

```
trend:    atr_pctrank_20d > 0.7  AND  persistence > 0.7
range:    atr_pctrank_20d < 0.3  AND  persistence < 0.3
inaczej:  ambiguous → wyklucz z obu testów
```

**Empiryczne znalezisko (test na syntetycznych danych, 105k świec = 12 miesięcy):** przy tych
progach regime "trend" wyszedł na <1% świec (ambiguous ~80%, range ~20%). To strukturalna
właściwość AND-owania dwóch warunków, nie tylko artefakt syntetycznych danych — sprawdzić na
prawdziwych danych jako pierwsze; jeśli się powtórzy, Test 1 może mieć za mało próbek na
wiarygodny wynik, rozważ złagodzenie `trend_threshold`.

## Metodologia testu leakage

Dla każdej funkcji `compute_*`: policz cechę na `df[:T]` i `df[:T+k]`, sprawdź identyczność
wartości do indeksu T w obu przypadkach. Formalna wersja: `agent_5_compliance/test_leakage.py`
(pytest, parametryzowany po wszystkich funkcjach w `FEATURE_FUNCTIONS`).

**Priorytet:** `atr_pctrank_20d` — największe ryzyko leakage w całym zestawie, bo rolling window
musi być trailing (kończący się na aktualnej świecy), nigdy centered. Zaimplementowane przez
`pandas.Series.rolling().rank(pct=True)` — zweryfikowane empirycznie (ręczne przeliczenie +
9/9 nieformalny leakage sanity check na syntetycznych danych), że daje poprawną rangę OSTATNIEJ
wartości okna względem całego okna, szybko (0.097s/105k wierszy przy oknie 5760).

## Rozszerzanie feature setu — protokół

Nie testować od razu dużej liczby wskaźników. Powody:

1. **Multiple testing / data dredging.** Im więcej cech testowanych na tym samym zbiorze, tym
   większa szansa znalezienia przypadkowej kombinacji, która "działa" tylko na tej historii.
2. **Efektywna liczba próbek.** Świece 5m są silnie autokorelowane — efektywna liczba
   niezależnych obserwacji jest mniejsza niż liczba wierszy. Więcej cech przy tej samej liczbie
   efektywnych próbek = łatwiej przeuczyć.
3. **Koszt diagnostyczny.** Z 3-9 cechami, gdy backtest nie działa, wiadomo gdzie szukać
   problemu. Z 50 cechami — nie.

**Procedura rozszerzania (Faza 1+):** dodawaj cechy pojedynczo, mierz przyrost na out-of-sample
(nigdy in-sample). Używaj feature importance / SHAP z OOS foldów jako filtr, nie jako dowód.
Rozważ testowanie grupowe (rodziny wskaźników: momentum, volatility, volume) zamiast wielu
pojedynczych zmiennych naraz, żeby kontrolować multiple comparisons.
