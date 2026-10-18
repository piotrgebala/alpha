---
id: 032
tytul: HT1 — czy wynik traderów Hyperliquid jest trwały (umiejętność czy przypadek); jeden odczyt na nowej bazie
typ: badawcze
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "2026-10-18: „dodaj Propozycja na tablicę wszystkie 3 opcje” — zgoda na wpis, nie na wykonanie"
utworzono: 2026-10-18
zalezy_od: [031]
budzet: "Opus (pre-rejestracja, werdykt) + 1 wykonawca; start dopiero przy werdykcie MIERZALNA"
---

# 032 — HT1: trwałość wyników traderów Hyperliquid

## Po co

Kopiowanie najlepszych z rankingu ma sens tylko wtedy, gdy wynik jest trwały, czyli najlepsi z przeszłości są lepsi
od reszty także później. Przy setkach traderów część wygląda na zdolnych czystym przypadkiem. Przy progu t > 1,96
około 2,5 % portfeli ma „istotny” zysk bez żadnej umiejętności.

Co mówią badania:
- Barber, Lee, Liu, Odean (2014, Tajwan 1992–2006): trwałość istnieje, ale przewidywalnie po opłatach zarabia mniej
  niż 1 % day traderów.
- Apesteguia i in. (*Management Science* 2020): możliwość kopiowania zwiększa ryzyko, bo ludzie kopiują najwyższe
  wyniki, a te biorą się zwykle z największego ryzyka.

Najbliższy wynik u nas to wniosek 90: reguła „za dużymi graczami” na Binance wyszła ujemna po kosztach. To zadanie
sprawdza samą umiejętność traderów. Kopiowania jeszcze nie testuje.

## Zakres

1. **Wejście z 031:** populacja z danych dostępnych danego dnia (point-in-time) i gęstość historii `portfolio`. Jeśli
   historia jest za rzadka albo zostali w niej tylko ocaleni, test idzie wyłącznie na danych zbieranych od startu
   kolektora.
2. **Pre-rejestracja przed obejrzeniem danych (zasady 1, 14, 18):**
   - **Hipoteza:** górne 10 % portfeli według wyniku skorygowanego o ryzyko (zysk ÷ zmienność dziennej wartości konta)
     z ostatnich 90 dni ma w kolejnych 30 dniach wyższy wynik skorygowany o ryzyko niż mediana populacji.
   - **Jedna statystyka:** średnia różnica „górne 10 % minus mediana” w kolejnych okresach, z t / t_neff i przedziałem.
   - **Populacja:** wybierana wyłącznie z danych sprzed startu okresu. Filtry z 031 (skarbce, animatorzy rynku,
     podkonta, minimalna wartość konta) zapisane z góry.
   - **Licznik:** nowa baza „HL-portfele” dostaje własny licznik wariantów (start 0) i próg t 1,96, a nie 3,84
     z historii Binance.
   - **Mierzalność:** `measurability_report` z liczby niezależnych okresów. Rok w okresach 30-dniowych daje tylko ~12
     obserwacji, więc test będzie prawdopodobnie NIEMIERZALNY. Inny horyzont wolno wybrać tylko na podstawie głębokości
     danych, przed obejrzeniem wyniku. **NIEMIERZALNA = runda nie startuje.** Wtedy do README wpisujemy najwcześniejszą
     datę odczytu z kolektora 031.
3. **Bramki 16a–c:**
   - pytanie „kogo NIE ma w zbiorze”;
   - czerwona flaga „wynik idealnie potwierdza hipotezę”;
   - kontrola negatywna A6: wyniki przetasowane między portfelami powinny dać ~0.
4. **Skarbce (vaults), tylko opis bez odczytu.** To gotowy produkt copy tradingu: lider dostaje 10 % zysku i musi mieć
   w skarbcu co najmniej 5 % kapitału. Jeśli 031 pokaże ich pełną historię, użytkownik zdecyduje, czy to druga
   populacja (osobny wariant, licznik +1).
5. **Dopiero przy wyniku dodatnim:** osobne zadanie na kopię z opóźnieniem 1 dnia (nasza cena, nasz koszt, checkpoint
   v2, korelacja z TS1 ≤ ~0,35). Nie w tym zadaniu.

Skille (zasada 19): `quant-strategy-catalog`, `clas5-quant`, `clas5-runda`, `data:statistical-analysis`,
`data:validate-data`, `engineering:code-review`. Gdy skill jest niedostępny: „niedostępny w sesji” i procedura z repo.

## Czego NIE robić

- Nie wybierać portfeli z dzisiejszego rankingu do testu wstecz. To przeciek z przyszłości, a w zbiorze zostają tylko
  ocaleni.
- Nie stroić okien 90/30 ani progu 10 % na danych (zasada 1). To ma być jeden wariant.
- Żadnego kopiowania, zleceń, kluczy ani MCP Liquid. Realne pieniądze tylko przez drabinę dowodów i zadanie typu `konto`.
- Nie łączyć z pozycjami traderów. To zakres zadania 033.

## Kryteria odbioru (dowody)

- Pre-rejestracja w commicie PRZED wynikiem (hash w README).
- Katalog `runs/…_ht1-trwalosc-hl/` z README (zasada 11) i `raw_output.txt`; wiersz w `runs/INDEX.md` z licznikiem
  bazy „HL-portfele”.
- Kluczowa liczba przeliczona drugą drogą (niezależny kod).
- Werdykt Ready / Caveats / Revision.

## Wynik

(dopisuje orkiestrator)
