# P4 — brama danych on-chain: pokrycie koszyków top-20 / top-50 (2026-09-25)

> **STATUS: ZAMKNIĘTA — ranking monet na darmowych danych on-chain NIEWYKONALNY.** Przepływy na giełdy
> i podaż na giełdach: tylko BTC i ETH (4–10 % koszyka). Aktywne adresy / MVRV / transakcje: średnio
> 37–46 % koszyka i spada (2025–26: 30–43 %). Próg sensowności rankingu (~70 %) nieosiągnięty. Brama danych,
> bez hipotezy, 0 wariantów. Przegląd: **Approve**.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Sprawdziliśmy, dla ilu monet z naszego koszyka są za darmo dane on-chain (z samych sieci blockchain).
Wynik: przepływy na giełdy (najciekawsza miara — „czy ludzie wpłacają monety, żeby sprzedać”) są tylko dla
BTC i ETH. Prostsze miary (aktywne adresy, transakcje) mają mniej niż połowa monet — brakuje m.in. SOL,
AVAX, PEPE, SUI, MATIC. Ranking z dziurami w połowie koszyka byłby skrzywiony, więc na darmowych danych
nie ma czego testować. Czy płatny dostawca (Glassnode itp.) pokrywa brakujące sieci — trzeba sprawdzić
w jego ofercie przed zakupem; to decyzja użytkownika.

## Metadane

- Branch `p4-pokrycie-onchain`. Skrypt `backtest/run_p4_pokrycie_onchain.py`, testy `tests/test_p4_pokrycie.py` (2).
  Komenda: `PYTHONUTF8=1 py -m backtest.run_p4_pokrycie_onchain` → `raw_output.txt`.
- Źródło: katalog CoinMetrics community `/v4/catalog-v2/asset-metrics` (ten sam host co `fetch_external`),
  metryki 1d dostępne za darmo. Koszyki top-20/top-50 jak w AU2 (skład miesięczny z danych sprzed miesiąca).

## Poprzedzające wyniki

L1 (on-chain podaż BTC jako cecha modelu 4h), SW (wniosek 90: ta sama jako reguła — po kosztach strata),
SH1 (81: AA1 aktywne adresy — NIEMIERZALNY), AU2 (92: przyrząd przekrojowy widzi IC ≥ 0,022).

## Pre-rejestracja (brama danych, bez hipotezy)

Kryterium podane użytkownikowi w rozmowie PRZED uruchomieniem: ranking on-chain ma sens przy pokryciu
≥ ~70 % koszyka; przy niskim — temat zamknięty bez zakupu danych. Odstępstwo: README nie był zacommitowany
przed przebiegiem (brama nie czyta zysków ani sygnałów, więc nie ma czego dopasować po fakcie).

## Wynik

| metryka | aktywów w katalogu | pokrycie top-20 (średnio / min / 2021 / 2025–26) | pokrycie top-50 |
|---|---|---|---|
| FlowInExUSD, FlowOutExUSD, SplyExNtv | 2 (BTC, ETH) | 10 / 10 / 10 / 10 % | 4 % |
| AdrActCnt | 138 | 46 / 25 / 68 / 43 % | 37 % (2025–26: 30 %) |
| CapMVRVCur | 125 | 45 / 25 / 62 / 43 % | 34 % |
| TxCnt | 142 | 46 / 25 / 68 / 44 % | 37 % |

Najczęstsi członkowie top-20 bez aktywnych adresów: SOL (62 mies.), AVAX, PEPE, MATIC, SUI, SHIB, FTM, FIL, WLD,
WIF, NEAR, OP. Mapowanie nazw sprawdzone (ADA, BNB, DOGE, XRP, LINK, LTC, DOT, TRX są rozpoznane) — braki są prawdziwe.

## Co na plus (+) / Co na minus (−)

**(+)** Odpowiedź bez hipotezy i bez oglądania zysków; test mapowania symboli. **(−)** Sprawdzony tylko darmowy
CoinMetrics; pokrycie płatnych dostawców nieznane (nie weryfikowane). Pokrycie liczone „od początku miesiąca” —
dziury wewnątrz szeregów (np. przerwy w danych) niezbadane, więc realne pokrycie może być tylko niższe.
**Kogo nie ma:** monety spoza CoinMetrics w ogóle (większość nowych L1 i memecoinów).

## Przegląd (16c)

`engineering:code-review` (samodzielnie): czyste funkcje `cm_asset`, `parse_catalog`, `coverage` z testami; stronicowanie
katalogu przez `next_page_url`; brak zapisu danych. **Werdykt jednym zdaniem: Approve** — skrypt tylko czyta katalog
i liczy udziały, bez wpływu na dane i wyniki.

## Wniosek

**Prostym językiem:** darmowe dane on-chain nie pokrywają naszego koszyka monet — nie da się na nich zbudować uczciwego
rankingu. **Technicznie:** przepływy na giełdy 2/~50 monet, adresy/MVRV 34–46 % koszyka.

## Rekomendacja

1. Ranking on-chain na darmowych danych — zamknięte.
2. Glassnode / inny płatny: przed zakupem sprawdzić w ich katalogu pokrycie SOL, XRP, BNB, DOGE, ADA, AVAX, SUI
   (najczęstsi członkowie koszyka); sensowne dopiero przy ≥ ~70 % koszyka przez 2021–2026. Decyzja użytkownika.
3. On-chain na samym BTC — bez sensu na tej historii (przyrząd widzi dopiero SR ≈ 0,86; wniosek 91/96).

## Użyte skille

Rejestr `runs/skille/p4-pokrycie-onchain.jsonl`: `clas5-quant` (brama danych przed hipotezą), `data:explore-data`
(katalog: które metryki, od kiedy), `clas5-runda` (dokumentacja; wczytany po przebiegu — brama bez hipotezy),
`engineering:code-review` (Approve). Pominięte: `data:validate-data` (brak liczby wynikowej do przeliczenia poza
udziałami; mapowanie sprawdzone ręcznie), `security-review` (host już używany w repo).
