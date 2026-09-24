# SH1 — sonda 15 nowych hipotez: żadna nie jest mierzalna, za to wyszedł błąd w danych (2026-09-24)

> **STATUS: ZAMKNIĘTA — 0 kandydatów do rundy, 0 wariantów.** 15 pomysłów z 4 kierunków → 10 po
> scaleniu → każdy sprawdzony przez „przeciwnika” (dane pobrane naprawdę, powtórki, rachunek mocy,
> mechanizm). **9 × NIEMIERZALNY, 1 × SŁABY MECHANIZM.** Efekt uboczny ważniejszy od hipotez:
> **uniwersum `data/raw/universe` obcięte w połowie alfabetu** (287 z 685 kontraktów) → runda RU1.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Szukaliśmy nowych pomysłów tam, gdzie projekt jeszcze nie zaglądał: popyt spoza Binance (Korea,
stablecoiny, ETF-y), makro (stopy, Fed), kalendarz (fixing ETF, odblokowania tokenów, funding)
i dane z łańcucha (aktywne adresy, Wikipedia). Każdy pomysł dostał osobnego „adwokata diabła”,
który pobrał dane i policzył, czy na 5 latach historii w ogóle da się go sprawdzić. W każdym
przypadku niepewność pomiaru była **2–5 razy większa** niż realistyczny efekt — czyli wynik nic by
nie rozstrzygnął (zasada 18). Na tej historii da się wykryć tylko efekty rzędu ≥ 20–25 % rocznie
na koszyku albo kilku procent na zdarzenie przy setkach zdarzeń, a żadna z hipotez takiej siły nie
obiecywała.

## ID testu

SH1 — sonda hipotez (przegląd, bez pomiaru przewagi).

## Metadane

- Przepływ wieloagentowy (16 agentów: 4 poszukiwaczy × kąt, scalanie, 10 weryfikatorów-przeciwników,
  synteza); agenci tylko czytali repo, pliki pomocnicze w scratchpadzie sesji. Zakaz liczenia
  zależności kandydata od przyszłych zwrotów — żaden agent nie oglądał wyniku hipotezy.
- Pełny zapis: `raw_output.txt` (logi, ranking, 10 werdyktów z pełnymi uzasadnieniami, 5 odrzuconych
  przy scalaniu).

## Poprzedzające wyniki

Wnioski 39 (zbiór informacyjny OHLCV wyczerpany), 40 (liczba monet ≠ liczba obserwacji), 67
(on-chain, DVOL, F&G jako cechy 4h), 71 (NL1), 72/80 (premia Coinbase), 79 (NC1); „Stan wiedzy —
skrót” → Otwarte: nowe źródła popytu.

## Pre-rejestracja

Cel sondy (zapisany w poleceniu przepływu przed startem): kandydat przechodzi dalej tylko z darmowymi
danymi z historią ≥ 2022, mechanizmem („kto traci i dlaczego się godzi”) i projektem mierzalnym
według faktów projektu (jedno aktywo ±29 %/rok na 5,5 roku; sygnały per moneta ±17 %/rok;
zdarzenia z błędem odpornym na skupiska). Werdykty: KANDYDAT / NIEMIERZALNY / POWTÓRKA /
BRAK_DANYCH / SŁABY_MECHANIZM; przy wątpliwości — negatywny.

## Wynik

| hipoteza | niepewność pomiaru | realistyczny efekt | werdykt |
|---|---|---|---|
| UN1 duże odblokowania tokenów (short) | ±2,9–3,2 % na zdarzenie | 0–2 % | NIEMIERZALNY |
| FS1 godzina po skrajnym fundingu | trzeba ~0,125 % brutto | 0,01–0,03 % | SŁABY MECHANIZM |
| EF1 godzina fixingu ETF | ±0,047 %/dzień (2,5 roku) | 0,01–0,03 % | NIEMIERZALNY |
| FL1 pierwszy listing na Upbit/Coinbase | ±4,5–7,0 % | 2–5 % | NIEMIERZALNY |
| UW2 skok uwagi w Wikipedii | ±1,3–2,0 pkt | ≤ 1 pkt | NIEMIERZALNY |
| SE1 napływ stablecoinów na łańcuch | ±1,65–1,9 % | 0,5–1,2 % | NIEMIERZALNY |
| KU1 udział Korei w obrocie (ranking) | ±0,92 Sharpe’a | 0–0,5 | NIEMIERZALNY |
| MS1 niespodzianki stóp (FOMC/CPI/NFP) | ±1,07 % na zdarzenie | 0–0,5 % | NIEMIERZALNY |
| AA1 aktywne adresy (ranking) | ±14–16 %/rok | 0–6 %/rok | NIEMIERZALNY |
| FD1 dryf przed FOMC | ±0,85 % (n = 36 od 2022) | 0,3–0,6 % | NIEMIERZALNY |

Odrzucone przy scalaniu: CB1 (podzbiór FL1), CU1 (KU1 z odwrotnym znakiem), UW1 (UW2 odwrotnie),
MV1 (to samo źródło co AA1), BB1 (kolejny ranking z cen koszyka, ~30 odczytów).

**Znalezisko danych (sprawdzone niezależnie przez Claude'a w sesji):** `data/raw/universe` ma 287
plików świec: A–G prawie komplet, z H–Z tylko 12 symboli; archiwum P2 ma 685. Skład top-20 według
agenta różnił się w 2025-08 → 2026-06 średnio na 5,5 z 20 miejsc (~28 %). Dotyczy TS1, TR1, X1,
X2, R1, TF1, TL1, LQ1, SZ1, NL1, P2; nie dotyczy CP1/CP2 (BTC/ETH/SOL), modeli na BTC, NC1
ani dziennika (osobne, pełne dane). → runda RU1.

## Co na plus (+) / Co na minus (−)

**(+)** Dziesięć pomysłów zamkniętych bez zużycia ani jednego odczytu na historii; każdy werdykt
oparty na danych pobranych w sesji, nie na pamięci. Wykryty błąd danych, który przeoczyło ~10 rund.
**(−)** Rachunki mocy robili agenci; w kilku przypadkach (KU1, AA1, UW2) liczyli rozrzut na
prawdziwych szeregach H0 — bez oglądania średniej sygnału, ale to i tak dotknięcie danych przyszłych
zwrotów; zapisane dla przejrzystości. Realistyczne efekty to oceny z literatury — mogą być zaniżone.

## Walidacja (16a)

`data:validate-data` — nie wczytany osobno w tej rundzie: kluczowe znalezisko (liczba plików
w `data/raw/universe` po literach: A 69, B 58, C 41, D 28, E 22, F 26, G 10, H–Z łącznie 12)
przeliczone przez Claude'a niezależnie od agenta (`ls` + zliczenie); archiwum 685 potwierdzone logiem
pobieracza. Werdykt: **Caveats** (rachunki mocy agentów nieprzeliczone w całości).

## Wniosek

**Prostym językiem:** na 5 latach danych dziennych prawie żadnego nowego pomysłu na „zakład
o kierunek” nie da się uczciwie sprawdzić — szum jest dużo większy niż efekty, jakich można się
spodziewać. Nie znaczy to, że te pomysły nie działają; znaczy, że historia ich nie rozstrzygnie.
Najcenniejsze w tej sondzie okazało się co innego: znaleźliśmy dziurę w danych, na których stały
nasze najlepsze wyniki (trend, momentum, portfel). Ją naprawiamy w pierwszej kolejności (RU1).

## Rekomendacja

1. RU1 — uzupełnić uniwersum i przeliczyć TS1, X1, SZ1 (w toku).
2. Przed kolejną sondą — tani filtr: efekt z badań PO publikacji ≥ 1,4 × niepewność pomiaru.
3. Opcjonalnie: codzienne migawki harmonogramów odblokowań (DefiLlama), bo tych danych nie da się
   odtworzyć wstecz — niski priorytet.

## Użyte skille

Rejestr `runs/skille/sonda-hipotez.jsonl`: `anthropic-skills:quant-strategy-catalog` — rodziny,
pięć pól i brama danych w poleceniach dla agentów. Pominięte: `data:statistical-analysis`
(rachunki mocy w werdyktach agentów, nie w tej rundzie), `engineering:code-review` (brak kodu
w repo), `dataviz`.
