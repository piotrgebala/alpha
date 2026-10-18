---
id: 010
tytul: Hyperliquid — brama danych dla fundingu i premii HL vs Binance (historia, point-in-time), bez odczytu
typ: zbieranie_danych
status: zrobione
zlecil: uzytkownik
decyzja_uzytkownika: "2026-09-29: zgoda na wszystkie 008–014 („Wszystkie 008–014”); odczyty na historii startują tylko, jeśli mapa 007 uzna rodzinę za MIERZALNĄ"
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
- **2026-10-05:** 004 zamknięte STOP (wniosek 115) — HL bez kolektora likwidacji; ta brama (`metaAndAssetCtxs` co 60 s) nie zależy od kosztu wag z 004 i może startować (zgoda z 29.09).
- **2026-10-06 (orkiestrator): zrobione.** Gałąź `zadanie-010-hl-stan-rynku` (`a6f0fbc`…`7826c05`) scalona w `47551cd`.
  Runda HS0: [`runs/2026-10-05_hs0-hl-stan-rynku/`](../runs/2026-10-05_hs0-hl-stan-rynku/README.md), wniosek 117,
  0 wariantów, bez odczytu.
  - **Sonda:** publiczne API daje godzinowy funding od 2023-05-12 (BTC/ETH/SOL 3,40 roku; pozostałe 17 monet koszyka
    1,0–3,4 roku, mediana 3,15). Na HL jest 20 z 26 symboli koszyka. Monety wycofane zachowują historię. Krótkich
    świec jest tylko ~5 000 ostatnich. Kontrola pozytywna z odczytem na żywo: 20/20.
  - **Kolektor:** `data/collect_hl_stan.py` (`metaAndAssetCtxs` co 60 s → `~/likwidacje_hl/stan/`) + blok 1c
    w `tools/likwidacje.sh`. Uruchomiony 2026-10-06 07:11 UTC z `~/alpha`. Cron z `~/alpha-dziennik` przejmie nadzór
    po pobraniu master przed przebiegiem 02:30. `--status` 07:14 UTC: 3 migawki w 3 cyklach, 0 błędów sieci,
    0 ponowień, 234 monety, 13 090 B gzip na migawkę (≈ 19 MB/dobę).
  - **Dowody:** `raw_output.txt`, `raw_output_druga_droga.txt`, `raw_output_kolektor.txt` (sha256 kolektora
    `d4db539d…a745db6676b`, ten sam w `f9e34ff` i `7826c05`). Druga droga orkiestratora: najstarszy funding BTC
    2023-05-12 00:00 UTC i ZEC 2025-10-02 14:00 UTC (curl), mediany 3,15 (17 monet) i 3,25 (20 monet) przeliczone z dat.
    16c: „Approve z uwagami”, uwagi 1–6 poprawione. Pełny pytest na scalonym master (`OMP_NUM_THREADS=4`, pipefail):
    2239 passed, 2 skipped, kod 0.
  - **Zostało:** (1) kopia danych HL poza serwerem — **decyzja użytkownika** (~7 GB/rok; do tego czasu dane są tylko
    na serwerze); (2) przed jakąkolwiek kartą „funding/premia HL” — rachunek mierzalności (zasada 18) i nowa seria
    z własnym licznikiem; (3) po tygodniu: `--status`, rozmiar plików, 1 440 migawek na dobę.
