---
name: "clas5-runda"
description: "Procedura rundy badawczej w projekcie CLAS-5 (repo alpha): przed eksperymentem, checkpointem lub analizą na realnych danych — czytanie indeksów runs/, pre-rejestracja, dokumentacja katalogowa."
---

# Runda badawcza CLAS-5

Procedura obowiązuje przy KAŻDEJ rundzie w repo `alpha` (eksperyment, checkpoint, kalibracja,
screening, diagnostyka na realnych danych). Nadrzędne źródło zasad: `CLAUDE.md` (zasady 1–17).

## 0. Synchronizacja (dwa środowiska!)

Na repo pracują sesja chmurowa i lokalna sesja Claude Code. Przed rundą:
- zsynchronizuj świeży stan plików z repo (nie ufaj cache'owi własnej sesji);
- sprawdź mtime plików, które zamierzasz pisać — jeśli na dysku są nowsze niż twoja kopia,
  NAJPIERW zmerguj, nigdy nie nadpisuj;
- jeśli druga sesja aktywnie pracuje (pliki zmieniają się na bieżąco), wstrzymaj zapis
  współdzielonych plików (runs/INDEX, STATUS, README, CLAUDE.md) do zakończenia jej rundy.

## 1. Przeczytaj przebyte runy (CLAUDE.md zasada 14)

- `runs/INDEX.md`: tabela + liczniki wariantów (per baza danych / per hipoteza) + sekcja
  **"Wnioski skumulowane"**;
- README runów powiązanych z planowaną zmianą.
- Nie powtarzaj wariantu już przetestowanego ani równoważnego (np. `bb_pctb_20` ≡
  `price_zscore_20`). Jeśli powtórka jest uzasadniona — odnotuj jawnie dlaczego.

## 2. Pre-rejestracja PRZED obejrzeniem wyniku

- Zapisz: hipotezę rundy, DOKŁADNIE JEDNĄ zmienną (zasada 4), listę wariantów, kryterium
  sukcesu/porażki, regułę STOP jeśli runda jest częścią programu.
- Dla eksperymentu policz MOC statystyczną (wzorzec Z19: `required_trades`,
  `min_detectable_hit_rate` z `backtest/metrics.py`) — runda bez mocy nie startuje.
- Zmiany wynikające z autonomii (CLAUDE.md, sekcja "Podział ról") dokumentuj z uzasadnieniem
  i ścieżką odwrotu.

## 3. Uruchomienie

- Nowe skrypty budują na `backtest/checkpoint_lib.py`; raport metodologią checkpointu v2:
  fold-jitter (NIGDY seed-sweep — deterministyczny XGBoost), pooled t-stat/t_neff, N_eff,
  rozbicie edge'u `p` / break-even / margines `(2p−1)·B − C` z z_margin.
- Warianty rozstrzygaj na pooled t i marginesie — per-fold `mean_sharpe` NIE jest nośną
  statystyką (C2.12). Kryteria GO/WARUNKOWY/NO-GO z docs/rag/03 pozostają werdyktem bramkowym.
- Dane per interwał: natywne z cache, nie resample z 5m (Z9 — resample psuje wolumen).
- Przechwyć PEŁNY stdout.

## 4. Dokumentacja (CLAUDE.md zasada 11)

Utwórz katalog `runs/YYYY-MM-DD_<id>-<slug>/`:
- `README.md` — ID testu; Metadane (branch/komenda/parametry/dane); **Poprzedzające wyniki**;
  Wynik (tabele); **Co na plus (+) / Co na minus (-)** (uczciwie, z ograniczeniami rundy);
  Wniosek; Rekomendacja;
- `raw_output.txt` — pełny stdout, nieskrócony;
- artefakty (CSV/wykresy) jeśli są.

Następnie: wiersz w tabeli `runs/INDEX.md` + aktualizacja WŁAŚCIWEGO licznika wariantów
(per baza/hipoteza) + aktualizacja "Wnioski skumulowane". Potem synteza (tylko synteza +
link — CLAUDE.md, wytyczna "jedna informacja = jedno miejsce") w `STATUS.md`
(§5/§7 historia rund, §13–§16 zadania/backlog). Jeśli runda zamyka KAMIEŃ MILOWY —
zaktualizuj tabelę "Kamienie milowe"
i sekcję "Status" w `README.md` (CLAUDE.md zasada 15).

## 5. Bramki jakości przed publikacją

Pełna, dopasowana do projektu ściąga (listy kontrolne, pułapki z naszych rund, wzory,
format werdyktów): `docs/skills/bramki-jakosci.md` — czytaj ją w tym kroku. Poniżej skrót.

- **Walidacja write-upu** — wg skilla `data:validate-data`: przelicz ≥ 1 kluczową liczbę
  niezależną drugą drogą; zapytaj "kogo NIE ma w zbiorze" (filtry/bramki — por. C2d, gdzie
  pozorny edge mieszkał w świecach odfiltrowanych); red-flag: wynik idealnie potwierdzający
  hipotezę; spójność sum/mianowników/okresów. Werdykt (Ready / Caveats / Revision) zapisz
  w README rundy.
- **Statystyka** — wg `data:statistical-analysis`: raportuj efekt + CI/half-width, nie samo
  p/z; zakresy zamiast fałszywej precyzji; przy skośnych zwrotach per trade mediana obok
  średniej; pamiętaj o multiple comparisons (licznik wariantów!).
- **Przegląd diffu przed merge** — wg `engineering:code-review` (korektność/edge-case'y/testy/
  czytelność); werdykt jednym zdaniem w README rundy.

## 6. Definition of Done

- Testy: pytest zielony w całości; nowa cecha → test leakage PRZED wejściem do modelu
  (zasada 2); zmiany w labeling/risk_controller → hypothesis property test (zasada 10).
- Lint: ruff + black na plikach dotykanych; skrypty historyczne ZAMROŻONE (zasada 13).
- Raport dla użytkownika: wynik, decyzje podjęte autonomicznie z uzasadnieniem, ścieżka
  revertu, co czeka na jego decyzję (operacje git, decyzje bramkowe faz — po jego stronie).
- **Język raportu i rozmowy — PROSTY (CLAUDE.md zasada 17):** bez żargonu; pojęcie fachowe
  wyjaśnione jednym zdaniem przy pierwszym użyciu; każda kluczowa liczba z tłumaczeniem, co
  z niej wynika dla decyzji. Dotyczy też sekcji Wniosek i Rekomendacja w README rundy.