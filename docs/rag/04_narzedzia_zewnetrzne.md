---
status: active
last_verified: 2026-08-01
depends_on: [01_hipoteza_i_architektura.md, 02_cechy_i_leakage.md]
---

# 04 — Narzędzia zewnętrzne: decyzje i uzasadnienia

Zasada wspólna dla wszystkich poniższych: **katalog wzorców do przeczytania i selektywnego
przepisania, nigdy zależność runtime w `requirements.txt` silnika produkcyjnego Fazy 0.**

## freqtrade

Otwarty framework do tradingu krypto z wbudowanym FreqAI (feature engineering + ML). Powody, dla
których NIE jest zależnością:

- Wnosi cały swój bagaż (event loop, DataProvider, Telegram, sqlite, webserver) do systemu, który
  ma być odizolowany i audytowalny.
- Liczy wskaźniki przez TA-Lib — stąd nasza decyzja o TA-Lib jako jedynej bibliotece dla
  wszystkich cech (spójność z tym, co i tak jest tam popularne).
- Użyteczny jako: (a) katalog do przeglądania `populate_indicators()` konkretnych strategii i
  przepisywania logiki jako czystych funkcji z testem leakage, (b) opcjonalny silnik do paper
  tradingu w Fazie 3 (dry-run/testnet ma to wbudowane) — ale LEAN jest tu mocniejszym kandydatem
  (patrz niżej), konkretnie dla perpetual futures.

## QuantConnect / LEAN

**Rozróżnienie ważne:** QuantConnect to firma/platforma chmurowa; LEAN to jej silnik, open-source,
w pełni self-hostowalny (`pip install lean`, Docker) — to LEAN, nie QuantConnect-jako-cloud, jest
tu relewantny dla wymogu "100% lokalne" z oryginalnego PRD.

**Zweryfikowane researchem (nie założenie):**
- `AddCryptoFuture("BTCUSDT")` — natywne wsparcie perpetual futures na Binance, nie generyczny
  spot crypto.
- `BinanceFutureMarginInterestRateModel` — wbudowana symulacja funding rate (long płaci short przy
  dodatnim funding i odwrotnie), rozliczana 3x dziennie (12AM/8AM/4PM), zgodnie z rzeczywistym
  mechanizmem Binance.
- Dedykowane źródło danych: `Lean.DataSource.BinanceFundingRate` (GitHub, QuantConnect).
- Architektura event-driven (`OnData`) zaprojektowana specyficznie przeciwko look-ahead bias —
  bezpośrednio służy naszemu Compliance Gate.
- Oryginalny PRD miał `config/lean.json` w drzewie plików — prawdopodobnie pierwotny zamysł, nie
  przypadkowa nazwa.

**Mimo mocniejszego dopasowania niż freqtrade, NIE w Commit 5 (Faza 0):** już napisane i
przetestowane `fetch_ohlcv.py`/`feature_miner.py` nie są zbudowane pod strukturę `QCAlgorithm`
(Initialize/OnData/Portfolio/Slice). Przejście na LEAN teraz oznacza naukę nowego frameworka
zamiast odpowiedzi na pytanie, czy Test 1/Test 2 mają edge — ta sama pułapka sekwencji, której
unikamy od początku projektu.

**Gdzie LEAN faktycznie wchodzi:**
- **Faza 1:** `Lean.DataSource.BinanceFundingRate` jako źródło prawdziwych danych funding rate
  zamiast pisania własnego fetchera do Binance API.
- **Faza 3 (paper trading):** LEAN, nie freqtrade — mocniejszy kandydat konkretnie dla perpetual
  futures z realistycznym modelowaniem funding/marginu/lot size.

## Multi-agentowe frameworki LLM (TradingAgents, FinCon, HedgeAgents, FinAgent)

Aktywna, legalna dziedzina badań — nie fantazja. Kluczowy konflikt z naszą architekturą: większość
z nich ma **LLM W pętli decyzyjnej** (analiza sentymentu/newsów → decyzja tradingowa przez
rozumowanie językowe) — dokładnie to, czego się wyrzekliśmy (LLM offline/nadzorczo, patrz
`01_hipoteza_i_architektura.md`). Wzięcie takiej architektury wholesale byłoby cofnięciem się z
tej decyzji.

Dodatkowo: te systemy są budowane pod akcje (sentyment, fundamenty, earnings) — BTC/ETH perpetual
futures na 5m mają inną strukturę relewantnych danych (funding rate, open interest, likwidacje),
więc "wstaw i działa" i tak by nie zadziałało.

**Wzorce faktycznie warte wzięcia (przeczytania i przepisania, nie importu):**
- **FinCon** — mechanizm "verbal reinforcement" (agenty krytykujące się nawzajem w języku
  naturalnym po transakcji) — pasuje do `post_trade_critic.py` z Fazy 3 (LLM offline, analiza po
  fakcie), nie do decyzji real-time.
- **HedgeAgents** — "balance-aware" alokacja ryzyka między pozycjami — potencjalnie użyteczne do
  rozbudowy `risk_controller.py` w Fazie 1+, jeśli projekt kiedyś obejmie wiele instrumentów.
