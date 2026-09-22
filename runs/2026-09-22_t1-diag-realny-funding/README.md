# T1-diag — czy realny funding w modelu kosztów cokolwiek zmienia (2026-09-22)

> **STATUS: ZAMKNIĘTA. Wynik: NIE ROBIMY TEGO — i premisa zadania była błędna.**
> Diagnostyka, nie eksperyment: zero zmian w kodzie produkcyjnym, zero spojrzeń na trafność.

## ID testu

**T1-diag** — diagnostyka poprawnościowa. **0 wariantów, POZA wszystkimi licznikami hipotez.**

## Metadane

- **Branch:** `task/T1-diag-realny-funding`
- **Komenda:** `py runs/2026-09-22_t1-diag-realny-funding/t1_sonda.py` (kopiowany do korzenia repo)
- **Populacja:** konfiguracja C2/balanced z K3 (bez bramki reżimu, po adopcji A1) — **8 033
  transakcje**, największa dostępna, więc efekt widać najwyraźniej.
- **Dane funding:** 7 457 rozliczeń, 2019-09-10 → 2026-06-30, odstęp 8h bez ani jednej dziury.

## Poprzedzające wyniki (zasada 14)

- **Zadanie T1** w `STATUS.md` (ETAP 3): *„Realny funding w modelu kosztów zamiast stałej
  `FUNDING_RATE_8H = 0.0001`. Mamy 7 457 rekordów od H2.0 i ich nie używamy. Zmierzony średni
  funding to −0,00243% (przychód!), a model zakłada +0,01% kosztu."*
- **H3** (`runs/2026-09-22_h3-noga-timeout-pasmo/`) — źródło liczby −0,00243%.
- **K3** — dostarczyło populację 8 033 transakcji i próg opłacalności 52,93%.
- **`backtest/costs.py:25`** — komentarz przy stałej: *„przybliżenie, brak jeszcze realnych
  danych funding"*. Dane są od H2.0, więc ta diagnostyka domyka też ten komentarz.

## Pytanie

Czy zastąpienie stałej realnymi stawkami zmienia próg opłacalności na tyle, żeby było warto
przebudować model kosztów?

Trzy modele policzone na **tej samej populacji transakcji**:

| wariant | jak liczy |
|---|---|
| **(0)** stała, ułamkowo | `0,0001 × (godziny/8)` — **model obecny** |
| **(1)** realne, ułamkowo | średnia realna stawka z okna trzymania × ułamek okresów |
| **(2)** realne, dyskretnie | **suma rozliczeń, które faktycznie wypadły w oknie** — tak działa giełda: funding pobiera się o 00/08/16 UTC, nie proporcjonalnie |

---

## Wynik

**Kontekst populacji:** średnie trzymanie 10,7 h (2,66 świecy); rozliczeń funding w oknie
średnio 1,33 (0 rozliczeń — 433 transakcje, 1 — 4 533, 2 — 3 067); **long 49,96%, short 50,04%**.

**Stawki:** stała w modelu `0,000100`; realna **średnia 0,000107** (+7,1%), realna **mediana
dokładnie 0,000100**.

### Funding jako ułamek nominału

| wariant | średnia | mediana | średnia z wartości bezwzględnej |
|---|---|---|---|
| (0) stała, ułamkowo *(model obecny)* | +0,00002% | −0,00500% | 0,01331% |
| (1) realne, ułamkowo | +0,00056% | +0,00025% | 0,01627% |
| (2) realne, dyskretnie *(poprawne)* | +0,00063% | 0,00000% | 0,01628% |

### Wpływ na próg opłacalności

Bariera średnia B = 1,3824% nominału.

| wariant | koszt C | break-even | **delta BE** |
|---|---|---|---|
| (0) stała, ułamkowo | 0,08108% | 52,933% | — |
| (1) realne, ułamkowo | 0,08161% | 52,952% | **+0,019 pp** |
| (2) realne, dyskretnie | 0,08168% | 52,954% | **+0,022 pp** |

**Przejście na model poprawny przesuwa próg opłacalności o +0,022 punktu procentowego.**

## Premisa zadania T1 jest BŁĘDEM KATEGORII

Zadanie mówi: *„zmierzony średni funding to −0,00243% (przychód!), a model zakłada +0,01%
kosztu"*. To zestawienie dwóch wielkości, które nie są porównywalne:

- **−0,00243%** to **signowany koszt per transakcja** — policzony **już z użyciem stałej
  0,0001** i z konkretną mieszanką kierunków. Nie jest to pomiar stawki. Na populacji tej
  diagnostyki ten sam rachunek daje **+0,00002%**; różnica wobec H3 bierze się wyłącznie
  z innej mieszanki long/short, nie z funding.
- **+0,01%** to **stawka za okres 8h**, nie koszt transakcji.

Ujemny znak w H3 nie znaczył, że funding jest przychodem „naprawdę" — znaczył, że w tamtej
populacji przeważały shorty, które przy dodatnim funding inkasują. Tutaj long/short jest
**49,96% / 50,04%**, więc signowany funding nettuje się niemal do zera **niezależnie od
tego, jakiej stawki użyjemy**. To jest właściwe wyjaśnienie, dlaczego zmiana stawki nic
nie daje.

## Co na plus (+) / Co na minus (−)

**(+) Stała 0,0001 okazała się trafna, i to nieprzypadkowo** — jest **dokładnie medianą**
realnego rozkładu stawek. Kto ją dobierał, dobrał dobrze.

**(+) Model ułamkowy okazał się dobrym przybliżeniem dyskretnego.** Różnica między (1) a (2)
to 0,003 pp progu — przy średnio 1,33 rozliczenia na transakcję ułamkowanie nie zdąży
zaszkodzić.

**(+) Zaoszczędzona przebudowa.** Wersja poprawna wymagałaby przeniesienia harmonogramu
funding przez cały silnik do `total_round_trip_cost` i przesunięcia baseline'u projektu
po raz kolejny — za +0,022 pp.

**(−) Kierunek jest odwrotny do sugerowanego w zadaniu.** Realny funding jest odrobinę
DROŻSZY niż stała (+7,1% na stawce), a nie tańszy. Poprzeczka opłacalności idzie o włos
w górę, nie w dół.

**(−) Zmierzono na jednej konfiguracji** (C2/balanced, 8 033 transakcje). C1 nie mierzono
osobno; przy efekcie rzędu 0,02 pp nie może to zmienić wniosku, ale formalnie jest to
ekstrapolacja.

**(−) Wniosek jest związany z mieszanką kierunków.** Gdyby przyszła strategia była
jednostronna (same longi albo same shorty), signowany funding przestałby się nettować
i stała mogłaby zacząć mieć znaczenie. **To jest warunek ważności tego wyniku, nie
przypis.**

## Walidacja (zasada 16a)

**Werdykt: READY.**

- **Kluczowa liczba drugą drogą:** stawka realna sprawdzona niezależnie od przebiegu —
  wprost z pliku funding (7 457 rekordów): średnia 0,00010705, mediana 0,00010000, odstęp
  między rozliczeniami 8h **we wszystkich 7 456 przypadkach** (zero dziur). Stała w modelu
  równa się medianie co do cyfry.
- **„Kogo NIE ma w zbiorze":** 433 transakcje z 8 033 (5,4%) mają **zero** rozliczeń funding
  w oknie — są za krótkie albo źle ułożone wobec siatki 00/08/16 UTC. W modelu ułamkowym
  płacą one funding mimo to, w dyskretnym nie płacą nic. To jedyna grupa, dla której oba
  modele różnią się jakościowo, a nie ilościowo — i jest zbyt mała, by ruszyć wynik.
- **Red flag „wynik potwierdza hipotezę": ODWROTNIE** — wynik **obala** zadanie, które go
  zamówiło, razem z jego uzasadnieniem. To nie jest wynik wygodny.

## Wniosek

Prostym językiem (zasada 17).

Model kosztów zakłada stałą opłatę za utrzymanie pozycji: **0,01% co 8 godzin**. Mamy realne
dane — 7 457 rzeczywistych rozliczeń z prawie siedmiu lat — i nigdy ich w tym miejscu nie
użyliśmy. Zadanie T1 mówiło, że to błąd wart naprawy.

**Sprawdziłem: nie jest.** Realna opłata wynosi średnio 0,0107% zamiast zakładanych 0,01%,
a jej **mediana to dokładnie 0,01%** — czyli stała została kiedyś dobrana trafnie. Po
przeliczeniu wszystkich 8 033 transakcji poprawnym modelem, w którym opłatę pobiera się
w rzeczywistych momentach rozliczeń, **próg opłacalności przesuwa się o 0,022 punktu
procentowego**. Dla porównania: dokładność naszego pomiaru to 1,09 punktu, a szukany efekt
ma 2,42 punktu. To jest zmiana pięćdziesiąt razy mniejsza od niepewności pomiaru.

**Uzasadnienie zadania było w dodatku pomyłką.** Liczba „−0,00243%", która miała dowodzić,
że funding jest przychodem, nie była pomiarem opłaty — była kosztem transakcji policzonym
**już z użyciem tej samej stałej**, tyle że dla próby, w której przeważały pozycje krótkie.
Pozycja krótka przy dodatniej opłacie ją inkasuje. Tutaj długie i krótkie są po połowie
(49,96% / 50,04%), więc opłata nettuje się niemal do zera — i to jest prawdziwy powód, dla
którego jej wysokość nie ma znaczenia.

## Rekomendacja

1. **Zadanie T1 zamknąć jako NIEZASADNE**, z zapisanym powodem — nie „zrobione", tylko
   „sprawdzone i niewarte zrobienia". Uzasadnienie w `STATUS.md` poprawić, bo zawiera błąd
   kategorii, który wprowadziłby w błąd każdego, kto po nie sięgnie.
2. **Zaktualizować komentarz przy `FUNDING_RATE_8H`** w `backtest/costs.py`: nie jest już
   prawdą, że „brak realnych danych". Dane są, przybliżenie zostało zweryfikowane, wpisać
   zmierzoną liczbę i link tutaj.
3. **Zapisać warunek ważności:** wniosek trzyma się na tym, że pozycje długie i krótkie są
   po połowie. **Strategia jednostronna unieważniłaby go** i wtedy realny funding trzeba by
   wprowadzić. Do odnotowania jako wyzwalacz, nie jako zadanie.
4. **Nie ruszać modelu kosztów.** Baseline projektu przesunął się w tej sesji raz (adopcja
   A1) i nie ma powodu robić tego drugi raz za 0,022 pp.
