# C2.9 — naprawa metodologii pomiaru: fold-jitter, t-stat, N_eff, pooled Sharpe (2026-09-21)

## ID testu

**C2.9** — patrz `runs/INDEX.md` dla pełnego spisu.

## Metadane

- **Branch:** `task/C2.9-measurement-methodology` (do utworzenia)
- **Poprzedzający stan (master):** Commit 2.8 + backlog Z1–Z15 (TASKS.md, przegląd całego
  projektu 2026-09-21). Ta runda realizuje **Z1+Z2+Z3+Z4+Z13** oraz higienę **Z11+Z12+Z14+Z15**.
- **Komenda:** `python3 -m backtest.run_checkpoint_v2` (pełny, z sweepem fold-jitter)
- **Nowe pliki:** `backtest/checkpoint_lib.py` (Z13, wspólna biblioteka — FORWARD-LOOKING,
  historyczne skrypty NIE refaktoryzowane wstecz), `backtest/run_checkpoint_v2.py`
  (kanoniczny checkpoint v2; `run_checkpoint.py` zostaje zamrożony jako zapis Commitu 6)
- **Zmiany:** `agents/labeling.py` (`start_offset_days` w `generate_walk_forward_folds` +
  hypothesis property test — DoD Warstwa 3), `backtest/engine.py` (`fold_start_offset_days`,
  `candle_minutes` — Z11), `backtest/metrics.py` (`compute_t_stat`, kolumna `t_stat`,
  `summarize_pooled_by_regime` z N_eff — Z2+Z3), `agent_5_compliance/test_leakage.py`
  (test spójności registry↔kod czyta YAML — Z15), `docs/rag/03` (aktualizacja sekcji
  stabilności), `README.md` (Z14), lint (Z12). Pełny zestaw testów: **139/139 przechodzi**
  (128 + 11).
- **Źródło danych:** `data/raw/BTC-USDT-USDT_5m_20250701T000000Z_20260701T000000Z.parquet`
  (105 120 świec 5m, bez dziur)
- **Parametry stałe:** CAŁY pipeline niezmieniony (progi 0.7/0.3, ATR_MULTIPLIER=1.5, bramka
  kosztowa 2.0, MOMENTUM_FEATURES bez `adx_14` — decyzja C2.8 utrzymana, seed=42)
- **Zmienna "eksperymentu":** wyłącznie METODOLOGIA POMIARU — offset startu okien
  walk-forward 0–9 dni (perturbacja arbitralnego wyrównania foldów, nie hipotezy)

## Dlaczego ta runda w ogóle powstała

Audyt projektu (2026-09-21, TASKS.md Backlog) wykazał, że **sweep stabilności po seedach
(C6.3) mierzył dokładnie nic**: `DEFAULT_XGB_PARAMS` nie zawiera `subsample`/
`colsample_bytree`, więc XGBoost jest w pełni deterministyczny — seed nie zmienia ani
jednego drzewa. Empirycznie: std=0,0000 identyczne do ostatniej cyfry w KAŻDYM
eksperymencie od Commitu 6 (C6, 2c, 2d, C2.5×4, C2.6×2, C2.8×2 — ~10 niezależnych
potwierdzeń "stabilności", z których żadne nie niosło informacji). Dodatkowo annualizowany
Sharpe per fold (sqrt(~800 transakcji/rok) przy n=31–37 na fold) produkował wartości rzędu
-22/-65 — arytmetycznie poprawne, statystycznie bezsensowne; a policzalna od C4.4 funkcja
`effective_sample_size` nigdy nie była wpięta do żadnego raportu.

## Wynik — kanoniczny przebieg (offset=0, identyczny z baseline C2.5/C2.8)

Klasyfikacja NIEZMIENIONA (kryteria docs/rag/03): **NO-GO**, mean_sharpe=-14,3078, 6/40
ważnych foldów — zgodne co do ostatniej cyfry z C2.5/C2.8 (offset=0 = dokładnie stary
przebieg; pełna porównywalność historyczna zachowana).

**NOWE — diagnostyka pooled per reżim (Z2+Z3), po raz pierwszy policzalna:**

| regime | n_trades | mean_return/trade | sharpe_per_trade | t_stat | N_eff | t_stat_neff |
|---|---|---|---|---|---|---|
| range | 223 | -0,001082 | -0,479 | **-7,15** | NaN* | NaN* |
| trend | 135 | -0,000625 | -0,251 | **-2,91** | 109,8 | **-2,63** |

\* estymator N_eff dla `range` zdegenerowany (suma autokorelacji ≤ -0,5) — raportowane
uczciwie jako NaN zamiast liczby udającej informację.

**Interpretacja:** średni zwrot per trade jest **istotnie UJEMNY w obu reżimach** (|t| ≫ 2,
w `trend` również po konserwatywnej korekcie N_eff). To mocniejsze stwierdzenie niż samo
"NO-GO wg kryteriów foldowych": system nie jest "nieodróżnialny od zera" — on **istotnie
traci** na poziomie per-trade, przy obecnych kosztach i cechach.

## Wynik — sweep fold-jitter (Z1, zamiennik pustego sweepu seedów)

| offset [dni] | mean_sharpe | klasyfikacja | n_valid_folds |
|---|---|---|---|
| 0 | -14,31 | NO-GO | 6/40 |
| 1 | -13,81 | NO-GO | 7/39 |
| 2 | -13,02 | NO-GO | 7/39 |
| 3 | -15,89 | NO-GO | 7/39 |
| 4 | -12,33 | NO-GO | 9/38 |
| 5 | -12,60 | NO-GO | 9/38 |
| 6 | -15,89 | NO-GO | 8/38 |
| 7 | -14,36 | NO-GO | 8/38 |
| 8 | -8,65 | NO-GO | 8/38 |
| 9 | -6,20 | NO-GO | 9/38 |

**std(mean_sharpe) = 3,09; zakres [-15,89; -6,20]; spójność znaku (ujemny) = 100%;
klasyfikacja NO-GO w 10/10 offsetów.** Celowo bez progu pass/fail (stary std<0,2 dotyczył
pustego szumu seedów) — raportowany rozkład, interpretacja przy użytkowniku.

## Co na plus (+)

- **NO-GO po raz pierwszy potwierdzone REALNĄ perturbacją:** 10/10 offsetów daje NO-GO i
  ujemny mean_sharpe — werdykt nie jest artefaktem arbitralnego wyrównania granic foldów.
  Dotychczasowe "std=0,0000 (STABILNY)" nie mówiło nic; "100% ujemnych przy realnym
  jitterze podziału danych" mówi dużo.
- **Pooled t-stat daje nową, twardą informację:** strata per trade jest statystycznie
  istotna w OBU reżimach (range t=-7,15; trend t=-2,91, po korekcie N_eff -2,63). To
  zamyka wątpliwość "może NO-GO to tylko szum małych foldów".
- **Skala szumu wyrównania foldów jest teraz ZMIERZONA (std≈3,1)** — i retrospektywnie
  kalibruje interpretację poprzednich rund: "poprawa" z C2.8 (+0,61 mean_sharpe po dodaniu
  `adx_14`) to **~0,2 odchylenia szumu fold-jitter** — kolejny, niezależny argument za
  ostrożnością wobec tamtego wyniku (spójny z rekomendacją C2.8, żeby NIE promować cechy).
- **Porównywalność historyczna zachowana:** offset=0 odtwarza -14,3078 co do ostatniej
  cyfry; kryteria klasyfikacji GO/WARUNKOWY/NO-GO nietknięte.
- Higiena domknięta w tej samej rundzie: Z11 (funding liczony z realnego czasu trzymania —
  `candle_minutes` przewleczone przez pipeline z testem integracyjnym), Z12 (lint 0 błędów),
  Z14 (README zaktualizowane), Z15 (test spójności registry↔kod czyta YAML zamiast
  hardkodować listę).

## Co na minus (-)

- **Wynik hipotezy pozostaje NO-GO** — ta runda naprawiała miarkę, nie strategię; lepsza
  miarka pokazała problem jeszcze ostrzej (istotnie ujemny zwrot per trade), nie łagodniej.
- **Rozrzut mean_sharpe po offsetach jest DUŻY (od -6,2 do -15,9)** — pojedyncza liczba
  mean_sharpe z jednego przebiegu (raportowana we wszystkich rundach C6→C2.8) ma niepewność
  rzędu ±3 (1σ) z samego wyrównania foldów. Porównania między wariantami różniące się o
  <~3 jednostki (jak C2.8) nie są rozstrzygalne tą metodą na tych danych — to wzmacnia
  argument Z5 (wydłużenie historii danych).
- **Estymator N_eff degeneruje się dla `range`** (ujemna suma autokorelacji ≤ -0,5) —
  uczciwie raportowane jako NaN, ale oznacza, że dla tego reżimu korekta autokorelacyjna
  jest niedostępna obecną metodą (kandydat na lepszy estymator, np. Newey-West, jeśli
  kiedykolwiek będzie potrzebny do decyzji).
- **Sweep nie jest darmowy:** 10 pełnych przebiegów pipeline'u (~40 s na tych danych) —
  akceptowalne, ale przy dłuższej historii (Z5) trzeba będzie to uwzględnić w czasie rund.
- Stary `run_checkpoint.py` zostaje w repo jako zamrożony zapis Commitu 6 — dwie wersje
  checkpointu obok siebie to świadomy koszt zachowania odtwarzalności historycznych rund.

## Wniosek

Metodologia pomiaru jest naprawiona: stabilność mierzy teraz realną perturbację (i werdykt
NO-GO ją przechodzi w 10/10), istotność jest raportowana uczciwie (t-stat bez annualizacji,
N_eff z korektą autokorelacji), a pooled diagnostyka dostarcza najtwardszego dotąd
sformułowania stanu hipotezy: **średni zwrot per trade jest istotnie ujemny w obu
reżimach**. Zmierzona skala szumu fold-jitter (σ≈3,1 mean_sharpe) retrospektywnie osłabia
jedyny "pozytywny" sygnał serii (C2.8, +0,61). Kontekst decyzji strategicznej Z10 jest
teraz kompletny.

## Rekomendacja (nie decyzja)

1. Wszystkie przyszłe rundy raportują przez `run_checkpoint_v2`/`checkpoint_lib` (offset=0
   + sweep + pooled) — koniec z cytowaniem pustego "std=0,0000".
2. Porównania wariantów o różnicy mean_sharpe < ~3 traktować jako nierozstrzygalne na
   rocznych danych 5m → **Z5 (3–5 lat historii) jest teraz najważniejszym odblokowaniem**
   dalszej pracy hipotezowej (fetch na Twojej maszynie).
3. Decyzja Z10 (rewizja hipotezy vs domknięcie Fazy 0) — przy użytkowniku; nowe pooled
   t-staty są najlepszym dotąd materiałem do tej decyzji.

## Pełny surowy output

```
[data] 105120 świec: 2025-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.

=== Klasyfikacja (kryteria docs/rag/03, NIEZMIENIONE) ===
{'classification': 'NO-GO', 'n_valid_folds': 6, 'n_total_folds': 40, 'fraction_above_threshold': 0.16666666666666666, 'fraction_le_zero': 0.8333333333333334, 'fraction_positive_sign': 0.16666666666666666, 'mean_sharpe': -14.3077642884818}

=== Rozbicie per reżim ===
regime classification  n_valid_folds  n_total_folds  fraction_above_threshold  fraction_le_zero  fraction_positive_sign  mean_sharpe
 range          NO-GO              2             20                      0.00              1.00                    0.00   -26.011196
 trend          NO-GO              4             20                      0.25              0.75                    0.25    -8.456048

=== Diagnostyka pooled per reżim (Commit 2.9/Z2+Z3) ===
regime  n_trades  mean_return  std_return  sharpe_per_trade    t_stat      n_eff  t_stat_neff
 range       223    -0.001082    0.002261         -0.478581 -7.146738        NaN          NaN
 trend       135    -0.000625    0.002491         -0.250750 -2.913452 109.790346    -2.627381

=== Stabilność fold-jitter (Commit 2.9/Z1 — zamiast pustego sweepu seedów) ===
 offset_days  mean_sharpe classification  n_valid_folds  n_total_folds
         0.0   -14.307764          NO-GO              6             40
         1.0   -13.812747          NO-GO              7             39
         2.0   -13.021264          NO-GO              7             39
         3.0   -15.892089          NO-GO              7             39
         4.0   -12.332791          NO-GO              9             38
         5.0   -12.600317          NO-GO              9             38
         6.0   -15.890071          NO-GO              8             38
         7.0   -14.363842          NO-GO              8             38
         8.0    -8.650515          NO-GO              8             38
         9.0    -6.202294          NO-GO              9             38

std(mean_sharpe) po 10 offsetach = 3.0880; zakres = [-15.8921, -6.2023]; spójność znaku (ujemny) = 100%
```

(Pełny per-fold Sharpe+t_stat kanonicznego przebiegu — deterministyczny, odtwarzalny komendą
z sekcji "Metadane"; skrócony tu do klasyfikacji + diagnostyki, zgodnie z konwencją.)
