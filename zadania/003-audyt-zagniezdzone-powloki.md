---
id: 003
tytul: Hook audytowy — luki wykrywania z przeglądu 002 (bash -c, gh api, hasła przy opcjach)
typ: infra
status: zrobione
zlecil: orkiestrator
decyzja_uzytkownika: "2026-09-29: kolejność tablica → izolacja → ewentualny harmonogram (podzadanie typu infra z zadania 002)"
utworzono: 2026-09-29
zalezy_od: [002]
budzet: "Opus medium, krótko"
---

# 003 — Luki wykrywania hooka audytowego

## Po co

Przegląd 16c zadania 002 znalazł znane granice analizy tekstowej w `tools/audyt_hook.py`. Hook ich nie widzi:

- ruch sieciowy w zagnieżdżonej powłoce: `bash -c '…'`, `sh -c '…'`;
- `gh api` i inne polecenia `gh`, bo `gh` nie ma na liście programów sieciowych;
- hasło przyklejone do opcji, np. `mysql -psecretpw`, trafia do dziennika jawnym tekstem;
- zapis przez `sed -i` poza repo i `cd /tmp && curl -o x`.

## Zakres

1. Zejście w `bash -c` i `sh -c`: parsować wewnętrzne polecenie tą samą funkcją.
2. `gh` jako program sieciowy (host `api.github.com`, już na liście).
3. Maskowanie `-p<hasło>` tam, gdzie to bezpieczne (np. `mysql`, `psql`), bez psucia innych poleceń.
4. Zapis przez `sed -i` i `tee` do pliku poza repo.
5. Testy dla każdego przypadku.

## Czego NIE robić

- Nie włączać blokowania; hook dalej tylko oznacza.
- Nie spowalniać hooka powyżej ok. 50 ms na wywołanie.

## Kryteria odbioru (dowody)

- Testy przechodzą, pełny `pytest` z kodem 0.
- Przegląd `engineering:code-review`.

## Wynik

- **Co zrobiono:** `tools/audyt_hook.py` analizuje wnętrze `bash -c`/`sh -lc`/`eval` (do 3 poziomów, także z `-o pipefail`
  przed `-c` — poprawka orkiestratora z przeglądu); `gh` = sieć do `api.github.com` (lub `--hostname`); zapisy przez
  `sed -i`, `curl -o`, `wget -O`; ścieżki względne po `cd`; maskowanie `-p<hasło>` dla mysql/mariadb i `sshpass -p`.
  Nadal tylko oznacza (kod 0, puste stdout).
- **Nie pokryto:** `psql -p` (to port), podpowłoki i `||` przy `cd`, obejścia przez `base64`/`$(...)` — granica
  opisana w docs/rag/13 (widoczność, nie piaskownica).
- **Commity i gałęzie:** `zadanie-003-audyt-powloki`: 43ce44f (wykonawca), poprawka `-o`/`-O` + test (orkiestrator); scalone do `master`.
- **Dowody:** pełny `OMP_NUM_THREADS=4 py -m pytest -q`: 1914 passed, 2 skipped, kod 0. Druga droga: 5 ręcznych wejść do hooka
  (`bash -c` z obcym hostem → oznaczone; `cd /tmp && curl -o x` → `zapis_tmp`; `mysql -pTajne123` → `-p***`; `gh pr list`
  → bez flagi, host na liście). Czas: mediana 21,8 → 22,1 ms (wykonawca).
- **Bramka 16c** (`engineering:code-review`, orkiestrator): **Approve** po poprawce jedynej luki (`bash -o pipefail -c`).
  Uwagi nieblokujące: `wget -o` (plik logu) nie liczy się jako zapis; `curl -O` (nazwa z adresu) też nie.
- **Co zostało:** nic w tym zadaniu.
