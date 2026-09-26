# TP1 — wyjście na celu zysku +1 % / +2 % „większym wolumenem” na strategiach dziennika (2026-09-26)

> **STATUS: NIEMIERZALNA — runda NIE wystartowała** (CLAUDE.md zasada 18). Decyzja użytkownika: „sprawdź jednak” (po
> ostrzeżeniu, że prior jest zły — N1, wnioski 45, 70, 72). Policzono wyłącznie zgodność silnika, mechanikę celu i szum
> porównania — **żadnej średniej wyniku nie obejrzano. 0 wariantów zużytych.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Pomysł: zamykać każdą pozycję, gdy zarobi 1 % albo 2 %, i grać większą pozycją. Żeby porównanie było uczciwe, obie wersje
(z celem zysku i bez) dostały to samo sterowanie ryzykiem co dziennik. Wersja z celem jest spokojniejsza, więc automatycznie
dostaje większą pozycję. Tak w praktyce wygląda „większy wolumen”.

**Wynik: historia nie potrafi tego rozstrzygnąć.** Obie wersje różnią się dzień po dniu tak mocno, że różnica ich wyników
ma rozrzut ±18–20 punktów procentowych rocznie. Uczciwe wykrycie zmiany o 5 punktów rocznie wymagałoby **67–83 lat danych**,
a mamy 5,4 roku. Zasada 18 mówi wtedy: nie startujemy i nie oglądamy wyników, bo liczba, która niczego nie rozstrzyga,
tylko by kusiła.

Bez patrzenia na zyski wyszły dwa fakty o samym mechanizmie:
- **cel zysku uruchamia się prawie zawsze**: w 86–92 % pozycji trendu i 78–88 % pozycji premii Coinbase (niemal każda moneta
  w ciągu tygodnia choć na chwilę zyskuje 1–2 %);
- **„większy wolumen” szybko uderza w sufit dźwigni**: żeby wersja z celem miała to samo ryzyko, trend musiałby w 97 % dni
  grać na maksymalnej dźwigni 2×; premia Coinbase w 9–48 % dni.

## Metadane

- Branch `tp1-cel-zysku` (z `master` `2974061`). Kod: `backtest/take_profit.py` (silnik z celem zysku), `tests/test_take_profit.py`
  (8), `backtest/run_tp1_cel_zysku.py` (tylko mierzalność). Komenda: `PYTHONUTF8=1 py -m backtest.run_tp1_cel_zysku --moc`
  → `moc.txt` (12 s). Druga droga: `PYTHONPATH=. PYTHONUTF8=1 py runs/2026-09-26_tp1-cel-zysku/druga_droga.py` → `druga_droga.txt`.
- Dane: jak nogi dziennika na pełnych danych — trend TS1 na `universe_full` (2021-02 → 2026-06, 1 969 dni), premia Coinbase
  CP1 (2021-05 → 2026-06, 1 880 dni); dzienne maksima i minima z `universe_ohlc_full` (195 monet — wszyscy członkowie top-20).

## Poprzedzające wyniki

- **N1 (wniosek 45):** częściowe wyjście na +1,67 % i stop na wejściu (BTC 4h) — różnica wobec zwykłego wyjścia +0,007 %
  na transakcję [−0,009; +0,024]; trafność 53,3 % to złudzenie przy progu 57,2 %. Seria N zamknięta 1/1.
- **SC1 (wniosek 78):** skalowanie siłą sygnału — szum różnicy ±13–17 %/rok → NIEMIERZALNA, nie wystartowała.
- **Wnioski 70, 72:** zyski trendu i premii Coinbase pochodzą z nielicznych dużych ruchów (bez 10 najlepszych dni: trend
  ~+15 → +6 %/rok, premia +32 → +16 %/rok). **KO1 (99):** koszty 0,8–1,5 %/rok. **LQ1 (76):** likwidacje przy 2×.
- **Teoria (zapisana przed rachunkiem):** dla ceny bez przewidywalnego kierunku cel zysku nie zmienia wartości oczekiwanej
  (twierdzenie o zatrzymaniu martyngału) — zmienia tylko kształt wyników (dużo małych zysków, rzadsze duże straty); jeśli
  strategia ma przewagę, cel oddaje część przewagi z czasu po wyjściu, a dokłada koszt wyjść i ponownych wejść.

## Pre-rejestracja (zapisana przed obejrzeniem jakiegokolwiek wyniku)

- **Zmienna (jedna):** cel zysku na każdej pozycji fazy — wyjście, gdy dzienne maksimum (long) / minimum (short) sięga ceny
  wejścia × (1 ± cel); wypełnienie dokładnie po cenie celu (luka otwarcia ponad cel liczona po celu — na niekorzyść); koszt
  wyjścia 0,07 % nominału; do następnego formowania fazy kapitał stoi w gotówce (bez fundingu i odsetek); cel i likwidacja
  w tej samej świecy → likwidacja (kolejności w świecy dziennej nie znamy — wariant niekorzystny). Reszta reguł bez zmian.
- **„Większy wolumen”:** obie wersje sterowane zmiennością jak dziennik — reguła R1 na jednym szeregu (cel 20 %/rok, EWMA
  com 45, krok 7 dni, rozbieg 60, **sufit dźwigni 2 — zasada 5**). Porównanie przy równym ryzyku, nie przy równej wielkości.
- **Ramiona (4):** trend TS1 i premia Coinbase CP1 × cel 1 % / 2 %. **X1 poza rundą** — ustalone przed odczytem: silnik X1
  w dzienniku co dzień wyrównuje wartość nóg i nie ma likwidacji, więc cel na pojedynczej pozycji nie ma tam jednoznacznego
  odpowiednika; próba odwzorowania pozycjami dała szereg niezgodny z dziennikiem (korelacja 0,09) — zamiast zgadywać
  konstrukcję, X1 wyłączony (0 odczytów).
- **Miara:** dzienna różnica zwrotów netto (z celem − bez celu) przy równym ryzyku; średnia roczna z przedziałem; N_eff
  kanoniczne (≤ n). **Kryterium:** POZYTYWNY (cel lepszy) przy t_neff > z_4 = 2,498 (cztery ramiona naraz); NEGATYWNY przy
  t_neff < −1,96; inaczej NIEROZSTRZYGNIĘTY.
- **Mierzalność (zasada 18):** najmniejsza zmiana warta zmiany reguł dziennika = **5 pkt %/rok przy ryzyku 20 %/rok**
  (różnica Sharpe'a 0,25). Ramię MIERZALNE, gdy ± (z_4) < 5 pkt; inaczej średniej nie liczymy ani nie drukujemy.
- **Reguła STOP serii TP:** 1 runda. Inne cele, cele ruchome (trailing), częściowe wyjścia, stopy, ponowne wejście w tygodniu
  po celu — tylko nową decyzją użytkownika i nową pre-rejestracją.

## Wynik — rachunek mierzalności (`moc.txt`)

**Zgodność silnika:** bez celu nowy silnik daje dokładnie szereg dziennika (trend i premia: max |różnica| 0,00).

| noga | cel | pozycji | zamkniętych na celu | likwidacji (bez celu) | mnożnik k (mediana) z celem / bez | k na sufitcie 2 | korelacja wersji | sd różnicy | ± (z_4) | potrzeba danych | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trend TS1 | 1 % | 39 459 | 36 482 (92 %) | 158 (688) | 2,00 / 1,14 | 97 % dni | 0,55 | 18,3 %/rok | 19,6 pp | ~83 lat | NIEMIERZALNA |
| trend TS1 | 2 % | 39 459 | 33 819 (86 %) | 249 (688) | 2,00 / 1,14 | 97 % dni | 0,64 | 16,3 %/rok | 17,6 pp | ~67 lat | NIEMIERZALNA |
| premia CP1 | 1 % | 1 887 | 1 659 (88 %) | 4 (8) | 1,95 / 0,58 | 48 % dni | 0,60 | 18,2 %/rok | 20,1 pp | ~83 lat | NIEMIERZALNA |
| premia CP1 | 2 % | 1 887 | 1 470 (78 %) | 7 (8) | 1,23 / 0,58 | 9 % dni | 0,66 | 18,0 %/rok | 19,8 pp | ~80 lat | NIEMIERZALNA |

N_eff = n we wszystkich ramionach (różnica bez istotnej autokorelacji). Nawet bez korekty na cztery ramiona (± 1,96) szum
to ±13,8–15,7 pp — trzy razy więcej niż efekt, który miałby znaczenie.

## Co na plus (+) / Co na minus (−)

**(+)** pomysł użytkownika sprawdzony w 12 sekund bez jednego odczytu wyniku (licznik prób na historii 2021–2026 bez zmian);
silnik z celem odtwarza dziennik co do bitu (testy + `moc.txt`); liczby mechaniki potwierdzone niezależną drogą.

**(−)** runda nie mówi, czy cel zysku pomaga — mówi, że historia 5,4 roku nie może tego pokazać; próg 5 pkt %/rok to wybór
(przy progu 15 pkt ramiona dalej byłyby na granicy); dane dzienne nie pokazują kolejności ruchów w dniu — przyjęto
wariant niekorzystny (likwidacja przed celem); X1 nie zbadany.

**Kogo nie ma:** X1 (wyłączony — konstrukcja); ruchów wewnątrz dnia (tylko maksimum i minimum dnia); danych sprzed 2021
(zasada 20); kosztu kapitału czekającego w gotówce (bez odsetek — drobna korzyść dla wersji z celem).

## Wniosek

Czy zamykanie pozycji na +1–2 % i gra większą pozycją poprawia strategie dziennika, tego historia 2021–2026 nie rozstrzygnie.
Wersja z celem to niemal inna strategia: wychodzi z prawie każdej pozycji w ciągu tygodnia i żeby utrzymać to samo ryzyko,
musiałaby grać na maksymalnej dźwigni. Rozrzut różnicy (±18–20 pkt rocznie) jest kilka razy większy niż jakakolwiek
realistyczna poprawa. Teoria i poprzednie pomiary (N1, wnioski 70 i 72) wskazują raczej na pogorszenie, ale to jest
prior, nie wynik tej rundy.

## Rekomendacja

1. Reguły dziennika bez zmian — nie ma dowodu, który uzasadniałby zmianę, a teoria i precedensy mówią „raczej gorzej”.
2. Nie liczyć średnich tego porównania „dla ciekawości” — przy tym szumie każda liczba byłaby przypadkiem, a oglądanie jej
   zwiększa ryzyko wyboru reguły po wyniku.
3. Jeśli cel zysku miałby wrócić: na danych prospektywnych (dziennik) jako druga, papierowa wersja z tymi samymi sygnałami —
   decyzja użytkownika; odczyt dopiero, gdy rachunek mocy na nowych danych da MIERZALNA.

## Bramki jakości (CLAUDE.md zasada 16)

- **16a walidacja (`data:validate-data`): Ready.** Druga droga bez silnika z celem: pozycje premii Coinbase dotykające celu
  liczone wprost z dziennych maksimów/minimów 1 665 / 1 476 wobec 1 659 / 1 470 z silnika (różnica 6 = likwidacje przed celem
  i skrócone ostatnie okno); szum analitycznie σ·√(2(1−ρ)) przy σ 20 %/rok: ±18,2–20,4 pp wobec ±17,6–20,1 pp z silnika;
  silnik bez celu = dziennik co do bitu. Czerwona flaga „wynik idealnie potwierdza” — nie dotyczy (bez wyniku).
- **16b statystyka (`data:statistical-analysis`):** szum różnicy z symulowanych szeregów (nie z przybliżenia — wniosek 58),
  N_eff kanoniczne, korekta na 4 ramiona, przełożenie na potrzebną długość historii; precedens SC1.
- **16c przegląd diffu (`engineering:code-review`): Approve** — silnik z celem jako rozszerzenie silnika dziennika (ta sama
  pętla, nowe zdarzenie), wariant niekorzystny przy konflikcie w świecy, koszty wyjść i ponownych wejść w obrocie, brak
  fundingu po wyjściu; skrypt bez średnich (nie da się podejrzeć wyniku). Testy: równość z silnikiem dziennika (3 losowe
  przypadki), long i short na celu, koszt wyjścia, konflikt cel/likwidacja, brak likwidacji bez dźwigni, brak zaglądania
  w przyszłość.

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz tp1-cel-zysku`:

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → N1/SC1/KO1 → mierzalność przed startem → bramki → DoD |
| `anthropic-skills:clas5-quant` | cel zysku = zarządzanie pozycją (seria N: nie tworzy informacji); równe ryzyko; N_eff ≤ n; Bonferroni |
| `anthropic-skills:quant-strategy-catalog` | sekcja I katalogu: overlay to nie źródło przewagi; prior z twierdzenia o zatrzymaniu |
| `engineering:testing-strategy` | plan testów: równość z silnikiem dziennika co do bitu, przypadki brzegowe celu i likwidacji |
| `data:validate-data` | druga droga wprost z OHLC; szum analityczny; X1 wyłączony przed odczytem |
| `data:statistical-analysis` | szum różnicy z symulacji zamiast przybliżenia; przełożenie na lata danych |
| `engineering:code-review` | przegląd silnika, testów i skryptu — Approve |

Bez użycia: `dataviz` (tabela wystarcza), `data:explore-data` (dane znane z RU2/LQ1).
