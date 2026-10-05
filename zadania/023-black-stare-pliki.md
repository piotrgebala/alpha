---
id: 023
tytul: Porządki formatu — `black --check .` czerwony na 15 starych plikach (9 zamrożonych poza `extend-exclude`)
typ: naprawa
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Wykonaj wszystkie 3 punkty” (wpis pozycji backlogu z STATUS.md na tablicę)"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Sonnet albo Opus medium, 1 wykonawca"
---

# 023 — `black --check .` na zielono

## Po co

`py -m black --check .` (komenda z `CLAUDE.md`) jest czerwony na 15 starych plikach, więc nie odróżnia nowych
błędów formatu od starych. Pozycja z backlogu w nagłówku `STATUS.md`.

## Zakres

1. Uruchomić `py -m black --check .` i wypisać pliki z błędem.
2. **Zamrożone** (`runs/ZAMROZONE.txt`, `py tools/frozen_guard.py lista`): nie formatować — dopisać do `extend-exclude`
   w `pyproject.toml` (sekcje black i ruff, tak jak pozostałe zamrożone).
3. **Pliki, z których korzysta dziennik** (lista w `CLAUDE.md`, „Dziennik papierowy”: `backtest/live_journal.py` i jego
   importy, `data/fetch_live.py` i jego importy): **nie formatować** — zmiana tych plików wymaga decyzji użytkownika
   i Poprawki N. Wypisać je w wyniku jako osobną pozycję do decyzji.
4. Pozostałe: `black` bez żadnej zmiany logiki; osobny commit „tylko format”.

## Czego NIE robić

- Nie edytować zamrożonych skryptów (hook `tools/frozen_guard.py` i tak odmówi).
- Nie łączyć formatowania ze zmianami treści.

## Kryteria odbioru (dowody)

- `py -m black --check .` i `py -m ruff check .` zielone (albo lista plików z punktu 3 jako jedyny wyjątek).
- `py -m pytest -q` zielony, ta sama liczba testów co przed zmianą.
- `git diff --stat` commitu formatu; `git diff -w` bez zmian logiki (przegląd 16c jednym zdaniem).

## Wynik

- **Zrobione 2026-09-29.** Gałąź `zadanie-023-black-stare-pliki` (`9eafcf1` exclude, `c39c1f6` tylko format,
  `a7aa724` rejestr skilli), scalona do master (`41746b8`).
- **Wynik:** z 15 plików: 9 zamrożonych (`backtest/`: calibrate_regime_thresholds, checkpoint_timeframe_robustness,
  diagnose_cost_feasibility, diagnose_range_signal, evaluate_confidence_threshold, evaluate_feature_candidate,
  run_funding_measured_f1, run_momentum_m1, screen_feature_candidates) dopisanych do `extend-exclude` (black i ruff);
  5 sformatowanych (`agents/regime_coherence.py`, 4 pliki `tests/`); 1 w łańcuchu dziennika — **`data/fetch_ohlcv.py`
  do decyzji użytkownika** (black usunąłby 1 pustą linię i zawinął 1 `print`; AST równe; wymaga Poprawki N).
- **Dowody (sprawdził orkiestrator):** AST 5 plików master wobec gałęzi równe (własne porównanie `ast.dump`); diff
  7 plików; na master po scaleniu `ruff check .` zielony, `black --check .` zgłasza wyłącznie `data/fetch_ohlcv.py`;
  pełny pytest: 1 946 passed, 2 skipped, kod 0 (liczba testów bez zmian wobec gałęzi przed formatem wg wykonawcy: 1 927 → 1 927).
- **Zostało:** (1) decyzja o `data/fetch_ohlcv.py`; (2) wykonawca ustalił programem (`sys.modules` po imporcie
  `backtest.live_journal` i `data.fetch_live`), że łańcuch dziennika to 25 plików projektu, szerzej niż lista
  w `CLAUDE.md` — poza nią m.in. `agents/{feature_miner,labeling,ml_optimizer,risk_controller}.py`,
  `backtest/{engine,execution,metrics,costs}.py`, `data/fetch_external.py` (statycznie); kandydat na test-strażnika
  łańcucha. (3) Pozostałe ~70 zamrożonych skryptów nie jest w `extend-exclude` (dziś przechodzą black).
