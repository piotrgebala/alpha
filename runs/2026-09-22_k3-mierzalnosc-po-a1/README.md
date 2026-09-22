# K3 — czy adopcja A1 przenosi się z wyroczni na REALNE cechy (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Sekcje „Wynik" i dalsze są celowo puste. Wszystko do sekcji
> „Arytmetyka oczekiwań" włącznie zapisano **przed napisaniem linijki kodu tej rundy**.

## ID testu

**K3** — kalibracja przyrządu. **0 wariantów, POZA wszystkimi licznikami hipotez** (ta sama
rola co K1, K2, Z19, Z9). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/K3-mierzalnosc-po-A1`
- **Poprzedzający stan (master):** `ab50fa0` (merge A1 — wagi klas przyjęte domyślnie)
- **Warianty:** **0** — patrz „Dlaczego to 0 wariantów".
- **Testy przed rundą:** 371/371.

## Poprzedzające wyniki (zasada 14)

- **K2** (`runs/2026-09-22_k2-naprawa-abstynencji/`) — zmierzyła, że wagi klas obniżają próg
  wykrywalności **na syntetycznej wyroczni**. Ta runda sprawdza, czy to samo dzieje się na
  realnych cechach. K2 sama zapisała to jako otwarte zastrzeżenie w Rekomendacji punkt 6.
- **Adopcja A1** (ADR w `docs/rag/03`) — `DEFAULT_CLASS_WEIGHT_MODE = balanced`. ADR zawiera
  jawne zastrzeżenie: A1 schodzi **poniżej** podłogi abstynencji, a na realnej cesze nie jest
  to zmierzone.
- **S1b** (`runs/2026-09-22_s1b-early-stopping-naprawiony/`) — `n = 345`, werdykt
  **NIEROZSTRZYGALNY** przy klauzuli `n < 925`.
- **H2.1** (`runs/2026-09-22_h2.1-funding-jako-cecha/`) — `n = 98`, werdykt
  **NIEROZSTRZYGNIĘTY** przy klauzuli `n < 1 000`, abstynencja **99,32%**.
- **K1** — próg wykrywalności; **jego liczba „~58%" została sprostowana w K2** jako artefakt
  siatki. Właściwością przyrządu jest `wald_half_width(n)`.
- **Z10** — pooled trafność projektu **50,27%** (n = 7 687). **H3** — próg opłacalności
  **52,69%**.

---

## Pytanie rundy

Dwie konfiguracje dostały werdykt „nierozstrzygnięty" **wyłącznie dlatego, że próba była za
mała** — nie dlatego, że coś zmierzono i wyszło źle. Obie mierzono modelem, który odmawiał
kierunku w 90,5% (S1b) i 99,32% (H2.1) świec.

Po adopcji A1 model tak już nie robi — **na wyroczni**. Pytanie brzmi: **czy na realnych
cechach też?**

To nie jest pytanie o zarabianie. To pytanie o to, czy wolno nam jeszcze cokolwiek mierzyć.

## Konfiguracje (ZAMROŻONE, obie odtworzone bez zmian)

| ID | konfiguracja | skąd | co dała przed A1 |
|---|---|---|---|
| **C1** | bramka reżimu `range`, 4h, V=3, `REVERSION_FEATURES` (4 cechy), walk-forward 60/28/28 | S1b (`run_single_regime_4h.py`) | `n = 345`, abstynencja 90,5% |
| **C2** | **bez bramki reżimu** (`REGIME_ALL`), reszta identyczna z C1 | H2.1 ramię A (`run_funding_feature_h21.py`) | `n = 98`, abstynencja 99,32% |

Każda konfiguracja biegnie w **dwóch ramionach**: `class_weight_mode="none"` (stan sprzed
adopcji) i `"balanced"` (stan po adopcji). Cztery przebiegi, zero nowych parametrów.

**Świadomie NIE dokładam ramienia z funding** (H2.1 ramię B) — licznik H2 jest wyczerpany
i seria zamknięta regułą STOP. Ta runda nie ma prawa go dotykać.

## Czego ta runda NIE raportuje — reguła D (wzorzec z H3, reguła D5)

**Trafność, `ci_low`/`ci_high`, `z_stat`, margines i klasyfikacja NIE są wynikiem tej rundy.**
Trafiają do `raw_output.txt` (zasada 11 jest bezwarunkowa), ale sekcja „Wynik" i decyzja ich
nie używają.

Powód nie jest kosmetyczny. Obie konfiguracje należą do **serii zamkniętych**: C1 do hipotezy
jednoreżimowej 4h (reguła STOP), C2 do hipotezy H2 (licznik 1/1 wyczerpany). Zaraportowanie ich
trafności byłoby **ponownym spojrzeniem na target w zamkniętej serii** — czyli wznowieniem
serii tylnymi drzwiami, bez pre-rejestracji i bez licznika. Runda pyta wyłącznie **„ile decyzji
podejmuje model"**, a to jest wielkość niezależna od tego, czy te decyzje są trafne.

**Jeśli ta runda zacznie raportować trafność — konsumuje wariant w zamkniętej serii, czego
reguła STOP zabrania. Wtedy runda jest nieważna, nie „ciekawa".**

## Co runda raportuje

Wielkości niezależne od targetu:

1. **Lejek w komplecie** — świece ocenione, odpadłe na abstynencji, na bramce pewności, na
   bramce kosztowej, sygnały, stłumione kill-switchem, w próbie (pytanie „kogo NIE ma
   w zbiorze", zasada 16a).
2. **Abstynencja** wobec podłogi wyznaczonej rozkładem etykiet.
3. **`n`** oraz **`wald_half_width(n)`** — szerokość pasma „opłacalne, ale niewidzialne".
4. **`break_even_p`** — wielkość czysto geometryczno-kosztowa (`0,5·(1+C/B)`), niezależna od
   trafności; potrzebna, żeby policzyć punkt 5.
5. **`min_detectable_hit_rate(break_even, n)`** — najniższa PRAWDZIWA trafność, którą przy tej
   próbie dałoby się odróżnić od progu opłacalności.

## Reguła odczytu — zapisana PRZED uruchomieniem

Kotwica nie jest wymyślona, tylko złożona z dwóch **zmierzonych** liczb projektu:

```
luka do zamknięcia = próg opłacalności − zmierzona trafność projektu
                   = 52,69% (H3) − 50,27% (Z10)
                   = 2,42 pp
```

Pasmo `wald_half_width(n)` mówi, czy w ogóle **zobaczylibyśmy** efekt tej wielkości:

| pasmo po A1 | odczyt |
|---|---|
| **< 2,42 pp** | przyrząd widziałby efekt dokładnie zamykający znaną lukę ⇒ konfiguracje wracają do gry **jako mierzalne** |
| **≥ 2,42 pp** | mimo poprawy nadal nie zobaczylibyśmy efektu zamykającego lukę ⇒ poprawa realna, ale niewystarczająca; priorytetem zostaje **T4** |
| **abstynencja nie spada** | **adopcja A1 NIE przenosi się z wyroczni na realne cechy** ⇒ do dopisania jako ograniczenie w ADR (`docs/rag/03`) |

To są **etykiety odczytu, nie bramki** — żadna z nich niczego nie zabija i nie ma tu
zamrożonego progu do przyszłego użytku (lekcja K2: projekt ma już dwa trupy po zamrożonych
progach). Liczba 2,42 pp obowiązuje w tej rundzie i wynika z dwóch opublikowanych pomiarów;
gdy którykolwiek się zmieni, zmieni się i ona.

## Arytmetyka oczekiwań — żeby runda nie mogła „potwierdzić hipotezy"

- **`n` MUSI wzrosnąć. To jest bliskie tautologii, nie odkrycie.** Wagi klas obniżają
  abstynencję z konstrukcji, a każda świeca, na której model przestaje milczeć, jest
  kandydatem na transakcję. **Zaraportowanie samego wzrostu `n` jako sukcesu byłoby
  oszustwem wobec samego siebie** — dokładnie ten błąd popełniłoby A2 w K2, gdyby nie
  zapisana z góry arytmetyka.
- **Wynik NIE jest przesądzony**, bo nie wiadomo, **o ile**. Na wyroczni model miał cechę,
  która zna prawdziwą etykietę w ułamku `q` przypadków; przy czterech cechach OHLCV posterior
  może pozostać skolapsowany mimo wag. **Możliwy jest wynik (c) — i byłby ważnym negatywem**,
  bo oznaczałby, że A1 kupiliśmy na syntetyku i nie działa tam, gdzie miało.
- **Więcej transakcji NIE znaczy lepszy pomiar** (wniosek skumulowany 26). Wąskie pasmo przy
  rozcieńczonym sygnale to dokładnie pułapka, w którą wpadło A2. Ta runda nie ma jak tego
  wykryć, bo nie patrzy na trafność — i **to ograniczenie jest zapisane z góry**, a nie
  dopisane po wyniku.
- **Ta runda nie może stwierdzić, że cokolwiek zarabia.** Może stwierdzić najwyżej, że
  pewne pytania wolno znów zadać.

## Dlaczego to 0 wariantów

Runda nie porównuje wariantów hipotezy i **nie patrzy na target**: raportuje liczebność,
abstynencję i geometrię kosztu. Ramiona `none`/`balanced` to stan sprzed i po zmianie, która
**już zapadła** (ADR), a nie dwaj kandydaci do wyboru. **Warunek utrzymania zera: żadna liczba
z K3 nie może być cytowana jako wynik hipotezy tradingowej ani jako powód wznowienia serii
zamkniętej regułą STOP.**

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
