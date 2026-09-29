---
id: 010
tytul: Hyperliquid — brama danych dla fundingu i premii HL vs Binance (historia, point-in-time), bez odczytu
typ: zbieranie_danych
status: czeka_na_decyzje
zlecil: uzytkownik
decyzja_uzytkownika: "brak"
utworzono: 2026-09-29
zalezy_od: [004]
nie_wczesniej_niz: 2026-09-30
budzet: "Sonnet do sondy, Opus do przeglądu"
---

# 010 — HL: brama danych (funding, premia, stan rynku)

## Po co

Hyperliquid to inna populacja traderów niż Binance (portfele on-chain, duzi gracze widoczni publicznie). Różnica
ceny lub fundingu HL vs Binance może być sygnałem popytu w stylu premii Coinbase (rodzina C2), a więc potencjalnie
nogą o niskiej korelacji. Wniosek 110 wskazał tani krok: `metaAndAssetCtxs` co 60 s (~19 MB/dobę gzip). Zadanie 004
tego nie robi („osobna decyzja”).

## Zakres

- Sonda: ile historii dają publiczne `fundingHistory` i `candleSnapshot` (od kiedy, jaka rozdzielczość, czy dla monet
  zdelistowanych). Kontrola pozytywna: zgodność z tym, co widać na żywo.
- Jeśli użytkownik zgodzi się: kolektor stanu rynku co 60 s do `$HOME/likwidacje_hl/stan/` (wzór LB0).
- Raport: BRAK DANYCH albo liczba lat historii i pokrycie koszyka top-20.

## Czego NIE robić

- Żadnego zestawienia z cenami Binance ani z wynikami strategii (to byłby odczyt).
- Tylko publiczne API bez klucza; bez MCP Liquid; bez płatnych źródeł.

## Kryteria odbioru (dowody)

README w `runs/`, `raw_output.txt` sondy, testy bez sieci, `security-review` (nowe połączenie).

## Pytanie do użytkownika

Zgoda na sondę historii i na kolektor stanu rynku co 60 s?

## Wynik

**2026-09-29:** decyzja dopiero po wyniku pomiaru wag z zadania 004 (koniec ≈ 2026-09-30 10:33 UTC); wtedy orkiestrator przedstawi rekomendację (kolejność z mapy 007: E1 → sonda HL). Status bez zmian.
