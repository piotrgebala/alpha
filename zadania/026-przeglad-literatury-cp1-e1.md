---
id: 026
tytul: Przegląd badań po publikacji — premia Coinbase (szczebel 1a drabiny) i wielkość efektu kaskad likwidacji (E1), 0 odczytów
typ: przeglad
status: do_przegladu
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

**Wykonawca, 2026-10-05 (gałąź `zadanie-026-przeglad-literatury-cp1-e1`):** raport
[`docs/przeglad_literatury_cp1_e1.md`](../docs/przeglad_literatury_cp1_e1.md); 0 odczytów, licznik E1 = 0.
- **CP1, szczebel 1(a): SŁABE (bez zmian).** Dla samego sygnału (premia Coinbase → BTC na tydzień) BRAK ŹRÓDŁA.
  Mechanizm pokrewny jest umiarkowany: napływy do ETF-ów → BTC (FalconX 2024: Granger p 0,004, szczyt +1,2 % po
  3–4 dniach; Mazur–Polyzos, JAI 2025) i premia GBTC → dzienny zwrot BTC (Huang i in., SSRN 2021: 40 pb dziennie;
  replikacja po publikacji SR −0,02). Przeciw: odkrywanie ceny na Binance (Cosenza–Stalder 2024), premie poruszają
  się razem ze wzrostami BTC (Makarov–Schoar, JFE 2020), BTC przewiduje premię USDT (Vo 2026).
- **1(b), tylko na papierze:** fundusze krajowe zamknięte w USA (36 lat, koszyk 20 funduszy → wykrywalny SR
  0,19–0,24 przy mocy 50 %). Dane płatne. Literatura raczej przeczy kierunkowi CP1.
- **E1 do karty 011:** 0,75 % brutto na epizod w 24 h (zakres 0–1,3 %; interpretacja, nie pomiar).
  Górna granica pochodzi z Miralles-Quirós (JAE 2022): +3,1 % po 24 h po spadku ≥ 5 % w godzinę (Kraken
  2016–2021), skorygowana × 0,42 (McLean–Pontiff, JF 2016). Dolna granica: momentum dzienne (Caporale–Plastun, FMPM
  2020). Środek leży poniżej progu wykrywalności po roku (0,9–1,3 %).
- **Dowody:** każdy link otwarty; przy kodzie 403 tytuł i autorzy potwierdzeni drugą stroną (kolumna
  „sprawdzenie”). Liczby z PDF-ów NBER/EIEF to cytaty z tekstu. Przeliczenia drugą drogą: 7,74/10,1 = 0,77;
  3,132 × 0,42 = 1,32. Bramka 16a: Caveats (liczby Miralles-Quirós tylko z indeksu wyszukiwarki; Lim
  niezweryfikowany).
