---
id: 030
tytul: Hook audytowy — drugi tydzień obserwacji po poprawkach R1–R8 i dwóch blokadach; powtórka przeglądu
typ: przeglad
status: nowe
zlecil: uzytkownik
decyzja_uzytkownika: "2026-10-06: „Jak w rekomendacji” — po poprawkach drugi tydzień obserwacji i powtórka przeglądu tymi samymi komendami; zadanie 006 „Po drugim tygodniu”"
utworzono: 2026-10-06
zalezy_od: [029]
budzet: "Opus medium, krótko"
nie_wczesniej_niz: 2026-10-14
---

# 030 — Drugi tydzień obserwacji hooka audytowego

## Po co

Zadanie 029 poprawiło reguły hooka (R1–R8) i włączyło dwie wąskie blokady. Pierwszy tydzień miał 359 fałszywych
alarmów na 364 flagi. Drugi tydzień ma pokazać, ile flag zostaje po poprawkach i czy blokady komuś przeszkadzają.
Od jego wyniku zależą dalsze decyzje: kolejne blokady i start zadania 006 (osobny użytkownik systemu).

## Zakres

1. Okno: pełne dni 2026-10-07 … 2026-10-13 z `~/.clas5_audyt/`.
2. Te same komendy co w pierwszym przeglądzie: `docs/rag/13_tydzien_obserwacji.md`, sekcje 1–6 i sekcja
   „Po wdrożeniu R1–R8 (zadanie 029)”.
3. Każda odmowa (pole `zablokowano`): co zablokowano i czy słusznie. Fałszywa odmowa to pilna sprawa dla
   użytkownika, nie tylko liczba w raporcie.
4. Flagi według rodzaju i ocena każdej (prawdziwa / fałszywy alarm / niejasna), porównanie z pierwszym tygodniem.
5. Otwarte decyzje z pierwszego raportu:
   - `poswiadczenia` w Bash (po R2 i R3);
   - `zapis_poza_repo` tylko dla subagentów;
   - `siec_poza_lista` zostaje bez blokady, chyba że dane mówią inaczej.
6. Zasięg „Wszędzie”: odmowy na Windows, w Cowork i w chmurze nie trafiają do dziennika na serwerze. Zapytać
   użytkownika, czy widział tam odmowy hooka.
7. Znana luka `"$( … )"` w cudzysłowie (ADR-13, „Granica”; zadanie 029): czy naprawić ją zadaniem `naprawa`.
8. Raport z decyzjami dla użytkownika, w tym decyzją o starcie 006.

## Czego NIE robić

- Nie zmieniać hooka ani listy `blokuj:` (każda blokada to decyzja użytkownika).
- `~/.clas5_audyt` tylko czytać. Do repo nie trafia żadne surowe polecenie z dziennika (maskowanie jak w raporcie).

## Kryteria odbioru (dowody)

Komendy do powtórzenia każdej liczby, jedna liczba policzona drugą drogą, werdykt bramki 16a.

## Wynik

(dopisuje orkiestrator)
