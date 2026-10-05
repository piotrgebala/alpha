---
id: 026
tytul: Przegląd badań po publikacji — premia Coinbase (szczebel 1a drabiny) i wielkość efektu kaskad likwidacji (E1), 0 odczytów
typ: przeglad
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „sprawdź co się kryje w nierozstrzygniętych hipotezach i czy możemy którąś z nich sprawdzić; jak tak, to dodaj nowe zadanie”"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, 1 wykonawca; sieć tylko do wyszukiwania publikacji (arXiv, SSRN, strony czasopism, NBER)"
---

# 026 — Przegląd badań: CP1 i E1

## Po co

Mapa 007 (`docs/mapa_hipotez_2026-10.md` §7) wypisuje „BRAK ŹRÓDŁA” przy każdej rodzinie i zaznacza, że nie
szukała w sieci. Dwie luki ważą dla decyzji o kapitale:

- **Premia Coinbase (CP1)** jest główną nogą dziennika papierowego. Ma szczebel 1(a) drabiny dowodów „słaby: praktyka
  rynkowa, brak badań” (`docs/rag/09`, tabela „Stan kandydatów”). Nikt tego nie sprawdził w literaturze. Jeśli badania
  istnieją, szczebel 1(a) się zmienia bez żadnego odczytu historii. Jeśli nie istnieją, zostaje to zapisane jako fakt.
- **E1 (kaskady likwidacji)** jest mierzalna po 1–3 latach tylko przy efekcie ≥ ok. 1 % na epizod (mapa 007 §5).
  Liczby efektu dla krypto: BRAK ŹRÓDŁA. Karta 011 powinna mieć zakładany efekt z publikacji, a nie z głowy.

To praca biurkowa: 0 odczytów historii, licznik DSR bez zmian.

## Zakres

1. **CP1, szczebel 1(a):** publikacje (recenzowane albo working papers) o premii/dyskoncie między giełdami
   (Coinbase vs Binance, „Kimchi premium”, segmentacja rynków, przepływy USD) i o tym, czy różnica cen **przewiduje
   zwrot BTC** w horyzoncie dni–tygodnia. Dla każdej: okres próby, rynek, wielkość efektu (SR, t, bps), czy efekt
   żyje **po** okresie próby, i czy sygnał jest ten sam co CP1 (premia → BTC na tydzień), czy tylko pokrewny
   (arbitraż, zbieżność premii).
2. **CP1, szczebel 1(b) — tylko propozycja:** czy istnieje niezależny od krypto rynek z tym samym mechanizmem
   (premia lokalnego popytu przewiduje cenę globalną, np. premie ADR, dyskonta funduszy zamkniętych, premia ETF do NAV).
   Opisać dane, długość, rachunek mocy **na papierze**. Bez pobierania danych i bez testu.
3. **E1:** publikacje o powrocie ceny po wymuszonej sprzedaży/likwidacjach (krypto i rynki tradycyjne): wielkość ruchu
   na epizod, horyzont, koszt, czy efekt przetrwał po publikacji. Wynik: przedział zakładanego efektu do karty 011.
4. Każde źródło: pełny cytat, link, i jedno zdanie, co dokładnie mierzy. Brak źródła = „BRAK ŹRÓDŁA”, nie domysł.

## Czego NIE robić

- Żadnego pobierania cen, żadnego backtestu, żadnego zestawienia premii ani likwidacji z cenami (to byłby odczyt).
- Nie zmieniać statusu CP1 w `docs/rag/09` ani w dzienniku — to decyzja użytkownika po lekturze raportu.
- Nie cytować liczb z pamięci modelu bez linku do źródła. Nie zmyślać autorów ani tytułów.
- Nie ruszać kodu dziennika.

## Kryteria odbioru (dowody)

- Plik `docs/przeglad_literatury_cp1_e1.md`: tabela źródeł (cytat, link, rynek, okres, efekt, po publikacji tak/nie,
  ten sam sygnał tak/nie), werdykt dla szczebla 1(a) CP1 (mocne / umiarkowane / słabe / brak) i przedział efektu dla E1.
- Każdy link sprawdzony (otwiera się, tytuł i autorzy się zgadzają) — druga droga zamiast przeliczenia liczby.
- Jednozdaniowy wpis w `STATUS.md` z linkiem; przy E1 — notka dla zadania 011 (zakładany efekt z przeglądu).
- Raport dla użytkownika 5–8 zdań prostym językiem: czy premia Coinbase ma oparcie w badaniach i co to zmienia
  przed odczytem dziennika ~2026-12-25.

## Wynik

(dopisuje orkiestrator)
