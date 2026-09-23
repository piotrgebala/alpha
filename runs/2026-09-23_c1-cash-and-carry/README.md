# C1 — cash-and-carry z hedgem spot: czy funding da się zebrać bez ryzyka kierunku? (2026-09-23)

> **STATUS: ZAMKNIĘTA — C1a POZYTYWNY (pierwszy pozytywny odczyt w historii projektu — ale to
> przepływ kontraktowy, nie przewidywanie), C1b NEGATYWNY.** Kolejność w gicie: pre-rejestracja
> `a8ce150` → kod `ae169f4` → przebieg → wynik w commicie scalającym. Seria C: **2/2, STOP.**
> Walidacja (16a): **READY** (z jedną nieścisłością etykiety w `raw_output.txt`, opisaną niżej);
> przegląd diffu (16c): **Approve**. Punkt 2 zlecenia użytkownika 2026-09-23.

## Wynik w skrócie — prostym językiem (CLAUDE.md zasada 17)

**Tak — opłatę funding da się zebrać bez ryzyka kierunku, i to jest pierwszy dodatni wynik w tym
projekcie.** Ale trzeba go przeczytać ostrożnie: to nie jest „strategia, która przewiduje rynek",
tylko odsetki za pożyczanie dźwigni innym, obarczone ryzykami, których ta runda nie mierzyła.

| ramię | wynik na 8 h | rocznie na nominale | rocznie na KAPITALE (spot + depozyt) | werdykt |
|---|---|---|---|---|
| **C1a — zawsze w pozycji** | +0,0099 % [+0,0063; +0,0135] | **+10,9 %** [6,9; 14,8] | **+5,4 %** [3,5; 7,4] | **POZYTYWNY** |
| C1b — tylko po dodatnim fundingu | −0,0170 % [−0,0253; −0,0086] | −18,6 % | −9,3 % | NEGATYWNY |

**Skąd bierze się wynik C1a:** z samej opłaty — 60,2 % nominału przez 5,5 roku. Hedge robi to, co
ma robić: rozjazdy między kontraktem a spotem dały łącznie −0,13 % (prawie nic), a największe
obsunięcie skumulowanego wyniku to 0,64 %. Koszty raz na wejściu i raz na wyjściu: 0,38 %.

**Trzy zastrzeżenia, bez których ta liczba wprowadza w błąd:**
1. **Połowa zysku pochodzi z 2021 roku** (30,6 % z 60,2 %). Od 2022 opłaty są 3–10 razy niższe:
   na kapitale 2022 +2,1 %, 2023 +3,9 %, 2024 +6,0 %, 2025 +2,6 %, pierwsze półrocze 2026 +0,4 %
   w skali roku. Przedział ufności średniej z 5,5 roku NIE jest prognozą — uczciwa prognoza to
   „niskie jednocyfrowe procenty rocznie na kapitale, zmienne z roku na rok" (ostatnie 3 lata:
   3,6 % brutto).
2. **Krótka pozycja na kontrakcie wymaga depozytu, a BTC potrafi urosnąć o 90 % w miesiąc.** Bez
   dokładania depozytu z zysków na spocie pozycja zostałaby zlikwidowana. Runda tego nie
   modelowała — na żywo to główny problem inżynierski i główne ryzyko.
3. **Ryzyko giełdy** (pieniądze i coiny leżą na Binance), koszt kapitału, podatki — poza pomiarem.

**C1b (przełączanie po znaku fundingu) przegrywa z arytmetyką, jak zapisano przed startem:**
875 przełączeń po 0,19 % kosztuje 166 % nominału, a zbiera te same ~61 % opłat. Reguła
„wychodź, gdy przestają płacić" jest droższa niż to, co chroni.

**Czym ten wynik NIE jest:** nie jest edge'em w sensie tego projektu (trafność, przewidywanie).
Jest zmierzoną ekonomią produktu „pożycz dźwignię za opłatę". Czy ten produkt uruchamiać —
z zarządzaniem depozytem, limitem na giełdę i porównaniem z bezpieczną lokatą w dolarze — to
decyzja użytkownika, nie kolejna runda pomiarowa.

---

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
  wyrównanie funding ↔ świece) z testami (10, w tym hypothesis). **Komenda:**
  `py -m backtest.run_cash_and_carry_c1` (Windows: `PYTHONUTF8=1`; czyta wyłącznie cache
  i config; pełny output `raw_output.txt`; skrypt na `runs/ZAMROZONE.txt`; czas < 1 s).
  N_eff z `agents.labeling.effective_sample_size` (≤ n).

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

### 1. Kryterium (próg 0; pozytyw przy z_2 = 2,241)

| ramię | n | średni P&L / 8h | CI 95 % (N_eff) | mediana | t | N_eff | t_neff | rocznie nominał | rocznie kapitał | odczyt |
|---|---|---|---|---|---|---|---|---|---|---|
| **C1a** zawsze w pozycji | 6 019 | **+0,00992 %** | [+0,00632; +0,01353] | +0,00637 % | +24,8 | **286** | **+5,40** | **+10,87 %** [6,92; 14,81] | **+5,43 %** [3,46; 7,41] | **POZYTYWNY** |
| **C1b** po dodatnim fundingu | 6 019 | −0,01698 % | [−0,02531; −0,00864] | +0,00224 % | −17,3 | 322 | −3,99 | −18,59 % [−27,72; −9,46] | −9,29 % [−13,86; −4,73] | **NEGATYWNY** |

`N_eff = 286` z 6 019: opłata funding jest silnie trwała (autokorelacja lag-1 0,84, lag-30 0,52),
więc 5,5 roku okresów 8-godzinnych to ~290 niezależnych obserwacji. Mediana (0,0064 %) niżej
niż średnia (0,0099 %): rozkład prawoskośny — 31 % okresów siedzi dokładnie na stawce bazowej
0,0100 %, a wysokie stawki z 2021 ciągną średnią w górę.

### 2. Dekompozycja (suma za 5,5 roku, % nominału)

| ramię | okresy w pozycji | Σ funding | Σ hedge (Δ bazy) | Σ koszty | Σ P&L | przełączenia | max obsunięcie |
|---|---|---|---|---|---|---|---|
| C1a | 6 019 (100 %) | +60,23 % | −0,13 % | 0,38 % | **+59,72 %** | 1 | 0,64 % |
| C1b | 5 146 (85,5 %) | +61,08 % | +3,18 % | **166,44 %** | −102,18 % | 875 | 124,93 % |

Hedge zdejmuje ryzyko kierunku niemal doskonale: zmiany bazy sumują się do −0,13 %, a rozjazd
jednego okresu nie przekracza ±0,32 %. Rok 2021 wnosi 30,6 % z 60,2 % opłat.

### 3. Per rok (opisowo, bez werdyktów) — C1a

| rok | okresy | P&L / 8h | rocznie nominał | rocznie kapitał | Σ funding | Σ hedge |
|---|---|---|---|---|---|---|
| 2021 | 1 094 | +0,0278 % | +30,4 % | +15,2 % | +30,57 % | +0,01 % |
| 2022 | 1 095 | +0,0038 % | +4,1 % | +2,1 % | +4,16 % | −0,03 % |
| 2023 | 1 095 | +0,0071 % | +7,7 % | +3,9 % | +7,89 % | −0,17 % |
| 2024 | 1 098 | +0,0109 % | +12,0 % | +6,0 % | +11,93 % | +0,07 % |
| 2025 | 1 095 | +0,0047 % | +5,1 % | +2,6 % | +5,13 % | −0,01 % |
| 2026 (do 30.06) | 542 | +0,0007 % | +0,8 % | +0,4 % | +0,55 % | +0,01 % |

Ostatnie 3 lata (2023-07 → 2026-06, 3 287 okresów, brutto): **7,3 %/rok nominału = 3,6 %/rok
kapitału.** C1b per rok: koszty 14–50 % rocznie (73–264 przełączeń), P&L ujemny w każdym roku
poza 2021.

### 4. Ryzyko nogi short (opisowo — poza P&L)

Największy wzrost ceny perp: **+90 % w 30 dni, +112 % w 90 dni** (2021). Short 1× bez uzupełnień
depozytu z zysków spot zostałby zlikwidowany; produkt na żywo wymaga reguły przenoszenia
zysków ze spotu na depozyt (koszt, opóźnienie, ryzyko operacyjne) — nie mierzone. Baza:
std 0,051 %, p1/p99 [−0,076 %; +0,145 %] — nieduża, ale ujemna od 2022 (perp poniżej spot).

### 5. Mierzalność — ex ante vs ex post

Ex ante: se 0,00033 %/8h (szum hedgu, N_eff = n) → t ≈ 30. Ex post C1a: sd P&L 0,031 %, **N_eff
286**, se 0,00184 % → t_neff 5,40; wykrywalny efekt 0,0052 %/8h = 5,6 %/rok nominału.
**Rachunek ex ante niedoszacował szumu 5,6×:** brał autokorelację hedgu (brak), a nośnikiem
autokorelacji jest sam funding (lag-1 0,84). Werdykt się nie zmienia (5,40 > 2,24), lekcja
zapisana we wniosku skumulowanym.

## Co na plus (+)

- **Pierwszy pozytywny wynik z prawidłowo działającym przyrządem:** próg 0, dwa ramiona
  z korektą Bonferroniego, N_eff z autokorelacji, kryterium zapisane przed wynikiem, przewidziany
  z góry znak obu ramion (C1a +, C1b − z arytmetyki kosztów).
- **Mechanizm potwierdzony liczbą:** cały wynik to opłata (60,2 %), hedge ≈ 0 (−0,13 %),
  koszty 0,38 % — dekompozycja przeliczona drugą drogą co do 0,003 %.
- **Nowe źródło danych sprofilowane przed pomiarem:** spot 8h, 0 dziur, znaczniki identyczne
  z perp i funding; konwencja czasu (świeca = otwarcie; stawka na zamknięciu = otrzymana)
  zapisana i przetestowana.
- **Definicja P&L jest czystą funkcją z testami** (znak fundingu, wyrównanie, koszty przy
  przejściach, hypothesis) — kolejne warianty produktu mierzy się tym samym kodem.

## Co na minus (−)

- **Niestacjonarność:** średnia z 5,5 roku miesza 2021 (15 % na kapitale) z 2022–2026
  (0,4–6 %). CI średniej nie jest prognozą; właściwa prognoza to zakres per rok i ostatnie 3 lata.
- **N_eff = 286** — rozdzielczość ~5,6 %/rok nominału; różnic między latami nie da się testować.
- **Ryzyko likwidacji nogi short nie jest w P&L** — a to ono decyduje, czy produkt przeżyje
  rok taki jak 2021. Kapitał 2× nominał to założenie, nie pomiar.
- **Ryzyko giełdy/kontrahenta, koszt kapitału, podatki, zniżki opłat** — poza zakresem;
  wynik netto dla konkretnego rachunku będzie inny.
- **Baza mierzona na zamknięciach 8h**, wejście/wyjście po zamknięciu — poślizg 2 bp przyjęty,
  nie zmierzony; C1a wchodzi raz, więc to nieistotne, ale dla produktu z rebalansem depozytu już nie.
- **Etykieta w `raw_output.txt`:** „baza na wejściu C1a +0,076 %" to zamknięcie PIERWSZEGO
  okresu ramki, nie cena wejścia (zamknięcie świecy poprzedniej: +0,051 %); precyzyjna
  dekompozycja jest w walidacji niżej. Wartość opisowa, bez wpływu na kryterium; nie
  uruchamiamy ponownie skryptu dla etykiety.

## Walidacja (zasada 16a) — werdykt: **READY**

- **Drugą drogą:** Σ funding = 6 019 × 0,01001 % = **60,23 %** ✔; Σ P&L C1a = 60,23 − 0,13 − 0,38 =
  **59,72 %** ✔; **Σ hedge (zwroty proste)** = tożsamość logarytmiczna `ln((1+b_start)/(1+b_end))`
  = +0,0953 % (b_start +0,0511 %, b_end −0,0442 %) plus człon wariancji `½Σ(r_spot² − r_perp²)`
  = −0,2216 % → **−0,1263 %** wobec −0,1291 % w skrypcie (reszta = wyrazy trzeciego rzędu) ✔ —
  hedge „traci" 0,22 % przez 5,5 roku, bo perp jest odrobinę bardziej zmienny niż spot; koszty
  C1b = 875 przejść (z wejściem na starcie) + 1 zamknięcie = 876 × 0,19 % = **166,44 %** ✔;
  N_eff: autokorelacja fundingu lag-1 0,838, lag-3 0,754, lag-30 0,518 → 286 spójne ✔.
- **Konwencje (red flag pozytywu):** `f_next` = stawka rozliczona na ZAMKNIĘCIU okresu — to
  przepływ otrzymany, nie sygnał; short otrzymuje przy > 0 (test „short pays negative rates");
  C1b decyduje po `f_now` (stawka na otwarciu, znana) — test; hedge = `r_spot − r_perp` (short perp
  zarabia, gdy perp spada względem spot — test). Wynik nie może pochodzić z przecieku, bo nie ma
  w nim żadnej predykcji: opłata jest kontraktowa.
- **Kogo NIE ma:** okresy, w których short zostałby zlikwidowany (2021: +90 %/30 dni); koszt
  kapitału; ryzyko giełdy; zmiany opłat w czasie; świece sprzed 2021; poślizg przy wyjściu
  awaryjnym.
- **Red flag „idealnie potwierdza":** C1a wyszło dokładnie jak arytmetyka (11 % nominału) — bo to
  arytmetyka opłat, nie hipoteza o rynku; niespodzianką był N_eff (286), zapisany jako lekcja.
- **Rząd wielkości:** funding 0,01 %/8h = 11 %/rok, baza ±0,05 %, koszty 0,19 % na przełączenie,
  874 przełączenia = 60 %/rok — wszystko w zakresach sprzed pomiaru.

## Przegląd diffu (zasada 16c) — werdykt: **Approve**

Zakres: `backtest/carry_hedged.py` (nowy, czyste funkcje), `tests/test_carry_hedged.py` (10),
`backtest/run_cash_and_carry_c1.py`, `config/settings.yaml` (+`spot_fee_rate`), README rundy.

**Korektność:** (1) `align_carry_frame`: merge 1:1 po `timestamp` z `validate`, zbiory znaczników
muszą być identyczne (fail loud), `r = pct_change` zamknięć, `f_next = f_now.shift(−1)`, pierwszy
i ostatni okres odpadają — bez lookaheadu w decyzji (stan z `f_now`), a `f_next` to przepływ
otrzymany. (2) `hedged_carry_pnl`: koszty przy przejściach 0→1 i 1→0 + zamknięcie na końcu,
gdy `s = 1`; `n_switches` liczone spójnie; walidacja stanu {0, 1}. (3) `summarize_pnl`: N_eff ≤ n,
CI z `se_neff`, annualizacja ×1 095 i /2 (stała `CAPITAL_PER_NOTIONAL` nazwana). (4) Skrypt:
argumenty `get_ohlcv_cached` identyczne z nazwą pliku cache → bez sieci; funding z cache
(start z `timeframe_start_overrides["4h"]`) i filtr ≥ 2021.

**Edge-case'y:** pusta/1-elementowa ramka → `summarize_pnl` zwraca `{"n"}`; `max_runup` z NaN
na początku okna (rolling) — `max()` ignoruje NaN; `align` przy różnych zbiorach znaczników →
`ValueError` (test).

**Uwagi (bez blokady):** zwroty proste zamiast log — sumowanie `hedge` niesie człon wariancji
(−0,22 %); to własność definicji z pre-rejestracji (hedge rebalansowany co okres), zapisana
w walidacji; etykieta „baza na wejściu" w skrypcie odnosi się do zamknięcia pierwszego okresu
(kosmetyka raportu, opisane w „minusach").

**Przegląd bezpieczeństwa (`security-review`, wczytany przy nowym źródle danych):** diff nie
zawiera sekretów ani kluczy; nowe dane pobrane istniejącym fetcherem przez publiczne API ccxt
(bez uwierzytelniania); skrypt rundy nie otwiera połączeń sieciowych, nie wykonuje poleceń,
pisze tylko do stdout; `spot_fee_rate` to stała liczbowa. **Brak ustaleń.**

**Werdykt jednym zdaniem:** kod poprawny, definicja P&L z pre-rejestracji odtworzona
w testach, bez lookaheadu i bez sieci — **Approve**, do scalenia.

## Wniosek

Long spot + short perpetual na BTC zbiera opłatę funding bez ryzyka kierunku: **+5,4 %/rok na
kapitale [3,5; 7,4] za 5,5 roku, w tym 15 % w 2021 i 0,4–6 % w latach 2022–2026** (ostatnie
3 lata: 3,6 % brutto). Hedge działa (rozjazdy bazy ≈ 0, obsunięcie 0,64 %), koszty są pomijalne,
jeśli się nie przełącza; przełączanie po znaku fundingu (C1b) kosztuje 60 %/rok i przegrywa
z pewnością. To pierwszy dodatni wynik w projekcie, ale **innego rodzaju niż wszystkie
poprzednie pytania**: nie ma tu prognozy, jest kontraktowy przepływ za dostarczanie dźwigni —
z ryzykami (likwidacja nogi short bez uzupełnień depozytu, giełda, koszt kapitału), których
runda nie wycenia. Seria C zamknięta 2/2.

## Rekomendacja

1. **Decyzja bramkowa użytkownika, nie kolejna runda:** czy budować produkt cash-and-carry
   (zarządzanie depozytem z zysków spot, limit ekspozycji na giełdę, porównanie z bezpieczną
   lokatą w dolarze — w latach 2023–2025 rzędu 4–5 % rocznie, bez ryzyka giełdy). Przy 2–6 %
   rocznie na kapitale i ryzyku kontrahenta odpowiedź nie jest oczywista.
2. **Jeśli tak — następny krok to inżynieria, nie pomiar:** symulacja depozytu (uzupełnienia,
   próg likwidacji, koszt przenoszenia), stress na +90 %/30 dni, monitoring znaku fundingu
   z histerezą liczoną z kosztu (nie C1b), ETH jako drugi instrument dopiero po BTC (zasada 9).
3. **Nie testować wariantów pomiarowych** (progi na stawkę, inne interwały, zniżki opłat) —
   STOP 2/2; ich wynik wynika z arytmetyki.
4. **Metodologicznie (wniosek 56):** rachunek mocy dla szeregów z trwałym sygnałem musi brać
   autokorelację SYGNAŁU, nie tylko szumu — inaczej `se` wychodzi kilkakrotnie za małe.

## Użyte skille

Rejestr gałęzi `c1-cash-and-carry` (`py tools/skill_audit.py raport --galaz c1-cash-and-carry`):

| skill | co wniósł |
|---|---|
| `anthropic-skills:clas5-runda` | procedura: gałąź → skille → dane → profil → pre-rejestracja → kod → run → bramki → DoD |
| `anthropic-skills:clas5-quant` | przyrząd dla targetu „carry" (próg 0, brak trafności/BE), N_eff, koszty obu nóg, kapitał, ryzyko likwidacji jako ograniczenie, jedna zmienna między ramionami |
| `anthropic-skills:quant-strategy-catalog` | rodzina D2 z hedgem, pięć pól, mechanizm i kto traci, pułapki perpetuali (likwidacja, baza, zmiana znaku) |
| `data:explore-data` | profil nowego zbioru (dziury, duplikaty, zgodność znaczników, baza, konwencja otwarcie/zamknięcie) PRZED pomiarem |
| `security-review` | nowe źródło danych przez sieć: brak sekretów, publiczne API, skrypt bez sieci — brak ustaleń |
| `engineering:testing-strategy` | plan testów modułu `carry_hedged` PRZED napisaniem (znak, wyrównanie, koszty, hypothesis, fail loud) |
| `data:validate-data` | bramka 16a: dekompozycja drugą drogą (tożsamość bazy + człon wariancji), koszty C1b, N_eff z autokorelacji, konwencje |
| `data:statistical-analysis` | bramka 16b: mediana obok średniej, niestacjonarność (per rok, ostatnie 3 lata) zamiast CI jako prognozy, Bonferroni |
| `engineering:code-review` | bramka 16c (sekcja „Przegląd diffu") |

Z tabeli zasady 19 pominięte: `dataviz` (bez wykresów), `engineering:architecture` (decyzja
o produkcie należy do użytkownika — ADR dopiero po niej), `update-config`, `lean-research`,
`ta-toolkit` (bez AT).
