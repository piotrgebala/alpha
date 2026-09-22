# Z9 — natywne świece 1h/4h: resample psuje WOLUMEN, a grubszy interwał obniża próg opłacalności z 82,8% do 52,7% (2026-09-22)

## ID testu

**Z9** (Backlog) — patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z9-native-timeframes`
- **Poprzedzający stan (master):** `1eff8f5` (Z18).
- **Komendy:** `py -m data.fetch_ohlcv` (pobranie kompletu interwałów),
  `py -m backtest.diagnose_timeframe_geometry`
- **Nowe pliki:** `backtest/diagnose_timeframe_geometry.py`
- **Zmiany:** `data/fetch_ohlcv.py` — `TIMEFRAME_MINUTES`, pętla po `cfg["timeframes"]`
  z raportem „z cache / pobrane z giełdy"; `config/settings.yaml` — `data.timeframes`.
- **Dane (trwały cache, `data/raw/`):** BTC/USDT:USDT 2023-07-01 → 2026-07-01 —
  **5m: 315 648**, **1h: 26 304**, **4h: 6 576** świec. Zero dziur w każdym interwale.
  Cache kluczowany po (symbol, interwał, zakres), więc każdy interwał ściągany jest RAZ.
- **Warianty hipotezy: 0** (walidacja danych + arytmetyka geometrii, bez uruchamiania modelu).
- **Testy:** **231/231** (bez zmian — zmiany dotyczą skryptu fetch i diagnostyki).

## Blok 1 (pytanie oryginalne Z9) — resample vs natywne

C2.6 testował hipotezę na świecach **resamplowanych z 5m**, bo sandbox nie miał dostępu do
Binance. Teraz mamy natywne, więc da się sprawdzić, czy agregacja zniekształcała dane.

| interwał | kolumna | identycznych | maks \|błąd wzgl.\| |
|---|---|---|---|
| 1h | open / high / low | 100,00% | ≤ 0,176% |
| 1h | close | 99,99% | 0,177% |
| **1h** | **volume** | **89,02%** | **283,79%** |
| 4h | open / low / close | 99,98% | ≤ 0,131% |
| 4h | high | 100,00% | 0,000% |
| **4h** | **volume** | **93,95%** | **23,13%** |

**Wynik: ceny są w porządku, wolumen NIE.** OHLC zgadza się praktycznie co do grosza
(mediana błędu 0,00000000%), ale wolumen rozjeżdża się w **11% świec 1h** i **6% świec 4h**,
miejscami o setki procent.

To ma konkretne konsekwencje: **`volume_zscore_20` jest cechą modelu** — występuje
i w `MOMENTUM_FEATURES`, i w `REVERSION_FEATURES` (`agents/ml_optimizer.py:45-46`). Zatem
w C2.6 model na 1h/4h dostawał częściowo zepsute wejście. Nie unieważnia to werdyktu C2.6
(NO-GO), ale oznacza, że tamten pomiar był robiony na danych gorszych, niż zakładano —
i że **każdy przyszły eksperyment na grubszych świecach musi używać natywnych**, nie resampla.

## Blok 2 — grubszy interwał NIE naprawia spójności

| interwał | `range`: epizodów / mediana / udział | `trend`: epizodów / mediana / udział |
|---|---|---|
| 5m | 9 717 / **5,0** świec / 21,62% | 728 / **2,0** / 0,53% |
| 1h | 980 / **4,0** świec / 23,41% | 45 / **1,0** / 0,37% |
| 4h | 297 / **4,0** świec / 25,98% | 17 / **1,0** / 0,43% |

Mediana epizodu w ŚWIECACH jest praktycznie **niezmienna** względem interwału (4–5 dla
`range`, 1–2 dla `trend`). To nie przypadek: reguła reżimu jest zdefiniowana w jednostkach
świec (`direction_persistence_10` na 10 świecach, `atr_pctrank_20d` na oknie 20 dni), więc
długość epizodu liczona w świecach jest z grubsza niezmiennicza skalowo.

**Wniosek: sam grubszy interwał nie uspójnia bramki przy `VERTICAL_BARRIER_CANDLES = 12`.**
Ale tabela pokazuje coś innego — **przy `V = 3` reżim `range` jest SPÓJNY na każdym
interwale** (mediana 4–5 ≥ 3; udział świec z pełnym oknem wewnątrz epizodu: 74% na 5m,
71% na 1h, **69% na 4h**). `trend` pozostaje niespójny wszędzie, zgodnie z Z16.

## Blok 3 — próg opłacalności spada z 82,8% do 52,7%

Koszt round-trip `C = 0,0900%` jest **stały per transakcja**, a ATR rośnie z interwałem.
Iloraz B/C poprawia się więc bez żadnych założeń o modelu.

| interwał | reżim | ATR/cena | B = 1,5×ATR | **break-even p** | zmierzone p | luka |
|---|---|---|---|---|---|---|
| 5m | `range` | 0,0914% | 0,1372% | **82,81%** | 50,38% | **−32,4 pp** |
| 5m | `trend` | 0,2738% | 0,4107% | 60,96% | 50,84% | −10,1 pp |
| 1h | `range` | 0,4430% | 0,6645% | **56,77%** | niezmierzone | — |
| 1h | `trend` | 0,8711% | 1,3067% | 53,44% | niezmierzone | — |
| **4h** | **`range`** | 1,0942% | 1,6414% | **52,74%** | niezmierzone | — |
| **4h** | **`trend`** | 1,4247% | 2,1371% | **52,11%** | niezmierzone | — |

**To jest pierwszy raz w całym projekcie, gdy wymaganie wobec `p` schodzi w okolice
realistyczne** (~52–53% zamiast 60–83%).

**Uwaga na rozjazd z wcześniejszymi liczbami:** w C2.11–C2.18 raportowałem break-even
~66,7% dla `range` na 5m, a tu wychodzi 82,81%. Obie liczby są poprawne, ale liczone na
innej populacji: tam z **realizowanych** transakcji (przefiltrowanych przez bramkę kosztową
`min_barrier_to_cost_ratio = 2.0`, która przepuszcza tylko świece o szerszej barierze),
tu z **mediany całego reżimu**. Bramka kosztowa podnosi więc efektywne B o ~48% — i to jest
jej zamierzone działanie.

## Co na plus (+)

- **Pytanie Z9 rozstrzygnięte i z niespodzianką.** Spodziewałem się, że resample jest
  wierny; dla cen jest, dla wolumenu **nie** — a wolumen jest cechą modelu. To realne
  ustalenie o jakości danych w C2.6, którego nie dałoby się zobaczyć bez natywnych świec.
- **Dane odłożone raz na zawsze.** `data/raw/` zawiera teraz komplet trzech interwałów,
  cache jest kluczowany po (symbol, interwał, zakres), a `py -m data.fetch_ohlcv` raportuje,
  co wziął z cache, a co pobrał. Kolejne uruchomienia nie dotykają sieci.
- **Zidentyfikowana pierwsza konfiguracja, w której arytmetyka domyka się realistycznie:**
  4h + `V = 3` + reżim `range` daje jednocześnie spójność (mediana epizodu 4 ≥ 3, 69% świec
  z pełnym oknem) i próg opłacalności **52,74%**.
- Mechanizm jest czysty: koszt stały, ATR rośnie z interwałem. Nie zakłada niczego o modelu
  i nie kosztuje budżetu multiple-testing.

## Co na minus (−)

- **Próg 52,74% to nadal więcej, niż kiedykolwiek zmierzyliśmy** (50,38% na 5m). Luka ~2,4 pp
  jest mała w porównaniu z dotychczasowymi 10–32 pp, ale realna — i nie ma żadnej przesłanki,
  że `p` na 4h będzie takie samo jak na 5m. C2.6 mierzył ~49% (1h) i ~41% (4h), choć na
  danych z zepsutym wolumenem i z nieproporcjonalnym horyzontem.
- **Próba na 4h jest mała.** 6 576 świec, z czego `range` to ~26%, czyli ~1 700 świec.
  Przy oknach walk-forward 60/14/14 dni to garść foldów. Nawet jeśli `p` wyjdzie powyżej
  progu, moc statystyczna może nie wystarczyć do rozstrzygnięcia — to trzeba policzyć
  PRZED uruchomieniem, nie po.
- Blok 3 porównuje próg z `p` zmierzonym na 5m, bo `p` na 1h/4h **nie jest zmierzone**.
  Tabela celowo pokazuje „niezmierzone" zamiast ekstrapolacji.
- `V = 3` przy 4h to horyzont 12h — trzeba sprawdzić, czy `embargo_candles` i warmup
  wskaźników (`atr_pctrank_20d` na 20 dniach = 120 świec 4h) nie zjedzą zbyt wiele próby.
- Wolumen: nie sprawdziłem, **która** wersja jest poprawna (natywna czy zagregowana) —
  zakładam natywną jako pochodzącą wprost z giełdy, ale to założenie, nie dowód.

## Wniosek

Dwa niezależne ustalenia:

1. **Resample z 5m psuje wolumen** (11% świec 1h, 6% świec 4h, błędy do setek procent),
   a wolumen jest cechą obu modeli. Każdy przyszły eksperyment na grubszych świecach musi
   iść na natywnych — i dane do tego są już pobrane i odłożone.
2. **Grubszy interwał to jedyny zmierzony mechanizm, który obniża wymaganie wobec `p` nie
   dotykając `p`.** Próg opłacalności w `range` spada 82,81% (5m) → 56,77% (1h) → **52,74%
   (4h)**. W połączeniu z `V = 3` (jedyny horyzont, przy którym `range` jest spójny) daje to
   pierwszą w projekcie konfigurację, w której wymaganie jest realistyczne.

## Rekomendacja

Następny krok to pre-rejestrowany pomiar `p` w konfiguracji **4h / `V = 3` / reżim `range`**
na natywnych świecach. To **nowa hipoteza**, nie wariant obecnej (zmienia interwał, horyzont
i porzuca dwureżimowość), więc własna pre-rejestracja, własny licznik wariantów i własna
reguła STOP.

**Przed uruchomieniem trzeba policzyć moc statystyczną** — przy ~1 700 świecach `range` na 4h
trzeba wiedzieć, czy pomiar w ogóle rozstrzygnie różnicę między `p = 50%` a `p = 52,7%`.
Jeśli nie, uczciwiej jest tego nie uruchamiać niż dostać nierozstrzygalny wynik i traktować
go jako przesłankę. To rachunek na 0 budżetu i powinien poprzedzić eksperyment.

## Pełny surowy output

```
[data] 5m: 315648 świec 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] 1h: 26304 świec 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:00:00+00:00
[data] 4h: 6576 świec 2023-07-01 00:00:00+00:00 -> 2026-06-30 20:00:00+00:00

================================================================================================
BLOK 1 (Z9) — natywne świece vs agregacja z 5m: czy resample zniekształca?
================================================================================================

-- 1h -- natywnych=26304, z resample=26304, wspólnych=26304
   open    identycznych=100.00%  maks |błąd wzgl.|=0.000000%  mediana=0.00000000%
   high    identycznych=100.00%  maks |błąd wzgl.|=0.015194%  mediana=0.00000000%
   low     identycznych=100.00%  maks |błąd wzgl.|=0.176429%  mediana=0.00000000%
   close   identycznych= 99.99%  maks |błąd wzgl.|=0.176978%  mediana=0.00000000%
   volume  identycznych= 89.02%  maks |błąd wzgl.|=283.790682%  mediana=0.00000000%

-- 4h -- natywnych=6576, z resample=6576, wspólnych=6576
   open    identycznych= 99.98%  maks |błąd wzgl.|=0.063460%  mediana=0.00000000%
   high    identycznych=100.00%  maks |błąd wzgl.|=0.000000%  mediana=0.00000000%
   low     identycznych= 99.98%  maks |błąd wzgl.|=0.131404%  mediana=0.00000000%
   close   identycznych= 99.98%  maks |błąd wzgl.|=0.069507%  mediana=0.00000000%
   volume  identycznych= 93.95%  maks |błąd wzgl.|=23.133784%  mediana=0.00000000%

================================================================================================
BLOK 2 — czy grubszy interwał naprawia spójność bramki z horyzontem?
================================================================================================

-- 5m -- świec z cechami: 309875
   trend  epizodów=  728  mediana=  2.0 świec (     10 min)  udział= 0.53%
   range  epizodów= 9717  mediana=  5.0 świec (     25 min)  udział=21.62%
regime  horizon_candles  median_length  n_windows_inside  share_windows_inside  coherent
 trend                3            2.0               538              0.328851     False
 trend               12            2.0                 8              0.004890     False
 trend               48            2.0                 0              0.000000     False
 range                3            5.0             49573              0.739940      True
 range               12            5.0             14123              0.210804     False
 range               48            5.0               105              0.001567     False

-- 1h -- świec z cechami: 25811
   trend  epizodów=   45  mediana=  1.0 świec (     60 min)  udział= 0.37%
   range  epizodów=  980  mediana=  4.0 świec (    240 min)  udział=23.41%
regime  horizon_candles  median_length  n_windows_inside  share_windows_inside  coherent
 trend                3            1.0                29              0.302083     False
 trend               12            1.0                 0              0.000000     False
 trend               48            1.0                 0              0.000000     False
 range                3            4.0              4305              0.712512      True
 range               12            4.0              1140              0.188679     False
 range               48            4.0                 8              0.001324     False

-- 4h -- świec z cechami: 6443
   trend  epizodów=   17  mediana=  1.0 świec (    240 min)  udział= 0.43%
   range  epizodów=  297  mediana=  4.0 świec (    960 min)  udział=25.98%
regime  horizon_candles  median_length  n_windows_inside  share_windows_inside  coherent
 trend                3            1.0                 5              0.178571     False
 trend               12            1.0                 0              0.000000     False
 trend               48            1.0                 0              0.000000     False
 range                3            4.0              1154              0.689367      True
 range               12            4.0               242              0.144564     False
 range               48            4.0                 0              0.000000     False

================================================================================================
BLOK 3 — relacja B/C: jak nisko schodzi PRÓG OPŁACALNOŚCI na grubszym interwale?
================================================================================================
koszt round-trip C = 0.0900% nominału (stały per transakcja, model C2.12)

interwał  reżim      ATR/cena   B=1.5xATR  break-even p  zmierzone p      luka
5m        range       0.0914%     0.1372%        82.81%       50.38%   -32.43pp
5m        trend       0.2738%     0.4107%        60.96%       50.84%   -10.12pp
1h        range       0.4430%     0.6645%        56.77%   niezmierz.         —
1h        trend       0.8711%     1.3067%        53.44%   niezmierz.         —
4h        range       1.0942%     1.6414%        52.74%   niezmierz.         —
4h        trend       1.4247%     2.1371%        52.11%   niezmierz.         —

[interpretacja] Koszt jest STAŁY per transakcja, a ATR rośnie z interwałem, więc
próg opłacalności spada bez żadnych założeń o modelu. To jedyny mechanizm w projekcie,
który obniża wymaganie wobec `p` nie dotykając `p`. UWAGA: niższy próg nie oznacza,
że model go osiągnie — `p` na 1h/4h wymaga osobnego, pre-rejestrowanego pomiaru.
```
