---
status: superseded
last_verified: 2026-09-22
depends_on: []
---

# 01 — Hipoteza tradingowa i architektura

> **STATUS: SUPERSEDED (2026-09-22).** Ten dokument opisuje hipotezę dwureżimową jako
> **do przetestowania**. Została przetestowana i ten opis jest nieaktualny jako stan projektu —
> pozostaje jako **zapis uzasadnienia pierwotnego wyboru**, nie jako opis tego, co obowiązuje.
>
> **Co zostało obalone:**
> - **specyfikacja dwureżimowa** (trend+range na 5m) — C2.5–C2.13, NO-GO odporne na fold-jitter,
>   pooled t istotnie ujemny w obu reżimach;
> - **architektura jednoreżimowa na `range`** (4h, V=3, 6,8 roku) — S1, kryterium przepadło
>   o 9,04 pp.
>
> **Czego NIE obalono — ważne rozróżnienie:**
> - **teza momentum pozostaje NIEPRZETESTOWANA.** Werdykt dla reżimu `trend` opiera się na próbie
>   zagłodzonej przez samą regułę reżimu: 0,53% świec, n=355, a tylko **0,49%** świec ma okno
>   etykiety wewnątrz własnego reżimu (Z16) — czyli niemal każda transakcja była oceniana ruchem
>   dziejącym się POZA reżimem, który ją uzasadnił. Najczystszy pomiar projektu (S1) testował
>   **wyłącznie `range`**. To jest niewykonalność pomiaru, nie dowód braku edge'u;
> - **konfiguracja 4h po naprawie pipeline'u jest NIETESTOWALNA** (S1b): przy poprawnie działającym
>   early stoppingu próba spada do n=345 wobec wymaganych 925 — brakuje 11,4 lat danych, których
>   Binance nie ma;
> - **ETH/SOL/BNB** — zero testów, wszystko na BTC (zasada 9 CLAUDE.md);
> - **funding rate jako CECHA/sygnał** (kandydat wskazany niżej w tym dokumencie na Fazę 1) —
>   nigdy nie zaimplementowany; modelowany wyłącznie jako składnik kosztu;
> - **ekonomia sizingu i dźwigni** — kill-switch testowany mechanicznie (C2c), nigdy jako
>   dźwignia rentowności.
>
> Aktualny stan: `runs/INDEX.md` („Wnioski skumulowane") i `STATUS.md`. Decyzja o dalszym
> kierunku (Z10) należy do użytkownika.

## Dlaczego nie realizujemy oryginalnego PRD wprost

Oryginalny PRD (CLAS-5, system 5-agentowy) zakładał, że autonomia, Compliance Gate, kill-switch,
audytowalność i dashboard budowane są równolegle jako gotowa architektura. Problem: **nigdzie nie
było zdefiniowanej hipotezy tradingowej (edge'u)**. Architektura bez potwierdzonego edge'u to
precyzyjnie zbudowany system do tracenia pieniędzy — dopracowany silnik wykonawczy wokół strategii,
która może nie mieć żadnej przewagi statystycznej.

Inne problemy zidentyfikowane w oryginalnym PRD:
- **Latencja 150ms niekompatybilna z LLM w hot-path.** Wywołanie API LLM to sekundy, nie
  milisekundy. Rozwiązanie: LLM działa wyłącznie offline/nadzorczo (recenzja modeli, wykrywanie
  driftu cech, raporty post-trade — `post_trade_critic.py`), nigdy w pętli decyzji real-time.
- **"100% lokalne" + zależność od API LLM to sprzeczność** — rozwiązana tym samym: hot-path
  (dane→cechy→XGBoost→ryzyko→decyzja) jest w 100% lokalny; LLM poza nim.
- **100% pokrycia testami to zły cel.** Coverage % nic nie mówi o poprawności finansowej logiki.
  Ważniejsze: property-based testing konkretnych właściwości (brak leakage, monotoniczność VaR).
- **Pełna autonomia na realnym kapitale od startu jest zbyt ryzykowna** bez fazy paper tradingu.

## Fazowanie — zasada nadrzędna

Nic z Części II oryginalnego PRD (5 agentów, dashboard, Docker) nie jest budowane, dopóki Faza 0
nie udowodni empirycznie edge'u statystycznego po kosztach transakcyjnych.

- **Faza 0:** dane + cechy + regime gate + dwa modele + risk_controller + checkpoint go/no-go.
- **Faza 1:** regime router (dispatcher), funding rate do modelu reversion, Compliance Gate
  budowany równolegle (nie po fakcie).
- **Faza 2:** `test_mathematics.py`, `ai_interpreter.py` — rozstrzygnąć, czy każdy "agent" z PRD
  faktycznie potrzebuje LLM, czy część to czysto deterministyczna logika.
- **Faza 3:** paper trading / testnet, minimum kilka tygodni. LEAN (nie freqtrade) jako silnik
  wykonawczy — patrz `04_narzedzia_zewnetrzne.md`.
- **Faza 4:** mały kapitał (w pełni tolerowalna strata), potem skalowanie.

## Hipoteza: regime-gated momentum + mean-reversion

Dwie SPRZECZNE tezy o tym samym ruchu ceny, rozdzielone regułą — nie połączone w jednym modelu:

- **Test 1 — Momentum:** w reżimie "trend" cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie "range" cena wraca do średniej po przegrzaniu.

Rozważane były też: funding rate/positioning i volatility breakout. Funding rate stał się
kandydatem na cechę do Test 2 w Fazie 1 (mechanistycznie pasuje do tezy "przegrzane
pozycjonowanie → odwrócenie"), nie osobnym testem.

**Czemu dwa osobne testy, nie jeden połączony model:** momentum zarabia na kontynuacji, reversion
na odwróceniu — to przeciwstawne zakłady o tym samym ruchu. Wrzucenie cech z obu do jednego
XGBoost bez informacji o reżimie zmusza model do odgadnięcia interakcji przy ograniczonej
efektywnej liczbie próbek — przepis na overfitting, który wygląda dobrze w backteście i nie
działa dalej. Testowanie osobno chroni diagnostykę: jeśli jeden test zawiedzie, wiadomo który i
dlaczego.

## Regime gate: reguła deterministyczna, nie ML

Trend/range/ambiguous klasyfikowane regułą (ATR percentile + direction persistence — patrz
`02_cechy_i_leakage.md`), nie modelem (np. HMM, klastering).

**Dlaczego reguła, nie ML** — to była świadoma decyzja, nie brak wiedzy o alternatywach (HMM i
RL do sizing to realne, używane w branży techniki):

1. **Budżet statystyczny.** Efektywna liczba niezależnych próbek w danych finansowych jest
   ograniczona (świece 5m są silnie autokorelowane). Każdy dodatkowy uczony komponent (regime
   przez HMM, sizing przez RL) zużywa ten budżet i mnoży ryzyko przeuczenia — trudniejsze do
   zdiagnozowania, gdy komponenty wchodzą w interakcję.
2. **Audytowalność.** Reguła jest w 100% deterministyczna — Compliance Gate testuje ją trywialnie
   (ten sam input = ten sam output). ML tutaj to dodatkowa czarna skrzynka do audytu.
3. **Sekwencja, nie wyrok.** Prostym, w większości regułowym systemem najpierw dowodzimy edge'u
   (Faza 0/1). Dopiero mając baseline, zamiana reguły na uczony komponent staje się dobrze
   zdefiniowanym eksperymentem (mierzalnym względem czegoś), nie skokiem na wiarę.

## Czemu XGBoost, nie deep learning (LSTM/GRU)

Świadomie odrzucone, nie brakujące. Dane tabelaryczne (RSI, ATR, returns) z ograniczoną liczbą
efektywnych próbek to dokładnie reżim, w którym gradient boosting (XGBoost) typowo bije sieci
neuronowe — te potrzebują znacznie więcej danych, żeby nie przeuczyć się bardziej niż drzewa.

## Czemu multi-agentowe LLM nie jest samo w sobie źródłem edge'u

Aktywna dziedzina badań (TradingAgents, FinCon, HedgeAgents, FinAgent) istnieje i jest legalna,
ale przegląd literatury (2026) formułuje kluczowe zastrzeżenie: wieloagentowe frameworki LLM
najlepiej traktować jako nadzorowanych asystentów badawczych, nie w pełni autonomicznych
decydentów finansowych — to pokrywa się z naszą decyzją o LLM offline/nadzorczym. Ta sama
literatura krytykuje się metodologicznie: małe próby (<50 spółek), krótkie okresy ewaluacji, brak
rygorystycznej statystyki out-of-sample — dokładnie te problemy, przed którymi zabezpiecza nasz
walk-forward.

Retail trading reality check: badanie CFTC na 36 000+ kont wykazało 60% traderów tracących;
szerzej cytowane statystyki mówią o 70-90% retail traderów kończących na stracie. Badanie
Quantopian na 888 strategiach: Sharpe z backtestu miał niemal zerową moc predykcyjną względem
wyników live, a nadmiernie zoptymalizowane strategie traciły do 80% zbacktestowanego zysku po
wdrożeniu — uzasadnienie całej dyscypliny walk-forward w tym projekcie.

## Multi-instrument: BTC, ETH, SOL, BNB

Zakres docelowy obejmuje cztery instrumenty, nie tylko BTC. To NIE zmienia sekwencji Fazy 0 —
zmienia to, co się dzieje PO Commicie 6.

**Zasada:** waliduj BTC samodzielnie do końca Commitu 6. Rozszerzenie na ETH/SOL/BNB to test
generalizacji tej samej, już ustalonej hipotezy (te same progi regime, te same hiperparametry,
bez retuningu per instrument) — nie równoległa walidacja czterech niezależnych strategii. Jeśli
edge trzyma się tylko na BTC, to sama w sobie wartościowa informacja (efekt specyficzny dla
płynności/mikrostruktury BTC), nie powód do odrzucenia projektu.

**Dlaczego nie trenować od razu łącznie (pooled) na wszystkich czterech:** więcej danych, ale
zakłada, że BTC/ETH/SOL/BNB mają tę samą dynamikę momentum/reversion — SOL jest wyraźnie bardziej
spekulacyjny/zmienny niż BTC, BNB ma idiosynkratyczne czynniki związane z samą giełdą Binance.
Pooled model uśredniłby te różnice, maskując, gdzie hipoteza faktycznie działa.

**Dlaczego nie trenować od razu osobno na czterech (cztery pary modeli):** mniej efektywnych
próbek na model niż przy jednym instrumencie — dokładnie problem efektywnej liczby próbek
(`03_ryzyko_i_sizing.md`), pomnożony przez cztery.

**Regime per instrument, nie market-wide — na razie.** BTC i altcoiny bywają silnie skorelowane
(efekt BTC dominance) — regime liczony osobno dla każdego instrumentu ignoruje to, że altcoiny
często podążają za BTC. To jest świadomie uproszczone na start, kandydat do rewizji w Fazie 1+,
nie błąd do naprawienia teraz.

**Kill-switch i limity ryzyka na poziomie CAŁEGO konta, nie per instrument** — inaczej cztery
pozycje mogą być każda "w normie" osobno, podczas gdy łączne konto traci. Wymaga risk_controllera
świadomego korelacji między instrumentami — patrz `03_ryzyko_i_sizing.md`.

**"4 instrumenty = 4x danych" jest błędne, jeśli są skorelowane.** Altcoiny często ruszają się
razem z BTC — to nie są niezależne próbki. Efektywna liczba próbek rośnie mniej niż 4x.
