# CLAS-5 — status projektu (plan, zadania, backlog)

> **Scalenie `IMPLEMENTATION_PLAN.md` + `TASKS.md` (2026-09-22).** Oba pliki usunięte —
> ten dokument jest ich jedynym następcą. Numeracja sekcji **§1–§12 zachowana** z
> `IMPLEMENTATION_PLAN.md`, żeby istniejące odniesienia („§5", „§7") nadal działały;
> treść `TASKS.md` weszła jako §13–§16.
>
> **Podział odpowiedzialności między trzy pliki w korzeniu** (świadomie nie jeden):
> - `CLAUDE.md` — zasady nienaruszalne (lista numerowana). **Jedyne źródło.** Ładowany automatycznie
>   do kontekstu Claude'a w każdej sesji, więc musi zostać krótki.
> - `README.md` — wizytówka projektu dla człowieka wchodzącego z zewnątrz.
> - `STATUS.md` (ten plik) — plan, historia rund, ryzyka, zadania, backlog.
>
> Księga eksperymentów i budżetu multiple-testing: `runs/INDEX.md` (CLAUDE.md zasada 11).
> Pełne uzasadnienia decyzji architektonicznych: `docs/rag/` + `docs/INDEX.md`.

---

> Dokument roboczy do pracy w VS Code. Konsoliduje wszystkie decyzje z sesji planistycznej.
> Jeśli zaczynasz nową sesję Claude Code, podepnij ten plik jako kontekst — zastępuje potrzebę
> przewijania całej wcześniejszej rozmowy.
>
> Ostatnia aktualizacja nagłówka: 2026-09-22. **Status: Faza 0 ZAMKNIĘTA wynikiem negatywnym
> (Z10). Po zamknięciu zmierzono z zapasem mocy wszystko, co da się zmierzyć tą metodologią na
> BTC: momentum (M1, 49,74%), funding jako cechę (F1, 50,34%); dane o pozycjonowaniu są
> niemierzalne (P1, 30 dni historii) — wniosek skumulowany 39 w `runs/INDEX.md`. Otwarte
> kierunki wymagają zmiany założeń (§17, ETAP 4). P2 (carry przekrojowy) wyszło NIEMIERZALNE; T4 (kalibracja
> early stoppingu, 2026-09-23) zamknięte bez zmian w kodzie. **W1 (2026-09-23): backtest mierzy
> wykonanie „po konkretnej cenie" (symulacja wypełnień); limit po close wypełnia się w 99,4 % i nic
> nie zmienia; cofnięcie podnosi trafność do 53,15 %, ale traci pieniądze (t = −3,9) — seria W
> zamknięta 3/3. N1 (2026-09-23, NOWA BAZA od 2021 — zasada 20): częściowe wyjście 50 % + stop
> na wejściu nie zmienia pieniędzy (różnica parowana +0,007 % [−0,009; +0,024]), trafność 53,3 %
> to iluzja geometrii (p\* 57,2 %) — seria N zamknięta 1/1. A1 (2026-09-23): formacje świecowe
> z podręcznika trafiają 46,4 % [44,4; 48,3] — poniżej monety — i jako cecha modelu nic nie
> zmieniają (−0,001 % [−0,012; +0,010]); rodzina formacji zamknięta 2/2. A2 (2026-09-23): reszta
> analizy technicznej jako reguły — struktura trendu 48,2 %, wsparcie/opór 49,9 %, Fibonacci 51,5 %
> (nierozstrzygnięte), zdarzenia AT 48,3 %, model + 10 cech AT bez zmian; seria A zamknięta 7/7,
> analiza techniczna na BTC 4h zamknięta jako kierunek. C1 (2026-09-23): cash-and-carry z hedgem
> spot — PIERWSZY POZYTYW, ale jako przepływ za dźwignię, nie prognoza: +5,4 %/rok kapitału
> [3,5; 7,4], połowa z 2021, ostatnie 3 lata 3,6 %; przełączanie po znaku fundingu NEGATYWNE;
> decyzja o produkcie należy do użytkownika. R1 (2026-09-23): premia rebalansowa koszyka top-20
> −3,6 %/rok [−9,5; +2,4] — ruchy względne w krypto trwają, rebalans nie zarabia; seria R 1/1.
> Kolektor pozycjonowania aktywny (codziennie 09:00). Punkt 2 zlecenia zamknięty.
> P3 (2026-09-23): podłączono 8 darmowych źródeł spoza OHLCV — **archiwum Binance ma
> pozycjonowanie co 5 min od 2020-09 (6 lat; P1 sprawdziło tylko REST z 30 dniami), więc
> pozycjonowanie jest MIERZALNE** (wniosek 59); do tego funding COIN-M, 24 kontrakty
> kwartalne, DVOL, on-chain, F&G, FRED, Coinbase. Zero pomiaru sygnału; następne rundy
> D1 (produkt carry) → O1 (pozycjonowanie jako cecha) → X1 (momentum przekrojowe).
> D1 (2026-09-23): produkt carry ma sens tylko w konstrukcji COIN-M (zabezpieczenie w BTC,
> bez likwidacji, kapitał 1×): +9,1 %/rok [5,9; 12,3], od 2022 ~+1,8 pp ponad T-bill
> (od −1,5 do +7,2); USDT-M z depozytem 1× i miesięcznym uzupełnianiem bezpieczne, ale od 2022
> poniżej T-bill; basis kwartalny ≈ funding. Decyzja o produkcie = użytkownik.
> X1 (2026-09-23): momentum przekrojowe top-20 (long zwycięzcy / short przegrani 4 tygodni,
> trzymanie tydzień) **+22 %/rok netto [−5; +49], dodatni w 6/6 lat, ale NIEROZSTRZYGNIĘTY**
> (t 1,58; 2025 = połowa sumy) — pierwszy dodatni punktowo zakład o kierunek relatywny;
> seria X 1/1 STOP; rozstrzygnięcie tylko większą próbą (decyzja użytkownika).
> **DECYZJA UŻYTKOWNIKA 2026-09-23 (po D1): „carry odpuszczamy — nie o takie zwroty mi
> chodzi"** — kierunek cash-and-carry (C1/D1) ZAMKNIĘTY bez produktu; cel projektu to zwroty
> rzędu zakładu o kierunek, nie kilkuprocentowy przepływ. Program idzie dalej: O1
> (pozycjonowanie jako cecha modelu 4h) i kolejne źródła z P3.
> O1 (2026-09-23): zmiana open interest 24h jako 5. cecha modelu 4h — **NEGATYWNY** (−0,074 %
> na transakcję, trafność 50,25 % vs próg 53,07 %), ale pierwsza cecha spoza wykresu, która
> porusza model (+0,024 pp [−0,019; +0,067] wobec kontroli, inny kierunek w 21 % transakcji);
> seria O 1/1 STOP. Pozostałe kolumny archiwum i inne źródła P3 (DVOL, on-chain, F&G) =
> osobne serie, każda po decyzji użytkownika.
> L1/V1/G1 (2026-09-23, decyzja użytkownika „wykonaj po kolei 3 warianty"): on-chain podaż na
> giełdach, DVOL − zrealizowana, Fear & Greed jako 5. cecha modelu 4h — **trzy razy NEGATYWNY**
> (p 49,8 / 50,5 / 49,9 % vs próg ~53,5 %; parowo +0,003 / +0,018 / +0,002 pp, wszystkie z zerem
> w CI). Wniosek 67: dokładanie pojedynczych cech spoza wykresu nie wyprowadzi modelu 4h ponad
> próg; serie L/V/G 1/1 STOP.
> X2 (2026-09-23, decyzja użytkownika „wykonaj oba"): momentum na top-50 **+15,9 %/rok
> [−12,3; +44,2], NIEROZSTRZYGNIĘTY i słabszy niż X1** (IC 0, połowa sumy w 33 dniach, 2022
> −20 %); reguła X1 na innej siatce tygodniowej daje +9 % zamiast +22 %/rok — **X1 wrażliwe na
> fazę rebalansu** (wniosek 68). Rodzina B1: słabe poparcie, bez dowodu; X2 1/1 STOP.**
> Y1/Y2 (2026-09-23, decyzja użytkownika „dla 2 sprawdź horyzont 1h oraz 1d"): ten sam model
> kontrolny na NOWYCH BAZACH 1h i 1d — **1h NEGATYWNY z ogromnym zapasem** (p 48,34 %
> [47,70; 48,98] vs próg 54,0 %, n 23 334, t_neff −11,74, 6/6 lat ujemnych), **1d
> NIEROZSTRZYGNIĘTY** (50,20 % [47,07; 53,34] vs 51,7 %, n 978 — jak policzono przed
> przebiegiem). Wniosek 69: zmiana horyzontu nie jest drogą; rodzina „kierunek z OHLCV"
> zmierzona na trzech interwałach. Serie Y1/Y2 1/1 STOP.**
> TS1 (2026-09-24, decyzja użytkownika „testuj dalej różne kombinacje”): trend tygodniowy na
> koszyku top-20 (każda moneta long/short wg znaku 28 dni, skalowanie zmiennością) —
> **+14,8 %/rok [−1,7; +31,3], t_neff 1,76: NIEROZSTRZYGNIĘTY, najsilniejszy ślad w projekcie**
> (6/6 lat, 7/7 faz dodatnich, bez bety; ponad 100 % H0). 3× kapitału niszczy wynik (CAGR +5 %,
> obsunięcie 90 %). Wniosek 70; seria TS 1/1 STOP; rozstrzygnąć może tylko test na żywo.**
> NL1 (2026-09-24): short na 569 nowych kontraktach USDT-M przez 14 dni — **+2,1 % na zdarzenie
> [−2,7; +6,9], NIEROZSTRZYGNIĘTY**; mediana +13,5 %, ale 12 % nowych monet podwaja cenę
> (likwidacja nawet przy 1×); przy 3× 42 % likwidacji. Wniosek 71; seria NL 1/1 STOP.**
> CP1 (2026-09-24): premia Coinbase → BTC na tydzień — **POZYTYWNY wg pre-rejestracji (pierwszy
> w projekcie): +32 %/rok [+2; +62], t_neff 2,09**, bez śladu przecieku; po korekcie na ~28
> odczytów nieistotny, alfa ponad trend t 1,67. Wniosek 72; seria CP 1/1 STOP; następny krok:
> ta sama reguła na danych od 2026-07-01.**
> TF1 (2026-09-24): trend TS1 z filtrem tłoku (funding) — **różnica −1,4 %/rok [−6,6; +3,8],
> NIEROZSTRZYGNIĘTY**, filtr nie pomaga. Wniosek 73; seria TF 1/1 STOP.**
> TR1/TP1 (2026-09-24): reguła TS1 poza próbą — **na monetach 21–50 +14,1 %/rok (t 1,62, kopia
> TS1, ale korelacja 0,86); na nowych danych lip–wrz 2026 +0,7 % (brak obalenia)**. Wniosek 74;
> seria TS zamknięta na historii, dalej dziennik prospektywny.**
> CP1P (2026-09-24): premia Coinbase na nowych danych lip–wrz 2026 — **+0,1 % przy BTC +33 %**,
> brak obalenia i brak wsparcia; dziennik CP co kwartał.**
> TL1 (2026-09-24): tłok lewara (OI) na przekroju top-20 — **−10,5 %/rok [−25,2; +4,2],
> NIEROZSTRZYGNIĘTY**, IC ≈ 0. Wniosek 75; seria TL 1/1 STOP.**
> LQ1 (2026-09-24): poprawka TS1 o likwidacje przy 3× — **koszt −3,6 %/rok, TS1 +11,3 %/rok
> (t 1,34)**; przy 2× koszt ~1,6 pkt. Wniosek 76.**
> SZ1 (2026-09-24): reguły wielkości pozycji dla trend + Coinbase — **po połowie / budżet ryzyka
> ~+19 %/rok, obsunięcie ~18–19 %, depozyt ~23 %; hamulec po stracie szkodzi** (opisowo). Wniosek 77.**
> SC1 (2026-09-24): skalowanie pozycji siłą sygnału — **NIEMIERZALNE (szum ±13–17 %/rok), nie
> wystartowało**. Wniosek 78.**
> NC1 + porządki metodyki (2026-09-24, „wykonaj wszystko” po przeglądzie SIGMA/lessons): **kontrola
> negatywna zaliczona** — TS1/X1/CP1 na szumie t ≈ 0, zajrzenie w przyszłość t ≥ 13 (wniosek 79);
> bramki A6/B6a/C1 z wytycznych SIGMA; strażnik `tests/test_runs_index_guard.py`; skrót stanu wiedzy
> na górze `runs/INDEX.md`; `CLAUDE.md` 340 → ~170 linii (pełne brzmienie: `docs/rag/08`).**
> CP2 (2026-09-24): premia Coinbase na ETH/SOL — **NIEMIERZALNA, nie wystartowała**: sygnał = BTC
> w 94 % / 89 % dni, rozdzielczość ±36–37 %/rok. CP1 rozstrzygnie tylko dziennik na żywo. Wniosek 80.**
> DZIENNIK NA ŻYWO (2026-09-24, decyzja użytkownika: 2–3 miesiące): trend 2× + premia Coinbase 3×, R1; wynik od
> 2026-09-24 (poprawka 1; progi 18,4 %/27,6 % — poprawka 2 po RU1); `py -m backtest.live_journal` codziennie; odczyt mechaniki ~2026-12-25. `dziennik/README.md`.**
> SH1 + RU1 (2026-09-24): sonda 10 hipotez — **0 mierzalnych** (wniosek 81); **uniwersum było obcięte
> (287/685)** — po korekcie TS1 +11 %/rok, X1 +42 % (1/3 z MYX), SZ1 R1 +17 %/18 %; oba ślady odporne,
> nierozstrzygnięte (wniosek 82).**
> RU2 (2026-09-24): TR1, X2, LQ1, TF1, R1 na pełnym uniwersum — **werdykty bez zmian** (wniosek 83).
> BACKLOG: TL1 (wymaga OI nowych członków).**
> **DECYZJA BRAMKOWA 2026-09-24 (użytkownik, droga B + C): ADR-09 — drabina dowodów** zamiast „dowodu na
> historii”. Trend: szczebel 1(a) i 2 spełnione, 1(b) = TX1 w toku; premia Coinbase: tylko papierowo;
> X1: poza dziennikiem. Szczebel 4 (≤ 5 % kapitału) — decyzja użytkownika po odczycie dziennika ~2026-12-25.**
> TX1 (2026-09-24): trend na 19 rynkach FRED 1990–2026 +5,1 %/rok (t 2,73, POZYTYWNY), po 2013 −0,2 % →
> szczebel 1(b) NIEROZSTRZYGNIĘTY (wniosek 84).**
> WF1 + HC1 (2026-09-24, decyzje użytkownika): dłuższe okno uczenia modelu 4h — oba warianty NEGATYWNE
> (wniosek 85); cykl halvingowy — 0–18 mies. wzrosty 9/9, 18–24 mies. spadki 3/3, trend traci w 24–30 mies.
> 4/4 (opis, wniosek 86). DO DECYZJI: czy zmniejszać dźwignię trendu w fazie 18–30 mies. (reguła ryzyka).**
> SKILL (2026-09-24): `zarzadzanie-pozycja` rozszerzony o tryb systemowy (sekcja E: lista zleceń z `dziennik/sygnaly.csv`,
> kontrole konta, dziennik wykonania papier vs rzeczywistość; bez reguł B/D trybu ręcznego) — paczka w Pobranych,
> obowiązuje po wgraniu na claude.ai przez użytkownika; wpis w tabeli zasady 19.**
> AU1 (2026-09-24): audyt — obliczenia poprawne; cechy spoza wykresu niezmierzone (model 60 dni za gruby);
> TR1 od 2021-02 t 1,99 (po fakcie); opisy skorygowane (wniosek 87). DO DECYZJI: pomiar cech jako reguł,
> RU3 (start TR1/X2), X1 w dzienniku.**
> RU3 (2026-09-24, decyzja użytkownika): start TR1/X2 od 2021-02 — TR1 +15,5 %/rok, t 1,99 (formalnie ponad 1,96,
> znany z AU1, niesiony przez 02–04.2021; od 2022 t 1,32), X2 t 1,59 — obraz bez zmian (wniosek 88).**
> X1F (2026-09-24): X1 jako średnia 7 dni tygodnia +9,5 %/rok, t 0,61 — dawne +42 % to najlepszy dzień;
> X1 w dzienniku papierowym od 25.09 (osobno, decyzja użytkownika); poprawka filtra nazw dziennika (wniosek 89).
> HARMONOGRAM (2026-09-24, prośba użytkownika): zadanie „CLAS5 dziennik” 02:30 — dodane nadrabianie terminu,
> budzenie, bateria, 3 ponowienia, praca w tle bez okna (test 24.09 19:01: kod 0, pełny przebieg); tryb bez
> logowania wymaga administratora (polecenie w `dziennik/README.md`).
> SERIA SW (decyzja użytkownika 2026-09-24): cechy spoza wykresu — etap 1 pojedyncze reguły, etap 2 jeden model
> XGBoost ze wszystkimi (okno 365 dni) jako JEDEN wariant = świadomy wyjątek od zasady 4.**
> SW (2026-09-24): 8 reguł tracą po kosztach, model 365 dni −0,050 %/tr (t −1,78); duża przewaga wykluczona; ślad
> przed kosztami +0,02–0,05 %/tr < koszt 0,08 % (wniosek 90). Seria zamknięta STOP. DO DECYZJI: wolniejszy horyzont
> (nowa hipoteza).**
> SKILL (2026-09-24): `quant-strategy-catalog` — nowa wersja ze statusami po P3/AU1/SW/X1F/RU3 (wnioski 1–90, nowa sekcja C2
> „popyt spoza Binance”, J1 „trend poza krypto”, „Stan po SW”); paczka w Pobranych, obowiązuje po wgraniu na claude.ai.**
> SERWER (2026-09-24, decyzja użytkownika): praca badawcza przenosi się na serwer Linux w Polsce. Przygotowanie:
> `git clone`, `bash tools/setup_serwer.sh <data_raw.zip>` (venv z `requirements-lock.txt`, `py`, dane, test Binance),
> `py -m pytest -q`, `/skills` (czy są skille konta), `git pull` przed każdą rundą. Preferencje użytkownika —
> `docs/rag/10`. Dziennik zostaje na komputerze (Harmonogram 02:30, osobny klon `alpha-dziennik`, 3 próby co 30 min)
> i od poprawki 5 sam commituje i wypycha wyniki (przegląd 16c: 10 znalezisk potwierdzonych, poprawione, testy);
> DZIENNIK → SERWER (2026-09-24, decyzja użytkownika): kopia i dostęp na serwerze gotowe; po wpisie crona serwer
> liczy co noc, a komputer oddaje dziennik SAM (`dziennik/przejete.sh`: zapis innej maszyny w ostatnich 3 dniach →
> wyłączenie zadania na komputerze). Commit dziennika podaje nazwę maszyny. Praca badawcza — tylko na serwerze.
> SERWER (2026-09-25): `.venv` badawczy przebudowany z `requirements-lock.txt` (był sprzed skryptu: XGBoost 3.4 → 3.2);
> autor commitów ustawiony lokalnie w obu klonach (jego brak dał 24.09 „commit nieudany” w próbie dziennika). Pierwszy
> przebieg dziennika na serwerze 2026-09-25 (`dantey1`); komputer nadrobił ten sam dzień 13 s wcześniej — wyniki
> identyczne, bez duplikatów. Cron na serwerze dodany przez użytkownika (`30 2 * * *`, czas UTC) — od następnej nocy dziennik liczy serwer.
> Claude Code na serwerze uruchamiać w `tmux` (zerwanie SSH kończy sesję i Remote Control).
> KP1 (2026-09-25): premia koreańska (Upbit) — **NIEMIERZALNA, 0 wariantów, zysków nie liczono**: sygnał inny niż CP1
> (zgodność 52,8 %), ale efekt z badań SR ~0,15 wobec progu przyrządu 0,86 (moc 5 %). Wniosek 91.
> AU2 krok 0 (2026-09-25, projekt użytkownika): przyrząd przekrojowy top-50 widzi rank IC ≥ 0,022 (~18 niezależnych
> zakładów po odjęciu rynku); na IR 0,75 trzeba IC ~0,025 → ML przekrojowe nie wykluczone. **DO DECYZJI:** karta kroków 1–2
> (`runs/2026-09-25_au2-moc-przekrojowa/karta_krokow_1_2.md`): zbiór cech, budżet przeszukiwania, drugi warunek werdyktu. Wniosek 92.
> AU2 kroki 1–2 (2026-09-25, decyzje użytkownika): ML przekrojowe uczciwe (0/40 fałszywych), ale moc przy +10/15 %/rok
> 25/35 % (ranking po właściwej cesze 80/85 %) → **nie startuje**. Wniosek 93. **DO DECYZJI: błąd kanonicznego N_eff**
> (`agents/labeling.py::effective_sample_size`, suma autokorelacji < −0,5 → N_eff = 1 / NaN; tylko zaniża pewność) —
> naprawa + runda audytu AU3 dawnych „nierozstrzygniętych”; dotyka metodologii i modułu importowanego pośrednio przez dziennik.
> AU3 (2026-09-25, decyzja użytkownika „tak”): N_eff naprawiony w `agents/labeling.py`; audyt 59 przebiegów — **0 zmienionych
> werdyktów** (zdarzenia tylko w K2/K3, bez wpływu). Poprawka 6 dziennika (bez wpływu). Wniosek 94.
> KR1 (2026-09-25): korelacje nóg TS1/X1/CP1 tyg. 0,35 / 0,24 / 0,16, w złych dniach niższe — portfel dywersyfikuje (wniosek 95).
> DZIENNIK Poprawka 7 (2026-09-25, zgoda użytkownika): `dziennik/stan_rynku.csv` — zamrożona etykieta (tercyl zmienności 30 d BTC,
> znak trendu 90 d), tylko zapis; odczyt „który składnik w jakich warunkach” po 6–12 miesiącach.
> AU4 (2026-09-25): deflated Sharpe CP1 = 0,52 przy N = 28 prób — po korekcie nieodróżnialny od szczęścia; tylko dziennik rozstrzygnie (wniosek 96).
> RU4 (2026-09-25): TL1 na pełnych danych OI +8,1 %/rok, t 0,62 — nadal nierozstrzygnięty, znak odwrócony (szum); luka danych z RU2 zamknięta (wniosek 97).
> P4 (2026-09-25): darmowe on-chain pokrywa 4–46 % koszyka (przepływy tylko BTC/ETH) — ranking on-chain niewykonalny; **DO DECYZJI:** czy sprawdzać płatnych dostawców (wniosek 98).
> SERWER: ciężkie przebiegi z `OMP_NUM_THREADS=1` i ≤ 24 procesami (bez tego przeciążenie ~15× i ryzyko dla walidatora).
> BACKLOG: `black --check .` czerwony na 15 starych plikach (9 zamrożonych poza `extend-exclude`) — do porządków.**
> Dalsze kierunki — §17, ETAP 4 i `runs/INDEX.md`.**
>
> *(Poprzednia treść tego nagłówka — stan z 2026-08-01, „Commity 1–6, 86/86 testów, następny
> krok: decyzja o Commit 2b" — była nieaktualna od serii C2.5; poprawiona w porządkach
> 2026-09-22.)*

---

## 1. Cel i zasada nadrzędna

Oryginalny PRD (CLAS-5, system 5-agentowy do tradingu BTC/ETH perpetual futures) zakładał, że
wszystkie wymagania funkcjonalne — autonomia, Compliance Gate, kill-switch, audytowalność,
dashboard — budowane są równolegle jako gotowa architektura.

**Zasada, którą stosujemy zamiast tego:** nic z Części II PRD (5 agentów, dashboard, Docker) nie
jest budowane, dopóki Faza 0 nie udowodni empirycznie, że istnieje jakikolwiek edge statystyczny
po kosztach transakcyjnych. Architektura bez potwierdzonej hipotezy to precyzyjnie zbudowany
system do tracenia pieniędzy.

---

---

## 2. Co zmienia się względem oryginalnego PRD

| Element PRD | Problem | Zmiana |
|---|---|---|
| Autonomia od startu | Brak zdefiniowanego edge'u | Faza 0-1 dowodzi edge najpierw, agenci potem |
| LLM w pętli decyzyjnej (150ms) | Wywołanie API LLM to sekundy, nie ms | LLM tylko offline/nadzorczo (recenzja modeli, raporty post-trade) |
| "100% lokalne" + API LLM | Sprzeczność | Hot-path w 100% lokalny; LLM poza hot-pathem |
| 100% pokrycia testami | Nie mówi nic o poprawności finansowej | Property-based testing konkretnych właściwości (leakage, VaR) |
| Multi-repo feature extraction | Ryzyko niekonsystencji + leakage | Jedna biblioteka (TA-Lib), każda cecha przepisana i przetestowana osobno |
| Regime/sizing jako coś do "wyuczenia" | Zużywa ograniczony budżet statystyczny, trudne do audytu | Reguły deterministyczne na start; ML tam, gdzie faktycznie się opłaca (patrz §8) |

---

---

## 3. Hipoteza tradingowa

**Regime-gated: dwie sprzeczne tezy, rozdzielone regułą, nie połączone w jednym modelu.**

- **Test 1 — Momentum:** w reżimie "trend" (wysoka zmienność + wysoka persystencja kierunku),
  cena kontynuuje ruch.
- **Test 2 — Mean-reversion:** w reżimie "range" (niska zmienność + oscylacja), cena wraca do
  średniej po przegrzaniu.
- **Regime gate:** reguła deterministyczna (nie model), bo (a) w 100% audytowalna dla Compliance
  Gate, (b) nie zużywa dodatkowego budżetu statystycznego z już ograniczonej efektywnej liczby
  próbek.
- **Funding rate:** kandydat na cechę do Test 2 w Fazie 1 — mechanistycznie pasuje do tezy
  "przegrzane pozycjonowanie → odwrócenie". Nie w Fazie 0.
- Test 1 i Test 2 przechodzą przez **cały pipeline osobno** — własny leakage test, własny
  walk-forward, własny go/no-go. Router łączący je to Faza 1, warunkowa na tym, że przynajmniej
  jeden test przejdzie.

---

---

## 4. Struktura projektu (stan docelowy Fazy 0)

```
clas5_core/
├── README.md                     [DONE] — wejście do repo dla ludzi (GitHub)
├── CLAUDE.md                     [DONE] — krótkie, stabilne instrukcje dla Claude Code
├── IMPLEMENTATION_PLAN.md        ← ten dokument (status commitów, zmienia się często)
├── .github/
│   └── workflows/
│       └── tests.yml              [DONE] — minimalne CI: pytest + spójność registry/kod
├── docs/
│   └── rag/                      [DONE] — pełne uzasadnienia decyzji, per temat
│       ├── 01_hipoteza_i_architektura.md
│       ├── 02_cechy_i_leakage.md
│       ├── 03_ryzyko_i_sizing.md
│       ├── 04_narzedzia_zewnetrzne.md
│       └── 05_metodologia_wytwarzania_i_testow.md
├── requirements.txt              [DONE]
├── config/
│   └── settings.yaml             [DONE]
├── data/
│   ├── __init__.py                [DONE]
│   ├── fetch_ohlcv.py             [DONE]
│   └── raw/                       (cache parquet, generowany przy pierwszym uruchomieniu)
├── agents/
│   ├── __init__.py                 [DONE]
│   ├── feature_miner.py            [DONE]
│   ├── feature_registry.yaml       [DONE]
│   ├── labeling.py                  [DONE, 14/14 testów przechodzi (13 w tests/test_labeling.py + 1 leakage w agent_5_compliance/)]
│   ├── ml_optimizer.py              [DONE, 8/8 testów przechodzi (tests/test_ml_optimizer.py)]
│   └── risk_controller.py           [DONE, 17/17 testów przechodzi (tests/test_risk_controller.py)]
├── agent_5_compliance/
│   └── test_leakage.py              [DONE, 12/12 testów przechodzi]
├── backtest/
│   ├── __init__.py                  [DONE]
│   ├── engine.py                    [DONE, 3/3 testów przechodzi (tests/test_engine.py)]
│   └── costs.py                     [DONE, 7/7 testów przechodzi (tests/test_costs.py)]
└── tests/
    ├── __init__.py                  [DONE]
    ├── test_fetch_ohlcv.py          [DONE, 6/6 testów przechodzi]
    ├── test_labeling.py             [DONE, 13/13 testów przechodzi]
    ├── test_ml_optimizer.py         [DONE, 8/8 testów przechodzi]
    ├── test_costs.py                [DONE, 7/7 testów przechodzi]
    ├── test_engine.py               [DONE, 3/3 testów przechodzi]
    └── test_risk_controller.py      [DONE, 17/17 testów przechodzi]
```

---

---

## 5. Plan Fazy 0 — commit po commicie

### Commit 1 — Dane `[ZROBIONE]`

`data/fetch_ohlcv.py` — pobieranie OHLCV z Binance USDS-M Futures (perpetuals, nie spot) przez
ccxt, z paginacją i cache w parquet.

- Zakres: **BTCUSDT, 5m, 2025-07-01 → 2026-07-01** (ostatnie ~12 miesięcy). Jeden instrument,
  jeden timeframe.
- `find_gaps()` — raportuje dziury w danych, nie blokuje pipeline'u (fault tolerance z PRD).
- **DO ZROBIENIA PRZED PIERWSZYM URUCHOMIENIEM:** zweryfikować dokładny symbol ccxt przez
  `exchange.load_markets()`. W kodzie jest `"BTC/USDT:USDT"` jako założenie — sandbox, w którym
  to pisałem, nie ma dostępu do API giełdy, więc to nie jest potwierdzone na żywo.

### Commit 2 — Feature registry `[ZROBIONE]`

`agents/feature_miner.py` + `agents/feature_registry.yaml` — 9 czystych funkcji +
`classify_regime()` + `split_by_regime()`.

| Cecha | Wzór | Rola |
|---|---|---|
| `atr_14` | ATR, Wilder, 14 (TA-Lib) | baza |
| `atr_pctrank_20d` | percentyl `atr_14` w trailing 20 dniach (5760 świec) | regime_filter |
| `direction_persistence_10` | \|Σsign(return)\|/10, ostatnie 10 świec | regime_filter |
| `return_lag_1` | ln(close_t/close_t-1) | signal, shared |
| `momentum_5` | ln(close_t/close_t-5) | signal, trend |
| `ema_diff_9_21` | (EMA9-EMA21)/close_t | signal, trend |
| `volume_zscore_20` | (volume-mean20)/std20 | signal, shared |
| `rsi_14` | RSI, Wilder, 14 (TA-Lib) | signal, range |
| `price_zscore_20` | (close-mean20)/std20 | signal, range |

**Regime rule (startowa, do kalibracji):**
```
trend:    atr_pctrank_20d > 0.7  AND  persistence > 0.7
range:    atr_pctrank_20d < 0.3  AND  persistence < 0.3
inaczej:  ambiguous → wyklucz z obu testów
```

### Commit 3 — Test leakage `[ZROBIONE]`

`agent_5_compliance/test_leakage.py` — formalny, parametryzowany pytest dla wszystkich 9 funkcji.

- Metoda: policz cechę na `df[:T]` i `df[:T+k]`, sprawdź identyczność do T.
- **Priorytet:** `atr_pctrank_20d` — największe ryzyko (rolling window musi być trailing, nie
  centered) — pokryty dodatkowym dedykowanym testem (mutacja świec po punkcie odcięcia).
- Nieformalna wersja tego testu już przeszła 9/9 na syntetycznych danych — formalny pytest
  (11 testów: 9 parametryzowanych + 1 dedykowany dla `atr_pctrank_20d` + 1 sanity na zestaw
  cech) potwierdza to empirycznie, 11/11 przechodzi lokalnie.

### Commit 4 — Target + walk-forward split `[ZROBIONE — poza C4.6, odłożone do Commit 5]`

`agents/labeling.py`

**Triple-barrier, ATR-scaled** (nie forward return — odwzorowuje faktyczny mechanizm wyjścia,
zgodny z risk_controllerem):
```
upper barrier:    entry + 1.5 × atr_14
lower barrier:    entry − 1.5 × atr_14
vertical barrier: 12 świec (1h) — timeout
label: która bariera trafiona pierwsza → +1 / −1 / 0
```
Symetryczne progi na start w obu testach (asymetria to Faza 1). Ten sam mnożnik `1.5×ATR` jak w
stop-lossie risk_controllera (Commit 5.5) — musi być skonsystentny.

**Walk-forward split:** okno 2 miesiące train / 2 tygodnie test, przesuwane co 2 tygodnie → ok.
kilkanaście foldów na 12 miesiącach danych. Chronologiczny split ZAWSZE, nigdy random.

**Diagnostyka efektywnej liczby próbek** (nie blokuje, tylko informuje interpretację wyniku z
Commitu 6):
```
policz autokorelację return_lag_1 do lag ~50
N_eff ≈ N / (1 + 2·Σρ_k)
```

**Zaimplementowane i zweryfikowane empirycznie:** `compute_triple_barrier_labels` (reużywa
`compute_atr_14` z `feature_miner.py`, nie duplikuje), `generate_walk_forward_folds`,
`effective_sample_size` — 14/14 testów przechodzi (7 scenariuszy triple-barrier + 3 walk-forward
+ 2 N_eff w `tests/test_labeling.py`, + 1 hypothesis property test wymagany przez DoD dla
`labeling.py`, + 1 formalny test leakage w `agent_5_compliance/test_leakage.py` — C4.5). Mnożnik
ATR i vertical barrier są teraz jedynym źródłem prawdy w `config/settings.yaml` sekcja
`labeling` (C4.2), które `risk_controller.py` będzie musiał czytać w Commicie 5.5. **C4.6
(koszt obliczeniowy pełnego tuningu) celowo NIE zrobione teraz** — wymaga realnych
hiperparametrów XGBoost (Commit 5) do sensownego pomiaru; przeniesione tam.

### Commit 5 — Dwa modele, osobno `[ZROBIONE]`

`agents/ml_optimizer.py`

- **Dwa niezależne XGBoosty**: `model_momentum` (dane Test 1 — świece "trend"),
  `model_reversion` (dane Test 2 — świece "range"). Żadnego wspólnego modelu na tym etapie.
- Start: `max_depth=4`, `learning_rate=0.05`, `n_estimators=200`, `early_stopping_rounds=20` na
  foldzie OOS (nigdy na train).
- Output: `predict_proba`, nie tylko klasa — potrzebne jako `signal_confidence`.
- Okna wskaźników kalibrowane WEWNĄTRZ walk-forward, nigdy na całym zbiorze na raz.

`backtest/costs.py` — taker fee Binance Futures (~0.04–0.05%), funding rate (średnia
historyczna), slippage jako stały bps.
`backtest/engine.py` — pętla: sygnał → risk_controller → PnL z kosztami → equity curve.

**Zaimplementowane i zweryfikowane empirycznie:** `agents/ml_optimizer.py::train_regime_model`
(natywne `xgboost.train()`/`DMatrix`, nie sklearn-wrapper) + `predict_signal` (argmax +
confidence z `predict_proba`, tylko drzewa do `best_iteration`) — 8/8 testów przechodzi
(`tests/test_ml_optimizer.py`). `backtest/costs.py` (fee/funding/slippage, wartości startowe
teraz też w `config/settings.yaml` sekcja `costs`) — 7/7 testów przechodzi
(`tests/test_costs.py`). `backtest/engine.py::run_backtest` — pełny pipeline cechy→labels→
regime→walk-forward→trening/predykcja→sizing→koszty→equity curve — 2/2 testy integracyjne
przechodzi (`tests/test_engine.py`, syntetyczny OHLCV z jawnie odseparowanymi segmentami
trend/range, bo czysto losowe dane dają regime="range" dużo częściej niż "trend", C2.5).

**Decyzja — `_placeholder_risk_controller` (tymczasowy, w `backtest/engine.py`) — ZASTĄPIONY w
Commicie 5.5:** `agents/risk_controller.py` to osobny Commit 5.5 (kontrakt formalny + kill-switch
+ hypothesis property testy, wymagane DoD). Ponieważ `run_backtest` potrzebował jakiegoś sizingu,
żeby policzyć PnL już w Commicie 5, `_placeholder_risk_controller` implementował TĘ SAMĄ formułę
z `docs/rag/03_ryzyko_i_sizing.md` (`size_risk`/`size_leverage`/`min()` + `signal_confidence`
skalujące `risk_per_trade`) — wstrzykiwany przez parametr `risk_controller_fn`. W Commicie 5.5
ten placeholder został usunięty, a `risk_controller_fn` domyślnie wskazuje na prawdziwy
`agents.risk_controller.compute_sizing` — bez żadnej zmiany w pętli `run_backtest`, dokładnie
jak planowano.

**Decyzja — brak modyfikacji `agents/labeling.py`:** PnL wymaga ceny wyjścia z pozycji; dla
timeoutów (label=0.0) to lookup do `close` w świecy `t + exit_bar_offset` w PEŁNYM df.
`agents.feature_miner.split_by_regime()` robi `reset_index(drop=True)`, co gubi tę możliwość —
`backtest/engine.py` świadomie NIE wywołuje `split_by_regime()`, filtruje reżim własnym boolean
maskiem zachowującym oryginalny index (plus defensywny `reset_index(drop=True)` na starcie
`run_backtest`, żeby zagwarantować czysty `RangeIndex`). Zero zmian w już scalonym Commicie 4.

**Decyzja — chronologia ponad reżimy:** modele trenowane per-regime per-fold niezależnie, ale
equity liczone w JEDNYM sekwencyjnym przebiegu po wszystkich sygnałach z obu reżimów, sortowanych
po `timestamp` — inaczej trades z trend/range (przeplatające się w czasie) dałyby błędną
chronologię compoundingu equity.

**C4.6 — pomiar częściowy (patrz TASKS.md):** jedno `train_regime_model` (produkcyjne
hiperparametry, 200 rund, early stopping wyłączony) na 30k wierszy × 4 cechy: **0.436s**
(~2.2ms/rundę) na Ryzen 7950X3D. Pełny grid search pozostaje niezmierzony — do zrobienia przy
faktycznej kalibracji hiperparametrów (Commit 6 / Faza 1).

### Commit 5.5 — Risk controller + interfejs `[ZROBIONE]`

`agents/risk_controller.py`

**Kontrakt (ml_optimizer → risk_controller):**
```
ml_optimizer emituje:
  { signal_direction: -1|0|1, signal_confidence: float,
    regime: "trend"|"range", atr_14: float, entry_price: float }

risk_controller zwraca:
  { position_size: float, stop_price: float, take_profit_price: float }
```

**Sizing (leverage cap zawsze wygrywa, jawnie):**
```
size_risk     = (equity × risk_per_trade) / (1.5 × atr_14)
size_leverage = (equity × max_leverage) / entry_price
position_size = min(size_risk, size_leverage)
```
- `risk_per_trade` = 0.5% equity (wartość startowa)
- `max_leverage` = 3x (wartość startowa, konserwatywnie)
- `signal_confidence` skaluje `risk_per_trade` liniowo (słabszy sygnał → mniejsza pozycja)

**Kill-switch:** prosta reguła już w backteście Fazy 0 — drawdown equity > X% od peaku →
zatrzymaj generowanie nowych sygnałów. Cel: zobaczyć historycznie, jak często by się aktywował.

**Zaimplementowane i zweryfikowane empirycznie:** `agents/risk_controller.py` — dwuwarstwowy
design: `compute_position_size` (czysty numeryczny rdzeń: `equity`, `atr_14`, `entry_price` →
`float`, matchuje dokładnie szablon hypothesis z `docs/rag/05_metodologia_wytwarzania_i_testow.md`)
+ `compute_sizing` (pełny kontrakt dict, drop-in replacement dla `risk_controller_fn` w
`backtest/engine.py::run_backtest`) + `check_kill_switch`. 17/17 testów przechodzi
(`tests/test_risk_controller.py`: 13 jednostkowych + 4 hypothesis property, w tym adaptacja
1:1 szablonu `test_position_size_never_exceeds_leverage_cap` z docs/rag/05).

**Trzy decyzje podjęte podczas planowania (zamiast rekomendowanych domyślnych wartości):**

1. **Próg kill-switcha = 15% drawdown od peaku equity** (nie rekomendowane 20%) —
   `KILL_SWITCH_DRAWDOWN_PCT = 0.15` w `agents/risk_controller.py`, zdublowane w
   `config/settings.yaml` sekcja `risk.kill_switch_drawdown_pct`. Konserwatywniejszy próg =
   kill-switch aktywuje się wcześniej, spójne z ogólnym duchem Fazy 0 (minimalizować ryzyko przed
   udowodnieniem edge'u).
2. **Re-check dynamiczny, nie permanentny latch** — `check_kill_switch` jest wywoływane PRZED
   sizingiem KAŻDEGO sygnału (nie tylko raz), więc kill-switch wznawia normalną pracę, gdy equity
   odzyska się z powrotem powyżej progu. Alternatywa (permanentny latch, wymagający ręcznego
   resetu) odrzucona — w Fazie 0 backtest ma pokazać, JAK CZĘSTO próg by się aktywował, a
   permanentny latch zniekształciłby ten pomiar (jedna aktywacja ubijałaby resztę okresu testowego).
3. **Sygnały stłumione przez kill-switch trafiają do `trades` DataFrame** (kolumna
   `kill_switch_active: bool`, `position_size=0.0`, `exit_price=NaN`, `equity_before==equity_after`)
   zamiast do osobnej listy `kill_switch_events` — jeden ustrukturyzowany trade journal, nie dwa
   równoległe źródła prawdy o tym, co działo się w czasie. Audytowalność: `trades[trades["kill_switch_active"]]`
   pokazuje dokładnie, kiedy i jak często kill-switch by się aktywował.

Integracja w `backtest/engine.py::run_backtest`: `peak_equity` (running max equity) śledzony w
pętli PRZED każdym sygnałem (bez lookahead — tylko przeszłość/teraźniejszość), `check_kill_switch`
sprawdzany przed wywołaniem `risk_controller_fn`. Nowy parametr `kill_switch_drawdown_pct`
(domyślnie `KILL_SWITCH_DRAWDOWN_PCT`) — nadpisywalny, analogicznie do innych parametrów silnika.
Dodatkowy test integracyjny `test_run_backtest_kill_switch_suppresses_signals_after_large_drawdown`
(`tests/test_engine.py`) — oversized stub `risk_controller_fn` (~50x normalnego stosunku
notional/equity, celowo ignorujący normalny cap 3x) deterministycznie wymusza drawdown > 15% bez
zależności od jakości predykcji modelu (gross_pnl i cost skalują się liniowo z position_size, więc
samo powiększenie position_size nie zmienia proporcji zysk/koszt — ale w połączeniu z choćby
jedną naturalnie występującą błędną predykcją kierunku daje duży wystarczający swing equity).

### Commit 6 — Checkpoint go/no-go: TRZY ścieżki `[ZROBIONE — wynik: NO-GO]`

| Wynik | Kryterium (startowe) | Decyzja |
|---|---|---|
| **GO** | Sharpe po kosztach > 0.5 w >60% foldów, zgodny znak | Faza 1: regime router + funding rate do Test 2 |
| **WARUNKOWY** | Sharpe 0–0.5 lub niestabilny znak między foldami | Max 3 iteracje protokołu "jedna cecha na raz", potem decyzja ponownie |
| **NO-GO** | Sharpe ≤ 0 w większości foldów | Wróć do Commit 2 — inna hipoteza/cechy, NIE tuning tego zestawu |

Sprawdzić też: stabilność wyniku przy losowym seedzie modelu (overfitting sanity check), wynik
osobno per reżim rynkowy (2023 niska zmienność vs 2024-25 era ETF).

**Metodologia (ustalona z użytkownikiem, brak w docs/rag — trzeba było doprecyzować przed
implementacją):** Sharpe per trade (risk-free=0, zwrot = net_pnl/equity_before, wyklucza
kill-switch), annualizacja `sqrt(trades_per_year)` z częstości transakcji per-fold (nie stała
globalna). C6.4 zinterpretowane jako podział wg REŻIMU (trend vs range), nie kalendarzowo —
realny zakres danych (2025-07→2026-07) nie sięga 2023. C6.3: 10 seedów (42-51), stabilny =
std zagregowanego Sharpe < 0.2. Implementacja: `backtest/metrics.py` (czyste funkcje, testy w
`tests/test_metrics.py`) + `backtest/run_checkpoint.py` (orkiestracja na realnych danych, poza
pytest).

**Wynik na realnych danych** (BTC/USDT:USDT 5m, Binance USDS-M Futures, 2025-07-01→2026-06-30,
105 120 świec, zero dziur — pierwsze rzeczywiste dane w tym projekcie, C1.3 potwierdzone przy
okazji):

- **C6.1/C6.2 — klasyfikacja ogólna: NO-GO.** Tylko 1 z 40 foldów (regime×fold_idx, 20 trend +
  20 range) miał policzalny Sharpe (≥2 transakcje, niezerowa wariancja): `range`, `fold_idx=0`,
  35 transakcji, Sharpe = **-65.43**. Pozostałe 39 foldów: NaN (brak transakcji albo fold
  pominięty przez `min_train_rows=30`).
- **C6.3 — stabilność:** 10 seedów (42-51) dały IDENTYCZNY mean_sharpe=-65.4333 na każdym
  (std=0.0000 < próg 0.2) → formalnie stabilne, ale głównie dlatego, że tylko ten jeden fold
  kiedykolwiek generuje transakcje i jego wynik okazał się w tym przebiegu niezależny od seeda
  modelu (płytkie drzewa, mały feature set — mało miejsca na wariancję od samego seeda).
- **C6.4 — per reżim:**
  - `trend`: **WARUNKOWY** w praktyce nieoceniony — WSZYSTKIE 20 foldów pominięte przez
    `min_train_rows`, bo 14-dniowe okno testowe konsekwentnie miało <30 świec sklasyfikowanych
    jako `trend` (typowo 6-29, patrz TASKS.md C6.1 Uwagi). To empiryczne potwierdzenie ryzyka z
    §7 ("regime trend może być rzadki"), nie nowe odkrycie — ale teraz na realnych danych, nie
    tylko syntetycznych.
  - `range`: **NO-GO** — model wygenerował sygnał tylko w 1 z 20 foldów; w pozostałych 19
    `predict_signal` zwracał wyłącznie `direction=0` (brak transakcji). **[BŁĘDNE — patrz korekta
    poniżej i Commit 2b.]**
- **Interpretacja (ważne dla decyzji o Commit 2):** Sharpe=-65.43 z pojedynczego foldu (35
  transakcji, mean_return/std_return≈-2.17 przed annualizacją) to artefakt małej próby — N_eff
  effektywnie bardzo mały (docs/rag/03 caveat), więc dosłowna wartość liczbowa niesie mało
  informacji. Bardziej wiarygodny sygnał to STRUKTURALNY: model `range` prawie nigdy nie handluje,
  a `trend` prawie nigdy nie ma wystarczających danych do wytrenowania/oceny w obecnej strukturze
  walk-forward. To sugeruje, że powrót do Commit 2 powinien objąć w szczególności C2.5 (kalibracja
  progów 0.7/0.3) i/lub przegląd feature setu pod kątem modelu `range`, a nie tylko "inne cechy"
  ogólnikowo — ostateczny zakres do ustalenia z użytkownikiem przed startem.
- **KOREKTA (Commit 2b, 2026-08-01):** oba powyższe zdania okazały się mylące co do przyczyny —
  sugerowały problem z modelem/cechami `range`. Diagnoza C2b.1/C2b.1b (patrz Commit 2b niżej)
  pokazuje, że `predict_signal` faktycznie zwraca `direction != 0` w ~99-100% wierszy testowych w
  KAŻDYM z 20 foldów `range` (nie tylko 1). Prawdziwa przyczyna "1/20 foldów z transakcjami" to
  kill-switch (`agents/risk_controller.py::check_kill_switch`), permanentnie stłumiony od
  2025-09-27 (3 dni w fold_idx=0) do końca datasetu (2026-06-30) po serii wczesnych strat.
  Rekomendacja "C2.5 i/lub przegląd cech `range`" z powyższego akapitu jest nieaktualna — patrz
  Commit 2b dla poprawionej rekomendacji zakresu.

### Commit 2b — Diagnoza NO-GO: przegląd cech modelu `range` `[ZAMKNIĘTE — przesłanka obalona w C2b.1; ścieżka przejęta przez C2c i serię C2.5–C2.13]`

> **Porządki 2026-09-22:** status „W TRAKCIE — zablokowane" był nieaktualny od sierpnia.
> C2b.1 pokazało, że przyczyną NO-GO był kill-switch (naprawiony w C2c), a nie cechy;
> C2b.2/C2b.3 (dodanie cechy do `range`) straciły przesłankę i nie zostaną wykonane —
> cechy `range` testowały później C2.7/C2.8, a Faza 0 zamknęła się w Z10.

**Kontekst i uzgodniony zakres (ustalony z użytkownikiem przed startem, 2026-08-01):** powrót do
Commit 2 ograniczony WYŁĄCZNIE do przeglądu/rewizji feature setu modelu `range`
(`REVERSION_FEATURES`) — jawnie WYKLUCZONE tej rundy: rekalibracja progów regime (C2.5) i zmiana
mnożnika ATR triple-barrier. Plan: (1) diagnoza przyczyny [C2b.1], (2) jeśli diagnoza wskaże na
niewystarczające cechy — dodać JEDNĄ kandydującą cechę [C2b.2], (3) ponowny checkpoint [C2b.3].

**C2b.1 — Diagnostyka (`backtest/diagnose_range_signal.py`, poza pytest, jak
`run_checkpoint.py`):** read-only skrypt reprodukujący dokładnie trening/predykcję
`backtest.engine._collect_candidate_signals` per fold `range` (te same domyślne
train/test/step_days, `train_regime_model`/`predict_signal`, seed=42), ale raportujący dodatkowo:
rozkład klas triple-barrier label (train/test), `booster.get_score(importance_type="gain")`, i
PEŁNY rozkład `signal_confidence` (nie tylko wiersze z `direction != 0`, w odróżnieniu od
`_collect_candidate_signals`, który je odrzuca).

**Wynik C2b.1 (nieoczekiwany):** model `model_reversion` sygnalizuje (`direction != 0`) w
~99-100% wierszy testowych w KAŻDYM z 20 foldów `range` (nie w 1 na 20, jak zapisano pierwotnie w
Commit 6) — łącznie 17 989 sygnałów spośród 17 989 wierszy testowych z policzalnym labelem.
Confidence umiarkowana, ale sensowna (~0.44-0.50, baseline losowy dla 3 klas = 0.33). Feature
importance (gain) niezerowa i zmienna między foldami dla wszystkich 4 cech (`rsi_14` najsilniejsza,
0.9-4.7 w zależności od foldu; `return_lag_1` najsłabsza, ale nigdy zero). Rozkład labeli
train/test w każdym foldzie sensownie zbalansowany (~45% +1, ~45% -1, ~9-13% timeout/0) — brak
strukturalnego problemu z brakiem zdarzeń +1/-1.

**Wniosek C2b.1:** model NIE jest wąskim gardłem. Hipoteza "cechy `range` są za słabe, model rzadko
sygnalizuje" — którą ta runda miała zweryfikować — jest FAŁSZYWA. Dodanie nowej cechy do
`REVERSION_FEATURES` (C2b.2) nie zaadresowałoby rzeczywistej przyczyny "1/20 foldów z
transakcjami" w Commit 6.

**C2b.1b — Weryfikacja rzeczywistego mechanizmu "0 transakcji":** bezpośrednia inspekcja
`run_backtest(raw_ohlcv, seed=42)["trades"]`/`["folds_summary"]` (ad hoc, bez zmian w kodzie
pipeline'u):
- `folds_summary` potwierdza C2b.1: KAŻDY z 20 foldów `range` ma dziesiątki-tysiące sygnałów
  kandydujących (`n_signals`, PRZED sizingiem/kill-switchem), od 71 (fold 9) do 1713 (fold 10).
- Łącznie **18 135** wierszy w `trades` (obie strategie/foldy razem) — z czego **18 100 (99,8%)**
  ma `kill_switch_active=True`, tylko **35** to realne transakcje (`kill_switch_active=False`) —
  dokładnie zgodne z liczbą "35 transakcji" zaraportowaną w Commit 6 dla `range` fold_idx=0.
- Kill-switch uruchamia się pierwszy raz **2025-09-27 01:55 UTC** — w fold_idx=0 dla `range`, ~3
  dni w 14-dniowe okno testowe tego foldu, po ok. 9-10 stratnych transakcjach pod rząd (każda
  -0,5% do -0,6% equity). Equity spada z 10 000 do **8469,93** (drawdown 15,30%, tuż nad progiem
  15%) i **zamraża się na tej wartości DO KOŃCA datasetu** (2026-06-30) — kill-switch pozostaje
  aktywny przez pozostałe ~9 miesięcy backtestu, bez jednego wyjątku.
- Mechanizm: `check_kill_switch` jest poprawnie bezstanowy i "dynamiczny" (nie permanentny latch —
  wznawia się, gdy equity wróci powyżej progu, zgodnie z docstringiem i C5.5.5). Problem to
  DEADLOCK EMERGENTNY z interakcji z resztą pętli `run_backtest`: gdy sygnał jest stłumiony,
  `position_size=0.0` → `net_pnl=0.0` → equity się NIE zmienia → `peak_equity` też się nie zmienia
  → drawdown zostaje dokładnie tam, gdzie było w momencie stłumienia. Equity może wrócić ponad próg
  WYŁĄCZNIE dzięki realnej transakcji — a realna transakcja jest właśnie tym, co jest stłumione.
  W obecnej architekturze Fazy 0 (brak mark-to-market otwartych pozycji, brak żadnego innego
  źródła ruchu equity) ten deadlock jest matematycznie nieunikniony, gdy tylko drawdown raz
  przekroczy próg wystarczająco wcześnie w backteście.
- Osobne, jeszcze niezbadane pytanie: DLACZEGO pierwsze ~9-10 transakcji `range` fold 0 straciło
  tak konsekwentnie (jakość sygnału na starcie datasetu, koszty transakcyjne, formuła sizingu,
  czy zbieg okoliczności) — to POZA zakresem tej rundy (tylko przegląd cech), zostawione jako
  input do decyzji poniżej.

**Status i decyzja wymagana:** C2b.2 (dodanie cechy) WSTRZYMANE — jego przesłanka jest obalona
przez C2b.1/C2b.1b. Wymagana NOWA decyzja z użytkownikiem o zakresie dalszej pracy — prawdopodobnie
dotyczy `agents/risk_controller.py` (mechanizm odzyskiwania kill-switcha i/lub formuła sizingu
powodująca wczesną serię strat), co jest OSOBNYM zakresem od "przeglądu cech modelu `range`"
uzgodnionego na tę rundę i wymaga własnego przeczytania docs/rag/03 przed jakąkolwiek zmianą
(CLAUDE.md, sekcja "Zanim zmienisz coś w risk_controller.py"). Diagnostyczny skrypt
`backtest/diagnose_range_signal.py` zachowany jako trwałe narzędzie (nie jednorazowy scratch) —
przydatny niezależnie od tego, jaki zakres zostanie wybrany dalej.

### Commit 2c — Kill-switch: przyczyna serii strat + mechanizm cooldown/re-arm `[ZROBIONE]`

**Kontekst i uzgodniony zakres (2026-08-01):** użytkownik zatwierdził ("1.yes 2.yes") rozszerzenie
zakresu na `agents/risk_controller.py`/`backtest/engine.py`, jedną rundą: (1) diagnoza PRZYCZYNY
wczesnej serii strat wywołującej kill-switch, (2) naprawa mechanizmu deadlocka. Wybór konkretnego
mechanizmu naprawy delegowany do decyzji inżynierskiej ("tak jak uważasz za najlepsze"). Przeczytano
`docs/rag/03_ryzyko_i_sizing.md` w całości przed zmianą (CLAUDE.md) — potwierdzono, że kill-switch
Fazy 0 ma cel WYŁĄCZNIE obserwacyjny ("zobaczyć historycznie, jak często by się aktywował") i docs
NIE przepisują żadnego konkretnego mechanizmu odzyskiwania — to była faktycznie otwarta przestrzeń
projektowa, nie nadpisanie istniejącej decyzji.

**C2c.1 — Diagnostyka przyczyny serii strat (`backtest/diagnose_kill_switch_trigger.py`, poza
pytest, jak `run_checkpoint.py`/`diagnose_range_signal.py`):** read-only skrypt inspekcji 35
realnych transakcji sprzed permanentnego zadziałania kill-switcha — rozbija zlumpowany koszt
(`cost`) z powrotem na `fee`/`funding`/`slippage`, klasyfikuje każdą transakcję jako
`gross_pnl_negative` (zły kierunek) albo `cost_ate_gain` (dobry kierunek, ale koszt > zysk brutto).

**Wynik C2c.1:** 100% z 35 transakcji miało `signal_direction=1.0` (wyłącznie long) w okresie
2025-09-24→2025-09-27, gdy cena BTC trendowała W DÓŁ (~113 047→~109 400, ok. -3,6%), sklasyfikowanym
jako reżim `range`. **26/35 (74%)** miało `gross_pnl < 0` (genuinie zły kierunek — model obstawiał
long podczas trwałego spadku). **9/35** miało `gross_pnl >= 0`, ale koszt transakcyjny (~28-38 na
transakcję) przewyższał zysk brutto (~21-23) — też netto ujemne. Średni koszt jako % nominału:
fee≈0,100%, funding≈0,0004%, slippage≈0,040%, razem≈0,140%.

**Wniosek C2c.1:** kill-switch NIE działał wadliwie — poprawnie wykrył realną, trwałą serię strat.
Głębsza przyczyna (dlaczego model konsekwentnie obstawiał long podczas trwałego spadku
sklasyfikowanego jako `range`, i dlaczego zyski były mniejsze niż koszty) to osobne pytanie o
jakość sygnału/klasyfikację reżimu — jawnie POZA zakresem tej rundy (wymagałoby C2.5 albo rework
modelu/cech, oba explicite wykluczone z wcześniejszych ustaleń).

**C2c.2 — Mechanizm naprawy deadlocka (decyzja inżynierska, delegowana przez użytkownika):**
**cooldown/re-arm** — `backtest.engine.run_backtest` śledzi `kill_switch_tripped_at` (moment
pierwszego nieprzerwanego zadziałania) i po `kill_switch_cooldown_days` (nowy parametr, domyślnie
**7.0**, `agents.risk_controller.KILL_SWITCH_COOLDOWN_DAYS`, zdublowany w `config/settings.yaml`)
ciągłej suppresji resetuje `peak_equity` do bieżącego (zamrożonego) equity, dając strategii kolejną
szansę. `check_kill_switch` sam w sobie NIE zmienia się (nadal czysty/bezstanowy) — decyzja "czy
już czas na re-arm" wydzielona jako osobna czysta, testowalna funkcja
`agents.risk_controller.should_rearm_kill_switch(kill_switch_tripped_at, current_timestamp,
cooldown_days)`, wywoływana z pętli `run_backtest` PRZED `check_kill_switch` w każdej iteracji.
Odrzucone alternatywy: mark-to-market otwartych pozycji (zbyt duża zmiana architektury Fazy 0 na tę
rundę), zmiana formuły sizingu (nie adresuje deadlocka, tylko wielkość pojedynczej straty).

**Testy (DoD, docs/rag/05):** `tests/test_risk_controller.py` — 4 testy jednostkowe + 3 hypothesis
property tests dla `should_rearm_kill_switch` (m.in. `kill_switch_tripped_at=None` → zawsze False
niezależnie od pozostałych argumentów; dla dowolnego `cooldown_days`+`extra_days>=0` → zawsze True;
dla dowolnego elapsed < cooldown_days → zawsze False). `tests/test_engine.py` — nowy integracyjny
`test_run_backtest_kill_switch_re_arms_after_cooldown` (oversized `risk_controller_fn` wymusza trip
deterministycznie, `kill_switch_cooldown_days=0.01` wymusza szybki re-arm, asercja że przynajmniej
jedna PÓŹNIEJSZA transakcja ma `kill_switch_active=False`). Pełny zestaw: **94/94 przechodzi**.

**C2c.3 — Ponowny checkpoint po naprawie (`backtest/run_checkpoint.py`, realne dane, domyślny
`kill_switch_cooldown_days=7.0`):**

| Metryka | Przed (Commit 6/2b, deadlock) | Po (Commit 2c, cooldown/re-arm, seed=42) |
|---|---|---|
| Range: foldy z policzalnym Sharpe | 1/20 | **20/20** |
| Range: łączna liczba realnych transakcji | 35 | **2 562** (34–272/fold) |
| Range: mean_sharpe | -65,43 (1 fold) | **-53,41** |
| Range: fraction_le_zero | 1,0 (1/1) | **1,0 (20/20)** |
| Trend: foldy z policzalnym Sharpe | 0/20 (WARUNKOWY — brak danych) | **3/20** |
| Trend: łączna liczba realnych transakcji | 0 | **63** |
| Trend: mean_sharpe | NaN | **-7,15** |
| Klasyfikacja ogólna (`classify_checkpoint`) | NO-GO (1/40 foldów ważnych) | **NO-GO (23/40 foldów ważnych, mean_sharpe=-47,38)** |
| Stabilność między 10 seedami (42-51) | stabilne, ale n=1 fold | **stabilne — identyczny mean_sharpe=-47,3774, std=0,0000 na WSZYSTKICH 10 seedach, teraz na 23/40 foldach ważnych** |

**Wniosek C2c.3:** naprawa deadlocka NIE zmienia werdyktu (nadal NO-GO), ale czyni go dużo bardziej
wiarygodnym — zamiast 1 foldu z 35 transakcjami, teraz WSZYSTKIE 20 foldów `range` handlują (2 562
transakcji łącznie), wszystkie ze średnim Sharpe głęboko ujemnym (-53,41, fraction_le_zero=1,0) i
identycznym wynikiem między 10 seedami modelu. To potwierdza (nie tylko sugeruje, jak poprzednio na
próbie n=1 fold), że model `range` ma systematycznie ujemny edge po kosztach na całym datasecie, nie
tylko w jednym oknie. `trend` przeszedł z "brak danych" (0/20) do 3/20 foldów z realnymi
transakcjami — też ujemny (-7,15), ale wyraźnie mniej negatywny niż `range`, i wciąż zbyt mało
foldów, żeby cokolwiek stanowczo wnioskować o `trend` osobno.

**Status:** ZROBIONE — mechanizm zaimplementowany, przetestowany (94/94), zweryfikowany na realnych
danych. Otwarta decyzja z użytkownikiem: czy następna runda skupia się na jakości sygnału/
klasyfikacji reżimu (C2.5 — rekalibracja progów 0.7/0.3, ujawniona przez C2c.1 jako prawdopodobna
przyczyna 100%-long-only podczas spadku sklasyfikowanego jako `range`) — POZA zakresem tej rundy, do
ustalenia osobno.

### Commit 2d — Bramka wykonalności kosztowej `[ZROBIONE]`

**Kontekst i uzgodniony zakres (2026-09-21):** runda miała być C2.5 (rekalibracja progów regime).
Przed jej rozpoczęciem wykonano read-only diagnostykę, która obaliła przesłankę — i użytkownik
zatwierdził zmianę zakresu na bramkę wykonalności kosztowej, z C2.5 przesuniętym na osobną,
następną rundę (jedna zmiana na raz, CLAUDE.md zasada 4). Przeczytano `docs/rag/03_ryzyko_i_sizing.md`
i `docs/rag/05_metodologia_wytwarzania_i_testow.md` w całości przed zmianą (CLAUDE.md) — potwierdzono,
że docs NIE opisują żadnej bramki wykonalności kosztowej, więc jest to nowa przestrzeń projektowa,
nie nadpisanie istniejącej decyzji.

**C2d.0 — Diagnostyka (`backtest/diagnose_cost_feasibility.py`, poza pytest, jak
`run_checkpoint.py`/`diagnose_range_signal.py`/`diagnose_kill_switch_trigger.py`):** trzy bloki
read-only na realnych danych BTC/USDT:USDT 5m (2025-07→2026-07, 105 120 świec) — rozkład reguły
reżimu, porównanie szerokości bariery triple-barrier z kosztem round-trip, oraz dekompozycja
realnych transakcji na gross vs koszt.

**Wynik C2d.0 — trzy ustalenia, z których drugie przewraca dotychczasową diagnozę:**

1. **`direction_persistence_10` jest zmienną DYSKRETNĄ** — z definicji `|sum(sign(return))|/10`
   przyjmuje tylko wartości `k/10`. Realny rozkład: 0,0 → 26%, 0,2 → 42%, 0,4 → 22%, 0,6 → 7%,
   0,8 → 1,3%, 1,0 → 0,1%. Próg `trend_threshold=0.7` wpada w LUKĘ rozkładu (między 0,6 a 0,8),
   więc `trend` = 0,53% świec. To próg persistence, nie `atr_pctrank_20d`, czyni ten reżim prawie
   pustym — doprecyzowanie ryzyka z §7 i C2.5. Przesunięcie 0,7→0,5 daje `trend` = 4,53%. **Implikacja
   dla C2.5: progi nie są ciągłym pokrętłem — muszą snapować do osiągalnych wartości rozkładu.**
2. **W reżimie `range` bariera zysku jest WĘŻSZA NIŻ KOSZT.** Mediana `1.5×ATR` w `range` = **0,130%
   ceny** przy koszcie round-trip = **0,140% nominału** (2× taker 0,05% + 2× slippage 2 bps; funding
   ~0,0004%, pomijalny). Wymagana trafność kierunku na break-even, `p = 0.5*(1 + koszt/bariera)`,
   wynosi tam **103,9% — arytmetycznie nieosiągalna**. W **56,8%** świec `range` nawet PEŁNE
   trafienie bariery nie pokrywa kosztu. Dla porównania: `trend` = 68,2%, `ambiguous` = 77,5%.
3. **Model `range` MA edge kierunkowy** — trafiał kierunek w **54,6%** z 2 562 realnych transakcji
   Commitu 2c. Mimo to **42%** transakcji z POPRAWNYM kierunkiem kończyło netto pod kreską, łączny
   gross wyniósł **-569** przy koszcie **9 168** (net -9 737).

**Wniosek C2d.0:** NO-GO Commitu 2c był w ~94% wynikiem ARYTMETYCZNYM, nie statystycznym. Hipoteza
mean-reversion nie została uczciwie przetestowana — została przetestowana na oknach, w których nie
mogła wygrać. Sama rekalibracja progów (C2.5) nie zaadresowałaby tego: przesunęłaby tylko, które
świece nazywamy `range`, nie zmieniając faktu, że definicja reżimu (niski percentyl ATR) z
konstrukcji wybiera świece o najgorszym stosunku ruchu do stałego kosztu.

**C2d.1 — Mechanizm (`agents/risk_controller.py`):** czysta funkcja
`is_cost_feasible(atr_14, entry_price, cost_fraction, atr_multiplier, min_barrier_to_cost_ratio)`
(+ jej rdzeń `barrier_to_cost_ratio`) — sygnał wchodzi do gry tylko, gdy
`(atr_multiplier * atr_14) / entry_price >= min_barrier_to_cost_ratio * cost_fraction`. Wartość
startowa **`MIN_BARRIER_TO_COST_RATIO = 2.0`** (`config/settings.yaml` sekcja `risk`) wyprowadzona
z arytmetyki break-even `p = 0.5*(1 + 1/ratio)` — ratio 2.0 ⇒ wymagana trafność 75% — a NIE z
przeszukiwania po Sharpe (CLAUDE.md zasada 1). `cost_fraction` liczony przez nową
`backtest.costs.round_trip_cost_fraction()` z tych samych stałych co `total_round_trip_cost` (zero
duplikacji literałów, docs/rag/05) i przekazywany jawnie — `agents/` nie zależy od `backtest/`.

Decyzje projektowe:
- **Bramka filtruje KANDYDATURĘ sygnału (`backtest.engine._collect_candidate_signals`), nie trafia
  do trade journalu** — inaczej niż kill-switch. Kill-switch jest zdarzeniem zależnym od equity i
  historii, więc jego moment ma znaczenie w torze transakcji; bramka kosztowa jest deterministyczną
  właściwością POJEDYNCZEJ świecy, niezależną od equity. Licznik odrzuceń trafia do
  `folds_summary["n_signals_cost_gated"]`. Dzięki temu `backtest/metrics.py` nie wymaga ŻADNEJ
  zmiany ani nowego wyjątku w filtrze realnych transakcji.
- **To NIE jest próg odcięcia po `signal_confidence`** — docs/rag/03 świadomie odrzuca taki próg
  („słabszy sygnał, mniejsza pozycja, nie próg odcięcia"). Bramka jest ortogonalna: dotyczy
  geometrii bariera-vs-koszt, nie pewności modelu.
- **`atr_multiplier` nietknięty** — CLAUDE.md zasada 3 nienaruszona (bariera triple-barrier i
  stop-loss nadal dzielą tę samą stałą).
- **`min_barrier_to_cost_ratio=0.0` wyłącza bramkę** — używane przez testy sprzed Commitu 2d oraz
  do odtworzenia baseline'u Commitu 2c.

**C2d.2 — Testy (DoD, docs/rag/05):** 7 testów jednostkowych + 4 hypothesis property tests w
`tests/test_risk_controller.py` (zgodność bramki ze stosunkiem; monotoniczność niemalejąca w
`atr_14`; próg 0.0 przepuszcza wszystko; fail-safe dla `entry_price<=0`/`cost_fraction<=0`/NaN;
reprodukcja diagnozy reżimu `range`), 3 jednostkowe w `tests/test_costs.py`, 2 integracyjne w
`tests/test_engine.py` (bramka odcina sygnały i księguje je bez gubienia:
`n_signals_on + n_gated_on == n_signals_off`; bramka domyślnie WŁĄCZONA). Trzy testy sprzed Commitu
2d dostały jawne `min_barrier_to_cost_ratio=0.0` — ich przedmiotem jest kill-switch, a syntetyczny
segment `range` ma z konstrukcji wąską barierę. Pełny zestaw: **110/110 przechodzi** (94 + 16).

**C2d.3 — Ponowny checkpoint po bramce (realne dane, `min_barrier_to_cost_ratio=2.0`):**

| Metryka | Przed (Commit 2c) | Po (Commit 2d, seed=42) |
|---|---|---|
| Sygnały odrzucone przez bramkę | — | **17 547 z 18 135 (96,8%)** — w tym 17 537/17 989 (97,5%) w `range` |
| Foldy z policzalnym Sharpe | 23/40 | **6/40** (range 2/20, trend 4/20) |
| Realne transakcje | 2 625 | **358** (range 223, trend 135) |
| `mean_sharpe` (ogółem) | -47,38 | **-14,31** |
| Range: mean_sharpe | -53,41 | **-26,01** |
| Trend: mean_sharpe | -7,15 | **-8,46** (ale 25% foldów ma Sharpe > 0,5, wcześniej 0%) |
| Łączny gross | **-593** (range -569, trend -24) | **+166** (range +38, trend +128) |
| Łączny koszt | 9 354 | **2 953** |
| Trafność kierunku (range) | 54,6% | **49,3%** |
| Klasyfikacja | NO-GO | **NO-GO** |
| Stabilność (10 seedów, 42-51) | std=0,0000 | **std=0,0000 — identyczny mean_sharpe na wszystkich 10** |

Regresja kontrolna: `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c **co do ostatniej
cyfry** (`mean_sharpe=-47,377414474779975`, 23/40 foldów) — bramka jest jedyną zmianą zachowania.

**Wniosek C2d.3 — dwa wyniki, jeden dobry i jeden zły:**
- **Potwierdzone: strata BYŁA kosztowa.** Łączny gross przeszedł z **-593 na +166** — po odcięciu
  świec, na których wygrana była arytmetycznie niemożliwa, strategia przestaje tracić brutto.
  Diagnoza C2d.0 jest empirycznie potwierdzona, nie tylko prawdopodobna.
- **Nowe, niewygodne ustalenie: edge kierunkowy ZNIKA dokładnie tam, gdzie transakcja jest
  opłacalna.** Trafność w `range` spada z 54,6% (wszystkie świece) do **49,3%** (tylko świece
  przechodzące bramkę) — czyli te 54,6% mieszkało w świecach wąskobarierowych, niskozmiennych,
  na których i tak nie dało się zarobić. Na świecach szerokobarierowych model jest nieodróżnialny
  od rzutu monetą. Przy wymaganych 75% to przepaść, nie luka do zasypania tuningiem.
- **Werdykt pozostaje NO-GO**, ale jego PRZYCZYNA jest teraz inna i dużo lepiej określona: nie
  „koszty zjadają zysk", tylko „na świecach, gdzie koszt da się pokryć, model nie ma kierunku".

**Status:** ZROBIONE. Następna runda (uzgodniona z góry): **C2.5 — rekalibracja progów regime
wewnątrz walk-forward**, z uwzględnieniem dyskretności `direction_persistence_10` (C2d.0 pkt 1).
Otwarte pytanie do rozstrzygnięcia przy okazji: czy przy trafności ~49% na świecach opłacalnych
hipoteza w obecnym kształcie (5m, `REVERSION_FEATURES`) nie wymaga raczej zmiany horyzontu/cech niż
progów — patrz §7.

### Commit 2.5 — Kalibracja progów reguły regime `[ZROBIONE — wynik: NO-GO, hipoteza falsyfikowana]`

**Zakres:** sprawdzić, czy poluzowanie progów `classify_regime` (uwzględniając dyskretność
`direction_persistence_10`, C2d.0 pkt 1) usuwa/łagodzi NO-GO, bez zmiany żadnego innego elementu
pipeline'u (bramka kosztowa Commitu 2d pozostaje AKTYWNA, `min_barrier_to_cost_ratio=2.0`).

**C2.5.1 — Parametryzacja (`agents/feature_miner.py`, `backtest/engine.py`):**
`DEFAULT_TREND_THRESHOLD=0.7`/`DEFAULT_RANGE_THRESHOLD=0.3` jako nazwane stałe (mirroring
`config/settings.yaml` sekcja `regime_rule`, wzorzec `ATR_MULTIPLIER` z `agents/labeling.py`,
docs/rag/05 — zero magic numbers poza registry/configiem). `classify_regime` i
`compute_all_features` przyjmują `trend_threshold`/`range_threshold` jako parametry (domyślnie
te stałe); `run_backtest` przyjmuje i przekazuje je dalej, żeby skrypt kalibracyjny mógł
porównywać kandydatów przez dokładnie ten sam pipeline bez duplikacji logiki. Testy: 6 nowych
jednostkowych w `tests/test_feature_miner.py` (równoważność domyślne/jawne progi, rozłączność
trend/range, niezmienniki monotoniczności populacji względem progów, przekazanie progów przez
`compute_all_features` do kolumny `regime`) + 1 nowy integracyjny w `tests/test_engine.py`
(próg nieosiągalny 0.99 ⇒ zero sygnałów trend, weryfikacja end-to-end przekazania parametru przez
`run_backtest`). Pełny zestaw: **117/117 przechodzi**.

**C2.5.2 — Kalibracja (`backtest/calibrate_regime_thresholds.py`, poza pytest, jak inne skrypty
analityczne):** 4 kandydaci `(trend_threshold, range_threshold)`, wybrani z góry WYŁĄCZNIE ze
STRUKTURY formuły `persistence` (dyskretne wsparcie {0, 0.2, 0.4, 0.6, 0.8, 1.0}), nie z
podglądania Sharpe'a na tym zbiorze (CLAUDE.md zasada 1): `(0.7, 0.3)` baseline, `(0.6, 0.4)`
kontrola (przewidywanie: ta sama "luka" rozkładu co baseline), `(0.5, 0.3)` przecina pierwszą
granicę masy na osi trend, `(0.5, 0.5)` przecina granicę na obu osiach. Każdy oceniony przez
identyczny pipeline co Commit 6 (10-seedowy sweep stabilności, seed 42-51), bez automatycznego
wyboru zwycięzcy. Pełny wynik + surowy output: `runs/2026-09-21_c2.5-threshold-calibration/README.md`.

**Wynik C2.5.2:**

| trend_thr | range_thr | %trend | %range | mean_sharpe (seed=42) | klasyfikacja | stabilność (10 seed) |
|---|---|---|---|---|---|---|
| 0.7 | 0.3 (baseline) | 0.50% | 21.13% | **-14.31** | NO-GO | std=0,0000 |
| 0.6 | 0.4 | 0.63% | 27.72% | **-14.25** | NO-GO | std=0,0000 |
| 0.5 | 0.3 | 4.28% | 21.13% | **-18.00** | NO-GO | std=0,0000 |
| 0.5 | 0.5 | 4.28% | 44.18% | **-19.58** | NO-GO | std=0,0000 |

**Wniosek C2.5 — hipoteza CZĘŚCIOWO potwierdzona co do mechanizmu, ale FALSYFIKOWANA co do
wniosku:**
- Poluzowanie progów faktycznie zwiększa populację `trend` (0,50%→4,28%, 8,5×) — mechanizm
  działa zgodnie z diagnozą C2d.0.
- Kandydat kontrolny `(0.6, 0.4)` NIE odtworzył identycznej populacji co baseline — przewidywanie
  było błędne, bo `atr_pctrank_20d` jest CIĄGŁA: nawet przesunięcie progu w "luce" rozkładu
  `persistence` samo w sobie zmienia próg na drugiej, ciągłej osi reguły AND. Uczciwa korekta:
  "luka rozkładu" nie jest jedynym czynnikiem sterującym populacją regime.
- **Główny wynik: więcej świec `trend`/`range` = GORSZY wynik, nie lepszy.** `mean_sharpe`
  pogarsza się monotonicznie wraz z poluzowaniem progów (-14,31 → -14,25 → -18,00 → -19,58).
  Świece DODANE przez poluzowanie progu są NIE LEPSZEJ jakości niż te już objęte przy 0,7/0,3 —
  to odrzuca hipotezę, że "brakujące" (odrzucone jako `ambiguous`) świece kryją niewykorzystany
  edge, który regime rule przez pomyłkę odcina. Wszystkie 4 kandydatów: **NO-GO**, stabilnie.

**Status:** ZROBIONE. Zgodnie z regułą routingu checkpointu (docs/rag/03: NO-GO → powrót do
rejestru cech, NIE dalszy tuning tej samej reguły), **rekalibracja progów regime jest wyczerpana
jako kierunek — `config/settings.yaml` pozostaje przy baseline (0.7, 0.3)**, bo jest w
rzeczywistości najlepszym (najmniej ujemnym) z czterech przetestowanych wyników. Ciężar dowodu
dla otwartego pytania "dlaczego model `range` stawiał na long podczas trendu spadkowego" przesuwa
się z hipotezy (a) "zła kalibracja progów" (WYCZERPANA) na hipotezę (b) "model/cechy nie mają
edge'u" — patrz §7. Decyzja o następnym kroku (nowa cecha vs głębsza diagnoza modelu) należy do
użytkownika.

### Commit 2.6 — Odporność hipotezy na timeframe (1h, 4h) `[ZROBIONE — wynik: NO-GO, hipoteza falsyfikowana]`

**Zakres:** użytkownik zauważył, że cały pipeline (Commit 1-2.5) działał WYŁĄCZNIE na 5m, i że
pozycja jest trzymana max. 1h (12 świec 5m) — bardzo krótki horyzont względem stałego kosztu
transakcyjnego. Zapytał, czy wynik (NO-GO, Commit 2d/2.5) utrzymuje się na grubszych interwałach
(1h, 4h), gdzie bariera ATR-owa naturalnie rośnie względem kosztu. Uzgodniony zakres: PRZELICZYĆ
cały checkpoint na 1h i 4h, zmieniając WYŁĄCZNIE timeframe danych (+ `candles_per_day` jako
wymuszona konwersja jednostek, nie parametr hipotezy) — wszystko inne (progi 0.7/0.3,
`ATR_MULTIPLIER`, bramka kosztowa 2.0) niezmienione (CLAUDE.md zasada 1/4).

**Ograniczenie środowiska (odkryte przy starcie, nie wcześniej znane):** cloud sandbox nie ma
dostępu sieciowego do Binance (`fapi.binance.com` → `403 Forbidden` na poziomie proxy,
zweryfikowane przed startem). Natywny fetch 1h/4h przez `data.fetch_ohlcv.get_ohlcv_cached` był
więc niemożliwy — dane 1h/4h zostały zamiast tego **zagregowane z tego samego, zweryfikowanego
źródła 5m** przez nową funkcję `data.fetch_ohlcv.resample_ohlcv` (open/high/low/close/volumen,
odrzucanie niepełnych bucketów brzegowych; 7 nowych testów jednostkowych). To świadome
zastępstwo, jawnie odróżnione nazwą w dokumentacji od potencjalnego przyszłego natywnego fetcha —
pełne ograniczenia w docstringu funkcji.

**C2.6.1 — Kod:** `resample_ohlcv` (`data/fetch_ohlcv.py`, + testy w `tests/test_fetch_ohlcv.py`).
`candles_per_day` sparametryzowane przez `classify_regime`/`compute_all_features`/`run_backtest`
(ten sam wzorzec co progi w C2.5) — BEZ tego atr_pctrank_20d na 1h/4h liczyłby okno "20 dni" z
literałem 288 zakładającym 5m, co dałoby okno o BŁĘDNEJ długości kalendarzowej (np. przy 1h:
288*20=5760 świec = 240 dni zamiast 20). To poprawka jednostek, nie tuning. 4 nowe testy w
`tests/test_feature_miner.py` + 1 integracyjny w `tests/test_engine.py`. Pełny zestaw: **125/125
przechodzi** (117 + 8: 4 resample + 3 feature_miner + 1 engine).

**C2.6.2 — Skrypt (`backtest/checkpoint_timeframe_robustness.py`, poza pytest):** identyczny
pipeline co Commit 6/2c/2d/2.5, uruchomiony na 5m (referencja), 1h (8 760 świec), 4h (2 190
świec) — dokładny, bezresztowy podział z 105 120 świec 5m potwierdza brak przesunięcia
granic/dziur przy resample. Pełny wynik: `runs/2026-09-21_c2.6-timeframe-robustness/README.md`.

**Wynik C2.6.2:**

| timeframe | mean_sharpe (seed=42) | klasyfikacja | trend: n_valid_folds | stabilność (10 seed) |
|---|---|---|---|---|
| 5m (referencja) | -14,31 | NO-GO | 4/20 | std=0,0000 |
| **1h** | **-15,57** | NO-GO | **0/18** | std=0,0000 |
| **4h** | **-8,75** | NO-GO | **0/12** | std=0,0000 |

Diagnostyka uzupełniająca (metodologia Commitu 2d, powtórzona per timeframe) potwierdza, że
mechanizm bariera-vs-koszt **DZIAŁA jak przewidziano**: w `range` wymagana trafność break-even
spada z niemożliwych 103,9% (5m) do 61,2% (1h) i 54,4% (4h), a odsetek świec arytmetycznie
niewykonalnych z 56,8% (5m) do **0,0%** (1h i 4h). Mimo to trafność kierunku na realnych
transakcjach po bramce pozostaje na poziomie rzutu monetą: **49,0%** (1h) albo wypada GORZEJ:
**41,2%** (4h, systematycznie zły kierunek, nie tylko brak edge'u).

**Wniosek C2.6 — trzeci niezależny test wskazujący ten sam kierunek:** naprawienie stosunku
bariera/koszt (potwierdzone empirycznie) NIE przywraca edge'u kierunkowego. Hipoteza "problem
jest tylko kosztowy/za krótki timeframe" jest FALSYFIKOWANA — dokłada się do wniosku z C2.5
("problem jest w modelu/cechach, nie w kalibracji reguły regime czy granulacji danych").
Dodatkowo: regime `trend` staje się PRAKTYCZNIE PUSTY na 1h/4h (0 transakcji), bo
`direction_persistence_10` pozostał liczony na STAŁEJ liczbie 10 świec (świadoma decyzja tej
rundy) — przy 1h/4h oznacza to wymóg 10h/40h tego samego znaku zwrotu, coraz rzadsze zjawisko.

**Ograniczenia do uwzględnienia przy interpretacji (jawnie udokumentowane, nie ukryte):**
1. `VERTICAL_BARRIER_CANDLES=12` NIE zostało przeliczone — pozycja trzymana 12h (1h) / 48h (4h)
   zamiast 1h (5m). Timeframe danych i horyzont trzymania NIE są rozdzielone w tej rundzie.
2. Dane 4h są małe (2 190 świec, 524 `range`) — wynik -8,75/41,2% może częściowo odzwierciedlać
   szum małej próby.
3. Dane 1h/4h to agregacja z 5m (ograniczenie środowiska), nie natywny fetch z giełdy.

**Status:** ZROBIONE. Kierunek "zmiana timeframe naprawia problem" wyczerpany na tym etapie —
patrz §7 dla zaktualizowanego stanu najważniejszego otwartego ryzyka.

---

### Commit 2.7 — Przegląd kandydatek nowych cech: korelacje `[ZROBIONE — wynik: 1 cecha odrzucona, brak sygnału cecha-target]`

**Zakres:** użytkownik zapytał, czy zamiast dalszego tuningu parametrów lepiej najpierw
zbudować szerszy zestaw kandydatek cech i sprawdzić korelacje między nimi, zanim wybierze się
którąś do formalnego testu. Uzgodniona metodologia (docs/rag/02, CLAUDE.md zasada 4): korelacja
cecha-cecha (Spearman, cały zbiór) jest BEZPIECZNA — nie dotyka etykiety, więc służy tylko do
wykrycia redundancji. Korelacja cecha-target jest z definicji podglądaniem etykiety na całym
zbiorze, więc dopuszczona WYŁĄCZNIE jako opisowa/eksploracyjna (nigdy jako bramka selekcji) —
jedyny krok o wadze dowodowej pozostaje formalny walk-forward jednej wybranej cechy.

**Kod:** nowy `backtest/screen_feature_candidates.py` (poza pytest, jak inne skrypty
analityczne) + 8 nowych, czystych funkcji cech (4 rodziny: volatility, momentum,
mean-reversion, volume), świadomie zaprojektowanych jako nie-redundantne z 9 cechami w
`agents/feature_miner.FEATURE_FUNCTIONS` NA PODSTAWIE definicji wzoru. Nie wchodzą do
registry produkcyjnego na tym etapie (screening przed-rejestracyjny, formalny test leakage
dopiero przy promocji jednej cechy). Pełny wynik: `runs/2026-09-21_c2.7-feature-candidate-screening/README.md`.

**Wynik — blok 2 (korelacja cecha-cecha, redundancja):**

| Znalezisko | Szczegóły |
|---|---|
| `bb_pctb_20` **ODRZUCONY** | corr=+1,000 z `price_zscore_20` (już w modelu Test 2) — afiniczna transformacja tej samej informacji, nie nowa cecha |
| `adx_14` **wyróżniony** | jedyny kandydat z niską korelacją do reszty registry (corr z `direction_persistence_10` = +0,07, mimo że oba mierzą "siłę trendu") — sensowny kandydat #1 do formalnego testu OOS |
| rodzina volatility (`bb_width_20`, `realized_vol_20`) | silnie redundantna z istniejącymi `atr_14`/`atr_pctrank_20d` (corr 0,79–0,88) |
| `obv_zscore_20` | etykieta "volume" myląca — w praktyce bliżej mean-reversion/momentum (corr 0,72–0,78 z `price_zscore_20`/`bb_pctb_20`), bo OBV odziedzicza znak zwrotu ceny |

**Wynik — blok 3 (korelacja cecha-target, opisowa/eksploracyjna):** żadna z 17 zbadanych cech
(9 istniejących + 8 kandydatek) nie przekracza |corr| ≈ 0,065 z targetem w żadnym reżimie
(`trend`: n=523, max=-0,065 `volume_roc_10`; `range`: n=22 198, max=-0,035 `realized_vol_20`).
Czwarty niezależny sygnał (po C2.5 progach, C2.6 timeframe) wskazujący, że problem nie jest w
doborze konkretnej cechy z tego zestawu.

**Wniosek:** krok bezpieczny dał jeden konkretny wynik praktyczny (odrzucenie `bb_pctb_20`,
wyróżnienie `adx_14`); krok opisowy nie dał przesłanki faworyzującej żadną cechę ponad szum —
spójne z NO-GO C2.5/C2.6. Decyzja, czy testować `adx_14` formalnie w walk-forward (i czy
osobno rozważyć go jako zamiennik `direction_persistence_10` w regule regime — otwarty wątek
z Commitu 2c o błędnej klasyfikacji trendu spadkowego jako `range`), należy do użytkownika.

**Status:** ZROBIONE. Zero zmian w `agents/feature_miner.FEATURE_FUNCTIONS`/
`agents/ml_optimizer.py`/config — czysty screening, żadna decyzja architektoniczna
nie została podjęta automatycznie.

---

### Commit 2.8 — Formalny test OOS: `adx_14` dodane do MOMENTUM_FEATURES `[ZROBIONE — wynik: NO-GO ogólnie, poprawa marginalna w trend]`

**Zakres:** użytkownik poprosił o sformalizowanie testu OOS dla `adx_14` (kandydat
wyróżniony w Commicie 2.7 jako jedyny nisko skorelowany z resztą registry). Zgodnie z
CLAUDE.md zasada 4 (jedna cecha na raz, mierzona OOS): `adx_14` DODANE (nie zamiana) do
`MOMENTUM_FEATURES` (Test 1/trend), `REVERSION_FEATURES` (Test 2/range) niezmienione —
porównanie baseline vs kandydat przez identyczny pipeline walk-forward.

**Kod:** `compute_adx_14` promowane z `backtest/screen_feature_candidates.py` (screening)
do produkcyjnego `agents/feature_miner.FEATURE_FUNCTIONS` (10. cecha) + wpis w
`agents/feature_registry.yaml` + jednostkowy test granic [0,100]
(`tests/test_feature_miner.py`) + formalny test leakage automatycznie objął nową cechę
(parametryzacja `agent_5_compliance/test_leakage.py`, licznik 9→10). Nowy parametr
`regime_feature_sets` w `backtest/engine.py::run_backtest` (ten sam wzorzec threading co
`trend_threshold`/`candles_per_day` z C2.5/C2.6) pozwala porównać warianty feature setu
bez duplikacji pipeline'u i bez trwałej zmiany `agents/ml_optimizer.py` — nowy test
integracyjny weryfikuje przekazanie parametru. Nowy skrypt
`backtest/evaluate_feature_candidate.py` (poza pytest): baseline (4 cechy) vs kandydat
(5 cech), pełny walk-forward + 10-seed sweep. Pełny zestaw: **128/128 przechodzi**
(125 + 3: 1 unit test adx_14 + 1 integracyjny regime_feature_sets + 1 nowa instancja
parametryzowanego testu leakage). Pełny wynik: `runs/2026-09-21_c2.8-adx14-oos-evaluation/README.md`.

**Wynik:**

| wariant | mean_sharpe (seed=42) | trend_sharpe | klasyfikacja ogólna | klasyfikacja trend | stabilność (10 seed) |
|---|---|---|---|---|---|
| baseline (4 cechy) | -14,3078 | -8,4560 | NO-GO | NO-GO | std=0,0000 |
| **+adx_14 (5 cech)** | **-13,6943** | **-7,1116** | **NO-GO** | **WARUNKOWY** | std=0,0000 |

Poprawa w `trend` wynika w praktyce z JEDNEGO foldu (fold_idx=11, seed=42) zmieniającego
Sharpe z -2,40 na +0,09 — wartość ledwo powyżej zera, przy tylko 4 ważnych foldach trend w
całym przebiegu (ten sam problem małej próby co C2.5/C2.6). `range` (2/2 ważne foldy
ujemne w obu wariantach, Sharpe ~-26/-27) pozostaje kompletnie niezmieniony i nadal
dominuje ogólny werdykt NO-GO.

**Wniosek C2.8 — piąty niezależny wynik w tym samym paśmie:** mała, konsekwentna (nie
losowa) poprawa w `trend`, niewystarczająca do zmiany ogólnego werdyktu i oparta na
efekcie pojedynczego foldu przy bardzo małej próbie. Spójne z C2.7 (korelacja
`adx_14`-target w `trend` = -0,0279, w paśmie szumu). Decyzja o promocji `adx_14` do
`MOMENTUM_FEATURES` na stałe należy do użytkownika — skrypt świadomie nie wybiera
zwycięzcy.

**Status:** ZROBIONE. `compute_adx_14` zostaje w registry (obliczana, przetestowana),
`MOMENTUM_FEATURES` w `agents/ml_optimizer.py` NIEZMIENIONE do czasu decyzji użytkownika.

---

### Commit 2.9 — Naprawa metodologii pomiaru (Backlog Z1–Z4, Z11–Z15) `[ZROBIONE — NO-GO odporne na fold-jitter; zwrot per trade istotnie ujemny w obu reżimach]`

**Zakres:** realizacja pierwszej transzy backlogu z pełnego audytu projektu (TASKS.md, sekcja
"Backlog — przegląd 2026-09-21"), na polecenie użytkownika ("Dopisz i wypchnij do repo a
później zacznij realizować"). Runda zmienia WYŁĄCZNIE metodologię pomiaru i higienę — zero
zmian w hipotezie, cechach, progach, kosztach czy modelu.

**Kluczowe odkrycie audytu (Z1):** sweep stabilności po seedach (C6.3) mierzył dokładnie
nic — `DEFAULT_XGB_PARAMS` bez `subsample`/`colsample_bytree` czyni XGBoost w pełni
deterministycznym, więc seed nie zmieniał ani jednego drzewa. Stąd std=0,0000 identyczne do
ostatniej cyfry w KAŻDYM eksperymencie C6→C2.8 (~10 pustych "potwierdzeń stabilności").

**Zrealizowane:**
- **Z1:** `start_offset_days` w `generate_walk_forward_folds` (labeling.py; + unit test +
  hypothesis property test, DoD Warstwa 3) → `fold_start_offset_days` w `run_backtest` →
  sweep fold-jitter (offsety 0–9 dni) w nowej wspólnej bibliotece. Perturbuje ARBITRALNE
  wyrównanie granic foldów, nie model — offset=0 odtwarza historyczny baseline co do
  ostatniej cyfry. Świadomie BEZ nowego progu pass/fail (stary std<0,2 dotyczył pustego
  szumu seedów) — raportowany rozkład + spójność znaku.
- **Z2:** `compute_t_stat` + kolumna `t_stat` per fold (bez annualizacji — annualizowany
  Sharpe przy n=31–37/fold nadmuchiwał wartości do ±20–60) + `summarize_pooled_by_regime`
  (wszystkie transakcje reżimu połączone między foldami). Kryteria klasyfikacji
  GO/WARUNKOWY/NO-GO NIEZMIENIONE — nowe miary są diagnostyką obok werdyktu.
- **Z3:** `effective_sample_size` (C4.4, dotąd NIGDZIE nieużywane) wpięte do raportu:
  `n_eff` + konserwatywny `t_stat_neff` w pooled summary.
- **Z4:** kolumna "Warianty" (księga multiple-testing) w `runs/INDEX.md` + suma pod tabelą
  (dotychczas: 7 wariantów hipotezy na tych samych danych).
- **Z13 (forward-looking):** `backtest/checkpoint_lib.py` — wspólne load/fetch/summarize/
  sweep; historyczne skrypty NIE refaktoryzowane (zamrożone zapisy eksperymentów). Pierwszy
  użytkownik: `backtest/run_checkpoint_v2.py` (kanoniczny checkpoint v2; `run_checkpoint.py`
  zostaje jako zapis Commitu 6).
- **Higiena:** Z11 (`candle_minutes` przewleczone do kosztów — funding liczony z realnego
  czasu trzymania, nie liczby świec; test integracyjny), Z12 (lint: ruff 0 błędów), Z14
  (README zaktualizowane: status, struktura z `runs/`), Z15 (test spójności registry↔kod
  czyta `feature_registry.yaml` zamiast hardkodować listę). docs/rag/03 zaktualizowane
  (sekcja stabilności). Pełny zestaw: **139/139 testów przechodzi** (128 + 11).

**Wynik na realnych danych (`runs/2026-09-21_c2.9-measurement-methodology/README.md`):**

| Miara | Wartość |
|---|---|
| Fold-jitter (10 offsetów) | **NO-GO w 10/10**, mean_sharpe zakres [-15,89; -6,20], std=3,09, znak ujemny 100% |
| Pooled `range` (n=223) | mean/trade=-0,00108, **t=-7,15** (N_eff zdegenerowany → NaN, uczciwie) |
| Pooled `trend` (n=135) | mean/trade=-0,00063, **t=-2,91**, N_eff=110 → **t_neff=-2,63** |

**Wniosek C2.9:** (a) NO-GO jest po raz pierwszy potwierdzone REALNĄ perturbacją — nie jest
artefaktem wyrównania foldów; (b) zwrot per trade jest **istotnie ujemny w obu reżimach**
(najtwardsze dotąd sformułowanie stanu hipotezy); (c) zmierzona skala szumu fold-jitter
(σ≈3,1 mean_sharpe) czyni porównania wariantów o Δ<~3 nierozstrzygalnymi na rocznych danych
— retrospektywnie: "poprawa" C2.8 (+0,61) to ~0,2σ tego szumu, co wzmacnia tamtejszą
rekomendację niepromowania `adx_14`; (d) **Z5 (3–5 lat historii, fetch na maszynie
użytkownika) jest teraz najważniejszym odblokowaniem** dalszej pracy hipotezowej.

**Status:** ZROBIONE. Backlog: Z1–Z4, Z11–Z15 zamknięte; Z5 zrealizowane w Commicie 2.10
(poniżej); otwarte pozostają Z6–Z9 i decyzja Z10.

---

### Commit 2.10 — Wydłużenie historii danych do 3 lat (Backlog Z5) `[ZROBIONE — NO-GO na nowej bazie; niska liczba ważnych foldów okazała się strukturalna, nie ilościowa]`

**Kontekst i zakres (2026-09-21):** Z5 czekało na maszynę użytkownika (sandbox bez dostępu do
Binance). Wykonane na niej: dostęp potwierdzony (ccxt 4.5.48, ~0,35 s/stronę). Decyzja
użytkownika: **3 lata, 2023-07-01 → 2026-07-01** (z opcji 3 lat / 5 lat / maks od 2019-09-10);
`end` bez zmian, więc stare okno jest ścisłym sufiksem nowego. Zero zmian w hipotezie/cechach/
progach/kosztach/modelu. **Nowa baza checkpointu — nie porównanie 1:1 z C6–C2.9**; licznik
multiple-testing w `runs/INDEX.md` rozwidlony per zbiór danych (stary: 7, nowy: 0).

**Co zrobiono:**
- **C2.10.1 — utwardzenie fetchu** (`data/fetch_ohlcv.py`): `_fetch_page_with_retry` — retry z
  wykładniczym backoffem na `ccxt.NetworkError` (max 5 prób), `ExchangeError` celowo bez retry;
  log postępu co 50 stron. Semantyka cache niezmieniona (nazwa pliku koduje zakres → nowy zakres
  = nowy plik, stary parquet ZOSTAJE jako zamrożone źródło C6–C2.9). 4 testy (stub, bez sieci).
  Pełny zestaw: **143/143** (139 + 4).
- **C2.10.2 — fetch + integralność:** `data.start=2023-07-01`; **315 648 świec = 1096×288, zero
  dziur/duplikatów/NaN**, bez ani jednego retry. Overlap 2025-07→2026-07 ze starym plikiem:
  105 120 wierszy, max |Δ|=0 na wszystkich kolumnach OHLCV, `equals=True`.
- **C2.10.3 — checkpoint v2** (`run_checkpoint_v2`, pełny sweep) + diagnostyka udziału reżimów i
  bramki kosztowej z `folds_summary`.

**Wynik na realnych danych (`runs/2026-09-21_c2.10-extended-history-z5/README.md`):**

| Miara | Stare okno (C2.9, 1 rok) | **Nowe okno (C2.10, 3 lata)** |
|---|---|---|
| Foldy ważne / łącznie | 6 / 40 (15,0%) | **21 / 144 (14,6%)** |
| Klasyfikacja, mean_sharpe | NO-GO, -14,31 | **NO-GO, -12,39** |
| Pooled `range`: n, t_stat, t_neff | 223, -7,15, NaN | **530, -10,47, -7,34** (N_eff=261) |
| Pooled `trend`: n, t_stat, t_neff | 135, -2,91, -2,63 | **395, -5,51, -4,04** (N_eff=213) |
| Fold-jitter | 10/10 ujemne, σ=3,09 | **10/10 ujemne**, σ≈2,5 bez outliera (offset 9: -189) |
| Udział `trend` / `range` | 0,55% / 22,25% | **0,53% / 21,62%** |
| Bramka kosztowa `range`: % zablokowanych | — | **98,0%** (61 313 / 62 553) |

**Wniosek C2.10:** (a) werdykt NO-GO jest twardszy — zwrot per trade istotnie ujemny w obu
reżimach z dużym zapasem (t≈-10 / -5,5), odporny na fold-jitter również na 3 latach; (b) **odsetek
ważnych foldów nie wzrósł** — 3× więcej danych dało liniowo więcej foldów, ale przyczyna jest
strukturalna: pusty reżim `trend` (0,53% świec, dyskretność persistence — C2.5/Z7) i bramka
kosztowa blokująca 98% sygnałów `range` (Commit 2d/Z6). Dłuższa historia tego nie naprawi;
(c) outlier offset=9 (mean_sharpe -189) to znana słabość annualizowanego per-fold Sharpe przy
n≈kilka (C2.9/Z2) — statystyką nośną są pooled t; (d) dalsze dźwignie: Z7 (reguła reżimu), Z6
(koszty — przy 98% blokady bramka jest werdyktem o kosztach, nie o modelu), Z10 (decyzja).

**Status:** ZROBIONE. Backlog: Z1–Z5, Z11–Z15 zamknięte; otwarte Z6–Z9 (Z9 teraz wykonalne z
maszyny użytkownika) i decyzja Z10.

---

### Commit 2.11 — Instrumentacja edge'u `[ZROBIONE — blokada jest w geometrii wypłaty, nie w kierunku sygnału]`

**Kontekst (2026-09-21):** Runda 1 z czterorundowego programu „droga do GO" uzgodnionego
z użytkownikiem (instrumentacja → koszty Z6 → próg pewności → reguła reżimu Z7; pre-rejestrowana
reguła STOP po Rundzie 3). Powód rundy: werdykt C2.10 („brak edge'u") **mieszał dwie różne
rzeczy**. Cała klasyfikacja liczy się z `net_pnl`, a `gross_pnl` — jedyna kolumna mówiąca
o jakości samego sygnału — była zapisywana w journalu i **nigdy nieczytana przez `metrics.py`**.

Bariery triple-barrier są symetryczne (±`ATR_MULTIPLIER`×ATR, odtwarzane przez
`engine._resolve_exit_price`), więc wypłata jest w pełni określona przez zgodność kierunku
z etykietą, a werdykt redukuje się do jednej nierówności:

```
(2p − 1) · B  >  C     p = trafność kierunku, B = szerokość bariery, C = koszt round-trip
```

**Co zrobiono:** `backtest/metrics.py` — `break_even_hit_rate` (= 0,5·(1+C/B)), `compute_hit_rate`
(trafność z `gross_pnl`, z-stat wobec H0: p=0,5, CI Walda, próg raportowania
`MIN_TRADES_FOR_HIT_RATE_CI=20`), `summarize_edge_by_regime` (rozbicie na człony + margines);
wpięte do `checkpoint_lib.run_and_summarize` (`edge_per_regime`) i `run_checkpoint_v2`.
**Kryteria GO/WARUNKOWY/NO-GO NIEZMIENIONE** — nowe miary to diagnostyka obok werdyktu,
dokładnie jak Z2/Z3 w C2.9. Testy: **157/157** (143 + 14: 11 unit + 3 `hypothesis`).

**Wynik (`runs/2026-09-21_c2.11-edge-instrumentation/README.md`)** — werdykt bit-identyczny z C2.10
(`mean_sharpe = -12,392006781796571`, 21/144), co jest regresją baseline'u potwierdzającą, że
runda jest czysto addytywna:

| regime | n | hit_rate | z | B | C | break_even_p | **margin** |
|---|---|---|---|---|---|---|---|
| `range` | 530 | 51,89% | +0,87 | 0,2707% | 0,1399% | **75,83%** | **−23,94 pp** |
| `trend` | 395 | 50,63% | +0,25 | 0,4719% | 0,1402% | **64,86%** | **−14,23 pp** |

**Wniosek C2.11:** trafność kierunku jest nieistotnie różna od rzutu monetą, ale **dodatnia
w obu reżimach — model nie jest odwrócony**. Jednocześnie wymagana trafność to 75,8%/64,9%,
więc nawet górny kraniec CI (56,1%/55,6%) zostawia ~20 pp / ~9 pp pod progiem opłacalności.
**NO-GO jest przesądzone arytmetycznie geometrią wypłaty, nie błędem kierunku** — to rozróżnienie
zmienia kierunek dalszej pracy: domknąć lukę może tylko zmiana C (koszt), B (geometria) albo
selekcja podzbioru o wyższym p, a nie „lepszy model" w realistycznym zakresie.

**Status:** ZROBIONE. Następna: Runda 2 (C2.12 / Backlog Z6) — realistyczny model wykonania.

---

### Commit 2.12 — Realistyczny model wykonania maker/taker (Backlog Z6) `[ZROBIONE — NO-GO, ale ok. połowa luki do opłacalności domknięta]`

**Kontekst (2026-09-21):** Runda 2/4 programu „droga do GO". C2.11 pokazał, że koszt jest członem
dominującym nierówności (2p−1)·B > C: 0,14% nominału wobec **1,47 bps** średniego edge'u brutto.
Tymczasem `costs.py` modelował **wyłącznie takera po obu stronach** — to nie było założenie
konserwatywne, tylko brak modelu (realna egzekucja limitem kosztuje 0,02%, nie 0,05%).
Decyzja użytkownika: maker na wejściu i take-proficie, taker na stop-lossie i timeoucie,
slippage tylko na nogach taker.

**Co zrobiono:** `backtest/costs.py` — `MAKER_FEE_RATE`, `leg_fee_rate`, `exit_leg_for_reason`,
fee liczone per noga (domyślne taker/taker wstecznie zgodne); `backtest/engine.py` — kolumna
**`exit_reason`** (z iloczynu `direction * label`; sam `label` nie wystarcza, bo short na
etykiecie −1 to TP, nie SL), `_execution_legs`, parametr `execution_model`
(`taker_only` | `maker_limit`). Bramka kosztowa działa przed wejściem, więc nie zna powodu
wyjścia — dostaje założenie konserwatywne (wyjście taker). Testy: **182/182** (+25), w tym
regresja baseline'u: `taker_only` odtwarza koszt sprzed C2.12 co do cyfry.

**Wynik (`runs/2026-09-21_c2.12-execution-cost-model/README.md`):**

| Miara | C2.11 | **C2.12** |
|---|---|---|
| Klasyfikacja | NO-GO | **NO-GO** |
| Foldy ważne / łącznie | 21 / 144 | **54 / 144** |
| Transakcje `range` / `trend` | 530 / 395 | **7 155 / 355** |
| Koszt C | 0,140% | **0,067%** (−52%) |
| break_even_p (`range` / `trend`) | 75,83% / 64,86% | **66,59% / 58,94%** |
| **margin (`range` / `trend`)** | −23,94 / −14,23 pp | **−15,52 / −9,08 pp** |
| Zwrot per trade | −0,001001 / −0,000712 | **−0,000686 / −0,000432** |

**Wniosek C2.12:** (a) mechanizm zadziałał zgodnie z przewidywaniem — koszt spadł o połowę,
bramka przestała blokować 98% sygnałów `range`, liczba ważnych foldów wzrosła 2,6×, a margines
poprawił się o **+8,4 pp / +5,1 pp**, czyli ok. **połowę** luki; (b) efekt jest tłumiony
sprzężeniem zwrotnym: tańszy koszt przepuszcza sygnały o **węższej barierze** (B −25%/−19%),
więc break-even spadł mniej niż proporcjonalnie do kosztu; (c) w `trend` zwrot per trade
przestał być istotnie ujemny po korekcie N_eff (t_neff = −1,75); (d) **ostrzeżenie pomiarowe:**
`mean_sharpe` rozjechał się (−12,4 → −59,6 przy JEDNOCZEŚNIE lepszej ekonomice per trade),
sweep fold-jitter dał σ=75,7 i dwa offsety **dodatnie**, spójność znaku 100%→80%. Per-fold
Sharpe — podstawa kryteriów z docs/rag/03 — przestał być wiarygodnym przyrządem przy dużej
liczbie transakcji; nośne są pooled t-staty i margin. Kryteriów NIE zmieniano (docs je zamrażają).

**Status:** ZROBIONE. Backlog: Z1–Z6, Z11–Z15 zamknięte. Następna: Runda 3 (C2.13) — próg
pewności kalibrowany wewnątrz walk-forward, atakujący człon `p`.

---

### Commit 2.13 — Próg pewności kalibrowany wewnątrz walk-forward `[ZROBIONE — hipoteza SFALSYFIKOWANA, reguła STOP uruchomiona]`

**Kontekst (2026-09-21):** Runda 3/4 programu „droga do GO", atakująca człon `p` nierówności
(2p−1)·B > C. Hipoteza, próg i kryterium sukcesu **zarejestrowane przed uruchomieniem**:
trafność w górnym kwartylu `signal_confidence` (zmierzona przed programem: 57,1% `range`,
63,3% `trend`) miała wobec progów break-even z C2.12 dać po raz pierwszy dodatni margines
w `trend`. Kryterium: `z_margin > 2` w co najmniej jednym reżimie + poprawa klasyfikacji.

**Metodologia:** próg = kwantyl `signal_confidence` z foldu **treningowego**, stosowany OOS;
JEDNA pre-rejestrowana wartość `q=0.75`, zero sweepu. Reszta pipeline'u bez zmian.

**Wynik (`runs/2026-09-21_c2.13-confidence-threshold/README.md`) — kryterium NIESPEŁNIONE:**

| | baseline (C2.12) | kandydat (q=0,75) |
|---|---|---|
| `range`: hit / margin / z_margin | 51,07% / −15,52 pp / −26,25 | 51,41% / −14,73 pp / **−17,11** |
| `trend`: hit / margin / z_margin | 49,86% / −9,08 pp / −3,42 | **45,54%** / −13,24 pp / **−2,66** |
| Klasyfikacja | NO-GO | NO-GO |

**Wniosek C2.13:** efekt, na którym opierała się hipoteza, **nie istnieje poza próbą, na
której go zmierzono**. Monotoniczną zależność trafności od pewności zmierzono post hoc, na
danych zpoolowanych z 3 lat, wybierając górny kwartyl PO zobaczeniu wyniku; uczciwa wersja
(próg w foldzie treningowym, ocena OOS) nie odtwarza jej wcale, a w `trend` daje wynik
**przeciwny** (−4,32 pp). To podręcznikowy przykład złudzenia z selekcji post hoc.
Po trzech rundach: koszt dał się obniżyć o połowę, ale **człon `p` nie daje się ruszyć** —
trafność pozostaje nieodróżnialna od rzutu monetą (`range` z=+1,64, `trend` z=−0,90).

**REGUŁA STOP — URUCHOMIONA.** Warunek (`z_margin ≤ 2` w każdym reżimie) spełniony, więc
**Runda 4 (C2.14 / Z7) NIE została uruchomiona** — jej uruchomienie po zobaczeniu
negatywnego wyniku byłoby dokładnie tym, czemu reguła zapobiega. Budżet multiple-testing
na nowej bazie: **2**.

**Status:** ZROBIONE. Program „droga do GO" zatrzymany zgodnie z regułą. Otwarta decyzja
**Z10** (przy użytkowniku): (a) udokumentowane zamknięcie Fazy 0 wynikiem negatywnym,
(b) świadome nadpisanie STOP i Runda 4 (Z7 — inna definicja reżimu), (c) nowa hipoteza na
członie `B` (Z8 — geometria wypłaty, jedyny człon nietknięty przez program). Niezależnie
od kierunku: **`mean_sharpe` jako raportowana liczba nagłówkowa wymaga rewizji**
(patrz ostrzeżenie pomiarowe z C2.12).

**SPROSTOWANIE (2026-09-21, weryfikacja kodu):** sformułowanie „kryteria opierają się na
`mean_sharpe`" było NIEPRECYZYJNE. `classify_checkpoint` (`backtest/metrics.py:301-307`)
podejmuje decyzję na `fraction_above_threshold` i `fraction_le_zero` — **`mean_sharpe` jest
liczone i zwracane, ale NIE wchodzi do gałęzi decyzyjnej**. Fold o Sharpe −189 liczy się
w tych ułamkach dokładnie tak samo jak fold o Sharpe −0,1, więc patologia annualizowanego
per-fold Sharpe'a **nie podważa werdyktu NO-GO** (C2.12: `fraction_le_zero` = 0,870 przy
54 ważnych foldach). Niestabilna jest raportowana liczba nagłówkowa, nie klasyfikacja.
Realna luka w bramce jest inna i węższa: `fraction_positive_sign` (`metrics.py:296,312`)
jest liczone i zwracane, ale **nigdy nieczytane** — warunek „zgodny znak" z `docs/rag/03:103`
nie jest zaimplementowany, więc bramka GO jest ściśle słabsza niż udokumentowana.

---

### Audyt po programie „droga do GO" (2026-09-21) — ustalenie przewodnie: bramka reżimu i target mierzą RÓŻNE HORYZONTY

**Kontekst:** po uruchomieniu reguły STOP (C2.13) wykonano audyt — 5 niezależnych diagnoz
+ 15 adwersarialnych weryfikacji. **Wszystkie 5 zaproponowanych rund zostało odrzuconych**
(po 2–3 głosy na każdą, m.in. za pre-rejestrację po zobaczeniu liczb, za kryteria
niefalsyfikowalne z konstrukcji i za test kodujący tautologię). Wartość audytu leży więc
nie w nowych rundach, tylko w **jednym pomiarze, którego wcześniej nikt nie zrobił**.

**Pomiar (zweryfikowany niezależnie, 315 648 świec, `classify_regime` + długości nieprzerwanych
epizodów):**

| reżim | epizodów | mediana | p90 | max | epizodów ≥ 12 świec (okno etykiety) |
|---|---|---|---|---|---|
| `trend` | 728 | **2 świece (10 min)** | 5 | 15 (75 min) | **4 (0,55%)** |
| `range` | 9 717 | **5 świec (25 min)** | 16 | 63 (5h15m) | 1 729 (17,8%) |

`VERTICAL_BARRIER_CANDLES = 12` = **60 min**. Czyli mediana epizodu reżimu jest **2–6× krótsza
niż horyzont etykiety**. Praktycznie każda transakcja `trend` jest etykietowana ruchem ceny,
który w większości dzieje się POZA reżimem, który uzasadnił wejście.

**Co to zmienia w interpretacji C2.10–C2.13:** dotychczasowy wniosek brzmiał „nie ma edge'u
kierunkowego". Dokładniejszy jest: **człon `p` był mierzony na sygnale o wewnętrznie
niespójnej specyfikacji** — bramka kwalifikuje świecę do reżimu trwającego ~10–25 minut,
a target ocenia, co stanie się przez 60 minut. To wyjaśnia, dlaczego `p` okazał się nieruchomy
w dwóch niezależnych, pre-rejestrowanych próbach: nie było czego ruszać.

**Co to zamyka (człon B):** wymagane B = C/(2p−1) = **3,15% ceny** (15,5× obecnego), co
implikuje horyzont rzędu dni. Maksymalny epizod `range` w 3 latach to 5h15m, a okien 12h/48h
w całości wewnątrz reżimu jest **zero**. Backlog **Z8 jest więc niewykonalny przy obecnej
definicji reżimu** — nie „za mało danych". W `trend` dodatkowo p=49,86% < 50%, więc (2p−1) < 0
i żadna szerokość bariery nie pomaga (szersza bariera pogarsza wynik).

**Sprostowanie do C2.12/C2.13:** teza, że „werdykt opiera się na zepsutym przyrządzie", była
nieprecyzyjna — `classify_checkpoint` decyduje na `fraction_above_threshold`/`fraction_le_zero`,
nie na `mean_sharpe`. Werdykt NO-GO jest odporny na patologię per-fold Sharpe'a i pozostaje
w mocy. Realna luka jest węższa: warunek „zgodny znak" z `docs/rag/03:103` nie jest
zaimplementowany (`fraction_positive_sign` liczone, nigdy nieczytane) → bramka GO jest ściśle
słabsza niż udokumentowana (osłabia GO, nie NO-GO).

**Długi techniczne potwierdzone w kodzie** (pełna lista: TASKS.md, Backlog II, Z16–Z23):
przeciek early stopping (`ml_optimizer.py:130` — dobór liczby drzew na foldzie OOS, **zawyża
`p`**); brak purge/embargo w całym repo (`test_start == train_end`, rośnie liniowo z V);
`run_backtest` bez parametrów geometrii (blokada dla eksperymentów typu Z8); trzy niekompatybilne
definicje `p` w obiegu (różnica 6–14 pp).

**Następny krok:** Z16 — diagnostyka spójności bramki z horyzontem (0 wariantów budżetu),
która formalizuje powyższy pomiar i zamyka Z8 bez wydawania wariantu. **Z16 nie zdejmuje
reguły STOP** — zdejmuje ją wyłącznie decyzja użytkownika (Z10).

---

### Seria Z16→Z5b + S1 — naprawy pomiaru, pivot na 4h i rozstrzygnięcie drugiej hipotezy `[ZROBIONE — S1: kryterium NIESPEŁNIONE, reguła STOP, seria zamknięta]`

**Synteza (2026-09-22; pełne wyniki w `runs/`, wnioski skumulowane w `runs/INDEX.md`):**

- **Z16** — reżim `trend` strukturalnie niespójny z horyzontem etykiety (0,49% świec z etykietą
  wewnątrz reżimu); `range` uspójnialny wygładzaniem → [runs/z16](runs/2026-09-22_z16-regime-coherence/README.md);
- **Z17+Z21** — przeciek early stopping + brak embargo naprawione; `p` było ZAWYŻONE
  (51,07%→50,38%) → [runs/z17+z21](runs/2026-09-22_z17-z21-early-stopping-leak/README.md);
- **Z18** — kanoniczna definicja `p` = `gross_pnl>0`; edge nie chowa się w żadnej składowej
  → [runs/z18](runs/2026-09-22_z18-unify-hit-rate/README.md);
- **Z9** — natywne świece 1h/4h (resample psuł WOLUMEN w 11% świec 1h); próg opłacalności
  `range` 82,81% (5m) → 52,74% (4h) → [runs/z9](runs/2026-09-22_z9-timeframe-geometry/README.md);
- **Z19** — rachunek mocy PRZED eksperymentem; rekomendacja Z9 obalona zanim kosztowała rundę
  → [runs/z19](runs/2026-09-22_z19-statistical-power/README.md);
- **Z5b** — pełna historia 4h (14 916 świec, 6,8 roku); 4h WYKONALNE; **pre-rejestracja**
  eksperymentu jednoreżimowego (kryterium: trafność ≥ 56,15%, STOP przy wyniku negatywnym)
  → [runs/z5b](runs/2026-09-22_z5b-long-history-4h-preregistration/README.md);
- **S1** — eksperyment uruchomiony wg zamrożonej pre-rejestracji: **kryterium NIESPEŁNIONE
  rozstrzygająco** — n=1 037 (>925), trafność **48,60%**, 95% CI [45,56%; 51,64%], górny
  kraniec PONIŻEJ progu opłacalności 53,07%; bramka kosztowa odrzuciła 0% sygnałów (geometria
  naprawiona — nie pomogło). **Reguła STOP uruchomiona, licznik serii 1/1 zużyty**
  → [runs/s1](runs/2026-09-22_s1-single-regime-4h/README.md).

**STAN KOŃCOWY — FAZA 0 ZAMKNIĘTA (Z10, decyzja użytkownika 2026-09-22).** Obie
architektury (dwureżimowa 5m/1h/4h i jednoreżimowa 4h) wyczerpane; po usunięciu wszystkich
znanych wad pomiaru `p` ani razu nie drgnęło w górę. Liczba zamykająca: pooled `p` =
**50,27%** (n=7 687, CI95 [49,15%; 51,38%], z=+0,47) — **górny kraniec CI leży 1,30 pp
poniżej najniższego progu opłacalności zmierzonego w projekcie (52,69%), przy mocy 2,8×
wymaganej próby.** To dowód braku, nie brak dowodu.

Wąskie gardło okazało się **informacyjne, nie inżynieryjne**: wszystkie 10 cech to
transformacje ceny i wolumenu, a każda kolejna naprawa inżynieryjna (geometria, koszty,
spójność bramki, dane, przeciek, metodologia) zostawiała `p` przy 50%.

**Jawnie NIEPRZETESTOWANE** (nie wolno cytować zamknięcia jako dowodu w tych sprawach):
momentum (próba zagłodzona przez bramkę — 0,53% świec), konfiguracja 4h po naprawie
(nietestowalna, brak 11,4 lat danych), ETH/SOL/BNB (zero testów), funding rate jako sygnał
(nigdy nie zaimplementowany), ekonomia dźwigni, target inny niż kierunek.

Pełny bilans: [runs/z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md).
**Nowa hipoteza (H2)** = osobna pre-rejestracja, **własny licznik od zera**, własna reguła
STOP, rachunek mocy PRZED uruchomieniem. Nie dziedziczy budżetu ani progów po Fazie 0.

---

---

## 6. Zweryfikowane empirycznie (nie tylko zaplanowane)

- TA-Lib (0.7.0) instaluje się i liczy ATR/RSI/EMA poprawnie (zweryfikowane na random walk).
- `pandas.Series.rolling().rank(pct=True)` daje poprawną, trailing (bez leakage) percentylową
  rangę ostatniej wartości okna — zweryfikowane ręcznym przeliczeniem. Szybkie: 0.097s na 105k
  wierszy przy oknie 5760.
- `compute_all_features()` na pełnym 12-miesięcznym syntetycznym zbiorze (105k wierszy): **0.23s**.
- Nieformalny leakage sanity check: 9/9 cech identyczne na `df[:T]` vs `df[:T+50]`.
- `tests/test_fetch_ohlcv.py`: 6/6 testów przechodzi (dedup, sortowanie, gap detection).
- `xgboost` 3.2.0 instaluje się bez problemu na Python 3.14 (`pip install xgboost>=2.0`) — ryzyko
  braku prebuilt wheela (oflagowane przy planowaniu Commitu 5) nie zmaterializowało się.
- `agents/ml_optimizer.py::train_regime_model`: jedno pełne trenowanie (200 rund, early stopping
  wyłączony, `max_depth=4`) na 30k wierszy × 4 cechy — **0.436s** na Ryzen 7950X3D
  (~2.2ms/rundę). Patrz też C4.6 w `TASKS.md`.
- Pełny zestaw testów po Commicie 5: **48/48 przechodzi** (31 z Commitów 1–4 + 17 nowych: 7
  `tests/test_costs.py` + 8 `tests/test_ml_optimizer.py` + 2 `tests/test_engine.py`).
- `agents/risk_controller.py::compute_position_size`/`compute_sizing`/`check_kill_switch` — sizing
  formula i kill-switch zweryfikowane zar\u00f3wno jednostkowo, jak i property-based (hypothesis):
  `position_size` nigdy nie przekracza leverage cap niezale\u017cnie od losowych `equity`/`atr_14`/
  `entry_price` (`test_position_size_never_exceeds_leverage_cap`), jest niemalej\u0105ce w
  `signal_confidence` (`test_position_size_monotonic_nondecreasing_in_confidence`),
  `check_kill_switch` matchuje r\u0119czn\u0105 formu\u0142\u0119 drawdown dla dowolnych losowych warto\u015bci
  (`test_check_kill_switch_matches_drawdown_formula`).
- Pełny zestaw testów po Commicie 5.5: **66/66 przechodzi** (48 z Commit\u00f3w 1\u20135 + 17 nowych w
  `tests/test_risk_controller.py` + 1 nowy integracyjny w `tests/test_engine.py`).- **Pierwsze realne dane w projekcie** (Commit 6): `data/fetch_ohlcv.py` __main__ miał
  nieużywany dotąd błąd — `open("config/settings.yaml")` bez `encoding="utf-8"` crashował
  (`UnicodeDecodeError`) na tej maszynie (locale cp1250, nie UTF-8), mimo że plik jest czystym
  UTF-8 z polskimi znakami w komentarzach. Naprawione jednym słowem kluczowym. Po naprawie:
  fetch BTC/USDT:USDT 5m 2025-07-01→2026-06-30 przez ccxt/binanceusdm = **105 120 świec, zero
  dziur**, bez interwencji ręcznej.
- `exchange.load_markets()` na żywym API (binanceusdm) potwierdza `"BTC/USDT:USDT"` jako
  poprawny symbol (C1.3, wcześniej tylko założenie) — obok wariantów z datą wygaśnięcia,
  nieużywanych tutaj.
- Pełny zestaw testów po Commicie 6: **86/86 przechodzi** (66 z Commitów 1–5.5 + 20 nowych w
  `tests/test_metrics.py`, w tym 1 hypothesis property test).
- Checkpoint go/no-go (`backtest/run_checkpoint.py`) na realnych danych: wynik **NO-GO**, patrz
  §5 Commit 6 dla pełnych liczb i interpretacji.
- **Kill-switch deadlock (Commit 2b, 2026-08-01):** zweryfikowano bezpośrednio na `run_backtest`
  (realne dane, seed=42) — 18 100/18 135 (99,8%) sygnałów kandydujących stłumionych przez
  kill-switch, permanentnie od 2025-09-27 (3. dzień foldu 0 `range`) do końca datasetu
  (2026-06-30). Model sam w sobie sygnalizuje w ~99-100% wierszy testowych w każdym foldzie
  `range` — pierwotna diagnoza Commit 6 ("model rzadko sygnalizuje") była błędna. Patrz §5 Commit
  2b dla pełnej diagnozy.
- **Kill-switch deadlock NAPRAWIONY (Commit 2c, 2026-08-01):** cooldown/re-arm
  (`agents.risk_controller.should_rearm_kill_switch` + `KILL_SWITCH_COOLDOWN_DAYS=7.0`)
  zweryfikowany na realnych danych — checkpoint po naprawie: **20/20** foldów `range` mają teraz
  policzalny Sharpe (**2 562** realnych transakcji łącznie, wcześniej 1/20 foldów, 35 transakcji),
  mean_sharpe=-53,41 (fraction_le_zero=1,0), stabilne na 10 seedach (std=0,0000). `trend` przeszedł
  z 0/20 do 3/20 foldów z transakcjami (mean_sharpe=-7,15). Werdykt ogólny pozostaje **NO-GO**, ale
  teraz oparty na 23/40 foldów ważnych (wcześniej 1/40) — znacznie bardziej wiarygodny. Root-cause
  diagnostyka (`backtest/diagnose_kill_switch_trigger.py`) pokazała, że pierwotna seria strat to
  100% sygnałów long podczas trwałego spadku ceny sklasyfikowanego jako `range` (74% genuinie zły
  kierunek, 26% koszt > zysk brutto) — patrz §5 Commit 2c.
- **Bariera `range` jest węższa niż koszt round-trip (Commit 2d, 2026-09-21).** Zmierzone na
  realnych danych (`backtest/diagnose_cost_feasibility.py`): mediana `1.5×ATR` w reżimie `range` =
  **0,130% ceny** wobec kosztu **0,140% nominału** → wymagana trafność break-even **103,9%**,
  arytmetycznie nieosiągalna; 56,8% świec `range` nie pokrywa kosztu nawet przy pełnym trafieniu
  bariery. `trend` = 68,2%, `ambiguous` = 77,5%.
- **`direction_persistence_10` jest zmienną dyskretną (Commit 2d).** `|sum(sign)|/10` przyjmuje
  tylko wartości `k/10`; realny rozkład to 0,0 → 26%, 0,2 → 42%, 0,4 → 22%, 0,6 → 7%, 0,8 → 1,3%.
  Próg 0,7 wpada w lukę rozkładu — to on, nie `atr_pctrank_20d`, czyni reżim `trend` prawie pustym
  (0,53% świec; przy progu 0,5 → 4,53%).
- **Model `range` ma edge kierunkowy, ale w niewłaściwych świecach (Commit 2d).** 54,6% trafności
  na wszystkich 2 562 transakcjach Commitu 2c, ale **49,3%** po odfiltrowaniu świec, na których
  bariera nie pokrywa kosztu. Łączny gross przeszedł z -593 (bez bramki) na **+166** (z bramką) —
  strata Commitu 2c była w ~94% kosztowa, co bramka potwierdziła empirycznie.
- **Bramka wykonalności kosztowej nie zmienia werdyktu (Commit 2d).** Po odcięciu 96,8% sygnałów:
  mean_sharpe -47,38 → **-14,31**, nadal **NO-GO**, stabilne na 10 seedach (std=0,0000). Regresja
  kontrolna z `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c co do ostatniej cyfry.

---

---

## 7. Znane ryzyka i otwarte pytania

- **Regime "trend" jest rzadki — POTWIERDZONE, a poluzowanie progów NIE POMAGA (Commit 6 →
  Commit 2.5, 2026-09-21).** Na realnych danych BTC/USDT:USDT 5m trend = 0,50% świec przy
  progach 0,7/0,3. Commit 2.5 poluzował progi do (0,5, 0,3)/(0,5, 0,5), zwiększając populację
  trend do 4,28% (8,5×) — ale `mean_sharpe` POGORSZYŁ SIĘ (-14,31 → -18,00/-19,58), wszystkie
  warianty NO-GO. Rzadkość regime `trend` NIE jest już otwartym ryzykiem do "naprawienia
  kalibracją" — jest zamkniętym eksperymentem z wynikiem: więcej świec trend/range nie poprawia
  wyniku, bo dodane świece nie mają lepszej jakości sygnału. Pełny wynik:
  `runs/2026-09-21_c2.5-threshold-calibration/README.md`.
- **Regime "trend" jest jeszcze rzadszy na grubszych timeframe'ach (Commit 2.6, 2026-09-21).**
  Przy STAŁEJ liczbie 10 świec dla `direction_persistence_10` (świadomie nieprzeliczonej per
  timeframe), regime `trend` dał **ZERO transakcji** na 1h i 4h (0/18 i 0/12 foldów), gorzej niż
  na 5m (4/20). Zmiana timeframe pogłębiła, nie złagodziła, problem z rzadkością trend — jeśli
  timeframe ma być badany dalej, `direction_persistence_10`/inne okna candle-based wymagałyby
  przeliczenia analogicznie do `candles_per_day` (Commit 2.6), co NIE zostało zrobione w tej
  rundzie (świadomy zakres: zmienić TYLKO timeframe + niezbędną konwersję jednostek ATR).
- **Symbol ccxt zweryfikowany na żywo (C1.3, 2026-08-01)** — `"BTC/USDT:USDT"` potwierdzony przez
  `exchange.load_markets()`, zgodny z `config/settings.yaml`. Ryzyko zamknięte.
- **Survivorship bias w pożyczonych wskaźnikach** — RSI/ATR/EMA przetrwały w publicznym obiegu
  (freqtrade i podobne) częściowo dlatego, że ktoś na nich pokazał dobry backtest. Stała czujność,
  nie coś do jednorazowego zamknięcia.
- **Koszt obliczeniowy pełnego tuningu** (walk-forward × hiperparametry × okna wskaźników)
  nieoszacowany — zmierzyć na małej próbce przed pełnym przeszukiwaniem, nawet na Ryzen 7950X3D.
- **Kill-switch deadlock — NAPRAWIONE (Commit 2c, 2026-08-01).** Poprzednio: `check_kill_switch`
  poprawnie zaprojektowany jako bezstanowy/dynamiczny, ale w pętli `run_backtest` equity mogło się
  poruszyć WYŁĄCZNIE przez realną transakcję — więc po pierwszym zadziałaniu blokował sam siebie
  do końca backtestu. Naprawione cooldown/re-arm mechanizmem: po `kill_switch_cooldown_days` (domyślnie
  7.0) ciągłej suppresji, `peak_equity` resetuje się do bieżącego equity. Zweryfikowane na realnych
  danych (§5 Commit 2c) — ryzyko zamknięte.
- **NOWE ryzyko (Commit 2c, 2026-08-01) — jakość sygnału/klasyfikacja reżimu podczas trwałych
  trendów.** Root-cause diagnostyka (`backtest/diagnose_kill_switch_trigger.py`) pokazała, że seria
  strat wywołująca kill-switch to 100% sygnałów `long` podczas trwałego spadku ceny BTC (~-3,6% w
  3 dni) sklasyfikowanego jako reżim `range` — model `model_reversion` konsekwentnie obstawiał
  zły kierunek. Sugeruje to, że reguła klasyfikacji reżimu (progi 0.7/0.3, C2.5) może błędnie
  etykietować trwałe trendy jako `range`, albo że `model_reversion` nie ma wystarczającego edge'u,
  żeby to skompensować. Jawnie POZA zakresem Commitu 2c (wymaga C2.5 rekalibracji progów i/lub
  rework modelu/cech `range`) — **doprecyzowane przez Commit 2d**: reguła reżimu faktycznie jest
  współwinna (dyskretność `direction_persistence_10`, próg 0,7 w luce rozkładu), ale nie jest
  całą przyczyną — patrz ryzyko niżej.
- **NAJWAŻNIEJSZE OTWARTE RYZYKO (Commit 2d→2.5→2.6, 2026-09-21) — brak edge'u kierunkowego,
  kandydaci (a) i (b) WYCZERPANE.** Po włączeniu bramki wykonalności kosztowej trafność
  kierunku modelu `range` spada z 54,6% do **49,3%** na 5m, przy wymaganych ~75% (ratio=2.0).
  Commit 2.5 przetestował kandydata (a) — rekalibrację progów regime — i go ODRZUCIŁ (4 z góry
  zarejestrowani kandydaci, wszyscy NO-GO, wynik pogarsza się wraz z poluzowaniem progów).
  **Commit 2.6 przetestował kandydata (b) — zmianę timeframe (1h, 4h) — i również go ODRZUCIŁ:**
  mechanizm bariera-vs-koszt naprawiony empirycznie (0% świec arytmetycznie niewykonalnych na
  1h/4h, wobec 56,8% na 5m), ale trafność kierunku pozostaje ~49% (1h) albo spada do ~41% (4h,
  gorzej niż rzut monetą) — patrz Commit 2.6 wyżej i
  `runs/2026-09-21_c2.6-timeframe-robustness/README.md`. Trzy niezależne testy (bramka kosztowa,
  progi regime, timeframe) wskazują teraz zgodnie na TEN SAM wniosek: problem nie jest ani
  kosztowy, ani kalibracyjny, ani granulacyjny — jest w samym modelu/cechach. Pozostają
  kandydaci: (c) weryfikacja założeń kosztowych (taker 0,05%/stronę to wartość startowa; przy
  maker 0,02% koszt spada do 0,08%) — coraz mniej prawdopodobne, żeby to zmieniło wniosek, skoro
  problem przetrwał nawet przy koszcie efektywnie ~11× mniejszym niż bariera na 4h; (d) powrót
  do rejestru cech per docs/rag/02, jedna cecha na raz, mierzona OOS (reguła routingu
  checkpointu, docs/rag/03: NO-GO → rejestr cech, nie dalszy tuning) — **Commit 2.7 rozpoczął
  ten kierunek** screeningiem korelacji (patrz niżej), formalny test OOS jednej cechy wciąż nie
  wykonany. Dodatkowy, nierozdzielony wątek z Commitu 2.6: `VERTICAL_BARRIER_CANDLES=12`
  nieprzeliczone przy zmianie timeframe (1h/4h oznacza 12h/48h trzymania pozycji) — jeśli
  timeframe ma być badany dalej, to osobny, jawnie nazwany eksperyment (rozdzielić timeframe
  danych od horyzontu trzymania).
- **Screening korelacji (Commit 2.7, 2026-09-21) — czwarty niezależny sygnał w tym samym
  kierunku, plus jeden konkretny wniosek praktyczny.** Korelacja Spearman cecha-target
  (opisowa/eksploracyjna, cały zbiór) na 17 cechach (9 istniejących + 8 nowych kandydatek,
  4 rodziny) nie pokazała ŻADNEJ korelacji przekraczającej |corr| ≈ 0,065 z targetem w
  żadnym reżimie — spójne z brakiem edge'u z C2.5/C2.6, tym razem metodą niezależną od modelu
  XGBoost. Praktyczny efekt uboczny: korelacja cecha-cecha ujawniła, że kandydat `bb_pctb_20`
  jest matematycznie redundantny z już używanym `price_zscore_20` (corr=1,000) — odrzucony bez
  potrzeby testu OOS. `adx_14` wyróżnia się jako jedyny kandydat nisko skorelowany z resztą
  registry (w tym, zaskakująco, z dyskretnym `direction_persistence_10` — corr=+0,07) — kandydat
  do ewentualnego formalnego testu OOS i/lub do osobnej dyskusji jako zamiennik
  `direction_persistence_10` w regule regime (dotyczy otwartego wątku o błędnej klasyfikacji
  trendu spadkowego jako `range`, Commit 2c). Żadna decyzja o promocji cechy nie została
  podjęta — pełny wynik: `runs/2026-09-21_c2.7-feature-candidate-screening/README.md`.
- **Formalny test OOS `adx_14` (Commit 2.8, 2026-09-21) — piąty niezależny wynik w tym samym
  paśmie "brak silnego sygnału".** Dodanie `adx_14` do `MOMENTUM_FEATURES` (Test 1, Test 2
  niezmieniony) daje małą, konsekwentną poprawę w `trend` (mean_sharpe -8,46→-7,11,
  klasyfikacja NO-GO→WARUNKOWY), ale werdykt OGÓLNY pozostaje NO-GO w obu wariantach
  (stabilne, std=0,0000 na 10 seedach). Poprawa opiera się na JEDNYM foldzie zmieniającym
  Sharpe z -2,40 na +0,09 (praktycznie zero) przy tylko 4 ważnych foldach trend — zbyt słaby i
  zbyt zależny od pojedynczego przypadku dowód, by uzasadnić promocję do produkcyjnego feature
  setu. `range` (dominujący udział w werdykcie NO-GO) kompletnie niezmieniony. `compute_adx_14`
  zostaje w registry (formalnie przetestowana pod kątem leakage), `MOMENTUM_FEATURES`
  NIEZMIENIONE do czasu decyzji użytkownika. Pełny wynik:
  `runs/2026-09-21_c2.8-adx14-oos-evaluation/README.md`.
- **Naprawiona metodologia pomiaru zaostrzyła obraz (Commit 2.9, 2026-09-21).** Sweep
  stabilności po seedach mierzył nic (deterministyczny XGBoost — każde dotychczasowe
  "std=0,0000 STABILNY" było puste); zastąpiony fold-jitterem: **NO-GO w 10/10 offsetów**,
  a pooled t-stat pokazuje **istotnie ujemny zwrot per trade w OBU reżimach** (range
  t=-7,15; trend t=-2,91/-2,63 po N_eff). Zmierzony szum wyrównania foldów (σ≈3,1
  mean_sharpe) czyni porównania wariantów o Δ<~3 nierozstrzygalnymi na rocznych danych 5m —
  **kolejne rundy hipotezowe bez dłuższej historii danych (Backlog Z5) mają ograniczoną moc
  rozstrzygania**. Pełny wynik: `runs/2026-09-21_c2.9-measurement-methodology/README.md`.
  **Aktualizacja C2.10 (Z5 zrobione, 3 lata danych):** werdykt twardszy (range t=-10,47, trend
  t=-5,51), ale odsetek ważnych foldów bez zmian (14,6%) — ograniczenie jest strukturalne
  (`trend`=0,53% świec; bramka kosztowa blokuje 98% sygnałów `range`), nie do naprawienia
  dłuższą historią. Pełny wynik: `runs/2026-09-21_c2.10-extended-history-z5/README.md`.
- **Założenia kosztowe są wartościami startowymi, a teraz decydują o werdykcie.** Dopóki koszt był
  jednym z wielu składników, jego przybliżony charakter nie miał znaczenia. Po Commicie 2d koszt
  jest osią diagnozy, więc `taker_fee_rate=0.0005` / `slippage_bps=2` / `funding_rate_8h=0.0001`
  z `config/settings.yaml` warto zweryfikować wobec realnych tierów fee i realistycznego udziału
  zleceń maker, zanim odrzuci się hipotezę na ich podstawie.

---

---

## 8. Zasady pracy — patrz CLAUDE.md

> **Sekcja scalona (2026-09-22).** Jej treść (8 zasad) była dosłownym podzbiorem zasad
> nienaruszalnych z `CLAUDE.md`, które od tamtej pory urosły do 16 i są jedynym źródłem.
> Numer sekcji zachowany, żeby odniesienia „§8" nie wskazywały w pustkę.
>
> **Zasady nienaruszalne: `CLAUDE.md`.** Zasady operacyjne (branch per zadanie, konwencja `runs/`,
> zarządzanie zużyciem): §13 niżej.

---

---

## 9. Fazy po Fazie 0 (skrót)

- **Faza 1:** regime router (dispatcher), dodanie funding rate do Test 2 metodycznie, Compliance
  Gate budowany równolegle (nie po fakcie).
- **Faza 2:** `test_mathematics.py` (zostaje deterministyczny, bez LLM — rozszerzenie Warstwy 3
  property-based testów na dane realne/backtestowe), `ai_interpreter.py` (LLM offline, on-demand
  read-only Q&A o systemie). Pełny projekt: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`.
- **Faza 3:** paper trading / testnet, minimum kilka tygodni. freqtrade jako silnik wykonawczy
  (dry-run) to sensowna opcja tutaj — nie trzeba pisać order management od zera. Równolegle:
  `post_trade_critic.py` (LLM offline, verbal-reinforcement po FinCon — patrz
  `04_narzedzia_zewnetrzne.md` i `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`) — potrzebuje
  realnych/paper trade'ów do krytykowania, stąd Faza 3, nie 2.
- **Faza 4:** mały kapitał (w pełni tolerowalna strata), potem skalowanie.

---

---

## 10. Mapowanie wizji z diagramu (Miro) na fazy planu

Diagram (Miro, "My First Board") pokrywa znacznie szerszy zakres niż Faza 0 — wiele źródeł
danych, wiele modeli, pełny cykl monitoring/retraining. Poniżej: co już jest w planie (inaczej
nazwane), co pasuje do konkretnej przyszłej fazy, co nie pasuje do obecnego zakresu wcale, i co
było brakującym tematem.

### Już zrobione / już zaplanowane (ta sama rzecz, inna nazwa)

| Element z diagramu | Gdzie już jest w planie |
|---|---|
| Market Data, Volume | Commit 1 (OHLCV) |
| RSI, ATR | Commit 2 |
| Market / Entry Condition / Signal valid? | `classify_regime` → `predict_proba` → `signal_confidence` |
| Conviction-Based Sizing | `signal_confidence` skaluje `risk_per_trade` (Commit 5.5) |
| Stop Loss / Take Profit Strategy | Triple-barrier + risk_controller (Commit 4, 5.5) |
| VAR, Max Drawdown | risk_controller + kill-switch (Commit 5.5) |
| Backtest Optimization | Walk-forward (Commit 4–6) |
| VS Code, GitHub | Już nasz workflow |

### Legalne rozszerzenia — Faza 1+, dodawane metodycznie (jedna cecha na raz)

| Element | Kiedy i jak |
|---|---|
| MACD, MACROSS, Bollinger, GMMA | Częściowo redundantne z tym, co mamy (Bollinger ~ `price_zscore_20`, GMMA ~ `ema_diff_9_21`) — testować pojedynczo na OOS, nie dodawać hurtowo |
| Onchain Data | Dobry kandydat do Test 2 razem z funding rate — krypto-specyficzny sygnał pozycjonowania |
| Multi-timeframe (Trend/Day/Hour) | Po walidacji na 5m — potwierdzenie trendu z wyższego interwału, osobny wymiar złożoności |
| Trailing Stop/Take Profit | Ulepszenie risk_controllera po walidacji statycznej wersji ATR |
| Expected Shortfall | Naturalne uzupełnienie VaR o ogon rozkładu strat |
| CatBoost, RandomForest | Tylko jako porównanie/ensemble PO potwierdzeniu edge'u XGBoostem, nie zamiennik na start |

### Faza 2+/3 — dotyczy dopiero po skalowaniu

| Element | Powód odłożenia |
|---|---|
| Twitter Sentiment | Osobna modalność (NLP), koszt/jakość danych API, wymaga własnego pipeline'u walidacji |
| Forex Factory News | Lepiej jako filtr "nie handluj wokół newsa" niż cecha predykcyjna |
| Correlation & Covariance, MPT Optimization | Dotyczy alokacji między wieloma instrumentami — nierelewantne przy jednym instrumencie w Fazie 0 |
| QuantConnect / LEAN | **Zaktualizowane po researchu:** LEAN (open-source silnik pod QuantConnect) ma natywne wsparcie `AddCryptoFuture("BTCUSDT")` + `BinanceFutureMarginInterestRateModel` (symulacja funding rate) + architekturę anty-leakage. Mocniejszy kandydat niż freqtrade konkretnie dla perpetuals. Mimo to NIE w Commit 5 (mismatch z już napisanym kodem) — `Lean.DataSource.BinanceFundingRate` jako źródło danych w Fazie 1, LEAN jako silnik paper tradingu w Fazie 3 zamiast freqtrade. Oryginalny PRD miał `config/lean.json` — to prawdopodobnie był pierwotny zamysł. |
| LM Studio / RAG | Pasuje do `ai_interpreter.py` z oryginalnego PRD — LLM offline, nie na start. Pełny projekt (narzędzia, pamięć, evals, bezpieczeństwo): `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` |

### Nie pasuje do obecnego zakresu

| Element | Dlaczego |
|---|---|
| Black-Scholes | Model wyceny **opcji** — nie handlujemy opcjami, tylko perpetual futures. Zastosowanie tylko, jeśli zakres kiedyś obejmie opcje. |
| Brownian Motion | Proces stochastyczny do symulacji cen/wyceny instrumentów pochodnych — nie jest to model predykcyjny do klasyfikacji kierunku |
| LSTM/GRU | Świadomie odrzucone, nie brakujące — dane tabelaryczne + ograniczona efektywna liczba próbek faworyzują drzewa (XGBoost) nad deep learning (patrz §8, zasada 7) |

### Brakujący temat — dobra uwaga z diagramu, dodać do Fazy 1

**"Retrain Models?"** — cadence retreningu. Tego faktycznie nie było w planie.

- Retraining na stałym harmonogramie (np. co miesiąc, spójnie z granulacją okna walk-forward)
  ORAZ wyzwalany retrening, jeśli live performance (rolling Sharpe/win-rate z ostatnich N
  transakcji) spadnie istotnie poniżej oczekiwań z backtestu — to sygnał driftu reżimu, nie tylko
  szumu.
- Nie retrenować częściej niż raz na okno testowe walk-forward — inaczej dopasowujesz się do
  najnowszego szumu zamiast do trwałego wzorca.

---

---

## 11. Pliki już wygenerowane

W `clas5_core/`, gotowe do wklejenia w VS Code:

- `README.md` — wejście do repo dla ludzi (GitHub), niezależne od `CLAUDE.md`
- `CLAUDE.md` — instrukcje dla Claude Code (czytane automatycznie na starcie sesji)
- `.github/workflows/tests.yml` — minimalne CI (pytest + spójność registry/kod)
- `requirements.txt`, `config/settings.yaml`
- `data/fetch_ohlcv.py`
- `agents/feature_miner.py`, `agents/feature_registry.yaml`
- `tests/test_fetch_ohlcv.py` (6/6 przechodzi)
- `docs/rag/01_hipoteza_i_architektura.md`
- `docs/rag/02_cechy_i_leakage.md`
- `docs/rag/03_ryzyko_i_sizing.md`
- `docs/rag/04_narzedzia_zewnetrzne.md`
- `docs/rag/05_metodologia_wytwarzania_i_testow.md`
- `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md` — planistyczny, Faza 2+ (patrz §12)

---

---

## 12. Faza 2 pogłębiona — LLM offline/nadzorczo (na podstawie kursu 4th-devs)

> Pełne uzasadnienie i wzorce: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`. Nic z listy poniżej
> nie jest budowane przed checkpointem go/no-go Commitu 6 — to planowanie, nie kod.

### Zadania fazowane (Faza 2 / Faza 3)

- [ ] **`test_mathematics.py` (Faza 2):** rozstrzygnięte — zostaje w 100% deterministyczny, bez
  LLM. Weryfikacja matematycznych niezmienników (leverage cap, monotoniczność sizing względem
  `signal_confidence`) na realnych/backtestowych danych, rozszerzenie Warstwy 3 z
  `05_metodologia_wytwarzania_i_testow.md`.
- [ ] **`ai_interpreter.py` (Faza 2):** on-demand, read-only Q&A o systemie. Narzędzia:
  `get_fold_metrics`, `get_feature_definition`, `get_trade_journal`, `get_rag_doc` — zero narzędzi
  zapisu/egzekucji. Tożsamość/protokół/głos wg wzorca Identity-Protocol-Voice-Tools-Knowledge.
- [ ] **`post_trade_critic.py` (Faza 3, nie Faza 2):** scheduled, batch, verbal-reinforcement po
  FinCon. Analiza zamkniętych (realnych/paper) transakcji, raport markdown. Nigdy automatyczna
  zmiana parametrów/modelu — tylko raport, człowiek decyduje.
- [ ] **Heads-up dla Commitu 5 (`backtest/engine.py`, wciąż Faza 0):** logować transakcje w
  ustrukturyzowanym formacie (trade journal) już przy pierwszej implementacji, żeby Faza 2/3 nie
  wymagały przebudowy. Nie zmienia zakresu Commitu 5 dzisiaj — tylko do uwzględnienia przy jego
  specyfikacji.
- [ ] **Observability/evals minimalny:** structured JSON log każdej interakcji LLM (uproszczona
  taksonomia Session/Trace/Span/Tool), eval dataset ~20-30 przykładów z oczekiwanymi faktami,
  ocena human-graded na start.
- [ ] **Bezpieczeństwo:** zero narzędzi zapisu/egzekucji jako główna linia obrony przed prompt
  injection; system prompt traktowany jako publiczny; "firewall"-prompt przed głównym wątkiem
  dopiero, gdy pojawi się zewnętrzny nieufny input (dziś brak takiego źródła).
- [ ] **Świadomie wykluczone z Fazy 2/3:** autonomiczne triggery/cron/webhooks, multi-agent
  orchestration, MCP server — jeden wąski, ręcznie uruchamiany agent wystarcza na start.

### Zadania niezależne od fazowania (dokumentacja/workflow — można wykonać kiedykolwiek, nie dotyka trading logic)

- [ ] Dodać YAML frontmatter (`status`, `last_verified`, `depends_on`) do każdego `docs/rag/*.md`.
- [ ] Dodać jeden plik-indeks (Mapa Treści) linkujący `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` +
  wszystkie `docs/rag/*.md` z jednozdaniowym opisem każdego.
- [ ] Nazwać formalnie już istniejącą rolę `IMPLEMENTATION_PLAN.md` jako "Observational Memory"
  sesji Claude Code; rozważyć rozdzielenie na "aktualny stan" vs "archiwum decyzji", gdy plik
  znacząco urośnie (np. po Fazie 1).

---

## 13. Zasady pracy operacyjne (z TASKS.md)

> Zasady NIENARUSZALNE są w `CLAUDE.md`. Poniżej wyłącznie zasady operacyjne:
> jak prowadzić branche, jak dokumentować rundy, jak zarządzać zużyciem.

### Zasada pracy: osobny branch per zadanie

**Nadrzędne założenie dla całego tego pliku:** każde zadanie (dowolne ID: `C*`, `F*`, `D.*`) jest
realizowane na osobnym branchu utworzonym z `master`, np. `task/C3.1-leakage-test-atr-pctrank`.
Commit/merge do `master` następuje DOPIERO PO wykonaniu zadania i jego walidacji (testy
przechodzą, zgodność z Definition of Done z `05_metodologia_wytwarzania_i_testow.md` tam, gdzie
dotyczy) — nigdy w trakcie pracy nad zadaniem. Status w kolumnie "Status" zmienia się na ✅
dopiero po scaleniu do `master`, nie po samej lokalnej implementacji.

**Opis commita/mergu zawsze opisuje, co faktycznie zostało zrobione** — merge do `master` ma w
treści konkretną zmianę (np. "Commit 3: formalny pytest leakage dla 9 funkcji cech, priorytet
`atr_pctrank_20d` (C3.1–C3.3)"), nigdy ogólnik typu "merge branch" czy "update". Ta sama zasada
dotyczy każdej zmiany statusu w kolumnie "Status" w tym pliku — commit aktualizujący status
opisuje, co zostało zweryfikowane/wykonane, nie tylko samą zmianę ikony statusu.
### Zasada pracy: zarządzanie zużyciem Claude Code (limity Pro/Max)

**Nie przechodzić na wyższy plan (Max) prewencyjnie.** Start na Pro; decyzję o upgrade'zie
podejmować na podstawie realnego zużycia z komendy `/usage`, nie z góry. Commit 5 (dwa modele
XGBoost + `backtest/engine.py` + `backtest/costs.py` + trade journal, C5.1–C5.6) to najbardziej
prawdopodobny punkt, w którym limity Pro (rolling 5h + tygodniowy) mogą zacząć przeszkadzać —
długie sesje iteracyjne trening→metryki→debug windują zużycie kontekstu szybciej niż w Commitach
1–4.

**Nawyki ograniczające zużycie, zgodne z zasadą branch-per-task:**
- `/clear` po każdym scaleniu zadania do `master` — nie ciągnąć jednej sesji przez kilka zadań
  C5.x naraz.
- Monitorować `/usage` na bieżąco podczas pracy nad Commitem 5, zamiast dowiadywać się dopiero po
  odcięciu.
- Zrzucać verbose output (logi treningu, output testów) do subagentów zamiast wklejać go wprost do
  głównej konwersacji.

**Trafienie limitu to pauza (reset okna czasowego), nie utrata pracy** — można poczekać na reset,
dokupić usage credits na sporadyczne przekroczenia, albo przejść na Max 5x, jeśli limit łapany jest
systematycznie (nie okazjonalnie), dopiero gdy dane z `/usage` to potwierdzą.
### Zasada pracy: `runs/` — katalog per run + obowiązek czytania przed rundą

**Ustalone z użytkownikiem 2026-09-21 (pliki + sekcja +/-), rozszerzone 2026-09-22 (katalogi
per run, wnioski skumulowane, obowiązek czytania — CLAUDE.md zasady 11 i 14).** Każde
uruchomienie skryptu analitycznego na realnych danych dostaje **WŁASNY KATALOG**
`runs/YYYY-MM-DD_<id>-<slug>/` z plikami:

- `README.md` — pełny write-up: **ID testu**, **Metadane**, **Poprzedzające wyniki** (które
  wcześniejsze runy motywują/ograniczają tę rundę — obowiązkowe dla nowych rund), **Wynik**,
  **Co na plus (+) / Co na minus (-)**, **Wniosek**, **Rekomendacja**;
- `raw_output.txt` — pełny, nieskrócony stdout (obowiązkowy dla nowych rund);
- ewentualne artefakty (CSV, wykresy).

Wszystko trafia do repo (**commitowane**, nie `.gitignore` — "commitować wszystko", decyzja
użytkownika) — trwały, odtwarzalny zapis, nie scratch.

**`runs/INDEX.md`** — spis treści (ID, data, link do katalogu, opis, **licznik wariantów** =
księga multiple-testing, rozwidlany per baza danych i per hipoteza, wynik) **+ sekcja
"Wnioski skumulowane"** — syntetyczny stan wiedzy ze wszystkich rund, aktualizowany po KAŻDEJ
rundzie. **Przed projektowaniem nowej rundy obowiązkowo czyta się INDEX (tabela + wnioski) i
README powiązanych runów** — projekt rundy buduje na przebytych wynikach, nie powtarza
przetestowanych wariantów (CLAUDE.md zasada 14). Pełna procedura krok-po-kroku:
`runs/INDEX.md`, sekcja "Jak dodać nowy wpis".

`IMPLEMENTATION_PLAN.md` i `TASKS.md` dostają tylko SYNTEZĘ i link do katalogu w `runs/`.

---

## 14. Legenda statusów i podsumowanie postępu

### Legenda statusów

| Status | Znaczenie |
|---|---|
| ✅ | Zrobione i zweryfikowane |
| ⚠️ | Zrobione częściowo — działa, ale ma otwarty punkt wymagający weryfikacji |
| ⬜ | Do zrobienia — aktywny zakres (bieżący commit) |
| ⏳ | Zaplanowane, poza aktywnym zakresem — czeka na checkpoint/gate opisany w sekcji |
### Podsumowanie postępu

| Sekcja | ✅ | ⚠️/⬜ | ⏳ | Razem |
|---|---|---|---|---|
| Commit 1 — Dane | 3 | 0 | 0 | 3 |
| Commit 2 — Feature registry | 5 | 0 | 0 | 5 |
| Commit 3 — Test leakage | 3 | 0 | 0 | 3 |
| Commit 4 — Target + walk-forward split | 5 | 1 | 0 | 6 |
| Commit 5 — Dwa modele + backtest | 6 | 0 | 0 | 6 |
| Commit 5.5 — Risk controller | 5 | 0 | 0 | 5 |
| Commit 6 — Checkpoint go/no-go (ZROBIONE — wynik NO-GO) | 5 | 0 | 0 | 5 |
| Commit 2b — Diagnoza NO-GO: przegląd cech `range` (W TRAKCIE — zablokowane) | 2 | 0 | 2 | 4 |
| Commit 2c — Kill-switch: przyczyna serii strat + cooldown/re-arm (ZROBIONE) | 3 | 0 | 0 | 3 |
| Commit 2d — Bramka wykonalności kosztowej (ZROBIONE — wynik NO-GO potwierdzony) | 4 | 0 | 0 | 4 |
| Commit 2.5 — Kalibracja progów regime (ZROBIONE — wynik NO-GO, hipoteza falsyfikowana) | 2 | 0 | 0 | 2 |
| Commit 2.6 — Odporność na timeframe 1h/4h (ZROBIONE — wynik NO-GO, hipoteza falsyfikowana) | 2 | 0 | 0 | 2 |
| Commit 2.7 — Przegląd kandydatek cech: korelacje (ZROBIONE — 1 cecha odrzucona, brak sygnału cecha-target) | 2 | 0 | 0 | 2 |
| Commit 2.8 — Formalny test OOS: adx_14 (ZROBIONE — NO-GO ogólnie, poprawa marginalna w trend) | 3 | 0 | 0 | 3 |
| Commit 2.9 — Naprawa metodologii pomiaru, Backlog Z1–Z4/Z11–Z15 (ZROBIONE — NO-GO odporne na fold-jitter) | 4 | 0 | 0 | 4 |
| Commit 2.10 — Historia danych 3 lata, Backlog Z5 (ZROBIONE — NO-GO na nowej bazie, niska liczba foldów strukturalna) | 3 | 0 | 0 | 3 |
| Commit 2.11 — Instrumentacja edge'u, Runda 1/4 „droga do GO" (ZROBIONE — blokada w geometrii wypłaty, nie w kierunku sygnału) | 1 | 0 | 0 | 1 |
| Commit 2.12 — Model wykonania maker/taker, Backlog Z6, Runda 2/4 (ZROBIONE — NO-GO, ale ok. połowa luki domknięta) | 1 | 0 | 0 | 1 |
| Commit 2.13 — Próg pewności w walk-forward, Runda 3/4 (ZROBIONE — hipoteza sfalsyfikowana, reguła STOP uruchomiona) | 2 | 0 | 0 | 2 |
| Faza 1 — regime router, funding rate, Compliance Gate | 0 | 0 | 12 | 12 |
| Faza 2 — LLM offline Q&A + test_mathematics.py | 0 | 0 | 4 | 4 |
| Faza 3 — paper trading + post_trade_critic.py | 0 | 0 | 4 | 4 |
| Faza 4 — mały kapitał, skalowanie | 0 | 0 | 2 | 2 |
| Dokumentacja/workflow (niezależne od fazowania) | 2 | 2 | 1 | 5 |
| **RAZEM** | **63** | **3** | **25** | **91** |

---

---

## 15. Zadania per faza

### Faza 0 — dowód edge'u (aktywna faza)

### Commit 1 — Dane (`data/fetch_ohlcv.py`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C1.1 | Pobieranie OHLCV z Binance USDS-M Futures (perpetuals) przez ccxt, paginacja + cache parquet | ✅ | |
| C1.2 | `find_gaps()` — raportowanie dziur w danych bez blokowania pipeline'u | ✅ | |
| C1.3 | Weryfikacja dokładnego symbolu ccxt (`"BTC/USDT:USDT"`) przez `exchange.load_markets()` na żywym API | ✅ | Potwierdzone 2026-08-01 na żywym API: `"BTC/USDT:USDT"` obecny w `exchange.symbols` (Binance USDS-M Futures), obok wariantów z datą wygaśnięcia (nieużywanych). Zgodne z `config/settings.yaml`, bez zmian |

### Commit 2 — Feature registry (`agents/feature_miner.py`, `agents/feature_registry.yaml`)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.1 | 9 funkcji cech (`atr_14`, `atr_pctrank_20d`, `direction_persistence_10`, `return_lag_1`, `momentum_5`, `ema_diff_9_21`, `volume_zscore_20`, `rsi_14`, `price_zscore_20`) | ✅ | |
| C2.2 | `classify_regime()` | ✅ | |
| C2.3 | `split_by_regime()` | ✅ | |
| C2.4 | Nieformalny leakage sanity check (9/9 na danych syntetycznych) | ✅ | Nie zastępuje formalnego testu z Commitu 3 |
| C2.5 | Kalibracja progów regime rule (0.7/0.3) na realnych danych | ✅ | **ZROBIONE 2026-09-21 — wynik: NO-GO, hipoteza falsyfikowana.** Pełny opis pracy i wyniku: sekcja "Commit 2.5" niżej (po Commicie 2d), `runs/2026-09-21_c2.5-threshold-calibration/README.md`, IMPLEMENTATION_PLAN.md §5/§7 |

### Commit 3 — Test leakage (`agent_5_compliance/test_leakage.py`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C3.1 | Formalny, parametryzowany pytest leakage dla wszystkich 9 funkcji cech (`df[:T]` vs `df[:T+k]`) | ✅ | Zaimplementowane: `agent_5_compliance/test_leakage.py::test_feature_no_leakage`, 9/9 cech przechodzi |
| C3.2 | Priorytet: `atr_pctrank_20d` — trailing, nie centered window | ✅ | Dodatkowy dedykowany test `test_atr_pctrank_20d_trailing_not_centered` (mutacja przyszłych świec) — przechodzi |
| C3.3 | Zweryfikować, że istniejące CI (`.github/workflows/tests.yml`, auto-discovery `pytest -v`) podłapuje nowy `test_leakage.py` bez edycji configu | ✅ | Potwierdzone na GitHubie (nie tylko lokalnie): run `30383077052` na `master` — `success`, 17/17 przechodzi, bez żadnej edycji `tests.yml` po dodaniu pliku testów |

### Commit 4 — Target + walk-forward split (`agents/labeling.py`) — ✅ ZROBIONE (poza C4.6, odłożone do Commit 5)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C4.1 | Triple-barrier ATR-scaled (upper/lower = ±1.5×ATR, vertical = 12 świec/1h) | ✅ | Zaimplementowane: `agents/labeling.py::compute_triple_barrier_labels` — reużywa `compute_atr_14` z `feature_miner.py` (bez duplikacji). 7 testów scenariuszowych w `tests/test_labeling.py` (upper/lower hit, vertical timeout, tiebreak gdy obie bariery trafione w tej samej świecy ×2, ATR-warmup→NaN, niepełne okno na końcu datasetu→NaN) + 1 hypothesis property test — wszystkie przechodzą |
| C4.2 | Spójność mnożnika 1.5×ATR z przyszłym `risk_controller` (Commit 5.5) | ✅ | Jedyne źródło prawdy: `config/settings.yaml` sekcja `labeling.atr_multiplier: 1.5`, `agents/labeling.py::ATR_MULTIPLIER` matchuje. `risk_controller.py` (Commit 5.5) MUSI czytać tę samą wartość — CLAUDE.md zasada 3 |
| C4.3 | Walk-forward split (2 mies. train / 2 tyg. test, krok 2 tyg., chronologiczny) | ✅ | Zaimplementowane: `agents/labeling.py::generate_walk_forward_folds` — chronologiczne, przesuwane okna, half-open intervals (brak nakładania train/test wewnątrz foldu). 3 testy w `tests/test_labeling.py` (chronologia + brak nakładania, oczekiwana liczba foldów, zbyt mało danych → pusta lista) przechodzą |
| C4.4 | Diagnostyka efektywnej liczby próbek (autokorelacja `return_lag_1`, N_eff) | ✅ | Zaimplementowane: `agents/labeling.py::effective_sample_size` (N_eff = N/(1+2·Σρ_k), `pd.Series.autocorr`). 2 testy sanity (i.i.d. → N_eff≈N; silnie autoskorelowany → N_eff≪N) przechodzą |
| C4.5 | Test leakage dla `labeling.py` PRZED wejściem do modelu | ✅ | Zaimplementowane: `agent_5_compliance/test_leakage.py::test_triple_barrier_no_leakage` — metodologia truncate-vs-extend dostosowana do labeli (porównywalny region = wiersze, których pełne okno w przód mieści się w obciętych danych). Przechodzi |
| C4.6 | Zmierzyć koszt obliczeniowy pełnego tuningu (walk-forward × hiperparametry × okna wskaźników) na małej próbce PRZED pełnym przeszukiwaniem | ⚠️ | Pomiar częściowy wykonany w Commicie 5 (po dodaniu realnych hiperparametrów XGBoost): jedno `train_regime_model` (max_depth=4, 200 rund, early stopping wyłączony) na 30k wierszy × 4 cechy = **0.436s** (~2.2ms/rundę), Ryzen 7950X3D. Ekstrapolacja: walk-forward ~9 foldów × 2 reżimy = 18 treningów/kombinację hiperparametrów ≈ 7.9s najgorszy przypadek; grid search 20 kombinacji ≈ 158s — koszt obliczeniowy nie wygląda na blocker. Otwarte: pomiar NIE obejmuje jeszcze przeszukiwania okien wskaźników (`feature_miner.py`) razem z hiperparametrami XGBoost — do zrobienia przy faktycznej kalibracji (Commit 6 / Faza 1) |

### Commit 5 — Dwa modele, osobno (`agents/ml_optimizer.py`, `backtest/`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.1 | `model_momentum` + `model_reversion` — dwa niezależne XGBoosty | ✅ | Zaimplementowane: `agents/ml_optimizer.py::train_regime_model` (generyczny, wywoływany osobno dla `MOMENTUM_FEATURES`/`REVERSION_FEATURES` per reżim w `backtest/engine.py`) — natywne API `xgboost.train()`/`DMatrix`, nie sklearn-wrapper. Żadnego wspólnego modelu |
| C5.2 | Hiperparametry startowe + `early_stopping_rounds=20` na foldzie OOS | ✅ | `DEFAULT_XGB_PARAMS` (max_depth=4, eta=0.05) + `NUM_BOOST_ROUND=200` + `EARLY_STOPPING_ROUNDS=20`, źródło prawdy `config/settings.yaml` sekcja `model`. Early stopping mierzony na `test_df` (OOS), nigdy train — potwierdzone testem `test_train_regime_model_early_stopping_engages` |
| C5.3 | `predict_proba` (nie tylko klasa) jako `signal_confidence` | ✅ | `agents/ml_optimizer.py::predict_signal` — `signal_confidence` = predict_proba klasy argmax (nie surowa etykieta), `signal_direction` zdekodowany do {-1,0,1} przez `CLASS_TO_LABEL`. Testy: `test_predict_signal_returns_valid_direction_and_confidence`, `test_predict_signal_preserves_index_after_dropna` |
| C5.4 | `backtest/costs.py` — taker fee, funding rate, slippage | ✅ | `round_trip_fee_cost`, `funding_cost`, `slippage_cost`, `total_round_trip_cost`. Wartości startowe w `config/settings.yaml` sekcja `costs` (taker_fee_rate=0.0005, funding_rate_8h=0.0001, slippage_bps=2). 7/7 testów przechodzi (`tests/test_costs.py`) |
| C5.5 | `backtest/engine.py` — pętla sygnał → risk_controller → PnL z kosztami → equity curve | ✅ | Zaimplementowane: `run_backtest`. Prawdziwy `risk_controller` (Commit 5.5, `agents/risk_controller.py::compute_sizing`) wstrzyknięty jako domyślny `risk_controller_fn`, wymienny bez zmiany pętli. Reżim filtrowany własnym boolean maskiem (nie `split_by_regime()`) żeby zachować index do lookupu ceny wyjścia dla timeoutów. Sygnały z obu reżimów sortowane po `timestamp` przed sekwencyjną symulacją equity. Kill-switch (`check_kill_switch`) sprawdzany co sygnał przed sizingiem. 3/3 testy integracyjne przechodzi (`tests/test_engine.py`) |
| C5.6 | Trade journal — logowanie transakcji w ustrukturyzowanym formacie już przy pierwszej implementacji | ✅ | `run_backtest` zwraca `trades: pd.DataFrame` z `TRADE_COLUMNS` (entry/exit price, position_size, gross/net PnL, equity before/after) — ustrukturyzowany format od pierwszej implementacji |

### Commit 5.5 — Risk controller (`agents/risk_controller.py`) — ✅ ZROBIONE

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C5.5.1 | Kontrakt wejścia/wyjścia (`signal_direction`/`signal_confidence`/`regime`/`atr_14`/`entry_price` → `position_size`/`stop_price`/`take_profit_price`) | ✅ | Zaimplementowane: `agents/risk_controller.py::compute_sizing` — dokładnie ten kontrakt, drop-in replacement dla `risk_controller_fn` w `backtest/engine.py::run_backtest` (kwargs identyczne z docs/rag/03). Dwuwarstwowy design: `compute_position_size` (czysty numeryczny rdzeń, zwraca float) + `compute_sizing` (pełny kontrakt ze słownikiem) — pozwala hypothesis property testom trzymać się dokładnie szablonu z docs/rag/05 |
| C5.5.2 | Sizing: `size_risk`, `size_leverage`, `position_size = min(size_risk, size_leverage)` | ✅ | Leverage cap zawsze wygrywa — CLAUDE.md zasada 5. Zaimplementowane w `compute_position_size`. Test hypothesis `test_position_size_never_exceeds_leverage_cap` (property, adaptowany z szablonu docs/rag/05) potwierdza cap niezależnie od `equity`/`atr_14`/`entry_price` |
| C5.5.3 | Parametry startowe: `risk_per_trade=0.5%`, `max_leverage=3x` | ✅ | `RISK_PER_TRADE=0.005`, `MAX_LEVERAGE=3.0` w `agents/risk_controller.py` ("wartość startowa"), zdublowane w `config/settings.yaml` sekcja `risk` jako źródło prawdy do przyszłej kalibracji. `atr_multiplier` importowany z `agents.labeling.ATR_MULTIPLIER`, nigdy redefiniowany lokalnie — CLAUDE.md zasada 3 |
| C5.5.4 | `signal_confidence` skaluje `risk_per_trade` liniowo | ✅ | `compute_sizing`: `effective_risk_per_trade = risk_per_trade * signal_confidence`, skaluje WYŁĄCZNIE `size_risk` — `size_leverage` zostaje twardym sufitem niezależnym od confidence (inaczej cap z C5.5.2 przestałby być prawdziwym hard cap). Test `test_compute_sizing_scales_effective_risk_by_confidence` + hypothesis `test_position_size_monotonic_nondecreasing_in_confidence` |
| C5.5.5 | Kill-switch (drawdown > X% od peaku → stop nowych sygnałów) | ✅ | `check_kill_switch(equity, peak_equity, drawdown_threshold=0.15)` — próg **15%** (decyzja użytkownika, nie rekomendowane 20%), re-check **dynamiczny** przy każdym sygnale (nie permanentny latch — wznawia się, gdy equity odzyska się powyżej progu), fail-safe `peak_equity <= 0` → `True`. Wpięty w `backtest/engine.py::run_backtest`: sprawdzany PRZED sizingiem każdego sygnału, sygnały stłumione trafiają do `trades` z `kill_switch_active=True` (position_size=0.0, equity bez zmian) zamiast osobnej listy — jeden trade journal, nie dwa równoległe źródła prawdy. 5 testów jednostkowych + hypothesis `test_check_kill_switch_matches_drawdown_formula` + integracyjny `test_run_backtest_kill_switch_suppresses_signals_after_large_drawdown` (oversized stub risk_controller_fn wymusza drawdown deterministycznie) |

### Commit 6 — Checkpoint go/no-go — ✅ ZROBIONE (wynik: **NO-GO**)

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C6.1 | Policzyć Sharpe po kosztach per fold | ✅ | Zaimplementowane: `backtest/metrics.py::compute_fold_metrics` (zwrot per trade = net_pnl/equity_before, wyklucza `kill_switch_active`; Sharpe annualizowany `sqrt(trades_per_year)`, `trades_per_year` z częstości transakcji per-fold; NaN gdy <2 transakcje lub zerowa wariancja). Realny przebieg (`backtest/run_checkpoint.py`, BTC/USDT:USDT 5m, 2025-07-01→2026-06-30, 105120 świec, brak dziur): tylko 1/40 foldów (regime×fold_idx) miało policzalny Sharpe = **-65.43** (range, fold_idx=0, 35 transakcji); pozostałe 39 NaN (brak transakcji albo fold pominięty przez `min_train_rows`) |
| C6.2 | Klasyfikacja wyniku: GO / WARUNKOWY / NO-GO wg kryteriów z §5 | ✅ | `classify_checkpoint`: **NO-GO** (fraction_le_zero=1.0 > 0.5 próg w jedynym policzalnym foldzie). Wg reguły routingu: wróć do Commit 2 (inna hipoteza/cechy), NIE tuning tego zestawu (§5). Pełna analiza przyczyn: IMPLEMENTATION_PLAN.md §6/§7 |
| C6.3 | Stabilność wyniku przy losowym seedzie modelu (overfitting sanity check) | ✅ | 10 seedów (42-51, ustalone z użytkownikiem) przez `backtest/run_checkpoint.py`: WSZYSTKIE dały identyczny mean_sharpe=-65.4333 (std=0.0000 < próg 0.2) → **stabilne** — głównie dlatego, że tylko 1 fold z 40 kiedykolwiek generuje transakcje, a jego wynik okazał się niezależny od seeda modelu w tym przebiegu |
| C6.4 | Wynik osobno per reżim rynkowy — zinterpretowane jako trend vs range (nie kalendarzowo, patrz Uwagi) | ✅ | Realny zakres danych (2025-07→2026-07) nie sięga 2023 — interpretacja kalendarzowa z opisu zadania nie pasowała, zamieniona (za zgodą użytkownika) na podział wg reżimu. Wynik `summarize_by_regime`: **trend = WARUNKOWY (0/20 foldów policzalnych — WSZYSTKIE pominięte przez `min_train_rows`, reżim empirycznie prawie nieobecny w 14-dniowych oknach testowych, potwierdza ryzyko z C2.5/§7 IMPLEMENTATION_PLAN.md)**; **range = NO-GO (1/20 foldów policzalnych, Sharpe=-65.43)** |
| C6.5 | Decyzja udokumentowana w `IMPLEMENTATION_PLAN.md` | ✅ | Udokumentowane w §5 (Commit 6) i §6/§7 — pełny opis liczb i przyczyn. Wynik: **NO-GO**. **Korekta (Commit 2b):** przyczyna "1/20 foldów z transakcjami" dla `range` opisana tu pierwotnie ("predict_signal zwraca wyłącznie direction=0") okazała się błędna — patrz Commit 2b niżej i IMPLEMENTATION_PLAN.md §5 |

### Commit 2b — Diagnoza NO-GO: przegląd cech modelu `range` — ZAMKNIĘTE (przesłanka obalona w C2b.1; C2b.2/C2b.3 bezprzedmiotowe, patrz §5)

> Zakres uzgodniony z użytkownikiem 2026-08-01: WYŁĄCZNIE przegląd/rewizja feature setu modelu
> `range` (`REVERSION_FEATURES`) — jawnie wykluczone: rekalibracja progów regime (C2.5), zmiana
> mnożnika ATR triple-barrier. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2b.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2b.1 | Zbudować read-only diagnostykę: per fold `range`, rozkład triple-barrier label, feature importance (`gain`), pełny rozkład `signal_confidence` (nie tylko `direction != 0`) | ✅ | `backtest/diagnose_range_signal.py` (poza pytest, jak `run_checkpoint.py`) — zachowany jako trwałe narzędzie. WYNIK: pierwotna diagnoza Commit 6 ("`predict_signal` zwraca wyłącznie `direction=0` w 19/20 foldów") jest BŁĘDNA — model sygnalizuje w ~99-100% wierszy testowych w KAŻDYM z 20 foldów (17 989/17 989 z policzalnym labelem), z sensowną confidence (~0.44-0.50 vs 0.33 baseline) i niezerowym, zmiennym feature importance dla wszystkich 4 cech. Rozkład labeli train/test sensownie zbalansowany w każdym foldzie — brak strukturalnego braku zdarzeń +1/-1. Model NIE jest wąskim gardłem |
| C2b.1b | Zweryfikować rzeczywisty mechanizm "0 transakcji" w 19/20 foldów `range`, skoro model jednak sygnalizuje | ✅ | Zweryfikowano ad hoc na `run_backtest(seed=42)["trades"]`/`["folds_summary"]`: 18 135 sygnałów kandydujących łącznie, **18 100 (99,8%) stłumionych przez kill-switch**, tylko **35** realnych transakcji (dokładnie zgodne z Commit 6). Kill-switch uruchomił się 2025-09-27 (3. dzień fold_idx=0 `range`) i NIGDY nie wznówił działania do końca datasetu (2026-06-30) — equity zamrożone na 8469,93 (drawdown 15,30%) permanentnie, bo bez realnej transakcji (a tę właśnie blokuje kill-switch) equity nie może się poruszyć. `check_kill_switch` sam w sobie poprawny/bezstanowy/dynamiczny — to deadlock EMERGENTNY z resztą pętli `run_backtest`, nie błąd tej funkcji. Osobne, niezbadane pytanie: dlaczego pierwsze ~9-10 transakcji fold 0 straciło tak konsekwentnie — poza zakresem tej rundy |
| C2b.2 | Dodać jedną kandydującą cechę do `REVERSION_FEATURES` (np. Bollinger %B) | ⏳ | **WSTRZYMANE** — C2b.1/C2b.1b obalają przesłankę ("model rzadko sygnalizuje"). Rozszerzanie feature setu nie zaadresuje rzeczywistej przyczyny. Czeka na NOWĄ decyzję użytkownika o zakresie — prawdopodobnie `agents/risk_controller.py` (mechanizm odzyskiwania kill-switcha i/lub formuła sizingu), co wymaga własnego przeczytania docs/rag/03 przed zmianą (CLAUDE.md) i jest POZA uzgodnionym zakresem tej rundy |
| C2b.3 | Ponowny checkpoint (`run_checkpoint.py`) po C2b.2, porównanie z baseline Commit 6 | ⏳ | Zablokowane przez C2b.2 |

### Commit 2c — Kill-switch: przyczyna serii strat + mechanizm cooldown/re-arm — ✅ ZROBIONE

> Zakres zatwierdzony przez użytkownika 2026-08-01 ("1.yes 2.yes" + "Do both in one round" +
> "tak jak uważasz za najlepsze" dla wyboru mechanizmu): diagnoza przyczyny serii strat + naprawa
> deadlocka kill-switcha, jedną rundą. Pełna diagnoza i wyniki: `IMPLEMENTATION_PLAN.md` §5 Commit 2c.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2c.1 | Root-cause diagnostyka serii strat wywołującej kill-switch (`backtest/diagnose_kill_switch_trigger.py`) | ✅ | Read-only skrypt inspekcji 35 realnych transakcji — rozbija koszt na fee/funding/slippage. WYNIK: 100% transakcji `signal_direction=1.0` (long) podczas trwałego spadku ceny BTC (~-3,6% w 3 dni) sklasyfikowanego jako `range`; 26/35 (74%) genuinie zły kierunek, 9/35 koszt > zysk brutto. Kill-switch NIE był wadliwy — poprawnie wykrył realną serię strat. Przyczyna głębsza (jakość sygnału/klasyfikacja reżimu) POZA zakresem tej rundy |
| C2c.2 | Zaprojektować i zaimplementować mechanizm naprawy deadlocka kill-switcha | ✅ | Cooldown/re-arm: `agents.risk_controller.should_rearm_kill_switch` (nowa czysta funkcja, testowalna w izolacji) + `KILL_SWITCH_COOLDOWN_DAYS=7.0` (domyślnie, `config/settings.yaml` sekcja `risk`) — po N dni ciągłej suppresji, `backtest.engine.run_backtest` resetuje `peak_equity` do bieżącego equity. `check_kill_switch` sam w sobie niezmieniony (nadal czysty/bezstanowy). Testy: 4 jednostkowe + 3 hypothesis property tests w `tests/test_risk_controller.py`, 1 nowy integracyjny (`test_run_backtest_kill_switch_re_arms_after_cooldown`) w `tests/test_engine.py`. Pełny zestaw: **94/94 przechodzi** |
| C2c.3 | Ponowny checkpoint (`run_checkpoint.py`) po naprawie, porównanie z baseline Commit 6/2b | ✅ | Range: 1/20→**20/20** foldów z policzalnym Sharpe (35→**2 562** transakcji), mean_sharpe=-53,41 (fraction_le_zero=1,0). Trend: 0/20→**3/20** foldów (mean_sharpe=-7,15). Ogólnie: **NO-GO potwierdzone** (23/40 foldów ważnych, wcześniej 1/40), stabilne na 10 seedach (std=0,0000). Naprawa nie zmienia werdyktu, ale czyni go dużo bardziej wiarygodnym — patrz IMPLEMENTATION_PLAN.md §5/§6/§7 |

### Commit 2d — Bramka wykonalności kosztowej — ✅ ZROBIONE

> Zakres uzgodniony z użytkownikiem 2026-09-21. Runda miała być C2.5 (rekalibracja progów regime);
> read-only diagnostyka przed startem obaliła jej przesłankę, więc zakres zmieniono za zgodą
> użytkownika na bramkę kosztową, a C2.5 przesunięto na następną, osobną rundę (jedna zmiana na
> raz). Pełna diagnoza i liczby: `IMPLEMENTATION_PLAN.md` §5 Commit 2d.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2d.0 | Diagnostyka wykonalności kosztowej (`backtest/diagnose_cost_feasibility.py`) | ✅ | Read-only skrypt (3 bloki: rozkład reguły reżimu, bariera vs koszt, dekompozycja realnych transakcji), zachowany jako trwałe narzędzie. WYNIKI: (1) `direction_persistence_10` jest DYSKRETNA (`k/10`), próg 0,7 wpada w lukę rozkładu — to on, nie ATR, czyni `trend` prawie pustym (0,53%; przy 0,5 → 4,53%); (2) w `range` mediana bariery 1.5×ATR = **0,130% ceny** < koszt **0,140% nominału** → wymagana trafność break-even **103,9%, arytmetycznie nieosiągalna**, 56,8% świec nie pokrywa kosztu nawet przy pełnym trafieniu; (3) model `range` trafiał kierunek w **54,6%** transakcji, a mimo to 42% transakcji z dobrym kierunkiem kończyło netto ujemnie (gross -569 vs koszt 9 168). Wniosek: NO-GO Commitu 2c był w ~94% wynikiem arytmetycznym, nie statystycznym |
| C2d.1 | Czysta funkcja bramki + wpięcie w pipeline | ✅ | `agents.risk_controller.is_cost_feasible` (+ rdzeń `barrier_to_cost_ratio`): sygnał dopuszczony tylko gdy `(atr_multiplier*atr_14)/entry_price >= min_barrier_to_cost_ratio * cost_fraction`. Próg startowy **2.0** (`config/settings.yaml` sekcja `risk`) wyprowadzony z break-even `p=0.5*(1+1/ratio)` → 75%, NIE z przeszukiwania po Sharpe (CLAUDE.md zasada 1). `cost_fraction` z nowej `backtest.costs.round_trip_cost_fraction()` — te same stałe co `total_round_trip_cost`, zero duplikacji. Filtruje KANDYDATURĘ sygnału w `_collect_candidate_signals` (nie trafia do trade journalu — to właściwość świecy, nie zdarzenie w torze equity, w odróżnieniu od kill-switcha), licznik w `folds_summary["n_signals_cost_gated"]`; `backtest/metrics.py` bez zmian. NIE jest progiem na `signal_confidence` (docs/rag/03 świadomie taki odrzuca — bramka jest ortogonalna). `atr_multiplier` nietknięty (CLAUDE.md zasada 3) |
| C2d.2 | Testy jednostkowe + hypothesis + integracyjne (DoD docs/rag/05) | ✅ | 7 jednostkowych + **4 hypothesis** w `tests/test_risk_controller.py` (zgodność bramki ze stosunkiem, monotoniczność niemalejąca w `atr_14`, próg 0.0 przepuszcza wszystko, fail-safe dla `entry_price<=0`/`cost_fraction<=0`/NaN, reprodukcja diagnozy `range`), 3 w `tests/test_costs.py`, 2 integracyjne w `tests/test_engine.py` (księgowanie bez gubienia sygnałów, bramka domyślnie włączona). Trzy testy sprzed 2d dostały jawne `min_barrier_to_cost_ratio=0.0` — ich przedmiotem jest kill-switch. Pełny zestaw: **110/110 przechodzi** (94 + 16) |
| C2d.3 | Ponowny checkpoint po bramce, porównanie z baseline Commit 2c | ✅ | Bramka odcięła **17 547 z 18 135 sygnałów (96,8%)**, w `range` 97,5%. Foldy z policzalnym Sharpe 23/40→**6/40**, transakcje 2 625→**358**, mean_sharpe -47,38→**-14,31** (range -26,01, trend -8,46, przy czym trend ma teraz 25% foldów z Sharpe>0,5 wobec 0% wcześniej). **Łączny gross -593 → +166** — strata BYŁA kosztowa, diagnoza potwierdzona empirycznie. ALE: trafność kierunku w `range` spada 54,6%→**49,3%** na świecach przechodzących bramkę — edge mieszkał w świecach nieopłacalnych. **Werdykt: NO-GO**, stabilne na 10 seedach (std=0,0000). Regresja kontrolna `min_barrier_to_cost_ratio=0.0` odtwarza baseline Commitu 2c co do ostatniej cyfry (-47,377414474779975, 23/40) |

### Commit 2.5 — Kalibracja progów reguły regime — ✅ ZROBIONE (wynik: NO-GO, hipoteza falsyfikowana)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("comitować wszystko, Chcesz, żebym tak rozpisał i
> odpalił C2.5 tak"): bounded-autonomy — z góry zarejestrowany, mały, strukturalnie (nie z PnL)
> uzasadniony zestaw kandydatów progów regime, oceniony przez pełny walk-forward checkpoint, bez
> automatycznego wyboru zwycięzcy. Pełna diagnoza, tabela i surowy output:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.5, `runs/2026-09-21_c2.5-threshold-calibration/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.5.1 | Parametryzacja progów regime (`agents/feature_miner.py`, `backtest/engine.py`) + testy (DoD docs/rag/05) | ✅ | `DEFAULT_TREND_THRESHOLD=0.7`/`DEFAULT_RANGE_THRESHOLD=0.3` jako nazwane stałe (mirroring `config/settings.yaml`, wzorzec `ATR_MULTIPLIER`); `classify_regime`/`compute_all_features`/`run_backtest` przyjmują i przekazują progi dalej, bez zmiany domyślnego zachowania. Testy: 6 nowych jednostkowych w `tests/test_feature_miner.py` (nowy plik — dotąd `feature_miner.py` miał pokrycie tylko przez test leakage, nie testu POPRAWNOŚCI reguły progowej) + 1 integracyjny w `tests/test_engine.py` (próg nieosiągalny 0.99 ⇒ zero sygnałów trend, weryfikuje przekazanie parametru end-to-end). Pełny zestaw: **117/117 przechodzi** (110 + 7) |
| C2.5.2 | Skrypt kalibracyjny (`backtest/calibrate_regime_thresholds.py`) + uruchomienie na realnych danych, 4 kandydaci × 10-seed sweep | ✅ | 4 kandydaci z góry zarejestrowani ze STRUKTURY dyskretnego wsparcia `direction_persistence_10` (`{0,0.2,0.4,0.6,0.8,1.0}`), nie z podglądania Sharpe'a (CLAUDE.md zasada 1): `(0.7,0.3)` baseline, `(0.6,0.4)` kontrola, `(0.5,0.3)`, `(0.5,0.5)`. WYNIK: **wszystkie 4 NO-GO**, `mean_sharpe` POGARSZA SIĘ wraz z poluzowaniem progów (-14,31→-14,25→-18,00→-19,58, stabilne na 10 seedach każdy, std=0,0000). Poluzowanie zwiększa populację `trend` (0,50%→4,28%) i `range` (21,13%→44,18%), ale dodane świece są GORSZEJ jakości, nie lepszej — falsyfikuje hipotezę "brakujące świece kryją niewykorzystany edge". Kandydat kontrolny `(0.6,0.4)` NIE odtworzył populacji baseline (przewidywanie w docstringu było błędne — `atr_pctrank_20d` jest ciągła, więc próg zmienia populację nawet w "luce" rozkładu `persistence`), udokumentowana korekta własnej hipotezy. **Decyzja: `config/settings.yaml` pozostaje przy baseline (0,7/0,3)** — najlepszy (najmniej ujemny) z czterech wyników, zgodnie z regułą routingu checkpointu (docs/rag/03: NO-GO → rejestr cech, nie dalszy tuning) |

### Commit 2.6 — Odporność hipotezy na timeframe (1h, 4h) — ✅ ZROBIONE (wynik: NO-GO, hipoteza falsyfikowana)

> Zakres uzgodniony z użytkownikiem 2026-09-21: użytkownik zauważył krótki horyzont trzymania
> pozycji na 5m (max. 1h) i zapytał, czy NO-GO utrzymuje się na grubszych interwałach (1h, 4h),
> gdzie bariera ATR rośnie względem stałego kosztu. Zmieniona WYŁĄCZNIE granulacja danych +
> niezbędna konwersja jednostek (`candles_per_day`) — reszta pipeline'u (progi, ATR_MULTIPLIER,
> bramka kosztowa) niezmieniona. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2.6,
> `runs/2026-09-21_c2.6-timeframe-robustness/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.6.1 | `resample_ohlcv` (`data/fetch_ohlcv.py`) + parametryzacja `candles_per_day` (`agents/feature_miner.py`, `backtest/engine.py`) + testy | ✅ | Sandbox nie ma dostępu do Binance (`fapi.binance.com` → 403 na proxy) — dane 1h/4h AGREGOWANE z bazy 5m (open/high/low/close/volumen, odrzucanie niepełnych bucketów brzegowych), jawnie odróżnione od potencjalnego natywnego fetcha. `candles_per_day` (288→24→6) sparametryzowane analogicznie do progów C2.5 — bez tego okno "20 dni" ATR percentile liczyłoby błędną liczbę dni na innym timeframe. Testy: 4 nowe w `tests/test_fetch_ohlcv.py` (agregacja OHLC/volumenu, spójność 5m→4h vs 5m→1h→4h, odrzucanie niepełnego bucketu, walidacja timeframe), 3 w `tests/test_feature_miner.py`, 1 integracyjny w `tests/test_engine.py`. Pełny zestaw: **125/125 przechodzi** (117 + 8) |
| C2.6.2 | Skrypt `backtest/checkpoint_timeframe_robustness.py` + uruchomienie na 5m (referencja)/1h/4h, 10-seed sweep każdy | ✅ | Dokładny bezresztowy podział z 105 120 świec 5m: 8 760 (1h), 2 190 (4h). WYNIK: **oba NO-GO** — 1h mean_sharpe=-15,57, 4h mean_sharpe=-8,75 (5m referencja: -14,31), stabilne na 10 seedach (std=0,0000 każdy). Diagnostyka bariera-vs-koszt (metodologia Commitu 2d) POTWIERDZA naprawę mechanizmu: 0% świec arytmetycznie niewykonalnych na 1h/4h (wobec 56,8% na 5m), wymagana trafność break-even spada z 103,9% do 54–61%. MIMO TO trafność kierunku pozostaje ~49,0% (1h, rzut monetą) albo spada do ~41,2% (4h, gorzej niż losowo). Regime `trend` praktycznie pusty na 1h/4h (0 transakcji) — `direction_persistence_10` pozostał na STAŁEJ liczbie 10 świec, nieprzeliczonej per timeframe (świadomy zakres tej rundy). **Trzeci niezależny test (po bramce kosztowej i progach regime) wskazujący, że problem jest w modelu/cechach, nie w koszcie/kalibracji/granulacji danych** |

### Commit 2.7 — Przegląd kandydatek nowych cech: korelacje — ✅ ZROBIONE (wynik: 1 cecha odrzucona, brak sygnału cecha-target)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("a czy nie lepiej zrobić X zmiennych i sprawdzić
> korelacje między nimi, a dopiero później zbudować model" → "tak zaproponuj i sporzać
> korelacje"): korelacja cecha-cecha (Spearman, cały zbiór) jako BEZPIECZNY krok redundancji;
> korelacja cecha-target dopuszczona WYŁĄCZNIE jako opisowa/eksploracyjna (nigdy jako bramka
> selekcji) — per `docs/rag/02_cechy_i_leakage.md` "Rozszerzanie feature setu — protokół" i
> CLAUDE.md zasada 4. Pełna diagnoza: `IMPLEMENTATION_PLAN.md` §5 Commit 2.7,
> `runs/2026-09-21_c2.7-feature-candidate-screening/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.7.1 | 8 nowych kandydatek cech (4 rodziny: volatility, momentum, mean-reversion, volume), świadomie nie-redundantnych z registry na podstawie definicji wzoru | ✅ | `backtest/screen_feature_candidates.py` (poza pytest, jak inne skrypty analityczne): `bb_width_20`, `realized_vol_20` (volatility, TA-Lib BBANDS/rolling std log-zwrotów); `roc_20`, `adx_14` (momentum/trend-strength, TA-Lib ADX); `bb_pctb_20`, `vwap_deviation_20` (mean-reversion, TA-Lib BBANDS/rolling VWAP); `obv_zscore_20`, `volume_roc_10` (volume, TA-Lib OBV). Ten sam kontrakt trailing-only co `agents/feature_miner.py`. NIE wchodzą do `FEATURE_FUNCTIONS`/`MOMENTUM_FEATURES`/`REVERSION_FEATURES` — screening przed-rejestracyjny, formalny test leakage dopiero przy promocji |
| C2.7.2 | Macierz korelacji Spearman cecha-cecha (17×17: 9 istniejących + 8 nowych), cały zbiór, próg redundancji opisowy `\|corr\|>0.7` | ✅ | WYNIK: 28 par powyżej progu. Najważniejsze: `bb_pctb_20` **PERFEKCYJNIE redundantny** z już używanym `price_zscore_20` (corr=+1,000, afiniczna transformacja tej samej wielkości) → **ODRZUCONY** bez potrzeby testu OOS. `adx_14` jedyny kandydat z niską korelacją do reszty registry (w tym +0,07 z `direction_persistence_10`, mimo że oba mają mierzyć "siłę trendu") → wyróżniony jako kandydat #1. Rodzina volatility (`bb_width_20`/`realized_vol_20`) silnie redundantna z istniejącymi `atr_14`/`atr_pctrank_20d` (corr 0,79–0,88). `obv_zscore_20` bliżej mean-reversion/momentum niż volume (corr 0,72–0,78 z `price_zscore_20`) |
| C2.7.3 | Korelacja Spearman cecha-target (label triple-barrier jako -1/0/1) per regime, jawnie oznaczona EKSPLORACYJNA (bez p-value, żeby nie sugerować istotności) | ✅ | WYNIK: żadna z 17 cech nie przekracza \|corr\|≈0,065 z targetem w żadnym reżimie (`trend`: n=523, max=-0,065 `volume_roc_10`; `range`: n=22 198, max=-0,035 `realized_vol_20`). Czwarty niezależny sygnał (po C2.5 progach, C2.6 timeframe) spójny z brakiem edge'u — tym razem metodą niezależną od modelu XGBoost. Żadna cecha nie wyróżnia się ponad poziom szumu — decyzja, którą (jeśli jakąkolwiek) testować formalnie w walk-forward, pozostaje przy użytkowniku |

### Commit 2.8 — Formalny test OOS: `adx_14` dodane do MOMENTUM_FEATURES — ✅ ZROBIONE (wynik: NO-GO ogólnie, poprawa marginalna w trend)

> Zakres uzgodniony z użytkownikiem 2026-09-21 ("sformalizować test OOS dla adx_14"):
> jedna cecha (CLAUDE.md zasada 4), DODANA do `MOMENTUM_FEATURES` (Test 1/trend),
> `REVERSION_FEATURES` (Test 2/range) niezmienione. Pełna diagnoza:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.8, `runs/2026-09-21_c2.8-adx14-oos-evaluation/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.8.1 | Promocja `compute_adx_14` do produkcyjnego registry (`agents/feature_miner.FEATURE_FUNCTIONS`, `agents/feature_registry.yaml`) + testy (DoD docs/rag/05) | ✅ | 10. cecha w `FEATURE_FUNCTIONS` — formalny test leakage (parametryzowany po kluczach) automatycznie objął `adx_14` (licznik 9→10, `agent_5_compliance/test_leakage.py`), + nowy jednostkowy test granic [0,100] w `tests/test_feature_miner.py`. Wpis w `feature_registry.yaml` z notatką o pochodzeniu (screening C2.7) i statusie (kandydat do MOMENTUM_FEATURES, nie jeszcze promowany) |
| C2.8.2 | Parametryzacja `regime_feature_sets` w `backtest/engine.py::run_backtest` (ten sam wzorzec threading co progi C2.5/candles_per_day C2.6) + test integracyjny | ✅ | Pozwala porównać warianty feature setu (baseline vs baseline+adx_14) przez identyczny pipeline, bez duplikacji logiki i bez trwałej zmiany `agents/ml_optimizer.py`. Nowy test `test_run_backtest_threads_regime_feature_sets_to_model_training` (dowód przez `KeyError` przy podaniu nieistniejącej kolumny cechy). Pełny zestaw: **128/128 przechodzi** (125 + 3: 1 unit adx_14 + 1 integracyjny + 1 nowa instancja parametryzowanego testu leakage) |
| C2.8.3 | Skrypt `backtest/evaluate_feature_candidate.py` (poza pytest) + uruchomienie: baseline (4 cechy) vs kandydat (+adx_14, 5 cech), pełny walk-forward + 10-seed sweep | ✅ | WYNIK: mean_sharpe -14,31→**-13,69** (poprawa), trend_sharpe -8,46→**-7,11** (poprawa, klasyfikacja NO-GO→**WARUNKOWY**), ale **klasyfikacja OGÓLNA pozostaje NO-GO** w obu wariantach (stabilne, std=0,0000 na 10 seedach). Poprawa w trend opiera się na JEDNYM foldzie (fold_idx=11) zmieniającym Sharpe z -2,40 na +0,09 (praktycznie zero) przy tylko 4 ważnych foldach trend — słaby, niejednoznaczny dowód. `range` (dominujący w werdykcie) kompletnie niezmieniony. **Piąty niezależny wynik w paśmie "brak silnego sygnału"** (po C2.5/C2.6/C2.7). Decyzja o promocji `adx_14` do `MOMENTUM_FEATURES` na stałe — przy użytkowniku; skrypt świadomie nie wybiera zwycięzcy. **Aktualizacja C2.9:** "std=0,0000 na 10 seedach" okazało się puste (deterministyczny XGBoost), a poprawa +0,61 to ~0,2σ zmierzonego szumu fold-jitter — nierozstrzygalna |

### Commit 2.9 — Naprawa metodologii pomiaru (Backlog Z1–Z4, Z11–Z15) — ✅ ZROBIONE (NO-GO odporne na fold-jitter; zwrot per trade istotnie ujemny w obu reżimach)

> Zakres: pierwsza transza backlogu z audytu 2026-09-21, na polecenie użytkownika ("Dopisz i
> wypchnij do repo a później zacznij realizować"). Zero zmian w hipotezie/cechach/progach/
> kosztach/modelu — wyłącznie metodologia pomiaru + higiena. Pełna diagnoza:
> `IMPLEMENTATION_PLAN.md` §5 Commit 2.9, `runs/2026-09-21_c2.9-measurement-methodology/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.9.1 | (Z1) Fold-jitter zamiast pustego sweepu seedów: `start_offset_days` w `generate_walk_forward_folds` + `fold_start_offset_days` w `run_backtest` + testy (unit + hypothesis, DoD Warstwa 3 dla labeling.py + integracyjny threading) | ✅ | Odkrycie audytu: XGBoost bez `subsample`/`colsample` jest deterministyczny — seed nie zmieniał NIC, każde dotychczasowe "std=0,0000 STABILNY" (C6→C2.8, ~10 rund) było puste poznawczo. Offset perturbuje ARBITRALNE wyrównanie granic foldów; offset=0 odtwarza baseline co do ostatniej cyfry. Świadomie bez nowego progu pass/fail — raport rozkładu + spójność znaku, interpretacja przy użytkowniku. docs/rag/03 zaktualizowane |
| C2.9.2 | (Z2+Z3) `compute_t_stat` + kolumna `t_stat` per fold + `summarize_pooled_by_regime` (pooled Sharpe/t-stat per regime) + `effective_sample_size` (C4.4, dotąd nieużywane) wpięte jako `n_eff`/`t_stat_neff` | ✅ | Bez annualizacji (sqrt(~800/rok) przy n=31–37 nadmuchiwał Sharpe do ±20–60). Kryteria klasyfikacji GO/WARUNKOWY/NO-GO NIEZMIENIONE — nowe miary to diagnostyka obok werdyktu. Guard: N_eff przycinany do (0, n], NaN przy n<10 albo zdegenerowanym estymatorze. 5 nowych testów w `tests/test_metrics.py` |
| C2.9.3 | (Z13) `backtest/checkpoint_lib.py` (wspólna biblioteka, FORWARD-LOOKING — historyczne skrypty zamrożone) + `backtest/run_checkpoint_v2.py` (kanoniczny checkpoint v2) + uruchomienie na realnych danych | ✅ | WYNIK: **NO-GO w 10/10 offsetów** (mean_sharpe zakres [-15,89; -6,20], std=3,09, znak ujemny 100%) — pierwsza REALNA weryfikacja odporności werdyktu. Pooled: `range` n=223, **t=-7,15**; `trend` n=135, **t=-2,91**, N_eff=110 → **t_neff=-2,63** — zwrot per trade istotnie ujemny w OBU reżimach. Zmierzony szum σ≈3,1 → porównania wariantów o Δ<~3 nierozstrzygalne na rocznych danych (→ priorytet Z5). `run_checkpoint.py` zostaje jako zamrożony zapis Commitu 6 |
| C2.9.4 | Higiena: (Z11) `candle_minutes` przewleczone do `total_round_trip_cost` + test integracyjny; (Z12) lint 0 błędów (unused numpy, 3×E741); (Z14) README odświeżone (status, struktura z `runs/`); (Z15) test spójności registry↔kod czyta YAML; (Z4) kolumna "Warianty" + suma w `runs/INDEX.md` | ✅ | Pełny zestaw: **139/139 testów przechodzi** (128 + 11: 2 labeling + 5 metrics + 3 engine + 1 zamiana testu registry) |

### Commit 2.10 — Wydłużenie historii danych do 3 lat (Backlog Z5) — ✅ ZROBIONE (NO-GO na nowej bazie; niska liczba ważnych foldów okazała się strukturalna)

> Zakres: Backlog Z5, wykonane na maszynie użytkownika (Binance dostępne). Decyzja użytkownika:
> **3 lata** (2023-07-01 → 2026-07-01), `end` bez zmian. Zero zmian w hipotezie/cechach/progach/
> kosztach/modelu — wyłącznie dane + utwardzenie fetchu. To NOWA BAZA checkpointu, nie porównanie
> 1:1 z C6–C2.9. Pełny wynik: `runs/2026-09-21_c2.10-extended-history-z5/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.10.1 | Utwardzenie `data/fetch_ohlcv.py`: `_fetch_page_with_retry` (backoff wykładniczy na `ccxt.NetworkError`, max 5 prób; `ExchangeError` bez retry) + log postępu; 4 testy (Warstwa 1, stub bez sieci) | ✅ | Powód: ~316 sekwencyjnych stron bez retry, zapis dopiero po pętli — jeden timeout tracił całość. Semantyka cache/nazwy pliku NIEZMIENIONA (nazwa koduje zakres → nowy zakres = nowy plik). Pełny zestaw: **143/143** (139 + 4). Ruff nieuruchomiony — brak na tej maszynie |
| C2.10.2 | `data.start` → 2023-07-01 w config; `py -m data.fetch_ohlcv`; weryfikacja integralności PRZED checkpointem | ✅ | **315 648 świec = 1096×288, zero dziur/duplikatów/NaN**, bez ani jednego retry (~2 min). Overlap 2025-07→2026-07 vs stary plik: 105 120 wierszy, max \|Δ\|=0 na wszystkich kolumnach, `equals=True`. Stary parquet ZOSTAJE jako zamrożone źródło C6–C2.9 |
| C2.10.3 | `py -m backtest.run_checkpoint_v2` (pełny sweep) na nowej bazie + diagnostyka udziału reżimów i bramki kosztowej z `folds_summary` | ✅ | WYNIK: **NO-GO, 21/144 ważnych foldów** (14,6% — jak 15,0% na roku), mean_sharpe -12,39. Pooled: `range` n=530 **t=-10,47** (N_eff=261, t_neff -7,34); `trend` n=395 **t=-5,51** (N_eff=213, t_neff -4,04) — istotnie ujemny zwrot per trade w obu reżimach z dużym zapasem. Fold-jitter 10/10 ujemne, σ≈2,5 bez outliera (offset 9: -189 — artefakt annualizowanego per-fold Sharpe przy n≈kilka; statystyką nośną są pooled t). **Odkrycie strukturalne:** `trend`=0,53% świec (jak na roku) → 61/72 foldów pominiętych; bramka kosztowa blokuje **98,0% sygnałów `range`** (61 313/62 553) → 60/72 foldów z zerem transakcji. Dłuższa historia tego nie naprawia → Z7 (reguła) / Z6 (koszty) / Z10 |

---

### Commit 2.11 — Instrumentacja edge'u (Runda 1/4 programu „droga do GO") — ✅ ZROBIONE (blokada w geometrii wypłaty, nie w kierunku sygnału)

> Zakres: pierwsza runda czterorundowego programu uzgodnionego z użytkownikiem 2026-09-21
> (instrumentacja → koszty Z6 → próg pewności → reguła reżimu Z7, z pre-rejestrowaną regułą
> STOP po Rundzie 3). Zero zmian w pipeline'ie — wyłącznie przyrząd pomiarowy. Pełny wynik:
> `runs/2026-09-21_c2.11-edge-instrumentation/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.11.1 | `break_even_hit_rate`, `compute_hit_rate`, `summarize_edge_by_regime` w `backtest/metrics.py` + wpięcie do `checkpoint_lib.run_and_summarize` / `run_checkpoint_v2` | ✅ | Motywacja: cały werdykt liczy się z `net_pnl`, a `gross_pnl` (jedyna miara jakości SYGNAŁU) było zapisywane i nigdy nieczytane przez `metrics.py`; trafność istniała tylko jako wyrażenia ad hoc w skryptach diagnostycznych, bez testów. Werdykt redukuje się do **(2p−1)·B > C** — raport pokazuje teraz wszystkie trzy człony + margines. Kryteria GO/NO-GO z docs/rag/03 **NIEZMIENIONE** (diagnostyka obok werdyktu, jak Z2/Z3). Testy: **157/157** (143 + 14: 11 unit + 3 `hypothesis`). WYNIK: werdykt bit-identyczny z C2.10 (regresja baseline'u); trafność **51,9%/50,6%** (z=+0,87/+0,25) vs wymagane **75,8%/64,9%** → luka **−23,9 pp / −14,2 pp** |

---

### Commit 2.12 — Realistyczny model wykonania maker/taker (Backlog Z6, Runda 2/4) — ✅ ZROBIONE (NO-GO, ale ok. połowa luki do opłacalności domknięta)

> Zakres: Runda 2 programu „droga do GO". Decyzja użytkownika: maker na wejściu i take-proficie,
> taker na stop-lossie i timeoucie; slippage tylko na nogach taker. Pełny wynik:
> `runs/2026-09-21_c2.12-execution-cost-model/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.12.1 | `backtest/costs.py`: `MAKER_FEE_RATE`, `leg_fee_rate`, `exit_leg_for_reason`, fee per noga + slippage tylko na nogach taker (domyślne taker/taker wstecznie zgodne) | ✅ | Motywacja: `costs.py` modelował WYŁĄCZNIE takera po obu stronach — to nie było założenie konserwatywne, tylko brak modelu. Asymetria TP=maker/SL=taker działa na NIEKORZYŚĆ strategii o niskiej trafności, więc jest konserwatywna wobec hipotezy. Testy: 9 nowych w `test_costs.py` |
| C2.12.2 | `backtest/engine.py`: kolumna `exit_reason` (z iloczynu `direction*label`), `_execution_legs`, parametr `execution_model`; bramka kosztowa dostaje konserwatywne założenie (wyjście taker) | ✅ | Blokada usunięta po drodze: `label` był konsumowany w `_resolve_exit_price` i nie trafiał do journalu, więc nogi wyjścia nie dało się wycenić. Sam `label` nie wystarcza — short na etykiecie −1 to TP, nie SL. Testy: 16 nowych w `test_engine.py`, w tym **regresja baseline'u** (`taker_only` odtwarza koszt sprzed C2.12 co do cyfry) |
| C2.12.3 | Pełny `run_checkpoint_v2` (kanoniczny + sweep fold-jitter) na 3 latach | ✅ | WYNIK: **NO-GO**, ale koszt **−52%**, foldy ważne **21→54**, transakcje `range` **530→7 155**, zwrot per trade **+35%/+39%**, margines **−23,9→−15,5 pp** / **−14,2→−9,1 pp**. `trend` t_neff = **−1,75** (\|t\|<2, nieodróżnialny od zera). Sprzężenie: tańszy koszt wpuszcza sygnały o węższej barierze (B −25%/−19%), więc break-even spadł tylko o 9,2/5,9 pp. **Ostrzeżenie:** `mean_sharpe` −12,4→−59,6 przy LEPSZEJ ekonomice per trade, fold-jitter σ 3,1→75,7, spójność znaku 100%→80% — per-fold Sharpe (podstawa kryteriów docs/rag/03) przestał być wiarygodnym przyrządem. Testy: **182/182** |

---

### Commit 2.13 — Próg pewności kalibrowany wewnątrz walk-forward (Runda 3/4) — ✅ ZROBIONE (hipoteza SFALSYFIKOWANA, reguła STOP uruchomiona)

> Zakres: Runda 3 programu „droga do GO". Hipoteza, próg i kryterium sukcesu zarejestrowane
> PRZED uruchomieniem (`runs/2026-09-21_c2.12-*.md`, sekcja Rekomendacja). Pełny wynik:
> `runs/2026-09-21_c2.13-confidence-threshold/README.md`.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| C2.13.1 | `_train_fold_confidence_threshold` + parametr `confidence_quantile` + liczniki `n_signals_confidence_gated`/`confidence_threshold` w `folds_summary` | ✅ | Próg liczony WYŁĄCZNIE na foldzie treningowym (kwantyl zbioru testowego byłby dobraniem progu pod dane, na których mierzymy wynik). Jawne zastrzeżenie: predykcje na treningu są in-sample, więc próg jest ZAWYŻONY → przepuszcza mniej, niż sugeruje nominalne q (46 239 odrzuconych vs 4 631 przepuszczonych) — obciążenie działa na niekorzyść hipotezy. Domyślnie `None` = baseline odtwarzalny co do cyfry. Testy: 8 nowych, w tym rozstrzygający „próg z train, nie z test" |
| C2.13.2 | `backtest/evaluate_confidence_threshold.py` (poza pytest, na `checkpoint_lib`) + uruchomienie baseline vs kandydat | ✅ | **WYNIK: kryterium NIESPEŁNIONE.** `range`: hit 51,07%→51,41%, margin −15,5→−14,7 pp, z_margin **−17,11**. `trend`: hit **49,86%→45,54%** (spadek o 4,32 pp, w stronę PRZECIWNĄ do przewidywanej), margin −9,1→−13,2 pp, z_margin **−2,66**, n spadło 355→101. Klasyfikacja NO-GO→NO-GO. Monotoniczny „skill" zmierzony przed programem okazał się **artefaktem selekcji post hoc**. Testy: **190/190** |
| C2.13.3 | Reguła STOP | ✅ | Warunek spełniony (`z_margin` ≪ +2 w obu reżimach) → **Runda 4 (C2.14 / Z7) NIE uruchomiona.** Uruchomienie jej po zobaczeniu negatywnego wyniku byłoby dokładnie tym, czemu reguła STOP zapobiega. Budżet multiple-testing na nowej bazie = **2**. Decyzja Z10 przy użytkowniku |

---

### Seria S — architektura jednoreżimowa 4h (NOWA hipoteza) — ❌ ZAMKNIĘTA regułą STOP

> Nowa hipoteza wobec dwureżimowej z `docs/rag/01`: jeden reżim (`range`), natywne świece 4h,
> 6,8 roku historii, spójny horyzont V=3. Własny licznik wariantów, własna reguła STOP.
> Konfiguracja zamrożona w pre-rejestracji (Z5b) PRZED uruchomieniem.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| S1 | Pomiar trafności na architekturze jednoreżimowej 4h | ❌ **WYNIK NEGATYWNY** | n=1 037 (>925, wynik rozstrzygający). Trafność **48,60%**, CI [45,56%; 51,64%] — **górny kraniec poniżej progu 53,07%**, czyli z 95% pewnością trafność jest NIŻSZA od progu opłacalności. Bramka kosztowa odrzuciła 0% sygnałów (geometria naprawiona, nie pomogło). Testy 246/246. **REGUŁA STOP URUCHOMIONA — seria zamknięta, licznik 1/1.** `runs/2026-09-22_s1-single-regime-4h/README.md` |

**Stan hipotezy po S1:** runda usunęła wszystkie znane wady pomiaru naraz (przeciek early
stopping, brak embargo, niespójność bramka↔horyzont, zepsuty wolumen z resampla, bariera
zjadana przez koszt, za mała próba, patologia per-fold Sharpe). Po ich usunięciu trafność
wynosi **48,60%**. Każda naprawa zostawiała `p` niezmienione albo nieznacznie gorsze — ani
razu lepsze. **Uczciwa rekomendacja: Z10 opcja 1 — udokumentowane zamknięcie Fazy 0 wynikiem
negatywnym.** Decyzja przy użytkowniku.

---
### Faza 1 — regime router, funding rate, Compliance Gate

> Start dopiero po wyniku GO/WARUNKOWY z Commitu 6.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F1.1 | Regime router (dispatcher) łączący Test 1 + Test 2 | ⏳ | |
| F1.2 | Funding rate jako cecha Test 2 — jedna cecha na raz, test leakage, OOS | ⏳ | CLAUDE.md zasada 4 |
| F1.3 | Compliance Gate budowany równolegle (nie po fakcie) | ⏳ | |
| F1.4 | Cadence retreningu — harmonogram + triggered retrain przy spadku live performance | ⏳ | Brakujący temat z diagramu Miro, §10 |
| F1.5 | Rozszerzenia cech pojedynczo na OOS: MACD, Bollinger, GMMA | ⏳ | Częściowo redundantne z istniejącymi cechami — testować pojedynczo |
| F1.6 | Onchain data jako kandydat cechy do Test 2 | ⏳ | |
| F1.7 | `Lean.DataSource.BinanceFundingRate` jako źródło danych funding rate | ⏳ | §10 |
| F1.8 | Rozszerzenie walidacji na ETH/SOL/BNB — te same progi i hiperparametry co BTC, bez retuningu | ⏳ | CLAUDE.md zasada 9 — test generalizacji tej samej hipotezy, nie równoległa walidacja 4 niezależnych strategii; start dopiero PO indywidualnej walidacji BTC do końca Commitu 6 |
| F1.9 | Multi-timeframe (Trend/Day/Hour) — potwierdzenie trendu z wyższego interwału | ⏳ | Dopiero po walidacji na 5m, §10 — osobny wymiar złożoności |
| F1.10 | Trailing Stop/Take Profit w `risk_controller.py` | ⏳ | Ulepszenie po walidacji statycznej wersji ATR (Commit 5.5), §10 |
| F1.11 | Expected Shortfall jako uzupełnienie VaR | ⏳ | Naturalne uzupełnienie ogona rozkładu strat, §10 |
| F1.12 | CatBoost / RandomForest jako porównanie/ensemble | ⏳ | Tylko PO potwierdzeniu edge'u XGBoostem (Commit 6 GO), nie zamiennik na start, §10 |
### Faza 2 — LLM offline/nadzorczo (Q&A) + test_mathematics.py

> Pełne uzasadnienie i wzorce: `docs/rag/06_llm_nadzorczy_i_baza_wiedzy.md`. Nic z tej sekcji nie
> jest budowane przed checkpointem go/no-go Commitu 6.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F2.1 | `test_mathematics.py` — property-based testy niezmienników na realnych/backtestowych danych | ⏳ | Zostaje deterministyczny, bez LLM |
| F2.2 | `ai_interpreter.py` — narzędzia `get_fold_metrics`/`get_feature_definition`/`get_trade_journal`/`get_rag_doc` | ⏳ | Zero narzędzi zapisu/egzekucji |
| F2.3 | Observability/evals minimalny (structured JSON log, eval dataset 20-30 przykładów, human-graded) | ⏳ | |
| F2.4 | Bezpieczeństwo: zero narzędzi zapisu/egzekucji, system prompt traktowany jako publiczny | ⏳ | |
### Faza 3 — paper trading + post_trade_critic.py

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F3.1 | Paper trading / testnet, minimum kilka tygodni | ⏳ | |
| F3.2 | LEAN jako silnik paper tradingu (zamiast freqtrade) | ⏳ | Zaktualizowana rekomendacja, §10 |
| F3.3 | `post_trade_critic.py` — verbal-reinforcement po FinCon, raport markdown | ⏳ | Nigdy automatyczna zmiana parametrów/modelu — tylko raport |
| F3.4 | Weryfikacja formatu trade journal z Commitu 5 pod kątem realnych potrzeb `post_trade_critic.py` | ⏳ | |
### Faza 4 — mały kapitał, skalowanie

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| F4.1 | Uruchomienie na małym kapitale (w pełni tolerowalna strata) | ⏳ | |
| F4.2 | Skalowanie po potwierdzeniu wyników | ⏳ | |

---
### Dokumentacja i workflow — niezależne od fazowania

> Można wykonać w dowolnym momencie, nie dotyka logiki tradingowej ani configu.

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| D.1 | YAML frontmatter (`status`, `last_verified`, `depends_on`) w każdym `docs/rag/*.md` | ✅ | Dodane 7/7 plikom (`01`–`07`); legenda wartości `status` (`active`/`stale`/`superseded`) w `docs/INDEX.md` |
| D.2 | Plik-indeks (Mapa Treści) linkujący `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` + `docs/rag/*.md` | ✅ | `docs/INDEX.md` — linkuje `CLAUDE.md`+`IMPLEMENTATION_PLAN.md`+`TASKS.md`+`README.md`+7 plików `docs/rag/*.md`, jednozdaniowy opis każdego. `README.md` "Mapa dokumentacji" rozszerzona o brakujące 06/07/`TASKS.md` i zlinkowana do `docs/INDEX.md` jako pełne źródło |
| D.3 | Formalizacja roli `IMPLEMENTATION_PLAN.md` jako "Observational Memory" — rozdzielenie na "aktualny stan" vs "archiwum decyzji" | ⏳ | Dopiero gdy plik znacząco urośnie (np. po Fazie 1) |
| D.4 | Odpowiedzieć na otwarte pytania z `docs/rag/07`: czy spotkanie/zespoły (Data Engineering/Quantitative Research/Risk Management) są realne, kto ma finalną decyzyjność przy konflikcie z `CLAUDE.md` | ⬜ | Blokuje D.5 |
| D.5 | Eskalacja rozbieżności terminów action items ze spotkania (15.08/30.08/10.09.2026, `docs/rag/07`) PRZED 15.08.2026, jeśli zobowiązania zespołów są realne | ⬜ | Rekomendacja z `docs/rag/07`; warunkowe od odpowiedzi na D.4 |

---

---

## 16. Backlog

### Backlog — przegląd całego projektu 2026-09-21 (po serii C2.5–C2.8)

> Wynik pełnego audytu kodu, metodologii, dokumentacji i infrastruktury (2026-09-21, po pięciu
> rundach C2.5–C2.8 w paśmie "brak silnego sygnału"). Zadania pogrupowane wg wartości;
> rekomendowana kolejność: **Z1 → Z5 → Z10** (Z6 tuż za nimi). Statusy aktualizowane w miarę
> realizacji; szczegóły każdej rundy realizacyjnej trafiają jak zwykle do sekcji Commitów +
> `runs/`.
>
> **Stan po Commicie 2.13 (2026-09-21):** program „droga do GO" zatrzymany regułą STOP;
> nowe ustalenia i zadania Z16–Z24 w sekcji **E** niżej.
>
> **Stan po Commicie 2.10 (2026-09-21):** Z1–Z5 i Z11–Z15 zamknięte. **Z5 zrealizowane na
> Twojej maszynie** (3 lata, 315 648 świec, zero dziur): NO-GO z twardszymi pooled t-statami
> (range -10,47, trend -5,51), ale odsetek ważnych foldów NIE wzrósł (14,6%) — problem jest
> strukturalny: `trend`=0,53% świec, bramka kosztowa blokuje 98% sygnałów `range`. Otwarte:
> **Z6** (koszty — przy 98% blokady bramka jest werdyktem o kosztach), **Z7** (reguła reżimu —
> adresuje pusty `trend`), **Z8/Z9** (Z9 teraz wykonalne z tej maszyny) oraz **Z10** (decyzja
> strategiczna — przy Tobie; `runs/2026-09-21_c2.10-extended-history-z5/README.md`, sekcja Rekomendacja).

### A. Wiarygodność pomiaru

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z1 | **Naprawić sweep stabilności — obecnie mierzy NIC** | ✅ C2.9 | `DEFAULT_XGB_PARAMS` bez `subsample`/`colsample_bytree` ⇒ XGBoost w pełni deterministyczny ⇒ seed niczego nie zmienia. Stąd std=0,0000 w KAŻDYM eksperymencie od Commitu 6 (identyczne do ostatniej cyfry). Zastąpić perturbacją, która coś robi: jitter przesunięcia startu okien walk-forward (offset 0–9 dni) — perturbuje PODZIAŁ danych, nie model, więc baseline pozostaje porównywalny |
| Z2 | Per-fold t-stat + pooled Sharpe per regime (diagnostyka obok, nie zamiast klasyfikacji) | ✅ C2.9 | Annualizacja sqrt(~800/rok) przy n=31–37 transakcji daje Sharpe -22/-65 — statystycznie bez sensu. Dodać t-stat i zbiorczy (pooled po foldach) Sharpe per regime; rozważyć Deflated Sharpe Ratio |
| Z3 | Wpiąć `effective_sample_size` (labeling.py, C4.4) do raportu checkpointu | ✅ C2.9 | Funkcja istnieje, jest przetestowana i NIGDZIE nieużywana — caveat "N_eff ≪ N" z docs/rag/03 jest dziś czysto teoretyczny |
| Z4 | Licznik multiple-testing w `runs/INDEX.md` | ✅ C2.9 | Kolumna "ile wariantów przetestowano w tej rundzie" — jawna księga budżetu statystycznego (C2.5: 4, C2.6: 2, C2.7: screening, C2.8: 1) |

### B. Realne dźwignie na wynik hipotezy

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z5 | **Wydłużyć historię danych do 3–5 lat** | ✅ C2.10 | Zrealizowane na maszynie użytkownika (2026-09-21): decyzja użytkownika **3 lata** (2023-07-01 → 2026-07-01), `data.start` w config, `py -m data.fetch_ohlcv` → `data/raw/BTC-USDT-USDT_5m_20230701T000000Z_20260701T000000Z.parquet`, **315 648 świec = 1096×288, zero dziur**, overlap 2025-07→2026-07 identyczny co do bajtu ze starym plikiem (który ZOSTAJE jako zamrożone źródło C6–C2.9). Pętla fetch dostała retry/backoff na `ccxt.NetworkError` (+4 testy). Wynik checkpointu v2 na nowej bazie: sekcja Commit 2.10 + `runs/2026-09-21_c2.10-extended-history-z5/README.md` |
| Z6 | Zweryfikować założenia kosztowe (kandydat (c) z §7 IMPLEMENTATION_PLAN.md) | ✅ C2.12 | Koszty są OSIĄ werdyktu od Commitu 2d, a `taker=0.05%`/`slippage=2bps`/`funding=0.01%/8h` to wartości startowe. Realny tier fee, udział maker (0.02%), realne dane funding |
| Z7 | Reguła regime na `adx_14` zamiast/obok dyskretnej `direction_persistence_10` | ⏳ | Osobny, z góry zarejestrowany eksperyment NA REGULE (nie modelu). Motywacja z trzech niezależnych rund: dyskretność persistence (C2.5), corr adx↔persistence=+0,07 (C2.7), błędna klasyfikacja trendu spadkowego jako `range` (C2c) |
| Z8 | Rozdzielić timeframe od horyzontu trzymania | ⏳ | Nierozdzielony confound C2.6: `VERTICAL_BARRIER_CANDLES=12` = 1h @ 5m, ale 48h @ 4h. Przeliczyć proporcjonalnie jako jawnie nazwany eksperyment |
| Z9 | Walidacja natywnych świec 1h/4h vs resample z 5m | ✅ **ZROBIONE** | WYNIK: ceny zgodne co do grosza, ale **wolumen rozjezdza sie w 11% swiec 1h i 6% swiec 4h** (bledy do 284%) — a `volume_zscore_20` jest cecha obu modeli, wiec C2.6 dostawal czesciowo zepsute wejscie. Dane 1h/4h pobrane i odlozone w `data/raw/` (cache trwaly). **Dodatkowo:** prog oplacalnosci `range` spada 82,81% (5m) -> 56,77% (1h) -> **52,74% (4h)** — pierwszy realistyczny prog w projekcie. `runs/2026-09-22_z9-timeframe-geometry/README.md`. Pierwotny opis: Wymaga maszyny użytkownika (dostęp do Binance); sprawdza, czy agregacja z 5m nie zniekształca wyniku C2.6 |
| Z10 | **DECYZJA STRATEGICZNA: rewizja hipotezy czy domknięcie Fazy 0** | ✅ **ROZSTRZYGNIĘTE 2026-09-22** | **Decyzja użytkownika: ZAMKNĄĆ Fazę 0 wynikiem negatywnym ORAZ otworzyć nową hipotezę (H2) jako osobny byt.** Liczba zamykająca (policzona od zera z `raw_output.txt`, nie z syntez): pooled `p` = **50,27%**, n=7 687, CI95 [49,15%; 51,38%], z=+0,47 — **górny kraniec CI leży 1,30 pp poniżej najniższego progu opłacalności (52,69%) przy mocy 2,8×**, czyli dowód braku, nie brak dowodu. Wąskie gardło **informacyjne** (wszystkie 10 cech to transformacje ceny/wolumenu). Jawnie NIEPRZETESTOWANE: momentum, ETH/SOL/BNB, funding-jako-sygnał, ekonomia dźwigni, target≠kierunek. Obie reguły STOP **aktywne na stałe**; H2 ma własny licznik od zera. → [runs/z10](runs/2026-09-22_z10-zamkniecie-fazy-0/README.md) |
| **H2** | **NOWA HIPOTEZA: funding rate jako źródło informacji spoza OHLCV** | ⚪ **ZAMKNIĘTA 2026-09-22, bez rozstrzygnięcia** | Licznik **1/1 wyczerpany**, reguła STOP zamknęła serię. H2.0: dane pobrane (7 457 rekordów, 0 dziur) + rachunek mocy odrzucił 2 z 3 sformułowań za 0 wariantów. H3: próg sprostowany 53,12% → 52,69%. **[H2.1](runs/2026-09-22_h2.1-funding-jako-cecha/README.md) — NIEROZSTRZYGNIĘTY** (`n = 98 < 1 000`): zdjęcie bramki podniosło udział klasy dominującej 60,83% → 66,58%, model odmawia kierunku w **99,3%** świec. ~~Funding potroił liczbę decyzji (35 → 98) — jedyne ustalenie rundy.~~ **⚠ USTALENIE WYCOFANE 2026-09-22 (F1):** „potrojenie” NIE odtwarza się na naprawionym przyrządzie — przy n ~8 000 funding zmienia liczbę decyzji o **1%** (8 114 → 8 196), a nie trzykrotnie. Był to artefakt zagłodzonej próby: przy 35 decyzjach dowolne zaburzenie posteriora mnoży tę liczbę wielokrotnie → [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md). Bramka leakage ZIELONA (19/19) przed eksperymentem |
| **H3** | Model kosztów: analiza wrażliwości na nogę `timeout` | ✅ **ZAMKNIĘTE 2026-09-22** | **Teza obalona przez własną rundę.** Kryterium: noga maker wymaga znanej CENY, a przy barierze pionowej znamy tylko CZAS ⇒ `taker` jest POPRAWNE. Zmierzone pasmo progu **[51,64%; 52,69%]** (60,00% timeoutów) — **D3: niepewność nieistotna decyzyjnie**, domyślna `TAKER` bez zmian. Naprawiona usterka strukturalna: bramka kosztowa miała własną kopię reguły nóg i literał, teraz wyprowadzana z tej samej funkcji co journal (**usunięta klasa błędu**). Sprostowane dwie moje liczby: próg H2.1 **53,12% → 52,69%** i ostrzeżenie o funding (błędne co do znaku). Testy 308/308. → [runs/h3](runs/2026-09-22_h3-noga-timeout-pasmo/README.md) |
| **H4** | Carry przekrojowy na wielu instrumentach | ⬜ | Wykonalny statystycznie przy ~20+ instrumentach (H2.0: ograniczeniem jest liczba nienakładających się okien w CZASIE, nie próg). Wymaga silnika portfelowego, którego Faza 0 nie ma, i łamie zasadę 9. Odnotowane jako kierunek, nie propozycja rundy |

### E. Backlog II — po programie „droga do GO" (C2.11–C2.13), audyt 2026-09-21

> Powstał po uruchomieniu reguły STOP (C2.13). Podstawa: 5 niezależnych diagnoz + 15
> adwersarialnych weryfikacji (wszystkie 5 pierwotnych propozycji rund ODRZUCONE — po 2–3
> głosy na każdą) + własna weryfikacja kluczowych liczb na realnych danych.
>
> **USTALENIE PRZEWODNIE (zweryfikowane niezależnie, 315 648 świec):** bramka reżimu i target
> **mierzą różne horyzonty**. Mediana nieprzerwanego epizodu reżimu to **2 świece (10 min)**
> dla `trend` i **5 świec (25 min)** dla `range`, podczas gdy `VERTICAL_BARRIER_CANDLES=12`
> to **60 min**. Tylko **4 z 728** epizodów `trend` jest dość długich, by pomieścić pełne okno
> etykiety. Praktycznie każda transakcja `trend` jest etykietowana ruchem ceny, który w
> większości dzieje się POZA reżimem uzasadniającym wejście. To nie jest „brak edge'u" — to
> **niespójna specyfikacja sygnału**, i wyjaśnia, dlaczego człon `p` był nieruchomy w dwóch
> niezależnych, pre-rejestrowanych próbach.
>
> **KONSEKWENCJA DLA CZŁONU B:** wymagane B = C/(2p−1) = **3,15% ceny** (15,5× obecnego),
> co implikuje horyzont rzędu dni. Maksymalny epizod `range` w 3 latach to 5h15m; okien 12h/48h
> w całości wewnątrz reżimu jest **zero**. Z8 nie jest „za mało danych" — jest **niewykonalne
> przy obecnej definicji reżimu**. W `trend` dodatkowo p=49,86% < 50%, więc (2p−1) < 0 i
> ŻADNA szerokość bariery nie pomaga.

| ID | Zadanie | Status | Koszt budżetu | Uwagi |
|---|---|---|---|---|
| Z16 | **Diagnostyka spójności bramki reżimu z horyzontem etykiety** (`agents/regime_coherence.py` + `backtest/diagnose_regime_coherence.py`) | ✅ **ZROBIONE** | **0** | WYNIK: `trend` **0,49%** świec z etykietą wewnątrz własnego reżimu (mediana epizodu 2 vs horyzont 12), `range` 21,1%. Z8 domknięty (B wymagane 4,21% => horyzont ~39 dni vs epizod 5h15m; w `trend` 2p−1<0). **Asymetria: `range` uspójnialny (mediana 5→39 przy udziale 46,9%), `trend` NIE (udział zapada do 0,05–1,5%).** Testy 214/214. `runs/2026-09-22_z16-regime-coherence/README.md`. Pierwotny opis: Formalizuje ustalenie przewodnie: rozkład długości epizodów per reżim + udział świec z pełnym oknem etykiety wewnątrz epizodu, dla V ∈ {12, 48, 144, 576}. Zamienia „nie znaleźliśmy edge'u" w mechanizm. **Zamyka Z8 bez wydawania wariantu.** Kryterium: udział `trend` z pełnym oknem < 5% (zmierzone: 0,55%) |
| Z17 | Naprawa przecieku early stopping (`agents/ml_optimizer.py:130` — `evals=[(dtest,"test")]`) | ✅ **ZROBIONE** (razem z Z21 — ta sama granica) | 0 | WYNIK: kierunek obciążenia potwierdzony, `p` było ZAWYŻONE. `range` hit 51,07%→**50,38%**, z_stat **+1,81→+0,63** — „bliskość istotności" z C2.12 była artefaktem przecieku. Testy 226/226. `runs/2026-09-22_z17-z21-early-stopping-leak/README.md`. Pierwotny opis: Early stopping wybiera liczbę drzew NA FOLDZIE OOS. Udokumentowane jako „decyzja" w docstringach i `config/settings.yaml:48` — dokumentacja opisuje buga jako wybór. Kierunek obciążenia: **ZAWYŻA `p`**. Wymaga `validation_fraction` (ogon foldu treningowego) + guard na `best_iteration` w 3 miejscach (`ml_optimizer.py:167`, `engine.py:357`, `diagnose_range_signal.py:138` — `AttributeError` na xgboost ≥2.0 bez ES). Zależność: **Z16 najpierw** |
| Z18 | Jedna definicja `p` | ✅ **ZROBIONE** | 0 | Zarzut audytu o trzech definicjach byl PRZESADZONY — `gross_pnl>0` uzywane spojnie; realny rozjazd dotyczy wylacznie timeoutow. Zmierzony: naiwna definicja zaniza o +5,6/+8,0 pp. **Kluczowe:** trafnosc na samych barierach poziomych = 50,50%/50,20% — edge nie chowa sie w zadnej skladowej. Testy 231/231. `runs/2026-09-22_z18-unify-hit-rate/README.md`. Pierwotny opis: Dziś w obiegu TRZY niekompatybilne definicje (`gross_pnl>0` z filtrem kill-switcha, `dir*label>0` bez timeoutów, `gross_pnl>0` na pełnej populacji), różniące się o 6–14 pp. Do czasu ujednolicenia każdy przyszły pomiar `p` jest nieporównywalny |
| Z19 | Moc statystyczna przed eksperymentem + `z_margin` do `metrics.py` | ✅ **ZROBIONE (moc)** | 0 | `wald_half_width`, `min_detectable_hit_rate`, `required_trades` + 11 testów. WYNIK: **4h NIEWYKONALNE** (foldy 21,5 < 30; próba 1 551 < 2 608), **1h `range` jedyna wykonalna** (n<=5 600 vs 425; próg 56,77%, trzeba zmierzyć 58,08%). Obaliło rekomendację z Z9 przed wydaniem budżetu. `runs/2026-09-22_z19-statistical-power/README.md`. Przeniesienie `z_margin` — nadal otwarte. Pierwotny opis: Statystyka, na której stanął werdykt C2.13, mieszka w jednorazowym skrypcie rundy |
| Z20 | Warunek „zgodny znak" z `docs/rag/03:103` — zaimplementować albo skorygować docs | ⬜ | 0 | `fraction_positive_sign` (`metrics.py:296,312`) liczone i zwracane, **nigdy nieczytane**. Bramka GO jest ściśle słabsza niż udokumentowana. Uwaga: to NIE podważa dotychczasowego NO-GO (osłabia tylko GO) |
| Z21 | Purge/embargo na granicy train/test | ✅ **ZROBIONE** (w Z17 — walidacja z ogona treningu wymagała embargo, inaczej naprawa byłaby pozorna) | 0 | `test_start == train_end`, zero purge w całym repo (grep: 0 trafień). Etykiety ostatnich ≤V świec treningu sięgają w okno testowe: 0,069% wierszy/fold przy V=12, ale **rośnie liniowo z V** (3,33% przy V=576) — blokujące dla każdej rundy z długim horyzontem |
| Z22 | `run_backtest`: parametr `vertical_barrier_candles` | ✅ **ZROBIONE** (w S1) | 0 | Horyzont etykiety jest parametrem; `embargo_candles=None` domyślnie **wiąże się z V**, więc nie da się ich rozjechać przez przeoczenie (to samo zabezpieczenie co zasada 3 dla mnożnika ATR). `atr_multiplier` celowo NIE parametryzowany — musiałby zmienić się jednocześnie w `risk_controller`. 4 testy. Pierwotny opis: Dziś `compute_triple_barrier_labels(df)` wołane bez argumentów, `ATR_MULTIPLIER` jako stała modułowa (`engine.py:321`). **Blokada metodologiczna:** żadnego eksperymentu na geometrii nie da się zrobić baseline-vs-wariant w jednym procesie. CLAUDE.md zasada 3: mnożnik musi zmienić się JEDNOCZEŚNIE z `risk_controller` |
| Z23 | Higiena | ⬜ | 0 | `README.md:27` 143→190 testów • `.claude/settings.json` przypadkowo zacommitowany w C2.11 (artefakt narzędzia) — odpiąć za zgodą użytkownika • przywrócenie pełnej tabeli per-fold w `runs/2026-09-21_c2.12-*.md` |

**Zadania HIPOTEZOWE (kosztują budżet, wymagają świadomego nadpisania reguły STOP przez użytkownika).**
Budżet na nowej bazie danych: **2 warianty wydane** (C2.12, C2.13).

| ID | Zadanie | Status | Koszt | Uwagi |
|---|---|---|---|---|
| Z8 | Rozdzielenie timeframe od horyzontu (geometria wypłaty) | ✅ **ZAMKNIĘTE przez Z16 — niewykonalne przy obecnej definicji reżimu** | 0 | Niewykonalne przy obecnej definicji reżimu (patrz ustalenie przewodnie). Zamknąć jako „ODŁOŻONE — niewykonalne", NIE jako „zmierzone negatywnie" — hipoteza bez uruchomienia nie jest zmierzona |
| Z7 | Reguła reżimu na `adx_14` | ⬜ przeformułowane przez Z16 — kryterium `is_rule_admissible` gotowe | screening **0**, potem OOS **1** | W obecnym brzmieniu atakuje nieruchomy człon `p` i jest zwykłym kolejnym wariantem po negatywnym wyniku. Po Z16 da się przeformułować na kryterium **mierzalne bez modelu**: reguła jest dopuszczalna, gdy mediana długości epizodu ≥ horyzont etykiety przy udziale reżimu ≥ 5% świec. Screening kandydatów pod tym kryterium nie dotyka modelu (0 wariantów). **Bez Z16 nie uruchamiać** |
| Z24 | Porzucenie bramki reżimu — handel na `ambiguous` (77,9% świec) | ⬜ | 1 (NOWA seria) | Empirycznie najlepiej uzasadniona z otwartych, ale to **NOWA hipoteza**, nie wariant obecnej (docs/rag/03 przy NO-GO: „wróć do feature registry — inna hipoteza, NIE tuning tego samego zestawu"). Własna pre-rejestracja, własny licznik, własna reguła STOP. Nie łączyć z Z7 |
| Z5b | Pełna historia 2019→2026 (**dla 4h**) | ✅ **ZROBIONE** | 0 | Pobrane i odłożone: **14 916 świec 4h, 6,8 roku, zero dziur**. 4h przeszło na WYKONALNE (foldy 21,5→48,0; próba 1 551→4 076). Nowy pomiar koryguje Z19: przy V=3 **60,8% to timeouty**, więc próg rośnie 52,30%→**54,60%**. Wybrano V=3 (spójność = wymóg poprawności). **Eksperyment PRE-ZAREJESTROWANY, nieuruchomiony** — kryterium: trafność ≥ 56,15%, margines mocy 4,3×, klauzula nierozstrzygalności przy n<925. `runs/2026-09-22_z5b-long-history-4h-preregistration/README.md`. Pierwotny opis: Odrzuciłem to jako „nie domyka żadnego członu" — prawda na 5m, **nieprawda na 4h**, gdzie wiążącym ograniczeniem jest liczebność próby. 4h od 2019-09 (~6,8 roku) dałoby ~3 600 świec `range` wobec wymaganych 2 608 — czyli **odblokowałoby konfigurację o najniższym progu w projekcie (52,74%)**. Wymaga też okna testowego 28 dni zamiast 14 | Nie domyka żadnego członu. Jedyny nowy deliverable (tabela mocy) liczy się na istniejących danych w sekundy, bo udział reżimu jest własnością REGUŁY, nie epoki rynkowej |

**Rekomendowana kolejność:** Z16 → **decyzja Z10 użytkownika** → jeśli zamknięcie Fazy 0:
Z18+Z23 do dokumentu zamykającego, Z17 jako adnotacja o skonfundowanym `p`; jeśli kontynuacja:
Z17, Z18, Z21, Z22, potem Z7 screening (0) i dopiero Z7 OOS (1 wariant).
**Z16 nie zdejmuje reguły STOP** — zdejmuje ją wyłącznie decyzja użytkownika (Z10).

---

### C. Poprawność jednostek / drobne bugi

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z11 | Przewlec `candle_minutes` przez `run_backtest` → koszty | ✅ C2.9 | `costs.CANDLE_MINUTES=5` zahardkodowane — funding przy 1h/4h liczony jak dla 5m (12×/48× zaniżony; materialnie mały, ~0,0004%, ale ten sam typ buga jednostek co naprawiony `candles_per_day`) |
| Z12 | Lint: nieużywany `import numpy` w engine.py, 3× E741 (`l`) w test_engine.py | ✅ C2.9 | Istniały przed C2.5–C2.8; opcjonalnie ruff/black w CI |

### D. Higiena kodu i procesu

| ID | Zadanie | Status | Uwagi |
|---|---|---|---|
| Z13 | Wspólna biblioteka checkpointu (`backtest/checkpoint_lib.py`) — FORWARD-LOOKING | ✅ C2.9 | `_load_config`/`_fetch_data`/`_run_and_summarize`/sweep/stabilność skopiowane 4× (run_checkpoint, calibrate, timeframe, evaluate). UWAGA: historycznych skryptów NIE refaktorować wstecz — są zamrożonymi zapisami eksperymentów, odtwarzalnymi komendą z `runs/` ("Metadane"); biblioteka obowiązuje od nowych skryptów |
| Z14 | Odświeżyć README.md | ✅ C2.9 | Status "Commit 6, 86/86 testów" nieaktualny (128/128, seria C2.5–C2.8), struktura bez `runs/` |
| Z15 | Test spójności registry↔kod jako pytest czytający YAML | ✅ C2.9 | `test_feature_functions_covers_all_ten` hardkoduje listę zamiast czytać `feature_registry.yaml`; check inline w tests.yml zostaje jako belt-and-suspenders |
| Z25 | Odchudzenie duplikacji PLAN↔TASKS (19 zduplikowanych sekcji per-commit, 99+69 KB) | ⏳ | Audyt 2026-09-22: PLAN i TASKS to NIE to samo (PLAN: decyzje/ryzyka/roadmapa; TASKS: statusy/zasady/backlog), ale sekcje per-commit są kopiowane 1:1 w 19 przypadkach, a od C2.9 syntezy żyją też w runs/INDEX. Docelowy podział: CLAUDE.md, wytyczna "jedna informacja = jedno miejsce". Odchudzić historyczne sekcje (szczegóły→runs/, w PLAN/TASKS status+2-3 zdania+link); od teraz nowe rundy piszą od razu krótko |

---

## 17. Mapa drogowa po zamknięciu Fazy 0 (ułożona 2026-09-22)

> **Prostym językiem (zasada 17):** Faza 0 sprawdziła, czy da się zarobić, przewidując kierunek
> ceny z samego wykresu. Nie da się — i to jest odpowiedź mocna, nie wymijająca. Teraz
> sprawdzamy **ostatnią nieprzetestowaną możliwość**: czy pomoże informacja, która nie jest
> przetworzoną ceną. Poniżej jest plan tego sprawdzenia i tego, co robimy z każdym możliwym
> wynikiem — **łącznie z wynikiem „nie pomogło"**, bo on jest najbardziej prawdopodobny.

### Zasada porządkująca całą mapę

Warunek zarobku to `(2p−1)·B + F > C`: trafność `p`, szerokość bariery `B`, przychód z funding
`F`, koszt `C`. Faza 0 ruszyła `B` i `C` do granic możliwości. **Zostało `p` i `F`** — i to one
wyznaczają kolejność zadań poniżej.

---

### ETAP 1 — H2.1: czy informacja spoza OHLCV rusza trafność — ⚪ **ZAMKNIĘTY 2026-09-22**

> **Status:** H2.1 wykonane, wynik **NIEROZSTRZYGNIĘTY** (`n = 98 < 1 000`), licznik H2
> **wyczerpany (1/1)**, reguła STOP zamknęła serię. Sekcja niżej opisuje plan sprzed
> uruchomienia i zostaje jako zapis tego, co zaplanowano — nie jako zadanie do zrobienia.

**Pytanie:** wszystkie 10 dotychczasowych informacji to przetworzona cena i obrót. Czy dodanie
czegoś **innego rodzaju** — opłaty za utrzymanie pozycji, publikowanej przez giełdę — podnosi
trafność ponad próg opłacalności?

**Poprzeczka: `ci_low(p) > 52,69%`** (sprostowana w H3). Dziś mamy **50,27%**, więc potrzeba
**+2,39 punktu**. Uczciwie: **żadna pojedyncza informacja w historii tego projektu nie dała
takiego skoku.** Prior jest niski i jest to zapisane przed uruchomieniem.

| ID | zadanie | warianty | uwagi |
|---|---|---|---|
| **H2.1a** | Silnik: tryb BEZ bramki reżimu (`regime_feature_sets` z wartownikiem „wszystkie świece") + regresja baseline'u bit-identyczna | 0 (infrastruktura) | Bloker: `engine.py` filtruje `df[df["regime"] == regime_name]`. Zysk uboczny: foldy ~4× większe ⇒ mniej pominiętych (S1 pomijał 22 z 85) i early stopping z sensownym zbiorem walidacyjnym |
| **H2.1b** | Cecha `funding_*`: złączenie siatki 8h ze świecami 4h + **test leakage PRZED wejściem do modelu** (zasada 2) + wpis w `feature_registry.yaml` | 0 (przygotowanie cechy) | **Bramka STOP: czerwony test leakage = natychmiastowe zatrzymanie.** Próg ABSOLUTNY, nigdy percentylowy (masa punktowa 35,85% — H2.0). Okno statystyk rozszerzające się wstecz, bo autokorelacja 0,797 czyni zwykły `rolling` podatnym na przeciek |
| **H2.1c** | **Eksperyment**: 4h, bez bramki, 11 cech, V=3, 6,8 roku | **1 — WYCZERPUJE licznik H2 (0/1 → 1/1)** | Kryterium pre-rejestrowane, klauzula `n < 1 000`, reguła STOP po jednym wariancie |

**Poprawka do pre-rejestracji z H2.0, wprowadzona PRZED uruchomieniem czegokolwiek:**
H2.0 zapisało H2.1 jako jedną rundę zmieniającą naraz **dwie** rzeczy wobec S1b (usunięcie
bramki + nowa cecha). To łamie zasadę 4 i zaciera atrybucję: przy wyniku negatywnym nie
wiedzielibyśmy, która zmiana zawiodła. Dlatego **H2.1a mierzy baseline bez bramki na
niezmienionych 10 cechach** (0 wariantów — charakteryzacja punktu odniesienia, kryterium
sukcesu NIE jest z nim związane, bo próg 52,69% pochodzi z geometrii kosztu, a nie z obejrzanej
trafności), a H2.1c mierzy **wyłącznie delta od dodania cechy**. Kryterium sukcesu, klauzula
nierozstrzygalności i reguła STOP pozostają **niezmienione**.

**Ryzyko rundy:** klauzula `n < 1 000` może wejść w grę, jak w S1b. Szacowana próba bez bramki
to ~1 200 transakcji, ale lejek (8,03%) zmierzono przy bramce — bez niej może być inny w obie
strony.

---

### ETAP 2 — rozwidlenie po H2.1 (zależne od wyniku, opisane Z GÓRY)

| wynik H2.1c | co to znaczy | co robimy |
|---|---|---|
| **pozytywny** (`ci_low > 52,69%`) | pierwszy dodatni wynik w historii projektu | **NIE wdrażamy.** Replikacja out-of-sample na ETH (zasada 9: BTC do końca, potem generalizacja bez retuningu). Dopiero potem rozmowa o Fazie 1 |
| **negatywny** | zbiór informacyjny OHLCV + funding **wyczerpany** dla predykcji kierunku na BTC 4h | Reguła STOP zamyka H2. Przejście do Etapu 4 — decyzja użytkownika |
| **nierozstrzygalny** (`n < 1 000`) | konfiguracja niemierzalna przy dostępnej historii, jak S1b | **Nie interpretujemy w żadną stronę.** Jedyna droga dalej to więcej próby, czyli wymiar przekrojowy (Etap **4A**, nie 4B — sprostowane 2026-09-22), nie kolejne `V` ani interwał |

---

### ETAP 0 (WYKONANY 2026-09-22) — kalibracja przyrządu: K1

> **Zadanie, które powinno być pierwsze, a było siedemnaste.** Projekt wyprodukował 15 wyników
> negatywnych na przyrządzie, którego nikt nie skalibrował.

| wynik | treść |
|---|---|
| **Aparat działa** | przy wyroczni doskonałej mierzy **100,00%** trafności na 4 843 transakcjach |
| **Kryterium uczciwe** | `ci_low > break_even` — **0 fałszywych alarmów na 6 losowaniach szumu**; uwiarygodnia WSZYSTKIE werdykty projektu, w tym Z10 |
| **Próg wykrywalności ~58%** | wobec progu opłacalności ~52,7% — **luka 5,5 pp**, w której sygnał byłby opłacalny i niewidzialny |
| **`classify_checkpoint` zdegradowany** | wystawił **GO czystemu szumowi** — nie jest kryterium werdyktu |
| **Otwarte** | trafność na szumie 54,09% (z=+1,21, nieistotne, ale n=220 nie wyklucza obciążenia ~7 pp) |

**Skutek dla mapy — SPROSTOWANY po K2 (2026-09-22).** Pierwotnie zapisano tu, że każda
przyszła runda musi podać, czy zakładana trafność przekracza **~58%**. **To była zła liczba:**
58,20% to trafność w pierwszym punkcie siatki `q`, w którym zapaliło się kryterium — przy
siatce zawierającej q=0,30 ta sama konfiguracja podałaby inną wartość, bez jednej zmiany
w kodzie. Właściwością przyrządu jest `wald_half_width(n)`, czyli szerokość pasma „opłacalne,
ale niewidzialne", zależna **wyłącznie od `n`**.

**Obowiązujące brzmienie:** każda przyszła runda liczy PRZED uruchomieniem
`metrics.measurability_report(zakładana_trafność, break_even, oczekiwane_n)` i podaje wynik
w pre-rejestracji. Nie ma tu zamrożonego progu i **świadomie się go nie dokłada** — projekt ma
już dwa trupy po zamrożonych progach (`MIN_VALIDATION_ROWS = 30`, `std < 0.2`). → [runs/k1](runs/2026-09-22_k1-kontrola-pozytywna/README.md)

### ETAP 3 — dług techniczny wart zrobienia NIEZALEŻNIE od H2.1

Te zadania nie zależą od żadnej hipotezy i poprawiają wszystko, co policzymy później.

| ID | zadanie | warianty | dlaczego warto |
|---|---|---|---|
| **T1** ❌ **ZAMKNIĘTE JAKO NIEZASADNE (T1-diag, 2026-09-22)** | Realny funding w modelu kosztów zamiast stałej `FUNDING_RATE_8H = 0.0001` — **sprawdzone i niewarte zrobienia**. Przejście na realne stawki z dyskretnym harmonogramem przesuwa próg opłacalności o **+0,022 pp** (przy niepewności pomiaru 1,09 pp). Stała jest **dokładnie medianą** realnego rozkładu. **Uzasadnienie tego zadania było błędem kategorii:** „−0,00243%" z H3 to signowany koszt per transakcja policzony JUŻ tą stałą, dla próby z przewagą shortów — nie pomiar stawki. **Warunek ważności:** long/short po połowie; strategia jednostronna unieważniłaby wniosek → [runs/t1-diag](runs/2026-09-22_t1-diag-realny-funding/README.md) | 0 (diagnostyka) | Zamknięte bez zmiany w kodzie produkcyjnym |
| **T2** ✅ **ZAMKNIĘTE (2026-09-22)** | `ruff` + `black` — luka DoD zgłaszana od C2.11. Zainstalowane (ruff 0.16.8, black 26.5.1), konfiguracja w `pyproject.toml`. **`line-length = 100`, nie domyślne 88** — przy 88 poza limit wypada 872 linii, przy 100 tylko 62; domyślna wartość przeformatowałaby też ZAMROŻONE skrypty rund. Ruff: **11 znalezisk → 0** (3 nieużywane importy, 8 × `zip()` bez `strict=`). Black: **15 plików dotkniętych w rundach** (zasada: nie całe repo). Zamrożone skrypty wyłączone z obu narzędzi spójnie. **Pozostało:** ~14 plików historycznych niesformatowanych — świadomie, bo formatowanie całego repo to osobna decyzja | 0 | Komendy: `py -m ruff check .` i `py -m black <pliki rundy>` |
| **T3** ✅ **ZAMKNIĘTE (2026-09-22)** | Sprzątanie repo. Usunięte: katalog `Claude outputs/` (2 pliki — jeden **bajt w bajt identyczny** z `runs/2026-09-21_c2.6-.../README.md`, drugi to nieaktualny poprzednik `runs/INDEX.md`) oraz **16 stubów** `runs/*.md`, które same deklarowały się jako usuwalne. **`.claude/settings.json` ZOSTAJE** — to współdzielona konfiguracja projektu (włączone wtyczki, allowlist komend); usunięcie zabrałoby zespółowi działającą konfigurację. Wyczyszczone z niego wpisy jednorazowe (merge konkretnego brancha z C2.11). **`settings.local.json` dopisany do `.gitignore`** — do dziś chronił go wyłącznie globalny gitignore użytkownika, więc na innej maszynie wylądowałby w commitcie | 0 | Wszystko odzyskiwalne z historii gita |
| **T4** ✅ **ZAMKNIĘTE (2026-09-23)** | `MIN_VALIDATION_ROWS = 30` i `validation_fraction = 0.2` — sprawdzone zagnieżdżonym podziałem wewnątrz danych treningowych (86 okien, konfiguracja kanoniczna 4h/`balanced`). **Early stopping działa** (bije 200 drzew w 86/86 oknach), **próg 30 wierszy bezczynny** (0/86 — walidacja ma ~70 wierszy), przy `balanced` ES **obniża** abstynencję. Zero zmian w kodzie. Wynik uboczny: nawet idealna liczba drzew bije zgadywanie o 0,7% — potwierdzenie wniosku 39. **Otwarte na przyszłość:** kalibrować `validation_fraction` tylko na wyroczni K1/K2, nigdy na realnych danych bez sygnału → [runs/t4](runs/2026-09-23_t4-kalibracja-early-stopping/README.md) | 0 (diagnostyka) | Zamknięte bez zmiany w kodzie produkcyjnym |
| **T5** ✅ **ZAMKNIĘTE — A1 PRZYJĘTE (decyzja użytkownika 2026-09-22)** | **ABSTYNENCJA MODELU — problem numer jeden** (K1). **K2: wagi klas DZIAŁAJĄ (próg wykrywalności niżej o krok siatki, odczyt przyrządu staje się monotoniczny), wymuszenie kierunku NIE** (n ×260, ale margines przy q=0,30 ujemny). **WYKONANE:** `DEFAULT_CLASS_WEIGHT_MODE = balanced` w silniku, `none` zostaje jako nazwany wariant odtwarzający baseline sprzed K2 (test z literałami). ADR: `docs/rag/03`. Adopcja ujawniła realny błąd (`KeyError` przy foldzie bez wszystkich klas) — naprawiony, z regresją. **Otwarte:** A1 schodzi PONIŻEJ podłogi abstynencji (43,6% wobec 66,5%), więc otwiera pozycje także na świecach kończących się niczym — niezmierzone na realnej cesze → [runs/k2](runs/2026-09-22_k2-naprawa-abstynencji/README.md). To ona, nie brak sygnału, ograniczyła S1b (345), H2.1 (98) i samą kontrolę negatywną K1 (n≈37). Kandydaci: wagi klas w XGBoost, wymuszenie kierunku zamiast trzeciej klasy `timeout` | 0 (poprawność pomiaru) | **Obniżenie progu wykrywalności jest warte więcej niż kolejna hipoteza** — dziś każda hipoteza poniżej 58% trafności jest niemierzalna, cokolwiek testujemy |
| **T6** ✅ **ZAMKNIĘTE (K2)** | Kill-switch jako źródło obciążenia na szumie — **ROZSTRZYGNIĘTE: obciążenia NIE MA.** Różnica ON−OFF **+0,04 pp przy CI ±0,34 pp** na 167 160 transakcjach; 54,09% z K1 przypisane szumowi przy n=220 → [runs/k2](runs/2026-09-22_k2-naprawa-abstynencji/README.md) | 0 (diagnostyka) | K1 zmierzył 54,09% trafności na czystym szumie (nieistotne, ale niewykluczone). Kill-switch tłumi transakcje po serii strat, więc może podnosić trafność wśród tych, które przetrwały — walidacja S1 zmierzyła ten efekt jako +0,30 pp przy n=1 037 |

#### ✅ T7 — usterki z przeglądu kodu po H3 (2026-09-22, 0 wariantów)

Przegląd diffu H3 (`/code-review`) zgłosił 15 uwag. Naprawione **wszystkie dotyczące kodu**;
zero zmian w wynikach jakiejkolwiek rundy (sprawdzone), testy **312/312**.

- **`engine.py`** — rekord „pusty reżim" w `folds_summary` miał 12 kluczy zamiast 17.
  Konsument sumujący liczniki po całej liście wywalał się `KeyError` — i to dopiero po pełnym
  walk-forwardzie. Klucze dołożone u źródła, niezmiennik pilnuje nowy test.
- **`costs.py`** — docstring bramki podawał jako „zmierzone w H3" prognozę, którą H3 **obaliła**
  (funding: prognoza +0,015% nominału, pomiar **−0,00243%**, czyli przeciwny znak). Wpisany
  faktyczny pomiar. To ta sama liczba, która stoi za zadaniem **T1** wyżej.
- **Trzy moduły `diagnose_*`** odtwarzały regułę nóg ręcznie zamiast wołać `gate_cost_fraction`.
  H3 ogłosiła, że „klasa błędu usunięta" — nieprawda, dopóki te trzy kopie istniały. Teraz
  jedno źródło; wartość identyczna co do bitu (0,0009), więc zapisy rund pozostają odtwarzalne.
- **Testy** — kotwica historyczna C2d wróciła do literału `0.0014` (wyprowadzona z żywych stałych
  przesuwałaby się razem z tym, co ma przytwierdzać); usunięta asercja o kill-switchu, która nie
  była niezmiennikiem, tylko właściwością fikstury; dodana tabela kosztów nóg wpisana literałami
  — jedyne miejsce w repo znające te liczby bez pytania kodu (odpowiedź na zarzut, że walidacja
  „drugą drogą" w H3 nie była niezależna); jeden test okazał się **pusty** (pętla nie wykonywała
  się ani razu) i został naprawiony.

**Niezamknięte, świadomie:** formatowanie `black`/`ruff` — patrz **T2** (brak na maszynie).
Otwarta pozostaje jedna uwaga metodologiczna do H3: pasmo progu policzono `break_even_hit_rate`
przy 60% timeoutów, a `backtest/metrics.py` sam ostrzega, że przy dominacji timeoutów ta funkcja
jest miarą **diagnostyczną, nie progiem opłacalności** (próg z realnego rozkładu wypłat dla tej
konfiguracji to 54,60% z Z5b). Hipoteza H2 jest zamknięta regułą STOP, więc nic z tego nie wisi
— ale gdyby ta konfiguracja wróciła, liczby H3 trzeba przeliczyć.

#### ✅ T8 — skille: procedura rundy nie miała jak zadziałać (2026-09-22, 0 wariantów)

Trzy niezależne usterki, wszystkie mechaniczne:

1. **Zasada 16 wskazywała na skille, których w sesji nie ma.** `data:validate-data`
   i `data:statistical-analysis` pochodzą z wtyczki `data`, wyłączonej w konfiguracji maszyny
   (`~/.claude/settings.json`: `"data@synced": false`). Dwie z trzech bramek jakości nie miały
   jak zadziałać od chwili zapisania zasady. Zasada 16 i mapowanie skilli przepisane tak, żeby
   **źródłem procedury był plik w repo** (`docs/skills/bramki-jakosci.md`), a skill był
   udogodnieniem, nie warunkiem.
2. **Skill `clas5-runda` istniał w TRZECH kopiach o różnej treści:** `docs/skills/` (zasady 1–17,
   aktualna), `.claude/skills/` (1–16, **ta się ładowała**) i kopia w chmurze konta (1–15).
   Wykonywana była wersja o dwie zasady starsza, odsyłająca do plików skasowanych przy
   konsolidacji dokumentacji. Duplikat w `docs/` **usunięty**; została jedna kopia w
   `.claude/skills/` — tam, gdzie Claude Code faktycznie czyta.
   **Aktualizacja 2026-09-23 (decyzja użytkownika): źródłem skilli jest CHMURA konta.** Kopia
   w `.claude/skills/clas5-runda/` była bajt w bajt identyczna z chmurową (sprawdzone `diff`
   z `~/.claude/skills/synced/`), więc usunięta bez utraty treści. Zmiana skilla = nowa
   wersja wgrana do chmury (procedura w `CLAUDE.md`).
   **Zmiany treści skilli w chmurze (2026-09-23):**
   - Partia 1 — wgrana i zweryfikowana (synchronizacja 08:34, treść bajt w bajt = paczki):
     `clas5-quant` — usunięty zamrożony próg „~58 %” (sprzeczny z zasadą 18) w SKILL.md
     i `methodology.md`, odwołanie do kopii w repo, stan projektu uzupełniony o P2 i T4;
     `quant-strategy-catalog` — carry przekrojowy „NIETKNIĘTE, priorytet 1” → „NIEMIERZALNY
     w P2, żyje tylko wersja z hedgem spot”, odwołanie do repo.
   - Partia 2 — wgrana i zweryfikowana (synchronizacja 09:04, treść bajt w bajt = paczki,
     poprawki partii 1 zachowane): `clas5-runda` — „operacje git po stronie użytkownika”
     sprzeczne z „Podziałem ról” w `CLAUDE.md`; `quant-strategy-catalog` — historia danych 4h
     to 6,8 roku (od 2019-09), nie 3 lata (dwa miejsca).
   - Partia 4 — **wgrana i zweryfikowana** (po A1; synchronizacja 17:14, treść bajt w bajt = paczki,
     `diff -r` scratchpad ↔ `synced/` dla wszystkich trzech skilli); paczki:
     `Downloads/clas5-skille-2026-09-23-po-a1/{ta-toolkit,quant-strategy-catalog,clas5-quant}.skill`
     (walidacja frontmatteru `skill-creator` OK; test przecieku nowej funkcji OK). Powód: po A1
     skille twierdziły, że formacje świecowe są „nietknięte", a kryterium werdyktu ma jeden
     warunek. `ta-toolkit` — status formacji ZMIERZONE-odrzucone (A1: 46,35 % [44,38; 48,31],
     kierunek odwrotny; jako cecha 0), krok 7 workflow „nie odwracaj znaku po wyniku",
     `compute_cdl_score_6` w `ta_features.py` (kopia kanonicznej z repo), częstości formacji na
     realnych świecach; `quant-strategy-catalog` — rodzina A5 (klasyczna AT jako reguła) ze
     statusem, overlay wykonania/zarządzania (W1/N1) jako nie-źródło edge'u, czwarty błąd
     (odwrócenie znaku / podgrupa post hoc), `n` z częstości zdarzenia dla reguł; `clas5-quant` —
     „Stan projektu" o zasadę 20, serie W/N/A, kryterium dwóch warunków (`t_neff` + `ci_low > p*`),
     cap N_eff ≤ n (Poprawka 2), wzorce błędów 11–14 w `lessons-learned.md`, §3/§4/§6/§7
     `methodology.md`, wykonanie i wyjścia wielonogowe w `risk-and-sizing.md` §4. `clas5-runda`
     bez zmian (procedura aktualna). Od 17:14 obowiązują nowe wersje (źródło: chmura, `CLAUDE.md`).
3. **Konfiguracja maszyny nie została ruszona.** Wtyczki `data` świadomie nie włączam: to plik
   poza repo, wyłączony celowo razem z sześcioma innymi, a działający na wszystkie projekty
   użytkownika. Rozwiązanie z punktu 1 jest odporniejsze — działa też w sesji chmurowej.
   Gdybyś chciał ją mimo wszystko włączyć, to jedna linia w `~/.claude/settings.json`.
   **Aktualizacja 2026-09-23 (decyzja użytkownika):** `data` włączona **dla tego projektu**
   (`.claude/settings.json`: `"data@synced": true`), nie globalnie — `~/.claude/settings.json`
   nadal nietknięty. Bramki jakości zostają w `docs/skills/bramki-jakosci.md`; skille `data:*`
   są wsparciem (działają od następnej sesji po włączeniu) — od zasady 19 OBOWIĄZKOWYM (T9).

#### ✅ T9 — zasada 19: skille obowiązkowe + automatyczny rejestr ich użycia (2026-09-23, 0 wariantów)

Decyzja użytkownika po T4, w której Claude pominął dwa pasujące skille (`clas5-quant`,
`engineering:code-review`). **`CLAUDE.md` zasada 19:** tabela „moment pracy → skill” jest
obowiązkowa, README rundy ma sekcję „Użyte skille”, wtyczki `engineering` i `data` włączone
w ustawieniach PROJEKTU. **Rejestr:** hooki `PostToolUse` (narzędzie Skill) i
`UserPromptExpansion` (komendy `/skill` użytkownika) → `tools/skill_audit.py` →
`runs/skille/<gałąź>.jsonl` (plik na przebieg); `.gitattributes` `merge=union`. Wpis robi
program, nie Claude — sprawdzone na żywo (pierwszy wpis: `engineering:code-review` przy
przeglądzie tej zmiany). Testy (55) obejmują prywatność — treść wiadomości użytkownika nigdy
nie trafia do rejestru; test wykrył błąd, przez który wiadomość „/ Haslo123” zapisałaby
„Haslo123”. **Przegląd przed scaleniem (16c) wykrył dwa kolejne:** jeden wspólny plik
rejestru blokowałby `git merge` każdej rundy (→ plik na gałąź, test odtwarza scenariusz)
i pomijałby skille z ukośnikiem w nazwie. Wszystkie trzy naprawione przed scaleniem.
**Przegląd diffu (16c): Approve** — po dwóch przebiegach `engineering:code-review` (drugi
dołożył odmianę liczebników w raporcie i limit długości nazwy pliku); 484 → 491 testów zielonych.
`update-config` i `engineering:testing-strategy` wczytano PRZED uruchomieniem hooka, więc
rejestr tej gałęzi ich nie zawiera — pierwszy wpis to przegląd kodu. Paczki skilli
`clas5-runda` (kroki z zasady 19) i `clas5-quant` (odwołania do zasad bez numerów) wgrane
i zweryfikowane (synchronizacja 10:55, treść = paczki).

**Otwarte:** format zdarzenia `UserPromptExpansion` jest nieudokumentowany — pierwsza komenda
`/skill` wpisana przez użytkownika pokaże w rejestrze, czy nazwa jest rozpoznawana (w przeciwnym
razie wpis `nierozpoznana-komenda` z listą samych nazw pól).

**Dopisek 1 — monitor CSV (prośba użytkownika, 2026-09-23).** Hook dopisuje też każdy wpis do
jednego lokalnego `runs/skille/uzycie_skilli.csv` w głównym repo (Excel: średnik, UTF-8 z BOM;
komórki zaczynające się od `= + - @` poprzedzone apostrofem — ochrona przed wykonaniem
formuły; bufor, gdy plik jest otwarty w Excelu; `py tools/skill_audit.py csv` odbudowuje
z JSONL). Przegląd diffu (16c, `engineering:code-review`): **Approve** — dołożony zrozumiały
komunikat zamiast błędu Pythona, gdy odbudowa trafi na plik otwarty w Excelu; 504 testy zielone.

**Dopisek 2 — wtyczki z GitHuba (decyzja użytkownika 2026-09-23).** Użytkownik zainstalował
`document-skills` i `example-skills` z `anthropics/skills` (zakres projektu). Weryfikacja:
brak synchronizacji z chmurą, a 5 skilli (`docx`, `pdf`, `pptx`, `xlsx`, `skill-creator`)
w innych wersjach niż chmurowe. Obie wtyczki odinstalowane, ustawienia projektu bez zmian
(instalacja przestawiła tylko kolejność pól). Skille ogólne — włączać na claude.ai. Zasada
dopisana do `CLAUDE.md` (wytyczna o skillach w chmurze). Przegląd diffu (16c): **Approve** —
przegląd wyłapał nieaktualny punkt „Otwarte” (paczki opisane jako niewgrane) i sklejone
akapity tej sekcji; poprawione.

**Dopisek 3 — wtyczki w projekcie i w chmurze (decyzja użytkownika 2026-09-23, zastępuje
dopisek 2).** Zakres projektu: `security-guidance`, `claude-code-setup` (`claude-plugins-official`),
`document-skills`, `example-skills` (`anthropic-agent-skills`) + dotychczasowy `code-review`.
Oba źródła zadeklarowane w `extraKnownMarketplaces` — wtyczki docierają przez repo do każdego
środowiska (także wyjątek `code-review` z dopisku 2 jest tym rozwiązany). Test niezmiennika:
`tests/test_project_settings.py`. Przy duplikatach z chmurą pierwszeństwo ma wersja
`anthropic-skills:`. **Uwaga kosztowa:** `security-guidance` robi przegląd diffu modelem
(domyślnie Opus 4.7) po każdej turze ze zmianami i agentowy przegląd przy każdym
`git commit`/`push` — zużywa limit konta; warstwy wyłącza się zmiennymi
(`ENABLE_STOP_REVIEW=0`, `ENABLE_COMMIT_REVIEW=0`, `SECURITY_GUIDANCE_DISABLE=1`).

**Dopisek 4 — `security-guidance` tylko wzorce (decyzja użytkownika 2026-09-23).** W `env`
projektu: `ENABLE_CODE_SECURITY_REVIEW=0` (wyłącznik główny wszystkich przeglądów modelem,
sprawdzony w kodzie wtyczki 2.0.8) + `ENABLE_STOP_REVIEW=0` i `ENABLE_COMMIT_REVIEW=0` jako
podwójna blokada. Sprawdzone na skrypcie wtyczki: przegląd po turze pominięty (kod 3, 0,5 s,
bez wywołania modelu), przegląd commita pominięty (kod 32), wzorzec `yaml.load` nadal daje
ostrzeżenie. Wtyczka nie zdążyła działać w tej sesji przed zmianą (brak `~/.claude/security`),
więc limit nie został zużyty. Zostaje jednorazowa instalacja SDK przy pierwszym starcie sesji
(~30–60 s), niewyłączalna bez wyłączenia całej wtyczki.

#### ✅ T10 — przegląd optymalizacyjny skilli, wtyczek i łączników (2026-09-23, 0 wariantów)

Prośba użytkownika: „przejrzyj jeszcze raz wszystkie skille oraz wtyczki oraz katalogi wtyczek
pod względem projektu i zaproponuj usprawnienia”, potem „wykonaj wszystko”. **Stan przed:**
68 skilli w sesji (32 bez zastosowania w CLAS-5), 7 wtyczek, 18 łączników MCP z wtyczek
`engineering`/`data` (13 próbuje się łączyć przy każdym starcie: 5 nie łączy się, 8 czeka na
logowanie, 0 używanych), 5 łączników konta, ~4,4 tys. tokenów kosztu stałego na sesję.
Liczniki użycia Claude Code (13 uruchomień): `engineering:code-review` 6×, `clas5-runda` 4×,
`clas5-quant` 3×, `update-config` 3×; wtyczka `data` 0× (brak rund badawczych od zasady 19),
`document-skills` / `example-skills` / `code-review` z GitHuba 0×.
**Zrobione w repo:** (B) `document-skills`, `example-skills` i `code-review` z GitHuba wyłączone
w `.claude/settings.json` (duplikaty chmury / 11 z 12 bez zastosowania / tylko pull requesty;
źródła zostają, powrót = jedna komenda); (C) 4 osobiste skille konta ukryte przed modelem przez
`skillOverrides` — sprawdzone w kodzie Claude Code 2.1.280, że działa TYLKO na skille spoza
wtyczek, więc wcześniejsza propozycja ukrycia duplikatów z wtyczek była błędna i odpadła;
(D) `disableClaudeAiConnectors` — łączniki konta zniknęły z sesji natychmiast po zapisie;
(E) **zasada 13 pilnowana programem:** `runs/ZAMROZONE.txt` (23 skrypty) + hook
`tools/frozen_guard.py` (PreToolUse; odmowa sprawdzona na żywo na pliku próbnym) + 59 testów,
w tym spójność listy z komendami w README rund i z wykluczeniami `pyproject.toml`;
(H) audyt `CLAUDE.md` listą kontrolną `claude-md-management` (z kopii katalogu, bez
instalowania wtyczki): dołożona sekcja „Komendy”, tabela zasady 19 +5 wierszy, nakładki skilli
rozstrzygnięte, lista skilli chmury 2→5, rozróżnienie `anthropic-skills:` / `anthropic-agent-skills`;
(J) test, że każda włączona wtyczka jest opisana w `CLAUDE.md`.
**Zostawione świadomie:** `security-guidance` (koszt mały; 302 MB środowiska SDK zostaje, bo
instalator nie patrzy na wyłączniki), wtyczki `engineering`/`data` w całości (7 z 20 skilli
używanych; wrócić po 3–4 rundach z danymi z rejestru), `pyright-lsp` (później, wymaga
`pip install pyright`), `discernment-nudge` (bez decyzji użytkownika).
**Po stronie użytkownika** (klasyfikator trybu auto zablokował edycję plików Claude Code poza
repo jako „samomodyfikację”): (A) `/mcp disable` dla 18 łączników wtyczek — zapis
w `~/.claude.json`; (I) usunięcie martwych wpisów `finance@synced` i `small-business@synced`
z `~/.claude/settings.json`. Do potwierdzenia po restarcie sesji: skille ukryte przez
`skillOverrides` nie są na liście modelu.
**Przegląd diffu (16c, `engineering:code-review`): Approve** — jedna poprawka po przeglądzie
(komunikat odmowy z polskimi znakami; JSON ucieka je do ASCII, więc kodowanie konsoli nie ma
znaczenia); 507 → 570 testów zielonych.
**Użyte skille** (rejestr gałęzi `wtyczki-w-claude-md`):
`claude-code-setup:claude-automation-recommender` (analiza zastosowania wtyczek),
`engineering:testing-strategy` (plan testów hooka), `engineering:code-review` (bramka 16c);
`update-config` nie wczytany ponownie — jego treść była w kontekście z dwóch wcześniejszych
gałęzi tej samej sesji.

---

### ETAP 4 — hipotezy otwarte, WYMAGAJĄCE DECYZJI UŻYTKOWNIKA

Żadna nie startuje bez decyzji bramkowej. Każda dostaje **własny licznik od zera**, własną
pre-rejestrację i własną regułę STOP.

| ID | hipoteza | co mówią liczby | czego wymaga |
|---|---|---|---|
| **4A** | **Carry przekrojowy** — ten sam mechanizm funding na 20+ instrumentach naraz | **Jedyna ścieżka, o której wiemy, że jest WYKONALNA statystycznie.** H2.0: na jednym instrumencie brakuje rzędu wielkości próby (0,03–0,12×), bo ogranicza liczba nienakładających się okien 48h w 6,8 roku. Przekrój mnoży próbę przez liczbę instrumentów. Próg opłacalności spada **poniżej 50%** (48,13%) — nie trzeba przewagi kierunkowej | Silnik portfelowy, którego Faza 0 nie ma. Łamie zasadę 9. **To inny projekt, nie kolejna runda** |
| **4B** | **Target inny niż kierunek** — np. przewidywanie zmienności zamiast kierunku | Zero testów. Zmienność jest znacznie lepiej przewidywalna niż kierunek (fakt powszechnie znany), ale **nie wiadomo, czy da się na tym zarobić bez opcji** | Nowa definicja etykiety, nowa ekonomia wypłaty. Prawdopodobnie poza zakresem perpetuali |
| **4C** ❌ **ROZSTRZYGNIETE 2026-09-22 (M1) — WYNIK NEGATYWNY** | **Momentum bez bramki reżimu.** ~~NIEPRZETESTOWANE~~ — przetestowane. **SPROSTOWANIE poprzedniego brzmienia:** stało tu, że to „dokładnie to, co Faza 0 obaliła na 7 687 transakcjach” — **było to za mocne i sprzeczne z wnioskiem skumulowanym 12**, bo tamte 7 687 transakcji to w **96% cechy mean-reversion**; momentum miało tam 299 transakcji i CI szerokie na 11 pp. M1 zmierzyło je na **8 512** transakcjach: trafność **49,74%**, CI [48,68%; 50,80%], próg **52,94%** — górny kraniec **2,14 pp poniżej progu** przy próbie 1,90× wymaganej. **Momentum NIE jest gorsze od mean-reversion** (różnica −0,63 pp, z = −0,80, nieistotna) — jest tak samo nieobecne → [runs/m1](runs/2026-09-22_m1-momentum-bez-bramki/README.md) | 1 (licznik M wyczerpany) |
| **4D** | **ETH / SOL / BNB** | Zero testów (zasada 9 nigdy nie została spełniona). **Ale:** to test GENERALIZACJI tej samej hipotezy, więc ma sens dopiero, gdy jest co generalizować | Czeka na pozytywny wynik czegokolwiek |
| **4E** | **Ekonomia dźwigni i sizingu** | Kill-switch testowany mechanicznie (C2c), nigdy jako dźwignia rentowności. **Uwaga: sizing nie tworzy edge'u** — mnoży istniejący. Przy `p` nieodróżnialnym od monety mnoży zero | Niski priorytet z tego powodu |

---

#### Hipoteza M — momentum bez bramki reżimu ⚪ ZAMKNIĘTA 2026-09-22, wynik NEGATYWNY

Pierwsza hipoteza postawiona **po** zamknięciu Fazy 0 i H2. Własny licznik od zera:
**1/1 wyczerpany**, reguła STOP aktywna. Powstała z wniosku skumulowanego 12 (momentum jako
pozycja, której Faza 0 **nie wykazała** — niewykonalność pomiaru, nie brak edge'u) i stała się
wykonalna dopiero po zdjęciu bramki (H2.1a) i adopcji wag klas (K2 → K3), które podniosły
próbę z 299 do 8 512.

**Wynik:** momentum trafia w **49,74%** przy progu **52,94%**; górny kraniec CI leży 2,14 pp
poniżej progu, próba 1,90× wymaganej do orzeczenia negatywu. **Dowód braku, nie brak dowodu.**
Ramię odniesienia odtworzyło historyczny pomiar projektu co do 0,01 pp.
→ [runs/m1](runs/2026-09-22_m1-momentum-bez-bramki/README.md)

#### Hipoteza F — funding jako cecha, ZMIERZONY ⚪ ZAMKNIĘTA 2026-09-22, wynik NEGATYWNY

Druga hipoteza postawiona po zamknięciu Fazy 0. Własny licznik: **1/1 wyczerpany**, reguła STOP.
H2 **nie zostało wznowione** — pytanie wróciło jako nowa hipoteza, tą samą drogą co momentum (M).
Uzasadnienie: H2.1 dało werdykt NIEROZSTRZYGNIĘTY wyłącznie z powodu `n = 98`, a przeszkoda była
instrumentalna (abstynencja 99,32%), nie informacyjna — i została zmierzona oraz usunięta (K3).

**Wynik:** funding **50,34%** przy progu **52,94%**, `n = 8 127` (1,81× wymaganej próby); górny
kraniec CI 1,51 pp poniżej progu. Różnica wobec ramienia bez funding: **−0,03 pp** (z = −0,04).
**Runda obaliła też jedyne ustalenie H2.1** — „funding potraja liczbę decyzji" nie odtwarza się
(2,80× → 1,01×), było artefaktem zagłodzonej próby.
→ [runs/f1](runs/2026-09-22_f1-funding-zmierzony/README.md)

#### P2 — sonda wykonalności carry przekrojowego (4A) ⚪ ZAMKNIĘTA 2026-09-22, NIEMIERZALNA

0 wariantów, poza licznikami. Na 20 największych monetach (poprawka 1 — decyzja użytkownika)
funding pokrywa koszt (F − C = 0,097% na 48h, CI [0,051%; 0,143%]), ale rozrzut wyniku okna
σ = 5,56% wymaga ~25 850 okien wobec 1 161 dostępnych (0,045×). **Rachunek 4A w tabeli niżej
(„20 instrumentów = 160 660”) jest OBALONY:** 18 monet ≈ k_eff = 2,0 niezależnych. Hipoteza C
nie startuje (zasada 18). Otwarte: cash-and-carry ze spotem — inny produkt, decyzja bramkowa.
→ [runs/p2](runs/2026-09-22_p2-sonda-carry-przekrojowy/README.md)

#### Seria W — wykonanie po konkretnej cenie ⚪ ZAMKNIĘTA 2026-09-23 (W1), 3/3, reguła STOP

Decyzja użytkownika 2026-09-23 (obowiązuje też na żywo): pozycji nie otwiera się ani nie zamyka
po cenie otwarcia/zamknięcia świecy, tylko po konkretnej cenie. Backtest liczył wejście po `close`
z założeniem 100 % wypełnienia (ograniczenie zapisane w C2.12, nigdy niezmierzone). W1 dodało
symulację wypełnień na ścieżce cen (`backtest/execution.py`, tryb `fill_model="path"`; ADR
w `docs/rag/04`) i zmierzyło trzy reguły wejścia kazane sprawdzić przez użytkownika.

**Wynik:** limit po close wypełnia się w **99,4 %** — trafność 50,11 % vs próg 52,96 %, NEGATYWNY
(założenie C2.12 było prawie prawdziwe). Limit na cofnięciu 0,5·ATR: trafność **53,15 %** —
pierwszy raz punktowo nad progiem (52,81 %) — **ale średni zwrot netto istotnie ujemny**
(t = −3,90): małe wygrane na timeoutach, pełne straty na stopach; werdykt NIEROZSTRZYGNIĘTY wg
kryterium trafności, ekonomicznie strata. Stop na wybiciu: 46,13 % vs 54,83 %, NEGATYWNY.
**Lekcja (wniosek skumulowany 43): kryterium `ci_low > break_even` jest niekompletne przy
wypłatach asymetrycznych — każda przyszła pre-rejestracja dopisuje `t_stat > 0`.**
→ [runs/w1](runs/2026-09-23_w1-wykonanie-po-cenie/README.md)

#### Seria N — nowy cel modelu (częściowe wyjście) ⚪ ZAMKNIĘTA 2026-09-23 (N1), 1/1, reguła STOP, NEGATYWNY

Decyzje użytkownika 2026-09-23: 50 % pozycji zamykane przy +5 % depozytu przy dźwigni 3× (= +1,67 %
ceny), stop na cenę wejścia, reszta do 1,5·ATR, limit czasu 12 h; sizing bez zmian; **dane od
2021-01-01 (zasada 20 — NOWA BAZA, nowe liczniki)**. Zrealizowane jako nakładka zarządzania na
ścieżce (`ManagedExitRule`, koszt per noga), etykieta bez zmian — jedna zmienna, ten sam model
i te same wejścia co kontrola. Poprawka 1 do pre-rejestracji (reguła 6) wykryta testami
przykładowymi PRZED uruchomieniem (commit `4683669`).

**Wynik:** zwrot netto **−0,094 %** [−0,131; −0,058] na transakcję (t_neff −4,08), kontrola −0,107 %;
**różnica parowana +0,007 % [−0,009; +0,024]** na 6 736 wspólnych transakcjach — zero. Trafność
49,6 → 53,3 % („na styk" starego progu 53,32 %) przy progu uogólnionym **p\* = 57,24 %** — iluzja
W1b. **Zarządzanie pozycją nie tworzy informacji** (wniosek skumulowany 45). Kontrola na nowej
bazie: p 49,58 %, −0,107 % (wniosek 46) — baza 2021+ jest trudniejsza niż 6,8 roku.
→ [runs/n1](runs/2026-09-23_n1-nowy-cel-czesciowe-tp/README.md)

#### Seria A — analiza techniczna: formacje świecowe ⚪ ZAMKNIĘTA 2026-09-23 (A1), 2/2, reguła STOP, OBA NEGATYWNE

Decyzja użytkownika 2026-09-23: „szukamy pozycji na podstawie analizy technicznej i formacji
świecowych" (skill `ta-toolkit`). Wskaźnik `cdl_score_6` = suma znaków 6 formacji z podręcznika
(TA-Lib, 0 stopni swobody, doji wyłączone; nowa cecha w `feature_miner.py` z testem przecieku
przed modelem). Dwa ramiona na populacji kontroli N1 (2021+, 69 okien): **A1a** reguła bez modelu
(bycza → long, niedźwiedzia → short, limit po close, ±1,5·ATR, 12 h), **A1b** ta sama informacja
jako 5. cecha modelu. Pomocniki `build_rule_signals` / `summarize_trade_returns` w `checkpoint_lib`.

**Wynik:** A1a trafność **46,35 %** [44,38; 48,31] — cały przedział PONIŻEJ 50 %; zwrot netto
**−0,177 %** [−0,245; −0,109] na transakcję (n 2 477). Objęcie (84 % sygnałów) czytane po
podręcznikowemu jest na 4h BTC częściej końcem ruchu niż początkiem (wniosek 48). A1b: różnica
parowana wobec kontroli **−0,001 % [−0,012; +0,010]** — zero. Odwrócenie reguły = nowa hipoteza
post hoc o ekonomii ≈ +0,01 % (wniosek 49) — nie uruchamiać bez osobnej decyzji. Poprawka 2
(raportowa): N_eff ≤ n w statystykach per transakcja (wniosek 50).
→ [runs/a1](runs/2026-09-23_a1-formacje-swiecowe/README.md)

**A2 (2026-09-23, decyzja użytkownika „wykonaj" pozostałe rodziny AT) — ZAMKNIĘTA, seria A 7/7,
WSZYSTKIE RODZINY AT ZE SKILLA ZAMKNIĘTE.** 10 cech deterministycznych ze skilla w `agents/ta_rules.py`
(parametry domyślne, test przecieku), rachunek mocy z częstości sygnału: 3 reguły stanowe osobno,
5 zdarzeniowych jako grupa (osobno niemierzalne: 86–988 sygnałów), model + 10 cech. **Wynik:**
struktura trendu **48,20 %** [46,98; 49,42], −0,127 % [−0,170; −0,084] NEGATYWNY; wsparcie/opór
49,87 %, −0,080 % NEGATYWNY; model + AT −0,099 %, parowane +0,005 % [−0,055; +0,066] NEGATYWNY;
Fibonacci 51,5 % [49,4; 53,6], −0,041 % NIEROZSTRZYGNIĘTY (rozdzielczość); grupa zdarzeń 48,3 %,
−0,103 % [−0,182; −0,024] NIEROZSTRZYGNIĘTY wg litery (guard n 2 133 < 2 366). Reguły „z ruchem"
konsekwentnie pod monetą (wniosek 51); reguły stanowe pogłębiają obsunięcia (52); rzadkie
zdarzenia → test rodziny (53). Analiza techniczna na BTC 4h zamknięta jako kierunek.
→ [runs/a2](runs/2026-09-23_a2-rodziny-at/README.md)

#### Seria C — cash-and-carry z hedgem spot ⚪ ZAMKNIĘTA 2026-09-23 (C1), 2/2, reguła STOP, C1a POZYTYWNY / C1b NEGATYWNY

Punkt 2 zlecenia użytkownika („wykonaj": kierunki spoza ceny i wolumenu); kierunek otwarty po
P2. Nowe źródło: świece 8h spot Binance (ccxt, publiczne API; profil `data:explore-data`: 0 dziur,
znaczniki = perp = funding). P&L per okres 8h = funding otrzymany + (r_spot − r_perp) − koszty
przełączeń (0,19 %); czyste funkcje `backtest/carry_hedged.py` z testami; target = **przepływ,
nie kierunek** (próg 0, N_eff z autokorelacji, z_2 = 2,241).

**Wynik:** C1a (zawsze w pozycji) **+5,4 %/rok na kapitale [3,5; 7,4]** (+10,9 % nominału),
t_neff 5,40 przy N_eff 286 — **pierwszy pozytywny odczyt w projekcie, ale to kontraktowy przepływ
za dźwignię, nie prognoza**; hedge ≈ 0 (−0,13 %), obsunięcie 0,64 %; **połowa wyniku z 2021**,
2022–2026: 0,4–6 %/rok kapitału, ostatnie 3 lata 3,6 % brutto (wniosek 54). C1b (po znaku
fundingu) NEGATYWNY: 875 przełączeń = 166 % kosztów (wniosek 55). Rachunek mocy niedoszacował
szumu 5,6× (autokorelacja fundingu — wniosek 56). Nie wyceniono: likwidacja shorta
(+90 %/30 dni), ryzyko giełdy, koszt kapitału.
→ [runs/c1](runs/2026-09-23_c1-cash-and-carry/README.md)

**Decyzja użytkownika (bramkowa):** czy budować produkt cash-and-carry (zarządzanie depozytem
z zysków spot, limit na giełdę, porównanie z lokatą USD ~4–5 % w 2023–2025). Jeśli tak — następny
krok to inżynieria (symulacja depozytu, stress +90 %/30 dni), nie pomiar.

#### Seria R — premia rebalansowa koszyka ⚪ ZAMKNIĘTA 2026-09-23 (R1), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY (punktowo ujemny)

„Inny cel niż kierunek" (punkt 2 zlecenia użytkownika) — rodzina B2: koszyk top-20 po
30-dniowym obrocie (uniwersum P2 z wycofanymi, skład point-in-time miesięcznie, od 2021-02),
rebalans dzienny (A) vs trzymanie w miesiącu (B); premia = r_A − r_B − 0,10 % × obrót; czyste
funkcje `backtest/rebalance_premium.py` z testami. **Wynik:** netto **−3,55 %/rok [−9,50; +2,40]**,
wartość A względem B −12,1 % przez 5,4 roku, 36/65 miesięcy dodatnich; scenariusz „ruchy
niezależne" (6–11 %/rok brutto) wykluczony — w krypto ruchy względne wewnątrz miesiąca trwają
(wniosek 57). Rozdzielczość 8,5 %/rok, 3× gorsza niż proxy ex ante (wniosek 58). Proces: kod
scommitowany z padającym testem (potok zamaskował kod wyjścia) — naprawa przed przebiegiem
końcowym; odtąd `set -o pipefail`.
→ [runs/r1](runs/2026-09-23_r1-premia-rebalansowa/README.md)

**Punkt 2 zlecenia użytkownika 2026-09-23 ZAMKNIĘTY:** carry z hedgem (C1: POZYTYWNY jako
przepływ — decyzja o produkcie po stronie użytkownika), inny cel (R1: nic), pozycjonowanie
(kolektor AKTYWNY — niżej). ~~Otwarte pozostają wyłącznie kierunki wymagające nowych danych
(pozycjonowanie za ~3 lata, on-chain — brama danych)~~ → **P3 (niżej) podłączyło te dane
od razu**; otwarta pozostaje decyzja o produkcie cash-and-carry.

#### Seria TS — uzupełnienie poza próbą (TR1/TP1) ⚪ ZAMKNIĘTA 2026-09-24, 2/2

Decyzja użytkownika („sprawdź na innych przedziałach”). TR1: monety 21–50, +14,1 %/rok
[−3,0; +31,2], t 1,62, korelacja z TS1 0,86. TP1: 2026-07-08 → 09-23, +0,69 %. Wniosek 74. Nowy
cache `data/raw/universe_2026q3`. Pełne wyniki: `runs/2026-09-24_ts-poza-proba/`.

#### Seria TF — trend z filtrem tłoku ⚪ ZAMKNIĘTA 2026-09-24 (TF1), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY

Druga z trzech nowych hipotez sesji. Filtr: long zerowany przy Σ funding 7 dni > 0,63 %, short
przy < −0,63 % (9,3 % pozycji). TF1 − TS1 −1,41 %/rok [−6,58; +3,77]. Wniosek 73. Pełne
wyniki: `runs/2026-09-24_tf1-trend-filtr-tloku/`.

#### Seria CP — premia Coinbase ⚪ ZAMKNIĘTA 2026-09-24 (CP1), 1/1, reguła STOP, POZYTYWNY (pre-rejestracja), nieistotny rodzinnie

Pierwsza z trzech nowych hipotez sesji 2026-09-24 (decyzja użytkownika „sprawdź 3 nowe hipotezy”).
Sygnał: znak(średnia premii Coinbase/Binance spot z 7 dni − z 90 dni), pozycja BTC silnikiem TS1
(haki `signs_override`/`keep_fn` dodane do `ts_momentum`, TS1 odtworzone). Wynik +32,0 %/rok
[+2,0; +62,1], t_neff 2,09, > q97,5 H0; test opóźnienia bez przecieku; alfa ponad trend t 1,67;
próg rodzinny niespełniony. Wniosek 72. Ścieżka odwrotu: revert commitu scalającego.
Pełne wyniki: `runs/2026-09-24_cp1-premia-coinbase/`.

#### Seria NL — short na nowych listingach ⚪ ZAMKNIĘTA 2026-09-24 (NL1), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY

Drugi kandydat panelu „co dalej” (decyzja użytkownika „testuj dalej różne kombinacje”). Nowe
źródło danych: `data/fetch_listings.py` (archiwum data.binance.vision — pierwszy dzienny plik =
data listingu, point-in-time, wycofane włącznie; miesięczne świece 1d i funding). 569 zdarzeń
2021–2026. Pre-rejestracja `47e196d`. Wynik: +2,12 % na zdarzenie [−2,68; +6,93], t 0,87;
mediana +13,5 %; 11,8 % likwidacji przy 1×, 41,5 % przy 3×. Wniosek 71. Ścieżka odwrotu: revert
commitu scalającego (nowe moduły, bez zmian w istniejących). Pełne wyniki:
`runs/2026-09-24_nl1-nowe-listingi/`.

#### Seria TS — momentum w czasie na koszyku top-20 ⚪ ZAMKNIĘTA 2026-09-24 (TS1), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY (najsilniejszy ślad)

Decyzja użytkownika 2026-09-23 („testuj dalej różne kombinacje”); kandydat wybrany z panelu pięciu
propozycji (trend tygodniowy, listingi, kalendarz, przepływ zleceń, relatywne/test na żywo — trzy
ostatnie NIEMIERZALNE lub słabe). Reguła: znak zwrotu 28 dni per moneta, w = s·min(3, 0,40/σ̂)/N,
7 faz tygodniowych, realny funding. Pre-rejestracja `d066412`. Wynik: +14,8 %/rok netto
[−1,7; +31,3], t_neff 1,76 (kryterium 1,96 niespełnione), ponad 100 % H0, 6/6 lat i 7/7 faz
dodatnich, bez bety rynku. Przełożenie: 3× kapitału → CAGR +4,9 %, obsunięcie 90 % (drag).
Wniosek 70. Ścieżka odwrotu: revert commitu scalającego (nowy moduł, bez zmian w istniejących).
Otwarte dla użytkownika: test prospektywny (paper trading) TS1 i X1 od 2026-07-01.
Pełne wyniki: `runs/2026-09-24_ts1-trend-koszyk/`.

#### Serie Y1 / Y2 — model kontrolny na 1h i 1d ⚪ ZAMKNIĘTE 2026-09-23, każda 1/1, reguła STOP, Y1 NEGATYWNY / Y2 NIEROZSTRZYGNIĘTY

Decyzja użytkownika 2026-09-23 („dla 2 sprawdź horyzont 1h oraz 1d"): DOKŁADNIE JEDNA zmienna —
interwał; natywne świece 1h/1d od 2021-01-01 (cache pobrany 2026-09-23, `timeframe_start_overrides`
w `config/settings.yaml`), okna walk-forward 60/28/28 (1h) i 365/91/91 (1d) jako parametr bazy
zapisany przed danymi; rachunek mierzalności z własności danych PRZED treningiem (obie MIERZALNE);
obie pre-rejestrowane w jednym commicie `e04ec02`. **Y1 (1h): NEGATYWNY z ogromnym zapasem** —
p 48,34 % [47,70; 48,98] (CI w całości poniżej 50 %) vs p* 54,01 %, r̄ −0,078 % na transakcję,
t_neff −11,74, n 23 334 (41× wymaganego), 6/6 lat ujemnych, 63 % timeoutów z p 45,6 %.
**Y2 (1d): NIEROZSTRZYGNIĘTY** — p 50,20 % [47,07; 53,34] vs 51,70 %, r̄ −0,094 % [−0,344;
+0,156], n 978, half-width 3,1 pp — dokładnie jak zapowiedziano; sumy roczne ±100 % nominału to
rozrzut bariery 6 %. Wniosek 69: zmiana horyzontu nie jest drogą. Ścieżka odwrotu: revert
commitu scalającego + usunięcie dwóch wpisów `timeframe_start_overrides` (cache 1h/1d mogą
zostać). Pełne wyniki: `runs/2026-09-23_y1-horyzont-1h/`, `runs/2026-09-23_y2-horyzont-1d/`.

#### Seria X2 — momentum przekrojowe na top-50 ⚪ ZAMKNIĘTA 2026-09-23 (X2), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY (słabszy niż X1)

Decyzja użytkownika 2026-09-23 („wykonaj oba"): większa próba przez szerokość — top-50 point-in-time,
nogi po 10, od 2021-05-01 (wcześniej < 50 kandydatów), reszta reguły jak X1; moc z symulacji
100 losowych rankingów PRZED wynikiem (17,5 %/rok; ×1,3 = 22,8 %). **Wynik:** +0,044 %/dzień
[−0,034; +0,121], t 1,10, +15,9 %/rok, Σ +82 % w 5,2 roku; **IC −0,006 [−0,033; +0,022]**;
33 skrajne dni = 52 % sumy; 2022 −20 %; noga short robi wynik; korelacja z BTC −0,11.
**Walidacja krzyżowa:** reguła X1 (top-20/5) tym samym kodem na siatce formowań X2 daje
+0,024 %/dzień (Σ +46 %) zamiast +0,060 (Σ +119 %) — **X1 zależało od fazy tygodniowego
kalendarza rebalansów** (wniosek 68). Rodzina B1 po dwóch odczytach: hipoteza ze SŁABYM
poparciem, bez dowodu; kolejne warianty zakazane; jedyna droga = pomiar prospektywny (7 faz
naraz, ≥ 2 lata) — decyzja użytkownika.
→ [runs/x2](runs/2026-09-23_x2-momentum-top50/README.md)

#### Serie L / V / G — cechy dzienne spoza wykresu jako 5. cecha modelu 4h 🔴 ZAMKNIĘTE 2026-09-23 (L1, V1, G1), każda 1/1, reguła STOP, trzy razy NEGATYWNY

Decyzja użytkownika 2026-09-23: „wykonaj po kolei 3 warianty celem zebrania informacji na
przyszłość". Trzy serie pre-rejestrowane W JEDNYM COMMICIE (`3278442`) przed jakimkolwiek
przebiegiem, ten sam przyrząd co O1; wspólny moduł `agents/external_features.py` (dopięcie
wartości dziennej z jawnym opóźnieniem publikacji: CoinMetrics +2 dni, DVOL +1 dzień, F&G +4h;
staleness > 7 dni = NaN), rejestr `external:`, testy przecieku. **Wyniki:** L1 (`ex_supply_change_7d`)
−0,097 % [−0,140; −0,054], p 49,79 %, parowo +0,003 pp [−0,047; +0,052]; V1 (`vrp_30d`) −0,076 %
[−0,120; −0,031], p 50,49 %, parowo +0,018 pp [−0,037; +0,074]; G1 (`fng_level`) −0,102 %
[−0,144; −0,059], p 49,90 %, parowo +0,002 pp [−0,045; +0,049], korelacja z RSI 0,29. Wspólny
wzorzec: cechy o skali dni podnoszą abstynencję (+4–7 pp), nie trafność. **Wniosek 67:** pięć
źródeł spoza wykresu (F1, O1, L1, V1, G1) — żadne nie zbliża się do progu; kierunek „dokładaj
cechę do modelu 4h" wyczerpany; obiecujący sygnał (X1) mieszka w innej formule.
→ [runs/l1](runs/2026-09-23_l1-onchain-podaz/README.md) · [runs/v1](runs/2026-09-23_v1-premia-zmiennosci/README.md) · [runs/g1](runs/2026-09-23_g1-strach-chciwosc/README.md)

#### Seria O — pozycjonowanie jako cecha modelu 4h 🔴 ZAMKNIĘTA 2026-09-23 (O1), 1/1, reguła STOP, NEGATYWNY

Pierwsze użycie archiwum z P3. Jedna cecha po mechanizmie (dźwignia → kaskady likwidacji):
`oi_change_24h` = log(OI_t/OI_t−6), OI z ostatniego odczytu 5-min WEWNĄTRZ świecy (bez lookaheadu
— test jednostkowy, shift-forward, walidacja na realnych danych), rejestr `positioning:`,
`agents/positioning_features.py`. Kontrola vs O1 parowo (ten sam seed, te same świece).
**Wynik: NEGATYWNY** — −0,074 % [−0,116; −0,032] na transakcję, t_neff −2,90, p 50,25 %
[49,06; 51,44] vs p* 53,07 %. **Ale:** wobec kontroli +0,024 pp [−0,019; +0,067], inny kierunek
w 20,6 % transakcji, trafność +0,67 pp, korelacja z wolumenem 0,045 — pierwsza cecha spoza OHLCV,
która w ogóle porusza model (wniosek 66). Pozostałe 5 kolumn archiwum (top-trader L/S, global
L/S, taker ratio, OI USD) = warianty tej samej rodziny → decyzja użytkownika, jedna na rundę.
→ [runs/o1](runs/2026-09-23_o1-pozycjonowanie/README.md)

#### Seria X — momentum przekrojowe (B1) ⚪ ZAMKNIĘTA 2026-09-23 (X1), 1/1, reguła STOP, NIEROZSTRZYGNIĘTY (punktowo wyraźnie dodatni)

Hipoteza odwrotna do R1 (wniosek 57). Uniwersum point-in-time top-20 (jak R1), sygnał = zwrot
28 dni, long top-5 / short bottom-5, trzymanie 7 dni, koszty 0,07 % × obrót obu nóg, funding per
symbol z cache P2; rachunek mocy PRZED wynikiem ze 100 losowych rankingów (half-width 21 %/rok)
→ MIERZALNA dla obietnicy literatury (52 %/rok). **Wynik: +0,060 %/dzień [−0,015; +0,135],
+22,0 %/rok netto [−5,3; +49,3], t 1,58; Σ +119 % w 5,4 roku, dodatni w 6/6 lat (2025 = 52 %
sumy), korelacja z BTC −0,13, IC +0,028 [−0,007; +0,064]; obrót 0,87/formowanie, koszty
3 %/rok, funding +1 %/rok; efekt z nogi short (przegrani tracą dalej).** Pierwszy zakład
o kierunek (relatywny) z dodatnim punktowo odczytem — hipoteza z poparciem, nie dowód
(rozdzielczość 27 %/rok, potrzeba ~4× próby). Wnioski 64–65. **Decyzja użytkownika:** (a) STOP
i archiwum, (b) nowa pre-rejestracja na szerszym uniwersum (top-50, nogi po 10), (c) pomiar
prospektywny (paper) od dziś — bez zużycia licznika. Realny kapitał: p(efekt ≤ 0) ≈ 6 %, koszty
shorta na przegranych wyższe niż w modelu.
→ [runs/x1](runs/2026-09-23_x1-momentum-przekrojowe/README.md)

#### D1 — produkt cash-and-carry: depozyt, COIN-M, basis, T-bill ⚪ ZAMKNIĘTA 2026-09-23 (0 wariantów reguł)

Cztery pytania otwarte po C1a, pre-rejestrowane z siatkami i kosztami (`93b3c6e`), na cache
C1 + danych P3; `backtest/carry_product.py` (czyste funkcje, 12 testów) + skrypt zamrożony.
**Wynik:** (Q1) run-up 30 dni max +89,6 %; depozyt 1× z miesięcznym uzupełnianiem → 0 likwidacji
w 5,5 roku (zapas 29 pp), +5,29 % na kapitale 2×; tańsze depozyty mają zapas kilku pp po `high`
i koszt uzupełnień do 1,43 %/rok (Poprawka 1 — koszt przycinania nóg, pominięty w
pre-rejestracji); (Q2) **COIN-M: wartość USD stała (tożsamość), brak likwidacji, kapitał 1× →
+9,07 %/rok [5,88; 12,26]** mimo stawki niższej o 1,8 pp; (Q3) basis 24 kontraktów kwartalnych
≈ funding zrealizowany (mediana frontu 5,9 %/rok; różnice median +1,8 / −0,9 pp; rozstęp ±17);
(Q4) ponad T-bill od 2022: COIN-M +1,8 pp/rok (−1,5…+7,2), USDT-M 2× −1,0 pp. N_eff z lag-1
zawyżony 8× (wniosek 63). Wnioski 61–63. **Decyzja o produkcie (realny kapitał, ryzyko giełdy)
należy do użytkownika.** Opcja tania: kontrakty COIN-M datowane (archiwum od 2020-09) —
stopa zamknięta bez likwidacji; nie mierzone.
**Decyzja użytkownika 2026-09-23: „carry odpuszczamy — nie o takie zwroty mi chodzi."**
Kierunek zamknięty bez produktu; kontrakty COIN-M datowane nie będą mierzone.
→ [runs/d1](runs/2026-09-23_d1-produkt-carry/README.md)

#### P3 — sonda źródeł danych II + podłączenie ⚪ ZAMKNIĘTA 2026-09-23 (0 wariantów)

Decyzja użytkownika 2026-09-23: „sprawdź wszystkie warianty, myślę też o podpięciu dodatkowych
danych". Brama danych G1–G4 zapisana PRZED pobraniem; kolektor `data/fetch_external.py` (8 źródeł,
bez kluczy, idempotentny, 4,5 min) + profil `data/profile_external.py`; przegląd bezpieczeństwa
nowego kodu sieciowego (1 znalezisko Medium — adres kolejnej strony z odpowiedzi serwera —
poprawione przed scaleniem, `http_get` tylko `https`). **Wynik: archiwum plików Binance ma
pozycjonowanie (OI, proporcje L/S, taker ratio) co 5 min od 2020-09-01 — 2 213 dni bez luki,
pokrycie bazy 99,9 %, wartości zgodne z kolektorem REST; P1 sprawdziło tylko REST API**
(wniosek 59, wniosek 39 zaktualizowany). Przechodzą też: funding COIN-M (od 2020-08), 24 kontrakty
kwartalne 8h, DVOL BTC/ETH (od 2021-03-24, 95,9 %), CoinMetrics 14 metryk on-chain (0 braków),
Fear & Greed, Coinbase; FRED jako tło. Odpadły: likwidacje, OKX, księga zleceń. Zastrzeżenia:
top-trader L/S z dziurą 2021-12→2022-12 (16 % bazy), 473 zerowe odczyty OI, 330 pustych świec
kontraktów po wygaśnięciu, masa punktowa fundingu COIN-M 42,7 % (wniosek 60). Cache
`data/raw/external/` (34 MB, poza gitem). Zero pomiaru sygnału.
→ [runs/p3](runs/2026-09-23_p3-sonda-zrodel-ii/README.md)

#### Zbieranie danych pozycjonowania (opcja C po P1) — URUCHOMIONE 2026-09-22 (po P3: zbędne dla historii)

`data/collect_positioning.py`: OI + 4 proporcje long/short, 1h, BTC/ETH/SOL/BNB, dopisywane do
`data/raw/positioning/`. Pierwszy przebieg 2026-09-22 (od 2026-09-01). **AKTYWNE (sprawdzone
2026-09-23 17:40):** zadanie Harmonogramu Windows `CLAS5-positioning` istnieje, stan Ready,
codziennie 09:00, ostatni przebieg 2026-09-23 09:00:01 z wynikiem 0, następny 2026-09-24;
`collect.log`: +221 wierszy 2026-09-23, 0 błędów; BTC OI 512 punktów 1h od 2026-09-01 23:00.
Ograniczenia zadania: „Logon Mode: Interactive only" (działa tylko przy zalogowanym
użytkowniku) i „No Start On Batteries" — dni bez logowania zostawią dziurę, którą kolejny
przebieg częściowo nadrobi (500 punktów = ~20,8 dnia). ~~Użyteczne za ~3,4 roku.~~
**Aktualizacja P3 (2026-09-23):** archiwum `data.binance.vision` daje te same wielkości od
2020-09 z opóźnieniem ~1 dnia, więc kolektor jest zbędny dla historii; zostaje jako tania
kontrola świeżości do czasu, aż O1 potwierdzi codzienne uzupełnianie archiwum. Wyłączenie
(`schtasks /Delete /TN "CLAS5-positioning" /F`) = decyzja użytkownika (zadanie na jego maszynie).

#### P1 — sonda wykonalności źródeł danych (2026-09-22)

Przed postawieniem F sprawdzono, co jeszcze jest do wzięcia poza OHLCV. **Wszystkie pięć
endpointów pozycjonowania Binance** (open interest, long/short ratio, pozycje top traderów)
oddaje **30,8 dnia** historii; jawny `startTime` sprzed lat zwraca **HTTP 400**. To ~112
transakcji wobec wymaganych 4 481 — **brakuje 40×**. Kontrola: `klines` i `fundingRate` przy
tym samym zapytaniu oddają dane od 2020. **Cała klasa źródeł odpada mechanicznie**, nie
merytorycznie. → [runs/p1](runs/2026-09-22_p1-sonda-zrodel-danych/README.md)

#### Rachunek mierzalności (zasada 18) — policzony 2026-09-22 na `n` ZMIERZONYM w K3

Próg opłacalności bez bramki reżimu: **52,93%** (K3). Projekt zmierzył trafność **50,27%**
(Z10, n = 7 687). Dostępne `n` na jeden instrument: **8 033** (K3, C2/balanced).

**Jakiej trafności musi sięgać hipoteza, żeby w ogóle była widoczna:**

| zasięg | `n` | pasmo | min. wykrywalna trafność | nadwyżka nad zmierzonymi 50,27% |
|---|---|---|---|---|
| 1 instrument (4C, 4D) | 8 033 | 1,09 pp | **54,02%** | +3,75 pp |
| 3 instrumenty (4D) | 24 099 | 0,63 pp | 53,56% | +3,29 pp |
| ~~20 instrumentów (4A)~~ | ~~160 660~~ | ~~0,24 pp~~ | ~~53,17%~~ | ~~+2,90 pp~~ — **OBALONE w P2:** 18 monet ≈ k_eff 2,0 niezależnych |

**Ile transakcji trzeba, żeby wykryć efekt danej wielkości (moc 80%):**

| zakładana trafność | nadwyżka nad progiem | wymagane `n` | skala |
|---|---|---|---|
| 53,50% | 0,57 pp | 60 161 | 7,5× instrument BTC |
| 54,00% | 1,07 pp | 17 065 | 2,1× instrument BTC |
| 55,00% | 2,07 pp | 4 555 | **mieści się w jednym** |
| 58,00% | 5,07 pp | 756 | **mieści się w jednym** |

**Odczyt dla mapy — i on zmienia priorytety:**

- **4C i 4D wymagają, żeby model osiągnął 54–55% trafności kierunkowej.** Najlepszy pomiar
  w historii projektu to 50,27%. Nie są niemożliwe, ale wymagają efektu **większego niż
  cokolwiek, co kiedykolwiek zmierzyliśmy** — i nie naprawia tego dokładanie instrumentów,
  bo próg schodzi tylko z 54,02% do 53,17% przy dwudziestokrotnie większej próbie.
- **⚠ SPROSTOWANE przez P2 (2026-09-22):** poniższy punkt zakładał, że przekrój mnoży próbę.
  Zmierzone: korelacja zwrotów 0,47 ⇒ k_eff ≈ 2, a σ wyniku okna 5,56% wymaga ~25 850 okien
  wobec 1 161 — 4A (na samych perpetualach) jest **NIEMIERZALNE**.
- ~~**4A (carry przekrojowy) jest jedyną ścieżką z wykonalną arytmetyką — teraz liczbowo.**~~
  Jego próg opłacalności to **48,13%**, czyli **poniżej rzutu monetą**: wypłata nie wymaga
  przewagi kierunkowej. Przy trafności 50,00% wystarczy **5 606 transakcji**, czyli **0,70×**
  tego, co daje jeden instrument BTC. Wąskim gardłem nie jest liczba świec, tylko liczba
  **nienakładających się okien 48h** w 6,8 roku (H2.0: moc 0,03–0,12× na jednym
  instrumencie) — i to jest dokładnie to, co mnoży przekrój.
- **4B (inny target) i 4E (ekonomia dźwigni) pozostają poza tym rachunkiem.** 4B ma inną
  definicję wypłaty, więc próg opłacalności trzeba by policzyć od nowa; 4E nie tworzy edge'u,
  tylko mnoży istniejący — przy `p` nieodróżnialnym od monety mnoży zero.

**Ten rachunek NIE jest decyzją bramkową.** Mówi, które hipotezy da się zmierzyć, a nie którą
uruchomić. Każda nadal wymaga zgody użytkownika, własnej pre-rejestracji i własnego licznika
od zera.

### Czego ta mapa świadomie NIE zawiera

- **Kolejnych wariantów w seriach zamkniętych** (dwureżimowa, jednoreżimowa 4h). Obie reguły
  STOP są aktywne na stałe.
- **Powrotu do nogi `timeout`** — H3 zamknął temat; powrót wymaga danych o wypełnieniach
  zleceń, nie kolejnego założenia.
- **Budowy czegokolwiek z PRD** (5 agentów, dashboard, Docker) — zasada nadrzędna projektu
  nie zmieniła się: architektura powstaje PO dowodzie edge'u, nie przed.
