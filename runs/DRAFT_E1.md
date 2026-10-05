# Karta hipotezy E1 — kaskady likwidacji: powrót ceny po wymuszonej sprzedaży/kupnie (2026-10-05)

> **STATUS: KARTA ZAPISANA; RACHUNEK MIERZALNOŚCI: NIEMIERZALNA (2026-10-05, §13) — odczyt nie startuje.** Pre-rejestracja (zadanie 011). Część A (§1–§12: definicja, target, koszty, kryterium, licznik, data
> odczytu) zapisana i zacommitowana **PRZED policzeniem jakiegokolwiek zdarzenia** na danych LK0/LB0 i bez żadnej
> ceny po likwidacji. Dowód kolejności: commit, w którym ten plik i `backtest/e1_kaskady.py` pojawiły się po raz
> pierwszy (`git log --diff-filter=A --format=%H -- runs/DRAFT_E1.md`). Część B (§13: realna częstość i rachunek
> mierzalności) dopisana w następnym commicie, z wydrukiem w `runs/2026-10-05_e1k-karta-kaskad/raw_output.txt`.
> **Licznik odczytów E1 = 0.** Zgoda użytkownika: 2026-09-29 „Wszystkie 008–014”; zależność 004 zamknięta jako STOP (wn. 115).

## 1. Pięć pól katalogu (`quant-strategy-catalog`)

| Pole | Wartość |
|---|---|
| Zbiór informacyjny | likwidacje na żywo: Bybit pełne (LB0, od 2026-09-27), Binance próbka (LK0, od 2026-09-25); obrót koszyka z `dziennik/koszyk.csv` |
| Formuła | zdarzeniowa, jednoaktywowa per moneta koszyka top-20 (transakcja na monecie, w której była kaskada); jednostką testu jest dzień UTC (§6) |
| Target | zwrot ceny w 24 h PRZECIW zlikwidowanym (powrót po przestrzeleniu) |
| Horyzont | 24 h (zdarzenia rzadkie, nieregularne) |
| Status CLAS-5 | ZBIERANE dane (wn. 102, 106); HL zamknięte (wn. 115); mapa 007: BRAK DANYCH, mechanizm mocny, efekt z literatury bez źródła dla tego sygnału (zadanie 026) |

## 2. Mechanizm (jedno zdanie)

Zlikwidowany gracz MUSI zamknąć pozycję po każdej cenie, więc w kaskadzie wymuszone zlecenia rynkowe przestrzeliwują
cenę ponad informację, a cierpliwa strona, która dostarcza płynność, dostaje premię, gdy cena wraca (Coval–Stafford 2007,
Brunnermeier–Pedersen 2009; na krypto pokrewnie Miralles-Quirós 2022 — liczby tylko z indeksu wyszukiwarki, **niepewne**).

## 3. Hipoteza (falsyfikowalna)

Średni zwrot netto (po koszcie C = 0,5 % i fundingu) transakcji „24 h przeciw zlikwidowanym” po kaskadzie z §4,
uśredniony per dzień UTC wejścia, jest dodatni: t_neff > 1,96 ORAZ ci_low(p) > p\* (§6).
Zakładany efekt brutto do rachunku mocy (zadanie 026, `docs/przeglad_literatury_cp1_e1.md` §4.3): **0,75 % na
epizod w 24 h, zakres 0–1,3 %** — interpretacja, nie pomiar; najwyższa liczba źródłowa (+3,1 % w 24 h po spadku ≥ 5 %
w godzinę, BTC spot 2016–2021) jest tylko z indeksu pełnego tekstu w wyszukiwarce — **niepewna**.

## 4. Definicja kaskady (wykonywalna: `backtest/e1_kaskady.py::detect_cascades`)

1. **Uniwersum:** monety z `czlonek_top20 = True` w `dziennik/koszyk.csv` dla miesiąca UTC zdarzenia (ten sam skład co
   koszyk dziennika, point-in-time: obrót z 30 dni PRZED miesiącem). Symbol musi wystąpić na Bybit pod tą samą nazwą
   (bez mapowania nazw; brakujące zgłasza się w raporcie jako „kogo nie ma w zbiorze”). Likwidacje spoza uniwersum
   miesiąca są ignorowane w całości.
2. **Źródło sygnału:** Bybit `allLiquidation` (pełne), tylko kontrakty liniowe USDT; strona = strona ZLIKWIDOWANEJ pozycji
   (`pos`; Bybit `Buy` = long), nominał `v × p` (`data/liquidation_index.parse_line`). Cena `p` jest użyta wyłącznie
   do nominału jednej likwidacji — żadnej ścieżki ceny.
3. **Okno:** suma nominału strony `d` monety `s` w oknie przesuwnym `(t − 60 min, t]` po czasie likwidacji `T`.
4. **Próg:** suma ≥ **θ · V(s, m)**, θ = **0,5 %**, V = `sredni_obrot_30d` (średni DZIENNY obrót USDT na Binance).
   Sens: w ciągu godziny wymuszono w jedną stronę ok. 12 % obrotu przeciętnej godziny (0,5 % / (100 %/24)).
5. **Chwila zdarzenia `t*`:** pierwsza likwidacja, po której próg jest przekroczony. Jeśli wtedy DRUGA strona tej
   monety też jest ≥ progu → zdarzenie niejednoznaczne, pomijane, bez blokady.
6. **Blokada:** po zdarzeniu moneta nie daje nowego zdarzenia (żadna strona) przez 24 h od `t*` — transakcje na
   monecie się nie nakładają.

**Stopnie swobody (jawnie):** trzy wolne parametry — W = 60 min, θ = 0,5 %, H = 24 h — ustalone z góry, bez danych:
W z opisu kaskad (88 % wymuszonej sprzedaży w 30 min od startu; Garcia Seuma 2026, zadanie 026 E-d), H z największego
efektu 6–24 h (E-a), θ z rachunku wpływu na cenę (wymuszony przepływ rzędu 10 % obrotu godziny), bez oglądania rozkładu
likwidacji. Elementy strukturalne (nie strojone): blokada = H, kierunek z mechanizmu, uniwersum = koszyk projektu,
opóźnienie wejścia (wykonalność). **1 wariant.** Po policzeniu częstości (§13) żaden parametr się nie zmienia —
inna definicja = nowa karta i kolejny wariant w liczniku E1.

## 5. Transakcja, ceny, koszty (stosowane dopiero przy odczycie)

- Kierunek: zlikwidowane longi → **kupno**; zlikwidowane shorty → **sprzedaż**.
- Wejście: otwarcie świecy 1m Binance USDT-M (archiwum `data.binance.vision`) w chwili `floor_min(t*) + 2 min`;
  wyjście: otwarcie świecy 1m 24 h później. Brak świecy (moneta niehandlowana / delisting) → transakcja wypada
  i jest liczona w raporcie („kogo nie ma”).
- Koszt główny **C = 0,5 %** round-trip (opłaty taker 2 × 0,05 % + poślizg w kaskadzie; zakres 0,3–1 % z mapy 007);
  wrażliwość 0,3 % i 1,0 % raportowana obok (to nie warianty — werdykt na C = 0,5 %). Funding z rozliczeń w 24 h
  (archiwum Binance) wliczony w zwrot netto.
- Bez stop-lossa, bez celu zysku, bez dźwigni w pomiarze (zwrot w % nominału).

## 6. Statystyka i kryterium

- **Jednostka:** dzień UTC wejścia; zwrot dnia = średnia zwrotów netto transakcji z wejściem tego dnia (kaskady w wielu
  monetach naraz to jedno zdarzenie rynkowe, nie k niezależnych). Seria dni z ≥ 1 transakcją → `t`, N_eff z
  autokorelacji (kanonicznie jak w `backtest/checkpoint_lib.py`), **N_eff ≤ n**.
- **POZYTYWNE:** t_neff > 1,96 średniego zwrotu netto dnia ORAZ ci_low(p) > p\*, gdzie p = udział dni z dodatnim zwrotem
  BRUTTO, a p\* = (L̄ + C)/(W̄ + L̄) — próg uogólniony z obserwowanych średnich W̄ = E[r | r > 0], L̄ = E[−r | r < 0]
  zwrotu brutto dnia. Tożsamość: p(W̄ + L̄) − L̄ − C = E[r] − C, więc p > p\* ⇔ zwrot netto > 0 — w granicy dużego n
  oba warunki mówią to samo i nie karzą celu rundy. (Uproszczony próg 0,5(1 + C/B) przy normalnym rozkładzie
  wymagałby efektu ≈ 1,57 × C — dlatego NIE jest używany; sprawdzenie liczbowe w §13.)
- **NEGATYWNE:** t_neff < −1,96 przy n ≥ wymaganym z §13. **NIEROZSTRZYGNIĘTE:** pozostałe.
- Obok: mediana zwrotu dnia, rozkład po monetach, osobno longi/shorty (opis, nie warianty).

## 7. Licznik wariantów i próg t

- **Licznik E1: 0/1** (jeden wariant: ta karta). Wspólny dla Bybit, Binance i (gdyby powstał) HL.
- Nowe dane spoza historii 2021–2026 → własny licznik, próg **t 1,96** (mapa 007 §1). Dla porządku wydruk
  `PYTHONUTF8=1 py -m backtest.dsr --k 1` (próg dla odczytów HISTORII, E1 go nie dotyczy):
  ```
  Rejestr odczytów historii: 61 wierszy (rund); odczyty programu (wiersze liczone do N): 35
    N metodą AU4 (Σ wariantów):                               40
    N z 13 odczytami 0-wariantowymi (Σ max(wariantów, 1)):     53
  Planowana runda: k = 1 … progi dla N + 1 = 41 (metodą AU4) i 54 (z odczytami 0-wariantowymi).
       N | E[max t] | t dla DSR 0,80 | t dla DSR 0,95 | min. SR roczny na 5.5 roku (0,80 / 0,95)
      41 |     2.20 |           3.04 |           3.84 | 1.30 / 1.64
      54 |     2.31 |           3.15 |           3.95 | 1.34 / 1.68
  ```

## 8. Rola pozostałych źródeł

- **Binance LK0:** próbka (≤ 1 zdarzenie/s/symbol) — w kaskadzie zaniża nominał. Tylko drugi nośnik: dolna granica
  częstości i opis zgodności (ile kaskad Bybit widać też w LK0), nie osobny test.
- **Hyperliquid:** brak kolektora (LH0 zamknięte, wn. 115). Stan pozycji przed kaskadą — wyłącznie opis, nigdy druga
  zmienna ani filtr.

## 9. Rachunek mierzalności — metoda zapisana z góry (wynik w §13)

- Częstość: liczba kaskad i dni z ≥ 1 kaskadą na Bybit w dniach zamkniętych (bez cen), średnie k transakcji na dzień,
  przedział Poissona; Binance tą samą funkcją jako dolna granica; druga droga niezależnym kodem.
- `oczekiwane_n` = `expected_trades(n_dni, 1 − udział_dni_z_kaskadą)` dla horyzontu 1 / 2 / 3 / 5 lat zbierania.
- Rozrzut zwrotu 24 h jednej transakcji σ ∈ {5 %, 8 %} (mapa 007; cen nie wolno oglądać), korelacja monet w tym samym
  dniu ρ = 0,6 → σ_dnia = σ·√((1 + (k − 1)ρ)/k).
- Zwrot: mierzalna, gdy μ − C > 1,96 · σ_dnia / √n (próg 50 % mocy, ta sama konwencja co `measurability_report`);
  podać też n i lata dla mocy 80 %.
- Trafność: p = Φ(μ/σ_dnia), p\* uogólnione z W̄, L̄ rozkładu N(μ, σ_dnia) → `measurability_report(p, p*, n)`.
  MIERZALNA tylko, gdy oba warunki mierzalne.
- **Scenariusz rozstrzygający:** μ = 0,75 %, σ = 5 %, C = 0,5 %. Obok (opis): μ 1,3 %, σ 8 %, C 0,3 / 1,0 %.
- **Rozsądny horyzont: ≤ 3 lata zbierania** (zadanie 026 §4.3: odczyt najwcześniej po 3 latach).
- Granica dużego n: n = 10⁶ dla μ = C ± 0,05 % — kryterium ma przechodzić wtedy i tylko wtedy, gdy μ > C.
- Liczony mimo spokojnego tygodnia: częstość z 7–8 dni jest niepewna (skupianie kaskad w okresach paniki);
  rachunek powtarza się z samych liczników (bez cen) — §10.

## 10. Data odczytu i kontrole mocy

- **Żadnego odczytu (zestawienia z cenami) przed spełnieniem obu warunków:** (a) ≥ 1 rok danych Bybit, czyli
  najwcześniej **2027-09-27**; (b) rachunek z §9 powtórzony na licznikach z całego okresu daje MIERZALNA
  w scenariuszu rozstrzygającym przy aktualnym n.
- **Kontrole mocy (tylko liczniki, 0 odczytów):** 2026-12-27 (3 miesiące), potem co kwartał. Jeśli w kontroli
  wymagany czas przekracza 5 lat od startu LB0 → rekomendacja zamknięcia E1 bez odczytu (decyzja użytkownika).

## 11. Zakazy

- Żadnych cen, zwrotów ani „próbki” po likwidacjach przed §10. Żadnej zmiany W, θ, H, uniwersum, kierunku,
  wejścia, kosztu po zobaczeniu częstości lub cen. Kolektory LK0/LB0, kod i konfiguracja dziennika — bez zmian.

## 12. Reguła STOP

Jeden odczyt. Wynik NEGATYWNY albo NIEROZSTRZYGNIĘTY przy n ≥ wymaganym → rodzina E1 w tej definicji zamknięta;
inna definicja kaskady na tych samych danych = post hoc (zakaz bez nowej decyzji użytkownika). Wynik POZYTYWNY
→ szczebel 2/3 drabiny (dziennik papierowy), nie kapitał.

**Poprzedzające wnioski (zasada 14, jednym zdaniem):** wn. 102/106 (Bybit pełne, Binance próbka → sygnał z Bybit,
jeden licznik), 115 (HL bez kolektora → tylko opis), 107/96 (historia wyczerpana, ale E1 to nowe dane: t 1,96),
mapa 007 (MDE po roku 0,9–1,3 % przy σ 5 %) i zadanie 026 (efekt 0,75 %, koszt 0,3–1 %) — stąd jednostka „dzień”,
koszt 0,5 % i odczyt dopiero po kontroli mocy.

## 13. Wynik rachunku mierzalności (część B — dopisana po commicie części A)

Część A (§1–§12) zacommitowana w `580092c` (gałąź `zadanie-011-e1-karta-z-czestosci`, wypchnięta przed zliczeniem).
Wydruk: `runs/2026-10-05_e1k-karta-kaskad/raw_output.txt`; druga droga: `raw_output_druga_droga.txt` (zgodna).

- **Częstość (Bybit, 7,133 dnia, 2026-09-27 20:48 → 10-05 00:00 UTC, bez cen):** **0 kaskad** (95 % Poisson 0–3,7),
  czyli ≤ 189 dni z kaskadą rocznie (górna granica). Najbliżej progu: SUI long 0,53 progu. Binance (próbka, 9,4 dnia):
  9 kaskad w 5 dniach (193 dni / rok [63; 451]). Próg od obrotu Binance czyni definicję na Bybit ~3× rzadszą
  (ograniczenie projektu karty, bez zmiany — §11).
- **Scenariusz rozstrzygający (μ 0,75 %, σ 5 %, C 0,5 %):** potrzeba 1 537 dni z kaskadą (moc 50 %) / 3 140 (80 %).
  Po 3 latach: przy 189 / rok n 566, `wald_half_width` 4,12 pp, MDE netto 0,41 % wobec 0,25 % → **NIEMIERZALNA**;
  przy 365 / rok (sufit) n 1 095, MDE netto 0,30 % → **NIEMIERZALNA**. Mierzalna dopiero po 4,2 roku (50 %) /
  8,6 roku (80 %), i to przy kaskadzie każdego dnia. Przy 189 / rok: 8,1 / 16,6 roku.
- **Granica dużego n:** próg uogólniony przepuszcza ⇔ μ > C; uproszczony wymagałby μ > 1,577 × C (karze cel).
- **Werdykt: NIEMIERZALNA w horyzoncie ≤ 3 lat → odczyt nie startuje.** Licznik E1 0/1 (wariant niezużyty).
  Kontrola mocy z liczników 2026-12-27 (§10).

