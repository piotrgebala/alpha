---
id: 029
tytul: Hook audytowy — poprawki reguł R1–R8 i dwie wąskie blokady (decyzje użytkownika 2026-10-06)
typ: naprawa
status: w_toku
zlecil: uzytkownik
decyzja_uzytkownika: "2026-10-06: blokady „Obie” (poswiadczenia w narzędziach plikowych, zapis do katalogu audytu); zasięg „Wszędzie”; pozostałe flagi „Jak w rekomendacji” (dalej oznaczać, poprawki R1–R6, lista hostów bez zmian, drugi tydzień obserwacji)"
utworzono: 2026-10-06
zalezy_od: [005]
budzet: "Opus, 1 wykonawca"
---

# 029 — Poprawki reguł hooka audytowego i dwie wąskie blokady

## Po co

Tydzień obserwacji (zadanie 005, `docs/rag/13_tydzien_obserwacji.md`) dał 364 flagi na 2797 wywołań. 359 z nich
to fałszywe alarmy, w większości z błędów samego hooka. Użytkownik zdecydował 2026-10-06: włączyć dwie blokady,
które w tygodniu dałyby 0 odmów, i to w każdym środowisku. Resztę flag hook dalej tylko oznacza, ale z poprawionymi
regułami.

## Zakres

1. Poprawki reguł R1–R6 z sekcji 5 raportu. Każda z testem „przed / po” na zamaskowanym przykładzie z tygodnia.
2. R7: lista `blokuj:` w `config/audyt_hosty.yaml` umie zawęzić flagę do wybranych narzędzi.
3. R8: osobna flaga zapisu do katalogu audytu (`dziennik_audytu_zapis`). Odczyt zostaje flagą `dziennik_audytu`.
4. Włączyć dwie blokady:
   - `poswiadczenia` tylko w Read, Write, Edit, MultiEdit, NotebookEdit, Grep i Glob. W Bash dalej tylko oznacza.
   - `dziennik_audytu_zapis` we wszystkich narzędziach.

   Wyjście odmowy jak w ADR-13, Etap 2, punkt 4. Blokada nie zależy od zmiennej środowiskowej. Działa wszędzie,
   gdzie działa hook (decyzja 9: „Wszędzie”).
5. Błąd hooka dalej przepuszcza wywołanie (fail-open).
6. Powtórka tygodnia nowymi regułami:
   - flagi według rodzaju, porównane z szacunkiem z raportu (tabela „po R1–R6”);
   - liczba odmów (oczekiwane 0);
   - na tygodniu 09-29…10-05 i osobno na 10-06.
7. Dokumentacja: ADR-13, Etap 2 (co wdrożono, data, decyzje), opis w nagłówku hooka i komentarz w
   `config/audyt_hosty.yaml`.

## Czego NIE robić

- Żadnych innych blokad. Lista hostów zostaje bez zmian.
- `~/.clas5_audyt` wolno tylko czytać. Powtórki idą z `CLAS5_AUDYT_DIR` ustawionym na katalog tymczasowy.
- Bez sieci, bez `~/.ssh`, bez kluczy.
- Bez zmian w `.claude/settings.json`. Rejestracja hooka zostaje taka, jak jest.

## Kryteria odbioru (dowody)

- Testy jednostkowe dla R1–R8 i dla obu blokad: dla każdej przypadek blokowany i nieblokowany, także ścieżki
  w stylu Windows.
- Test właściwości w `hypothesis`: pusta lista `blokuj:` nigdy nie blokuje; zepsute wejście nigdy nie blokuje.
- Powtórka tygodnia: komenda i liczby. Jedna liczba policzona drugą drogą.
- Pełny pytest na gałęzi (z `OMP_NUM_THREADS=4`); `ruff` i `black` na dotkniętych plikach.
- Po scaleniu sprawdza orkiestrator, na żywo: odczyt atrapy pliku z kluczem w scratchpadzie dostaje odmowę, a zwykły
  odczyt przechodzi.

## Ścieżka odwrotu

Wyczyścić listę `blokuj:` w `config/audyt_hosty.yaml` (jeden commit). Hook wraca wtedy do samego oznaczania.

## Wynik

(dopisuje orkiestrator)
