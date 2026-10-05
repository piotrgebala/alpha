---
id: 015
tytul: Warstwa wykonania dla szczebla 4 — kontrole przed zleceniem, stany ryzyka i uzgadnianie z giełdą (wzorce nautilus_trader)
typ: konto
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: []
budzet: "Opus, główna sesja (nie w roju)"
nie_wczesniej_niz: 2026-12-01
---

# 015 — Warstwa wykonania dla szczebla 4

## Po co

Szczebel 4 drabiny dowodów (ADR-09) to mała realna kwota, najwyżej 5 % kapitału jako depozyt. Dziennik liczy dziś
sygnały tylko na papierze. Brakuje warstwy, która bezpiecznie zamieni sygnał na zlecenie. nautilus_trader ma
sprawdzony wzorzec takiej warstwy: silnik ryzyka i uzgadnianie stanu z giełdą. Źródło: przegląd bibliotek
z 2026-09-29 (użytkownik: „tak wrzuć na tablicę z zadaniami”). To zgoda na wpis na tablicę, nie na wykonanie.

## Zakres

**Krok A — bez kluczy i bez sieci (po decyzji użytkownika):**

- Przed pracą wczytać skill `anthropic-skills:zarzadzanie-pozycja` (sekcja E, tryb systemowy) i
  `engineering:architecture`.
- ADR w `docs/rag/`: jak sygnał z `dziennik/sygnaly.csv` staje się listą zleceń i gdzie mieszkają limity.
- Czyste funkcje z testami (`engineering:testing-strategy`):
  - **stany handlu:** aktywny / tylko zmniejszanie / wstrzymany. Wzorzec: `nautilus_trader/risk/engine.pyx`
    (TradingState, ok. l. 87–88 i 264–266);
  - **kontrola przed zleceniem:** limit nominału na zlecenie; limit depozytu łącznie z pozycjami ręcznymi
    (≤ 5 % kapitału); zlecenie tylko zmniejszające pozycję (reduce-only); sufit dźwigni przez jawne `min()` (zasada 5);
  - **ogranicznik liczby zleceń** na sekundę. Wzorzec: `nautilus_trader/risk/config.py` (domyślnie „100/00:00:01”);
  - **uzgadnianie:** pozycja oczekiwana wobec raportu giełdy po restarcie i okresowo. Rozbieżność przełącza stan na
    „wstrzymany”. Wzorzec: `nautilus_trader/live/reconciliation.py`, `nautilus_trader/live/config.py:177-201`;
  - **dziennik wykonania:** papier wobec rzeczywistości (cena, ilość, koszt, opóźnienie).

**Krok B — osobna decyzja użytkownika, dopiero po odczycie 014:** połączenie z giełdą, klucze API,
`security-review` jednorazowo w tym momencie (zasada 19).

## Czego NIE robić

- Nie importować nautilus_trader (zasada 8; licencja LGPL-3.0). Czytać wzorzec i pisać po swojemu.
- W kroku A: żadnych kluczy, zleceń ani połączeń sieciowych.
- Nie zmieniać kodu dziennika (`backtest/live_journal.py` i jego importów). Każda taka zmiana to Poprawka N i decyzja
  użytkownika.
- Nie zlecać wykonawcom z roju. Typ `konto` zostaje w głównej sesji (`zadania/README.md`).
- LLM nigdy w ścieżce decyzji (zasada 6).

## Kryteria odbioru (dowody)

- ADR w `docs/rag/` i wpis w `docs/INDEX.md`.
- Moduł z testami jednostkowymi i testami właściwości w `hypothesis`, co najmniej:
  - w stanie „tylko zmniejszanie” żadne wejście nie daje zlecenia, które zwiększa pozycję;
  - łączny depozyt (system + pozycje ręczne) nigdy nie przekracza limitu;
  - rozbieżność uzgadniania zawsze kończy się stanem „wstrzymany”.
- Przykładowy `sygnaly.csv` zamieniony na listę zleceń zgodną z ręcznym rachunkiem w README (druga droga).
- `py -m pytest -q` zielone, `ruff` i `black` na dotykanych plikach, hash commita.

## Wynik

- **2026-09-30, decyzja użytkownika: „15 czekamy do grudnia”.** Przed startem kroku A orkiestrator pyta jeszcze raz (typ `konto`).
