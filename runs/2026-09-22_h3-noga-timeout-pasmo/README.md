# H3 — noga „timeout" w modelu kosztów: PASMO niepewności zamiast przerzucenia flagi (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Sekcje „Wynik", „Walidacja", „Wniosek" i „Rekomendacja"
> są celowo puste — zostaną wypełnione PO przebiegu. Wszystko poniżej sekcji „Reguła
> decyzyjna" zapisano **przed napisaniem linijki kodu produkcyjnego**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Skąd to się wzięło.** W poprzedniej rundzie napisałem, że prawdopodobnie przepłacamy
w rachunku kosztów. Gdy pozycja kończy się „z upływem czasu", zakładamy drogie wyjście po
cenie rynkowej — a przecież wiadomo z góry, kiedy to nastąpi, więc można by złożyć tańsze
zlecenie oczekujące. Oszacowałem oszczędność na 1 punkt procentowy poprzeczki.

**Sprawdziłem to dokładniej i moja teza się nie broni.** Z dwóch powodów:

1. **Pomyliłem się w rachunku.** Użyłem najdroższego możliwego kosztu zamiast tego, który
   naprawdę zmierzyliśmy. Prawdziwa poprzeczka to **52,66%**, a nie 53,12%. Czyli **prawie
   połowa rzekomej oszczędności nigdy nie istniała** — była moim błędem.

2. **Zlecenie oczekujące wymaga znajomości CENY, nie tylko czasu.** Przy wejściu i przy
   zyskownym wyjściu cenę znamy z góry. Przy wyjściu „z upływem czasu" znamy **moment**, ale
   nie cenę — a program liczy wyjście po cenie zamknięcia tej świecy. Żeby dostać *tę* cenę
   zleceniem oczekującym, trzeba by ją znać wcześniej. **Policzenie tańszej opłaty za cenę,
   którą można dostać wyłącznie drogo, to policzenie tej samej korzyści dwa razy.**

**Co wobec tego robimy.** Nie zmieniamy zachowania programu. Dokładamy przełącznik i puszczamy
ten sam test w obu wersjach — żeby sprawdzić, **czy to założenie w ogóle wpływa na decyzję**.
Przy okazji łatamy prawdziwą usterkę: koszt jest dziś liczony w dwóch miejscach niezależnie
i mogą się po cichu rozjechać.

**Czego ta runda NIE zrobi:** nie obniży poprzeczki. To jest zapisane z góry w regule D2 niżej,
żeby nie dało się tego zrobić po obejrzeniu wyniku.

---

## ID testu

**H3** — runda poprawności modelu kosztów. **0 wariantów** (pod warunkiem D5). Patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/H3-noga-timeout`
- **Poprzedzający stan (master):** `c2ecd19` (merge H2.0)
- **Decyzja użytkownika 2026-09-22:** po przedstawieniu obu kontrargumentów — *„Zmierzyć, ile
  to zmienia"*, z zachowaniem domyślnego zachowania.
- **Komenda:** `py -m backtest.run_timeout_leg_band` (pełny output: `raw_output.txt`)
- **Warianty:** **0** — patrz reguła **D5**, która określa warunek utrzymania tego zera.
- **Testy przed rundą:** 265/265.

## Poprzedzające wyniki (zasada 14)

- **H2.0** (`runs/2026-09-22_h2.0-funding-wykonalnosc/`) — wniosek skumulowany nr 16 w INDEX
  zapisał podejrzenie „`timeout → taker` to prawdopodobnie błąd". **Ta runda je rozstrzyga —
  na niekorzyść podejrzenia** (sekcja „Rozstrzygnięcie merytoryczne").
- **C2.12 / Z6** (`runs/2026-09-21_c2.12-execution-cost-model/`) — wprowadziło model maker/taker
  i obecne mapowanie `exit_reason → noga`. Precedens metodologiczny: nazwany wariant
  (`execution_model`) zamiast pokrętła, i to on daje dziś regresję baseline'u.
- **S1b** (`runs/2026-09-22_s1b-early-stopping-naprawiony/`) — dostarcza **konfigurację pomiaru
  i liczby odniesienia**: `n=345`, `cost_pct=0,000767`, `barrier_pct=0,014276`,
  `break_even_p=0,526862`, `share_timeout=0,60`.
- **C2d** — bramka kosztowa i diagnoza `range`; `tests/test_risk_controller.py` trzyma jej
  historyczny zapis, którego nie wolno naruszyć (patrz „Pułapka" w sekcji Testy).
- **Z19** — rachunek mocy przed eksperymentem; tutaj w wersji: **reguła decyzyjna przed pomiarem**.

---

## Rozstrzygnięcie merytoryczne (zapisane PRZED przebiegiem)

Kryterium, które tłumaczy całą obecną mapę nóg naraz:

> **Noga „maker" jest dobrze zdefiniowana tylko wtedy, gdy CENA zlecenia jest znana w momencie
> jego składania.** Zlecenie limit to para (cena, czas ważności) — nie da się złożyć limitu
> „na tę świecę, po cenie jaka wyjdzie".

| noga | cena znana z góry? | wyjście przymusowe? | dziś | spójne? |
|---|---|---|---|---|
| wejście | TAK (bieżący `close`) | NIE — brak fill = nie wchodzimy | maker | ✔ |
| `tp` | TAK (`entry + 1,5·ATR`, znane w chwili wejścia) | NIE — brak fill = transakcja trwa | maker | ✔ |
| `sl` | TAK, ale wyjście obowiązkowe | TAK | taker | ✔ |
| **`timeout`** | **NIE — znamy CZAS (świeca `t+V`), nie cenę** | TAK | taker | ✔ |

**Obecna mapa nie jest niedbała — jest implementacją tej zasady.** Timeout jest jedyną nogą,
gdzie znamy czas, a nie cenę. To klasyczny trade-off egzekucji: **albo pewny czas i nieznana
cena (market/taker), albo pewna cena i nieznany czas (limit/maker)**. Nie da się mieć obu.

**Drugi, twardszy argument — wewnętrzna niespójność wariantu „maker":** `engine.py:407-408`
liczy cenę wyjścia timeoutu jako `close` świecy timeoutu. Żeby dostać *ten* `close` zleceniem
limit, trzeba by znać go z wyprzedzeniem (lookahead) albo skrosować księgę. Naliczenie stawki
maker za cenę osiągalną wyłącznie taker-em to **policzenie tej samej korzyści dwa razy**.
Realistyczne „timeout → maker" wymagałoby własnego modelu ceny wyjścia (limit na poziomie X,
fill tylko gdy rynek do X dojdzie, inaczej pościg), co zmieniłoby `gross_pnl`, a nie tylko
`cost` — i złamałoby zasadę 4.

**Konsekwencja:** kraniec „maker" jest optymistyczny **nie tylko na opłatach, ale i na cenie**,
więc prawda leży **bliżej krańca taker**, niż sugerowałaby naiwna mieszanka pół na pół.

### Sprostowanie własnego błędu z H2.0

H2.0 policzyło próg **53,12%** z kosztu **bramkowego** `round_trip_cost_fraction(MAKER, TAKER)
= 0,0900%` — czyli tak, jakby KAŻDA transakcja wychodziła najdroższą nogą. Journal liczy koszt
per transakcja, a `tp` kosztuje 0,0400%. Faktycznie zmierzony koszt w S1b to **0,0767%**, czyli
próg **52,66%**.

| | próg |
|---|---|
| H2.0, koszt bramkowy 0,0900% | 53,12% ❌ |
| **faktycznie zmierzony, koszt 0,0767%** | **52,66%** ✔ |
| Z10 („najniższy próg w projekcie") | 52,69% — zgodne ✔ |

**Około 0,45 z rzekomej dźwigni 1,04 pp było artefaktem mojego rachunku, nie efektem nogi
timeout.** Realny efekt zmiany nogi to ~0,96 pp — i to przy założeniu, które powyżej podważyłem.

---

## Reguła decyzyjna — zapisana PRZED uruchomieniem czegokolwiek

Zabezpieczenie przed obniżeniem poprzeczki po obejrzeniu wyniku.

- **D1. Domyślna produkcyjna pozostaje `timeout_leg = TAKER`.** Ta runda z założenia nie może
  jej zmienić: spór jest o mechanikę rynku i rozstrzyga go argument o znanej cenie, nie słupki
  z backtestu. Zmiana domyślnej to osobna decyzja użytkownika z zapisanym uzasadnieniem.
- **D2. Pre-rejestrowany próg H2.1 wolno zrewidować WYŁĄCZNIE w stronę pesymistyczną.**
  Sprostowanie 53,12% → 52,66% — **TAK** (dotyczy obu krańców, niezależne od nogi timeout).
  Zejście do ~51,70% — **NIE**, dopóki obowiązuje D1.
- **D3. Jeśli oba krańce dają ten sam werdykt** — niepewność jest nieistotna decyzyjnie i tak
  się to zapisuje. Temat zamknięty na stałe. To najbardziej prawdopodobny i najcenniejszy wynik.
- **D4. Jeśli krańce rozstrzelają werdykt** — wynik brzmi **„NIEROZSTRZYGNIĘTE: decyzja zależy
  od nieznanej stopy wypełnienia"**, próg zostaje pesymistyczny, a jedyną drogą dalej jest runda
  **mierząca** tę stopę na danych o fillach (których nie mamy) — nie kolejne założenie.
- **D5. Licznik multiple-testing: 0 wariantów**, pod jawnym warunkiem, że raport respektuje
  zakaz z sekcji „Czego ta runda NIE raportuje". Precedens: **C2.12 policzono jako 1 wariant**
  właśnie dlatego, że raportował werdykt klasyfikacyjny na tych samych danych. Jeśli ta runda
  zacznie raportować werdykt — **konsumuje wariant H2 (0/1 → 1/1) i zamyka H2 przed H2.1**.
  Ten koszt jest zapisany z góry i to on dyscyplinuje.

---

## Projekt pomiaru (zapisany PRZED przebiegiem)

**Konfiguracja: ZAMROŻONA konfiguracja S1b** (`backtest/run_single_regime_4h.py:47-56`) —
4h natywne 6,8 roku, reżim `range`, V=3, walk-forward 60/28/28, `seed=42`.

Trzy powody: (1) **na tej konfiguracji target już widzieliśmy** (S1b opublikowane), więc
ponowny przebieg nie zużywa nowego spojrzenia; pomiar na konfiguracji H2.1 spaliłby darmowe
spojrzenie na baseline hipotezy, której jeszcze nie uruchomiliśmy; (2) konfiguracja H2.1 dziś
**nie jest uruchamialna** — `engine.py:223` filtruje po `regime`, więc „brak bramki" wymaga
zmiany silnika, co należy do H2.1 (zasada 4); (3) jest do czego porównać co do cyfry.

**Trzy przebiegi:** `timeout_leg=TAKER`, `timeout_leg=MAKER`, oraz kontrolny **bez argumentu**
(dowód bit-identyczności z baseline'em na realnych danych).

**Lista raportowanych liczb — zamknięta:** `cost_pct` średnia **i mediana** (zasada 16b) ·
rozbicie kosztu na **fee / slippage / funding** · `share_timeout` z CI · rozkład `exit_reason`
w sztukach · `barrier_pct` (asercja: identyczny) · `break_even_p` per wariant + delta w pp ·
**5 liczników lejka (muszą być identyczne co do sztuki)** · sprostowana tabela geometrii z H2.0.

**Walidacja drugą drogą (zasada 16a, obowiązkowa):** średni `cost_pct` z journalu vs policzony
analitycznie z mieszanki wyjść `s_tp·0,0004 + s_sl·0,0009 + s_to·(0,0009|0,0004) + funding`.

### Czego ta runda NIE raportuje i NIE interpretuje

**`hit_rate`, `ci_low`/`ci_high`, `z_stat`, `margin`, `classification` nie są wynikiem tej
rundy.** Trafiają do `raw_output.txt` (zasada 11 jest bezwarunkowa), ale sekcja „Wynik"
i decyzja ich nie używają.

Powód mechaniczny: `gross_pnl` jest z definicji niezależne od kosztu (pilnuje tego test
`test_run_backtest_gross_pnl_identical_across_timeout_leg`), więc `p` może się tu ruszyć
**wyłącznie przez selekcję** — inna ścieżka equity → inny moment kill-switcha. To byłby szum
selekcyjny, nie sygnał.

---

## Wynik

*(do wypełnienia po przebiegu)*

## Co na plus (+) / Co na minus (−)

*(do wypełnienia po przebiegu)*

## Walidacja (zasada 16a)

*(do wypełnienia po przebiegu — werdykt Ready / Caveats / Revision)*

## Przegląd diffu (zasada 16c)

*(do wypełnienia przed merge — werdykt jednym zdaniem)*

## Wniosek

*(do wypełnienia po przebiegu)*

## Rekomendacja

*(do wypełnienia po przebiegu)*

## Pełny surowy output

*(`raw_output.txt` — po przebiegu)*
