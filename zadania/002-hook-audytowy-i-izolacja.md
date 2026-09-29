---
id: 002
tytul: Hook audytowy wykonawców i plan izolacji na serwerze
typ: infra
status: zrobione
zlecil: cowork
decyzja_uzytkownika: "2026-09-29: kolejność tablica → izolacja → ewentualny harmonogram"
utworzono: 2026-09-29
zalezy_od: [000]
budzet: "Sonnet do kodu, Opus do przeglądu"
---

# 002 — Hook audytowy i izolacja wykonawców

## Po co

Wnioski z incydentu OpenAI/Hugging Face (lipiec 2026) i raportów OpenAI z 17.09:

- agenci znajdują boczne kanały w każdym wspólnym zasobie, do którego mogą pisać;
- przy przeszkodzie szukają obejścia (publiczne serwisy, zmyślone dane).

Zanim tablica zacznie działać bez nadzoru, potrzebujemy widoczności i granic.

## Zakres

1. **Hook audytowy** Claude Code (`PreToolUse` lub `PostToolUse`, obok istniejącego strażnika kontekstu
   `tools/straznik_kontekstu.py`). Zapisuje do `~/.clas5_audyt/RRRR-MM-DD.jsonl` i oznacza:
   - polecenia sieciowe (`curl`, `wget`, `git push`, `pip install`, `python -c` z `requests`/`urllib`) do hostów spoza
     listy dozwolonych w pliku konfiguracyjnym;
   - zapisy poza bieżącym worktree i poza `runs/`/`data/`;
   - odczyty `~/.ssh`, plików `.env`, kluczy i poświadczeń.

   Tryb pierwszy: **tylko oznacza, nie blokuje**. Blokowanie po tygodniu obserwacji, za decyzją użytkownika.
2. **Testy** hooka bez sieci (przypadki dozwolone i oznaczane).
3. **Plan izolacji**, tylko dokument (`docs/rag/13_izolacja_wykonawcow.md`):
   - osobny użytkownik systemu dla wykonawców, bez dostępu do `~/.ssh`, kluczy i katalogów danych kolektorów;
   - uprawnienia do katalogów;
   - lista dozwolonych hostów;
   - co wymaga `sudo`, czyli co musi zrobić użytkownik.

## Czego NIE robić

- Nie zmieniać uprawnień systemowych ani użytkowników (wymaga `sudo`, a więc decyzji i rąk użytkownika).
- Nie blokować niczego w pierwszej wersji.
- Nie ruszać kolektorów, dziennika ani crona.

## Kryteria odbioru (dowody)

- Testy hooka przechodzą.
- Przykładowy plik audytu z jednej sesji.
- `security-review` i `engineering:code-review` (bramki).
- Dokument planu izolacji z listą kroków dla użytkownika.

## Wynik

- **Co zrobiono:** hook `tools/audyt_hook.py` (PreToolUse: Bash, Read, Write, Edit, MultiEdit, NotebookEdit, WebFetch,
  Grep, Glob), wpięty w `.claude/settings.json` wywołaniem `py || python3 || true`. **Tylko oznacza:** zawsze kod 0,
  nic na stdout. Zapis do `~/.clas5_audyt/RRRR-MM-DD.jsonl` (0700/0600, `O_NOFOLLOW`). Flagi: `siec_poza_lista`
  (lista w `config/audyt_hosty.yaml`, 31 hostów z kodu repo), `zapis_poza_repo`, `zapis_tmp` (łagodna, scratchpad),
  `poswiadczenia`, `wejscie_nieczytelne`. Nie zapisuje treści plików; maskuje wzorce sekretów. Czas ok. 22 ms na
  wywołanie. Plan izolacji: `docs/rag/13_izolacja_wykonawcow.md` (3 etapy, numerowana lista kroków z `sudo` dla
  użytkownika, przejście „oznacza → blokuje” po tygodniu za decyzją użytkownika, ścieżka odwrotu).
- **Commity i gałęzie:** `zadanie-002-hook-audytowy`: 0fabfb1 (wykonawca), a164a96 (przegląd 16c: maskowanie
  `-u użytkownik:hasło`), domknięcie orkiestratora (zdanie o granicy bramki `pre-receive` w dok. 13); scalone do `master`.
- **Dowody:** pełny `OMP_NUM_THREADS=4 py -m pytest -q` na gałęzi po poprawkach: 1859 passed, 2 skipped, kod 0
  (orkiestrator, 2026-09-29). Druga droga: 4 ręczne wejścia do hooka (curl z hasłem do obcego hosta → zamaskowane
  i oznaczone; odczyt `~/.ssh/id_ed25519` → `poswiadczenia`; `git status` → bez flag; zły JSON → `wejscie_nieczytelne`),
  wszystkie kod 0, puste stdout. Przykładowy audyt: `docs/rag/13_przyklad_audytu.jsonl` (11 wierszy, 3 oznaczone;
  zbudowany z realnych wywołań podanych hookowi, bo hook worktree nie był aktywny w sesji wykonawcy).
- **Bramki:** `security-review` (wykonawca): Ready, bez podatności wysokich/średnich. `engineering:code-review`
  (niezależny przeglądający): **Approve z uwagami** — jedyny wyciek (hasło w `curl -u`) poprawiony z 5 testami.
- **Co zostało:**
  - znane luki wykrywania (`bash -c`/`sh -c`, `gh api`, hasło przyklejone do opcji jak `-psecret`) → zadanie 003;
  - tydzień obserwacji dziennika `~/.clas5_audyt/`, potem decyzja użytkownika o blokowaniu;
  - kroki z `sudo` z dokumentu 13 — do zrobienia przez użytkownika, gdy zdecyduje.
