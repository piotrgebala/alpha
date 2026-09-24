# NC1 — kontrola negatywna przyrządów na danych bez informacji o przyszłości (2026-09-24)

> **STATUS: ZAMKNIĘTA — ZALICZONA.** Silniki TS1, X1 i reguła znaku CP1 na 40 losowaniach danych
> bez informacji o przyszłości dają zwrot brutto ≈ 0 (średnie t −0,12 / +0,17 / −0,20; fałszywe
> alarmy 1, 2 i 1 z 40), a koszty tylko odejmują. Kontrola czułości: celowe zajrzenie w przyszły
> tydzień daje t od +13 do +30 w 40/40 losowań. Pre-rejestracja `433505a`. Walidacja: **READY**;
> przegląd: **Approve**. 0 wariantów.
> Poprzednio: **PRE-REJESTRACJA (przed przebiegiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Sprawdzamy nie strategię, tylko **nasze narzędzia pomiarowe**. Generujemy sztuczne ceny, które
wyglądają jak krypto (duże skoki, spokojne i nerwowe okresy, monety chodzące razem), ale w których
**z definicji nie da się przewidzieć kierunku**. Jeśli nasze silniki (trend tygodniowy, momentum
przekrojowe, reguła znaku premii Coinbase) pokażą na takich danych „zysk”, to znaczy, że gdzieś
w kodzie zaglądają w przyszłość albo źle liczą — a nie, że znalazły przewagę. Dodatkowo psujemy
silnik celowo (każemy mu znać przyszły tydzień), żeby upewnić się, że sprawdzian w ogóle umie
taki błąd złapać.

## Metadane

- Branch `metodyka-kontrole`. Moduł `backtest/negative_control.py` (+ `tests/test_negative_control.py`,
  8 testów); skrypt `backtest/run_negative_control_nc1.py`; komenda
  `PYTHONUTF8=1 py -m backtest.run_negative_control_nc1` → `raw_output.txt`.
- Dane: WYŁĄCZNIE syntetyczne (zasada 20 nie dotyczy — brak świec rynkowych). 40 losowań
  (ziarna 0–39) × 20 monet × 2 000 dni (≈ 5,5 roku, jak baza od 2021).
- Model zwrotów: t-Student df = 3 (grube ogony), GARCH(1,1) α = 0,08, β = 0,90 (grupowanie
  zmienności), wspólny czynnik rynkowy ρ = 0,5, średnia zmienność 4 %/dzień, średnia 0; funding 0;
  koszt 0,09 % obrotu.

## Poprzedzające wyniki

- **K1 (2026-09-22)** — kontrola POZYTYWNA modelu 4h (wyrocznia ze znanym sygnałem) + 6 losowań
  czystego szumu: 0 fałszywych alarmów. Dotyczyła tylko ścieżki model 4h → trafność; silniki
  portfelowe dziennych rund (TS1, X1, CP1, LQ1, SZ1 — wnioski 60–77) takiej kontroli nie miały.
- **TS1 / X1 / CP1** — H0 tych rund to przesunięte w czasie PRAWDZIWE sygnały na PRAWDZIWYCH cenach:
  test „czy ten sygnał jest lepszy od przypadkowego”, ale nie „czy silnik na danych bez żadnej
  informacji daje zero” (np. błąd w dryfie wag zawyżałby oba ramiona po równo).
- **Przegląd SIGMA** (`docs/rag/Repo lessons i sigma — co przydatne dla alpha.md`, wytyczna 2):
  tam brak kontroli negatywnej przepuścił AUC 0,84 z etykiety liczonej z przyszłego wygładzonego
  wskaźnika.

## Pre-rejestracja (zapisana przed przebiegiem)

- **Mierzone:** t_neff (`carry_hedged.summarize_pnl`, N_eff ≤ n) dziennego zwrotu BRUTTO i NETTO
  każdego silnika na każdym losowaniu.
- **Silniki:** TS1 (`ts_momentum.portfolio`, 7 faz), X1 (`xs_momentum.long_short_returns`,
  top/bottom 5 z 20), CP1 (reguła znaku z zewnętrznego szeregu: losowa premia AR(1), φ = 0,9,
  NIEZALEŻNA od cen, średnia 7 − średnia 90 dni, jedna moneta). Model 4h pominięty — kontrolę
  negatywną ma z K1 (6 losowań szumu, 0 alarmów).
- **Kryterium ZALICZENIA (każdy silnik, zwrot brutto):** |średnia t_neff z 40 losowań| < 0,5
  (se średniej ≈ 0,16 przy t ~ N(0,1)) ORAZ liczba losowań z |t| > 1,96 ≤ 5 z 40 (dwumian
  n = 40, p = 0,05: P(X ≥ 6) ≈ 4 %). Netto: średni zwrot ≤ brutto (koszty tylko odejmują).
- **Kontrola CZUŁOŚCI:** TS1 ze znakiem zwrotu NASTĘPNYCH 7 dni (celowe zajrzenie w przyszłość) —
  zaliczenie, gdy t_neff > 5 na każdym losowaniu. Jeśli nie — kontrola negatywna jest ślepa i
  jej zaliczenie nic nie znaczy.
- **Niezaliczenie** = błąd przyrządu do znalezienia PRZED jakąkolwiek dalszą rundą na tym silniku;
  wyniki rund opartych na nim (TS1/TR1/TP1/X1/X2/CP1/LQ1/SZ1) dostają adnotację „do ponownej
  weryfikacji”.
- **Liczniki:** 0 wariantów — test przyrządu, POZA licznikami hipotez (jak K1–K3, T4).

## Wynik

`raw_output.txt` (162 s). Kolumna „t” = t_neff zwrotu dziennego (N_eff ≤ n) w każdym losowaniu.

| silnik | śr. t | sd t | \|t\| > 1,96 | min / max t | śr. zwrot %/rok | kryterium |
|---|---|---|---|---|---|---|
| TS1 brutto | −0,12 | 0,84 | 1/40 | −1,46 / +2,16 | −1,0 | ✓ |
| TS1 netto | −0,33 | 0,86 | 1/40 | −1,72 / +1,97 | −2,7 | ✓ (≤ brutto) |
| X1 brutto | +0,17 | 1,04 | 2/40 | −1,98 / **+3,62** | +0,2 | ✓ |
| X1 netto | −0,25 | 1,03 | 4/40 | −2,48 / +3,20 | −3,4 | ✓ (≤ brutto) |
| CP1 brutto | −0,20 | 1,03 | 1/40 | −2,29 / +1,57 | −3,9 | ✓ |
| CP1 netto | −0,32 | 1,02 | 2/40 | −2,39 / +1,41 | −6,1 | ✓ (≤ brutto) |
| **czułość: TS1 ze znakiem przyszłego tygodnia** | **+22,9** | 4,6 | **40/40** | +13,4 / +30,4 | +218 | ✓ (> 5 wszędzie) |

Łącznie fałszywe alarmy brutto: **4 ze 120 = 3,3 %** (przedział Wilsona 95 % [1,3 %; 8,3 %]),
zgodne z nominalnymi 5 %.

**Dodatkowo, dopisane PO obejrzeniu wyniku (diagnostyka, kryterium bez zmian):** X1 miał jedno
losowanie z t = +3,62 (ziarno 16, nadwyżka kurtozy dziennego szeregu 11,2). Przy rozkładzie
normalnym to rzadkie (P(|t| > 3,6) ≈ 0,03 %), więc sprawdzono, czy na grubych ogonach t z X1 nie
jest źle skalibrowane: `raw_output_x1_ogon.txt` (400 losowań, 18 min) — średnia t +0,055, sd 0,977;
|t| > 1,96: **20/400 = 5,00 %**; |t| > 2,576: 1/400 (normalny 1 %); |t| > 3: 1/400 (normalny
0,27 %). **Kalibracja poprawna** — +3,62 to jedno rzadkie losowanie, nie wada przyrządu.

## Co na plus (+) / Co na minus (−)

**(+)** Trzy silniki, na których stoją wszystkie dzienne rundy od X1 do SZ1, nie wymyślają zysku
z szumu, także przy grubych ogonach i grupowaniu zmienności. Kontrola czułości pokazuje, że
sprawdzian nie jest ślepy (zajrzenie w przyszłość → t ≥ 13 w każdym losowaniu). t z X1 ma
poprawne ogony (400 losowań). TS1 ma sd t 0,84 < 1 — t_neff tego silnika jest raczej ostrożny
(zaniża pewność), co przemawia na korzyść wyniku TS1, nie przeciw.
**(−)** Kontrola sprawdza tylko jedną klasę błędów: przeciek z przyszłości i złą rachubę zwrotów.
Nie wykrywa błędów w DANYCH rzeczywistych (przeżywalność, złe znaczniki czasu, funding), bo dane
syntetyczne ich nie mają; funding = 0, więc jego rachuba nie jest tu sprawdzona. Model 4h pominięty
(ma kontrolę z K1). Jedno ziarno X1 z t 3,6 mówi, że na 5,5 roku pojedynczy wynik t ≈ 3 bywa
przypadkiem (~1 na 300–400).

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY**: X1 brutto na losowaniu 0 przeliczony NIEZALEŻNIE prostą pętlą numpy
(top-5/bottom-5, stałe wagi w tygodniu, bez funkcji silnika): korelacja dzienna z silnikiem
**0,998**, średnia +0,89 vs +1,19 %/rok (różnica = dryf wag w tygodniu), t +0,14 vs +0,19.
Kogo nie ma w zbiorze: fundingu, przeżywalności, modelu 4h (patrz „minus”). Czerwona flaga (t 3,62)
sprawdzona 400 losowaniami. `data:statistical-analysis`: przedział dla odsetka alarmów podany;
kryteria dwumianowe zapisane z góry. `engineering:code-review` — **Approve**: generator deterministyczny
z ziarna, parametry walidowane (df > 2, α + β < 1), dno ceny −95 %/dzień; test znaków zwrotów
zamiast surowej autokorelacji (przy GARCH surowa ma większy rozrzut niż 1/√n — poprawione przed
commitem); jedna sugestia wdrożona (docstring strażnika: czerwony w trakcie rundy świadomie).

## Wniosek

**Prostym językiem:** sprawdziliśmy nasze „wagi”, kładąc na nich pusty talerz. Na sztucznych
cenach, w których kierunku z definicji nie da się przewidzieć, trzy silniki (trend tygodniowy,
momentum przekrojowe, reguła premii Coinbase) pokazały zero — tak jak powinny. Ten sam silnik
z celowo wstawionym oszustwem (znajomość przyszłego tygodnia) od razu pokazał ogromny „zysk”, więc
sprawdzian umie złapać taki błąd. Wniosek: dodatnie wyniki trendu i premii Coinbase **nie są
artefaktem naszego kodu**. To nie czyni ich dowodem przewagi — dalej mogą być przypadkiem wybranym
z ~30 prób — ale jedno podejrzenie odpada.

## Rekomendacja

1. Kontrola negatywna jest odtąd bramką A6 (`docs/skills/bramki-jakosci.md`) dla każdego NOWEGO
   silnika albo zmiany w rachubie zwrotów; test `test_trend_engine_finds_nothing_on_noise` pilnuje
   TS1 przy każdym `pytest`.
2. Wynik t ≈ 3 pojedynczej reguły na 5,5 roku nie jest sam w sobie dowodem — jeden na kilkaset
   przebiegów szumu go osiąga; dalej obowiązuje korekta na liczbę odczytów.
3. Następna runda: CP2 (premia Coinbase na ETH/SOL) — gałąź `cp2-replikacja-eth-sol`.

## Użyte skille

Rejestr `runs/skille/metodyka-kontrole.jsonl` (`py tools/skill_audit.py raport --galaz metodyka-kontrole`):
7 wczytań, 7 skilli.

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-quant` | przyrząd kalibruje się na danych ze ZNANYM sygnałem (T4/K1) — stąd para: szum + celowe zajrzenie |
| `anthropic-skills:clas5-runda` | pre-rejestracja w osobnym commicie przed przebiegiem, katalog rundy, 0 wariantów poza licznikami |
| `engineering:testing-strategy` | testy generatora: niezależność ZNAKÓW zamiast surowej autokorelacji, kurtoza, korelacja czynnika, spójność OHLC |
| `engineering:architecture` | decyzja porządkowa: CLAUDE.md skrócony z zachowaniem numeracji, pełne brzmienie w `docs/rag/08`; strażnik w kodzie zamiast prośby |
| `data:validate-data` | niezależne przeliczenie X1 (korelacja 0,998) i sprawdzenie czerwonej flagi t 3,62 |
| `data:statistical-analysis` | przedział Wilsona dla odsetka fałszywych alarmów, porównanie ogona z rozkładem normalnym |
| `engineering:code-review` | Approve; sugestia o docstringu strażnika wdrożona |

Pominięte z tabeli zasady 19: `dataviz` (wynik to tabela 7 wierszy, wykres niczego nie dodaje).
