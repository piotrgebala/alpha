# LK0 — kolektor likwidacji Binance USDT-M: brama danych rodziny E1 (2026-09-25)

> **STATUS: URUCHOMIONY 2026-09-25** (decyzja użytkownika: „kolektor tak”; STATUS ETAP 5, propozycja 4). **0 wariantów — POZA
> licznikami:** to zbieranie danych, nie pomiar; żadnej hipotezy nie odczytano i nie wolno jej odczytać, dopóki rachunek mocy
> na REALNEJ częstości zdarzeń nie powie „mierzalna”.

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

Likwidacja to przymusowe zamknięcie przez giełdę pozycji z dźwignią, gdy strata zjada depozyt. Kaskady likwidacji są jednym
z nielicznych mechanizmów z prawdziwym „ktoś MUSI handlować” (rodzina E1 w katalogu strategii), ale nie ma darmowej historii:
archiwum Binance jej nie zawiera (P3), REST `allForceOrders` zniknął w 2021, a płatni dostawcy nie dokumentują głębokości.
Jedyna droga to zbierać samemu od dziś. Od 2026-09-25 serwer zapisuje każde zdarzenie ze strumienia Binance do pliku dziennego.
Za ~1–2 lata będzie z czego sprawdzić hipotezę E1 — do tego czasu tylko zbieranie i kontrola, czy proces żyje.

## Metadane

- Branch `kolektor-likwidacji` (z `master` `8c442e7`). Kod `data/collect_liquidations.py`; nadzór `tools/likwidacje.sh` (cron co
  5 min, `flock` = jedna instancja na maszynie); testy `tests/test_collect_liquidations.py` (13, bez sieci: parser, pliki dzienne,
  odczekanie, pętla z podmienionym połączeniem — zapis, pomijanie złych wiadomości, ponowne łączenie, odczyt).
- Źródło: `wss://fstream.binance.com/market/ws/!forceOrder@arr` (publiczne, bez klucza, tylko `wss://`, adres stały w kodzie).
- Dane POZA repo: `$HOME/likwidacje/YYYY-MM-DD.jsonl` (dzień UTC czasu zdarzenia `E`), `status.json` (liczniki, ostatnie zdarzenie,
  odświeżane co ≥ 30 s), `kolektor.log` (połączenia, rozłączenia, pominięte wiadomości), `kolektor.out` (stdout/stderr).
- Wiersz = jedno zdarzenie, pola surowe z JSON (liczby jako teksty): `E` (ms), `st` (1 = UM, 2 = CM), `ps` (para), `s` symbol,
  `S` strona, `o` typ, `f` czas ważności, `q` ilość, `p` cena, `ap` średnia cena wykonania, `X` status, `l` ostatnie wypełnienie,
  `z` wypełnienie łączne, `T` czas zlecenia. Odczyt do analizy: `collect_liquidations.load_day` (czasy UTC, liczby float).

## Poprzedzające wyniki

P1 (pozycjonowanie z REST: 30 dni → niemierzalne), P3 (archiwum `data.binance.vision`: likwidacje puste), O1 (pozycjonowanie jako
cecha 4h — nic), TL1/RU4 (tłok OI — nierozstrzygnięty), katalog `quant-strategy-catalog` E1 = WYKLUCZONE-danymi, STATUS ETAP 5
pkt 4 („jedyna rodzina z mocnym mechanizmem wykluczona wyłącznie danymi; zdarzeniowa → setki zdarzeń/rok → mierzalna szybciej”).

## Co ustalono przy uruchomieniu (2026-09-25) — pełny zapis w `raw_output.txt`

1. **Dokumentowany adres nie działa.** `wss://fstream.binance.com/ws/!forceOrder@arr` odpowiada poprawnym handshake'iem (101),
   ale nie wysyła ŻADNEJ ramki — także dla kontrolnego `btcusdt@aggTrade`, który normalnie nadaje kilka wiadomości na sekundę.
   Spot Binance i obcy serwer echo działały natychmiast, więc to nie sieć serwera. ccxt 4.5.48 łączy się inaczej: Binance
   rozdzielił strumienie futures na kategorie — `/public/ws/<n>` (trade/depth/bookTicker) i `/market/ws/<n>` (reszta, w tym
   `forceOrder`) — i tak dostaje dane. Test: `/market/ws/!forceOrder@arr` nadaje (26 zdarzeń/60 s), subskrypcja na
   `/market/ws/0` też (25). Wybrano ścieżkę bez subskrypcji (prostsza, bez potwierdzeń). Cisza > 15 min = ponowne połączenie
   z wpisem w logu — gdyby adres znów się zmienił, widać to w `--status` (brak nowych zdarzeń).
2. **Pola `ps`/`st` przychodzą WEWNĄTRZ zlecenia `o`** (dokumentacja pokazuje je na wierzchu) — parser bierze oba miejsca.
3. **Próba 90 s (13:28–13:30 UTC):** 56 zdarzeń, 29 symboli (XAUUSDT, BTCUSDT po 5; 龙虾USDT, SPCXUSDT, CLUSDT po 4), `st` 1: 55 /
   2: 1 (strumień łączy UM i COIN-M), 43 SELL / 13 BUY, wszystkie `FILLED`, nominał ≈ 3,7 mln USD. Rząd wielkości ~40 zdarzeń/min.
4. **Przegląd bezpieczeństwa (`security-review`, wbudowany):** 0 podatności; dwie uwagi niskie wdrożone — JSONL w ASCII (linia =
   rekord także przy znakach U+2028), jawny zakres czasu zdarzenia 2019–2100 (poza nim `ValueError` → wiadomość pominięta,
   nie zerwanie połączenia; wcześniej Linux rzucał `OSError`). **Przegląd kodu (`engineering:code-review`): Approve** — czyste
   funkcje testowane bez sieci, sieć w jednej cienkiej warstwie, każdy błąd transportu = ponowne łączenie z wykładniczym
   odczekaniem (1 → 60 s), zapis append-only z `flush`, status atomowy.

## Co na plus (+) / Co na minus (−)

**(+)** darmowe, bez klucza; zdarzenia zapisywane surowo (bez przeliczeń, odtwarzalnie); proces wznawiany przez cron; adres
sprawdzony doświadczalnie, a nie przepisany z dokumentacji (która w tym punkcie jest nieaktualna).

**(−)**
- **Próbka, nie pełna lista:** giełda pokazuje ≤ 1 zlecenie/s/symbol — w kaskadach wolumen jest zaniżony; liczby zdarzeń to dolne
  ograniczenie. Do sumowania wolumenu likwidacji potrzebny byłby dostawca agregujący (płatny; decyzja użytkownika: na razie nie).
- **Zero historii:** rodzina E1 pozostaje WYKLUCZONA-danymi, aż zbierze się ≥ 1 rok; rachunek mocy z realnej częstości PRZED
  jakimkolwiek odczytem (`expected_trades` z częstości zdarzeń, nie ze świec — zasada 18).
- **Jeden proces:** awaria = dziura do 5 min + restart; restart serwera = dziura do pierwszego uruchomienia crona. Dziury widać
  w `status.json` (`reconnects`, `last_error`) i w logu.
- **Adres nieudokumentowany** — może się zmienić; sygnał alarmowy: `--status` bez nowych zdarzeń od kilkunastu minut.
- **Kogo nie ma:** likwidacji spoza Binance USDT-M (COIN-M tylko wtedy, gdy strumień je dołącza; inne giełdy — nie), zdarzeń
  sprzed 2026-09-25, zdarzeń z minut, gdy proces nie żył.

## Nadzór i uruchomienie

- Stan: `PYTHONUTF8=1 .venv/bin/python -m data.collect_liquidations --dir ~/likwidacje --status` — „ostatnie” powinno być sprzed
  minut, `rozłączeń` rosnąć powoli (Binance zamyka połączenie co 24 h — to normalne).
- Cron (dodaje użytkownik; klon dziennika = zawsze `master`, skrypt pojawi się tam po nocnym pobraniu 2026-09-26):
  `*/5 * * * * bash $HOME/alpha-dziennik/tools/likwidacje.sh`
- Ręczny start z dowolnego klonu: `nohup bash tools/likwidacje.sh >/dev/null 2>&1 &` (blokada wspólna, druga instancja nie wystartuje).

## Wniosek

Dane o likwidacjach da się zbierać za darmo, ale tylko na żywo i tylko jako próbkę; brama danych rodziny E1 otworzy się
najwcześniej za rok. Odkrycie uboczne warte zapamiętania: dokumentacja Binance nie nadąża za zmianą adresów strumieni futures —
każde nowe źródło sprawdzać doświadczalnie z kontrolą pozytywną (strumień, który na pewno nadaje), nie po opisie.

## Rekomendacja

1. Zbierać; nic nie odczytywać. Po 4–6 tygodniach profil danych (`data:explore-data`): zdarzeń/dzień, symboli, dziury, udział CM,
   rozkład nominałów — do rachunku mocy.
2. Kartę hipotezy E1 (`quant-strategy-catalog`) pisać dopiero z tym rachunkiem; horyzont zdarzeniowy (co po kaskadzie), nie 4h.
3. Jeśli kiedyś płatny agregator: najpierw pokrycie i głębokość historii (jak P4), nie cennik.

## Użyte skille (CLAUDE.md zasada 19)

Wynik `py tools/skill_audit.py raport --galaz kolektor-likwidacji`:

| czas (UTC) | skill | co wniósł |
|---|---|---|
| 13:13:08 | `anthropic-skills:clas5-quant` | nowe źródło danych = brama danych z własną historią (§E); rachunek mocy z częstości zdarzeń, nie ze świec; zero odczytów przed mocą |
| 13:16:40 | `engineering:code-review` | bramka 16c: przegląd parsera, pętli łączenia, zapisu, skryptu nadzoru i testów — Approve; uwagi wdrożone |

`security-review` (wbudowany, nowe połączenie sieciowe): wczytany i wykonany przez agenta przeglądu (wynik w pkt 4) — rejestr
`runs/skille/` nie zapisuje skilli wbudowanych. Skille z tabeli zasady 19, których moment runda obejmowała, a których nie ma
w rejestrze: `data:explore-data` — profil zbioru dopiero, gdy będą dane (rekomendacja 1); `quant-strategy-catalog` — bez nowej
hipotezy (karta E1 po rachunku mocy); `dataviz` — bez wykresu. Skill `clas5-runda` wczytany wcześniej w tej sesji na gałęzi
PR1 (procedura ta sama; rejestr przypisuje wczytania do gałęzi).
