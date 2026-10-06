# Mapa dokumentacji projektu

> Plik-indeks (D.2 w `STATUS.md`): jedno miejsce linkujące wszystkie dokumenty projektu, z
> jednozdaniowym opisem każdego. Nie zastępuje żadnego z nich — `STATUS.md` zostaje
> jedynym źródłem aktualnego statusu, `docs/rag/*.md` jedynym źródłem pełnych uzasadnień decyzji.
>
> Ostatnia aktualizacja: 2026-10-06.

## Dokumenty nadrzędne (root)

| Plik | Jednozdaniowy opis |
|---|---|
| [`README.md`](../README.md) | Wejście do repo dla ludzi (GitHub) — czym jest projekt, szybki start, zastrzeżenia |
| [`CLAUDE.md`](../CLAUDE.md) | Krótkie, stabilne instrukcje/zasady dla Claude Code, czytane automatycznie na starcie sesji |
| [`STATUS.md`](../STATUS.md) | Plan, historia rund, ryzyka (§7), zadania z ID i statusem, backlog — żywy dokument (scalone IMPLEMENTATION_PLAN+TASKS, 2026-09-22) |
| [`runs/INDEX.md`](../runs/INDEX.md) | Księga eksperymentów: wyniki rund, wnioski skumulowane, liczniki budżetu multiple-testing |
| [`mapa_projektu.html`](mapa_projektu.html) | Źródło zakładki „Mapa” strony „Pulpit CLAS-5” (https://claude.ai/artifact/NKxticRcxgFFXxntNZnZ4b#mapa; składa `tools/pulpit_clas5.py`): przepływ od pomysłu do kapitału, automaty dnia, mapa myśli i stan wiedzy — widok; przy sprzeczności wygrywają pliki źródłowe |
| [`strona_dziennik.html`](strona_dziennik.html) | Źródło zakładki „Dziennik” strony „Pulpit CLAS-5” (https://claude.ai/artifact/NKxticRcxgFFXxntNZnZ4b#dziennik): stan dziennika papierowego z dokumentu bazy `dziennik/stan` (rutyna Cowork, 06:30 UTC); odtworzone 2026-09-28 z opublikowanej strony |
| [`mapa_hipotez_2026-10.md`](mapa_hipotez_2026-10.md) | Mapa hipotez (zadanie 007, 2026-09-29, 0 odczytów): 10 rodzin (B3, B4, C1, D3, G1, Y2, PT1, E1, Hyperliquid ×2) z pięcioma polami, filtrem (a)–(f), rachunkiem mocy liczonym dwiema drogami (skrypt `mapa_hipotez_2026-10_moc.py`, wydruk `.txt`) i werdyktem: 6 NIEMIERZALNYCH, 4 BRAK DANYCH; kolejność E1 → HL → PT1 |
| [`przeglad_literatury_cp1_e1.md`](przeglad_literatury_cp1_e1.md) | Przegląd badań (zadanie 026, 2026-10-05, 0 odczytów): premia Coinbase — dla samego sygnału BRAK ŹRÓDŁA, mechanizm pokrewny umiarkowany, szczebel 1(a) słaby; E1 — zakładany efekt 0,75 % brutto na epizod w 24 h (zakres 0–1,3 %) do karty 011; propozycja 1(b) na funduszach krajowych zamkniętych |

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
| [`09_drabina_dowodow.md`](rag/09_drabina_dowodow.md) | **ADR-09 (2026-09-24):** kryterium decyzji o kapitale = drabina dowodów (mechanizm poza naszymi danymi → spójność w wycinkach → dziennik ≥ 3 mies. → ≤ 5 % kapitału → skalowanie), zamiast t > 1,96 na historii 2021–2026, strukturalnie nieosiągalnego dla strategii tygodniowych |
| [`10_preferencje_uzytkownika.md`](rag/10_preferencje_uzytkownika.md) | Preferencje użytkownika przeniesione z pamięci lokalnej Claude Code (2026-09-24): sposób handlu (3× na części kapitału, depozyt = ekspozycja/3), cel zwrotów (bez carry), rynek przed 2022, skille z chmury konta |
| [`11_przeglad_kandydatow_2026-09-27.md`](rag/11_przeglad_kandydatow_2026-09-27.md) | Przegląd całego projektu (2026-09-27, 0 odczytów): 35 kandydatów do testów i dziennika — 3 przeszły (kolektor likwidacji Bybit, kopia i indeks LK0, rozbicie zwrotu dziennika), 18 wymaga decyzji użytkownika, 14 odrzuconych z powodem; historia 2021–2026 nie rozstrzygnie nowej hipotezy (41. odczyt, dowód wymaga t ≈ 3,84) |
| [`12_zuzycie_tokenow.md`](rag/12_zuzycie_tokenow.md) | Pomiar zużycia tokenów (2026-09-28): 57 % główna sesja (kontekst 0,5–0,8 mln na wywołanie, 9 % przepisania po przerwie), 43 % workflow; ocena wytycznych (Headroom: nie; nowa sesja na zadanie: tak) i zasady oszczędzania; monitor `tools/zuzycie_tokenow.py`; strona „Tokeny CLAS-5” i warianty jej codziennego odświeżania |
| [`13_izolacja_wykonawcow.md`](rag/13_izolacja_wykonawcow.md) | **ADR-13 (2026-09-29, zadanie 002):** izolacja wykonawców tablicy — etap 1 hook audytowy `tools/audyt_hook.py` (tylko oznacza: sieć poza `config/audyt_hosty.yaml`, zapisy poza repo, poświadczenia; dziennik `~/.clas5_audyt/`), etap 2 blokowanie po tygodniu za decyzją użytkownika, etap 3 osobny użytkownik `clas5wyk` + proxy + repo pośrednie — numerowana lista kroków z `sudo` i ścieżka odwrotu; przykład dziennika `13_przyklad_audytu.jsonl` |
| [`13_tydzien_obserwacji.md`](rag/13_tydzien_obserwacji.md) | **Tydzień obserwacji hooka audytowego (zadanie 005, 2026-10-06):** 2797 wywołań, 364 z flagą (13 %), 0 nadużyć, 4 prawdziwe zdarzenia (pomiar LH0 poza repo), reszta głównie fałszywe alarmy samego hooka; poprawki reguł R1–R8 z miejscem w `tools/audyt_hook.py`; propozycja dla każdej flagi (blokować teraz tylko `poswiadczenia` w narzędziach plikowych i zapis do katalogu audytu) i komendy `jq`/Python do powtórzenia |
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
