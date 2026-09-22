---
status: active
last_verified: 2026-08-01
depends_on: [02_cechy_i_leakage.md, 03_ryzyko_i_sizing.md]
---

# 05 — Metodologia wytwarzania oprogramowania i testów

## Dlaczego standardowe TDD nie wystarcza w tym projekcie

Klasyczny TDD (napisz test → zaimplementuj → refaktoryzuj) łapie błędy logiczne, ale **nie łapie
leakage czasowego** — funkcja może przechodzić każdy standardowy unit test i wciąż nielegalnie
zaglądać w przyszłość. Potrzebna dodatkowa kategoria testów, której zwykły TDD nie przewiduje.

Adaptacja stosowana w tym projekcie:
- **"Leakage-test-first" dla cech** — dla każdej nowej funkcji w `feature_miner.py` pisz test
  shift-forward PRZED albo równolegle z implementacją, nie po fakcie.
- **Property-based dla modułów ryzyka** — dla `risk_controller.py`, `labeling.py`: niezmienniki
  matematyczne, nie przykłady.
- **Walk-forward backtest to osobna warstwa** — waliduje HIPOTEZĘ (czy jest edge), nie POPRAWNOŚĆ
  KODU. Zielony backtest nie znaczy "kod bez błędów"; przechodzące testy jednostkowe nie znaczą
  "strategia ma edge". To dwa różne pytania, nie zastępują się nawzajem.

## Piramida testów tego projektu

| Warstwa | Co testuje | Przykład | Kiedy odpalana |
|---|---|---|---|
| 1. Unit tests | Poprawność czystej funkcji na konkretnym wejściu | `test_clean_ohlcv_removes_duplicate_timestamps` | Przy każdej zmianie, CI |
| 2. Leakage tests | Czy funkcja używa tylko danych do t włącznie | `assert_no_lookahead(compute_atr_pctrank_20d, df)` | Przed dopuszczeniem cechy do modelu |
| 3. Property-based (hypothesis) | Niezmienniki matematyczne dla losowych wejść | "position_size nigdy nie przekracza max_leverage × equity, dla dowolnych equity/atr/entry_price > 0" | Przy każdej zmianie `risk_controller.py`/`labeling.py` |
| 4. Integration | Pełny pipeline end-to-end na małej próbce syntetycznej | dane → cechy → regime → model → risk → decyzja, bez błędów i NaN tam gdzie nie powinno | Przed każdym Commitem uznanym za "zrobiony" |
| 5. Walk-forward backtest | Czy hipoteza ma edge po kosztach | Sharpe, drawdown, win rate per fold | Checkpoint go/no-go (Commit 6), nie częściej niż raz na iterację cech |

**Warstwy 1-4 to test poprawności kodu — muszą być zielone zawsze. Warstwa 5 to test hipotezy —
może wyjść na NO-GO i to jest prawidłowy, użyteczny wynik, nie porażka kodu.**

## Property-based testing (hypothesis) — przykład konkretny

Oryginalny PRD wymagał "testów właściwościowych" dla `risk_manager`/`features`. Konkretnie dla
`risk_controller.py` (Commit 5.5), przykładowe właściwości do zakodowania biblioteką `hypothesis`:

```python
from hypothesis import given, strategies as st

@given(
    equity=st.floats(min_value=1, max_value=1e7),
    atr_14=st.floats(min_value=0.01, max_value=1e5),
    entry_price=st.floats(min_value=0.01, max_value=1e6),
)
def test_position_size_never_exceeds_leverage_cap(equity, atr_14, entry_price):
    size = compute_position_size(equity, atr_14, entry_price, risk_per_trade=0.005, max_leverage=3.0)
    max_allowed = (equity * 3.0) / entry_price
    assert size <= max_allowed + 1e-9  # tolerancja float

@given(equity=st.floats(min_value=1, max_value=1e7), atr_14=st.floats(min_value=0.01, max_value=1e5))
def test_position_size_non_negative(equity, atr_14):
    size = compute_position_size(equity, atr_14, entry_price=100.0, risk_per_trade=0.005, max_leverage=3.0)
    assert size >= 0
```

To wychwytuje błędy, których nie znajdziesz przykładami wymyślonymi ręcznie — `hypothesis`
generuje setki losowych kombinacji wejść, w tym przypadki brzegowe (bardzo mały ATR, bardzo duży
equity), których autor testu by nie pomyślał samodzielnie.

## Definicja "zrobione" (Definition of Done) per Commit

Commit z `STATUS.md` nie jest "zrobiony", gdy kod działa raz na dev maszynie. Jest
zrobiony, gdy:

1. Kod ma docstring z wzorem/uzasadnieniem, nie tylko `# TODO: wyjaśnić później`.
2. Testy jednostkowe (Warstwa 1) przechodzą.
3. Jeśli commit dotyczy cechy: formalny test leakage (Warstwa 2) przechodzi —
   `agent_5_compliance/test_leakage.py`, nie tylko nieformalny sanity check w konsoli.
4. Jeśli commit dotyczy `risk_controller.py`/`labeling.py`: co najmniej jedna właściwość
   zakodowana w `hypothesis` (Warstwa 3).
5. Żaden nowy parametr nie jest hardcoded inline w kodzie — trafia do
   `feature_registry.yaml`/`config/settings.yaml`, z komentarzem "wartość startowa, do
   kalibracji" tam, gdzie dotyczy.
6. `docs/rag/` zaktualizowane, jeśli commit zmienia albo doprecyzowuje decyzję architektoniczną
   (nie tylko implementuje coś, co już było ustalone).
7. `STATUS.md` status zaktualizowany (`TODO` → `DONE`, z krótką notatką co
   zweryfikowano empirycznie).

## Konwencje kodu

- **Czyste funkcje wszędzie, gdzie to możliwe** — input jawny (DataFrame/parametry), output
  jawny (Series/dict), bez efektów ubocznych, bez odczytu globalnego stanu. Ułatwia to testy
  Warstw 1-3 i audyt Compliance Gate.
- **Type hints + `from __future__ import annotations`** we wszystkich nowych plikach.
- **Docstring = co liczy + jaki wzór + skąd pochodzi** (biblioteka, artykuł, repo źródłowe) —
  nie tylko opis funkcjonalny.
- **Zero magic numbers poza registry/configiem.** Jeśli liczba pojawia się dwa razy w kodzie
  (np. mnożnik ATR w barierze i w stop-lossie), to sygnał, że powinna być jedną stałą importowaną
  w obu miejscach, nie dwoma osobnymi literałami, które mogą się rozjechać.

## Reprodukowalność

- Random seed jawnie ustawiany i logowany przy każdym treningu modelu — potrzebne do sanity
  checku "stabilność wyniku przy losowym seedzie" z checkpointu Commitu 6 (patrz
  `03_ryzyko_i_sizing.md`).
- Walk-forward split deterministyczny — te same daty graniczne foldów przy powtórnym uruchomieniu
  na tych samych danych.
- `requirements.txt` z minimalnymi wersjami (`>=`), nie dokładnym pinningiem — świadomy
  kompromis: elastyczność vs ryzyko dryfu zależności. Jeśli pojawi się problem z reprodukowalnością
  między maszynami, rozważ przejście na dokładny pinning (`==`) + `pip freeze`.

## Konwencja "Commitu" w tym projekcie

Jeden "Commit" z `STATUS.md` (np. "Commit 4 — Target + walk-forward split") to
jedna logiczna, kompletna jednostka pracy: kod + testy + aktualizacja rejestru/configu +
aktualizacja `docs/rag`, jeśli dotyczy. Nie "commituj", żeby zapisać postęp w połowie — commit
niekompletny wg checklisty wyżej zostaje w gałęzi roboczej, nie w `main`.

## CI/CD — minimalne teraz, świadomie nie więcej

`.github/workflows/tests.yml` — automatyczne odpalanie `pytest` (bare, bez ścieżki — auto-discovery
po całym repo, żeby przyszłe testy z `agent_5_compliance/` były podłapywane bez edycji configu) +
sprawdzenie zgodności `feature_registry.yaml` z `feature_miner.py` na każdym push/PR.

**Dlaczego nie pełny pipeline (staging, deployment, multi-environment) już teraz:** to ten sam
błąd sekwencji co import freqtrade/LEAN jako zależności przed Fazą 3 — budowanie infrastruktury
wdrożeniowej przed potwierdzeniem edge'u. Solo-projekt w Fazie 0 nie ma jeszcze czego wdrażać;
główna wartość CI/CD (ochrona zespołu przed regresją innych osób) jest tu mniej istotna niż w
projekcie wieloosobowym — lokalne odpalanie testów przed commitem już to pokrywa.

**Kiedy rozbudować:** Faza 3 (paper trading) — wtedy "deployment" zaczyna znaczyć coś realnego
(wdrożenie na testnet), i dopiero wtedy CD (nie tylko CI) ma sens dodać.

**Co CI faktycznie łapie, czego test lokalny mógł przeoczyć:** dokładnie to, co znaleźliśmy przy
ręcznej walidacji całego projektu — nieaktualne odniesienia między plikami, niespójność
`feature_registry.yaml` vs kod. Automatyzacja tego konkretnego sprawdzenia (krok w workflow)
zapobiega powtórce tego samego błędu przy kolejnych commitach.
