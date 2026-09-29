---
id: 026
tytul: Hook audytowy — analiza wywraca się na samotnym surogacie (\ud800) w os.path.realpath
typ: naprawa
status: w_toku
zlecil: orkiestrator
decyzja_uzytkownika: "brak (typ naprawa — orkiestrator sam, zadania/README.md)"
utworzono: 2026-09-29
zalezy_od: [002, 021]
budzet: "Opus medium, 1 wykonawca"
---

# 026 — Samotny surogat w ścieżce wywraca analizę hooka audytowego

## Po co

Wykonawca zadania 021 trafił na niestabilny test `tests/test_audyt_hook.py::test_property_nested_shell_analysis_never_raises`:
`hypothesis` losuje znak `\ud800`, a `os.path.realpath` w `tools/audyt_hook.py` rzuca `UnicodeEncodeError` (Linux).
Hook łapie wyjątek i zapisuje wiersz z błędem analizy, więc sesja nie pada. Ale polecenie z takim znakiem nie jest
oceniane, a test raz przechodzi, raz nie. Niestabilny test osłabia DoD (zasada 10).

## Zakres

1. Odtworzyć błąd jawnym przykładem (`\ud800` w ścieżce w poleceniu) — test, który dziś pada.
2. Poprawka: normalizacja ścieżek w hooku nie może rzucać na samotnym surogacie (Linux i Windows). Ścieżka z surogatem
   ma być oceniona jak każda inna: np. zapis do pliku w `~/.ssh` z surogatem w nazwie nadal oznaczony jako podejrzany.
3. Testy: regresja z punktu 1, test oznaczenia z punktu 2, test właściwości bez zmiany zakresu losowania (albo szerszy).
4. Przegląd kodu (`engineering:code-review`) przed oddaniem; werdykt jednym zdaniem w wyniku.

## Czego NIE robić

- Nie zmieniać zachowania dla bajtu zerowego (udokumentowane: wiersz z `blad_analizy`, osobny test).
- Nie zmieniać `.claude/settings.json` ani tego, co i gdzie hook zapisuje (`~/.clas5_audyt/`).
- Hook dalej tylko oznacza, niczego nie blokuje (decyzja o blokowaniu: zadanie 005).

## Kryteria odbioru (dowody)

- Test z punktu 1 pada przed poprawką i przechodzi po niej (wydruk obu w logu zadania).
- `tests/test_audyt_hook.py` zielony kilka razy z rzędu (np. 5 przebiegów z różnym `--hypothesis-seed`).
- Pełny `pytest -q` zielony (OMP_NUM_THREADS=4), `ruff` + `black --check` na dotkniętych plikach.

## Wynik

(dopisuje orkiestrator)
