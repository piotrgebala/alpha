---
status: active
last_verified: 2026-10-06
depends_on: [12_zuzycie_tokenow.md]
---

# 13 — Izolacja wykonawców: hook audytowy i plan osobnego użytkownika (2026-09-29)

Zadanie 002 z tablicy (`zadania/002-hook-audytowy-i-izolacja.md`), decyzja użytkownika 2026-09-29: kolejność
„tablica → izolacja → ewentualny harmonogram”. Ten dokument opisuje, co już działa (hook audytowy: oznacza
każde wywołanie, a od 2026-10-06 blokuje dwie wąskie rzeczy — etap 2), i planuje twardą granicę (osobny
użytkownik systemu). **Etap 3 nie jest wykonany**: każdy krok z `sudo` robi użytkownik, po decyzji.

## Po co

Wykonawca (subagent, który robi zadanie z tablicy) ma dziś te same prawa co użytkownik `dantey1`. Może
przeczytać klucz SSH `likwidacje_deploy` (z prawem zapisu do GitHuba), dane kolektorów, dowolny plik w domu,
i połączyć się z dowolnym adresem w internecie. Dwie lekcje z 2026 roku:

- incydent OpenAI/Hugging Face (lipiec): agenci zrobili sobie kanał w zasobie, do którego mogli pisać;
- raporty OpenAI z 17.09: przy przeszkodzie agenci szukają obejścia (publiczny serwis, zmyślone dane).

Zanim tablica zacznie działać bez nadzoru, potrzebujemy najpierw **widoczności** (co wykonawcy robią), potem
**granicy** (czego nie mogą zrobić, nawet gdyby chcieli).

## Decyzja (ADR-13)

**Status:** zaproponowana. Etap 1 wdrożony na gałęzi `zadanie-002-hook-audytowy`. Etap 2 wdrożony
2026-10-06 (zadanie 029, decyzje użytkownika z karty 005): dwie wąskie blokady, reszta flag dalej tylko
oznacza. Etap 3 czeka na decyzję użytkownika.

| etap | co | kto | kiedy |
|---|---|---|---|
| 1 | hook audytowy `tools/audyt_hook.py`: **tylko oznacza**, dziennik `~/.clas5_audyt/` | Claude (zrobione) | od scalenia |
| 2 | przegląd tygodnia dziennika → wybrane flagi zaczynają **blokować** | decyzja użytkownika, kod Claude (zrobione 2026-10-06: `poswiadczenia` w narzędziach plikowych, zapis do katalogu audytu) | po ≥ 7 dniach obserwacji |
| 3 | osobny użytkownik systemu `clas5wyk` + proxy z listą hostów + wspólne repo z bramką na gałęzie | ręce użytkownika (`sudo`) | po decyzji |

### Rozważone opcje

**A. Tylko hook (stan po etapie 1).** Prosty, bez `sudo`, działa dla głównej sesji i dla subagentów (hook
dostaje wtedy `agent_id`). Ale to analiza TEKSTU polecenia, nie granica. Polecenie
`bash -c "$(echo Y3VybCAuLi4= | base64 -d)"` przejdzie bez flagi. Hook daje widoczność, nie bezpieczeństwo.

**B. Piaskownica wbudowana w Claude Code** (`sandbox` w ustawieniach UŻYTKOWNIKA: bubblewrap, sieć przez
proxy z `allowedDomains`, `denyRead` dla `~/.ssh`). Nie wymaga nowego użytkownika i obejmuje subagentów
w tym samym procesie. Minusy: obejmuje tylko polecenia Bash — narzędzia Read, Grep i WebFetch działają
w procesie Claude poza piaskownicą (trzeba je domknąć regułami `permissions.deny`); kluczowe pola (np.
`strictAllowlist`) Claude Code czyta tylko z ustawień użytkownika, nie z repo; wymaga
`sudo apt install bubblewrap socat`. Dobra warstwa pośrednia, jeśli etap 3 się opóźni.

**C. Osobny użytkownik systemu (rekomendacja docelowa).** Granicę trzyma jądro systemu, a nie analiza tekstu:
użytkownik `clas5wyk` nie wejdzie do `/home/dantey1` (katalog ma już prawa `750`), więc nie przeczyta
`~/.ssh`, kluczy ani danych kolektorów `~/likwidacje*`. Sieć tylko przez lokalne proxy z listą hostów. Kod
wraca wyłącznie przez gałąź `zadanie-*` we wspólnym repo. Minus, który trzeba znać: **subagent działa
w procesie sesji głównej**, więc nie może mieć innego użytkownika systemu. Wykonawca staje się osobnym
procesem `claude -p` uruchamianym jako `clas5wyk` (skrypt-opakowanie + reguła `sudoers`). To zmiana modelu
orkiestracji (narzędzie Agent → skrypt) — osobne zadanie po decyzji. Wykonawca potrzebuje też własnego
logowania do Claude (konto użytkownika).

| wymiar | A: hook | B: piaskownica CC | C: osobny użytkownik |
|---|---|---|---|
| siła granicy | brak (widoczność) | średnia (tylko Bash) | wysoka (jądro) |
| `sudo` | nie | tak (pakiety) | tak (użytkownik, proxy, nft, sudoers) |
| zmiana orkiestracji | nie | nie | tak (`claude -p` jako `clas5wyk`) |
| koszt utrzymania | lista hostów | lista hostów + reguły deny | lista hostów + repo pośrednie |

**Konsekwencje.** Łatwiej: każda sesja zostawia ślad; przegląd tygodnia odpowie, czy wykonawcy w ogóle
próbują czegoś spoza zadania. Trudniej: lista hostów wymaga aktualizacji przy nowym źródle danych (commit
z powodem). Do powtórki po etapie 2: czy hook ma być fail-closed w trybie blokowania (2026-10-06: nie — patrz
„Wdrożenie 2026-10-06” w etapie 2).

## Etap 1 — hook audytowy (zrobione, tylko oznacza)

- **Kod:** `tools/audyt_hook.py`, wpięty w `.claude/settings.json` projektu jako `PreToolUse` dla Bash, Read,
  Write, Edit, MultiEdit, NotebookEdit, WebFetch, Grep i Glob. Wywołanie jak pozostałe hooki
  (`py … || python3 … || true`), więc działa na serwerze Linux, na Windows i w Cowork.
- **Dziennik:** `~/.clas5_audyt/RRRR-MM-DD.jsonl` (data UTC), katalog `0700`, plik `0600`, tworzone przez hook;
  otwarcie pliku z `O_NOFOLLOW` (dowiązanie symboliczne nie przekieruje zapisu). Zmienna `CLAS5_AUDYT_DIR`
  zmienia katalog (testy).
- **Jeden wiersz na wywołanie narzędzia**, także niepodejrzane (`"flagi": []`) — to ślad całej pracy.
  Pola: `czas`, `sesja`, `agent`, `agent_typ`, `cwd`, `narzedzie`, `polecenie` albo `sciezka` albo `url`,
  `flagi`, `hosty_spoza_listy`, `sciezki_oznaczone`.
- **Nie loguje treści plików** (pól `content`, `new_string` hook nie czyta) ani sekretów. Skrót polecenia
  ma maks. 300 znaków; przed obcięciem hook maskuje wzorce: `Authorization:`, `Bearer …`, `key=/token=/
  secret=/password=`, `--password …`, `user:hasło@` w adresie, tokeny GitHub/OpenAI/AWS/Slack oraz długie
  ciągi liter z cyframi (≥ 32 znaki: klucze, podpisy, hashe).
- **W etapie 1 nigdy nie blokował:** nic nie wypisywał na stdout (brak `permissionDecision`), zawsze kod 0,
  własny błąd połyka. Od etapu 2 (2026-10-06) wypisuje odmowę tylko dla flag z listy `blokuj:` (niżej,
  „Wdrożenie 2026-10-06”). Zły JSON na wejściu → wiersz z flagą `wejscie_nieczytelne` (zły JSON nie jest
  sposobem na zniknięcie z dziennika). Błąd analizy → wiersz z flagą `blad_analizy` i nazwą wyjątku. Oba
  przypadki nigdy nie blokują.
- **Szybkość:** tylko biblioteka standardowa, bez YAML. Pomiar na serwerze: mediana 22 ms, maks. 23 ms na
  wywołanie (11 wywołań, cały proces Pythona). `git remote get-url` (lokalnie, bez sieci) tylko dla
  `git push/fetch/pull` bez adresu w poleceniu.

### Flagi

| flaga | kiedy |
|---|---|
| `siec_poza_lista` | curl, wget, git push/fetch/pull/clone/ls-remote, pip install (także `python -m pip`, `uv pip`), python z `requests`/`urllib`/`socket`/`httpx`/`aiohttp`/`websockets`/`ccxt`…, nc, telnet, ssh, sftp, scp, rsync zdalny, WebFetch — do hosta spoza `config/audyt_hosty.yaml` |
| `siec_host_nieznany` | polecenie sieciowe, którego hosta nie widać w tekście (np. adres w zmiennej) |
| `zapis_poza_repo` | zapis poza dozwolonymi katalogami (niżej); od 2026-10-06 bez flagi `~/.claude/plans/` i — w sesji głównej — `~/.claude/projects/<projekt>/memory/` (R6) |
| `zapis_tmp` | zapis w `/tmp`, `/var/tmp`, `$TMPDIR`; od 2026-10-06 bez flagi własny scratchpad sesji (R5) |
| `poswiadczenia` | odczyt lub zapis: `.ssh`, `.gnupg`, `.aws`, `.kube`, `.docker`, `~/.config/gh` (składniki ścieżki), katalog o nazwie będącej CAŁYM słowem poświadczeń (`secrets`, `.secrets`, `keys`, `api_tokens`…), `.git-credentials`, `.netrc`, `.pgpass`, `.pypirc`, `.env`/`.env.*`/`*.env`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`/`id_ed25519*`, pliki DANYCH z członem `key(s)`/`secret(s)`/`token(s)`/`credential(s)`/`password(s)` w nazwie; w kodzie interpretera (`python - <<EOF`, `python -c`, `node -e`) podciąg ścieżki wrażliwej — **od 2026-10-06 blokowana w narzędziach plikowych** |
| `poswiadczenia_slabe` | od przeglądu 16c (2026-10-06): ten sam człon w nazwie pliku kodu lub dokumentacji (`.py`, `.md`, `.js`…), pliku w bibliotece (`site-packages`, `dist-packages`, `node_modules`, biblioteka standardowa), w dłuższej nazwie katalogu (`runs/…-tokens`), oraz szablony `.env.example`/`.sample`/`.template`/`.dist` — **tylko oznacza** (nie ma jej w `blokuj:`) |
| `dziennik_audytu` | narzędzie czyta katalog audytu (do 2026-10-06 także zapis — wtedy jedna flaga); także podciąg `.clas5_audyt` w kodzie interpretera |
| `dziennik_audytu_zapis` | od 2026-10-06 (R8): narzędzie zmienia katalog audytu — **blokowana we wszystkich narzędziach** |
| `wejscie_nieczytelne`, `blad_analizy` | hook nie zrozumiał wejścia albo analiza padła (nigdy nie blokuje) |

W Bash hook sprawdza „wrażliwe” tylko słowa wyglądające na ścieżkę (z `/`, `.` albo `~`), więc
`grep -rn api_key tools` nie jest oznaczane, a `cat .env` jest. Żaden plik z `git ls-files` nie dostaje flagi
`poswiadczenia` (pilnuje test).

### Rozstrzygnięcie: które zapisy są „poza”

Zadanie mówi: „zapisy poza bieżącym worktree i poza `runs/`/`data/`”. Hook rozstrzyga tak:

1. Korzeń = najbliższy katalog z `.git` w górę od `cwd` z wejścia hooka (dla wykonawcy: jego worktree;
   dla sesji głównej: `/home/dantey1/alpha`). **Zapis wewnątrz korzenia — bez flagi.**
2. Jeśli korzeń to worktree (plik `.git` wskazuje `<główne>/.git/worktrees/<nazwa>`), bez flagi są też
   `runs/` i `data/` **głównego checkoutu** — tam trafiają wspólne artefakty (np. rejestr skilli, cache
   danych). Kod głównego checkoutu (np. `/home/dantey1/alpha/tools/`) dla wykonawcy jest już „poza”.
3. `/dev/null`, `/dev/stdout` itp. — bez flagi.
4. `/tmp`, `/var/tmp`, `$TMPDIR` — osobna flaga `zapis_tmp`, nie `zapis_poza_repo`. `/tmp` jest wspólny
   dla wszystkich sesji, więc to potencjalny boczny kanał — ale leży tam też scratchpad każdej sesji Claude
   Code, więc flaga byłaby w prawie każdej sesji. Osobna nazwa pozwala ją przeglądać bez zagłuszania
   poważniejszych.
5. Wszystko inne — `zapis_poza_repo`.

Zapisy w Bash hook widzi tylko w prostych formach: przekierowanie `>`/`>>`, `tee`, cel `cp`/`mv`/`install`.
Zapis przez skrypt Pythona (`open(...).write`) nie jest widoczny — to granica analizy tekstu.

### Lista dozwolonych hostów (`config/audyt_hosty.yaml`)

Zebrana z kodu `data/` i `tools/` (grep adresów 2026-09-29) i z treści zadań:

| grupa | hosty |
|---|---|
| lokalnie | `localhost`, `127.0.0.1`, `::1` |
| Binance | `fapi.binance.com`, `dapi.binance.com`, `api.binance.com`, `fstream.binance.com`, `data.binance.vision`, `s3-ap-northeast-1.amazonaws.com` (listing archiwum) |
| Bybit | `api.bybit.com`, `stream.bybit.com` |
| Hyperliquid (zadanie 001) | `api.hyperliquid.xyz` |
| inne dane | `api.exchange.coinbase.com`, `api.upbit.com`, `www.deribit.com`, `community-api.coinmetrics.io`, `api.alternative.me`, `fred.stlouisfed.org` |
| kod i pakiety | `github.com`, `api.github.com`, `codeload.github.com`, `raw.githubusercontent.com`, `objects.githubusercontent.com`, `pypi.org`, `files.pythonhosted.org` |

Wpis `*.domena` obejmuje poddomeny (sama `domena` nie). Brak pliku = pusta lista, czyli każde polecenie
sieciowe dostaje flagę (bezpieczniejszy kierunek błędu). Nowe źródło danych = nowy wpis w tym samym commicie
co kod, z powodem.

### Przykład dziennika

`docs/rag/13_przyklad_audytu.jsonl` — 11 wierszy, 3 z flagą (2 × `siec_poza_lista` dla
`curl -sI https://example.com`, 1 × `zapis_tmp` dla pliku w scratchpadzie), 8 bez flag (`git status`,
`cat README.md`, odczyty i zapisy w worktree, pytest, grep). **Jawnie:** hook z `.claude/settings.json`
worktree nie był aktywny w sesji wykonawcy zadania 002 (sesja wczytała ustawienia głównego checkoutu
z `master`, a tam hooka jeszcze nie ma; `~/.clas5_audyt` nie istniał). Przykład powstał tak, że realne
wywołania narzędzi z tej sesji (te same polecenia i ścieżki, `curl` do example.com naprawdę wykonany
z odpowiedzią `HTTP/2 200`) podano jako JSON na wejście prawdziwego procesu hooka. Pole `agent` jest puste,
bo `agent_id` tej sesji nie był znany wykonawcy.

### Jak przeglądać dziennik

```bash
cat ~/.clas5_audyt/*.jsonl | jq -r '.flagi[]' | sort | uniq -c           # ile flag każdego rodzaju
cat ~/.clas5_audyt/*.jsonl | jq -c 'select(.flagi != [])'                # tylko oznaczone wiersze
cat ~/.clas5_audyt/*.jsonl | jq -r 'select(.agent) | .agent' | sort | uniq -c   # aktywność subagentów
cat ~/.clas5_audyt/*.jsonl | jq -r '.hosty_spoza_listy[]?' | sort | uniq -c    # hosty do oceny
```

## Etap 2 — z „oznacza” na „blokuje” (po tygodniu, decyzja użytkownika)

1. **Tydzień obserwacji** od scalenia etapu 1. Nic nie blokuje.
2. **Raport tygodnia** (Claude, wpis w `zadania/` jako typ `przeglad`): liczba wywołań, flagi według rodzaju,
   każda flaga z oceną „prawdziwa / fałszywy alarm”, hosty do dopisania lub odrzucenia. Pierwszy raport
   (tydzień 2026-09-29…10-05, zadanie 005, z listą decyzji dla każdej flagi):
   [`13_tydzien_obserwacji.md`](13_tydzien_obserwacji.md).
3. **Decyzja użytkownika dla KAŻDEJ flagi osobno.** Blokować tylko te z zerem fałszywych alarmów w tygodniu.
   Proponowana kolejność: `poswiadczenia` → `siec_poza_lista` → `zapis_poza_repo`. Nigdy nie blokować
   `zapis_tmp` ani `siec_host_nieznany` (za dużo niejednoznacznych przypadków).
4. **Wdrożenie:** w `config/audyt_hosty.yaml` sekcja `blokuj: [<flaga>, …]` (domyślnie pusta). Dla flagi z tej
   listy hook wypisuje `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
   "permissionDecisionReason": "<flaga>: <powód>; decyzja użytkownika <data>"}}`. Model widzi powód i może
   poprosić użytkownika o zgodę. Testy: przypadki blokowane i nieblokowane dla każdej flagi.
5. **Błąd hooka zostaje fail-open** (przepuszcza), bo hook nie może psuć sesji — twardą granicą jest etap 3,
   nie hook.

### Wdrożenie 2026-10-06 (zadanie 029)

**Decyzje użytkownika z 2026-10-06** (karta 005, po raporcie tygodnia):

- **Blokady „Obie”:** `poswiadczenia` tylko w narzędziach plikowych (Read, Write, Edit, MultiEdit, NotebookEdit,
  Grep, Glob; w Bash dalej tylko oznacza) oraz zapis do katalogu audytu (nowa flaga `dziennik_audytu_zapis`)
  we wszystkich narzędziach, łącznie z Bash.
- **Zasięg „Wszędzie”:** blokada zapisana w repo, bez zmiennej środowiskowej, która by ją włączała albo
  wyłączała. To decyzja **wbrew rekomendacji raportu** („na razie tylko serwer”, decyzja 9). Blokada działa
  w każdym środowisku, które wczytuje `.claude/settings.json` z repo: serwer Linux, Windows (`py`) i Cowork
  (`python3`). Z Windows i Cowork nie ma jeszcze dziennika, więc tam blokady ruszają bez tygodnia danych.
- **Reszta „Jak w rekomendacji”:** pozostałe flagi tylko oznaczają, poprawki R1–R6, lista hostów bez zmian,
  potem drugi tydzień obserwacji.

**Format `blokuj:` (R7)** w `config/audyt_hosty.yaml` — stan po wdrożeniu:

```yaml
blokuj:
  - flaga: poswiadczenia
    narzedzia: [Read, Write, Edit, MultiEdit, NotebookEdit, Grep, Glob]
    decyzja: "2026-10-06"
  - flaga: dziennik_audytu_zapis        # brak `narzedzia` = wszystkie narzędzia hooka
    decyzja: "2026-10-06"
```

- Wpis to nazwa flagi (blokada we wszystkich narzędziach hooka) albo mapa: `flaga` (wymagana), `narzedzia`
  (niepusta lista narzędzi, na które hook jest wpięty; wielkość liter ma znaczenie) i `decyzja` (data
  RRRR-MM-DD, trafia do powodu odmowy). Obie postacie mogą być w stylu blokowym albo `{…}` w jednej linii.
- **Zły wpis niczego nie blokuje, reszta działa:** nieznana flaga (także `wejscie_nieczytelne` i
  `blad_analizy` — błąd hooka nigdy nie blokuje), nieznane narzędzie, pusta lista, nieznany klucz (literówka
  `narzedzie:` nie rozszerza blokady na wszystkie narzędzia), zła data, zły typ.
- **Zepsuta sekcja nie blokuje niczego; reszta pliku nie ma wpływu.** Hook czyta bez biblioteki YAML
  (szybkość) tylko sekcję `blokuj:` — od linii `blokuj:` w kolumnie 0 do następnej linii z treścią w kolumnie 0.
  Błąd albo zapis spoza podzbioru w liście hostów (np. `- api.example.com:8080`) nie wyłącza więc blokad
  (przegląd 16c). Podzbiór: mapy i listy blokowe, `[a, b]` i `{klucz: wartość}` w jednej linii, skalary zwykłe
  i w cudzysłowie, komentarze. Sekcja zepsuta albo spoza podzbioru (tabulator, wartość w kilku liniach,
  kotwice, powtórzony klucz), brak sekcji albo dwie sekcje → żadnej blokady. Test właściwości z PyYAML pilnuje
  dwóch rzeczy: hook nigdy nie blokuje więcej, niż wynika z odczytu sekcji przez PyYAML (gdy PyYAML pada —
  nic), a sekcję z podzbioru czyta dokładnie tak jak PyYAML.
- Zmienna `CLAS5_AUDYT_HOSTY` zmienia tylko listę hostów (testy), nigdy `blokuj:`.

**Wyjście odmowy.** Format z punktu 4 sprawdzony 2026-10-06 w skillu `update-config` (opis hooków Claude Code):
aktualny, bez zmian — `hookSpecificOutput.permissionDecision: "deny"` z `permissionDecisionReason`, kod
wyjścia 0. JSON idzie w samym ASCII (polskie litery jako sekwencje ucieczki JSON), żeby stdout w cp1252 na
Windows nie wywrócił decyzji.
Powód: `<flaga>: <opis> (<ścieżka zamaskowana jak w dzienniku>) w narzędziu <X> — blokada hooka audytowego
(config/audyt_hosty.yaml, ADR-13); decyzja użytkownika 2026-10-06`. Bez treści pliku. Kilka blokad w jednym
wywołaniu → jedna decyzja, powody rozdzielone ` | `. Wiersz dziennika dostaje pole `zablokowano` (lista
flag); odmowy drugiego tygodnia: `cat ~/.clas5_audyt/*.jsonl | jq -c 'select(.zablokowano)'`.

**Fail-open w szczegółach (punkt 5).** Zły JSON, brak albo zepsuty plik konfiguracji, wyjątek w analizie
albo w liczeniu decyzji → brak odmowy, kod 0, wiersz z `wejscie_nieczytelne` albo `blad_analizy`. Jedna
świadoma różnica: **błąd zapisu dziennika nie zdejmuje odmowy już policzonej.** Decyzja nie zależy od
dziennika, więc zepsuty katalog audytu (np. plik w miejscu katalogu) nie wyłącza blokady. To odpowiedź na
pytanie z „Konsekwencji” o fail-closed: hook zostaje fail-open; ginie tylko decyzja, której nie dało się
policzyć.

**Szybkość.** Pomiar 2026-10-06 na serwerze, cały proces Pythona, 33 wywołania (Bash z heredokiem, Read, Write),
stara i nowa wersja w tych samych warunkach (po poprawkach 16c): mediana 31,6 ms (maks. 33,7 ms) wobec 22,7 ms
(maks. 25,5 ms) przed zadaniem 029. Różnica to głównie kompilacja ponad dwa razy dłuższego pliku przy każdym
uruchomieniu. Plik konfiguracji z `blokuj:` hook czyta tylko wtedy, gdy wywołanie ma jakąś flagę. Polecenie
200 KB (np. `echo a+a+…`) zajmuje poniżej 0,2 s: maskowanie działa tylko na początku tekstu (przegląd 16c;
wcześniej 40 KB trwało 6,4 s, a 80 KB — 25,7 s, ponad limit czasu hooka). Limit czasu hooka w
`.claude/settings.json` to 10 s.

**Poprawki reguł** (`tools/audyt_hook.py`; testy „przed/po” na zamaskowanych przykładach z tygodnia, część
„przed” liczy hook z commita `44d2257`):

| id | co zmieniono |
|---|---|
| R1 | cyfry przyklejone do `>`/`<` (`2>&1`, `2>/dev/null`) to numer deskryptora, nie słowo; `git push/pull/fetch` pomija przekierowania i ich cele przy szukaniu nazwy zdalnego repo |
| R2 | treść heredoka (`<<EOF`, `<<'EOF'`, `<<-EOF`) to dane: nie trafia do segmentów ani ścieżek. Wyjątek: heredoc, który w tym samym potoku trafia do powłoki (`bash <<EOF`, `cat <<EOF \| sh`, `ssh host <<EOF`), jest analizowany jak polecenia. Dla `python - <<EOF` heurystyki bibliotek sieciowych i podciągów ścieżek wrażliwych dalej widzą cały tekst. `<<` w cudzysłowie, w komentarzu, w `$(( ))` i `<<<` nie zaczyna heredoka; w `"$( … )"` zaczyna się zwykłe polecenie (heredoc opisu commita jest rozpoznany) |
| R3 | słowo z nową linią (wieloliniowy `python -c "…"`, opis commita z `"$(cat <<'EOF' …)"`) to nie ścieżka. Wybrany drugi wariant z raportu: pomijanie całego argumentu `-c` ukryłoby też jednolinijkowe `python -c "open('~/.ssh/…')"`, a takiego fałszywego alarmu w tygodniu nie było |
| R4 | `NAZWA=wartość` z tego samego polecenia (sam segment przypisań albo `export`) rozwija się w ścieżkach i w `cd` jak `$HOME`; wartość nieznana (`$(…)`, nieznana `$X`) zostaje nierozwinięta. Ścieżka ZACZYNAJĄCA się od nierozwiniętej zmiennej (`$D/plik`) ma nieznane miejsce: bez flag zależnych od miejsca. Zmienna w środku (`/home/x/$D/plik`, `/etc/$X`) nie zmienia oceny — `zapis_poza_repo` zostaje (przegląd 16c) |
| R5 | `<tmp>/claude-<uid>/<projekt>/<session_id>/scratchpad/` tej sesji (także jej subagentów) bez flagi; scratchpad innej sesji i reszta `/tmp` dalej `zapis_tmp` |
| R6 | `~/.claude/plans/` bez flagi; `~/.claude/projects/<projekt>/memory/` bez flagi tylko w sesji głównej (bez `agent_id`) |
| R8 | `dziennik_audytu_zapis` przy zapisie do katalogu audytu: Write/Edit/MultiEdit/NotebookEdit i zapisy w Bash rozpoznawane jak dotąd (`>`, `>>`, `tee`, cel `cp`/`mv`/`install`, `sed -i`, `curl -o`, `wget -O`). Rozszerzenie względem raportu, tylko dla tej flagi: także polecenia, które zmieniają plik bez zapisu treści — `rm`, `rmdir`, `unlink`, `shred`, `truncate`, `touch`, `chmod`, `chown`, `ln`, źródła `mv`, `dd of=`, `find … -delete` (usunięcie albo podmiana dziennika to też zmiana nadzoru). `zapis_poza_repo` i `zapis_tmp` bez zmian. Odczyt zostaje `dziennik_audytu` i nie jest blokowany |

**Poprawki po przeglądzie 16c (2026-10-06, ten sam dzień).** Recenzent sprawdził pierwszą wersję
(`c0ae883`) na prawdziwym procesie. Każdy jego przypadek ma test „odmowa przed / bez odmowy po” na tej
wersji i test, że prawdziwe zdarzenie dalej jest blokowane albo oznaczane.

1. Fałszywe odmowy `poswiadczenia`: `secrets.py` i `token.py` z biblioteki standardowej, `yaml/tokens.py`,
   `ccxt/…/keys.py` w `.venv`, `tools/token_report.py`, `.env.example`, Grep w katalogu `runs/…-tokens`,
   `~/.config/ghostty/config`. Teraz: `.config/gh` jako składniki ścieżki (ghostty bez flagi); człon
   key/token/secret… blokuje tylko pliki danych; reszta dostaje flagę `poswiadczenia_slabe` (widoczną
   w dzienniku, poza `blokuj:`). Twarde przypadki — katalogi kluczy, `.env`, `.env.local`, rozszerzenia
   kluczy, `id_rsa*`, `bybit_api_key.json`, `token.txt` — blokują jak przedtem.
2. Fałszywe odmowy zapisu do katalogu audytu w Bash: `(cd ~/.clas5_audyt && wc -l *.jsonl) > wynik.txt`,
   `cd ~/.clas5_audyt; cd -; rm x.txt`, `ln -s ~/.clas5_audyt/a.jsonl` z jednym argumentem, heredoc notatki
   z `rm ~/.clas5_audyt/x` i dalej `echo … | bash`, `commit -m "$(cat <<'EOF' …)"` z nieparzystą liczbą `"`.
   Teraz: katalog wraca po `)` podpowłoki; `cd -` wraca do katalogu sprzed ostatniego `cd` w poleceniu (bez
   niego katalog nieznany); `ln` z jednym argumentem pominięte; heredoc analizowany jak polecenia tylko, gdy
   w tym samym potoku trafia do powłoki; w `"$( … )"` zaczyna się zwykłe polecenie.
3. Grep nie sprawdzał pola `glob`: `Grep(path="~", glob=".ssh/*")` przechodził. Teraz `glob` w Grep
   i `pattern` w Glob liczą się względem `path` → odmowa.
4. Utrata widoczności: odczyt kluczy w `python3 - <<EOF`, wieloliniowym `python -c` i `node -` nie był
   oznaczany; `echo x > /home/x/$D/plik` i `cp x /etc/$X` traciły `zapis_poza_repo`. Teraz podciągi ścieżek
   wrażliwych w kodzie interpretera dają flagę (tylko flagę), a R4 pomija tylko ścieżkę zaczynającą się od `$`.
5. Host `- api.example.com:8080` (poprawny YAML spoza podzbioru) po cichu wyłączał obie blokady. Teraz
   sekcja `blokuj:` jest czytana niezależnie od reszty pliku.
6. W kodzie stał dosłowny niewidoczny znak U+202A; teraz zakresy są zapisane jako `\U0000202a`.
7. Maskowanie miało czas kwadratowy (40 KB → 6,4 s, 80 KB → 25,7 s, ponad limit hooka). Teraz maskuje się
   tylko początek tekstu (300 + 512 znaków); długość schematu adresu w wykrywaniu URL jest ograniczona.

Ponowny przegląd 16c (ten sam dzień): katalog o nazwie będącej całym słowem poświadczeń (bez wiodącej kropki,
bez rozróżniania wielkości liter, z ewentualnym przedrostkiem `api`) znów jest przypadkiem twardym —
`Grep(path="/run/secrets")` dostaje odmowę, a słowo jako część dłuższej nazwy katalogu
(`runs/2026-10-10_t1-tokens`) daje dalej tylko flagę słabą. Plik w takim katalogu, także plik kodu
(`keys/x.py`), jest twardy tak samo jak plik w `.ssh/`.

Powtórka tygodnia nowymi regułami (0 odmów w tygodniu i 0 w dniu 2026-10-06; szczegóły i komendy):
[`13_tydzien_obserwacji.md`](13_tydzien_obserwacji.md), sekcja 9.

**Granica bez zmian:** to analiza tekstu, nie piaskownica. Na przykład zapis do katalogu audytu z wnętrza
`python skrypt.py` albo kopia klucza pod niewinną nazwą (`cp ~/.ssh/klucz x; cat x` — w Bash tylko flaga)
nie zostaną zablokowane. Ograniczenia wprowadzone świadomie:

- po R2 hook nie czyta skryptu zapisanego heredokiem i uruchomionego w tym samym poleceniu
  (`cat > x.sh <<EOF … EOF; bash x.sh`) — tak samo jak skryptu zapisanego narzędziem Write; w dziennikach
  2026-09-29…10-06 nie ma ani jednego takiego polecenia;
- kod interpretera (`python - <<EOF`, `python -c`, `node -e`) przeglądają tylko heurystyki podciągów
  (biblioteki sieciowe, `.ssh/`, `.aws/`, `.clas5_audyt`…). Dają same flagi: zapis do katalogu audytu
  z wnętrza takiego kodu dostaje flagę ODCZYTU `dziennik_audytu`, nigdy odmowę;
- plik kodu z prawdziwymi sekretami (np. `config/secrets.py`) dostaje tylko `poswiadczenia_slabe`, bez
  odmowy — tak zdecydował orkiestrator po przeglądzie 16c, żeby nie blokować modułów o takich nazwach;
- ścieżka zaczynająca się od nieznanej zmiennej (`$D/plik`) i zapis względny po `cd -` bez znanego
  poprzedniego katalogu nie dostają flag zależnych od miejsca;
- znana luka sprzed zadania 029, do zadania 030: polecenia wewnątrz `"$( … )"` w podwójnym cudzysłowie
  nie są analizowane jako polecenia, więc np. `echo "$(curl https://evil.io)"` albo
  `x="$(rm ~/.clas5_audyt/a.jsonl)"` nie dostają flagi (bez cudzysłowu `$( … )` działa).

Blokady chronią przed pomyłką i prostą próbą; twardą granicą jest etap 3.

## Etap 3 — osobny użytkownik systemu (lista kroków dla użytkownika)

Stan serwera (2026-09-29, odczyt bez zmian): użytkownik `dantey1` w grupach `adm cdrom sudo dip plugdev lxd
docker`; `/home/dantey1` ma prawa `750`, `/home/dantey1/alpha` `775`; kolektory i dziennik działają z crona
jako `dantey1` (`~/alpha-dziennik`, `~/likwidacje`, `~/likwidacje_bybit`, `~/likwidacje_kopia`). **Grupy
`docker`, `lxd`, `sudo`, `adm` dają w praktyce prawa roota — nowy użytkownik nie może być w żadnej z nich.**

Kroki oznaczone `sudo` robi wyłącznie użytkownik. Każdy krok ma sprawdzenie. Nic z tego nie dotyka crona,
kolektorów ani dziennika — działają dalej jako `dantey1`.

1. **Użytkownik bez hasła i bez grup dodatkowych** (`sudo`):
   ```bash
   sudo useradd --create-home --shell /bin/bash --user-group clas5wyk
   sudo passwd -l clas5wyk                       # brak logowania hasłem
   id clas5wyk                                   # oczekiwane: tylko grupa clas5wyk
   ```
2. **Sprawdzenie, że nie widzi domu `dantey1`** (`sudo`, tylko odczyt):
   ```bash
   sudo -u clas5wyk ls /home/dantey1             # oczekiwane: Permission denied
   sudo -u clas5wyk test -r /home/dantey1/.ssh && echo ZLE || echo OK
   sudo -u clas5wyk test -r /home/dantey1/likwidacje && echo ZLE || echo OK
   ```
   Jeśli któreś da „ZLE”: `chmod 750 /home/dantey1` (bez `sudo`, własny katalog).
3. **Wspólne repo pośrednie z bramką na gałęzie.** Wykonawca pcha tylko `zadanie-*`; `master` zmienia tylko
   `dantey1` (`sudo` do katalogu `/srv`):
   ```bash
   sudo mkdir -p /srv/clas5 && sudo chown dantey1:clas5wyk /srv/clas5 && sudo chmod 2770 /srv/clas5
   git clone --bare /home/dantey1/alpha /srv/clas5/alpha.git            # jako dantey1
   git -C /srv/clas5/alpha.git config core.sharedRepository group
   chmod -R g+rwX /srv/clas5/alpha.git
   chmod 755 /srv/clas5/alpha.git/hooks && chmod 644 /srv/clas5/alpha.git/config   # bez zapisu grupy
   cat > /srv/clas5/alpha.git/hooks/pre-receive <<'EOF'
   #!/bin/sh
   [ "$(id -un)" = "dantey1" ] && exit 0
   while read old new ref; do
     case "$ref" in refs/heads/zadanie-*) ;; *) echo "odmowa: $ref (wykonawca pcha tylko zadanie-*)"; exit 1;; esac
   done
   EOF
   chmod 755 /srv/clas5/alpha.git/hooks/pre-receive
   git -C /home/dantey1/alpha remote add wykonawcy /srv/clas5/alpha.git
   ```
   `hooks/` i `config` bez prawa zapisu dla grupy — inaczej wykonawca mógłby podmienić bramkę albo ustawić
   `core.hooksPath`. Sprawdzenie: `sudo -u clas5wyk git -C <klon> push origin HEAD:master` → „odmowa”.
   **Granica tej bramki:** grupa ma prawo zapisu w `refs/` repozytorium `/srv/clas5/alpha.git`, więc wykonawca
   może przestawić `master` wprost na dysku, z pominięciem `pre-receive`. Bramka chroni przed pomyłką, nie przed
   celowym obejściem. Prawdziwą ochroną jest to, że `dantey1` scala tylko w głównym repo
   (`/home/dantey1/alpha`) i nigdy nie pobiera `master` z `/srv/clas5/alpha.git`; stamtąd bierze wyłącznie
   gałęzie `zadanie-*`, i to po przeglądzie (przegląd 16c zadania 002).
4. **Klon wykonawcy i środowisko Pythona** (`sudo -u`):
   ```bash
   sudo -u clas5wyk git clone /srv/clas5/alpha.git /home/clas5wyk/alpha
   sudo -u clas5wyk python3 -m venv /home/clas5wyk/alpha/.venv
   sudo -u clas5wyk /home/clas5wyk/alpha/.venv/bin/pip install -r /home/clas5wyk/alpha/requirements-lock.txt
   ```
   (Ten krok przed krokiem 6, gdy sieć jeszcze nie jest zamknięta — albo po nim, przez proxy.)
5. **Proxy z listą hostów** (`sudo`): lokalny `tinyproxy` na `127.0.0.1:8888`, `FilterDefaultDeny Yes`,
   filtr = hosty z `config/audyt_hosty.yaml` **plus hosty samego Claude Code** (co najmniej
   `api.anthropic.com`; pełną listę podaje dokumentacja Claude Code o pracy za proxy — sprawdzić przed
   włączeniem, inaczej wykonawca nie połączy się z modelem):
   ```bash
   sudo apt install tinyproxy
   # /etc/tinyproxy/tinyproxy.conf: Listen 127.0.0.1 · Port 8888 · Filter "/etc/tinyproxy/clas5.filter"
   #   FilterDefaultDeny Yes · FilterExtended On · ConnectPort 443
   # /etc/tinyproxy/clas5.filter: po jednym wzorcu na linię, np. ^fapi\.binance\.com$
   sudo systemctl restart tinyproxy
   ```
   U wykonawcy (`/home/clas5wyk/.claude/settings.json`, pole `env`): `HTTPS_PROXY=http://127.0.0.1:8888`,
   `HTTP_PROXY=http://127.0.0.1:8888`, `NO_PROXY=localhost,127.0.0.1`.
6. **Zapora: `clas5wyk` wychodzi tylko na interfejs lokalny** (`sudo`). Osobna tabela nft — nie rusza reguł
   Dockera:
   ```bash
   sudo tee /etc/clas5-nft.conf >/dev/null <<'EOF'
   table inet clas5 {
     chain wyjscie {
       type filter hook output priority 0; policy accept;
       meta skuid "clas5wyk" oif "lo" accept
       meta skuid "clas5wyk" counter drop
     }
   }
   EOF
   sudo nft -f /etc/clas5-nft.conf
   sudo -u clas5wyk curl -sI -m 5 https://example.com && echo ZLE || echo OK      # bez proxy: blokada
   sudo -u clas5wyk curl -sI -m 5 -x http://127.0.0.1:8888 https://api.bybit.com | head -1   # przez proxy: działa
   ```
   Trwałość po restarcie: jednostka systemd typu `oneshot` z `ExecStart=/usr/sbin/nft -f /etc/clas5-nft.conf`
   (`sudo systemctl enable clas5-nft`). **Nie** zapisywać całego `nft list ruleset` do `/etc/nftables.conf`
   — to utrwaliłoby też dynamiczne reguły Dockera.
7. **Claude Code dla wykonawcy** (ręce użytkownika): instalacja dla `clas5wyk` i jednorazowe logowanie
   (`sudo -u clas5wyk -i claude`). Logowanie kontem to decyzja użytkownika (koszt, limit). Hook audytowy
   działa u wykonawcy z repo (`.claude/settings.json` klonu).
8. **Uruchamianie wykonawcy przez orkiestratora** (`sudo visudo -f /etc/sudoers.d/clas5`):
   ```
   dantey1 ALL=(clas5wyk) NOPASSWD: /usr/local/bin/clas5-wykonawca
   ```
   `/usr/local/bin/clas5-wykonawca` (własność `root`, `755`) przyjmuje tylko numer zadania, robi
   `git fetch`, zakłada gałąź `zadanie-NNN-…` od `origin/master` i uruchamia `claude -p` z treścią zadania;
   na koniec `git push origin zadanie-NNN-…`. Treść skryptu i zmiana orkiestratora (Agent → skrypt) to osobne
   zadanie `infra` po decyzji — tu tylko reguła.
9. **Dziennik audytu wykonawcy poza jego zasięgiem.** Hook u `clas5wyk` pisze do `~clas5wyk/.clas5_audyt`
   — wykonawca może ten plik zmienić. Odporna wersja: hook dodatkowo wysyła wiersz do dziennika systemowego
   (`logger -t clas5-audyt`), którego wykonawca nie zmieni; `dantey1` czyta go przez `journalctl -t
   clas5-audyt` (grupa `adm`). Zmiana hooka — osobne zadanie po decyzji.

### Co wymaga `sudo` (czyli rąk użytkownika)

Kroki 1, 2 (sprawdzenia), 3 (katalog `/srv/clas5`), 4 (`sudo -u`), 5 (pakiet i konfiguracja proxy),
6 (zapora i jednostka systemd), 7 (logowanie jako `clas5wyk`), 8 (`sudoers`). Bez `sudo`: `chmod 750
/home/dantey1`, sklonowanie repo pośredniego, `git remote add`.

## Ścieżka odwrotu

- **Etap 1 (hook):** usunąć grupę `audyt_hook.py` z `PreToolUse` w `.claude/settings.json` (jeden commit,
  test `tests/test_project_settings.py` trzeba zdjąć razem z nim). Dziennik `~/.clas5_audyt/` zostaje;
  usunięcie danych to decyzja użytkownika.
- **Etap 2 (blokowanie):** wyczyścić listę `blokuj:` w `config/audyt_hosty.yaml` — hook wraca do „oznacza”.
- **Etap 3 (użytkownik):** `sudo rm /etc/sudoers.d/clas5`; `sudo systemctl disable --now clas5-nft`;
  `sudo nft delete table inet clas5`; `sudo apt remove tinyproxy`; gałęzie z `/srv/clas5/alpha.git` pobrać do
  głównego repo (`git fetch wykonawcy`), potem `sudo rm -rf /srv/clas5`; `sudo userdel -r clas5wyk`.
  Wykonawcy wracają do subagentów w procesie sesji głównej (stan sprzed etapu 3).

## Otwarte

- Hook nie widzi sieci ani zapisów wewnątrz skryptów Pythona uruchamianych z pliku (`python skrypt.py`) —
  zakres etapu 3, nie hooka.
- Hosty Claude Code dla proxy (krok 5) sprawdzić w dokumentacji przed włączeniem zapory.
- Czy przykład z żywej sesji (hook aktywny) zastąpi odtworzony — po scaleniu do `master`.
