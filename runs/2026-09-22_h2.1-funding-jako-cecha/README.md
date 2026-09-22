# H2.1 — funding jako cecha, bez bramki reżimu: wynik NIEROZSTRZYGNIĘTY, model milczy w 99,3% (2026-09-22)

## W skrócie — prostym językiem (zasada 17)

**Co sprawdzaliśmy.** Faza 0 pokazała, że z samego wykresu ceny nie da się przewidzieć kierunku.
Więc dołożyliśmy informację **innego rodzaju** — opłatę, którą co 8 godzin płacą sobie
posiadacze pozycji długich i krótkich. To pierwsza w tym projekcie informacja, która nie jest
przetworzoną ceną. Zdjęliśmy też filtr, który wcześniej wycinał większość świec.

**Wynik: nie wiemy. I to jest uczciwa odpowiedź, nie wykręt.**

Powód jest zaskakujący i nie ma nic wspólnego z samą opłatą: **model prawie zawsze odmawia
zajęcia pozycji.** Na 14 448 ocenionych świec podjął decyzję **98 razy** — czyli w **0,7%**
przypadków. Przy tak małej liczbie transakcji każdy wynik mieści się w granicach przypadku,
więc z góry umówiliśmy się, że go nie interpretujemy. Umowa zadziałała.

**Dlaczego model milczy.** Zdjęcie filtra miało zwiększyć próbę — i zwiększyło liczbę
*ocenianych* świec czterokrotnie. Ale przy okazji **pogorszyło proporcje**: bez filtra aż
**66,6%** świec kończy się „nic się nie wydarzyło" (wcześniej 60,8%). Model uczy się, że
najbezpieczniej jest przewidywać właśnie to — i przestaje handlować.

**Co jednak widać.** Dodanie opłaty **potroiło liczbę decyzji** (35 → 98). Model uznał ją za
na tyle informacyjną, żeby częściej ryzykować. To jedyna rzecz, którą ta runda pokazuje —
ale **nie mówi nic o tym, czy te decyzje były trafne**, bo próbka jest za mała.

> ⚠️ **W surowym zapisie pojawia się słowo „GO". To NIE jest wynik pozytywny.** To znany
> artefakt liczony z 3 i 11 foldów, udokumentowany w C2.12 — przy kilku transakcjach na fold ta
> miara produkuje bzdury (tutaj wartość 21,3 przy typowej skali 1–3). Werdykt tej rundy brzmi
> **NIEROZSTRZYGNIĘTY**, i tylko tak wolno go cytować.

---

## ID testu

**H2.1** — pierwszy i jedyny eksperyment hipotezy H2. Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/H2.1-funding-jako-cecha`
- **Poprzedzający stan (master):** `b5bcadc`
- **Commity:** `8435939` (kod + zielona bramka leakage, PRZED eksperymentem)
- **Komenda:** `py -m backtest.run_funding_feature_h21` (pełny output: `raw_output.txt`)
- **Warianty:** **1 — LICZNIK H2 WYCZERPANY (0/1 → 1/1)**
- **Testy:** **319/319** (313 + 6 na tryb bez bramki; bramka leakage 19/19)

## Poprzedzające wyniki (zasada 14)

- **Z10** — diagnoza kierunkowa: wąskie gardło Fazy 0 było **informacyjne**, wszystkie cechy to
  transformacje ceny i wolumenu. To uzasadnia sięgnięcie po funding.
- **H2.0** — pre-rejestracja; odrzuciła bramkowanie na skrajnym funding (moc 0,05–0,44×)
  i carry (0,03–0,12×), zostawiając to sformułowanie jako **jedyne wykonalne**.
- **H3** — sprostowanie progu: **53,12% → 52,69%** (mój błąd: koszt bramkowy zamiast realnego).
- **S1b** — precedens klauzuli nierozstrzygalności i źródło lejka odniesienia.
- **Z16** — `V=3` jako jedyny horyzont spójny na 4h.
- **Z17b** — early stopping potrafi po cichu podnieść abstynencję modelu z 70,9% do 90,5%.
  **Tutaj ten mechanizm wrócił w skrajnej postaci.**

## Konfiguracja (ZAMROŻONA przed uruchomieniem)

| element | wartość |
|---|---|
| interwał | 4h natywne, 2019-09 → 2026-07 (14 916 świec) |
| bramka reżimu | **BRAK** (`REGIME_ALL`) |
| cechy | `REVERSION_FEATURES` (4) + `funding_rate` |
| V | 3 (12h) |
| walk-forward | 60/28/28 dni, seed 42 |
| model kosztów | niezmieniony (maker/taker, `timeout_leg=TAKER`) |
| **kryterium** | **`ci_low(p) > 52,69%`** |
| **klauzula** | **`n < 1 000` ⇒ NIEROZSTRZYGNIĘTE** |

**Poprawka do pre-rejestracji z H2.0, zapisana przed uruchomieniem** (commit `8435939`):
(a) rozbicie na dwa ramiona, bo pierwotny zapis zmieniał naraz dwie rzeczy wobec S1b (bramka
+ cecha) i łamał zasadę 4; (b) **jedna cecha surowa zamiast „funding + z-score"** — XGBoost
jest drzewiasty, więc niewrażliwy na monotoniczne przeskalowanie, a każdy wybór okna
normalizacji byłby wolnym parametrem bez możliwości kalibracji. Obie poprawki to
**zaostrzenia**; kryterium, klauzula i reguła STOP niezmienione.

---

## Wynik

### Lejek — tu jest cała historia tej rundy

| licznik | A (4 cechy) | B (4 + funding) |
|---|---|---|
| świec ocenionych | 14 448 | 14 448 |
| **model odmówił kierunku** | **14 413 (99,76%)** | **14 350 (99,32%)** |
| odrzucone przez bramkę kosztową | 0 | 0 |
| **transakcji** | **35** | **98** |
| foldy / pominięte | 86 / **0** | 86 / **0** |
| foldy z early stoppingiem | 86 | 86 |

**Zdjęcie bramki zadziałało dokładnie tak, jak miało — i to nie wystarczyło.** Ocenionych
świec jest 4× więcej niż w S1b (14 448 vs 3 642), a **pominiętych foldów jest ZERO** (w S1 były
22 z 85, i walidacja wykazała, że nie były losowe). Ale abstynencja modelu skoczyła z 90,5% do
**99,3%**, więc próba spadła z 345 do 98.

### Dlaczego model milczy — mechanizm zmierzony, nie zgadnięty

Rozkład etykiet przy `V=3` na 4h:

| etykieta | tylko reżim `range` (S1b) | **wszystkie świece (H2.1)** |
|---|---|---|
| −1 (dolna bariera) | 20,44% | 17,23% |
| **0 (timeout)** | **60,83%** | **66,58%** |
| +1 (górna bariera) | 18,73% | 16,19% |

**Zdjęcie bramki podniosło udział klasy dominującej o 5,75 pp.** Reżim `range` to świece
o niskim ATR, więc bariery ±1,5×ATR są tam wąskie i częściej dotykane. Bez bramki wchodzą
świece o szerokich barierach, których 12h nie wystarcza dotknąć. Przy działającym early
stoppingu (86/86 foldów) model uczy się, że najbezpieczniej przewidywać klasę większościową.

> **To jest to samo zjawisko co w Z17b, tylko silniejsze.** Tam naprawa early stoppingu ścięła
> próbę z 1 037 do 345. Tutaj zdjęcie bramki ścięło ją z 345 do 98 — i **znowu nie
> przewidziałem tego przed uruchomieniem**, mimo że precedens był udokumentowany w tym samym
> repo.

### Rozbicie edge'u

| miara | A baseline | B kandydat | delta |
|---|---|---|---|
| n transakcji | 35 | **98** | **+63** |
| trafność | 57,14% | 46,94% | −10,20 pp |
| 95% CI | [40,75%; 73,54%] | [37,06%; 56,82%] | — |
| break-even | 52,43% | 52,49% | +0,07 pp |

**Jedyne, co te liczby pokazują:** dodanie funding **potroiło liczbę decyzji** (35 → 98), czyli
model uznał tę cechę za na tyle informacyjną, żeby częściej opuszczać klasę „timeout".
**Trafności NIE wolno tu czytać** — oba przedziały ufności obejmują 50% i są szerokie
odpowiednio na 33 i 20 punktów procentowych.

### ⚠️ Czerwona flaga: „GO" w surowym zapisie

`classify_checkpoint` zwraca **GO** dla OBU ramion. To **artefakt, nie wynik**:

| | A | B |
|---|---|---|
| `n_valid_folds` | **3** z 86 | **11** z 86 |
| `mean_sharpe` | 2,28 | **21,31** |

`mean_sharpe = 21,3` przy typowej skali 1–3 to dokładnie patologia udokumentowana w C2.12
(annualizacja przy kilku transakcjach na fold; σ fold-jitter rozjechała się tam 3,1 → 75,7).
CLAUDE.md wytyczna miękka mówi wprost, że **per-fold `mean_sharpe` nie jest nośną statystyką**.
Odnotowuję to jawnie, bo write-up bez tego ostrzeżenia dałoby się zacytować jako „projekt
osiągnął GO" — co byłoby nieprawdą.

## WERDYKT: **NIEROZSTRZYGNIĘTY** (klauzula pre-rejestrowana)

`n = 98 < 1 000` ⇒ klauzula wchodzi w grę. **Wyniku nie interpretuję w żadną stronę** — ani
jako potwierdzenia, ani jako zaprzeczenia hipotezy. Żeby cokolwiek orzec przy tej próbie,
trzeba by zmierzyć trafność **62,59%**; nic w historii projektu nie zbliża się do tej wartości.

**Licznik H2: 1/1 — WYCZERPANY.** Wariant zostaje zużyty niezależnie od tego, że wynik jest
nierozstrzygnięty: porównanie zostało wykonane na tych danych. Reguła STOP zamyka serię.

## Co na plus (+)

- **Klauzula nierozstrzygalności zadziałała po raz drugi** i znowu powstrzymała nadinterpretację.
  Bez niej „46,94% wobec progu 52,69%" brzmiałoby jak twarde obalenie, a to odczyt bezpodstawny
  przy `n=98`.
- **Bramka leakage przeszła przed eksperymentem** (zasada 2), z trzema metodami, w tym jedną
  celowaną wprost w ryzyko specyficzne dla złączenia dwóch źródeł o różnych siatkach czasowych.
- **Zdjęcie bramki naprawiło dokładnie to, co miało naprawić:** zero pominiętych foldów wobec
  22 z 85 w S1, i to właśnie tych systematycznie wycinających okna szybkich ruchów.
- **Czerwona flaga „GO" wyłapana i opisana**, zamiast przemilczana.
- **Nowa cecha i tryb bez bramki zostają w repo jako sprawdzona infrastruktura**, niezależna
  od losu tej hipotezy.

## Co na minus (−)

- **Nie przewidziałem zapaści próby, mimo że precedens był udokumentowany w tym samym repo**
  (Z17b: naprawa early stoppingu ścięła n trzykrotnie). Rachunek mocy w H2.0 szacował ~1 200
  transakcji na podstawie lejka zmierzonego **przy bramce** — i wprost zapisałem wtedy, że ten
  lejek „może być inny w obie strony". Był inny 12-krotnie w złą stronę. **To ta sama klasa
  błędu co margines mocy 4,3× w Z5b, który okazał się fikcją.**
- **Runda zużyła jedyny wariant hipotezy H2 i nie rozstrzygnęła jej.** Stan informacyjny po niej
  jest niewiele lepszy niż przed.
- **Nie wiem, czy abstynencja 99,3% to zdrowa ostrożność, czy patologia early stoppingu** przy
  `MIN_VALIDATION_ROWS = 30` — to samo pytanie zostało bez odpowiedzi w S1b i nadal jej nie ma.
  Rozstrzygnięcie wymagałoby zagnieżdżonego walk-forward (zadanie T4 mapy drogowej).
- **Klasa większościowa nie była mierzona przed eksperymentem.** Rozkład etykiet bez bramki
  (66,58% timeoutów) dało się policzyć w pięć sekund **przed** uruchomieniem i przewidzieć
  problem. Rachunek mocy patrzył na liczbę świec, a nie na to, czy model będzie miał czego się
  na nich nauczyć.

## Walidacja (zasada 16a) — werdykt: **CAVEATS**

- **Kluczowa liczba przeliczona drugą drogą:** mechanizm abstynencji zweryfikowany niezależnie
  od backtestu — rozkład etykiet policzony bezpośrednio z `compute_triple_barrier_labels`
  na tych samych danych (66,58% timeoutów bez bramki vs 60,83% w `range`). To wyjaśnia wzrost
  abstynencji ścieżką całkowicie niezależną od silnika.
- **Kogo NIE ma w zbiorze:** (a) **14 350 z 14 448 świec** — model odmówił kierunku; wynik
  obowiązuje na **0,7%** ocenionych świec; (b) **2 świece bez funding** (sprzed pierwszego
  rozliczenia 2019-09-10T08:00) — pomijalne; (c) **tylko BTC, tylko 4h, tylko V=3**; (d) zestaw
  cech to `REVERSION_FEATURES` (4), **nie wszystkie 10** — projekt nigdy nie karmił jednego
  modelu wszystkimi; (e) krach COVID jest **w zbiorze** (zero pominiętych foldów), w odróżnieniu
  od S1 — to jedyny wymiar, w którym ta runda ma szerszą populację niż poprzednie.
- **Red-flag „wynik idealnie potwierdza hipotezę":** **ZACHODZI w formie odwrotnej** —
  `classify_checkpoint` zwrócił **GO** dla obu ramion. Obsłużone: pokazane jako artefakt
  `mean_sharpe` przy 3 i 11 ważnych foldach, z odwołaniem do C2.12 i do wytycznej CLAUDE.md.
  **Werdykt rundy jest NIEROZSTRZYGNIĘTY i nie opiera się na tej mierze.**
- **Dlaczego CAVEATS, a nie READY:** liczby są poprawne, ale **runda nie odpowiada na pytanie,
  które zadała**. Nie da się orzec, czy funding niesie informację — wiadomo tylko, że model
  uznał ją za wartą częstszego działania. To ustalenie o zachowaniu modelu, nie o rynku.

## Wniosek

**Hipoteza H2 pozostaje NIEROZSTRZYGNIĘTA, a jej licznik jest wyczerpany.**

Przyczyną nie jest funding ani długość historii, tylko **struktura zadania uczenia**: przy
`V=3` na 4h dwie trzecie świec kończy się bez dotknięcia bariery, a model z działającym early
stoppingem uczy się przewidywać tę klasę i przestaje handlować. **Zdjęcie bramki, które miało
powiększyć próbę, pogorszyło proporcję klas i zmniejszyło ją ponad trzykrotnie.**

To trzeci raz, gdy ten sam mechanizm zaskakuje projekt: S1 → S1b (1 037 → 345), S1b → H2.1
(345 → 98). **Za każdym razem szacunek próby powstawał z liczby świec, a nie z tego, ile z nich
model uzna za wartą działania.**

## Rekomendacja

1. **Reguła STOP zamyka serię H2.** Żadnego drugiego `V`, interwału ani wariantu cechy —
   uruchomienie czegokolwiek po zobaczeniu tego wyniku byłoby dokładnie tym, czemu reguła
   zapobiega.
2. **Do mapy drogowej wchodzi nowy wymóg, wynikający z trzeciej powtórki tego samego błędu:**
   rachunek mocy przed eksperymentem musi obejmować **rozkład klasy docelowej**, a nie tylko
   liczbę świec. Liczba obserwacji nie jest liczbą transakcji.
3. **Zadanie T4 mapy drogowej awansuje** (`MIN_VALIDATION_ROWS` / `validation_fraction`
   nieskalibrowane): to samo pytanie zostało bez odpowiedzi trzeci raz z rzędu i blokuje
   interpretację każdego kolejnego wyniku.
4. **Decyzja o dalszym kierunku należy do użytkownika** (Etap 2 mapy drogowej, wariant
   „nierozstrzygalny"): jedyną drogą do większej próby jest **wymiar przekrojowy** — ten sam
   mechanizm na wielu instrumentach — a nie kolejne `V`, interwał ani cecha na BTC.

## Pełny surowy output

[`raw_output.txt`](raw_output.txt). Skrypt: [`backtest/run_funding_feature_h21.py`](../../backtest/run_funding_feature_h21.py).
