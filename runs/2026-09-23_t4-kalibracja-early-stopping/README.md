# T4 — czy early stopping na tak małych oknach wybiera liczbę drzew z sygnału, czy z szumu (2026-09-23)

> **STAN: PRE-REJESTRACJA.** Ten plik zapisano i zacommitowano PRZED napisaniem skryptu
> i przed obejrzeniem jakiejkolwiek liczby. Sekcje Wynik / Wniosek / Rekomendacja dochodzą
> w osobnym commicie po uruchomieniu.

## ID testu

**T4** — zadanie z `STATUS.md` §17, ETAP 3 („PRIORYTET 1 po K1"). Diagnostyka przyrządu,
**0 wariantów** (poza licznikami hipotez — uzasadnienie niżej).

## Pytanie prostym językiem

Model uczy się w rundach. W każdej rundzie dokłada jedno małe „drzewo decyzyjne”, które
poprawia błędy poprzednich. Zbyt wiele rund prowadzi do tego, że model zaczyna uczyć się
przypadkowych zbiegów okoliczności z danych treningowych. **Early stopping** (wczesne
zatrzymanie) ma temu zapobiegać. Odkłada 20% najnowszych danych treningowych na bok,
po każdej rundzie sprawdza model na tym kawałku i przerywa naukę, gdy wynik przestaje
się poprawiać.

Ten mechanizm ma dwie ustawione na oko liczby: **20%** (`validation_fraction`) i
**co najmniej 30 wierszy** (`MIN_VALIDATION_ROWS`). Nikt ich nie sprawdzał. Wiemy już,
że potrafią szkodzić: próg 30 wierszy wyłączył kiedyś po cichu early stopping w 92% okien
(Z17b). Pytamy więc wprost: **w obecnej, kanonicznej konfiguracji, czy ten mechanizm wybiera
liczbę drzew, która naprawdę lepiej działa na nowych danych, czy losuje ją z szumu?**

## Poprzedzające wyniki (zasada 14)

- **Z17+Z21** — early stopping liczono na danych testowych (przeciek). Przeniesiony na ogon
  danych treningowych, z odcięciem `V` świec na granicy (embargo).
- **S1 → S1b (Z17b)** — przy formule `round(n·0,2)` próg 30 wierszy wyłączał early stopping
  w 58/63 oknach. Po naprawie `max(30, round(n·0,2))` działa w 53/63. Skutek uboczny:
  abstynencja modelu (odmowa zajęcia pozycji) wzrosła 70,9% → 90,5%. S1b zapisało wprost:
  *„Nie wiem, czy wzrost abstynencji to zdrowa ostrożność, czy artefakt zbyt agresywnego
  early stoppingu przy 30 wierszach walidacji. Rozstrzygnięcie wymagałoby zagnieżdżonego
  walk-forward”*. **To jest dokładnie to rozstrzygnięcie.**
- **K2/A1** — wagi klas `balanced` przyjęte jako domyślne. Walidacja jest ważona tą samą mapą
  co trening, więc early stopping optymalizuje ten sam cel co trening.
- **K3, M1, F1** — obecna konfiguracja kanoniczna: 4h, bez bramki reżimu, V=3, wagi
  `balanced`, walk-forward 60/28/28 dni. Okno treningowe to ~360 świec, więc część
  walidacyjna ma ~70 wierszy. **Taka mała próbka do oceny krzywej błędu to realne ryzyko,
  że decyzję o liczbie drzew podejmuje szum.**
- **Wniosek skumulowany 39** — zbiór informacyjny na BTC jest wyczerpany (M1, F1: trafność
  ~50% przy dużej próbie). **Ta runda nie reanimuje żadnej hipotezy.** Dotyczy przyrządu:
  wynik ma znaczenie dla każdego przyszłego pomiaru tym pipeline'em, również dla innego
  instrumentu albo innego celu (§17, ETAP 4).

Czego ta runda NIE powtarza: nie mierzy trafności na danych testowych dla żadnego zestawu
cech. M1 i F1 już to zrobiły, a ich serie są zamknięte regułą STOP.

## Projekt — zagnieżdżony podział wyłącznie wewnątrz danych treningowych

Dla każdego okna walk-forward biorę **dokładnie ten `train_df`**, który silnik podaje do
`train_regime_model`. Przechwytuję go opakowaniem funkcji, więc to ten sam przebieg, nie
kopia logiki. Konfiguracja: ramię A z F1/K3-C2, czyli 4 cechy reversion, 4h, bez bramki,
V=3, `balanced`, 60/28/28, seed 42.

Dalej, dla każdego okna:

1. `train_clean` = po `dropna` i po embargu `V`, tak jak w produkcji.
2. Podział produkcyjny: `n_val = max(30, round(0,2·n))`. Ogon produkcyjny (`val_part`)
   staje się **wewnętrznym zbiorem testowym**. Te wiersze nie biorą udziału w żadnym
   wyborze.
3. Z części `fit_part` odcinam ostatnie `V` wierszy (embargo względem wewnętrznego testu).
   Resztę dzielę tą samą regułą na **wewnętrzny trening** i **wewnętrzną walidację**,
   dla `f ∈ {0,1; 0,2; 0,3}`.
4. Trenuję 200 rund na wewnętrznym treningu i zapisuję krzywe ważonego `mlogloss` na
   walidacji i na wewnętrznym teście. Mapa wag pochodzi z wewnętrznego treningu, jak
   w produkcji.
5. Z krzywej walidacji odtwarzam decyzję early stoppingu: najlepsza runda i stop po 20
   rundach bez poprawy. Wyrocznię (runda najlepsza na wewnętrznym teście) liczę WYŁĄCZNIE
   jako punkt odniesienia; nigdy jej nie wybieram.

**Żadna etykieta z testowej części walk-forward nie jest czytana.** Skrypt nie wywołuje
`run_and_summarize`. Przebieg produkcyjny służy tylko do przechwycenia `train_df`
i `folds_summary`. Journal transakcji nie jest drukowany ani analizowany.

## Miary (zarejestrowane z góry)

**D0 — fakty o konfiguracji produkcyjnej** (z `folds_summary` i przechwyconych danych):
liczba okien aktywnych i pominiętych, rozkład `n_val`, **w ilu oknach `max(30, ·)` zmienia
wynik**, udział okien z early stoppingiem, rozkład `best_iteration`, udział okien z
`best_iteration` < 5 (model praktycznie = rozkład klas) i = 199 (early stopping nie zadziałał).

**D1 — MIARA GŁÓWNA.** Dla `f = 0,2`, w każdym oknie:
`Δ_200 = L_test(k_ES) − L_test(200)` oraz `Δ_1 = L_test(k_ES) − L_test(1)`, gdzie `L_test` to
ważony `mlogloss` na wewnętrznym teście. Raport: średnia, mediana i 95% CI średniej po
oknach (t-Student).

**D2** — rozkład `k_ES` vs `k_wyrocznia`: korelacja Spearmana i „żal”
`L_test(k_ES) − L_test(k_wyrocznia)` (≥ 0 z konstrukcji; to strata wobec idealnej decyzji).

**D3** — wrażliwość na `f ∈ {0,1; 0,2; 0,3}`: mediana `k_ES` i średnie `Δ_200`.
**Obserwacja, nie wybór.** Żadna wartość `f` nie zostaje w tej rundzie przyjęta.

**D4** — konsekwencja praktyczna: udział wierszy wewnętrznego testu, na których model
przewiduje „timeout” (abstynencja), przy `k_ES` vs przy 200 drzewach. To mechanizm z S1b.

## Kryteria interpretacji (zapisane PRZED wynikiem)

| wynik D1 (`Δ_200`, f=0,2) | czytanie |
|---|---|
| górny kraniec CI < 0 | early stopping **pomaga**: wybiera liczbę drzew lepszą niż „bez zatrzymania” na danych, których nie widział. Zostaje |
| CI obejmuje 0 | przy tej wielkości okna early stopping jest **nieodróżnialny od braku early stoppingu**. Liczba drzew to wtedy w praktyce wybór losowy (szum), ale nieszkodliwy dla straty |
| dolny kraniec CI > 0 | early stopping **szkodzi**: wybiera gorzej niż stała 200. To wada przyrządu do zgłoszenia jako osobne zadanie |

Analogicznie `Δ_1` odpowiada na pytanie, czy early stopping bije model zatrzymany po
pierwszej rundzie (praktycznie sam rozkład klas).

`MIN_VALIDATION_ROWS`: jeśli `max()` nie zmienia `n_val` w żadnym aktywnym oknie
kanonicznej konfiguracji, to stała jest tutaj **bezczynna**. Wtedy wniosek brzmi
„niegroźna w tej konfiguracji”, a nie „skalibrowana”.

**Reguła niezależna od wyniku:** ta runda **nie zmienia żadnej wartości w kodzie
produkcyjnym**. Zmiana `validation_fraction`, `EARLY_STOPPING_ROUNDS` albo
`MIN_VALIDATION_ROWS` zmieniłaby każdy przyszły pomiar. Byłaby więc osobną rundą z własną
pre-rejestracją, dla której ta runda jest tylko przesłanką. Dzięki temu D3 nie jest
przeszukiwaniem siatki parametrów, tylko opisem.

**Red flag zapisany z góry:** gdyby wynik wyglądał na „early stopping jest bezużyteczny,
więc S1b/H2.1 były artefaktem”, trzeba pamiętać, że K2/A1 już zmieniło mechanizm
abstynencji. Wniosek o S1b dotyczy konfiguracji `none`, a ta runda mierzy `balanced`.

## Dlaczego 0 wariantów i jak z mierzalnością (zasada 18)

- **0 wariantów:** runda nie porównuje żadnej hipotezy rynkowej z wynikiem na danych
  testowych. Liczy wyłącznie na danych treningowych każdego okna, czyli wewnątrz
  walk-forward (zasada 1). Ta sama kategoria co K1/K2/K3 (kalibracja przyrządu).
- **`measurability_report` nie ma tu zastosowania.** Ta funkcja dotyczy hipotez
  o trafności. Jednostką tutaj jest okno walk-forward, oczekiwane `n` ≈ 85 (F1: 85 okien,
  0 pominiętych). Precyzję D1 podam po fakcie jako połowę szerokości CI. Jeśli okaże się
  szersza niż sama różnica, którą chcemy zobaczyć, werdykt brzmi „nierozstrzygnięte”,
  a nie „brak efektu”.

## Ścieżka odwrotu

Runda nie zmienia kodu produkcyjnego. Dodaje jeden skrypt analityczny
(`backtest/diagnose_early_stopping_t4.py`) i ten katalog. Revert = `git revert` commitów
rundy.
