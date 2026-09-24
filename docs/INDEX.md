# Mapa dokumentacji projektu

> Plik-indeks (D.2 w `STATUS.md`): jedno miejsce linkujące wszystkie dokumenty projektu, z
> jednozdaniowym opisem każdego. Nie zastępuje żadnego z nich — `STATUS.md` zostaje
> jedynym źródłem aktualnego statusu, `docs/rag/*.md` jedynym źródłem pełnych uzasadnień decyzji.
>
> Ostatnia aktualizacja: 2026-09-22.

## Dokumenty nadrzędne (root)

| Plik | Jednozdaniowy opis |
|---|---|
| [`README.md`](../README.md) | Wejście do repo dla ludzi (GitHub) — czym jest projekt, szybki start, zastrzeżenia |
| [`CLAUDE.md`](../CLAUDE.md) | Krótkie, stabilne instrukcje/zasady dla Claude Code, czytane automatycznie na starcie sesji |
| [`STATUS.md`](../STATUS.md) | Plan, historia rund, ryzyka (§7), zadania z ID i statusem, backlog — żywy dokument (scalone IMPLEMENTATION_PLAN+TASKS, 2026-09-22) |
| [`runs/INDEX.md`](../runs/INDEX.md) | Księga eksperymentów: wyniki rund, wnioski skumulowane, liczniki budżetu multiple-testing |

## `docs/rag/` — pełne uzasadnienia decyzji

| Plik | Jednozdaniowy opis |
|---|---|
| [`01_hipoteza_i_architektura.md`](rag/01_hipoteza_i_architektura.md) | Dlaczego Faza 0 poprzedza resztę PRD, fazowanie Faza 0–4, hipoteza regime-gated (momentum vs mean-reversion) |
| [`02_cechy_i_leakage.md`](rag/02_cechy_i_leakage.md) | Metodologia ekstrakcji cech z wielu repo bez zależności runtime, definicje 9 cech Fazy 0, podejście do leakage |
| [`03_ryzyko_i_sizing.md`](rag/03_ryzyko_i_sizing.md) | Triple-barrier labeling (ATR-scaled), walk-forward split, diagnostyka N_eff, dwa osobne modele; ADR-y: bramka kosztowa jako GÓRNE oszacowanie (H3), próg wykrywalności (K1), **wagi klas domyślnie — adopcja A1 po K2** |
| [`04_narzedzia_zewnetrzne.md`](rag/04_narzedzia_zewnetrzne.md) | Uzasadnienie decyzji o freqtrade/LEAN/QuantConnect jako katalogach wzorców, nigdy zależnościach runtime |
| [`05_metodologia_wytwarzania_i_testow.md`](rag/05_metodologia_wytwarzania_i_testow.md) | Piramida testów (unit/leakage/property-based/integration/walk-forward) i Definition of Done per commit |
| [`06_llm_nadzorczy_i_baza_wiedzy.md`](rag/06_llm_nadzorczy_i_baza_wiedzy.md) | Projekt trzech komponentów LLM offline/nadzorczo (`ai_interpreter`, `post_trade_critic`, `test_mathematics`) i `docs/rag/` jako baza wiedzy |
| [`07_notatki_spotkania_i_szersza_wizja_systemu.md`](rag/07_notatki_spotkania_i_szersza_wizja_systemu.md) | Analiza rozbieżności między notatkami ze spotkania (pełny zakres PRD, zespoły z terminami) a dyscypliną Fazy 0 — otwarte pytania |
| [`08_zasady_pelne_brzmienie.md`](rag/08_zasady_pelne_brzmienie.md) | Pełne brzmienie zasad 1–20 z uzasadnieniami, historią i sprostowaniami — kopia `CLAUDE.md` sprzed odchudzenia (2026-09-24); `CLAUDE.md` mówi CO, ten plik DLACZEGO |
| [`Repo lessons i sigma — co przydatne dla alpha.md`](<rag/Repo lessons i sigma — co przydatne dla alpha.md>) | Przegląd dwóch innych projektów użytkownika (SIGMA na QuantConnect, lessons/AI_devs) — wytyczne 1–7 wdrożone w `docs/skills/bramki-jakosci.md` (A6, B6a, C1), kontrola negatywna NC1, strażnik `tests/test_runs_index_guard.py`, odchudzony `CLAUDE.md`. Kolejność propozycji w pliku jest już nieaktualna (D1/O1 zamknięte, carry odrzucone jako cel) |

## `docs/skills/` — procedury pracy (wersjonowane z repo, niezależne od pluginów)

| Plik | Jednozdaniowy opis |
|---|---|
| [`bramki-jakosci.md`](skills/bramki-jakosci.md) | Pełna ściąga trzech bramek jakości z CLAUDE.md zasady 16: walidacja write-upu, standard statystyk, przegląd kodu — listy kontrolne, pułapki z naszych rund, wzory, format werdyktów |

**Skille projektu (`clas5-runda`, `clas5-quant`) NIE mieszkają w repo**, tylko w chmurze
konta claude.ai (decyzja użytkownika 2026-09-23, `CLAUDE.md` — wytyczna „Skille projektu
mieszkają w chmurze konta”). Modyfikacja skilla = nowa wersja wgrana do chmury, nie edycja
pliku w repo. Historia: do 2026-09-22 istniały trzy kopie `clas5-runda` (tu, w `.claude/skills/`
i w chmurze) i rozjechały się; 2026-09-22 zostawiono kopię w `.claude/skills/`, 2026-09-23 —
po sprawdzeniu, że była bajt w bajt zgodna z chmurową — usunięto i ją. `bramki-jakosci.md`
to dokument procedury (zasada 16), nie skill, więc zostaje tutaj.

## Legenda `status` (YAML frontmatter w `docs/rag/*.md`)

| Status | Znaczenie |
|---|---|
| `active` | Treść zgodna z aktualnym stanem kodu/decyzji — domyślny status |
| `stale` | Treść może nie odzwierciedlać aktualnego stanu — do przeglądu przed poleganiem na niej |
| `superseded` | Zastąpione przez inny dokument (patrz jego `depends_on`/treść) — zostaje jako archiwum |

`depends_on` w każdym pliku wskazuje inne `docs/rag/*.md`, na których dany dokument buduje swoje
uzasadnienie — czytaj je najpierw, jeśli potrzebujesz pełnego kontekstu.
