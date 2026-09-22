# CLAS-5 — Instrukcje projektowe (Claude Code)

## Projekt
System tradingowy BTC/ETH/SOL/BNB perpetual futures. Regime-gated: deterministyczna reguła (nie
model) rozdziela dane na reżim "trend" (momentum) i "range" (mean-reversion) — dwa osobne,
niezależnie trenowane modele XGBoost, nie jeden połączony.

**Cel Fazy 0:** udowodnić edge statystyczny minimalnym, audytowalnym systemem, zanim dobuduje się
cokolwiek z oryginalnego PRD (5 agentów, dashboard, Docker). Status commitów, checkpointy,
otwarte ryzyka → `STATUS.md`; zadania i backlogi → `STATUS.md`; surowe
wyniki rund → `runs/INDEX.md`. Te pliki zmieniają się często — traktuj jako aktualny stan, nie
jako źródło stałych zasad.

## Nienaruszalne zasady

1. **Nigdy nie optymalizuj parametrów** (okna wskaźników, progi regime, hiperparametry) na całym
   zbiorze danych naraz — tylko wewnątrz walk-forward. Uzasadnienie: `docs/rag/03_ryzyko_i_sizing.md`.
2. **Każda nowa cecha dostaje test leakage PRZED wejściem do modelu**, nie po.
   Metodologia: `docs/rag/02_cechy_i_leakage.md`.
3. **Target (triple-barrier) i risk_controller (stop-loss) używają TEGO SAMEGO mnożnika ATR
   (1.5×).** Rozjazd między nimi = trenujesz na czymś innym niż handlujesz.
4. **Rozszerzanie feature setu: jedna cecha na raz, mierzona na out-of-sample.** Nigdy grid search
   po wielu kombinacjach naraz. Powód: `docs/rag/02_cechy_i_leakage.md` (multiple testing).
5. **Leverage cap zawsze wygrywa nad fixed-fractional sizing** — jawna reguła `min()`, nie coś do
   odkrycia w runtime.
6. **LLM nigdy w hot-pathie decyzyjnym.** Offline/nadzorczo tylko (recenzja modeli, raporty
   post-trade). Powód: `docs/rag/01_hipoteza_i_architektura.md`.
7. **Regime gate i sizing zostają regułami (nie ML), dopóki minimalny system nie udowodni
   edge'u.** Zamiana na HMM/RL to eksperyment PO ustaleniu baseline'u.
8. **freqtrade / LEAN / QuantConnect = katalog wzorców, nigdy zależność runtime w Fazie 0.**
   Szczegóły per narzędzie: `docs/rag/04_narzedzia_zewnetrzne.md`.
9. **Multi-instrument (BTC/ETH/SOL/BNB): waliduj BTC samodzielnie do końca Commitu 6 PRZED
   testowaniem pozostałych.** Rozszerzanie na inne instrumenty to test generalizacji tej samej
   hipotezy (te same progi, bez retuningu), nie równoległa walidacja czterech niezależnych
   strategii naraz. Uzasadnienie: `docs/rag/01_hipoteza_i_architektura.md`.
10. **Commit nie jest "zrobiony" bez testów jednostkowych + (jeśli dotyczy) testu leakage +
    (jeśli dotyczy) property-based testu w `hypothesis`.** Pełna checklista Definition of Done:
    `docs/rag/05_metodologia_wytwarzania_i_testow.md`.
11. **Każdy ciężki przebieg na realnych danych** (checkpoint, kalibracja, sweep, screening)
    **dostaje WŁASNY KATALOG `runs/YYYY-MM-DD_<id>-<slug>/`** zawierający `README.md`
    (write-up: ID, Metadane, **Poprzedzające wyniki**, Wynik, "Co na plus (+) / Co na minus
    (-)", Wniosek, Rekomendacja) **+ `raw_output.txt`** (pełny, nieskrócony stdout) + ewentualne
    artefakty. Do tego **wiersz w `runs/INDEX.md` z licznikiem wariantów** (księga budżetu
    multiple-testing) **i aktualizacja sekcji "Wnioski skumulowane"** tamże. Pełna procedura:
    `runs/INDEX.md`, sekcja "Jak dodać nowy wpis".
12. **Wyniki raportuje się metodologią checkpointu v2** (`backtest/run_checkpoint_v2.py` /
    `backtest/checkpoint_lib.py`: sweep fold-jitter, per-fold t-stat, pooled per regime, N_eff;
    od C2.11 także rozbicie edge'u: trafność `p`, break-even, margines). **Uwaga na dwie
    wielkości pod nazwą „margines":** kolumna `margin` w `summarize_edge_by_regime` to
    `hit_rate − break_even_p` w PUNKTACH TRAFNOŚCI, a `(2p−1)·B − C` to margines
    w JEDNOSTKACH ZWROTU. Dla S1: −0,0447 vs −0,00113. Zawsze podawaj, o którą chodzi.
    **Nigdy nie cytuj "stabilności na 10 seedach"** — XGBoost w konfiguracji Fazy 0 jest
    deterministyczny, więc ten sweep nie mierzy niczego (`docs/rag/03`, aktualizacja 2026-09-21).
13. **Historyczne skrypty analityczne są ZAMROŻONE** — to odtwarzalne zapisy zakończonych
    eksperymentów (komenda w sekcji "Metadane" ich plików `runs/`), nie kod do refaktoryzacji
    wstecz. Nowe skrypty budują na `backtest/checkpoint_lib.py`.
14. **PRZED każdą nową rundą/eksperymentem przeczytaj `runs/INDEX.md`** (tabela + "Wnioski
    skumulowane") **i README runów powiązanych z planowaną zmianą** — projekt rundy musi
    jawnie budować na przebytych wynikach: sekcja "Poprzedzające wyniki" w README nowej rundy
    wymienia, które wcześniejsze runy ją motywują/ograniczają. Nigdy nie testuj ponownie
    wariantu już przetestowanego (albo równoważnego — jak `bb_pctb_20` ≡ `price_zscore_20`,
    C2.7) bez jawnego odnotowania, dlaczego powtórka jest uzasadniona.
15. **Wynik każdego kamienia milowego jest aktualizowany w `README.md`** — sekcja
    "Kamienie milowe" (tabela: ID, data, jednozdaniowy wynik, link do katalogu w `runs/`)
    plus zsynchronizowana sekcja "Status". Kamień milowy = zamknięta runda z `runs/`,
    checkpoint go/no-go, decyzja bramkowa fazy, uruchomienie/zatrzymanie programu badawczego.
    README jest widokiem z lotu ptaka dla CZŁOWIEKA — aktualizacja domyka rundę tak samo
    obowiązkowo jak wpis do `runs/INDEX.md` (zasada 11).
16. **Bramki jakości rundy** (procedury przystosowane do projektu; obowiązują ZAWSZE,
    niezależnie od tego, czy w sesji są jakiekolwiek wtyczki ze skillami):
    (a) **PRZED publikacją write-upu rundy** — walidacja: przeliczenie co najmniej JEDNEJ
    kluczowej liczby drugą, niezależną drogą; jawne pytanie **"kogo NIE ma w zbiorze"**
    (filtry/bramki/warmupy — dokładnie ten bias złapał nas w C2d, gdzie pozorny edge
    mieszkał w odfiltrowanych świecach); red-flag "wynik idealnie potwierdza hipotezę";
    werdykt **Ready / Caveats / Revision zapisany w README rundy**;
    (b) **standard raportowania statystyk** — efekt + CI/half-width zamiast samego p/z,
    zakresy zamiast fałszywej precyzji, przy skośnych zwrotach per trade mediana obok
    średniej, zawsze w kontekście licznika multiple-testing (zasada 11);
    (c) **PRZED merge rundy do master** — przegląd diffu (korektność/edge-case'y/testy/
    czytelność) z werdyktem jednym zdaniem w README rundy.
    **Źródłem procedury jest `docs/skills/bramki-jakosci.md`** (listy kontrolne, pułapki
    z naszych rund, wzory do przeliczeń, format werdyktów) — plik w repo, bez zależności od
    wtyczek. Jeśli w sesji są skille `engineering:code-review` / `engineering:architecture`,
    używaj ich jako wsparcia; brak skilla NIE zwalnia z bramki.
17. **Rozmowa z użytkownikiem toczy się prostym, zrozumiałym językiem.** Odpowiedzi na czacie
    i raporty z rund mają być zrozumiałe dla osoby, która nie zna żargonu statystyki, tradingu
    ani programowania: krótkie zdania, bez skrótów myślowych. Jeśli fachowe pojęcie jest
    naprawdę potrzebne (np. „przedział ufności", „walk-forward", „edge"), wyjaśnij je przy
    pierwszym użyciu jednym prostym zdaniem w nawiasie. Każdą kluczową liczbę podawaj z
    tłumaczeniem, co z niej wynika dla decyzji — np. „trafność 48,6% przy progu 53,1% =
    strategia trafia rzadziej, niż musiałaby, żeby wyjść na zero po kosztach". To samo dotyczy
    sekcji **Wniosek** i **Rekomendacja** w README każdej rundy. Techniczna precyzja (wzory,
    pełne tabele, kod) zostaje w sekcjach technicznych i w `raw_output.txt` — prosty język ją
    TŁUMACZY, nie zastępuje.
18. **Hipoteza dostaje rachunek MIERZALNOŚCI przed uruchomieniem, nie po.** Pre-rejestracja
    każdej rundy eksperymentalnej podaje wynik
    `backtest/metrics.py::measurability_report(zakładana_trafność, break_even, oczekiwane_n)`.
    **`oczekiwane_n` liczy się przez `expected_trades(n_świec, abstynencja, admission_rate)`,
    nie z liczby świec** — to człon, którego brak przewrócił trzy rundy z rzędu: S1 → S1b
    (1 037 → 345), S1b → H2.1 (345 → 98), i samą kontrolę K1 (n≈37 na losowanie). Za każdym
    razem zaskoczenie, mimo że precedens leżał już w repo (wniosek skumulowany 19).
    **Runda, której `measurability_report` zwraca NIEMIERZALNA, nie startuje** — jej wynik
    nie rozstrzygnie niczego NIEZALEŻNIE od tego, co wyjdzie, więc uczciwiej jej nie
    uruchamiać, niż potem interpretować nierozstrzygalną liczbę.
    **ŚWIADOMIE BEZ ZAMROŻONEGO PROGU.** Nie wolno dokładać stałej w rodzaju „hipoteza musi
    zakładać ≥58% trafności" — liczba 58,2% z K1 była artefaktem rozdzielczości siatki `q`
    i została sprostowana w K2. Właściwością przyrządu jest `wald_half_width(n)`, zależna
    WYŁĄCZNIE od `n`. Projekt ma już dwa udokumentowane trupy po zamrożonych progach
    (`MIN_VALIDATION_ROWS = 30` po cichu wyłączył early stopping w 92% foldów — Z17b;
    `std < 0.2` ze sweepu seedów, o którym `checkpoint_lib` pisze wprost, że go nie
    rejestruje). Trzeciego nie dokładamy.
    **Kryterium pre-rejestrowane sprawdź też w granicy dużego `n`** — czy nie jest
    anty-skorelowane z celem rundy. Bramka 1 w K2 żądała, by CI trafności zawierało próg
    opłacalności, co na czystym szumie jest równoważne warunkowi `n ≤ ~1 142`: mierzyła
    nieprecyzyjność zamiast specyficzności i karała każde ramię osiągające cel rundy
    (wniosek skumulowany 28).

## Wytyczne (miękkie — do rewizji, gdy zmienią się dane)

- **Per-fold `mean_sharpe` NIE jest już nośną statystyką porównań** (C2.12: σ fold-jitter
  rozjechała się 3,1→75,7 przy LEPSZEJ ekonomice per trade — annualizacja przy n≈kilka
  transakcji/fold produkuje artefakty). Warianty rozstrzygaj na **pooled t-stat / t_neff i
  marginesie `(2p−1)·B − C`** (z z_margin); kryteria klasyfikacji z docs/rag/03 pozostają
  formalnie niezmienione jako werdykt bramkowy. Szum nośnych statystyk zmierz ponownie po
  każdej istotnej zmianie datasetu/modelu kosztów.
- **Liczniki wariantów rozwidlają się per baza danych i per hipoteza** — stara baza
  (2025-07→2026-07), nowa baza (2023-07→2026-07, od C2.10) i nowa hipoteza jednoreżimowa 4h
  (od Z5b) mają OSOBNE liczniki w `runs/INDEX.md`; wyników między bazami nie porównuje się 1:1.
- **Jedna informacja mieszka w JEDNYM miejscu** (podział odpowiedzialności dokumentów):
  `runs/<katalog>/` = pełne wyniki (źródło prawdy); `runs/INDEX.md` = syntezy + wnioski
  skumulowane + liczniki; `STATUS.md` = decyzje/uzasadnienia/ryzyka (§7)/roadmapa
  faz — sekcja per commit KRÓTKA (status + 2-3 zdania + link do runs/); `STATUS.md` = statusy
  zadań/zasady pracy/backlog — wiersz zadania to status + jednozdaniowa uwaga + link;
  `README.md` = widok dla człowieka + kamienie milowe (zasada 15). Nie kopiuj pełnych syntez
  do PLAN/TASKS (historyczna duplikacja do odchudzenia: Backlog Z25).
- **Mapowanie na momenty pracy — najpierw pliki w repo, wtyczki dopiero jako wsparcie.**
  Procedura rundy → skill `clas5-runda` (**jedyna kopia: `.claude/skills/clas5-runda/SKILL.md`**
  — to plik, który Claude Code faktycznie ładuje; nie rób drugiej kopii w `docs/`, bo rozjazd
  jest wtedy kwestią czasu, a ładowana zostaje wersja starsza). Bramki jakości →
  `docs/skills/bramki-jakosci.md` (zasada 16). Decyzja architektoniczna → ADR do `docs/rag/`,
  wsparcie: `engineering:architecture`. Wykresy → `dataviz`.
  **Zanim oprzesz procedurę na skillu z wtyczki, sprawdź, czy on w tej sesji istnieje** —
  wtyczki włącza się per maszyna i per projekt, a nie da się tego wyczytać z repo. Zasady
  16a/16b wskazywały kiedyś `data:validate-data` i `data:statistical-analysis`; w praktyce
  wtyczka `data` bywa wyłączona i obie bramki po cichu nie miały jak zadziałać. Dlatego
  procedura mieszka w repo, a skill jest udogodnieniem, nie warunkiem.
- Lint/format: `ruff` + `black` na plikach dotykanych w rundzie; plików zamrożonych (zasada 13)
  nie reformatuj. Różnice CRLF/LF między repo (Windows) a środowiskiem pracy są normalne.
- **Dwa środowiska pracują na tym repo** (sesja chmurowa Cowork + lokalna sesja Claude Code na
  maszynie użytkownika). Przed każdą rundą ZSYNCHRONIZUJ stan z repo (zasada 14 obejmuje też
  "przeczytaj świeży stan plików, nie cache z własnej pamięci sesji"); nie nadpisuj plików,
  których wersja na dysku jest nowsza niż twoja — zmerguj.

## Podział ról i autonomia (uzgodnione 2026-09-22)

**Użytkownik:** decyzje bramkowe faz (przejście do Fazy 1, zamknięcie Fazy 0, jakikolwiek realny
kapitał) i wszystko nieodwracalne (usuwanie danych/historii).

> **Sprostowanie 2026-09-22:** wcześniejsze brzmienie przypisywało użytkownikowi także operacje
> git i pobieranie danych, uzasadniając to tym, że „Claude nie ma shella na maszynie" i „sandbox
> nie ma dostępu sieciowego do giełdy". **W sesji lokalnej Claude Code oba są nieprawdą** —
> w rundach Z5/Z9/Z5b Claude pobrał dane 5m/1h/4h wprost z Binance i sam prowadził
> branche/merge/push. Zapis w starej formie mógłby zniechęcić przyszłą sesję do zrobienia
> rzeczy, które umie. Podział zależy więc od środowiska: sesja chmurowa Cowork bywa bez shella
> i bez sieci, sesja lokalna ma oba. **Niezmienne pozostaje to, co wyżej:** decyzje bramkowe
> i operacje nieodwracalne zawsze wymagają zgody użytkownika.

**Claude — pełna autonomia badawcza W RAMACH zasad 1–18:** samodzielnie wybiera i uruchamia
kolejne eksperymenty (w tym z backlogu w `STATUS.md`), może wprowadzać wynikające z wyników
zmiany parametrów/cech/configu — **raportując po fakcie, w tej samej rundzie** (plik `runs/` +
`STATUS.md` §5/§7 + `STATUS.md`). Autonomia nie uchyla dyscypliny: jedna zmiana na
raz, warianty rejestrowane z góry (przed obejrzeniem wyniku), licznik multiple-testing
aktualizowany, każda decyzja udokumentowana z uzasadnieniem i ścieżką odwrotu (co i jak
zrevertować). Skrypty pozostają neutralnymi reporterami — decyzję podejmuje i podpisuje w
dokumentacji Claude, nigdy "automat w skrypcie".

## Struktura projektu

```
data/, agents/, agent_5_compliance/, backtest/, tests/   — kod produkcyjny
backtest/checkpoint_lib.py + run_checkpoint_v2.py        — kanoniczna metodologia pomiaru (zasada 12)
runs/<data>_<id>-<slug>/ (+ runs/INDEX.md)               — katalog per run: README.md +
                                                            raw_output.txt (zasady 11 i 14);
                                                            INDEX = spis + wnioski skumulowane
docs/rag/ (01–07) + docs/INDEX.md                        — PEŁNE uzasadnienia decyzji (czytaj
                                                            przed zmianą architektury, nie tylko kodu)
STATUS.md                                                 — plan, historia rund, ryzyka,
                                                            zadania, backlog, zasady operacyjne
                                                            (scalone IMPLEMENTATION_PLAN+TASKS,
                                                            2026-09-22; numeracja §1–§12 zachowana)
config/settings.yaml, agents/feature_registry.yaml        — źródło prawdy dla parametrów
```

## Zanim zmienisz coś w `risk_controller.py`, `labeling.py`, `feature_miner.py` lub metodologii pomiaru

Przeczytaj odpowiedni plik w `docs/rag/` (dla metodologii pomiaru: `docs/rag/03`, sekcja
checkpointu + aktualizacja 2026-09-21) — te decyzje mają konkretne, przetestowane uzasadnienie
(nie są arbitralne), i zmiana jednej wartości bez sprawdzenia drugiej strony (np. mnożnika ATR)
łamie spójność, którą specjalnie budowaliśmy.
