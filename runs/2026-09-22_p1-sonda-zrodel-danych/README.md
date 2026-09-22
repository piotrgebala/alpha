# P1 — ile historii Binance faktycznie oddaje dla danych pozycjonowania (2026-09-22)

> **STATUS: ZAMKNIĘTA. Wynik: cała klasa źródeł odpada MECHANICZNIE.**
> Sonda odczytowa, zero zmian w repo, zero spojrzeń na target.

## ID testu

**P1** — diagnostyka wykonalności źródeł danych. **0 wariantów, POZA wszystkimi licznikami
hipotez** (ta sama rola co Z19: rachunek wykonalności PRZED wydaniem wariantu).

## Pytanie

Po M1 wniosek skumulowany 11 wskazuje kierunek: `p` może ruszyć **nowy zbiór informacyjny**,
a nie kolejna transformacja OHLCV. Naturalni kandydaci to dane o **pozycjonowaniu** — open
interest, long/short ratio, pozycje największych traderów. Mechanizm jest sensowny i nie
wywodzi się z ceny.

**Ale zasada 18 pyta najpierw o co innego: czy da się to w ogóle zmierzyć.** Na 4h/V=3 przy
abstynencji ~40% potrzeba **4 481 transakcji** (moc 80%, `required_trades` wobec progu 52,94%),
czyli około **3,4 roku** historii.

## Metoda

Odczyt pięciu endpointów `futures/data/*` z `fapi.binance.com` dla BTCUSDT, okres 4h,
limit 500. Dwa pytania per endpoint: jak daleko sięga domyślna odpowiedź oraz co zwraca przy
jawnym `startTime` sprzed lat. Dla kontroli te same pytania zadano endpointom, z których
projekt **już korzysta**.

## Wynik

| endpoint | punktów | zakres | historia | `startTime=2020` |
|---|---|---|---|---|
| `openInterestHist` | 186 | 2026-08-22 → 2026-09-22 | **30,8 dnia** | **HTTP 400** |
| `topLongShortAccountRatio` | 186 | — | **30,8 dnia** | **HTTP 400** |
| `topLongShortPositionRatio` | 186 | — | **30,8 dnia** | **HTTP 400** |
| `globalLongShortAccountRatio` | 186 | — | **30,8 dnia** | **HTTP 400** |
| `takerlongshortRatio` | 186 | — | **30,8 dnia** | **HTTP 400** |

**Kontrola — dane, których projekt już używa:**

| endpoint | `startTime=2020` |
|---|---|
| `klines` (OHLCV) 4h | **500 punktów od 2020-01-01** ✅ |
| `fundingRate` | **500 punktów od 2020-01-01** ✅ |

Kontrola jest istotna: dowodzi, że ograniczenie leży **w tych konkretnych endpointach**,
a nie w sondzie, kluczu ani sposobie odpytywania.

## Rachunek

| | |
|---|---|
| 30,8 dnia na 4h | **186 świec** |
| przy abstynencji 40% | **~112 transakcji** |
| wymagane (zasada 18) | **4 481** |
| **brakuje** | **40×** |
| potrzebna historia | ~7 468 świec = **3,4 roku** |
| dostępna historia | **0,084 roku** |

## Wniosek

Prostym językiem (zasada 17).

**Dane o pozycjonowaniu — kto ile ma otwartych pozycji, ilu graczy stoi po której stronie —
to najbardziej oczywisty kandydat na „informację spoza wykresu ceny". Binance udostępnia je
publicznie. Ale tylko za ostatnie 30 dni.**

Przy naszej konfiguracji trzydzieści dni daje około **stu dwunastu transakcji**. Żeby cokolwiek
orzec, potrzeba **czterech i pół tysiąca**. Brakuje czterdziestokrotnie. Nie jest to kwestia
lepszego modelu ani cierpliwości — **nie ma czego mierzyć**.

Próba sięgnięcia głębiej jawnym parametrem czasu kończy się błędem 400: to nie jest limit
jednego zapytania, tylko **granica tego, co giełda w ogóle przechowuje pod tym adresem**.

**Jedyną drogą do tych danych byłoby zbieranie ich od dziś na bieżąco** — po trzech i pół roku
byłoby czym mierzyć.

## Rekomendacja

1. **Open interest, long/short ratio i pochodne WYKREŚLIĆ z listy kandydatów** — nie dlatego,
   że mechanizm jest zły, tylko dlatego, że są niemierzalne przy tej metodologii. Zapisane,
   żeby nikt nie proponował ich po raz drugi.
2. **Jeśli ktoś uzna je za obiecujące — jedyna droga to zbieranie od dziś.** Koszt: jeden
   proces zapisujący 186 punktów dziennie, wynik użyteczny za ~3,4 roku. To decyzja o
   inwestycji czasu, nie runda badawcza.
3. **Zostaje funding** — jedyne źródło spoza OHLCV, które projekt ma z wystarczającą historią
   (7 457 rekordów, 6,8 roku, zero dziur) i którego **nigdy nie zmierzył** (H2.1 skończyło się
   `n = 98`). To bezpośrednia motywacja hipotezy **F**.
