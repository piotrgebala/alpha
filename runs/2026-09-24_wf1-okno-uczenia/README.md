# WF1 — dłuższe okno uczenia modelu 4h (2026-09-24)

> **STATUS: ZAMKNIĘTA — oba dłuższe okna NEGATYWNE.** Na wspólnych świecach od 2023: okno 365 dni
> p 49,59 % [48,14; 51,05], zwrot netto −0,061 %/transakcję, t_neff −2,59; okno 730 dni p 48,50 %
> [47,06; 49,95], −0,084 %, t_neff −3,53; kontrola 60 dni p 50,12 %, −0,105 %, t −3,97. Kontrola na
> pełnym okresie odtworzyła co do sztuki znane liczby (n 6 789, p 49,58 %). Pre-rejestracja `eb56d55`.
> Walidacja: **READY**; przegląd: **Approve**. Seria WF 2/2, STOP.
> Poprzednio: **PRE-REJESTRACJA (przed wynikiem).**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Użytkownik: „może okno jest za wąskie — BTC porusza się w dłuższych cyklach”. Model kierunku na
świecach 4h uczył się dotąd tylko na 60 ostatnich dniach. Sprawdzamy, czy uczenie na roku albo
dwóch latach historii daje lepsze przewidywania. Wszystko inne zostaje bez zmian.

## ID testu

WF1 — seria WF (okno uczenia), otwarta decyzją użytkownika 2026-09-24 dla tej jednej zmiennej
(seria modeli Fazy 0 była zamknięta regułą STOP).

## Metadane

- Branch `wf1-okno-uczenia`. Skrypt `backtest/run_train_window_wf1.py` (buduje na zamrożonym
  `run_horizon_y`: te same cechy, wejście, model wypełnień, koszty).
- Dane: natywne świece 4h BTC/USDT:USDT od 2021-01-01 (zasada 20), 12 042 świece.

## Poprzedzające wyniki

- Kontrola 4h (wniosek 46): p 49,58 % [48,39; 50,77], r̄ netto −0,107 %/transakcję, n 6 789, abstynencja 40,4 %.
- T4 (wniosek 41): najlepsza możliwa liczba drzew poprawia stratę tylko o 0,7 % → cechy niosą mało informacji.
- Y2 (1d, okno 365 dni): p 50,2 % [47,1; 53,3], n ≈ 1 000 — nierozstrzygnięty (za mało transakcji).
- Długości okna uczenia na 4h nigdy nie badano jako zmiennej.

## Pre-rejestracja (przed wynikiem)

- **Hipoteza:** dłuższe okno uczenia (więcej różnych stanów rynku) poprawia trafność i zwrot netto
  modelu kontrolnego 4h.
- **JEDNA zmienna:** `train_days` ∈ {60 (kontrola, 0 wariantów), 365, 730}; test/krok 28/28 dni.
- **Wspólny okres oceny:** sygnały z `timestamp` ≥ 2023-01-01 (pierwszy dzień testu ramienia 730
  przy danych od 2021-01-01) — ten sam zbiór świec dla wszystkich ramion; filtr czasu, nie wyniku.
- **Kryterium per ramię (m = 2, z = 2,241):** POZYTYWNY, gdy t_neff zwrotu netto > 2,241 ORAZ
  ci_low(p) > p*; NEGATYWNY, gdy t_neff < −2,241 przy n ≥ required_trades(0,50; BE); inaczej
  NIEROZSTRZYGNIĘTY. Kontrola 60 dni: odczyt przy z = 1,96, bez licznika.
- **Opisowo:** ramiona na pełnym okresie każdego z nich (kontrola na pełnym okresie powinna
  odtworzyć znane liczby: n 6 789, p 49,58 % — sprawdzian odtwarzalności).
- **Mierzalność (`moc.txt`):** wspólne 7 662 świece → oczekiwane n ≈ 4 541 na ramię, half-width
  1,66 pp (z 2,241), próg ±B ≈ 51,7 %; `measurability_report(0,56; 0,5174; 4 541)` → **MIERZALNA**.
- **Licznik:** nowa seria WF 2/2 (365, 730), STOP po tej rundzie.

## Wynik

`raw_output.txt` (trening 3 ramion: 15 s).

| okno uczenia | foldy | abstynencja | n (wspólne) | trafność p [CI 95 %] | próg p* | zwrot netto/transakcję [CI] | t_neff | werdykt |
|---|---|---|---|---|---|---|---|---|
| 60 dni (kontrola) | 69 | 40,4 % | 4 346 | 50,12 % [48,63; 51,60] | 54,81 % | −0,105 % [−0,148; −0,062] | −3,97 | NEGATYWNY (z 1,96) |
| **365 dni** | 58 | 37,4 % | 4 543 | **49,59 % [48,14; 51,05]** | 52,22 % | **−0,061 % [−0,110; −0,012]** | −2,59 | **NEGATYWNY** |
| **730 dni** | 45 | 37,9 % | 4 606 | **48,50 % [47,06; 49,95]** | 52,17 % | **−0,084 % [−0,133; −0,036]** | −3,53 | **NEGATYWNY** |

Pełne okresy (opisowo): 60 dni n 6 789, p 49,58 % (odtworzenie kontroli); 365 dni n 6 001, p 49,53 %.

## Co na plus (+) / Co na minus (−)

**(+)** Test czuły (n ≈ 4 500 na ramię) i uczciwie porównany (te same świece). Pytanie użytkownika ma
jasną odpowiedź: dłuższa historia nie daje modelowi lepszych przewidywań. Dłuższe okna tracą nieco mniej
na transakcję, bo dłuższe okno obniża próg p* (inne proporcje wyjść), ale trafność zostaje przy 50 %.
**(−)** Zmieniła się tylko długość okna; cechy to nadal przekształcenia wykresu BTC (wniosek 39) —
runda nie mówi nic o innych cechach ani o cyklu halvingowym (osobno: HC1).

## Walidacja, statystyka, przegląd (16a–c)

`data:validate-data` **READY**: kontrola 60 dni na pełnym okresie odtworzyła co do sztuki opublikowane
liczby (n 6 789, p 49,58 %, p* 53,64 %, r̄ −0,1069 %) — przyrząd ten sam. `data:statistical-analysis`:
przedziały 95 %, z 2,241 dla dwóch ramion; wszystkie trzy przedziały trafności obejmują 50 % albo leżą
poniżej. `engineering:code-review` — **Approve**: filtr sygnałów po czasie przed symulacją (zapisany z góry),
reszta z zamrożonego `run_horizon_y`.

## Wniosek

**Prostym językiem:** model, który uczy się na roku albo dwóch latach historii zamiast na dwóch
miesiącach, dalej zgaduje kierunek BTC jak rzut monetą (48,5–49,6 % trafności wobec wymaganych ~52 %).
Krótkie okno nie było przyczyną porażki — przyczyną jest to, że z samego wykresu BTC nie da się
przewidzieć ruchu na najbliższe 12 godzin.

## Rekomendacja

1. Seria WF zamknięta (2/2, STOP); model kierunku 4h pozostaje zamknięty.
2. Pytanie o cykl 4-letni — osobno w HC1 (opis, nie test).

## Użyte skille

Rejestr `runs/skille/wf1-okno-uczenia.jsonl` (wspólny z HC1): `clas5-runda`, `clas5-quant` (wspólny okres
oceny, kryterium dwuwarunkowe), `data:validate-data`, `data:statistical-analysis`, `engineering:code-review`.
Pominięte: `dataviz`.
