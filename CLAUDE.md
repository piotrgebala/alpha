# CLAS-5 — Instrukcje projektowe (Claude Code)

## Projekt

Badania nad strategiami na perpetualach Binance (BTC i koszyk top-20). Cel: minimalny, audytowalny
system; o realnym kapitale decyduje **drabina dowodów** (`docs/rag/09_drabina_dowodow.md`, decyzja
użytkownika 2026-09-24) — mechanizm poza naszymi danymi, spójność w wycinkach, dziennik papierowy,
potem mała kwota; sposób mierzenia (zasady 1–20) bez zmian. Ten plik
mówi, CO obowiązuje. **DLACZEGO** (uzasadnienia, historia, przykłady z rund) —
`docs/rag/08_zasady_pelne_brzmienie.md`; numeracja zasad jest tam ta sama.
Stan prac, decyzje, ryzyka → `STATUS.md`; wyniki rund → `runs/INDEX.md` (na górze „Stan wiedzy —
skrót”). Tych plików nie kopiuj tutaj — zmieniają się często. Preferencje użytkownika (sposób
handlu, cel zwrotów, rynek przed 2022) → `docs/rag/10_preferencje_uzytkownika.md`.

## Nienaruszalne zasady

1. **Nigdy nie optymalizuj parametrów** (okna, progi, hiperparametry) na całym zbiorze naraz —
   tylko wewnątrz walk-forward (`docs/rag/03`).
2. **Każda nowa cecha dostaje test leakage PRZED wejściem do modelu** (`docs/rag/02`).
3. **Target (triple-barrier) i stop-loss używają TEGO SAMEGO mnożnika ATR (1,5×)** —
   `ATR_MULTIPLIER` mieszka w `labeling.py`, `risk_controller.py` go importuje.
4. **Feature set rozszerza się o jedną cechę na raz, mierzoną na OOS.** Nigdy grid search po
   kombinacjach (multiple testing, `docs/rag/02`).
5. **Sufit dźwigni wygrywa nad fixed-fractional sizing** — jawne `min()`.
6. **LLM nigdy w ścieżce decyzji handlowych** — tylko offline/nadzorczo (`docs/rag/01`).
7. **Bramka reżimu i sizing zostają regułami (nie ML), dopóki minimalny system nie udowodni
   przewagi.**
8. **freqtrade / LEAN / QuantConnect = katalog wzorców, nie zależność runtime** (`docs/rag/04`).
9. **Inne instrumenty = test generalizacji tej samej hipotezy** (te same progi, bez retuningu),
   nie równoległe strojenie kilku strategii.
10. **Commit nie jest „zrobiony” bez testów jednostkowych + (jeśli dotyczy) testu leakage +
    (jeśli dotyczy) testu właściwości w `hypothesis`** (DoD: `docs/rag/05`).
11. **Każdy ciężki przebieg dostaje WŁASNY KATALOG `runs/YYYY-MM-DD_<id>-<slug>/`**:
    `README.md` (ID, Metadane, **Poprzedzające wyniki**, Pre-rejestracja, Wynik, „Co na plus (+) /
    Co na minus (−)”, Wniosek, Rekomendacja, **Użyte skille**) + `raw_output.txt` (pełny stdout) +
    artefakty; do tego wiersz w `runs/INDEX.md` z licznikiem wariantów i aktualizacja „Wniosków
    skumulowanych” (procedura: `runs/INDEX.md` → „Jak dodać nowy wpis”). Pilnuje
    `tests/test_runs_index_guard.py`.
12. **Wyniki raportuje się metodologią checkpointu v2** (`backtest/checkpoint_lib.py`: fold-jitter,
    t / t_neff, N_eff ≤ n, rozbicie przewagi: trafność `p`, próg, margines). Dwa „marginesy”:
    `margin` = trafność − próg (punkty trafności), `(2p−1)·B − C` = jednostki zwrotu — zawsze
    podaj, o który chodzi. **Nie cytuj „stabilności na 10 seedach”** (XGBoost jest deterministyczny).
13. **Skrypty zakończonych rund są ZAMROŻONE** (`runs/ZAMROZONE.txt`; hook `tools/frozen_guard.py`
    odmawia edycji; `tests/test_frozen_guard.py` sprawdza, że każdy skrypt z komendy README jest
    na liście). Nowe skrypty budują na `checkpoint_lib.py`. Zdjęcie z listy = decyzja z powodem
    w `STATUS.md`.
14. **PRZED każdą rundą przeczytaj `runs/INDEX.md`** (skrót stanu wiedzy, tabela, wnioski) **i
    README powiązanych rund**; sekcja „Poprzedzające wyniki” mówi, na czym runda buduje. Nie
    powtarzaj wariantu już przetestowanego ani równoważnego bez jawnego uzasadnienia.
15. **Kamień milowy aktualizuje `README.md`** (tabela „Kamienie milowe” + sekcja „Status”) —
    tak samo obowiązkowo jak wpis w `runs/INDEX.md`.
16. **Bramki jakości rundy** — procedura: `docs/skills/bramki-jakosci.md` (bez zależności od
    wtyczek): (a) przed publikacją write-upu — przeliczenie ≥ 1 kluczowej liczby drugą drogą,
    pytanie „kogo NIE ma w zbiorze”, czerwona flaga „wynik idealnie potwierdza hipotezę”, przy
    nowym silniku kontrola negatywna (A6); werdykt **Ready / Caveats / Revision** w README;
    (b) statystyka — efekt + przedział, zakresy, mediana obok średniej, zawsze z licznikiem
    wariantów; (c) przed merge — przegląd diffu z werdyktem jednym zdaniem w README.
17. **Rozmowa i raporty prostym językiem.** Krótkie zdania, bez skrótów myślowych; pojęcie
    fachowe wyjaśnione w nawiasie przy pierwszym użyciu; każda kluczowa liczba z tłumaczeniem,
    co z niej wynika dla decyzji. Precyzja techniczna zostaje w sekcjach technicznych.
18. **Rachunek MIERZALNOŚCI przed uruchomieniem.** Pre-rejestracja podaje
    `backtest/metrics.py::measurability_report(zakładana_trafność, próg, oczekiwane_n)`, a
    `oczekiwane_n` liczy się przez `expected_trades(n_świec, abstynencja, admission_rate)` (dla
    reguły bez modelu — z częstości zdarzenia; dla portfela dziennego — z rozrzutu szeregu).
    **NIEMIERZALNA = runda nie startuje.** Bez zamrożonych progów typu „≥ 58 %” — właściwością
    przyrządu jest `wald_half_width(n)`. Kryterium sprawdź też w granicy dużego `n` (czy nie
    karze celu rundy).
19. **Skille są OBOWIĄZKOWE w wyznaczonych momentach; ślad prowadzi program.** Skill wczytuje
    się PRZED pracą, na gałęzi rundy (rejestr przypisuje użycia do gałęzi):

    | moment pracy | skill |
    |---|---|
    | cechy, wskaźniki, etykiety, backtest, walk-forward, trening, hiperparametry, ryzyko/sizing, mierzalność, werdykt, nowe źródło danych, diagnoza „czemu nie działa” | `clas5-quant` |
    | start rundy na realnych danych — po utworzeniu gałęzi rundy | `clas5-runda` |
    | nowa hipoteza lub strategia, „co jeszcze przetestować”, pomysł z biblioteki strategii | `quant-strategy-catalog` |
    | analiza techniczna: formacja, świeca, wskaźnik, wsparcie/opór, Fibonacci, TradingView/Pine | `ta-toolkit` |
    | LEAN / QuantConnect | `lean-research` |
    | przed publikacją write-upu rundy (bramka 16a) | `data:validate-data` |
    | liczby i przedziały w raporcie (bramka 16b) | `data:statistical-analysis` |
    | przed scaleniem do master (bramka 16c) | `engineering:code-review` |
    | wykres | `dataviz` |
    | decyzja architektoniczna (ADR do `docs/rag/`) | `engineering:architecture` |
    | błąd, którego przyczyny nie widać od razu | `engineering:debug` |
    | testy nowego modułu | `engineering:testing-strategy` |
    | konfiguracja Claude Code (hooki, uprawnienia, `settings.json`) | `update-config` |
    | nowa wersja skilla projektu + paczka do wgrania na claude.ai | `anthropic-skills:skill-creator` |
    | plik Word / Excel / PowerPoint / PDF | `anthropic-skills:docx` / `anthropic-skills:xlsx` / `anthropic-skills:pptx` / `anthropic-skills:pdf` |
    | nowy zbiór danych: dziury, duplikaty, dziwne wartości (obok `clas5-quant`) | `data:explore-data` |
    | wykonanie sygnałów dziennika na realnych pieniądzach (szczebel 4 ADR-09): lista zleceń, kontrole konta, dziennik wykonania | `anthropic-skills:zarzadzanie-pozycja` (sekcja E, tryb systemowy) |
    | kod z kluczami API, zleceniami albo nowym połączeniem sieciowym | `security-review` (wbudowany; jednorazowo w tym momencie, nie przy każdym commicie) |
    | pytanie, jakie automatyzacje Claude Code dodać | `claude-code-setup:claude-automation-recommender` (tylko czyta; nowe skille i tak trafiają do chmury, nie do repo) |

    Przegląd kodu = `engineering:code-review` (wbudowany `/code-review` to droższy dodatek, nie
    zamiennik); wykres = `dataviz`. **Rejestr:** hook uruchamia `tools/skill_audit.py`, który
    dopisuje każde wczytanie do `runs/skille/<gałąź>.jsonl` (plików nie edytuje się ręcznie;
    commituje się je z pracą gałęzi) i do lokalnego monitora `runs/skille/uzycie_skilli.csv`.
    **README rundy — sekcja „Użyte skille”:** wynik `py tools/skill_audit.py raport --galaz
    <gałąź>` + jedno zdanie, co wniósł każdy skill + skille z tabeli, których moment runda
    obejmowała, a których nie ma w rejestrze — z powodem. Skill niedostępny w sesji → „niedostępny
    w sesji” i procedura z repo (`docs/skills/bramki-jakosci.md`, zasady 11–19).
20. **Testy na realnych danych używają WYŁĄCZNIE danych od 2021-01-01** (decyzja użytkownika
    2026-09-23). Filtr mieszka w jednym miejscu: `config/settings.yaml` (`data.min_start`),
    nakładany przez `backtest/checkpoint_lib.py::fetch_window`. Starsze świece zostają tylko dla
    odtwarzalności zamrożonych rund; wyników sprzed W2 nie porównuje się 1:1 z nowymi.

## Wytyczne (miękkie — do rewizji, gdy zmienią się dane)

- **Kryterium POZYTYWNE ma DWA warunki:** `t_neff > 1,96` zwrotu netto ORAZ (przy regułach
  z trafnością) `ci_low(p) > p*` — trafność nad progiem przy ujemnym zwrocie to iluzja geometrii
  wypłaty (`bramki-jakosci.md` B3). Per-fold `mean_sharpe` nie jest statystyką porównań.
- **Liczniki wariantów rozwidlają się per baza danych i per hipoteza** (`runs/INDEX.md`);
  wyników między bazami nie porównuje się 1:1.
- **Jedna informacja w JEDNYM miejscu:** `runs/<katalog>/` = pełne wyniki; `runs/INDEX.md` =
  skrót stanu wiedzy, tabela, wnioski, liczniki; `STATUS.md` = decyzje, ryzyka, zadania,
  backlog (wpisy krótkie + link); `README.md` = widok dla człowieka + kamienie milowe.
- **Skille projektu mieszkają w chmurze konta, nie w repo** (`clas5-runda`, `clas5-quant`,
  `quant-strategy-catalog`, `ta-toolkit`, `lean-research`; lokalnie jako `anthropic-skills:<nazwa>`).
  `.claude/skills/` zostaje puste; `~/.claude/skills/synced/` to tylko pamięć podręczna. Zmiana
  skilla = nowa wersja przygotowana przez Claude + wgranie przez użytkownika na claude.ai;
  jednozdaniowa notka w `STATUS.md`. Skille konta bez związku z projektem ukrywa `skillOverrides`.
- **Wtyczki włącza się w `.claude/settings.json` projektu** (ze źródłem w `extraKnownMarketplaces`,
  pilnuje `tests/test_project_settings.py`): z chmury konta `engineering`, `data`; z GitHuba
  `security-guidance` (tylko warstwa wzorców — ostrzeżenie przy edycji traktuj jak uwagę
  z przeglądu kodu), `claude-code-setup` (jego rada o `.claude/skills/` u nas nie obowiązuje),
  `discernment-nudge` (pytania kontrolne po polsku). Czego świadomie nie włączamy i dlaczego —
  `docs/rag/08`.
- Lint/format: `ruff` + `black` na dotykanych plikach; zamrożonych nie reformatuj. Różnice
  CRLF/LF są normalne.
- **Środowiska pracujące na repo:** serwer Linux w Polsce (praca badawcza od 2026-09-24;
  przygotowanie `bash tools/setup_serwer.sh`), komputer użytkownika z Windows (dziennik papierowy
  z Harmonogramu zadań) i Cowork w chmurze. Przed rundą `git pull` i świeży stan plików; nowszej
  wersji nie nadpisuj — zmerguj. Wersje bibliotek: `requirements-lock.txt` (inne wersje = inne liczby).
- **Dziennik papierowy:** pliki `dziennik/*.csv` i `przebiegi.log` zapisuje wyłącznie automat
  (commit i push po każdym przebiegu, poprawka 5). Zmiana kodu, którego dziennik używa
  (`backtest/live_journal.py`, `ts_momentum.py`, `xs_momentum.py`, `sizing.py`, `rebalance_premium.py`,
  `run_coinbase_cp1.py`, `data/fetch_live.py`), wymaga decyzji użytkownika i wpisu „Poprawka N”
  w `dziennik/README.md` — inaczej wynik dziennika przestaje być zapisem z góry.

## Podział ról i autonomia

**Użytkownik:** decyzje bramkowe faz (przejście/zamknięcie fazy, jakikolwiek realny kapitał)
i wszystko nieodwracalne (usuwanie danych/historii).

**Claude:** pełna autonomia badawcza W RAMACH zasad — sam wybiera i uruchamia eksperymenty,
wprowadza wynikające z nich zmiany, prowadzi git (branch/commit/merge/push) i pobiera dane, jeśli
środowisko ma shell i sieć (sesja lokalna ma; Cowork bywa bez). Raportuje po fakcie w tej samej
rundzie (`runs/` + `STATUS.md`). Jedna zmiana na raz, warianty zapisane przed obejrzeniem wyniku,
licznik aktualny, każda decyzja z uzasadnieniem i ścieżką odwrotu. Skrypty są neutralnymi
reporterami — werdykt podpisuje Claude w dokumentacji, nigdy „automat w skrypcie”.

## Struktura projektu

```
data/, agents/, agent_5_compliance/, backtest/, tests/   — kod
backtest/checkpoint_lib.py + run_checkpoint_v2.py        — kanoniczny pomiar (zasada 12)
backtest/negative_control.py                             — dane bez informacji o przyszłości (bramka A6)
runs/<data>_<id>-<slug>/ + runs/INDEX.md                 — rundy (zasady 11, 14)
docs/rag/ (01–08) + docs/INDEX.md                        — uzasadnienia decyzji; 08 = pełne brzmienie zasad
docs/skills/bramki-jakosci.md                            — procedura bramek (zasada 16)
STATUS.md                                                — plan, decyzje, ryzyka, zadania, backlog
config/settings.yaml, agents/feature_registry.yaml       — źródło prawdy parametrów
tools/skill_audit.py + runs/skille/<gałąź>.jsonl         — rejestr skilli (zasada 19)
tools/frozen_guard.py + runs/ZAMROZONE.txt               — zamrożone skrypty (zasada 13)
```

## Komendy (Windows: `py`; serwer Linux: `py` z `.venv` po `tools/setup_serwer.sh`; Cowork: `python3`)

```
py -m pytest -q                                   # cały zestaw testów (DoD, zasada 10)
py -m ruff check . && py -m black --check .       # lint/format; zamrożone skrypty omijane w pyproject.toml
py -m backtest.run_checkpoint_v2                  # kanoniczny checkpoint v2 (zasada 12)
py tools/skill_audit.py raport --galaz <gałąź>    # sekcja „Użyte skille” README rundy (zasada 19)
py tools/frozen_guard.py lista                    # lista zamrożonych skryptów (zasada 13)
```

## Zanim zmienisz `risk_controller.py`, `labeling.py`, `feature_miner.py` lub metodologię pomiaru

Przeczytaj odpowiedni plik w `docs/rag/` (metodologia pomiaru: `docs/rag/03`) — zmiana jednej
wartości bez sprawdzenia drugiej strony (np. mnożnika ATR) łamie spójność budowaną celowo.
