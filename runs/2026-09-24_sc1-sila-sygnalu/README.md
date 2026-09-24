# SC1 — wielkość pozycji według siły sygnału („pewności”) (2026-09-24)

> **STATUS: ZAMKNIĘTA — NIEMIERZALNA, runda NIE wystartowała (zasada 18).** Decyzja użytkownika
> 2026-09-24: „sizing zależny od pewności modelu” (punkt 3). Rachunek mocy (`moc.txt`, tylko
> rozrzut, bez oglądania wyników): szum różnicy „siła − znak” wynosi **±13,2 %/rok (trend)**
> i **±16,7 %/rok (premia Coinbase)**, a realistyczny efekt skalowania to kilka %/rok. Wynik nie
> rozstrzygnąłby niczego niezależnie od tego, co by wyszło — więc go nie liczymy. **0 wariantów
> zużytych.**

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Chcieliśmy sprawdzić, czy opłaca się grać większą pozycją, gdy sygnał jest silny (mocny trend,
duże odchylenie premii Coinbase), a mniejszą, gdy słaby. Zanim policzyliśmy wynik, sprawdziliśmy,
czy test w ogóle jest w stanie to rozstrzygnąć. Nie jest: przesuwanie pozycji między silnymi
i słabymi sygnałami samo z siebie robi tyle szumu (±13–17 % rocznie), że poprawa rzędu kilku
procent byłaby niewidoczna. Uczciwiej jest tego nie liczyć, niż potem wróżyć z przypadkowej liczby.

## Metadane

- Branch `sc1-sila-sygnalu`. Skrypt `backtest/run_signal_strength_sc1.py` (na `runs/ZAMROZONE.txt`);
  komenda rachunku mocy: `PYTHONUTF8=1 py -m backtest.run_signal_strength_sc1 --moc` → `moc.txt`.
  Tryb pełny istnieje, ale **nie został uruchomiony**.

## Pre-rejestracja (zapisana przed rachunkiem mocy)

- **Siła sygnału:** trend — z = log-zwrot 28 dni / (σ̂·√(28/365)); premia Coinbase —
  z = (średnia 7 dni − średnia 90 dni) / (sd 90 dni / √7). s = clip(z, ±2)/2.
- **Uczciwe porównanie:** s × c, c = 1/średnia|s| z samych sygnałów (trend c = 2,86, Coinbase
  c = 1,50) — ta sama średnia ekspozycja co wersja znakowa.
- **Kryterium (m = 2, z = 2,241):** różnica parowana dziennego zwrotu netto siła − znak (TS1/CP1
  bez likwidacji); POZYTYWNY, gdy t_neff > 2,241; NEGATYWNY, gdy górny kraniec < 0.
- **Mierzalność (`moc.txt`):** sd różnicy 13,68 %/rok (trend), 14,57 %/rok (Coinbase) → half-width
  ±13,20 / ±16,74 %/rok. Oczekiwany efekt (literatura o skalowanym trendzie: poprawa rzędu kilku
  %/rok; precedens C2.13: pewność modelu wręcz szkodziła) < half-width → **NIEMIERZALNA** na obu
  ramionach.

## Wniosek

**Prostym językiem:** na 5 latach danych nie da się sprawdzić, czy skalowanie pozycji siłą
sygnału pomaga — test miałby rozdzielczość ±13–17 % rocznie. Zostajemy przy prostym „znaku”
(pełna pozycja w kierunku sygnału), który jest łatwiejszy i nie koncentruje ryzyka w kilku
skrajnych sygnałach (przy trendzie najsilniejsze sygnały dostałyby prawie 3× średniej pozycji).

## Rekomendacja

1. Nie stosować skalowania siłą sygnału w dzienniku na żywo — brak możliwości sprawdzenia, a
   dodatkowe ryzyko koncentracji jest pewne.
2. Jeśli kiedyś: jako porównanie na danych prospektywnych po ≥ 2 latach, nie na tej historii.
3. Użyte skille: rejestr `runs/skille/sc1-sila-sygnalu.jsonl` (`clas5-runda`, `clas5-quant` —
   precedens C2.13, wyrównanie ekspozycji z sygnałów). Bramki 16a–c: walidacja nie dotyczy (brak
   wyniku); przegląd kodu: skrypt cienki, sygnały z danych ≤ t (okna trailing), `c` z sygnałów —
   **Approve**; pominięte `data:validate-data`, `data:statistical-analysis`, `testing-strategy`
   (brak wyniku do walidacji; funkcje to jednolinijkowe okna trailing na przetestowanym silniku).
