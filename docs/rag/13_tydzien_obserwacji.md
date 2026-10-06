---
status: active
last_verified: 2026-10-06
depends_on: [13_izolacja_wykonawcow.md]
---

# 13 — Tydzień obserwacji hooka audytowego (2026-09-29 … 2026-10-05)

Zadanie 005 z tablicy (typ `przeglad`). To materiał do decyzji użytkownika z ADR-13, etap 2
([`13_izolacja_wykonawcow.md`](13_izolacja_wykonawcow.md)): czy hook audytowy ma zacząć **blokować**,
osobno dla każdej flagi. **Nic nie zostało włączone.** Hook dalej tylko oznacza. Poprawki reguł są tu
wyłącznie propozycjami.

> **Stan po 2026-10-06:** użytkownik zdecydował (karta 005), a zadanie 029 wdrożyło poprawki R1–R8 i dwie
> blokady. Sekcje 1–8 i „Decyzje dla użytkownika” opisują stan sprzed wdrożenia. Powtórka tygodnia nowymi
> regułami: sekcja 9.

Pojęcia użyte niżej:

- **hook** — mały program, który Claude Code uruchamia przed każdym użyciem narzędzia (Bash, Read, Write…).
  Nasz `tools/audyt_hook.py` dopisuje wtedy jeden wiersz do `~/.clas5_audyt/RRRR-MM-DD.jsonl`.
- **flaga** — etykieta „do uwagi” w wierszu, np. `siec_poza_lista` (połączenie z hostem spoza
  `config/audyt_hosty.yaml`).
- **blokada** — hook odmawia wykonania narzędzia. Claude widzi powód i może poprosić użytkownika o zgodę.
- **fałszywy alarm** — flaga na zwykłej, uzasadnionej pracy albo skutek błędu samego hooka.
- **subagent** — pomocnik uruchomiony przez sesję główną (np. wykonawca zadania z tablicy).
- **scratchpad** — prywatny katalog roboczy sesji: `/tmp/claude-…/<sesja>/scratchpad`.
- **heredoc** — tekst wklejony w polecenie powłoki: `cat > plik <<'EOF' … EOF`.

## Najważniejsze

1. W tygodniu było **2797 wywołań narzędzi**. **364 z nich (13 %) ma flagę.** Żadna nie pokazała
   nadużycia. W dzienniku nie ma odczytu kluczy, zapisu do dziennika audytu ani wysyłki danych do obcego
   hosta.
2. **4 flagi to prawdziwe zdarzenia**, ale zgodne z zadaniem: pomiar Hyperliquid w `~/likwidacje_hl/`
   (karty 001 i 004 każą trzymać te dane poza repo). **7 jest niejasnych**, bo dziennik ucina polecenia na
   300 znakach. **Pozostałe 359 to fałszywe alarmy.**
3. Większość fałszywych alarmów robi sam hook. Czyta tekst heredoka jak polecenia. Bierze „2” z `2>&1`
   (przekierowanie błędów) za nazwę zdalnego repo. Nie rozwija `$ZMIENNYCH`. Poprawki reguł R1–R6 (niżej)
   usuwają około 300 z 370 flag. R7 i R8 pozwalają blokować wąsko.
4. Reguła ADR-13 „blokuj tylko flagę z zerem fałszywych alarmów” przepuszcza dziś **tylko dwie wąskie
   blokady**: `poswiadczenia` w narzędziach plikowych i zapis do katalogu audytu. Obie dałyby w tygodniu
   0 odmów. Każda szersza blokada zatrzymałaby codzienną pracę.
5. Dane są przeciw ADR-13 w jednym punkcie: `siec_poza_lista` nie nadaje się na drugą blokadę.
   46 z 46 jej oznaczeń to przegląd literatury (zadanie 026).

**Werdykt bramki 16a: Caveats.** Liczby są pewne (dwie drogi, niżej). Ograniczenia: 643 polecenia ucięte,
tydzień nietypowy (57 % wierszy z dnia budowy hooka), brak danych z innych środowisk (sekcja 7).

## 1. Dane i ich jakość

- **Okno:** `~/.clas5_audyt/2026-09-29.jsonl` … `2026-10-05.jsonl`. Pliki są za 4 dni: 09-29 (1598 wierszy),
  09-30 (243), 10-01 (24), 10-05 (932). Pierwszy wiersz 09-29 06:38 UTC, ostatni 10-05 21:04 UTC.
- **10-02, 10-03, 10-04 to dni bez pracy sesji na serwerze, a nie dziura w zapisie.** W git (wszystkie
  gałęzie) od 10-01 07:13 do 10-05 17:20 są tylko commity automatów z crona (dziennik 02:42, tokeny 04:30)
  i jeden commit z sesji w chmurze (autor „Claude”, rejestr skilli, 10-03). Żaden plik zapisu rozmów
  Claude Code na serwerze nie zmienił się w te dni. W dni z pracą zmieniło się od 1 do 23 takich plików.
- **Plik `2026-10-06.jsonl` jest poza oknem.** Ten przegląd (subagent) czytał katalog audytu, więc dziś
  pojawią się tam flagi `dziennik_audytu`. To oczekiwane.
- **Profil zbioru:** 0 wierszy nieczytelnych, 0 flag `wejscie_nieczytelne`, 0 `blad_analizy`. Daty w
  wierszach zgadzają się z nazwami plików.
- **30 identycznych wierszy** (24 grupy). Wszystkie to Edit i żaden nie ma flagi. To osobne wywołania:
  dla Edit dziennik zapisuje tylko ścieżkę, więc kilka edycji jednego pliku w tej samej sekundzie wygląda
  tak samo.
- **643 z 2218 poleceń Bash (29 %) jest uciętych na 300 znakach.** Przy części flag przyczyny nie widać.
- **0 wierszy Grep, Glob, MultiEdit, NotebookEdit.** Sesje szukają przez `grep` i `find` w Bash.
- **Tydzień nie jest typowy.** 57 % wierszy pochodzi z 09-29, kiedy budowano sam hook (zadania 002, 003,
  027). 7 z 8 flag `poswiadczenia` to praca nad hookiem i kartami o izolacji.

## 2. Zestawienie (wersja a — tak, jak zapisał hook)

### Według flagi

| flaga | wierszy | % wszystkich wywołań | sesja główna | subagenci |
|---|---:|---:|---:|---:|
| `zapis_tmp` | 248 | 8,9 % | 7 | 241 |
| `siec_poza_lista` | 46 | 1,6 % | 0 | 46 |
| `siec_host_nieznany` | 39 | 1,4 % | 20 | 19 |
| `zapis_poza_repo` | 27 | 1,0 % | 22 | 5 |
| `poswiadczenia` | 8 | 0,3 % | 5 | 3 |
| `dziennik_audytu` | 2 | 0,1 % | 2 | 0 |
| `wejscie_nieczytelne`, `blad_analizy` | 0 | 0 % | 0 | 0 |
| **wiersze z co najmniej jedną flagą** | **364** | **13,0 %** | **52** | **312** |

Razem 370 flag w 364 wierszach (6 wierszy ma po dwie). Co z tego wynika: dwie trzecie flag to
`zapis_tmp`, czyli pliki robocze w scratchpadzie. Flagi „groźne z nazwy” (`poswiadczenia`,
`dziennik_audytu`) są rzadkie: 10 flag w 8 wierszach na tydzień.

### Według narzędzia

| narzędzie | wywołań | z flagą | % z flagą |
|---|---:|---:|---:|
| Bash | 2218 | 195 | 8,8 % |
| Edit | 244 | 8 | 3,3 % |
| Write | 163 | 117 | 71,8 % |
| Read | 128 | 0 | 0 % |
| WebFetch | 44 | 44 | 100 % |

Write ma często flagę, bo subagenci zapisują pliki robocze w scratchpadzie. Każdy WebFetch szedł do
serwisu spoza listy. Read nie dostał żadnej flagi.

### Sesja główna, subagenci, typ agenta

Sesja główna: 350 wywołań, 52 z flagą (14,9 %). Subagenci: 2447 wywołań (87 % całości), 312 z flagą
(12,8 %). Było ich 41, w 8 sesjach.

| typ agenta | wywołań | z flagą | % z flagą |
|---|---:|---:|---:|
| general-purpose | 2219 | 303 | 13,7 % |
| Explore | 140 | 1 | 0,7 % |
| fork | 42 | 2 | 4,8 % |
| wykonawca | 32 | 6 | 18,8 % |
| bez typu — sesja główna | 350 | 52 | 14,9 % |
| bez typu — subagent (14 agentów po 1 wywołaniu) | 14 | 0 | 0 % |

### Według sesji (litery zamiast identyfikatorów)

| sesja | od – do (UTC) | wywołań | główna | subagenci | agentów | z flagą |
|---|---|---:|---:|---:|---:|---:|
| A | 09-29 06:38 – 08:16 | 107 | 37 | 70 | 2 | 12 |
| B | 09-29 08:17 – 09:10 | 91 | 20 | 71 | 3 | 21 |
| C | 09-29 09:11 – 11:46 | 1234 | 70 | 1164 | 17 | 143 |
| D | 09-29 10:10 | 1 | 1 | 0 | 0 | 0 |
| E | 09-29 11:48 – 09-30 06:24 | 252 | 89 | 163 | 3 | 46 |
| F | 09-30 06:25 – 10-01 05:49 | 174 | 44 | 130 | 2 | 30 |
| G | 10-01 07:12 – 10-05 18:22 | 289 | 60 | 229 | 6 | 68 |
| H | 10-05 18:44 – 21:04 | 649 | 29 | 620 | 8 | 44 |

Wszystkie 46 flag `siec_poza_lista` pochodzą od jednego subagenta sesji G (10-05, 17:32–17:39).

## 3. Dwie wersje liczenia: (a) zapis, (b) obecne reguły z master

Hook zmieniał się 09-29. Uruchamia się plik z drzewa roboczego głównego checkoutu
(`$CLAUDE_PROJECT_DIR/tools/audyt_hook.py`). Reflog głównego checkoutu pokazuje, że od 09-29 08:07 był on
cały czas na `master` (tylko scalenia i `pull`). Lista hostów nie zmieniła się od 09-29 06:34.

| okres (09-29, UTC) | wersja hooka | wierszy | w tym uciętych |
|---|---|---:|---:|
| 06:38 – 06:52 | zadanie 002 (`a164a96`) | 44 | 10 |
| 06:52 – 06:57 | gałąź zadania 003 przed poprawką 16c (`43ce44f`) | 6 | 4 |
| 06:57 – 12:33 | zadanie 003 (`49bbc28`) | 1544 | 358 |
| od 12:33:49 do końca okna | zadanie 027 (`44d2257`, dzisiejszy master) | 1203 | 271 |

Zmiana 003 → 027 dotyczy tylko znaków, których system plików nie zakoduje (`_kodowalna`). W tygodniu było
0 wierszy `blad_analizy`, więc ta zmiana nie dotknęła żadnego wiersza.

**Wersja (b)** powstała offline. Każdy zapisany wiersz przeszedł przez `analizuj()` z dzisiejszego
`tools/audyt_hook.py` (`CLAS5_AUDYT_DIR` ustawione na katalog tymczasowy; nic nie zostało zapisane).
11 z 19 worktree z tygodnia już nie istnieje. Dla nich korzeń repo i `git remote get-url` są
odtworzone tak, jak wyglądały w dniu zapisu.

| flaga | (a) zapis | (b) obecne reguły na zapisanym tekście | **zablokowane przy obecnych regułach** |
|---|---:|---:|---:|
| `zapis_tmp` | 248 | 222 | **248** |
| `siec_poza_lista` | 46 | 46 | **46** |
| `siec_host_nieznany` | 39 | 28 | **37–39** |
| `zapis_poza_repo` | 27 | 24 | **27** |
| `poswiadczenia` | 8 | 0 | **6–8** |
| `dziennik_audytu` | 2 | 0 | **2** |
| wiersze z flagą | 364 | 316 | **361–364** |

Jak czytać tę tabelę:

- (b) różni się od (a) w **62 wierszach i wszystkie mają polecenie ucięte** na 300 znakach. Przyczyna flagi
  była dalej, a dziennik jej nie przechowuje. W **2154 wierszach z pełnym tekstem (b) = (a)**, także
  w 36 pełnych wierszach z najstarszych wersji. Zmiany hooka w tygodniu nie zmieniły więc ocen.
- Ostatnia kolumna to obecne reguły na **pełnym** poleceniu. Dla 2783 wierszy jest to wartość (a). 2154
  wiersze mają pełny tekst. 629 uciętych z okresu od 06:57 hook ocenił na żywo regułami równoważnymi
  z master.
- Niepewne jest 14 uciętych wierszy z 06:38–06:57 (starsza wersja hooka i brak końca polecenia). W 3 z nich
  (a) ≠ (b): 2 × `poswiadczenia`, 2 × `siec_host_nieznany`. Stąd przedziały.
- Bez odtworzenia usuniętych worktree różnic byłoby 80, czyli o 18 więcej (`git` w katalogu, którego już
  nie ma). To ten sam fragment z sekcji 8 bez linii `ah.katalogi_dozwolone, ah._url_zdalnego = kat, url`.

Co z tego wynika dla decyzji: liczbę odmów przy blokadzie daje ostatnia kolumna. Różnice wobec (a) są
małe (najwyżej 3 wiersze) i nie zmieniają żadnej rekomendacji.

## 4. Każdy oznaczony wiersz — grupa i ocena

Ocena: **P** = prawdziwy powód do uwagi, **F** = fałszywy alarm (codzienna praca albo błąd hooka),
**N** = niejasne. Przykłady są skrócone i zamaskowane (`~` = katalog domowy, `…` = pominięte).

| grupa | flaga | wierszy (główna / sub.) | ocena | przykład | poprawka |
|---|---|---|---|---|---|
| T1 własny scratchpad sesji | `zapis_tmp` | 248 (7 / 241) | F | `cat > /tmp/claude-…/<sesja>/scratchpad/czas.py <<'EOF'` | R5 |
| N1 WebFetch do serwisów z publikacjami | `siec_poza_lista` | 44 (0 / 44) | F (praca zlecona: przegląd literatury, zad. 026) | WebFetch `https://arxiv.org/abs/…` | lista bez zmian |
| N2 curl pobiera artykuł do scratchpadu | `siec_poza_lista` | 2 (0 / 2) | F (ten sam przegląd) | `curl -sL -A "Mozilla/5.0 …" …` (host `www.tandfonline.com`) | lista bez zmian |
| H1 `git push/pull/fetch` z `2>&1` bez nazwy zdalnego repo | `siec_host_nieznany` | 17 (14 / 3) | F (błąd hooka) | `git pull -q 2>&1 \| tail -2; …` | R1 |
| H2 `python -c` importuje bibliotekę sieciową bez połączenia | `siec_host_nieznany` | 6 (0 / 6) | F | `python -c "import websockets, requests; print(…)"` | — (informacja) |
| H3 heredoc Pythona edytuje plik, którego tekst wspomina `requests`/`socket` | `siec_host_nieznany` | 7 (3 / 4) | F (w 6 z 7 słowo stoi za 300 znakami) | `python3 - <<'EOF' ⏎ p='tools/audyt_hook.py' …` | — (heurystyka zostaje) |
| H4 linia `git push` w tekście notatki pisanej heredokiem | `siec_host_nieznany` | 1 (1 / 0) | F | `cat > $M/push-osobna-komenda.md <<'EOF' …` | R2 |
| H5 `cd $W`, potem `git fetch` | `siec_host_nieznany` | 1 (0 / 1) | F | `W=~/alpha/.claude/worktrees/agent-…; cd $W; git fetch -q origin` | R4 |
| H6 łańcuch `git add`/`git commit`, przyczyna za 300 znakami | `siec_host_nieznany` | 7 (2 / 5) | N (najpewniej H1) | `git add runs/skille/….jsonl && git commit -q -m "…" && git…` | R1 (prawdop.) |
| Z1 pamięć sesji: nota przekazania, MEMORY.md | `zapis_poza_repo` | 14 (14 / 0) | F (procedura z CLAUDE.md) | `cat >> ~/.claude/projects/…/memory/nota-przekazania.md <<'EOF'` | R6 |
| Z2 plik planu (tryb planowania Claude Code) | `zapis_poza_repo` | 5 (4 / 1) | F | Write `~/.claude/plans/<nazwa>.md` | R6 |
| Z3 pomiar LH0 w `~/likwidacje_hl/pomiar_krok1/` | `zapis_poza_repo` | 4 (1 / 3) | **P** (zgodne z kartami 001/004) | `cd ~/likwidacje_hl/pomiar_krok1 && setsid nohup ~/alpha/.venv/bin/python …` | — (ma być widoczne) |
| Z4 cel `$S/…` (to scratchpad), hook nie rozwinął `$S` | `zapis_poza_repo` | 3 (3 / 0) | F | `S=/tmp/claude-…/scratchpad; … cat > $S/merge017.txt <<'EOF'` | R4 (+R5) |
| Z5 `x > 0,` w kodzie Pythona w heredoku wzięte za zapis do pliku `0,` | `zapis_poza_repo` | 1 (0 / 1) | F | `.venv/bin/python - <<'EOF' ⏎ import glob, pandas as pd …` | R2 |
| P1 tekst karty zadania o hooku i izolacji wspomina `~/.ssh`, `~/.clas5_audyt` | `poswiadczenia` (3), `dziennik_audytu` (2) | 3 wiersze (3 / 0) | F | `cat > zadania/004-….md <<'EOF' ⏎ --- ⏎ id: 004 …` | R2 |
| P2 testy i edycja samego hooka, przykładowe wejścia z `~/.ssh/…` | `poswiadczenia` | 4 (1 / 3) | F | `for j in '{"tool_name":"Read","tool_input":{"file_path":"~/.ssh/…"}…'` | R2 + R3 (3 z 4) |
| P3 `sc.keys()` w kodzie Pythona wzięte za plik z „keys” w nazwie | `poswiadczenia` | 1 (1 / 0) | F | `python3 - <<'EOF' ⏎ … sc.keys() …` | R2 |

**Bilans (370 flag):** P = 4 (Z3), N = 7 (H6), F = 359. W wierszach: 4 P, 7 N, 353 F.

Dowód mechanizmu H1: wszystkie 17 poleceń `git push/pull/fetch` bez nazwy zdalnego repo, ale z `2>`, ma
flagę. Z 24 takich poleceń bez `2>` flagi nie ma 22. Pozostałe 2 dostały ją za inną część tego samego
polecenia. Tokenizer hooka zostawia „2” z `2>&1` jako osobne słowo. `_siec_git()` bierze je za nazwę
zdalnego repo, a `git remote get-url 2` kończy się błędem.

Grupa Z3 (prawdziwa) w szczegółach. Subagent sesji B (09-29 08:33) skopiował skrypt do
`~/likwidacje_hl/pomiar_krok1/`. Zapisał `start.sh` i uruchomił pomiar w tle (`setsid nohup`), więc
proces przeżył sesję. 10-05 sesja główna G zapisała tam wynik pomiaru. Karty 001/004 każą trzymać te
dane poza repo, więc to nie nadużycie. Właśnie takie działanie (proces w tle poza repo, start przez
subagenta) człowiek powinien jednak widzieć.

Przegląd wierszy **bez** flag pod kątem obejść, których hook nie oznacza. Było 13 odczytów
`.claude/settings*.json` i 6 razy `crontab -l`. Wszystko to odczyty. Nie było zmian ustawień, `base64`,
`/dev/tcp`, wysyłki danych przez `curl -d/-F/-T`, `ssh`/`scp`/`nc` ani `sudo`. Zapisów do katalogu audytu
i do plików z poświadczeniami: 0.

**Czerwona flaga „wynik idealnie potwierdza hipotezę”:** „0 nadużyć” może znaczyć „0 nadużyć widocznych dla
hooka”. Hook czyta tylko tekst polecenia (sekcja 7). To argument za etapem 3 ADR-13, nie przeciw temu
przeglądowi.

## 5. Propozycje poprawek reguł (nic nie wdrożone)

| id | co zmienić | gdzie w `tools/audyt_hook.py` | usuwa w tygodniu |
|---|---|---|---|
| R1 | Cyfra przyklejona do `>`/`<` (`2>&1`, `2>/dev/null`) to numer deskryptora, a nie słowo. W `git` pomijać słowa po przekierowaniu. | `segmenty()` (gałąź `elif c in "<>"`: bufor z samych cyfr tuż przed `>`/`<` odrzucić) oraz `_siec_git()` (`reszta` bez słów po `>`, `>>`, `<`) | H1: 17 (+ prawdop. H6: 7) |
| R2 | Treść heredoka to dane, nie polecenia: nie dzielić jej na segmenty i nie brać słów za ścieżki. Dla `python - <<…` zostaje tylko heurystyka bibliotek sieciowych. | `analizuj_bash()` przed `segmenty()` (wyciąć tekst od linii po `<<SŁOWO`/`<<'SŁOWO'`/`<<-SŁOWO` do linii końca); `siec_w_segmencie()` dalej dostaje pełny tekst (`cale`) | P1: 3 (+2 `dziennik_audytu`), P2: 2, P3: 1, H4: 1, Z5: 1 |
| R3 | Kod z `python -c '…'` to nie ścieżka. | pętla odczytów w `analizuj_bash()` (pominąć argument po `-c` dla Pythona) albo `_wyglada_na_sciezke()` (słowo z nową linią to nie ścieżka) | P2: 1 |
| R4 | `$NAZWA` z prostego przypisania w tym samym poleceniu (`S=/tmp/…; … > $S/x`) rozwijać jak `$HOME`. Nierozwinięte `$…` nie daje `zapis_poza_repo`. To samo dla `cd $W`. | `analizuj_bash()` (zapamiętać `NAZWA=wartość`) i `rozwin()` | Z4: 3, H5: 1 |
| R5 | Własny scratchpad sesji (`/tmp/claude-<uid>/<projekt>/<session_id>/scratchpad/`) bez flagi. Reszta `/tmp` dalej `zapis_tmp`. | `sprawdz_sciezke()` (potrzebny `session_id`, przekazać z `analizuj()`) | T1: 248 |
| R6 | Katalogi Claude Code: `~/.claude/plans/` bez flagi. `~/.claude/projects/<projekt>/memory/` bez flagi tylko w sesji głównej. Subagent piszący do pamięci zostaje oznaczony, bo pamięć wczytuje się do każdej przyszłej sesji. | `sprawdz_sciezke()` / `katalogi_dozwolone()` (potrzebny `agent_id`) | Z1: 14, Z2: 5 |
| R7 | Blokada zawężona do narzędzi: `blokuj:` musi umieć np. `poswiadczenia` tylko dla narzędzi plikowych albo `siec_poza_lista` tylko dla Bash. | wdrożenie etapu 2: `config/audyt_hosty.yaml` i `hook_main()`; flagi bez zmian | — (warunek decyzji 1) |
| R8 | Rozdzielić `dziennik_audytu` na odczyt i zapis (np. nowa flaga `dziennik_audytu_zapis`). | `sprawdz_sciezke()` (`zapis=True` daje flagę zapisu) | — (warunek decyzji 6) |

Szacunek skutku R1–R6. Każda grupa z sekcji 4 jest przypisana do poprawki, która ją usuwa. Zadanie
wdrażające musi to potwierdzić testami i powtórką tego przeglądu.

| flaga | teraz | po R1–R6 | co zostaje |
|---|---:|---:|---|
| `zapis_tmp` | 248 | 0 | — |
| `siec_poza_lista` | 46 | 46 | przegląd literatury |
| `siec_host_nieznany` | 39 | 13–20 | H2 (6), H3 (7); +7, jeśli H6 to nie błąd z R1 |
| `zapis_poza_repo` | 27 | 4 | Z3 — prawdziwe zapisy pomiaru LH0 |
| `poswiadczenia` | 8 | 1 | ręczny test hooka z `~/.ssh/…` w JSON-ie w poleceniu |
| `dziennik_audytu` | 2 | 0 | — |

Lista hostów: **bez zmian.** 27 hostów spoza listy to serwisy z publikacjami (`ideas.repec.org` 8,
`arxiv.org` 6, `www.tandfonline.com` 3, `www.nber.org` 3, … 20 hostów po jednym razie). Żaden nie jest
źródłem danych projektu. Dopisywanie ich nie nadąży za kolejnymi przeglądami literatury.

## 6. Propozycja dla każdej flagi

Dziennik papierowy i kolektory działają z crona, bez Claude Code. Żadna blokada ich nie dotknie. Dalej
chodzi o pracę sesji.

| flaga | odmów w tygodniu przy blokadzie | F / P / N | co z codziennej pracy by padło | propozycja |
|---|---:|---|---|---|
| `poswiadczenia` | 6–8 (Bash); 0 w narzędziach plikowych | 8 / 0 / 0 | ręczne testy hooka w Bash, karty zadań pisane przez `cat > … <<EOF`; pytest, git, kolektory — nic | **blokować teraz w narzędziach plikowych** (Read, Write, Edit, MultiEdit, NotebookEdit, Grep, Glob: 0 odmów na 535 wywołań); w Bash dalej oznaczać do R2+R3 |
| `siec_poza_lista` | 46 | 46 / 0 / 0 | cały przegląd literatury (zad. 026); git i pip — nic (0 takich wierszy; `git push/pull` idzie do `github.com` z listy) | **dalej tylko oznaczać** |
| `zapis_poza_repo` | 27 | 23 / 4 / 0 | nota przekazania i MEMORY.md (14), tryb planowania (5), start i odczyt pomiaru LH0 (4), zapisy przez `$S` do scratchpadu (3) | **dalej oznaczać; najpierw R2, R4, R6**; za tydzień rozważyć blokadę tylko dla subagentów |
| `zapis_tmp` | 248 | 248 / 0 / 0 | każdy zapis do scratchpadu (w tym 28 poleceń pytest i 13 ruff/black z wynikiem w scratchpadzie) | **nie blokować** (jak w ADR-13); R5 |
| `siec_host_nieznany` | 37–39 | 32 / 0 / 7 | 17+ zwykłych `git push/pull … 2>&1` (scalanie przez orkiestratora), sprawdzanie wersji bibliotek, edycje plików heredokiem | **nie blokować** (jak w ADR-13); R1, R2, R4 |
| `dziennik_audytu` | 2 | 2 / 0 / 0 | karty zadań pisane heredokiem; przy blokadzie odczytu także ten przegląd (subagent czyta katalog) | **R8, potem blokować tylko zapis** (0 zapisów w tygodniu) |
| `wejscie_nieczytelne`, `blad_analizy` | 0 | — | — | **nie blokować** (ADR-13: błąd hooka przepuszcza) |

Na co zwrócić uwagę w danych, gdy porównać je z ADR-13:

1. **Kolejność `poswiadczenia` → `siec_poza_lista` → `zapis_poza_repo`.** Druga pozycja nie pasuje do
   danych. `siec_poza_lista` ma najwięcej uzasadnionych wywołań: 46 od jednego subagenta w 8 minut,
   27 różnych hostów. Nawet zawężona do Bash (curl, wget, pip, git, ssh, python) dałaby 2 odmowy w
   tygodniu, obie przy tym samym przeglądzie, czyli też fałszywe. Uwaga do etapu 3: proxy z listą hostów
   zatrzyma pobieranie artykułów przez `curl`. Czy zatrzyma też WebFetch, zależy od tego, skąd łączy się
   Claude Code; to trzeba sprawdzić.
2. **„Nigdy `zapis_tmp`”.** Uzasadnienie z ADR-13 potwierdza się w pełni: 248 z 248 flag to własny
   scratchpad. Po R5 flaga byłaby w tygodniu pusta. Zalecenie „nie blokować” zostaje. Tydzień bez zdarzeń
   nie mówi, ile fałszywych alarmów dałaby blokada.
3. **„Zero fałszywych alarmów”.** Bez zawężenia (R7, R8) żadna z sześciu flag nie spełnia tej reguły.
   Spełniają ją tylko `poswiadczenia` w narzędziach plikowych i zapis do katalogu audytu.

## 7. Kogo nie ma w zbiorze

- **Automaty z crona na serwerze:** dziennik papierowy (`~/alpha-dziennik`), tokeny, kolektory likwidacji
  (`~/likwidacje*`). Nie idą przez Claude Code.
- **Inne środowiska:** Windows, Cowork, rutyny w chmurze (strona dziennika, strona tokenów). Jeśli wczytują
  `.claude/settings.json` z repo, hook pisze do ich własnego `~/.clas5_audyt`, którego tu nie ma.
  Lista `blokuj:` z repo zadziała tam bez obserwacji.
- **`claude -p` z crona albo sesje uruchomione poza katalogiem projektu**, a także sesje z wyłączonymi
  hookami. Brak hooka projektu. W tygodniu nie ma wierszy o porach crona.
- **Wnętrze programów:** sieć i zapisy z `python skrypt.py` (kolektory, pomiar LH0, pytest). Hook widzi
  tylko tekst polecenia.
- **Narzędzia spoza listy hooka:** WebSearch, Agent, Skill, Artifact i ArtifactData, narzędzia MCP. Nie
  zostawiają wiersza. Przegląd literatury mógł więc korzystać z sieci szerzej niż 46 widocznych wywołań.
- **Treść edycji:** Edit i Write zapisują tylko ścieżkę, nie zawartość.
- **Końcówki długich poleceń:** 643 polecenia ucięte na 300 znakach.

## 8. Jak powtórzyć

Wszystko uruchamia się z katalogu repo (`~/alpha`). Katalog audytu jest tylko czytany.

```bash
TYDZ() { cat ~/.clas5_audyt/2026-09-29.jsonl ~/.clas5_audyt/2026-09-30.jsonl \
             ~/.clas5_audyt/2026-10-01.jsonl ~/.clas5_audyt/2026-10-05.jsonl; }

# sekcja 1: pliki, wiersze na dzień, brak 10-02..10-04
ls ~/.clas5_audyt/; wc -l ~/.clas5_audyt/2026-09-29.jsonl ~/.clas5_audyt/2026-09-30.jsonl \
  ~/.clas5_audyt/2026-10-01.jsonl ~/.clas5_audyt/2026-10-05.jsonl            # 1598 243 24 932
git log --all --since=2026-10-01T07:13Z --until=2026-10-05T17:20Z --format='%ci %an %s'
for d in 2026-10-02 2026-10-03 2026-10-04; do find ~/.claude/projects -maxdepth 4 -name '*.jsonl' \
  -newermt "$d 00:00" ! -newermt "$d 23:59:59" | wc -l; done                  # 0 0 0
TYDZ | sort | uniq -c | awk '$1 > 1 {s += $1 - 1; g++} END {print g, s}'     # 24 grupy, 30 wierszy
TYDZ | sort | uniq -d | jq -r .narzedzie | sort | uniq -c                     # 24 Edit

# sekcja 2: zestawienie (a)
TYDZ | wc -l                                                                  # 2797
TYDZ | jq -c 'select(.flagi != [])' | wc -l                                   # 364
TYDZ | jq -r '.flagi[]' | sort | uniq -c | sort -rn                           # per flaga
TYDZ | jq -r '[.narzedzie, (.flagi != [])] | @tsv' | sort | uniq -c           # per narzędzie
TYDZ | jq -r '(if .agent then "subagent" else "główna" end) as $k | "\($k)\twszystkie",
  (select(.flagi != []) | "\($k)\toznaczone"), (.flagi[] | "\($k)\t\(.)")' | sort | uniq -c
TYDZ | jq -r '(.agent_typ // "-") as $t | "\($t)\twszystkie", (select(.flagi != []) | "\($t)\toznaczone")' \
  | sort | uniq -c
TYDZ | jq -r '[.sesja, (if .agent then "sub" else "gl" end), (.flagi != []), (.agent // ""), .czas[5:16]] | @tsv' \
  | awk -F'\t' '!($1 in L){L[$1]=sprintf("%c",65+n++); od[L[$1]]=$5} {s=L[$1]; w[s]++; do_[s]=$5;
    if($2=="gl")g[s]++; if($3=="true")f[s]++; if($4!="" && !((s SUBSEP $4) in A)){A[s SUBSEP $4]=1; a[s]++}}
    END{for(s in w) printf "%s %s..%s wywołań=%d główna=%d sub=%d agentów=%d z_flagą=%d\n",
    s, od[s], do_[s], w[s], g[s], w[s]-g[s], a[s], f[s]}' | sort                # tabela sesji A–H

# sekcja 3: wersje hooka, ucięte polecenia, wersja (b)
git log --format='%h %ci %s' -- tools/audyt_hook.py config/audyt_hosty.yaml   # hosty: tylko 09-29 06:34
git log master --merges --format='%h %ci %s' --since=2026-09-29T00:00Z --until=2026-09-30T00:00Z \
  | grep -E 'zadanie 00[23]|zadanie 026'                                      # 06:43, 06:57, 12:33
git reflog --date=iso | grep 'checkout:' | head -1   # stan 10-06: ostatnie przełączenie 09-29 08:07 (→ master)
TYDZ | jq -r '(.czas | if . < "2026-09-29T06:52:05Z" then "V1_002" elif . < "2026-09-29T06:57:06Z"
  then "V2_003_bez_16c" elif . < "2026-09-29T12:33:49Z" then "V3_003" else "V4_obecna" end)
  + "\tobcięte=" + ((.polecenie // "") | endswith("…") | tostring)' | sort | uniq -c
TYDZ | jq -r '.cwd | capture("(?<w>/\\.claude/worktrees/agent-[0-9a-f]+)").w // empty' | sort -u \
  | while read w; do [ -d ~/alpha"$w" ] && echo istnieje || echo usunięty; done | sort | uniq -c   # 8 / 11
CLAS5_AUDYT_DIR="$(mktemp -d)" .venv/bin/python - <<'EOF'
import collections, json, os, re, subprocess
from tools import audyt_hook as ah

G = os.path.expanduser("~/alpha")  # główny checkout (ścieżki w dzienniku wskazują na niego)
WT = re.compile("^(" + re.escape(G) + r"/\.claude/worktrees/agent-[0-9a-f]+)(/|$)")
ORIGIN = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
_kat = ah.katalogi_dozwolone


def kat(cwd):  # worktree usunięty po tygodniu: korzeń taki jak w dniu zapisu
    m = WT.match(os.path.realpath(cwd or ""))
    return [m.group(1), G + "/runs", G + "/data"] if m else _kat(cwd)


def url(k, nazwa):  # wspólny .git/config; katalogu, którego wtedy nie było (np. „$W”), git nie znajdzie
    k = os.path.realpath(k or ".")
    if not (os.path.isdir(k) or (WT.match(k) and "$" not in k)) or not k.startswith(G):
        return None
    return ORIGIN if nazwa == "origin" else None


ah.katalogi_dozwolone, ah._url_zdalnego = kat, url
H, KAT = ah.wczytaj_hosty(), os.path.realpath(os.path.expanduser("~/.clas5_audyt"))
a, b, rozne = collections.Counter(), collections.Counter(), collections.Counter()
for d in ("2026-09-29", "2026-09-30", "2026-10-01", "2026-10-05"):
    for linia in open(os.path.join(KAT, d + ".jsonl"), encoding="utf-8"):
        r = json.loads(linia)
        n, p = r["narzedzie"], r.get("polecenie") or ""
        ti = (
            {"command": p.removesuffix("…")}
            if n == "Bash"
            else {"url": r.get("url") or ""} if n == "WebFetch" else {"file_path": r.get("sciezka") or ""}
        )
        w, _ = ah.analizuj({"tool_name": n, "tool_input": ti, "cwd": r["cwd"]}, H, KAT)
        a.update(r["flagi"])
        b.update(w.flagi)
        if sorted(w.flagi) != r["flagi"]:
            stara = r["czas"] < "2026-09-29T06:57:06Z"  # wersje hooka sprzed zadania 003
            rozne[("obcięte" if p.endswith("…") else "pełne") + (" przed 06:57" if stara else "")] += 1
            if stara:
                print(r["czas"], "(a)", r["flagi"], "(b)", sorted(w.flagi))
print("(a)", sorted(a.items()))
print("(b)", sorted(b.items()))
print("wiersze z (a) != (b):", dict(rozne))
EOF
# wynik 2026-10-06: 3 wiersze sprzed 06:57 (2 × poswiadczenia, 2 × siec_host_nieznany tylko w (a));
# (b) siec_host_nieznany 28, siec_poza_lista 46, zapis_poza_repo 24, zapis_tmp 222;
# wiersze z (a) != (b): {'obcięte przed 06:57': 3, 'obcięte': 59}

# sekcja 4: grupy
TYDZ | jq -r 'select(any(.flagi[]; . == "zapis_tmp")) | .sesja as $s
  | [.sciezki_oznaczone[] | select(startswith("/tmp/") or startswith("/var/tmp/"))]
  | if length > 0 and all(test("^/tmp/claude-[0-9]+/[^/]+/" + $s + "/scratchpad(/|$)"))
    then "własny scratchpad sesji" else "inne" end' | sort | uniq -c            # 248 / 0
TYDZ | jq -r 'select(any(.flagi[]; . == "siec_poza_lista")) | [.narzedzie, .agent_typ, .agent, .czas[0:16]] | @tsv' \
  | sort | awk -F'\t' '{k=$1" "$2; c[k]++; ag[$3]=1; if(!(k in od))od[k]=$4; do_[k]=$4}
    END{for(k in c) print c[k], k, od[k]"…"do_[k]; print length(ag), "agent(ów)"}'   # 44 + 2, 1 agent
TYDZ | jq -r '.hosty_spoza_listy[]?' | sort | uniq -c | sort -rn                # 27 hostów
TYDZ | jq -r 'select(any(.flagi[]; . == "siec_host_nieznany")) | (.polecenie // "") as $p
  | (if .agent then "subagent" else "główna" end) as $k
  | (if ($p|test("git (push|pull|fetch)( -[^ ;&|]+)* [0-9]>")) then "H1"
     elif ($p|test("python[0-9.]* -c")) and ($p|test("requests|urllib|socket|httpx|aiohttp|websocket|ccxt")) then "H2"
     elif ($p|test("python[0-9.]* - <<")) then "H3" elif ($p|test("cd \\$")) then "H5"
     elif ($p|test("cat >>? [^ ]+ <<")) then "H4" else "H6" end) + "\t" + $k' | sort | uniq -c
TYDZ | jq -r 'select(any(.flagi[]; . == "zapis_poza_repo")) | ((.sciezki_oznaczone // []) | join(" ")) as $s
  | (if .agent then "subagent" else "główna" end) as $k
  | (if ($s|test("/\\.claude/projects/[^/]+/memory/")) then "Z1" elif ($s|test("/\\.claude/plans/")) then "Z2"
     elif ($s|test("/likwidacje_hl/")) then "Z3" elif ($s|test("\\$")) then "Z4" else "Z5" end) + "\t" + $k' \
  | sort | uniq -c
TYDZ | jq -r '.flagi[] as $f | select($f == "poswiadczenia" or $f == "dziennik_audytu") | (.polecenie // "") as $p
  | (if ($p|test("zadania/")) then "P1" elif ($p|test("audyt_hook|tool_name")) then "P2" else "P3" end)
  + "\t" + $f + "\t" + (if .agent then "subagent" else "główna" end)' | sort | uniq -c
# mechanizm H1: "z 2>" 17 × flaga=true; "bez 2>" 22 × false, 2 × true
TYDZ | jq -r '(.polecenie // "") as $p | select($p|test("git (push|pull|fetch)( -[^ ;&|]+)*( [0-9]>| *($|[;&|)]))"))
  | (if ($p|test("git (push|pull|fetch)( -[^ ;&|]+)* [0-9]>")) then "z 2>" else "bez 2>" end)
  + "\tflaga=" + (any(.flagi[]; . == "siec_host_nieznany") | tostring)' | sort | uniq -c
# zapisy do katalogu audytu i do plików z poświadczeniami: 0 i 0
TYDZ | jq -c 'select(any(.flagi[]; . == "dziennik_audytu") and any(.flagi[]; . == "zapis_poza_repo"))' | wc -l
TYDZ | jq -c 'select(any(.flagi[]; . == "poswiadczenia") and any(.flagi[]; . == "zapis_poza_repo" or . == "zapis_tmp"))' | wc -l
# obejścia w wierszach bez flag: 13 odczytów .claude/settings, 6 × crontab -l; reszta 0
TYDZ | jq -r '(.polecenie // .sciezka // .url // "") as $p | [("base64"|select($p|test("base64"))),
  ("/dev/tcp"|select($p|test("/dev/(tcp|udp)"))), ("curl wysyłka"|select($p|test("curl[^|;&]* (-d|--data|-F|--form|-T|--upload-file)( |=)"))),
  ("ssh/scp/nc"|select($p|test("(^|[;&| ])(ssh|scp|sftp|nc|ncat|telnet) "))), ("sudo"|select($p|test("(^|[;&| ])sudo "))),
  ("crontab"|select($p|test("crontab"))), (".claude/settings"|select($p|test("\\.claude/settings")))][]
  + "\t" + .narzedzie' | sort | uniq -c

# sekcja 6: codzienna praca a flagi (pytest 176 bez flagi + 28 zapis_tmp + 1 notatka w pamięci; skill_audit 30 bez flagi)
TYDZ | jq -r 'select(.narzedzie == "Bash") | (.polecenie // "") as $p | ([("pytest"|select($p|test("pytest"))),
  ("skill_audit"|select($p|test("skill_audit"))), ("git push/pull/fetch"|select($p|test("git (push|pull|fetch)"))),
  ("ruff/black"|select($p|test("ruff|black")))][]) + "\t" + (.flagi | join("+") | if . == "" then "-" else . end)' \
  | sort | uniq -c
TYDZ | jq -r 'select(.narzedzie == "Read" or .narzedzie == "Write" or .narzedzie == "Edit") | .flagi | index("poswiadczenia") != null' \
  | sort | uniq -c                                                            # 535 × false
```

**Druga droga (bramka 16a).** Liczbę wierszy z flagą i liczbę `siec_poza_lista` policzono dwa razy:
przez `jq` i przez Pythona z samą biblioteką standardową (bez kodu hooka).

```bash
TYDZ | jq -c 'select(.flagi != [])' | wc -l                                         # 364
TYDZ | jq -c 'select(any(.flagi[]; . == "siec_poza_lista"))' | wc -l                 # 46
python3 -c "import json,os; P=os.path.expanduser('~/.clas5_audyt/'); R=[json.loads(l) for d in ('2026-09-29','2026-09-30','2026-10-01','2026-10-05') for l in open(P+d+'.jsonl',encoding='utf-8')]; print('python: wywołań=%d oznaczone=%d siec_poza_lista=%d' % (len(R), sum(1 for r in R if r['flagi']), sum('siec_poza_lista' in r['flagi'] for r in R)))"
# python: wywołań=2797 oznaczone=364 siec_poza_lista=46
```

Wynik 2026-10-06: `jq` daje 364 i 46, Python daje 364 i 46. Liczby się zgadzają.

## Decyzje dla użytkownika

Poprawki R1–R6 i R8 niczego nie blokują. Mogą iść jako zadanie typu naprawa (z testami), a potem drugi
tydzień obserwacji i powtórka tego przeglądu tymi samymi komendami. Decyzji użytkownika wymaga każda
blokada.

1. **`poswiadczenia` — blokować teraz, ale tylko w narzędziach plikowych** (Read, Write, Edit, MultiEdit,
   NotebookEdit, Grep, Glob). W tygodniu: 0 odmów na 535 wywołań tych narzędzi i 0 fałszywych alarmów, więc
   reguła ADR-13 jest spełniona. Wymaga R7. Ryzyko: nowy plik z „key”, „secret” albo „token” w nazwie
   (np. `token_usage.json`) też zostałby zablokowany; w tygodniu nie było takiego. W Bash dalej tylko
   oznaczać: tam blokada dałaby 6–8 odmów na tydzień, wszystkie fałszywe. Po R2+R3 zostaje 1, wtedy
   decyzja za tydzień.
2. **`siec_poza_lista` — dalej tylko oznaczać.** Blokada dałaby 46 odmów na tydzień, czyli zatrzymałaby cały
   przegląd literatury (zad. 026). Prawdziwych zdarzeń: 0. Wariant ostrzejszy: blokować tylko sieć z Bash.
   To 2 odmowy w tygodniu, obie fałszywe (pobranie PDF w tym samym przeglądzie).
3. **`zapis_poza_repo` — dalej tylko oznaczać; najpierw R2, R4, R6.** Blokada dziś dałaby 27 odmów:
   nota przekazania i MEMORY.md (14), plany (5), pomiar LH0 (4), `$S` (3), `>` w Pythonie (1). Po poprawkach
   zostają 4 prawdziwe zapisy LH0. Wtedy rozważyć blokadę tylko dla subagentów: 3 odmowy na tydzień, start
   pomiaru LH0 za zgodą użytkownika.
4. **`zapis_tmp` — nie blokować (jak w ADR-13); wdrożyć R5.** 248 z 248 flag to własny scratchpad sesji.
   Po R5 w tygodniu byłoby 0 flag. Flaga pokazywałaby wtedy tylko zapisy do wspólnego `/tmp`.
5. **`siec_host_nieznany` — nie blokować (jak w ADR-13); wdrożyć R1, R2, R4.** Blokada dałaby 37–39 odmów,
   w tym 17 zwykłych `git push/pull … 2>&1`. Po poprawkach zostaje 13–20 flag informacyjnych.
6. **`dziennik_audytu` — wdrożyć R8, potem blokować tylko zapis do katalogu audytu.** W tygodniu było
   0 takich zapisów i 0 fałszywych alarmów. Odczyt dalej tylko oznaczać, bo przegląd tygodnia (to zadanie)
   czyta katalog. Blokada odczytu zatrzymałaby ten przegląd. Dwie flagi z tygodnia to tekst kart zadań;
   znikną po R2.
7. **`wejscie_nieczytelne` i `blad_analizy` — nie blokować.** 0 w tygodniu. ADR-13: błąd hooka przepuszcza.
8. **Lista hostów — bez zmian.** Żaden z 27 hostów spoza listy nie jest źródłem danych projektu
   (20 z nich pojawiło się tylko raz).
9. **Zasięg blokady — na razie tylko serwer.** `blokuj:` w repo zadziała w każdym środowisku, które
   wczytuje `.claude/settings.json` z repo (Windows, Cowork, rutyny w chmurze). Ich dzienników tu nie ma.
   Propozycja: hook blokuje tylko przy zmiennej środowiskowej ustawionej w ustawieniach użytkownika na
   serwerze, dopóki nie ma tygodnia danych z innych środowisk.

## 9. Po wdrożeniu R1–R8 (zadanie 029)

Użytkownik zdecydował 2026-10-06 (karta 005): dwie blokady („Obie”), zasięg „Wszędzie” (wbrew propozycji 9
wyżej), reszta jak w rekomendacji. Zadanie 029 wdrożyło poprawki R1–R8 i obie blokady. Opis zmian, format
listy `blokuj:` i wyjście odmowy: ADR-13, etap 2, „Wdrożenie 2026-10-06”
([`13_izolacja_wykonawcow.md`](13_izolacja_wykonawcow.md)). Tu jest powtórka tygodnia nowymi regułami.

**Jak liczono.** Te same zapisane wejścia co w sekcji 3, przepuszczone offline przez trzy zestawy reguł:

- **(a)** — flagi zapisane w dzienniku na żywo;
- **(b)** — reguły sprzed zadania 029 (hook z commita `44d2257`) na tekście z dziennika;
- **(c)** — nowe reguły (R1–R8) na tym samym tekście, z sesją i agentem z wiersza (potrzebne do R5 i R6).

Usunięte worktree są odtworzone jak w sekcji 8. Katalog audytu był tylko czytany. **Obcięte** = polecenie
ucięte w dzienniku na 300 znakach. W takich wierszach (b) i (c) widzą tylko początek polecenia, a hook na
żywo widzi całość.

### Tydzień 2026-09-29 … 10-05 (2797 wywołań)

| flaga | (a) zapis | (b) stare reguły | (c) nowe reguły | (c): pełne / obcięte | szacunek „po R1–R6” | (c) na pełnym tekście — ocena |
|---|---:|---:|---:|---|---|---|
| `zapis_tmp` | 248 | 222 | 33 | 0 / 33 | 0 | 0 (33 to cięcie w środku ścieżki scratchpadu) |
| `siec_poza_lista` | 46 | 46 | 46 | 45 / 1 | 46 | 46 |
| `siec_host_nieznany` | 39 | 28 | 9 | 3 / 6 | 13–20 | 13–20 |
| `zapis_poza_repo` | 27 | 24 | 9 | 2 / 7 | 4 | 4 (pomiar LH0) |
| `poswiadczenia` | 8 | 0 | 0 | 0 / 0 | 1 | 1 (w Bash, bez blokady) |
| `dziennik_audytu` | 2 | 0 | 0 | 0 / 0 | 0 | 0 |
| `dziennik_audytu_zapis` (nowa) | — | — | 0 | 0 / 0 | — | 0 |
| wiersze z flagą | 364 | 316 | 97 | 50 / 47 | — | — |

**Odmowy przy nowym `blokuj:`: 0** (oczekiwane 0). Co z tego wynika: w tym tygodniu żadna z dwóch blokad nie
zatrzymałaby pracy. Wiersze z flagą spadają z 364 do 97 na tekście z dziennika. Na żywo, bez skutków cięcia
(niżej), zostałoby około 64–71 wierszy: 46 z przeglądu literatury, 13–20 informacyjnych
`siec_host_nieznany`, 4 zapisy pomiaru LH0 i 1 ręczny test hooka.

Grupy z sekcji 4 w wersji (c):

| grupa | flaga | wierszy | zostaje w (c): pełne / obcięte | poprawka |
|---|---|---:|---|---|
| H1 `git … 2>&1` bez nazwy repo | `siec_host_nieznany` | 17 | 0 / 0 | R1 |
| H2 `python -c` z biblioteką sieciową | `siec_host_nieznany` | 6 | 3 / 3 | zostaje (informacja) |
| H3 heredoc Pythona z `requests`/`socket` | `siec_host_nieznany` | 7 | 0 / 1 | zostaje; 6 ma to słowo za cięciem |
| H4 `git push` w treści notatki | `siec_host_nieznany` | 1 | 0 / 0 | R2 |
| H5 `cd $W; git fetch` | `siec_host_nieznany` | 1 | 0 / 0 | R4 |
| H6 łańcuch `git add/commit` | `siec_host_nieznany` | 7 | 0 / 0 | przyczyna za cięciem (najpewniej R1) |
| N1, N2 przegląd literatury | `siec_poza_lista` | 46 | 45 / 1 | lista bez zmian |
| T1 własny scratchpad | `zapis_tmp` | 248 | 0 / 33 | R5 |
| Z1 pamięć sesji głównej | `zapis_poza_repo` | 14 | 0 / 0 | R6 |
| Z2 plany | `zapis_poza_repo` | 5 | 0 / 0 | R6 |
| Z3 pomiar LH0 (prawdziwe) | `zapis_poza_repo` | 4 | 2 / 2 | zostaje (ma być widoczne) |
| Z4 `$S/…` | `zapis_poza_repo` | 3 | 0 / 0 | R4 + R5 |
| Z5 `x > 0,` w heredoku | `zapis_poza_repo` | 1 | 0 / 0 | R2 |
| P1 karty zadań w heredoku | `poswiadczenia`, `dziennik_audytu` | 3 + 2 | 0 / 0 | R2 |
| P2 testy hooka | `poswiadczenia` | 4 | 0 / 0 | R2, R3 (1 zostaje na żywo, niżej) |
| P3 `sc.keys()` | `poswiadczenia` | 1 | 0 / 0 | R2 |

**Skąd różnice z szacunkiem raportu.** Szacunek z sekcji 5 był liczony na grupach z pełnego tekstu. Ta
powtórka liczy na tekście z dziennika. Różnice biorą się z cięcia na 300 znakach, nie z reguł:

1. **`zapis_tmp`: 33 zamiast 0.** Wszystkie 33 wiersze są obcięte i dziennik uciął je w środku ścieżki
   własnego scratchpadu (np. `> /tmp/claude-…/<sesja>/scr…`). Taki kawałek nie wygląda na scratchpad, więc
   dostaje flagę. Sprawdzone wiersz po wierszu: każda z 33 oznaczonych ścieżek to początek ścieżki
   scratchpadu tej samej sesji. W pełnych wierszach (c) daje 0. Hook na żywo widzi pełny tekst, więc: 0.
2. **`zapis_poza_repo`: 9 zamiast 4.** Cztery to Z3, czyli prawdziwe zapisy pomiaru LH0. Pięć pozostałych to
   też cięcie w środku celu zapisu: `2>/dev/null` ucięte do `2>/de`, `> /tm…`, ucięta druga ścieżka `cp`.
   Stare reguły (b) dają na tym samym tekście te same flagi, więc to nie skutek R1–R8. Na żywo: 4.
3. **`siec_host_nieznany`: 9 zamiast 13–20.** H2 zostaje cała (6), jak w szacunku. Z H3 widać tylko 1 z 7:
   w 6 wierszach słowo `requests`/`socket` stoi za 300 znakami, więc na tekście z dziennika heurystyka go
   nie widzi, a na żywo widzi (heurystyka bez zmian). H6 daje 0, bo przyczyna stoi za cięciem; z dziennika
   nie da się sprawdzić, czy to R1. Do tego 2 obcięte wiersze z flagą, którą dają też stare reguły (np.
   nazwa zdalnego repo ucięta do `ori`). Na żywo: 6 + 7 + 0…7 = 13–20, jak w szacunku.
4. **`poswiadczenia`: 0 zamiast 1.** Jedyny wiersz, który miał zostać (ręczny test hooka:
   `for j in '{…"~/.ssh/…"…}'`), ma tę ścieżkę za 300 znakami. Nowe reguły dalej oznaczają taki wiersz (test
   `test_r3_single_line_credential_paths_in_bash_are_flagged_not_denied`). Na żywo: 1, w Bash bez blokady.
5. **7 obciętych wierszy ma w (c) flagę, której nie ma zapis (a).** Wszystkie 7 mają ją też w (b). To skutek
   cięcia, nie nowych reguł.

### Dzień 2026-10-06 (poza oknem; plik dalej się pisze)

Pomiar 2026-10-06 o 08:50 UTC na kopii pierwszych **479 wierszy** pliku.

| flaga | (a) zapis | (b) stare reguły | (c) nowe reguły | (c): pełne / obcięte |
|---|---:|---:|---:|---|
| `dziennik_audytu` | 41 | 36 | 36 | 7 / 29 |
| `poswiadczenia` | 4 | 0 | 0 | 0 / 0 |
| `siec_host_nieznany` | 9 | 6 | 0 | 0 / 0 |
| `zapis_poza_repo` | 6 | 3 | 0 | 0 / 0 |
| `zapis_tmp` | 69 | 67 | 1 | 0 / 1 |
| `dziennik_audytu_zapis` (nowa) | — | — | 0 | 0 / 0 |
| wiersze z flagą | 118 | 109 | 37 | 7 / 30 |

**Odmowy: 0.** `dziennik_audytu` (36) to odczyty katalogu audytu: przegląd tygodnia (zadanie 005) i ta
powtórka (`cat`, `wc`, `ls`, kopia pliku do scratchpadu). Odczyt nie jest blokowany. `zapis_tmp` 1 — to samo
cięcie w ścieżce scratchpadu co w tygodniu. W 2 obciętych wierszach (c) daje flagę, której nie dają ani zapis,
ani stare reguły. To polecenia tej powtórki w postaci `A=~/.clas5_audyt; cat $A/…`: R4 rozwija `$A`, więc odczyt
dziennika schowany za zmienną jest teraz widoczny. To poprawne oznaczenie, nie fałszywy alarm.

### Druga droga (bramka 16a)

Liczbę odmów policzono drugi raz, bez kodu hooka: dwoma filtrami `jq` (niżej). Filtr 1 szuka narzędzi
plikowych ze ścieżką, która wygląda na plik z poświadczeniami (reguły nazw zapisane od nowa jako wyrażenie
regularne). Filtr 2 szuka zmiany katalogu audytu: Write/Edit/MultiEdit/NotebookEdit ze ścieżką w
`.clas5_audyt` albo Bash z operatorem zapisu lub poleceniem zmieniającym plik przed `.clas5_audyt` w tej samej
linii. Wynik: tydzień 0 i 0; dzień 2026-10-06 (479 wierszy) 0 i 0. Kontrola, że filtry nie są puste z
założenia: na sztucznych wierszach każdy łapie oba przypadki, które powinien (2 z 2). **Python z kodem hooka i
`jq` bez niego dają to samo: 0 odmów.**

Werdykt bramki 16a dla tej sekcji: **Caveats.** Liczba odmów jest pewna (dwie drogi). Ograniczenia: wiersze
obcięte (643 w tygodniu) dają tylko przybliżenie, które w tabeli wyżej jest rozbite na pełne i obcięte;
zachowanie na pełnym tekście potwierdzają testy z przykładami każdej grupy. Pomiar na żywo da drugi tydzień
obserwacji (odmowy: pole `zablokowano`).

### Jak powtórzyć

Z katalogu repo (`~/alpha`) po scaleniu zadania 029. Katalog audytu jest tylko czytany.

```bash
A=~/.clas5_audyt; T="$(mktemp -d)"
TYDZ_PLIKI="$A/2026-09-29.jsonl $A/2026-09-30.jsonl $A/2026-10-01.jsonl $A/2026-10-05.jsonl"
head -n 479 "$A/2026-10-06.jsonl" > "$T/2026-10-06-479.jsonl"   # dzień 10-06: stan z pomiaru

# (a), (b), (c), grupy, odmowy; drugi przebieg dla dnia: zamiast $TYDZ_PLIKI podaj "$T/2026-10-06-479.jsonl"
CLAS5_AUDYT_DIR="$T/audyt" .venv/bin/python - $TYDZ_PLIKI <<'EOF'
import collections, importlib.util, json, os, re, subprocess, sys, tempfile
from tools import audyt_hook as ah  # (c): reguły po zadaniu 029 (R1–R8) i lista `blokuj:`

kod = subprocess.run(["git", "show", "44d2257:tools/audyt_hook.py"], capture_output=True, text=True, check=True)
plik = os.path.join(tempfile.mkdtemp(), "audyt_hook_44d2257.py")
open(plik, "w", encoding="utf-8").write(kod.stdout)
spec = importlib.util.spec_from_file_location("stary", plik)
stary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stary)  # (b): reguły sprzed zadania 029

G = os.path.expanduser("~/alpha")
WT = re.compile("^(" + re.escape(G) + r"/\.claude/worktrees/agent-[0-9a-f]+)(/|$)")
ORIGIN = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()


def url(k, nazwa):  # jak w sekcji 8: worktree usunięty po tygodniu ma `origin` z dnia zapisu
    k = os.path.realpath(k or ".")
    if not (os.path.isdir(k) or (WT.match(k) and "$" not in k)) or not k.startswith(G):
        return None
    return ORIGIN if nazwa == "origin" else None


for m in (ah, stary):
    def kat(cwd, _k=m.katalogi_dozwolone):  # korzeń usuniętego worktree jak w dniu zapisu
        w = WT.match(os.path.realpath(cwd or ""))
        return [w.group(1), G + "/runs", G + "/data"] if w else _k(cwd)
    m.katalogi_dozwolone, m._url_zdalnego = kat, url
H, B = ah.wczytaj_hosty(), ah.wczytaj_blokady()
KAT = os.path.realpath(os.path.expanduser("~/.clas5_audyt"))


def dane(r):  # wejście hooka odtworzone z wiersza dziennika (polecenie bez „…” obcięcia)
    n, s = r["narzedzie"], r.get("sciezka") or ""
    ti = {"command": (r.get("polecenie") or "").removesuffix("…")} if n == "Bash" else (
        {"url": r.get("url") or ""} if n == "WebFetch" else {"notebook_path": s} if n == "NotebookEdit"
        else {"path": s, "pattern": "x"} if n == "Grep" else {"pattern": s} if n == "Glob" else {"file_path": s})
    return {"tool_name": n, "tool_input": ti, "cwd": r["cwd"], "session_id": r["sesja"], "agent_id": r["agent"]}


def grupa(r, f):  # grupy z sekcji 4 (te same reguły co filtry jq w sekcji 8)
    p, s = r.get("polecenie") or "", " ".join(r.get("sciezki_oznaczone") or [])
    if f == "zapis_tmp":
        return "T1"
    if f == "siec_poza_lista":
        return "N1" if r["narzedzie"] == "WebFetch" else "N2"
    if f == "siec_host_nieznany":
        if re.search(r"git (push|pull|fetch)( -[^ ;&|]+)* [0-9]>", p):
            return "H1"
        if re.search(r"python[0-9.]* -c", p) and re.search("requests|urllib|socket|httpx|aiohttp|websocket|ccxt", p):
            return "H2"
        return next((g for g, w in (("H3", r"python[0-9.]* - <<"), ("H5", r"cd \$"), ("H4", r"cat >>? [^ ]+ <<"))
                     if re.search(w, p)), "H6")
    if f == "zapis_poza_repo":
        return next((g for g, w in (("Z1", r"/\.claude/projects/[^/]+/memory/"), ("Z2", r"/\.claude/plans/"),
                                    ("Z3", "/likwidacje_hl/"), ("Z4", r"\$")) if re.search(w, s)), "Z5")
    return "P1" if "zadania/" in p else "P2" if re.search("audyt_hook|tool_name", p) else "P3"


a, b, c, pelne, obciete = (collections.Counter() for _ in range(5))
wiersze, odmowy, nowe, stub = collections.Counter(), [], collections.Counter(), 0
grupy = collections.defaultdict(lambda: [0, 0, 0])  # wierszy, w (c) zostaje: pełne, obcięte
for nazwa in sys.argv[1:]:
    for linia in open(nazwa, encoding="utf-8"):
        r = json.loads(linia)
        wiersze["wszystkie"] += 1
        if not r.get("narzedzie"):
            continue
        wb, _ = stary.analizuj(dane(r), H, KAT)
        wc, _ = ah.analizuj(dane(r), H, KAT)
        ob = (r.get("polecenie") or "").endswith("…")
        a.update(r["flagi"])
        b.update(wb.flagi)
        c.update(wc.flagi)
        (obciete if ob else pelne).update(wc.flagi)
        wiersze["(a)"] += bool(r["flagi"])
        wiersze["(b)"] += bool(wb.flagi)
        wiersze["(c) pełne" if not ob else "(c) obcięte"] += bool(wc.flagi)
        for f in r["flagi"]:
            g = grupy[grupa(r, f), f]
            g[0] += 1
            g[1 + ob] += f in wc.flagi
        for f in set(wc.flagi) - set(r["flagi"]):  # nowa flaga względem zapisu: czy stare reguły też?
            nowe["obcięte" if ob else "pełne", "też w (b)" if f in wb.flagi else "tylko (c)"] += 1
        wlasny = f"/tmp/claude-{os.getuid()}/-home-dantey1-alpha/{r['sesja']}/scratchpad"
        tmp = [p for p in wc.sciezki if p.startswith("/tmp/")]
        stub += ah.F_TMP in wc.flagi and ob and all(wlasny.startswith(p) for p in tmp)
        if z := ah.zablokowane_flagi(wc.flagi, r["narzedzie"], B):
            odmowy.append((r["czas"], r["narzedzie"], z))
print("wierszy:", wiersze["wszystkie"], " blokuj:", [(x.flaga, sorted(x.narzedzia or ["wszystkie"])) for x in B])
for f in sorted(set(a) | set(b) | set(c) | {ah.F_AUDYT_ZAPIS}):
    print(f"{f:22} (a) {a[f]:4} (b) {b[f]:4} (c) {c[f]:4}  (c) pełne/obcięte {pelne[f]}/{obciete[f]}")
print("wiersze z flagą:", dict(wiersze))
for (g, f), (n, zp, zo) in sorted(grupy.items()):
    print(f"grupa {g} {f:20} wierszy {n:4}  w (c) zostaje: pełne {zp}, obcięte {zo}")
print("zapis_tmp (c) ucięty w środku ścieżki własnego scratchpadu:", stub)
print("flagi nowe w (c) względem (a):", dict(nowe))
print("ODMOWY (c):", len(odmowy), odmowy)
EOF
# wynik 2026-10-06 (tydzień): zapis_tmp 248/222/33 (0/33), siec_poza_lista 46/46/46, siec_host_nieznany 39/28/9,
# zapis_poza_repo 27/24/9, poswiadczenia 8/0/0, dziennik_audytu 2/0/0, dziennik_audytu_zapis 0;
# wiersze z flagą 364/316/97; ucięte w ścieżce scratchpadu 33; nowe w (c): 7, wszystkie też w (b); ODMOWY 0
# wynik dla "$T/2026-10-06-479.jsonl": dziennik_audytu 41/36/36, poswiadczenia 4/0/0, siec_host_nieznany 9/6/0,
# zapis_poza_repo 6/3/0, zapis_tmp 69/67/1; wiersze z flagą 118/109/37; nowe w (c): 2 „tylko (c)”; ODMOWY 0

# druga droga: odmowy bez kodu hooka (jq)
cat > "$T/posw.jq" <<'JQ'
select(.narzedzie | IN("Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Grep", "Glob"))
| (.sciezka // "")
| select(test(
    "(^|[/\\\\])\\.(ssh|gnupg|aws|kube|docker)([/\\\\]|$)"
    + "|\\.config[/\\\\]gh"
    + "|(^|[/\\\\])(\\.git-credentials|\\.netrc|_netrc|\\.pgpass|\\.pypirc|\\.npmrc|credentials(\\.json|\\.ya?ml)?|authorized_keys|known_hosts)$"
    + "|(^|[/\\\\])\\.env(\\.[^/\\\\]*)?$|\\.env$"
    + "|\\.(pem|key|p12|pfx|keystore|jks|ppk|asc|gpg)$"
    + "|(^|[/\\\\])id_(rsa|ed25519|ecdsa)[^/\\\\]*$"
    + "|(^|[/\\\\._-])(api[_-]?)?(keys?|secrets?|tokens?|credentials?|passwords?)([._-][^/\\\\]*)?$";
    "i"))
JQ
cat > "$T/audyt.jq" <<'JQ'
select(
  ((.narzedzie | IN("Write", "Edit", "MultiEdit", "NotebookEdit")) and ((.sciezka // "") | contains("/.clas5_audyt")))
  or ((.narzedzie == "Bash") and ((.polecenie // "") | test(
        "(>>?|\\btee\\b|\\b(rm|mv|truncate|touch|chmod|chown|ln|shred|unlink|rmdir|dd)\\b)[^;&|\\n]*\\.clas5_audyt")))
)
| [.czas, .narzedzie] | @tsv
JQ
for P in "$TYDZ_PLIKI" "$T/2026-10-06-479.jsonl"; do
  cat $P | jq -r -f "$T/posw.jq" | wc -l      # 0
  cat $P | jq -r -f "$T/audyt.jq" | wc -l     # 0
done
printf '%s\n' '{"narzedzie":"Read","sciezka":"/x/.ssh/id_ed25519"}' '{"narzedzie":"Grep","sciezka":"C:\\Users\\x\\.aws"}' \
  '{"narzedzie":"Read","sciezka":"tools/zuzycie_tokenow.py"}' | jq -r -f "$T/posw.jq" | wc -l          # 2 (kontrola)
printf '%s\n' '{"narzedzie":"Write","sciezka":"/h/.clas5_audyt/a.jsonl"}' \
  '{"narzedzie":"Bash","polecenie":"echo x >> ~/.clas5_audyt/a.jsonl"}' \
  '{"narzedzie":"Bash","polecenie":"cat ~/.clas5_audyt/a.jsonl > x"}' | jq -r -f "$T/audyt.jq" | wc -l   # 2 (kontrola)
```
