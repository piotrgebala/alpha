# Z10 — ZAMKNIĘCIE FAZY 0 wynikiem negatywnym (2026-09-22)

## ID testu

**Z10** — decyzja bramkowa fazy, nie eksperyment. Patrz `runs/INDEX.md`.

## W skrócie — prostym językiem (CLAUDE.md zasada 17, dopisane po fakcie)

**Co sprawdzaliśmy przez całą Fazę 0:** czy da się zarobić, przewidując kierunek ceny bitcoina
na podstawie samego wykresu ceny i obrotu.

**Odpowiedź: nie da się. I to jest mocna odpowiedź, nie wymijająca.**

Różnica jest ważna. „Nie znaleźliśmy" znaczyłoby tylko tyle, że mogliśmy szukać za słabo.
Tutaj jest inaczej: **zebraliśmy prawie trzy razy więcej danych, niż było potrzeba**, żeby taki
zysk wykryć — więc gdyby istniał, zobaczylibyśmy go.

Liczby w jednym zdaniu: system trafiał w **50,27%** przypadków (na 7 687 transakcjach), a żeby
wyjść na zero po opłatach giełdowych, musiałby trafiać w **52,69%**. Margines błędu pomiaru
sięga najwyżej 51,38% — czyli **nawet najbardziej optymistyczny odczyt nie dobija do progu
opłacalności**. Dla porównania: rzut monetą to 50%.

**Gdzie leży problem:** nie w programie i nie w metodzie. Po kolei naprawiliśmy sześć rzeczy —
sposób liczenia zysku, model opłat, dopasowanie filtrów, jakość danych, błąd w uczeniu modelu
i samą metodę pomiaru. **Po każdej naprawie trafność wracała do 50%.** Powód jest prostszy:
wszystkie 10 informacji, którymi karmiliśmy model, to **przetworzona cena i obrót**. Czyli
ciągle to samo, w dziesięciu wariantach. Nie wyczerpaliśmy metod — wyczerpaliśmy **jedno źródło
informacji**.

**Czego ta Faza 0 NIE udowodniła** (i nie wolno tego mylić z powyższym):
- **momentum** — czyli „gdy cena rośnie, będzie rosła dalej" — **nigdy nie dostało uczciwego
  testu.** Filtr, który miał wyłapywać takie momenty, przepuszczał ich tak mało (pół procenta
  czasu), że nie było czego mierzyć;
- **nie testowaliśmy ETH, SOL ani BNB** — wszystko robiliśmy na bitcoinie;
- **nie testowaliśmy opłaty za utrzymanie pozycji jako sygnału** — traktowaliśmy ją wyłącznie
  jako koszt;
- **nie testowaliśmy, czy da się zarobić na dźwigni i wielkości pozycji** zamiast na kierunku.

**Co z tego wynika praktycznie:** Faza 0 zrobiła dokładnie to, do czego była. Jej zadaniem było
**sprawdzić, zanim zbudujemy** — i sprawdziła. Nie powstał ani jeden z pięciu planowanych
agentów, dashboard ani Docker. Zaoszczędzone: cała budowa systemu wokół sygnału, którego nie ma.

---

## Metadane

- **Typ:** decyzja bramkowa (CLAUDE.md, „Podział ról" — **wyłączna kompetencja użytkownika**)
- **Decydent:** użytkownik, 2026-09-22
- **Treść decyzji (dosłownie):** *„Zamknąć Fazę 0 — z uczciwym sformułowaniem: »specyfikacja
  dwureżimowa i jednoreżimowa na range obalone; momentum, ETH/SOL/BNB, funding-jako-cecha
  i ekonomia dźwigni nieprzetestowane«. Otworzyć nową hipotezę — momentum bez bramki reżimu,
  albo funding rate jako sygnał. Własna pre-rejestracja, własny licznik, własna reguła STOP."*
- **Branch:** `task/Z10-zamkniecie-fazy-0`
- **Poprzedzający stan (master):** `c3bbc5e`
- **Komenda:** `py runs/2026-09-22_z10-zamkniecie-fazy-0/z10_bilans.py` (`raw_output.txt`)
- **Warianty:** **0** — decyzja i synteza, zero nowych porównań na danych.
- **Testy:** **251/251**.

## Poprzedzające wyniki (zasada 14)

Ten dokument nie wprowadza nowej wiedzy — domyka 17 rund. Pełna tabela: `runs/INDEX.md`.
Bezpośrednio rozstrzygające:

- **C2.5–C2.13** — seria falsyfikacji hipotezy dwureżimowej na 5m; reguła STOP programu
  „droga do GO" uruchomiona po C2.13.
- **Z16** — reżim `trend` strukturalnie niespójny z horyzontem etykiety; **Z8 domknięty**
  (wymagane B = 4,21% ceny ⇒ horyzont ~39 dni vs epizody reżimu 5h15m).
- **Z17+Z21** — przeciek early stopping naprawiony; `p` było **zawyżone** (51,07% → 50,38%).
- **Z5b → S1 → S1b** — hipoteza jednoreżimowa 4h: pre-rejestracja, wynik negatywny, a po
  naprawie Z17b **nierozstrzygalny przy dostępnych danych**.
- **Walidacja S1 (zasada 16a)** — werdykt **CAVEATS**; ustaliła, na jakiej populacji wynik
  obowiązuje (6,95% historii).

## Liczba, na której stoi to zamknięcie

Poprzednie write-upy orzekały **per runda**. Zamknięcie fazy wymaga liczby **zbiorczej**, więc
policzyłem ją od zera z kanonicznych `raw_output.txt` (nie z syntez w write-upach) — pooled
trafność kierunku na trzech **najczystszych** pomiarach projektu, czyli wykonanych **po** naprawie
przecieku early stopping:

| pomiar | n | wygranych | `p` | CI95 |
|---|---|---|---|---|
| 5m `range` (Z17+Z21) | 7 043 | 3 548 | 50,38% | [49,21%; 51,54%] |
| 5m `trend` (Z17+Z21) | 299 | 152 | 50,84% | [45,17%; 56,50%] |
| 4h `range` (S1b) | 345 | 164 | 47,54% | [42,27%; 52,81%] |
| **POOLED** | **7 687** | **3 864** | **50,27%** | **[49,15%; 51,38%]** |

> **z = +0,47 wobec H₀: p = 50% — nieodróżnialne od rzutu monetą.** Półszerokość CI: 1,12 pp.

**S1 (n = 1 037, p = 48,60%) świadomie POMINIĘTY** w tym zestawieniu: to te same dane co S1b,
zmierzone na pipelinie z martwym early stoppingiem. Wliczenie obu byłoby podwójnym liczeniem
tej samej historii — i, co ważne, pominięcie działa **na korzyść hipotezy** (S1 ma niższe `p`).

### Dlaczego to zamyka sprawę mocniej niż którakolwiek pojedyncza runda

| | |
|---|---|
| najniższy próg opłacalności zmierzony w projekcie | **52,69%** (4h, model maker/taker) |
| górny kraniec CI95 dla pooled `p` | **51,38%** |
| **różnica** | **−1,30 pp — przedział ufności NIE SIĘGA progu** |
| transakcji na wykrycie `p` = 52,69% wobec H₀ = 50% przy mocy 80% | 2 717 |
| zmierzono łącznie | **7 687** |
| **moc** | **2,8× wymaganej próby** |

To jest różnica, na której zależy mi najbardziej i której nie było w żadnym pojedynczym
write-upie: **nie „nie znaleźliśmy edge'u", tylko „mieliśmy moc 2,8×, żeby go znaleźć, a
przedział ufności go wyklucza".** Pierwsze to brak dowodu. Drugie to dowód braku — w granicach
przetestowanej specyfikacji.

Luka do pozostałych progów, dla skali: **+6,50 pp** (1h) i **+32,54 pp** (5m taker).

## Co zostaje OBALONE

Sformułowania poniżej są celowo wąskie — obalona jest **specyfikacja**, nie „trading algorytmiczny
na krypto".

1. **Hipoteza dwureżimowa** (deterministyczna bramka `trend`/`range` + dwa modele XGBoost na
   10 cechach OHLCV, świece 5m). Pięć niezależnych testów na starej bazie, potwierdzone na
   nowej 3-letniej (pooled t: `range` −10,47 / `trend` −5,51), odporne na fold-jitter 10/10.
2. **Hipoteza jednoreżimowa 4h na `range`** (V = 3, historia 6,8 roku, pre-rejestrowana w Z5b).
   Kryterium przepadło o 9,04 pp.
3. **Cztery hipotezy naprawcze**, każda testowana osobno i osobno odrzucona: kalibracja progów
   reżimu (C2.5), grubszy interwał (C2.6/Z9/S1), dodatkowa cecha `adx_14` (C2.8), próg pewności
   modelu (C2.13 — trafność **spadła** zamiast wzrosnąć, kierunek przeciwny do przewidywanego).
4. **Teza „to koszty nas zabijają, wystarczy je urealnić"** — model maker/taker obniżył koszt
   o 52% i domknął ~połowę luki (C2.12), a na 4h bramka kosztowa odrzucała **0%** sygnałów.
   Geometria została naprawiona i to **nie pomogło**: `p` ani razu nie drgnęło w górę.

## Czego NIE wykazano — lista, którą trzeba czytać razem z powyższą

To jest część, którą najłatwiej przemilczeć, więc jest tu jawnie. **Żadnego z poniższych
projekt nie testował, i żadne nie zostało „obalone przez implikację":**

| obszar | stan faktyczny |
|---|---|
| **momentum / kontynuacja trendu** | **NIEPRZETESTOWANE.** Werdykt dla `trend` opiera się na próbie zagłodzonej przez samą regułę reżimu: 0,53% świec, n = 299–355, a tylko **0,49%** świec ma okno etykiety wewnątrz własnego reżimu (Z16). Niemal każda transakcja była oceniana ruchem spoza reżimu, który ją uzasadnił. Najczystszy pomiar projektu (S1/S1b) testował **wyłącznie `range`**. To niewykonalność pomiaru, nie dowód braku edge'u |
| **konfiguracja 4h po naprawie pipeline'u** | **NIETESTOWALNA** (S1b): przy działającym early stoppingu n = 345 wobec wymaganych 925; brakuje **11,4 lat** danych, których Binance nie ma |
| **ETH / SOL / BNB** | **ZERO testów.** Wszystko na BTC (zasada 9: BTC do końca przed resztą — i ten warunek nigdy nie został spełniony) |
| **funding rate jako CECHA/sygnał** | **Nigdy nie zaimplementowany.** Modelowany wyłącznie jako składnik kosztu — i to jedną stałą (`FUNDING_RATE_8H = 0.0001`), nie danymi. Zadeklarowany w `feature_registry.yaml` jako `planned_not_added` od początku projektu |
| **ekonomia sizingu i dźwigni** | Kill-switch testowany **mechanicznie** (C2c: czy nie zakleszcza się), nigdy jako dźwignia rentowności |
| **target inny niż kierunek** | Np. zmienność, czas do bariery — poza zakresem, zero rund |
| **informacja spoza OHLCV** | **Wszystkie 10 cech to transformacje ceny i wolumenu.** Projekt nigdy nie sprawdził innego zbioru informacyjnego — to najważniejsza luka i uzasadnienie kierunku H2 |

## Bilans zasobów

| | |
|---|---|
| rundy z katalogiem w `runs/` | 17 (+ ta) |
| **budżet multiple-testing zużyty** | **10 wariantów** — 7 (stara baza, dwureżimowa) + 2 (nowa baza) + 1 (jednoreżimowa 4h, licznik 1/1 wyczerpany) |
| dane | BTC 5m: 315 648 świec (3 lata) · 1h: 26 304 · **4h: 14 916 (6,8 roku)** — zero dziur, cache trwały |
| testy | **251/251** |
| reguły STOP uruchomione | 2 (program „droga do GO" po C2.13; seria jednoreżimowa po S1) |

## Co na plus (+)

- **Faza 0 zrobiła dokładnie to, do czego była.** Jej celem było *udowodnić edge, zanim
  powstanie architektura* — a nie *znaleźć edge*. Wynik negatywny osiągnięty za 10 wariantów
  i 251 testów, zanim powstał choćby jeden z 5 agentów, dashboard czy Docker z PRD, to
  **sukces procesu**, nie porażka. Koszt uniknięty: cała architektura wokół sygnału, którego nie ma.
- **Cztery wady pomiaru wykryte i naprawione po drodze** — każda z nich, niewykryta,
  produkowałaby fałszywie pozytywny wynik albo fałszywe uzasadnienie:
  przeciek early stopping (zawyżał `p`), brak embarga, resample psujący wolumen (11% świec 1h,
  błędy do 284%), pusty sweep seedów (XGBoost deterministyczny — mierzył nic).
- **Dyscyplina utrzymała się pod presją wyniku.** Reguła STOP zadziałała dwa razy; klauzula
  nierozstrzygalności w S1b powstrzymała odczytanie `n = 345` jako „jeszcze gorzej"; walidacja
  zasady 16a wycofała własne przesadzone sformułowania z opublikowanego write-upu.
- **Infrastruktura jest hipotezo-niezależna i zostaje w całości** (patrz niżej).

## Co na minus (−)

- **Rachunek mocy przyszedł za późno.** `Z19` (`required_trades`, `min_detectable_hit_rate`)
  powstał dopiero po C2.13 — po zużyciu **9 z 10 wariantów**. Gdyby istniał przed C2.5,
  pokazałby, że próg 82,81% na 5m jest nieosiągalny dla ~50-procentowego sygnału, i oszczędził
  większość serii. To najdroższy błąd procesu w tym projekcie.
- **Zasada 16(a) była łamana systematycznie** — walidacja write-upów uruchomiona raz, po fakcie,
  na żądanie użytkownika, i natychmiast wyłapała przesadzoną retorykę w S1. Pozostałe 16 rund
  nie przeszło tej bramki.
- **DoD punkt 6 (`docs/rag`) łamany przez całą serię** — instrukcja, która **zakodowała buga**
  (early stopping „na foldzie OOS"), przeżyła w `docs/rag/03` z datą `last_verified` świeższą
  niż błąd, do D2. Dokumentacja niosła błąd dalej niż kod.
- **Momentum nie dostało uczciwej szansy i już jej nie dostanie w tej specyfikacji.** Bramka
  reżimu, która miała je wyizolować, zagłodziła próbę do 0,53% świec. Projekt odnotował to
  dopiero w Z16 — po tym, jak `trend` był już wielokrotnie raportowany jako „przetestowany".
- **Zamknięcie fazy nie jest zamknięciem pytania.** Siedem obszarów z tabeli wyżej pozostaje
  otwartych. Uczciwy stan to „ta specyfikacja nie ma edge'u", a nie „edge'u nie ma".

## Co zostaje użyteczne niezależnie od hipotezy

Nic z poniższego nie jest związane z bramką reżimu ani z parą trend/range — wszystko przechodzi
do H2 bez zmian:

- `backtest/checkpoint_lib.py` + `run_checkpoint_v2.py` — kanoniczna metodologia (fold-jitter,
  pooled t, N_eff);
- `backtest/metrics.py` — rozbicie `(2p−1)·B > C` na człony, CI, **rachunek mocy**
  (`required_trades`, `min_detectable_hit_rate`, `wald_half_width`);
- `backtest/costs.py` — model wykonania maker/taker z nogami per typ wyjścia;
- `agents/regime_coherence.py` — pomiar spójności bramka↔horyzont (`is_rule_admissible`);
- `agents/labeling.py` — triple-barrier z parametrycznym `V` + walk-forward skalowany per interwał;
- `agent_5_compliance/test_leakage.py` — testy leakage per cecha (ze **świadomością
  udokumentowanych ograniczeń**: ślepe na poziom modelu i podziału, `docs/rag/02`);
- **trwały cache danych** `data/raw/` — 5m/1h/4h, w tym 6,8 roku 4h;
- księga budżetu multiple-testing i konwencja rund (`runs/INDEX.md`) — proces, który w tej
  fazie dwukrotnie zatrzymał p-hacking.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Kluczowa liczba przeliczona niezależnie:** pooled `p` policzone od zera ze skryptu
  `z10_bilans.py`, ze źródeł `raw_output.txt` poszczególnych rund, **z pominięciem syntez
  w write-upach**. Kontrola całkowitości: `p × n` musi dać liczbę całkowitą wygranych dla
  każdego składnika — spełnione dla wszystkich trzech (asercja w skrypcie).
- **Kogo NIE ma w zbiorze:** (a) **S1 pominięty celowo** — podwójne liczenie tej samej historii;
  pominięcie działa **na korzyść** hipotezy; (b) **wszystkie pomiary sprzed naprawy Z17+Z21
  pominięte** — zawierały przeciek zawyżający `p`, więc ich włączenie też działałoby na korzyść
  hipotezy; (c) pooled łączy dwie bazy danych (5m 3 lata i 4h 6,8 roku) i dwa reżimy —
  metodologicznie to mieszanka, dlatego **liczba zbiorcza nie zastępuje werdyktów per runda**,
  tylko podsumowuje ich kierunek; (d) wszystkie ograniczenia populacji ze S1 (6,95% historii,
  krach COVID poza zbiorem) **przechodzą na składnik 4h** i nie są tu naprawione; (e) `trend`
  wnosi 299 z 7 687 obserwacji (3,9%) — **pooled jest zdominowane przez `range`**, więc nie
  jest dowodem w sprawie momentum i nie jest tak cytowane.
- **Red-flag „wynik idealnie potwierdza hipotezę":** nie zachodzi — liczba zbiorcza jest
  *słabsza* niż retoryka poszczególnych write-upów (50,27% to „moneta", a nie „ujemny edge")
  i **osłabia** wcześniejsze sformułowania o „istotnie ujemnym zwrocie". Istotność ujemna
  w rundach pochodziła z **kosztów**, nie z odwróconego sygnału — co potwierdza walidacja S1
  (brutto `t = −0,48`, nieodróżnialne od zera).
- **Ograniczenie:** pooled CI nie uwzględnia autokorelacji między nakładającymi się oknami
  (`N_eff < n`). Korekta poszerzyłaby CI, ale **nie zmienia werdyktu**: żeby górny kraniec
  sięgnął 52,69%, `N_eff` musiałoby spaść do **1 640, czyli 21,3% `n`** — a zmierzone `n_eff/n`
  w tym projekcie wynosi **60,2%** (S1b: 207,6/345) i **59,8%** (S1: 620,0/1 037), czyli blisko
  trzykrotnie więcej. Margines na autokorelację jest więc zachowany z zapasem.

## Wniosek

**Faza 0 zostaje zamknięta wynikiem negatywnym.** Hipoteza, dla której powstała — regime-gated
momentum/mean-reversion na cechach OHLCV — **nie ma edge'u kierunkowego wystarczającego do
pokrycia kosztów transakcyjnych**, i nie jest to brak dowodu, tylko dowód braku: przy mocy 2,8×
przedział ufności [49,15%; 51,38%] nie sięga najniższego progu opłacalności zmierzonego
w projekcie (52,69%).

Wąskie gardło jest **informacyjne, nie inżynieryjne**. Projekt naprawił po kolei geometrię
wypłaty, model kosztów, spójność bramki z horyzontem, jakość danych, przeciek w treningu
i metodologię pomiaru — i po każdej z tych napraw `p` pozostawało przy 50%. Wszystkie 10 cech
to transformacje tej samej informacji: ceny i wolumenu. **Nie wyczerpaliśmy metod. Wyczerpaliśmy
jeden zbiór informacyjny.**

## Rekomendacja

1. **Faza 0 zamknięta** — żadnych dalszych wariantów w seriach dwureżimowej i jednoreżimowej.
   Obie reguły STOP pozostają aktywne **na stałe**; ten dokument ich nie zdejmuje.
2. **Nowa hipoteza (H2) startuje jako osobny byt** — własna pre-rejestracja, **własny licznik
   od zera**, własna reguła STOP, własny rachunek mocy **przed** uruchomieniem (lekcja
   z minusa nr 1 powyżej). Nie dziedziczy budżetu ani progów po Fazie 0.
3. **Kierunek H2 wybrany zgodnie z diagnozą powyżej:** wąskie gardło jest informacyjne, więc
   zmianą, która może ruszyć `p`, jest **nowy zbiór informacyjny**, a nie kolejna transformacja
   OHLCV ani kolejna architektura nad tymi samymi cechami. Pre-rejestracja: `runs/` H2.
4. **Trzy rzeczy do przeniesienia jako twarde wymogi H2**, bo w Fazie 0 zawiodły:
   rachunek mocy **przed** eksperymentem; walidacja write-upu **przed** publikacją (zasada 16a);
   aktualizacja `docs/rag` **w tej samej rundzie**, co zmiana w kodzie (DoD punkt 6).

## Pełny surowy output

Patrz [`raw_output.txt`](raw_output.txt). Skrypt przeliczenia: [`z10_bilans.py`](z10_bilans.py).
