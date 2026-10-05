---
id: 025
tytul: Dziennik przy wstrzymaniu lub wycofaniu kontraktu — zamarzła cena ostatnia, brak rozliczenia likwidacji i zamknięcia
typ: dziennik
status: czeka_na_decyzje
zlecil: orkiestrator
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [017]
---

# 025 — Wycofanie kontraktu a rozliczenie w dzienniku

## Po co

LP1 (zadanie 017) pokazało, że przy wstrzymaniu lub wycofaniu kontraktu (FTT 2022-12, LUNA 2022-05, ALPACA 2025-05)
cena ostatnia zamarza, a cena mark dalej się zmienia. Według wykonawcy LP1 dziennik nie rozlicza wtedy ani likwidacji,
ani ceny zamknięcia (orkiestrator tego jeszcze nie sprawdzał na kodzie). Pozycja w wycofywanej monecie mogłaby zostać
w dzienniku z wynikiem niemożliwym do uzyskania. Użytkownik zgodził się 2026-09-29 dopisać to na tablicę („Wykonaj”);
zmiana dziennika wymaga osobnej decyzji.

## Zakres (po decyzji)

1. Sprawdzić na kodzie (`backtest/live_journal.py` i jego importy), co dziennik robi, gdy świece monety przestają się
   zmieniać albo znikają — bez oglądania wyników dziennika.
2. Opisać regułę rozliczenia (np. cena rozliczenia Binance przy wycofaniu, cena mark) i propozycję Poprawki N.

## Czego NIE robić

- Nie zmieniać kodu dziennika przed decyzją użytkownika i wpisem „Poprawka N” w `dziennik/README.md`.
- Nie zaglądać w wyniki dziennika (`dziennik/*.csv`); zob. 014.

## Kryteria odbioru (dowody)

- Opis zachowania dziennika z odnośnikami do kodu i testem na sztucznym przypadku zamarzniętej ceny.

## Wynik

- **2026-09-30, decyzja użytkownika: „25 zgoda”.** Krok 1 (przegląd kodu, bez zmian i bez wyników dziennika) zlecony wykonawcy razem z policzeniem, jak często moneta z koszyka top-20 była wstrzymana lub wycofana. Poprawka dziennika = osobna decyzja.
- **Krok 1 zrobiony 2026-09-30** (gałąź `zadanie-025-dziennik-wycofanie`, `8eca38a`; bez zmian kodu, bez wyników
  dziennika, 0 wariantów). Dowody: `zadania/025-dowody/przeglad.md`, `czestosc.txt`, `dowod_syntetyczny.txt` + skrypty.
  - Gdy świece się kończą: pozycja stoi po ostatniej cenie, zwrot 0, bez likwidacji i ceny rozliczenia, aż do
    przebudowy fazy (≤ 7 dni); moneta wypada z koszyka od następnego miesiąca; brak alarmu. Gdy cena zamarza: trend
    może otwierać pozycje po zamrożonej cenie (~28 dni), a zamrożona moneta może wejść do koszyka (FTT 2022-12,
    ALPACA 2025-05). Przebieg się nie wywraca (4 scenariusze sztuczne).
  - Ryzyko: małe dla R1 (wagi 0,15–2 % kapitału fazy), istotne dla X1 (10 % na monetę: rozliczenie −90 % ≈ −9 %
    kapitału X1, dziennik pokaże 0).
  - Częstość (koszyk top-20, 2021-02…2026-06, funkcja dziennika `monthly_members`): 6 zdarzeń na 1 300 par
    moneta-miesiąc = 0,46 %, Wilson 95 % [0,21; 1,00] % — w 5 z 65 miesięcy, ok. raz w roku (LUNA 2022-05, FTT 2022-12,
    BNX 2025-03, ALPACA 2025-05, EOS 2025-05, TON 2026-06). Druga droga wykonawcy (osobny ranking i liczenie serii):
    te same 6; orkiestrator przeliczył przedział ręcznym wzorem Wilsona: [0,2117; 1,0033] %.
  - BRAK DANYCH: historia statusów kontraktów Binance, oficjalna reguła ceny rozliczenia, miesiące 2026-07…09.
- **Czeka na decyzję użytkownika:** Poprawka N wg szkicu w `przeglad.md` (cena mark/oficjalna przy wycofaniu,
  likwidacja na cenie mark, brak nowych pozycji na zamrożonej cenie, dni bez obrotu nie liczą się do koszyka,
  alarm przy zniknięciu pliku).
