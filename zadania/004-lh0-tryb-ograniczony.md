---
id: 004
tytul: LH0 — tryb ograniczony: pomiar wag na dłuższym oknie, potem kolektor likwidacji Hyperliquid na kilku głównych monetach
typ: zbieranie_danych
status: w_toku
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: „Tryb ograniczony, bez kosztów: kolektor tylko na kilka głównych monet. Najpierw trzeba zmierzyć na dłuższym oknie, czy zmieści się w limicie.”"
utworzono: 2026-09-29
zalezy_od: [001]
budzet: "Opus medium do kodu i pomiaru, Opus do przeglądu i README"
---

# 004 — LH0 w trybie ograniczonym

## Po co

Sonda z zadania 001 (wniosek 110) pokazała, że Hyperliquid nie ma strumienia likwidacji. Każdą likwidację rynkową
da się rozpoznać: zlikwidowany jest stroną aktywną, a jego wypełnienie w `userFillsByTime` ma pole `liquidation`.
Kosztuje to jednak zapytania. Sama trójka BTC/ETH/SOL zużyła 1 243 wagi/min, a limit wynosi 1 200 wagi/min na IP.
Użytkownik wybrał tryb ograniczony, bez kosztów: tylko kilka głównych monet, a najpierw pomiar, czy to się zmieści.

## Zasady (jak w 001)

- 0 wariantów, poza licznikami, **bez odczytu E1**: nie zestawiamy likwidacji z cenami. Licznik E1 wspólny z LK0/LB0.
- Tylko `https://api.hyperliquid.xyz/info` i `wss://api.hyperliquid.xyz/ws`, bez kluczy, portfeli, zleceń i MCP Liquid.
  Nic płatnego.
- Wzór techniczny: LB0 (`DayWriter`, `status.json`, `kolektor.log`, `--status`, `--probe`, ping, strażnik ciszy,
  rosnące odczekanie). Dane poza repo, w `$HOME/likwidacje_hl/`.
- Działanie LK0 i LB0 bez zmian; `tests/test_likwidacje_sh.py` przechodzi.
- Katalog rundy: kontynuacja `runs/2026-09-29_lh0-kolektor-hyperliquid/` (sekcja „Krok 1 — tryb ograniczony”)
  albo nowy katalog z „Poprzedzającymi wynikami” → LH0 krok 0. [pre] / [implementacja] jak w LB0.

## Kroki

**A. Pomiar wag na dłuższym oknie (bez kolektora).**

- [pre] Zapisz przed pomiarem: zestawy monet (np. {BTC}, {BTC, ETH}, {BTC, ETH, SOL}), sposób odpytywania i próg.
  Próg: średnie zużycie ≤ 50 % limitu (600 wagi/min), bo reszta zostaje na zapas i na ewentualne 0b. Próg możesz
  uzasadnić inaczej, ale ZANIM zobaczysz wyniki.
- Okno ≥ 24 h, z porą azjatycką, europejską i amerykańską. Najlepiej także jeden okres większego ruchu (kaskada),
  bo wtedy stron aktywnych jest więcej.
- Sposoby ograniczania kosztu do zmierzenia:
  - odpytywanie tylko adresów, które przy transakcji były stroną aktywną z ruchem cenowym (zlecenie rynkowe kupujące
    płynność);
  - łączenie zapytań w obiegi co N minut z `startTime` (jedno zapytanie na adres na obieg);
  - pomijanie adresów, które w oknie już wiadomo, że nie mają pozycji.
  Każdy filtr sprawdź na danych, czy nie gubi likwidacji. Porównaj z pełnym odpytaniem na krótkim oknie.
- Wynik: waga/min (mediana, p95, maks.) per zestaw monet i per sposób; opóźnienie wykrycia; czy są błędy 429.
- **Jeśli żaden zestaw nie mieści się w progu:** STOP, raport do użytkownika.

**B. Kolektor** (`data/collect_liquidations_hl.py`), tylko na zestawie, który przeszedł A.

- Wiersz = jedna likwidacja: `T` (ms), `coin`, `pos` (kierunek zlikwidowanej pozycji), wielkość, cena, surowe pola,
  `ts`, `rcv`. Adres zlikwidowanego tylko do usuwania duplikatów, uzasadnić w README.
- Budżet wag pilnowany w kodzie: licznik wag i zwolnienie przy zbliżaniu się do limitu, zapis do `status.json`.
- Kontrola pozytywna ≥ 60 min w tym samym oknie co LK0 i LB0 (rząd wielkości, kierunek).

**C. Nadzór i kopia:** wpięcie w `tools/likwidacje.sh` (ta sama linia crona, własny `flock`, `WYLACZONY`, podwójny fork),
katalog w `data/liquidation_backup.py` i `data/liquidation_index.py`.

**D. Dokumentacja:** README z wynikami A i B, wiersz/aktualizacja w `runs/INDEX.md` (wniosek po 110), `STATUS.md`.

## Czego NIE robić

- Żadnego odczytu E1.
- Nie zbierać stanu pozycji (0b) ani stanu rynku co 60 s — to osobne decyzje, jeszcze niepodjęte.
- Nie przekraczać limitu API: przy błędach 429 zwolnić, nie obchodzić (bez wielu IP, proxy itp.).
- Nie zmieniać LK0 ani LB0 poza wspólnym nadzorem i kopią.

## Kryteria odbioru (dowody)

- `raw_output.txt` z pomiaru A; próg zapisany przed wynikiem.
- Testy bez sieci (w tym `hypothesis` tam, gdzie LB0 je ma), pełny `pytest` z kodem 0.
- `security-review` (nowe połączenie sieciowe) i `engineering:code-review`; `black`; rejestr skilli gałęzi.
- Kolektor działa pod nadzorem, `--status` pokazuje świeże dane.

## Wynik

(dopisuje orkiestrator)
