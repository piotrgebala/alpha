# AU3 — naprawa kanonicznego N_eff i audyt dawnych werdyktów (2026-09-25)

> **STATUS: ZAMKNIĘTA — błąd naprawiony; ŻADEN dawny werdykt się nie zmienia.** Na 59 przebiegów
> zamrożonych rund błąd wystąpił tylko w dwóch rundach kalibracyjnych (K2: 19/99 wywołań, K3: 1/4), a ich
> wydruki przed i po naprawie są identyczne (N_eff nie trafiało tam do werdyktu). Rundy od W2 odtwarzają się
> na serwerze co do liczby. Audyt — 0 wariantów. Walidacja (16a): **Ready**; przegląd (16c): **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

AU2 wykazał błąd we wzorze, którym projekt liczy „ile naprawdę niezależnych obserwacji” ma wynik (N_eff).
Na krótkich szeregach wzór potrafił dać liczbę ujemną, a program zamieniał ją na 1 — i wtedy prawdziwy
wynik wyglądał na nierozstrzygnięty. Naprawiamy wzór w jednym miejscu i sprawdzamy WSZYSTKIE dawne
rundy: w których ten błąd w ogóle wystąpił i czy zmienia to ich werdykt. Błąd mógł tylko zaniżać
pewność, więc zmienić mogą się wyłącznie werdykty „nierozstrzygnięty” (albo sam zapis liczb t_neff).

## ID testu

**AU3** — audyt przyrządu (jak AU1). Następca AU2 kroków 1–2 (wniosek 93).

## Metadane

- Branch `au3-naprawa-neff` (z `master` `014d627`).
- **Naprawa:** `agents/labeling.py::effective_sample_size` — gdy `1 + 2Σρ ≤ 0`, N_eff = n (zamiast ujemnego).
  Wywołujący (`carry_hedged.summarize_pnl`: `max(1, min(N_eff, n))`, `checkpoint_lib.summarize_trade_returns`:
  `min(N_eff, n)`) bez zmian. Testy: `tests/test_neff_au3.py` (regresja + test właściwości `hypothesis`:
  N_eff > 0 i skończone, |t_neff| ≤ |t|), `tests/test_au3_audit.py`.
- **Audyt:** `tools/au3_audit.py` — 55 komend uruchomienia skryptów `backtest/…` z README rund, filtr: skrypt sięga po N_eff
  (tekst lub import, rekurencyjnie); bez `run_au2_ml` (własna pula procesów; błąd obsłużony w AU2).
  Każdy skrypt w osobnej kopii roboczej (`git worktree`, dane podlinkowane), 1 wątek numeryczny, ≤ 20 naraz,
  limit 45 min. Tryb `old` = wzór sprzed AU3 + licznik wywołań z mianownikiem ≤ 0; tryb `new` (tylko gdy licznik > 0)
  = wzór naprawiony. Komenda: `py tools/au3_audit.py exec <worktree> runs/2026-09-25_au3-audyt-neff/logi`.
- Dziennik papierowy: moduł `labeling` jest importowany pośrednio (`run_coinbase_cp1` → `carry_hedged`), ale
  dziennik nie liczy N_eff — jego wyniki się nie zmieniają; wpis „Poprawka 6” w `dziennik/README.md`.

## Poprzedzające wyniki

- **AU2 kroki 1–2 (93):** błąd odtworzony (N_eff = −990 → 1); ~25–30 % przebiegów kalibracji dotkniętych.
- **Wniosek 50 (A1, Poprawka 2):** N_eff ≤ n — korekta tylko odejmuje pewność; naprawa jest z nim zgodna.
- **AU1 (87):** poprzedni audyt metodologii — nie wykrył tego błędu (dotyczył obliczeń na konkretnych danych).

## Pre-rejestracja

- **Pytanie:** które zamrożone rundy wywołały N_eff z mianownikiem ≤ 0 i czy po naprawie zmienia się ich werdykt?
- **Odczyt per skrypt:** (a) licznik `bad_denominator` w trybie `old`; 0 → wynik rundy nietknięty (koniec);
  (b) > 0 → porównanie wydruków `old` vs `new`: linie z t_neff / werdyktem („ODCZYT KRYTERIUM”, „POZYTYWNY”,
  „NEGATYWNY”, „NIEROZSTRZYGNIĘTY”, GO/NO-GO).
- **Reguła:** werdykt zmieniony → korekta wniosku w `runs/INDEX.md` (dopisek „[korekta AU3]”) i w README rundy
  NIE (skrypty i README zamrożonych rund zostają; korekta tylko w INDEX i w tym README). Nowy POZYTYWNY =
  odczyt z zastrzeżeniem multiple testing jak w oryginalnej rundzie (licznik rundy bez zmian — to nie nowy wariant).
- **Kontrola odtwarzalności przy okazji:** wydruk `old` porównany z `raw_output` rundy (inne wersje bibliotek
  albo dane na serwerze → różnice opisowo).
- **Czego runda NIE robi:** nie zmienia kryteriów werdyktów, nie stroi niczego, nie przelicza rund bez zdarzeń.

---

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

Błąd we wzorze N_eff jest naprawiony w jednym miejscu. Sprawdziliśmy każdą dawną rundę, którą da się
uruchomić z jej README (59 przebiegów). Błąd pojawił się tylko w dwóch rundach technicznych (K2, K3)
i w żadnej nie wpłynął na wynik — liczby przed i po naprawie są identyczne. **Wszystkie dotychczasowe
werdykty projektu zostają.** Błąd był groźny głównie dla krótkich szeregów tygodniowych (jak w AU2),
których w starszych rundach prawie nie było; od teraz takie szeregi są liczone poprawnie.

## Wynik

Logi: `logi/*.log` (wydruk każdego przebiegu), `logi/wyniki.json` + `logi/wyniki_dodatkowe.json` (liczniki),
`raw_output.txt`, `raw_output_dodatkowe.txt`.

| co | liczba |
|---|---|
| komendy skryptów z README rund sięgające po N_eff | 54 (+ 5 z argumentami tekstowymi, doliczone po poprawce parsera) |
| przebiegi trybu `old` zakończone | 59 (2 pierwsze próby z błędnie odczytanym argumentem zastąpione dodatkowymi) |
| **przebiegi z mianownikiem ≤ 0** | **2: K2 `run_abstention_fix_k2` (19 z 99 wywołań), K3 `run_measurability_k3` (1 z 4)** |
| różnice wydruku `old` → `new` w tych dwóch | **0** (poza czasem działania) |
| zmienione werdykty | **0** |

**Odtwarzalność (opisowo, zgodność liczb w wydruku `old` z `raw_output` rundy):** wszystkie rundy od W2
(baza od 2021, zasada 20) — 100 %, poza A1/A2/W1/N1/T4 96–99 % (drobne liczby). Rundy Fazy 0 sprzed W2
(C2.x, H2.1, H3, S1, Z19, K1) — 2–46 %: na serwerze działa już globalny filtr danych od 2021 i nowsze dane,
więc stare liczby się nie odtwarzają (CLAUDE.md: nie porównuje się ich 1:1). KP1 `--profil` i SW — porównanie
z innym plikiem wyjściowym rundy (nie różnica).

## Co na plus (+) / Co na minus (−)

**(+)**
- Naprawa w jednym miejscu (`effective_sample_size`), zgodna z wnioskiem 50; test regresji (−6 080 → n) i test
  właściwości `hypothesis` (N_eff > 0, skończone, |t_neff| ≤ |t|).
- Audyt mechaniczny, nie „z pamięci”: licznik zdarzeń w każdym przebiegu, porównanie wydruków przed/po;
  osobna kopia robocza — artefakty rund nietknięte.
- Przy okazji: potwierdzona odtwarzalność rund od W2 na serwerze Linux (100 %).

**(−)**
- **Kogo nie ma w audycie:** `run_au2_ml` (błąd obsłużony w samej AU2), skrypty bez komendy w README,
  analizy robione ręcznie w sesjach (np. walidacje `walidacja.py` — nie liczą N_eff z tej funkcji albo nie
  są komendą rundy); stare rundy Fazy 0 nie odtwarzają się na dzisiejszych danych, więc dla nich audyt
  sprawdza przebieg na dzisiejszych danych (0 zdarzeń), nie na historycznych.
- Pierwszy parser komend gubił argumenty tekstowe (G1/L1/V1/1h/1d) — wykryte po pierwszych logach, poprawione,
  test dopisany, przebiegi doliczone.

## Walidacja (16a), statystyka (16b), przegląd (16c)

`data:validate-data`: druga droga = porównanie całych wydruków `old`/`new` (niezależne od licznika) — zgodne
z licznikiem (różnice tylko tam, gdzie licznik > 0, i nawet tam 0 w wynikach); kogo nie ma — wyżej. **Ready.**
`data:statistical-analysis`: runda liczy zdarzenia, bez wnioskowania; efekt naprawy dotyczy wyłącznie przypadków
z mianownikiem ≤ 0. `engineering:code-review` (samodzielnie): naprawa zmienia wynik tylko przy mianowniku ≤ 0
(test „old = new” dla zwykłego szeregu); podmiana funkcji w audycie przed importem skryptu (inaczej `from … import`
związałby starą wersję); wyjście do osobnej kopii roboczej; Poprawka 6 w dzienniku. **Werdykt jednym zdaniem:
Approve** — minimalna, przetestowana zmiana wzoru, a audyt pokazał, że nie zmienia ona żadnego zapisanego werdyktu.

## Wniosek

**Prostym językiem:** wzór jest naprawiony, a wszystkie dawne wyniki projektu zostają ważne.

**Technicznie:** `effective_sample_size`: mianownik ≤ 0 → N_eff = n. Audyt 59 przebiegów: zdarzenia tylko w K2/K3,
wydruki identyczne, 0 zmienionych werdyktów. Błąd dotyczył praktycznie tylko krótkich szeregów (AU2: 221 tygodni).

## Rekomendacja

1. Nic nie korygować w dawnych wnioskach (0 zmian); wniosek 93 uzupełniony dopiskiem o naprawie.
2. Przy przyszłych szeregach tygodniowych/krótkich — N_eff liczone już poprawnie; w AU2 werdykt „poprawiony”
   jest odtąd zgodny z kanonicznym.
3. `tools/au3_audit.py` zostaje jako narzędzie: każda przyszła zmiana kanonicznego pomiaru → ten sam audyt.

## Użyte skille

Rejestr `runs/skille/au3-naprawa-neff.jsonl`: **6 wczytań, 6 skilli.**

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | pre-rejestracja reguły korekty przed audytem |
| `anthropic-skills:clas5-quant` | zgodność naprawy z wnioskiem 50 (N_eff ≤ n, korekta tylko odejmuje pewność) |
| `engineering:testing-strategy` | regresja + test właściwości `hypothesis` (zasada 10 dla `labeling.py`), testy narzędzia audytu |
| `data:validate-data` | druga droga: porównanie całych wydruków old/new; kogo nie ma w audycie |
| `data:statistical-analysis` | runda zliczeniowa — bez wnioskowania, opis zakresu |
| `engineering:code-review` | przegląd naprawy, podmiany przed importem i izolacji — Approve |

Pominięte z tabeli zasady 19: `engineering:debug` (przyczyna ustalona w AU2), `dataviz` (bez wykresu).
