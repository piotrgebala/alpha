# M1 — momentum po raz pierwszy na próbie zdolnej cokolwiek rozstrzygnąć (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Sekcje „Wynik" i dalsze są celowo puste. Wszystko do sekcji
> „Czego ta runda NIE rozstrzygnie" włącznie zapisano **przed napisaniem linijki kodu**.

## ID testu

**M1** — pierwszy wariant **NOWEJ HIPOTEZY M**. Własny licznik od zera (wniosek skumulowany 13),
własna reguła STOP, własna pre-rejestracja. **Nie dziedziczy budżetu ani progów po Fazie 0
ani po H2.**

## Metadane

- **Branch:** `task/M1-momentum-bez-bramki`
- **Poprzedzający stan (master):** `9296650`
- **Warianty:** **1** — wyczerpuje licznik M (0/1 → 1/1).
- **Testy przed rundą:** 390/390. Bramka leakage: **19/19 zielona** (`momentum_5`
  i `ema_diff_9_21` objęte testem sparametryzowanym po `FEATURE_FUNCTIONS` — zasada 2
  spełniona, żadna cecha nie jest nowa).

## Skąd ta hipoteza — rachunek z plików indeksowych, nie z pomysłu

**Wniosek skumulowany 12** wymienia momentum na liście rzeczy, których Faza 0 **NIE wykazała**:
*„próba zagłodzona przez samą bramkę: 0,53% świec — **niewykonalność pomiaru, nie brak
edge'u**"*. Z10 pisze to samo prostym językiem: *„momentum nigdy nie dostało uczciwego testu"*.

Rozbicie liczby zamykającej Fazę 0 pokazuje, dlaczego:

| pomiar | cechy | `n` | trafność | CI | pasmo |
|---|---|---|---|---|---|
| 5m `range` (Z17+Z21) | **reversion** | 7 043 | 50,38% | [49,21%; 51,54%] | 1,17 pp |
| 5m `trend` (Z17+Z21) | **momentum** | **299** | 50,84% | **[45,17%; 56,50%]** | **5,67 pp** |
| 4h `range` (S1b) | reversion | 345 | 47,54% | [42,27%; 52,81%] | 5,28 pp |
| **POOLED (Z10)** | — | **7 687** | **50,27%** | [49,15%; 51,38%] | 1,12 pp |

**96% liczby zamykającej Fazę 0 to cechy mean-reversion.** Momentum zmierzono na 299
transakcjach z przedziałem szerokim na **11 punktów** — obejmującym zarówno „bezużyteczne",
jak i „bardzo dochodowe".

**SPROSTOWANIE WPISU 4C w `STATUS.md` (ETAP 4).** Stoi tam: *„Bez bramki »momentum« to po
prostu predykcja kierunku z cech OHLCV — czyli dokładnie to, co Faza 0 obaliła na 7 687
transakcjach"*. To jest **za mocne i sprzeczne z wnioskiem 12**: tamte 7 687 transakcji to
w 96% inny zestaw cech. Wpis zostaje sprostowany w tej rundzie.

**Co się zmieniło, że to jest dziś wykonalne** — dwie rzeczy, obie zmierzone:
1. **Zdjęcie bramki reżimu** (H2.1a) — to ona głodziła próbę do 0,53% świec.
2. **Adopcja A1** (K2 → K3) — abstynencja 99,76% → 43,84%, próba **35 → 8 033** na tej
   konfiguracji, pasmo 16,56 pp → **1,09 pp**.

## Co przemawia PRZECIW — zapisane z góry, żeby nie zniknęło po wyniku

**Wniosek skumulowany 11 mówi wprost:** *„zmianą zdolną ruszyć `p` jest **nowy zbiór
informacyjny**, nie kolejna transformacja OHLCV ani nowa architektura nad tymi samymi
cechami"*. Momentum to **transformacja OHLCV**. Ten wniosek obniża prior tej rundy i nie
wolno go pomijać w interpretacji wyniku.

Napięcie między wnioskami 11 i 12 jest realne i rozstrzygam je tak: **wniosek 11 jest
uogólnieniem zbudowanym na powtarzalnych porażkach cech mean-reversion, a momentum to
jedyna gałąź OHLCV, na której tego uogólnienia nigdy nie sprawdzono.** Wniosek 12 istnieje
dokładnie po to, żeby nie cytować 11 jako dowodu w tej sprawie. Runda zamyka tę lukę —
w którąkolwiek stronę.

## Konfiguracja (ZAMROŻONA) i ramiona

Wszystko poza zestawem cech jest identyczne z konfiguracją zmierzoną w K3 (C2):

- **interwał** 4h, **V** = 3, **bramka reżimu** BRAK (`REGIME_ALL`)
- **wagi klas** `balanced` (A1, przyjęte 2026-09-22)
- walk-forward **60/28/28**, seed **42**, historia **6,8 roku** (14 916 świec)

| ramię | cechy | warianty | rola |
|---|---|---|---|
| **A** (odniesienie) | `REVERSION_FEATURES` (4) | **0** | punkt odniesienia w tej samej konfiguracji |
| **B** (kandydat) | `MOMENTUM_FEATURES` (4) | **1 — WYCZERPUJE licznik M** | przedmiot rundy |

**Dokładnie JEDNA zmienna** (zasada 4): zestaw cech. Ramię A liczy się za 0 wariantów wg tego
samego uzasadnienia, które zapisano w H2.1: **próg opłacalności pochodzi z geometrii kosztu,
a nie z obejrzanej trafności**, więc pomiar odniesienia nie może przesunąć poprzeczki.

## Rachunek mierzalności (zasada 18) — i uczciwe postawienie pytania

`expected_trades(14 448 świec, abstynencja 43,84%)` = **8 114**; pasmo = **1,09 pp**;
próg opłacalności **52,93%** (K3).

| założona trafność | skąd to założenie | werdykt |
|---|---|---|
| 50,84% | punktowy pomiar 5m/`trend` (n=299) | **NIEMIERZALNA** |
| 52,93% | dokładnie próg opłacalności | **NIEMIERZALNA** |
| **54,02%** | dolna granica wykrywalności przy tym `n` | MIERZALNA |
| 56,50% | górny kraniec CI pomiaru 5m/`trend` | MIERZALNA |

**To znaczy rzecz, którą trzeba powiedzieć wprost: tej rundzie NIE wolno obiecywać odpowiedzi
„momentum działa".** Żeby to orzec, momentum musiałoby dowozić ≥ 54,02% — więcej niż
cokolwiek, co ten projekt kiedykolwiek zmierzył.

**Ale pytanie odwrotne JEST mierzalne, i to z zapasem.**
`required_trades(50,84% wobec progu 52,93%)` = **4 481**, a mamy **8 114** — czyli **1,8×
wymaganej próby przy mocy 80%**. Runda ma więc moc orzec, że **momentum NIE dobija do progu
opłacalności** — dokładnie tym samym standardem („dowód braku, nie brak dowodu"), którym
Z10 zamknęło Fazę 0.

**Dlatego runda startuje.** Nie po to, żeby znaleźć edge, tylko żeby **zamknąć lukę z wniosku
12** liczbą zamiast przypisem.

## Kryterium — zapisane PRZED uruchomieniem

- **POZYTYWNY:** `ci_low(p_B) > break_even_B`. Byłby to **pierwszy dodatni wynik w historii
  projektu** i nie uruchamia niczego poza **replikacją na innym instrumencie** (zasada 9).
  Żadnego wdrożenia, żadnego kolejnego wariantu w tej serii.
- **NEGATYWNY:** `ci_high(p_B) < break_even_B` — momentum nie dobija do progu. Zamyka
  momentum jako kierunek i domyka pozycję z wniosku 12.
- **NIEROZSTRZYGNIĘTY:** `n_B < 4 481` (poniżej próby wymaganej do orzeczenia negatywu przy
  mocy 80%) **albo** CI przecina próg. Wtedy **nie interpretujemy w żadną stronę** — precedens
  S1b i H2.1.
- **REGUŁA STOP:** jeden wariant. Po nim seria M jest zamknięta **niezależnie od wyniku**.
  Żadnego drugiego `V`, interwału ani wariantu cech.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **Spodziewam się wyniku negatywnego.** Prior jest niski i opiera się na wniosku 11 oraz na
  tym, że każda naprawa pomiaru w Fazie 0 zostawiała `p` przy 50% — ani razu wyżej.
- **Jedyny pomiar momentum (50,84%) NIE jest przenośny co do poziomu:** pochodzi z 5m, gdzie
  próg opłacalności wynosił 82,81%, a nie 52,93%. Traktuję go jako słaby prior co do
  **rzędu wielkości**, nie jako prognozę.
- **`n` w ramieniu B może się różnić od 8 114**, bo abstynencja zależy od cech. Jeśli spadnie
  poniżej 4 481 — werdykt NIEROZSTRZYGNIĘTY, i tak to zaraportuję.
- **Wynik pozytywny traktuję z podejrzliwością proporcjonalną do jego niezwykłości.**
  Pierwsza reakcja na `ci_low > break_even` to **nie ogłoszenie**, tylko sprawdzenie, czy nie
  mamy przecieku — projekt złapał już trzy (Z17, Z17b, Z9), wszystkie ręcznie.

## Czego ta runda NIE rozstrzygnie

- **ETH/SOL/BNB** — zero testów, zero danych na dysku (tylko BTC).
- **Inny target niż kierunek** — inna definicja wypłaty, próg do policzenia od zera.
- **Carry przekrojowy (4A)** — wymaga silnika portfelowego, którego Faza 0 nie ma.
- **Czy utracona selektywność niosła informację** (otwarte pytanie z K3) — inny mechanizm,
  byłby confounderem. Osobna runda, jeśli w ogóle.
- **Wniosku 11 w ogólności** — negatywny wynik M1 go **wzmacnia**, ale go nie dowodzi dla
  cech spoza OHLCV.

---

## Wynik

*(do wypełnienia po przebiegu)*

## Co na plus (+) / Co na minus (−)

*(do wypełnienia po przebiegu)*

## Walidacja (zasada 16a)

*(do wypełnienia — werdykt Ready / Caveats / Revision)*

## Przegląd diffu (zasada 16c)

*(do wypełnienia przed merge)*

## Wniosek / Rekomendacja

*(do wypełnienia po przebiegu)*
