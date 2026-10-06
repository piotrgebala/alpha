---
id: 029
tytul: Hook audytowy — poprawki reguł R1–R8 i dwie wąskie blokady (decyzje użytkownika 2026-10-06)
typ: naprawa
status: zrobione
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

- **2026-10-06 (orkiestrator): scalone → `zrobione`.** Gałąź `zadanie-029-hook-poprawki-blokady` (`c0ae883`, `f160297`,
  `afbf0ef`), merge `33d798e`.
  - **Co działa od 2026-10-06:** R1–R8 i lista `blokuj:` (R7) z dwiema blokadami. Pierwsza: `poswiadczenia` w Read, Write,
    Edit, MultiEdit, NotebookEdit, Grep i Glob, tylko przypadki twarde (katalogi `.ssh`, `.gnupg`, `.aws`, `.kube`,
    `.docker` i katalogi nazwane jak poświadczenia, `~/.config/gh`, `.env`, `.env.local`, rozszerzenia kluczy, `id_rsa*`,
    pliki danych ze słowem key/token/secret w nazwie). Druga: `dziennik_audytu_zapis` we wszystkich narzędziach. Słowo
    key/token w plikach kodu, w bibliotekach, w dłuższej nazwie katalogu i w szablonach `.env.example` daje nową flagę
    `poswiadczenia_slabe`, która tylko oznacza. Wiersz dziennika ma pole `zablokowano`.
  - **Odstępstwa przyjęte w 16c:**
    - odmowa zostaje, gdy nie da się zapisać dziennika (inaczej zepsuty katalog audytu wyłączałby blokadę);
    - R8 liczy jako zapis także rm, mv, truncate, ln, chmod, touch, dd of= i find -delete;
    - `cd -` wraca do katalogu sprzed ostatniego `cd` w poleceniu.
  - **Dowody:**
    - pytest wykonawcy: 2656 passed, kod 0; pełny pytest na scalonym master (`OMP_NUM_THREADS=4`, kod wyjścia bez potoku): 2657 passed, 2 skipped, kod 0;
    - powtórka tygodnia (wykonawca, `docs/rag/13_tydzien_obserwacji.md`, sekcja „Po wdrożeniu R1–R8”): wierszy z flagą
      364 → 97, odmów 0 (tydzień) i 0 (10-06); druga droga wykonawcy (jq): 0 i 0;
    - druga droga orkiestratora: hook z gałęzi jako osobny proces na zapisanych wejściach, tydzień 2797 wierszy, 10-06
      679 wierszy: 0 odmów, wszystkie kody 0. Ta droga nie sprawdza blokady katalogu audytu, bo `CLAS5_AUDYT_DIR` przenosi
      też chroniony katalog. Wierszy z flagą wychodzi 116, a nie 97, bo 20 z 28 `siec_host_nieznany` pochodzi
      z usuniętych worktree (`cwd` już nie istnieje);
    - próby orkiestratora: 9 przypadków zgodnych. Jedna różnica: Grep po NIEISTNIEJĄCEJ ścieżce `…-tokens` dostaje odmowę,
      a istniejący katalog przechodzi. To bez skutku, bo Grep po nieistniejącej ścieżce i tak się nie uda;
    - na żywo po scaleniu: Read atrapy `api_key.txt` w scratchpadzie → odmowa z powodem i datą decyzji, w dzienniku
      wiersz z `zablokowano: [poswiadczenia]`; zwykły Read przechodzi.
  - **16c** (`engineering:code-review`, recenzent-subagent): dwa razy Approve with comments. Pierwszy przegląd: 7 uwag
    (fałszywe odmowy dla słowa key/token w plikach kodu i w `.venv`, `/.config/gh` dopasowywane jako podciąg, przybliżenia
    `cd` w Bash, Grep bez sprawdzania `glob`, utrata widoczności po R2–R4, host z portem wyłączał blokady, znak U+202A,
    kwadratowe `maskuj`: 80 KB w 25,7 s). Naprawione w `f160297`. Drugi przegląd: regresja (Grep po katalogu
    `secrets` lub `keys` bez odmowy). Naprawiona w `afbf0ef`.
  - **Zostało:**
    - luka `"$( … )"` w cudzysłowie: polecenie w środku nie dostaje flagi; była już przed 029; opisana w ADR-13
      („Granica”); decyzja w 030;
    - drugi tydzień obserwacji: [030](030-audyt-drugi-tydzien.md);
    - push na GitHub: polecenie użytkownika (tryb auto odrzucił push orkiestratora);
    - worktree wykonawcy zostaje do końca sesji.
