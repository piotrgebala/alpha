# F1 — funding po raz pierwszy na próbie zdolnej cokolwiek rozstrzygnąć (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Sekcje „Wynik" i dalsze są celowo puste. Wszystko do sekcji
> „Czego ta runda NIE rozstrzygnie" włącznie zapisano **przed napisaniem linijki kodu**.

## ID testu

**F1** — pierwszy wariant **NOWEJ HIPOTEZY F**. Własny licznik od zera (wniosek skumulowany 13),
własna reguła STOP, własna pre-rejestracja. **Nie dziedziczy budżetu ani progów po Fazie 0,
po H2, ani po M.**

## Metadane

- **Branch:** `task/F1-funding-zmierzony`
- **Poprzedzający stan (master):** `2abca35` (merge M1)
- **Warianty:** **1** — wyczerpuje licznik F (0/1 → 1/1).
- **Testy przed rundą:** 390/390. **Bramka leakage dla funding: 6/6 ZIELONA**
  (`test_funding_feature_no_leakage_truncate_vs_extend` i pokrewne) — zasada 2 spełniona
  PRZED wejściem cechy do modelu.

## Dlaczego H2 zostaje zamknięte, a to jest NOWA hipoteza

Licznik H2 jest **wyczerpany 1/1**, a serię zamknęła reguła STOP. **Nie obchodzę tego i nie
wznawiam H2.** Pytanie wraca jako nowa hipoteza z własnym licznikiem — dokładnie tą drogą,
którą kilka godzin temu przeszło momentum (hipoteza M).

Uzasadnienie jest to samo i opiera się na czterech faktach z archiwum:

1. **H2.1 nie odpowiedziało na pytanie.** Werdykt brzmiał **NIEROZSTRZYGNIĘTY**, z jednego
   konkretnego powodu: `n = 98 < 1 000`. Własna reguła projektu mówi wtedy: *„nie
   interpretujemy w żadną stronę"*. **Nierozstrzygnięcie nie jest negatywem.**
2. **Przeszkoda była instrumentalna, nie informacyjna.** Model odmawiał kierunku
   w **99,32%** świec. To nie funding zawiódł — zawiódł przyrząd.
3. **Przeszkoda została zmierzona i usunięta.** K2 → adopcja A1 → K3: na tej samej
   konfiguracji abstynencja 99,76% → 43,84%, próba **35 → 8 033**, pasmo 16,56 pp → 1,09 pp.
4. **Precedens M1 jest świeży i jednoznaczny.** Momentum było w identycznej sytuacji
   (niewykonalność pomiaru, nie brak edge'u), dostało nową hipotezę z licznikiem od zera
   i **zostało rozstrzygnięte**.

## Dlaczego akurat funding — i dlaczego to ostatni taki kandydat

**Wniosek skumulowany 11** wskazuje kierunek: `p` może ruszyć **nowy zbiór informacyjny**, a nie
kolejna transformacja OHLCV. **M1 ten wniosek wzmocnił** — momentum, ostatnia nieprzetestowana
gałąź OHLCV, wypadło przy 50%.

**P1** (`runs/2026-09-22_p1-sonda-zrodel-danych/`) sprawdziło, co jeszcze jest do wzięcia.
Wszystkie pięć endpointów pozycjonowania Binance — open interest, long/short ratio, pozycje
top traderów — oddaje **30,8 dnia** historii, a jawny `startTime` sprzed lat zwraca **HTTP 400**.
To **112 transakcji** wobec wymaganych 4 481: brakuje **40×**.

**Funding zostaje jako jedyne źródło spoza OHLCV, które projekt ma z wystarczającą historią**
(7 457 rozliczeń, 6,8 roku, zero dziur) — i którego nigdy nie zmierzył.

## Konfiguracja (ZAMROŻONA) i ramiona

Identyczna z H2.1, **z jedną różnicą: wagi klas `balanced`** (A1, przyjęte 2026-09-22).
To właśnie ta różnica czyni pomiar wykonalnym.

- **interwał** 4h, **V** = 3, **bramka reżimu** BRAK (`REGIME_ALL`)
- walk-forward **60/28/28**, seed **42**, historia **6,8 roku**
- funding doklejany przez `attach_funding_rate` (`merge_asof(direction="backward")`)

| ramię | cechy | warianty | rola |
|---|---|---|---|
| **A** (odniesienie) | `REVERSION_FEATURES` (4) | **0** | punkt odniesienia w tej samej konfiguracji |
| **B** (kandydat) | 4 + **`funding_rate`** | **1 — WYCZERPUJE licznik F** | przedmiot rundy |

**Dokładnie JEDNA zmienna** (zasada 4): obecność cechy `funding_rate`. Ramię A za 0 wariantów
wg uzasadnienia z H2.1 i M1: **próg opłacalności pochodzi z geometrii kosztu, a nie z obejrzanej
trafności**, więc pomiar odniesienia nie może przesunąć poprzeczki.

## Rachunek mierzalności (zasada 18)

Oczekiwane `n` ≈ **8 000** (K3 i M1 zmierzyły 8 033 i 8 512 na tej konfiguracji); próg
opłacalności ≈ **52,93%**; pasmo ≈ **1,09 pp**.

**Powtarzam ograniczenie z M1, bo obowiązuje tak samo:** wykrywalność zaczyna się od
**≈ 54,0%**. **Tej rundzie NIE wolno obiecywać odpowiedzi „funding działa"** — żeby to orzec,
funding musiałby wynieść trafność powyżej czegokolwiek, co ten projekt kiedykolwiek zmierzył.

**Pytanie odwrotne jest mierzalne z zapasem:** `required_trades` wobec progu przy trafności
rzędu 50–51% daje ~4 500, a mamy ~8 000 — **około 1,8× wymaganej próby przy mocy 80%**.
Runda ma moc orzec, że **funding nie wynosi trafności do progu opłacalności**.

**Dlatego runda startuje:** żeby zamienić „nie wiadomo" na liczbę — nie żeby znaleźć edge.

## Kryterium — zapisane PRZED uruchomieniem

- **POZYTYWNY:** `ci_low(p_B) > break_even_B`. Byłby to **pierwszy dodatni wynik w historii
  projektu**. Nie uruchamia niczego poza **szukaniem przecieku**, a dopiero potem replikacją
  na innym instrumencie (zasada 9). Żadnego wdrożenia.
- **NEGATYWNY:** `ci_high(p_B) < break_even_B` — funding nie wynosi trafności do progu.
- **NIEROZSTRZYGNIĘTY:** `n_B < 4 481` **albo** CI przecina próg. Wtedy **nie interpretujemy
  w żadną stronę** — precedens S1b, H2.1.
- **REGUŁA STOP:** jeden wariant. Po nim seria F zamknięta **niezależnie od wyniku**.

**Dodatkowo raportuję — jako obserwację, NIE kryterium:** różnicę `p_B − p_A` z przedziałem
ufności. M1 pokazało, dlaczego to konieczne: bez tego kusi napisać „funding wypadł lepiej",
gdy różnica jest szumem.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **Spodziewam się wyniku negatywnego.** Prior jest niski: wniosek 11 mówi, że nowy zbiór
  informacyjny **może** ruszyć `p`, a nie że ruszy. Funding jest **następny w kolejce**,
  a nie **rokujący**.
- **Jedyne ustalenie H2.1 dotyczyło LICZBY DECYZJI, nie trafności:** funding potroił je
  z 35 do 98. Model uznał go za informacyjny — ale „model chętniej działa" **nie znaczy**
  „model działa lepiej". Gdyby F1 znów pokazało wzrost `n` i nic więcej, byłoby to
  **powtórzeniem tego samego nieustalenia**, a nie wynikiem.
- **Wzrost `n` w ramieniu B jest więc SPODZIEWANY i sam w sobie nie jest odkryciem.**
  Zaraportowanie go jako sukcesu byłoby powtórzeniem błędu, przed którym K2 ostrzegało przy A2.
- **Świece sprzed pierwszego rozliczenia funding mają NaN** i wypadają jak rozbieg każdego
  wskaźnika. Liczbę odrzuconych świec raportuję jawnie w lejku.
- **Wynik pozytywny traktuję z podejrzliwością proporcjonalną do niezwykłości.** Funding to
  dana o **własnej siatce czasowej** (co 8h wobec świec 4h), więc jest to dokładnie ten typ
  cechy, przy którym przeciek jest najłatwiejszy. Bramka leakage jest zielona, ale przy
  wyniku pozytywnym pierwszym krokiem jest **ponowne sprawdzenie przyczynowości**, nie
  ogłoszenie.

## Czego ta runda NIE rozstrzygnie

- **Funding jako carry** (4A) — inne sformułowanie, odrzucone w H2.0 rachunkiem mocy na
  jednym instrumencie; żyje wyłącznie w wymiarze przekrojowym.
- **Funding jako bramka** (skrajne stawki) — odrzucony w H2.0, zagładza próbę.
- **Inne transformacje funding** (z-score, okna) — H2.0 zawęziło do surowej stawki
  z trzech powodów; reguła STOP zamyka serię po jednym wariancie.
- **ETH/SOL/BNB, inny target, dźwignia** — poza zakresem.
