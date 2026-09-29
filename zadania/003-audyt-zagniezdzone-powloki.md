---
id: 003
tytul: Hook audytowy — luki wykrywania z przeglądu 002 (bash -c, gh api, hasła przy opcjach)
typ: infra
status: w_toku
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

(dopisuje orkiestrator)
