# P2 — sonda wykonalności carry przekrojowego (2026-09-22)

> **STATUS: PRE-REJESTRACJA.** Ten plik powstał i został zacommitowany PRZED napisaniem kodu
> i PRZED obejrzeniem jakichkolwiek danych poza listą symboli. Sekcje „Wynik", „Wniosek"
> i „Rekomendacja" zostaną dopisane po uruchomieniu — sekcje pre-rejestracji się nie zmieniają.

## ID testu

**P2** — sonda wykonalności hipotezy **4A** (`STATUS.md` §17, ETAP 4): carry przekrojowy.
**0 wariantów, POZA licznikami hipotez** — ta sama rola co H2.0, Z19 i P1: rachunek
wykonalności PRZED wydaniem wariantu. Warunek utrzymania zera: **runda nie liczy i nie
drukuje średniego zwrotu z ruchu cen ani łącznego P&L strategii** (patrz „Czego ta runda NIE
liczy").

## Metadane

- Branch: `worktree-p2-carry-porzadki` (od `master` @ `c1f121a`).
- Decyzja użytkownika: 2026-09-22, „wykonaj powyższe" w odpowiedzi na propozycję
  „B — tania sonda carry przekrojowego (bez modelu, 0 wariantów)".
- Dane: Binance USDS-M, historia funding (`/fapi/v1/fundingRate`) i świece dzienne
  (`/fapi/v1/klines`, 1d) dla wszystkich symboli z publicznego archiwum
  `data.binance.vision` (952 symbole, w tym wycofane). Zakres **2020-01-01 → 2026-07-01**
  (koniec jak w bazie projektu).
- Komenda: uzupełniona po uruchomieniu.

## Poprzedzające wyniki

- **H2.0** (`runs/2026-09-22_h2.0-funding-wykonalnosc/`) — carry na samym BTC: próg opłacalności
  spada **poniżej 50%** (48,13%), bo wypłata `(2p−1)·B + F > C` nie wymaga przewagi kierunkowej,
  gdy `F > C`. Ale moc 0,03–0,12×: w 6,8 roku mieści się tylko **1 240 nienakładających się
  okien 48h**. H2.0 zapisało: „żyje w formule PRZEKROJOWEJ, nie czasowej".
- **`STATUS.md` §17, rachunek mierzalności 4A** — przyjmował, że 20 instrumentów daje
  **160 660 transakcji** (20 × 8 033). **Ta runda sprawdza to założenie wprost i podejrzewa,
  że jest błędne:** koszyki monet w tym samym oknie czasowym są skorelowane (krypto chodzi
  razem, szczególnie w stresie — `docs/rag/01`, zasada 9, „4 instrumenty to nie 4× danych").
  Niezależną jednostką próby jest raczej **okno czasowe**, a przekrój zmniejsza ROZRZUT
  wyniku okna, a nie mnoży liczbę okien.
- **F1** — funding jako cecha KIERUNKOWA na BTC: 50,34%, brak efektu. To NIE przesądza o carry:
  carry nie przewiduje kierunku, tylko zbiera opłatę.
- **P1** — endpointy pozycjonowania mają 30 dni historii; **kontrola P1 potwierdziła, że
  `fundingRate` i `klines` mają historię od 2020** — to jest źródło danych tej rundy.
- **T1-diag** — funding nettuje się do zera przy long/short 50/50. Carry przekrojowy jest
  z założenia **strukturalnie niesymetryczny względem fundingu** (short tam, gdzie funding
  wysoki, long tam, gdzie niski), więc wyzwalacz z wniosku 33 jest tu aktywny: realny funding
  jest samą treścią hipotezy, nie poprawką kosztową.
- **H3** — realny koszt round-trip w modelu kosztów projektu: **0,0767%** (wejście maker,
  mieszanka wyjść). Użyty jako koszt podstawowy.

## Pytanie

Czy carry przekrojowy jest na tyle obiecujący i MIERZALNY, żeby wydać na niego wariant
(własną hipotezę z licznikiem od zera, pre-rejestracją i regułą STOP)?

## Konstrukcja (zamrożona)

**Uniwersum (bez błędu przeżywalności):** wszystkie symbole z archiwum `data.binance.vision`
kończące się na `USDT`, łącznie z wycofanymi. Wykluczone: kontrakty `TRADIFI_PERPETUAL`
(akcje/surowce — hipoteza dotyczy krypto) oraz stablecoiny jako aktywo bazowe
(`USDC`, `BUSD`, `TUSD`, `FDUSD`, `USDP`, `DAI`, `USDE`, `USD1`).

**Siatka okien:** nienakładające się okna 48h, start `t` = 2020-01-01 00:00 UTC + k·2 dni,
ostatnie okno kończy się ≤ 2026-07-01.

**Kwalifikacja symbolu w oknie `t` (wyłącznie dane sprzed `t`):**
- ≥ 30 dni historii funding przed `t`;
- istnieje świeca dzienna zamknięta dokładnie w `t` (cena wejścia).

**Uniwersum PODSTAWOWE — TOP50:** spośród zakwalifikowanych 50 symboli o największym obrocie
(suma `quote_volume` z 30 dni przed `t`). Powód: realnie handlowalny zbiór. **Wrażliwość —
ALL:** wszystkie zakwalifikowane.

**Sygnał (znany w `t`):** suma stawek funding z `[t − 48h, t)` — suma po CZASIE, bo część
symboli rozlicza się co 4h lub 1h, nie co 8h.

**Koszyki:** górny decyl sygnału → SHORT (otrzymuje dodatni funding), dolny decyl → LONG;
min. 2 symbole w koszyku; okno pominięte, gdy zakwalifikowanych < 20. Równe wagi.

**Wielkości per okno:**
- `F` = średnia z koszyka SHORT sumy funding w `[t, t+48h)` − średnia z koszyka LONG tej sumy
  (przychód z fundingu na jednostkę nominału każdej nogi);
- `C` = 2 nogi × `obrót` × `c_rt`, gdzie `obrót` = udział miejsc w koszyku zmienionych
  względem poprzedniego okna (pierwsze okno = 1), `c_rt` = **0,0767%** (podstawowy, H3);
  wrażliwość: `c_rt` = 0,14% (taker+poślizg na obu końcach) oraz `obrót` = 1;
- `R` = średni zwrot ceny koszyka LONG − średni zwrot ceny koszyka SHORT, zamknięcie→zamknięcie
  przez 48h; symbol wycofany w trakcie okna — zwrot do ostatniego dostępnego zamknięcia.

## Pomiary (zamrożone)

1. **Uniwersum i przeżywalność:** ile symboli, ile wycofanych, ile zakwalifikowanych okien;
   jaka część uniwersum istnieje TYLKO w archiwum (niewidoczna w bieżącej liście giełdy).
2. **Trwałość mechanizmu:** średnia po oknach korelacji rang (Spearman) sygnału z sumą funding
   w następnym oknie — czy wysoki funding dziś oznacza wysoki funding jutro.
3. **Ekonomia mechanizmu (górna granica):** `μ_net = średnia(F − C)` z CI95 (t-Studenta,
   błąd standardowy korygowany przez `N_eff` z autokorelacji szeregu `F − C`), mediana obok
   średniej. To jest zysk, GDYBY ruchy cen obu nóg się znosiły.
4. **Mierzalność pełnego testu:** `σ` = odchylenie standardowe szeregu `F − C + R` (bez
   drukowania jego średniej), `N_eff` z autokorelacji tego szeregu,
   `n_req = ((1,959964 + 0,841621) · σ / μ_net)²` okien (moc 80%, α = 5% dwustronnie).
   Porównanie `N_eff` dostępnych okien z `n_req`.
5. **Kontrola założenia z §17:** średnia korelacja zwrotów symboli w obrębie okna
   (przeciętna parowa korelacja w TOP50) i wynikająca z niej efektywna liczba niezależnych
   instrumentów `k_eff = k / (1 + (k − 1)·ρ̄)`.

## Kryteria decyzji (zamrożone przed uruchomieniem)

- **D1 — ekonomia:** dolny kraniec CI95 `μ_net` > 0 w uniwersum TOP50 przy koszcie podstawowym.
  Niespełnione ⇒ **NIEWYKONALNA ekonomicznie** (opłata nie pokrywa kosztów nawet przy
  założeniu, że ceny się znoszą — pełnego testu nie ma po co robić).
- **D2 — mierzalność:** `N_eff` dostępnych okien ≥ `n_req`. Niespełnione ⇒ **NIEMIERZALNA**
  (zasada 18: pełny test nie rozstrzygnąłby niczego).
- **Oba spełnione ⇒ WYKONALNA** — rekomendacja: postawić hipotezę **C** (carry przekrojowy)
  z licznikiem od zera, pre-rejestracją pełnego testu P&L i regułą STOP. **Decyzja bramkowa
  o jej uruchomieniu należy do użytkownika** (łamie zasadę 9 i wymaga nowej architektury).
- Wrażliwości (ALL, `c_rt` = 0,14%, `obrót` = 1) są raportowane opisowo i nie zmieniają werdyktu.

## Czego ta runda NIE liczy (warunek „0 wariantów")

- średniej `R` (zysku/straty z ruchu cen),
- średniej `F − C + R` (łącznego P&L), Sharpe'a ani krzywej kapitału.

`σ` i autokorelacja szeregu `F − C + R` są parametrami ubocznymi rachunku mocy (jak rozkład
etykiet w H2.0) — ich średnia jest liczona wewnątrz funkcji odchylenia standardowego, ale nie
jest zwracana ani drukowana. `F` jest liczone i raportowane, bo to mechanizm hipotezy (jak
„F realne" w H2.0).

## Ograniczenia znane z góry

- Koszt 0,0767% zmierzono dla BTC; altcoiny mają szersze spready — koszt realny wyższy
  (stąd wrażliwość 0,14%). Nie modelujemy wpływu na rynek przy małych monetach.
- Świece dzienne: cena wejścia/wyjścia z zamknięcia dnia, bez uwzględnienia momentu rozliczenia.
- Stablecoiny wykluczone listą stałą — rzadkie przypadki spoza listy mogą przeciec.
