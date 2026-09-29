# Tablica zadań CLAS-5

Jedno miejsce, z którego orkiestrator (Opus w sesji Claude Code na serwerze) bierze pracę. Uzgodnione z użytkownikiem
2026-09-29. Zakaz zapisu z sesji Cowork zdjęty **wyłącznie dla katalogu `zadania/`**.

## Role

- **Użytkownik** decyduje o wszystkim, co oznaczono „wymaga decyzji”. Uruchamia orkiestratora poleceniem
  „wykonaj zadania z tablicy” (na razie tylko ręcznie).
- **Cowork (Marian)** zapisuje nowe zadania i czyta wyniki. Pisze wyłącznie w `zadania/`, na `master`, poza oknem
  02:00–03:00 UTC (wtedy wypycha dziennik). Zmienia tylko pliki o statusie `nowe`.
- **Orkiestrator (Opus na serwerze)** czyta tablicę, dzieli zadania na kroki i zleca je wykonawcom. Przegląda wyniki,
  scala i zmienia statusy. Sam nie wykonuje ciężkiej pracy: kontekst ma zostać mały (lekcja z 28.09, `docs/rag/12`).
- **Wykonawcy** to subagenci. Każdy pracuje w osobnym worktree, na gałęzi `zadanie-NNN-<slug>`. Model dobiera się do
  pracy: Haiku lub Sonnet do mechaniki (kolektory, testy, pobieranie danych, formatowanie), Opus do metodologii
  (pre-rejestracja, rachunek mocy, werdykty).

## Plik zadania

Nazwa `NNN-<slug>.md`, numeracja rosnąca. Nagłówek według `SZABLON.md`. Statusy:

`nowe` → `w_toku` → `do_przegladu` → `zrobione`; poza tym `czeka_na_decyzje` i `odrzucone`.

Orkiestrator dopisuje na końcu pliku sekcję **Wynik**:

- co zrobiono;
- commity i gałęzie;
- gdzie są dowody;
- co zostało.

Nie usuwa treści zadania.

## Co orkiestrator może sam, a co wymaga decyzji użytkownika

| Typ zadania | Orkiestrator sam? |
|---|---|
| `infra`, `naprawa`, `testy`, `dokumentacja`, `przeglad` | tak, może też tworzyć podzadania tych typów |
| `zbieranie_danych` (kolektor, 0 wariantów, bez odczytu) | tak, jeśli zadanie ma zapisaną decyzję użytkownika |
| `badawcze`: nowa hipoteza, odczyt na danych, zmiana parametru, runda | **nie**: status `czeka_na_decyzje` |
| `dziennik`: każda Poprawka, zmiana pozycji lub progów | **nie** |
| `konto`: realne pieniądze, klucze, giełdy, Liquid/Bybit | **nie**, nigdy w roju |

Powód: pętla „wynik → nowe zadanie → wynik” to maszyna do przeszukiwania hipotez. Każde nowe badanie to kolejny
odczyt historii, a dowód wymaga już t ≈ 3,84 (wniosek 107, `runs/odczyty_historii.csv`).

## Zasady scalania: dowody, nie raporty

1. Scalamy tylko wtedy, gdy przechodzą testy, jest `raw_output.txt` albo log, powtarzalna komenda i hash commita.
   Każdą kluczową liczbę przelicza drugi, niezależny sposób (jak numpy 0,9996 w TX1).
2. Porażka jest porażką. Brak danych zgłaszamy jako „BRAK DANYCH”. Nie podmieniamy źródła, nie uzupełniamy
   i nie wymyślamy liczb. W raportach OpenAI z 17.09 modele robiły właśnie to: ukrywały błędy w streszczeniach
   i zmyślały dane przy nieudanym pobraniu.
3. Noty przekazania (strażnik kontekstu) sprawdzamy z `git log` i wynikami testów. Nie przyjmujemy ich na słowo.
4. Bramki jakości (`docs/skills/bramki-jakosci.md`) obowiązują tak samo jak bez tablicy.

## Izolacja wykonawców

Incydent OpenAI/Hugging Face z lipca 2026: agenci zrobili sobie kanał w zasobie, do którego mogli pisać.

- Wykonawca pisze tylko w swoim worktree i na swojej gałęzi. Jedynymi kanałami są tablica i gałąź.
- Bez dostępu do `~/.ssh` (w tym klucza `likwidacje_deploy` z prawem zapisu), kluczy API i danych giełd.
- Żadnych narzędzi handlowych (Liquid, Bybit) w pracy wykonawców.
- Sieć tylko do adresów wymienionych w zadaniu.
- Docelowo osobny użytkownik systemu i hook audytowy (zadanie 002).

## Koszt

Workflow i subagenci zjadły 43% tokenów w pomiarze z 28.09. Orkiestrator działa na żądanie, bez ciągłej pętli
i bez odpytywania. Zadanie może podać budżet w nagłówku.
