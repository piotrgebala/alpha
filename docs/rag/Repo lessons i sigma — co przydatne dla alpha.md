# Repo lessons i sigma — co przydatne dla alpha

Sep 24, 2026 · @Piotr Gębala

## W skrócie

> **Pilne, niezależnie od alpha:** w repo lessons są **śledzone przez git dwa pliki z kluczami API** (`files/aidevsapikey.txt`, `files/gpt4o apykey.txt`), a `.gitignore` nie wyklucza folderu `files/`. Zdalne repo to `github.com/piotrgebala/lessons`. Nie sprawdziłem, czy jest publiczne, ale jeśli klucze były wypchnięte, trzeba je traktować jak ujawnione — **unieważnić i wygenerować nowe**. Szczegóły w sekcji „AI\_devs 4: czego nie przenosić, błędy i problemy”.

- **Kurs Tokenomia (`maths/`): przydatny częściowo** — jako ściąga z pomiaru ryzyka i lista przestróg, nie jako źródło pomysłów na przewagę. Najcenniejszy jest rozdział 5 (VaR i Expected Shortfall) — od razu do D1. Archiwum jest niekompletne: 26 z 54 lekcji, 4 pliki to pusty szablon. W optymalizacji strategii i ocenie modeli alpha jest już dalej niż kurs.
- **Kurs AI\_devs 4 (reszta repo lessons): nic o tradingu ani statystyce.** Wartość jest w sposobie pracy: \~12 konkretnych wskazówek dla `CLAUDE.md`, `runs/INDEX.md` i przyszłych komponentów LLM. Kurs sam mówi, że LLM nie powinien tworzyć raportów, na których opiera się ważne decyzje — zgodnie z zasadą alpha.
- **Sigma:** wynik bramki trendu (AUC 0,84) to artefakt budowy etykiety — sam bieżący ADX daje 0,91 na czysto losowych danych. Wartość sigmy to 7 wytycznych dla alpha, nie kod.
- **Duplikat:** lokalne foldery `lessons` i `4th-devs` to dwie kopie tego samego zdalnego repo.

## Co jest w repo lessons

| Folder | Co zawiera | Kto to napisał | Znaczenie dla alpha |
| --- | --- | --- | --- |
| `maths/` | Kurs Tokenomia, Moduł 3: 26 lekcji, indeks, podsumowanie pobrania | Cudzy materiał, pobrany automatycznie | Średnie — część „Tokenomia” poniżej |
| `01_01_*` … `05_04_*` (52 foldery) | Przykładowy kod kursu AI\_devs 4 (Node.js/TypeScript): wywołania modelu, narzędzia, MCP, RAG, agenci, ewaluacje, UI | Autorzy kursu | Wzorce do przeczytania, nie do kopiowania |
| `aidev4/` | 25 pełnych tekstów lekcji AI\_devs 4 (komplet) + 14 transkrypcji krótkich filmów | Autorzy kursu | Główne źródło części „AI\_devs 4” |
| `answers/` | Twoje rozwiązania 20 zadań (s01e05–s05e05) + asystent `timetra`: skrypty, logi, `notes.md`, `tech_solution.md` | Ty (z pomocą AI) | Niskie (zadania kursowe), dobry warsztat |
| `answers/preferences.md` | Twój workflow do każdej lekcji | Ty | Niskie |
| `ideas/` | Dwie Twoje analizy: architektura kursu i wnioski z zadań (z częścią o tradingu i QuantConnect) | Ty (z pomocą AI) | Średnie |
| `mcp/` | Trzy serwery MCP z kursu | Autorzy kursu | Brak |
| `files/` | **Dwa pliki z kluczami API** — śledzone przez git | Ty | Problem bezpieczeństwa |
| `README.md`, `METHODOLOGY.md`, `REPOSITORIES_GUIDE.md` | Instrukcja kursu; opis repo; przegląd Twoich 13 repozytoriów | Kurs / Ty z AI | Brak |

**Duplikat:** lokalny `4th-devs` ma te same 52 foldery, te same teksty lekcji i `answers/`, a jego `.git` wskazuje na to samo zdalne repo `piotrgebala/lessons` (gałąź `main`, a `lessons` używa `master`). Materiał z `maths/` nie ma odpowiednika w żadnym innym repo.

## Tokenomia: folder maths rozdział po rozdziale

Prawdziwa treść jest w około 13 plikach po 3–7 KB. Pozostałe to krótkie zarysy albo szablon. Podsumowanie pobrania deklaruje 54 lekcje, a w repo jest 26. `METHODOLOGY.md` też podaje 26.

| Rozdział | Pliki / lekcje w kursie | Co zawiera | Przydatność dla alpha |
| --- | --- | --- | --- |
| 1. Suplement z programowania | 1 / 1 | Krótki zarys | Brak |
| 2. Wprowadzenie | 2 / 4 | Zwrot, ryzyko, Sharpe, statystyka, korelacja | Niska: podstawy, które alpha ma |
| 3. Wycena instrumentów | 4 / 6 | Black-Scholes, greki, hedging, Monte Carlo | Średnia: Monte Carlo do D1, BS do zrozumienia DVOL |
| 4. Q&A | 0 / 3 | Brak plików | Brak |
| 5. Zarządzanie ryzykiem | 3 / 5 | VaR, Expected Shortfall, aksjomaty miary ryzyka, przykłady na ETH | **Wysoka: D1 teraz** |
| 6. Optymalizacja portfela | 2 / 4 | Markowitz, granica efektywna, wagi z ograniczeniami | Niska teraz, przyda się przy koszyku carry |
| 7. Q&A | 0 / 3 | Brak plików | Brak |
| 8. Modelowanie stochastyczne | 3 / 4 | Proces Wienera, GBM, prognozowanie ceny | Średnia: GBM jako generator kontroli negatywnej |
| 9. Algorytmy handlowe | 2 / 4 | **Oba pliki to pusty szablon** | Brak |
| 10. Q&A | 0 / 3 | Brak plików | Brak |
| 11. Budowa własnego modelu | 6 / 7 | Pojęcia ML, metryki, zarys walidacji; 1 plik pusty | Średnia: poprawne definicje, mylące metryki |
| 12. Własna strategia | 3 / 5 | Optymalizacja parametrów; 1 plik pusty | **Ujemna: przepis na błąd sigmy** |
| 13. Q&A | 0 / 3 | Brak plików | Brak |
| 14. Egzamin | 0 / 2 | Brak plików | Brak |

Puste pliki szablonu to: rozdział 9 (oba), rozdział 11 „Wykład 7” i rozdział 12 „Pliki”. Wszystkie mają identyczny tekst ogólnikowy zamiast treści lekcji. W 8 plikach nagłówki mają uszkodzone polskie znaki („Modu?” zamiast „Moduł”).

## Tokenomia: co przenieść do alpha

Najważniejsze jest Expected Shortfall liczone z historii, a nie z rozkładu normalnego. Widzą to już liczby samego kursu dla ETH: przy 99% rozkład normalny daje średnią stratę w najgorszych dniach 1 458 USD, a historia 2 080 USD, czyli o 43% więcej.

| Narzędzie z kursu | Etap alpha | Po co |
| --- | --- | --- |
| Expected Shortfall, metoda historyczna (rozdz. 5) | D1 teraz | Miara ryzyka krótkiej nogi carry. Rozkład normalny zaniża skrajne ruchy, które wywołują likwidację |
| Aksjomaty miary ryzyka (rozdz. 5) | D1 teraz | Uzasadnienie wyboru ES zamiast VaR. VaR nie jest subaddytywny, ES jest, a carry to dwie nogi naraz |
| Monte Carlo na ścieżkach (rozdz. 3) | D1 teraz | Likwidacja zależy od największego wybicia w oknie, nie od zwrotu końcowego. Losowanie bloków historii daje rozkład takich wybić |
| Proces Wienera i GBM (rozdz. 8) | Przyrząd pomiarowy | Generator danych bez żadnej informacji o przyszłości do kontroli negatywnej: pipeline musi na nich dać około 50% |
| Black-Scholes (rozdz. 3) | Przyszła seria na danych DVOL | Pojęcie zmienności implikowanej, potrzebne do hipotezy o premii za zmienność (VRP) z kolejki P3 |
| Markowitz z ograniczeniami (rozdz. 6) | Koszyk carry ETH/SOL/BNB (zasada 9) | Wagi z limitem udziału. Lepiej wariant minimalnej wariancji albo równe wagi niż maksymalny Sharpe |

Dwa zastrzeżenia. Losowanie bloków historii nie wytworzy ruchu gorszego od najgorszego historycznego. Kontrolę negatywną lepiej generować z grubymi ogonami (t-Studenta albo bootstrap), bo czysty GBM ma cienkie ogony.

## Tokenomia: czego NIE przenosić

Pięć praktyk z kursu stoi w sprzeczności z tym, czego nauczyły rundy alpha.

| Praktyka z kursu | Dlaczego nie | Źródło w alpha |
| --- | --- | --- |
| Optymalizacja parametrów pod Sharpe lub CAGR: brute force, algorytm genetyczny, Bayes (rozdz. 12) | Wybór najlepszej z wielu prób sam tworzy pozorny wynik. Kurs o tym milczy. Sigma sprawdziła 180 kombinacji na zbiorze testowym i dostała Sharpe 3,49 znikąd | Licznik wariantów, zasada 11; retrospektywa sigmy |
| Trafność i F1 jako miara dobrej strategii (rozdz. 11) | Więcej wygranych nie oznacza więcej pieniędzy, gdy wygrane są małe, a straty pełne | W1, N1 |
| „Przy niedouczeniu dodaj cech albo złożony model” (rozdz. 11) | Przy słabym sygnale to prosta droga do przeuczenia | Zasada 4 (jedna cecha na raz) |
| Sharpe powyżej 1 jako próg sukcesu (rozdz. 2) | Bez przedziału ufności i liczby transakcji ta liczba nic nie mówi. Było to kryterium sigmy | C2.12 (per-fold Sharpe odrzucony) |
| Dobór okna danych, które „najlepiej odzwierciedla obecną sytuację” (rozdz. 8) | To ukryty stopień swobody, czyli dopasowanie do wyniku | Zasada 20 (stała baza danych od 2021) |

Kurs w kilku miejscach ma rację. Poprawnie definiuje rozdział na zbiór treningowy, walidacyjny i testowy: sigma złamała tę zasadę w kodzie, kurs jej nie łamie. Nazywa też przeciek danych, survivorship bias i look-ahead oraz przypomina, że istotność statystyczna to nie to samo co znaczenie praktyczne.

## Tokenomia: błędy i luki w materiale kursu

### Błędy merytoryczne

| Co mówi kurs | Dlaczego to problem | Co z tego dla alpha |
| --- | --- | --- |
| Rozkład normalny jako domyślne założenie przy VaR/ES | Liczby z samego kursu: ES 99% z rozkładu normalnego = 1 458 USD, z historii = 2 080 USD, czyli **+43%**. Dla VaR 99% różnica to +13%. Krypto ma grube ogony — rozkład normalny zaniża straty w złych dniach. | Ryzyko liczymy z danych historycznych (ES historyczny), nie z wzoru normalnego. |
| Stablecoin jako „pieniądz bez ryzyka” (przykład w Ch05, przy własności przesunięcia) | Kontrprzykłady: UST w 2022 (upadek do zera), USDC w marcu 2023 (chwilowy spadek do \~0,88 USD). | Carry rozliczane w USDT ma własne ryzyko stablecoina — w D1 porównujemy je z bonem skarbowym, więc to ryzyko trzeba nazwać wprost. |
| Etykiety percentyli w historycznym VaR zamienione miejscami | Same kwoty są przypisane dobrze, tylko opisy się pomyliły — łatwo się pomylić przy przepisywaniu. | Przy przenoszeniu wzoru sprawdzić na liczbach, nie na opisach. |
| Prognoza ceny ETH z modelu GBM (średnia 0,18%/dzień, odchylenie 3,37%) | Z roku danych statystyka t ≈ 1,0 — średnia nie odróżnia się od zera. Żeby znać średnią z dokładnością ±0,05%/dzień, potrzeba ok. **17 450 dni (\~48 lat)**. Dryf w tej prognozie to szum. | GBM nadaje się jako generator danych „bez przewagi” (kontrola negatywna), nie jako prognoza. |

### Luki — czego kurs w ogóle nie uczy

Żaden z pobranych rozdziałów nie obejmuje tematów, na których stoi alpha:

- mechaniki kontraktów perpetual i funding rate,
- depozytu zabezpieczającego, dźwigni i likwidacji,
- kosztów maker/taker i poślizgu,
- wielokrotnego testowania i błędu selekcji (czyli dlaczego „najlepszy z 180 wariantów” zwykle jest przypadkiem),
- mocy testu (ile danych trzeba, żeby w ogóle coś wykryć),
- tego, że pozycja neutralna cenowo (delta-neutral) **nie jest** neutralna wobec depozytu — jedna noga może zostać zlikwidowana, zanim druga zarobi.

### Stan samego archiwum

- Pobrane **26 z 54** lekcji — brakuje ponad połowy, w tym całych rozdziałów 4, 7, 10, 13 i 14.
- **4 pliki to wypełniacze** (oba w Ch09, „Wykład 7” w Ch11, „Pliki” w Ch12) — bez treści merytorycznej.
- **8 plików ma zepsute polskie znaki** (mojibake) — czytelne, ale trudne do przeszukiwania.

## Tokenomia: rekomendacja

**Czy to będzie przydatne? Tak, ale wąsko.** Kurs uczy narzędzi (jak mierzyć ryzyko, jak symulować), a nie tego, skąd bierze się przewaga na rynku. Nie będzie więc źródłem nowych hipotez dla alpha.

| Priorytet | Co | Kiedy |
| --- | --- | --- |
| Teraz | **Ch05 (miary ryzyka)** — ES historyczny zamiast normalnego, spójne miary ryzyka | Przy D1 (analiza ryzyka produktu carry) |
| Jako narzędzia | **Ch03 i Ch08** — symulacje Monte Carlo po ścieżce ceny, GBM jako generator danych bez przewagi | Przy testach ryzyka likwidacji i kontrolach negatywnych |
| Później | Markowitz — tylko jeśli powstanie koszyk kilku strategii carry | Nie wcześniej niż po D1 |
| Jako podstawy | Reszta rozdziałów | Ściąga pojęć, nie autorytet metodologiczny |

### Porządki w folderze maths (opcjonalnie)

1. Jeśli masz jeszcze dostęp do platformy — pobrać brakujące **28 lekcji**, szczególnie rozdziały 4, 7, 10, 13 i 14.
2. Usunąć albo oznaczyć **4 pliki-wypełniacze**, żeby nie myliły przy wyszukiwaniu.
3. Naprawić kodowanie w 8 plikach z zepsutymi polskimi znakami.

### Co ewentualnie dopisać do alpha

Dwa krótkie akapity do `docs/rag/03_ryzyko_i_sizing.md`: (a) ES liczony z historii, nie z rozkładu normalnego, (b) ryzyko stablecoina jako osobna pozycja w carry. **Nie w tej sesji** — obowiązuje zasada „niczego nie nadpisujemy”; najlepiej przez sesję w VS Code, po Twojej zgodzie.

## AI\_devs 4: folder po folderze

### Przykładowy kod kursu (52 foldery)

| Moduł | Temat | Przykłady ważne dla alpha |
| --- | --- | --- |
| 01 | Podstawy: wywołania modelu, JSON Schema, narzędzia, MCP, multimodalność, pierwszy agent | `01_01_structured` (wymuszony format odpowiedzi), `01_05_confirmation` (człowiek zatwierdza akcję) |
| 02 | RAG, dzielenie tekstu, wyszukiwanie hybrydowe, grafy, pamięć | `02_05_agent` — wzorzec Observer/Reflector (kompresja historii w obserwacje i refleksje) |
| 03 | Ewaluacje, obserwowalność, piaskownica do kodu, przeglądarka, Gmail | `03_01_evals` (testy odpowiedzi modelu), `03_03_*` (hooki w cyklu życia agenta) |
| 04 | Baza wiedzy w Markdown, agent recenzujący dokumenty, MCP Apps | `04_01_garden` (baza wiedzy), `04_05_review` (komentarze zakotwiczone w tekście + akceptuj/odrzuć) |
| 05 | Graf agentów, głos, automatyczna optymalizacja promptów, pełna platforma API+UI | `05_03_coding` (`maybeCompactMemory` — kompresja przy progu) |

Kod jest w Node.js/TypeScript, a alpha w Pythonie — to wzorce do przeczytania, nie do skopiowania.

### `aidev4/` — teksty lekcji

- **Komplet 25 lekcji**, czyste kodowanie UTF-8, bez duplikatów (sprawdzone sumami kontrolnymi).
- **14 krótszych plików (`AID4_*`, `SxxEyy.md`) to transkrypcje filmów**, nie Twoje notatki. 5 z nich to surowe napisy z błędami rozpoznawania mowy (np. „Antropic”, „Cloda”). Prawdopodobnie 2–3 mają złą nazwę (np. `S05E02.md` cytuje lekcję S03E02) — to wniosek z treści, nie pewnik.
- Dużo treści jest na obrazkach, których w plikach nie ma. Ok. 20–35% każdej lekcji to fabuła i zadanie, bez wartości dla alpha.

### `answers/` — Twoje rozwiązania

- Spójny, dobry warsztat: w każdym zadaniu notatka z lekcji, opis zadania, logi z czasem i poziomem, ponawianie z wydłużonym odstępem (1 s / 2 s / 4 s), `tech_solution.md`.
- Twoja obserwacja z `ideas/`: **większość zadań rozwiązał zwykły kod** (grep, BFS, Dijkstra), a LLM był potrzebny rzadko. Ta sama lekcja pasuje do alpha.
- W `s03e01` było zadanie z wykrywaniem anomalii — to jedyny przykład bliski analizie danych.

### `ideas/` — Twoje analizy

- **Architektura kursu** — rzetelne podsumowanie wzorców (pętla agenta, pamięć, bezpieczeństwo, MCP).
- **Wnioski z zadań + trading** — część o QuantConnect/LEAN jest zgodna z decyzją w alpha (`docs/rag/04`). Ale szkic „agenta tradingowego” stawia **LLM w modelu decyzyjnym** (sentyment z newsów → KUP/SPRZEDAJ). Alpha świadomie tego nie robi, więc tego fragmentu nie przenosić. Dobre zdanie z tej notatki: „ewaluacja offline jest tu obowiązkowa, nie opcjonalna”.

## AI\_devs 4: co przenieść do alpha

| # | Wskazówka (prostym językiem) | Źródło | Gdzie w alpha | Kiedy |
| --- | --- | --- | --- | --- |
| 1 | **Mniej, ogólniejszych reguł.** Przy długich instrukcjach model zaczyna pomijać część z nich. Krzyk typu CRITICAL/MUST nie jest już zalecany. | S02E02, S05E03 | `CLAUDE.md` (\~20 reguł): scalić i uogólnić; szczegółowa checklista w skillu `clas5-runda` | Teraz |
| 2 | **Bez statusu i wyników w instrukcjach.** Postęp projektu miesza modelowi chronologię. Nie wspominać narzędzi, których w danym środowisku nie ma — model zachowuje się, jakby były. | S02E01, S05E04 | `CLAUDE.md`: status tylko w `STATUS.md`; sekcje „tylko lokalnie” / „tylko w chmurze” | Teraz |
| 3 | **Dziennik + osobne wnioski.** Surowy dziennik tylko dopisujemy; wnioski to osobny, krótki plik z limitem rozmiaru, zatwierdzany przez człowieka. Kompresja = zapominanie, więc stare wersje do archiwum. | S02E03, S04E04 | `runs/INDEX.md` (86 KB, 60 wniosków) — to jest podział Observer/Reflector, pre-rejestrowany w `docs/rag/06` | Teraz |
| 4 | **Jeden plik = jeden właściciel.** Dwie sesje piszące do jednego pliku nadpisują się nawzajem. | S02E04 | Każde środowisko pisze tylko do swojego `runs/<id>/`; `runs/INDEX.md` generowany skryptem | Teraz |
| 5 | **Notatki dla czytelnika bez kontekstu:** data, źródło, status (aktywny/zastąpiony), bez „ostatnio” czy „poprzednia wersja” bez linku. | S04E04 | Frontmatter w `docs/rag` i w README runów | Przy okazji |
| 6 | **AI proponuje, człowiek decyduje** o treści i zasadach. Według kursu ok. 60% sugestii modelu do promptu „nie ma sensu”, ok. 30% wymaga poprawek. | S04E04, S02E01 | Zmiany w `CLAUDE.md` i `docs/rag` tylko jako propozycja zmian do akceptacji | Teraz |
| 7 | **Testuj przyrząd pomiarowy.** Test, którego nie da się oblać, jest błędem; AI domyślnie pisze płytkie testy. | S03E01, S03E04 | `test_mathematics`: przypadki, które muszą się nie udać; kontrole negatywne (patrz „Sigma: wytyczne dla alpha”) | Przy następnym kodzie |
| 8 | **Poprawny format ≠ poprawna treść.** W odpowiedzi modelu pole „za mało danych”; kolejność: uzasadnienie → werdykt → pewność. Liczby liczy kod, nie model. | S01E05, S01E01 | Przyszły `post_trade_critic`: każda liczba z odnośnikiem do `runs/` i sprawdzona skryptem | Faza 3 |
| 9 | **Kilka próbek modelu:** rozbieżność to sygnał, ale zgodność to nie dowód (modele mylą się podobnie). | S03E05 | Krytyka od LLM: kilka próbek, przy rozbieżności decyduje człowiek. Nie pytać „do skutku”. | Faza 3 |
| 10 | **Strażnik w kodzie, nie w prośbie.** Hook przed zakończeniem sprawdza wymagane kroki; akceptacja przez kod, nie decyzją modelu. | S03E03, S01E05 | Run nie trafia do `runs/INDEX.md` bez pre-rejestracji, kontroli i podbitego licznika wariantów | Teraz |
| 11 | **Monitoring automatów:** sprawdzać wynik (czy plik jest, rozmiar, kompletność), a nie tylko kod wyjścia; jawna strefa czasowa; blokada z terminem wygaśnięcia. | S04E04 (transkrypcja) | Pipeline danych: świeżość, UTC, liczba świec i luki, blokada przy pobieraniu z dwóch środowisk | Przy danych do O1/X1 |
| 12 | **Koszty API:** tryb wsadowy ok. −50%, stały początek promptu da się cache'ować (ok. 1/10 ceny), data w instrukcji systemowej psuje cache. | S01E01, S04E02 | Tylko jeśli krytyka pójdzie przez API | Faza 3 |

Liczby w punktach 6 i 12 to deklaracje autorów kursu, nie niezależne pomiary.

## AI\_devs 4: czego nie przenosić, błędy i problemy

### Poza tematem alpha

| Temat | Dlaczego nie |
| --- | --- |
| Obrazy, wideo, głos, transkrypcja (S01E04, S05E02) | Alpha pracuje na liczbach, nie na mediach |
| Czat, generatywne UI, MCP Apps (S03E05, S05E04) | Alpha nie ma interfejsu użytkownika |
| Agenci do Gmaila, kalendarza, przeglądarki (S03E02–S04E03) | Inne zastosowanie |
| Bazy wektorowe i grafy wiedzy (S02E02, S04E01) | Przy bazie wiedzy alpha wystarczy wyszukiwanie tekstu — kurs sam to przyznaje w S05E02 |
| Budowa serwerów MCP, OAuth, VPS (S01E03, S01E05) | Niepotrzebne w fazie badań |
| LLM jako źródło sygnału (szkic w `ideas/`) | Sprzeczne z decyzją alpha: LLM tylko offline i nadzorczo |

### Błędy względem dobrej praktyki statystycznej

- **Optymalizacja promptu 60% → 90%** (S05E03): „zachowaj, jeśli lepiej” na 2 przykładach, sprawdzone na 1. To dopasowanie do szumu — ten sam błąd co wybór najlepszego ze 180 wariantów w sigmie i optymalizacja z rozdz. 12 Tokenomii.
- **Wybór modelu na kilku testach** (S03E04): „skuteczność perfekcyjna” bez powtórzeń i bez miary niepewności.
- **„3+ źródła = wysoka pewność”** (S01E02): ignoruje to, że źródła często powtarzają się nawzajem.
- **Progi ewaluacji bez liczby przypadków i przedziałów ufności** (S03E01).
- **Liczby bez źródła** (np. „cztery pytania wyłapią 90% problemów”) i **korelacja podana jak przyczyna** („routing daje 3× więcej wdrożeń”).
- Drobny błąd faktograficzny: „RAG – Retrieval Agentic Generation” (S02E01) — poprawnie Retrieval-Augmented Generation.

### Bezpieczeństwo i porządek w repo lessons

| Problem | Co sprawdziłem | Co zrobić |
| --- | --- | --- |
| **Klucze API w git** | `files/aidevsapikey.txt` i `files/gpt4o apykey.txt` są w indeksie git w **obu** folderach (`lessons` i `4th-devs`). `.gitignore` wyklucza tylko `.env`, `node_modules/` itp. Zawartości kluczy nie otwierałem. | 1) Unieważnić oba klucze u dostawców i wygenerować nowe. 2) Dodać `files/` do `.gitignore` i zdjąć z śledzenia (`git rm --cached`). 3) Jeśli repo jest publiczne — usunąć z historii (np. `git filter-repo`); sam nowy commit nie wystarczy. |
| **Duże pliki w git** | 2 filmy po \~18 MB, log 18 MB (`answers/s03e02`), `raw_signals.json` 1,8 MB | Logi i dane surowe do `.gitignore`; zostawiać tylko kod i notatki |
| **Dwie kopie jednego repo** | `lessons` (gałąź `master`) i `4th-devs` (gałąź `main`) wskazują na `piotrgebala/lessons` | Zostawić jedną kopię lokalną, żeby zmiany nie rozjeżdżały się między gałęziami |
| Hasła do paneli kursu w notatkach | W `answers/` są loginy do ćwiczeniowych paneli kursu | Niskie ryzyko (konta szkoleniowe), ale lepiej nie trzymać haseł w notatkach |

## Sigma: co wykazała weryfikacja

Sigma to wcześniejszy projekt z tym samym pomysłem co alpha: najpierw „bramka” dzieli rynek na trend i konsolidację, potem drugi model zgaduje kierunek. Sprawdziłem kod i wyniki na liczbach, w tym test na **czysto losowych danych** (20 przebiegów, 11 353 świec, bez żadnej informacji o przyszłości).

| Co | Wynik sigmy | Co pokazał test | Wniosek |
| --- | --- | --- | --- |
| Bramka trend/konsolidacja | AUC 0,84 na teście (CV 0,86) | Na losowych danych sam **bieżący ADX, bez żadnego uczenia**, daje AUC **0,91** (zakres 0,90–0,92) | Wynik bramki to artefakt budowy etykiety, nie wiedza o rynku |
| Model kierunku (long/short) | AUC 0,538 | Na losowych danych 0,49 (zakres 0,43–0,52) | Ledwo powyżej rzutu monetą — za słabe, żeby pokryć koszty |
| Backtest | 27 transakcji, Sharpe −4,1, trafność 37%, profit factor 0,54, wynik −7,2% | — | Brak przewagi; „alpha +5%” to tylko mniejsza strata niż kup-i-trzymaj (−12,2%). 27 transakcji to i tak za mało na jakikolwiek wniosek |

### Dlaczego bramka „wyglądała” tak dobrze

Etykieta „trend” jest liczona z **przyszłego** ADX (ADX za 5 świec). ADX to średnia wygładzona (EWM 1/14), więc ok. **69%** jego wartości za 5 świec to po prostu dzisiejszy stan. Model „przewiduje” więc głównie coś, co już widzi. To nie jest klasyczny wyciek danych w cechach — wyciek siedzi w **definicji etykiety**.

### Trzy dodatkowe problemy w procesie

- **Optymalizacja etykiety pod wynik.** Optuna (300 prób) szuka też parametrów samej etykiety i daje premię za AUC powyżej 0,80 — czyli nagradza właśnie ten artefakt.
- **Dobór parametrów na zbiorze testowym.** `auto_backtest.py` sprawdza 180 kombinacji (6 progów × 5 mnożników ATR × 6 poziomów take-profit) na danych testowych i wybiera najlepszą po Sharpe. Przy 180 próbach bez żadnej przewagi rzędu 9 przejdzie próg p<0,05 czysto przez przypadek (kombinacje są skorelowane, więc to przybliżenie). Taki „najlepszy wynik” nie jest już wynikiem testowym.
- **Automatyczne wdrażanie.** `auto_optimize.py --deploy` sam podmienia parametry w `main.py` i robi `git push` — bez przeglądu człowieka, na podstawie wyniku wybranego z testu.

## Sigma: wytyczne dla alpha

| # | Wytyczna | Po co |
| --- | --- | --- |
| 1 | **Etykieta tylko z przyszłej ceny** (zwrot po kosztach, bariery). Nigdy z przyszłej wartości wygładzonego wskaźnika (ADX, średnie, zmienność EWM). | Inaczej model „przewiduje” dzisiejszy stan wskaźnika — jak bramka sigmy |
| 2 | **Kontrola negatywna na losowych danych** przy każdej nowej etykiecie lub klasyfikatorze: ten sam kod, dane bez przewagi (spacer losowy z grubymi ogonami). Oczekiwane AUC ≈ 0,5; wyraźnie więcej = szukać artefaktu, zanim spojrzymy na prawdziwe dane. | Uzupełnia kontrolę pozytywną K1 — razem sprawdzają, czy narzędzie pomiarowe działa w obie strony |
| 3 | **Parametry etykiety ustalone w pre-rejestracji**, nie optymalizowane. Zakaz nagradzania wysokiego AUC w optymalizacji. | Optymalizacja etykiety pod AUC wzmacnia artefakty zamiast przewagi |
| 4 | **Zbiór testowy użyty raz.** Wybór parametrów tylko na walidacji; każda sprawdzona kombinacja wchodzi do licznika wariantów. | „Najlepszy ze 180 na teście” to błąd selekcji, nie wynik |
| 5 | **Minimalna liczba transakcji i N\_eff przed wnioskiem.** | 27 transakcji sigmy nie pozwala nic stwierdzić — ani plusa, ani minusa |
| 6 | **Przewaga = dodatni wynik po kosztach z przedziałem ufności**, nie „lepiej niż kup-i-trzymaj”. | Mniejsza strata w spadkach to nie przewaga |
| 7 | **Człowiek zatwierdza każdą zmianę parametrów.** Żadnego automatycznego wdrażania ani `git push` z pętli optymalizacji. Nie uruchamiać `auto_optimize.py --deploy` w sigmie. | Automat wdrożyłby wynik dobrany na teście — najgorsze połączenie |

### Co dalej z sigmą

Nie rozwijać jej osobno — zostawić jako archiwum. Wartość sigmy to te wytyczne, nie kod. Wytyczne 1–3 to kandydaci do `docs/skills/bramki-jakosci.md` (sekcja C, przegląd kodu — wyciek w definicji etykiety) i do opisu kontroli w `runs/`. **Nie w tej sesji** — dopisanie do repo alpha przez sesję w VS Code, po Twojej zgodzie.

## Wspólny plan działań

1. **Dziś, poza alpha:** unieważnić dwa klucze API i zdjąć `files/` ze śledzenia w git.
2. **Teraz, przy D1:** ES historyczny zamiast normalnego i ryzyko stablecoina jako osobna pozycja (Tokenomia, rozdz. 5).
3. **Przed kolejną rundą (O1):** z AI\_devs punkty 1–4, 6 i 10 — odchudzenie `CLAUDE.md`, podział `runs/INDEX.md` na dziennik i wnioski, jeden właściciel pliku, strażnik w kodzie przed wpisem do indeksu. Do tego wytyczne sigmy 1–3 w `docs/skills/bramki-jakosci.md`.
4. **Przy następnym kodzie testowym:** kontrola negatywna na losowych danych z grubymi ogonami (sigma 2, Tokenomia rozdz. 8, AI\_devs punkt 7).
5. **Faza 3 (komponenty LLM):** AI\_devs punkty 8, 9 i 12; wtedy warto przeczytać `02_05_agent`, `03_01_evals` i `04_05_review`.
6. **Porządki w repo lessons:** jedna kopia lokalna i jedna gałąź główna; logi, dane surowe i media do `.gitignore`; poprawić nazwy 2–3 transkrypcji; w `REPOSITORIES_GUIDE.md` zaktualizować opis sigmy („TBD”) i liczbę lekcji Tokenomii (jest 54, faktycznie pobranych 26).

Zmiany w repo alpha najlepiej zrobić w sesji VS Code, po Twojej zgodzie. W tej sesji **niczego w repo alpha nie nadpisuję**.
