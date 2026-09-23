# C1 — cash-and-carry z hedgem spot: czy funding da się zebrać bez ryzyka kierunku? (2026-09-23)

> **STATUS: PRE-REJESTRACJA (przed pomiarem).** Dane spot pobrane i sprofilowane (skill
> `data:explore-data`), rachunek mocy policzony z SZUMU hedgu i ŚREDNIEGO fundingu — **średni
> wynik hedgu (Δ) ani P&L nie były liczone**. Kod pomiaru i przebieg następują PO commicie tego
> pliku. Punkt 2 zlecenia użytkownika 2026-09-23 („wykonaj": kierunki spoza ceny i wolumenu),
> kierunek otwarty po P2 (wniosek 40: „żyje tylko wersja z hedgem spot — inny produkt").

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

**Pomysł:** na kontrakcie wieczystym (perpetual) co 8 godzin jedna strona płaci drugiej opłatę
„funding". Gdy jest dodatnia — a na BTC od 2021 jest dodatnia w 85 % rozliczeń — płacą ci,
którzy trzymają pozycję na wzrost, a dostają ci, którzy mają pozycję na spadek. Jeśli
jednocześnie kupimy tyle samo BTC na rynku spot (zwykłym), ruch ceny nam nie szkodzi: strata
na jednej nodze jest zyskiem na drugiej. Zostaje sama opłata minus koszty i minus drobne
rozjazdy między ceną kontraktu a ceną spot („baza"). To nie jest zakład o kierunek — to inny
cel niż wszystko, co dotąd mierzyliśmy.

**Jak mierzymy:** dla każdego okresu 8 h od 2021 liczymy wynik pary „long spot + short
perpetual" na 1 jednostkę nominału: otrzymany funding + (zmiana spot − zmiana perpetuala) −
koszty wejścia/wyjścia. Dwa ramiona:
1. **C1a — zawsze w pozycji** (produkt jako taki: raz wejść, trzymać, raz wyjść).
2. **C1b — w pozycji tylko wtedy, gdy ostatni funding był dodatni** (podręcznikowa reguła
   „zbieraj, gdy płacą"; każde przełączenie kosztuje obie nogi).

**Czego się spodziewamy (przed wynikiem):** C1a — dodatni wynik brutto rzędu 11 % rocznie
nominału (średni funding 0,0100 % na 8 h × 1 095 okresów), ale to wynik na NOMINALE; na
zaangażowanym kapitale (spot + depozyt pod kontrakt) jest o połowę mniejszy, a od 2022 funding
zmalał kilkukrotnie. C1b — **koszty przełączeń zjedzą wszystko:** od 2021 funding zmieniał znak
874 razy, każde przełączenie to ~0,38 % nominału, razem ~60 % rocznie wobec ~11 % z opłat.
Ten wniosek wynika z arytmetyki przed uruchomieniem; runda go potwierdzi liczbą, nie odkryje.

**Rzecz, której ta runda NIE mierzy, a która decyduje o produkcie na żywo:** krótka pozycja
na kontrakcie wymaga depozytu, a BTC potrafi urosnąć o 90 % w miesiąc (2021). Bez dokładania
depozytu z zysków na nodze spot pozycja zostałaby zlikwidowana. Runda mierzy ekonomię opłaty;
zarządzanie depozytem to osobny problem inżynierski, zapisany niżej jako ograniczenie.

---

## ID testu

**C1** — nowa hipoteza (rodzina D2 katalogu z hedgem spot), własny licznik: ramiona **C1a** i
**C1b** = 2 warianty, kontrola brak (próg = 0). Po rundzie: **2/2, STOP** (niżej).

## Metadane

- **Gałąź:** `c1-cash-and-carry` (od master `ca48872`).
- **Dane (zasada 20: od 2021-01-01):** funding BTC/USDT:USDT Binance USDS-M (cache,
  rozliczenia 00/08/16 UTC, 6 021 od 2021); świece **8h natywne** perp (`binanceusdm`) i **spot
  BTC/USDT (`binance`) — nowe źródło**, oba 6 021 świec 2021-01-01 → 2026-06-30 16:00, 0 dziur,
  0 duplikatów, znaczniki identyczne z rozliczeniami funding (profil niżej).
- **Konwencje:** znacznik świecy 8h = jej OTWARCIE; rozliczenie funding o `T` przypada na
  zamknięcie świecy otwartej o `T − 8h`. Okres `t` = świeca otwarta o `T_t`; funding OTRZYMANY
  w okresie `t` = stawka rozliczona o `T_{t+1}` (znak Binance: dodatnia = long płaci short).
  Stan pozycji `s_t ∈ {0, 1}` ustalany o `T_t` na podstawie informacji znanych o `T_t`.
- **Koszty:** spot 0,10 % za stronę (`costs.spot_fee_rate`, Binance Spot VIP0, bez zniżki),
  perp taker 0,05 %, poślizg 2 bp na każdej nodze → wejście (kup spot + sprzedaj perp) 0,19 %
  nominału, wyjście 0,19 %; brak fundingu na spocie; brak kosztu kapitału (zapisane jako
  ograniczenie).
- **Kapitał:** nominał spot (1,0) + depozyt pod short perp przyjęty jako 1,0 nominału (dźwignia
  1×) → **kapitał = 2× nominał**; zwrot na kapitale = zwrot na nominale / 2. Bez modelowania
  likwidacji i uzupełnień depozytu (ograniczenie).
- **Kod:** czyste funkcje w `backtest/carry_hedged.py` (P&L per okres, koszty przełączeń,
  wyrównanie funding ↔ świece) z testami; skrypt `backtest/run_cash_and_carry_c1.py` (po tej
  pre-rejestracji; komenda przy zamknięciu, wpis na `runs/ZAMROZONE.txt`). N_eff z
  `agents.labeling.effective_sample_size` (≤ n).

## Poprzedzające wyniki (zasada 14)

- **P2 (wniosek 40):** carry przekrojowy BEZ hedgu — funding pokrywa koszt (F − C = 0,097 % na
  48 h, CI [0,051; 0,143]), ale ruch cen koszyka 57× większy od opłaty → niemierzalne; „żyje tylko
  wersja z hedgem spot (cash-and-carry) — inny produkt". Ta runda jest tym produktem, na BTC.
- **F1 (wniosek 37):** funding jako CECHA kierunkowa — 50,34 %, zero; tu funding jest
  TARGETEM (przepływem), nie sygnałem — inne pole katalogu.
- **T1-diag (wniosek 33):** stała 0,0001 trafna; „strategia jednostronna unieważnia symetrię
  fundingu" — tu pozycja jest jednostronna (short perp), więc używamy REALNYCH stawek.
- **H2.0 (wniosek 14):** carry zmienia nierówność na `(2p−1)·B + F > C`; przy hedgu spot człon
  kierunkowy znika — zostaje `F − Δbasis − C`.
- **W1 (wniosek 42):** koszt round-trip perp mierzony realistycznie; tu dochodzi noga spot.

## Profil danych (skill `data:explore-data`, przed pomiarem)

| co | wynik |
|---|---|
| spot / perp / funding od 2021 | 6 021 / 6 021 / 6 021 wierszy; duplikaty 0 / 0 / 0; dziury na siatce 8h: 0 |
| zgodność znaczników | spot = perp = funding (zbiory identyczne); godziny 0/8/16 UTC |
| ceny ≤ 0, wolumen 0 | 0 |
| baza (perp − spot)/spot na zamknięciu | średnia −0,019 %, mediana −0,040 %, std 0,051 %, p1/p99 [−0,076 %; +0,145 %], min/max [−0,23 %; +0,37 %] |
| baza per rok (średnia) | 2021 +0,037 %; 2022 −0,045 %; 2023 −0,025 %; 2024 −0,005 %; 2025 −0,043 %; 2026 −0,049 % |
| szum hedgu Δ = r_spot − r_perp per 8h | std **0,0255 %**, p1/p99 [−0,074 %; +0,069 %], max |Δ| 0,32 %, N_eff = n (brak autokorelacji) |
| funding od 2021 | średnia **0,0100 %/8h**, mediana 0,0079 %, std 0,0196 %, dodatni 85,5 %, dokładnie 0,0100 % (stawka bazowa) 31,4 %; per rok: 2021 0,028 %, 2022 0,0038 %, 2023 0,0072 %, 2024 0,0109 %, 2025 0,0047 %, 2026 0,001 % |
| przełączenia znaku fundingu | **874** od 2021; epizody ≤ 0 średnio 2,0 okresu (16 h) |
| ryzyko shorta (opisowo) | max wzrost perp w 30 dni **+90 %**, w 90 dni **+112 %** |

Uwaga: baza od 2022 jest ujemna (perp poniżej spot na zamknięciach 8h) mimo dodatniego
fundingu — to poziom, nie zmiana; do P&L wchodzi tylko ZMIANA bazy (plus baza w chwili
wejścia i wyjścia). Zapisane, żeby nie „odkrywać" tego po wyniku.

## Rozstrzygnięcia projektowe (zapisane PRZED przebiegiem)

### Pięć pól katalogu

| pole | wartość |
|---|---|
| zbiór informacyjny | funding + baza spot/perp (NIE OHLCV jako sygnał) |
| formuła | jednoaktywowa (BTC), pozycja parowa spot/perp |
| target | **carry (przepływ)** — nie kierunek |
| horyzont | okresy 8h; pozycja dni–miesiące |
| status | NIETKNIĘTE (D2 z hedgem, po P2) |

**Mechanizm jednym zdaniem:** lewarowani długo płacą za utrzymanie pozycji — kto traci po
drugiej stronie, to long z dźwignią, który godzi się płacić za ekspozycję bez kapitału; hedge
spot zdejmuje z nas ryzyko kierunku, zostawiając opłatę, bazę i koszty.

### Definicja P&L (identyczna w kodzie i tutaj)

Dla okresu `t` (świeca 8h otwarta o `T_t`, zamknięta o `T_{t+1}`), przy stanie `s_t`:

```
pnl_t = s_t · [ f_{t+1} + (spot_{t+1}/spot_t − 1) − (perp_{t+1}/perp_t − 1) ]
        − koszt_wejścia · 1[s_t = 1, s_{t−1} = 0] − koszt_wyjścia · 1[s_t = 0, s_{t−1} = 1]
```

- `f_{t+1}` — stawka rozliczona o `T_{t+1}` (short otrzymuje, gdy > 0; płaci, gdy < 0),
- ceny = zamknięcia świec 8h (`spot_t` = zamknięcie świecy `t−1`, czyli cena o `T_t`),
- koszt wejścia = koszt wyjścia = 0,10 % + 0,02 % (spot) + 0,05 % + 0,02 % (perp) = **0,19 %**,
- C1a: `s_t = 1` dla wszystkich `t` (koszt wejścia w pierwszym okresie, wyjścia w ostatnim);
- C1b: `s_t = 1[f_t > 0]` — stawka rozliczona o `T_t` (znana w chwili decyzji).

Jednostki: % nominału na okres. Roczny zwrot na nominale = średnia × 1 095; **na kapitale** = /2.

### Kryterium — zapisane PRZED uruchomieniem (dwa ramiona → Bonferroni m = 2)

Statystyka nośna: średni `pnl_t` per okres (% nominału) z CI 95 % i `t_neff`
(`N_eff = min(n, N/(1 + 2Σρ))` z szeregu `pnl_t` ramienia). Próg = 0 (nie ma trafności ani
break-even — target to przepływ).

- `z_2 = Φ⁻¹(1 − 0,025/2) = 2,241`.
- **POZYTYWNY (ramię):** `t_neff > 2,241`, czyli dolny kraniec CI średniego P&L netto przy z_2
  leży powyżej zera. Raportowany razem z rocznym zwrotem netto **na kapitale** i jego CI —
  o tym, czy to jest warte uruchamiania (materialność wobec ryzyka giełdy/likwidacji), decyduje
  użytkownik; runda nie ustala progu materialności (zasada 18: bez zamrożonych stałych).
- **NEGATYWNY (ramię):** górny kraniec CI 95 % (1,96) średniego P&L netto poniżej zera.
- **NIEROZSTRZYGNIĘTY:** wszystko inne.
- **Granica dużego n:** oba warunki monotoniczne; przy prawdziwym efekcie 0 żaden nie zapala
  się częściej niż α.
- **Dekompozycja** (obserwacja, nie kryterium): Σ funding, Σ Δ (baza), Σ koszty per ramię;
  tabela per rok; obsunięcie skumulowanego P&L; max niekorzystny ruch nogi short w 30/90 dni.

### Rachunek mierzalności (zasada 18)

`n = 6 020` okresów (5,5 roku × 1 095), `N_eff = 6 020` (Δ bez autokorelacji). Szum: std Δ
0,0255 % → `se = 0,00033 %` na okres. Sygnał: średni funding 0,0100 % → `t ≈ 30`. Wykrywalny
efekt (moc 80 %): **0,00092 %/8h ≈ 1,0 %/rok nominału (0,5 %/rok kapitału)**. Werdykt:
**MIERZALNA** z zapasem — i tak samo dla C1b, gdzie oczekiwany efekt (koszty ~60 %/rok) jest
rząd wielkości większy od rozdzielczości.

### Reguła STOP (seria C)

Po C1 licznik 2/2. Zakazane po wyniku: progi na stawkę („wchodź, gdy funding > x"), histereza,
inne interwały rebalansu, inne monety (ETH/…), zniżki opłat, noga maker na perp — każde to
nowy wariant; pozytyw C1a ewentualnie otwiera OSOBNĄ decyzję użytkownika o produkcie
(zarządzanie depozytem, ryzyko giełdy), nie kolejną rundę pomiarową.

### Arytmetyka oczekiwań

- C1a: brutto ≈ 0,0100 %/8h = 11,0 %/rok nominału z fundingu, ± wkład bazy (nieznany, oczekiwany
  ≈ 0 w zmianach), koszty 0,38 % raz → oczekiwany werdykt POZYTYWNY na nominale, na kapitale
  ≈ 5 %/rok; **od 2022 funding 3–10× niższy niż w 2021** (2022: 0,0038 %/8h = 4,2 %/rok nominału =
  2,1 %/rok kapitału) — rok 2021 może nieść większość wyniku; tabela per rok to pokaże.
- C1b: 874 przełączeń × 0,38 % = 332 % nominału w 5,5 roku ≈ 60 %/rok kosztów wobec ≈ 11 %/rok
  z fundingu → oczekiwany werdykt NEGATYWNY. Pomiar potwierdza arytmetykę, nie odkrywa.
- Red flag zapisany z góry: jeśli wkład bazy okaże się duży i dodatni — sprawdzić wyrównanie
  znaczników (spot/perp) i znak konwencji fundingu, zanim cokolwiek powiemy.

### Czego runda NIE raportuje i NIE interpretuje

Likwidacji i uzupełnień depozytu (opisowo tylko max ruch nogi short); ryzyka giełdy; kosztu
kapitału i alternatywnej stopy; podatków; zniżek opłat; wersji na innych monetach; progów
wejścia. Per-rok = tabela opisowa, nie werdykty.

### Kogo NIE ma w zbiorze

Świece sprzed 2021 (zasada 20); okresy, w których hedge byłby zlikwidowany (nie modelowane —
seria zakłada nieograniczony depozyt); różnice między ceną zamknięcia 8h a ceną wykonania
(wejście/wyjście raz w C1a, 874× w C1b: poślizg 2 bp na nogę przyjęty); zmiany stawek opłat
w czasie (przyjęte dzisiejsze VIP0).

## Definition of Done tej rundy

- `backtest/carry_hedged.py` (czyste funkcje) + testy: znak fundingu (short dostaje przy > 0),
  wyrównanie `f_{t+1}` do świecy `t`, koszt tylko przy zmianie stanu, C1a koszt na obu końcach,
  hedge doskonały (spot = perp → P&L = funding − koszty), własność hypothesis (P&L addytywny
  w stanie; przy `s = 0` P&L = koszty wyjścia albo 0).
- Skrypt = neutralny reporter; werdykt w README. Bramki 16a–c; `raw_output.txt`; INDEX
  (wiersz, licznik C = 2/2, wnioski); STATUS; README (kamień milowy); ZAMROZONE; „Użyte skille".

## Wynik

_(po przebiegu)_

## Co na plus (+) / Co na minus (−)

_(po przebiegu)_

## Walidacja (zasada 16a)

_(po przebiegu)_

## Przegląd diffu (zasada 16c)

_(po przebiegu)_

## Wniosek

_(po przebiegu)_

## Rekomendacja

_(po przebiegu)_

## Użyte skille

_(po przebiegu — z `py tools/skill_audit.py raport --galaz c1-cash-and-carry`)_
