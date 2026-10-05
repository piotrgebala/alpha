"""
liquidation_time.py — JEDNA reguła czasu zdarzenia likwidacji (ms od epoki, UTC) dla kolektorów
(`data/collect_liquidations.py`: pola `E` i `T`; `data/collect_liquidations_bybit.py`: `T` i `ts`),
dziennego indeksu (`data/liquidation_index.py`, pole `T`) i kopii (`data/liquidation_backup.py`,
przez indeks).

Po co (zadanie 021, backlog STATUS §17 ETAP 6): kolektor Binance nie sprawdzał czasu transakcji `T`,
więc rekord z `T` spoza zakresu wychwytywał dopiero indeks albo kopia — dzień później. Reguła indeksu
(dotąd w `liquidation_index.parse_line`) i granice (dotąd zdublowane w kolektorze i w indeksie)
mieszkają teraz tutaj; kolektor sprawdza `T` przy zapisie tą samą funkcją. Nowego progu nie ma.

Reguła `event_time_ms(wartość)` — wartość pola z JSON jest poprawnym czasem, gdy:
- nie jest `bool` (w Pythonie `True` to 1, ale JSON-owe `true` to nie liczba);
- daje się zamienić przez `int(...)`: liczba całkowita, liczba z ułamkiem (ucięta) albo tekst
  z cyframi; `null`, tekst nieliczbowy, nieskończoność i NaN nie przechodzą;
- mieści się w `[MIN_EVENT_MS, MAX_EVENT_MS]` = 2019-01-01 … 2100-01-01 UTC (granice LK0 z
  `collect_liquidations.day_path`). Poza nimi `datetime.fromtimestamp` rzuca błędy zależne od
  platformy (np. 10**17 → „year 3170843 is out of range”).
Reguła NIE porównuje `T` z `E` ani z dniem pliku: `T` z poprzedniej doby w pliku dnia `E` (zdarzenie
tuż po północy UTC) jest poprawne — indeks przyjmuje je tak samo.

Moduł bez importów (czysta funkcja i stałe), więc indeks i kopia nie ciągną kodu sieciowego
kolektorów. Testy: `tests/test_liquidation_time.py` (w tym właściwość „ta sama reguła co indeks”
w `hypothesis`).
"""

from __future__ import annotations

MIN_EVENT_MS = 1_546_300_800_000  # 2019-01-01 00:00:00 UTC
MAX_EVENT_MS = 4_102_444_800_000  # 2100-01-01 00:00:00 UTC
RANGE_TEXT = "2019-01-01…2100-01-01 UTC"
SHORT_CHARS = 40  # tyle znaków wartości trafia do komunikatu (status, log)


def short_repr(value) -> str:
    """Wartość do komunikatu: `repr` ucięty do `SHORT_CHARS` znaków (int > 4300 cyfr → nazwa typu)."""
    try:
        text = repr(value)
    except ValueError:  # limit konwersji int → tekst (Python ≥ 3.11)
        text = f"<{type(value).__name__}>"
    return text if len(text) <= SHORT_CHARS else text[: SHORT_CHARS - 1] + "…"


def event_time_ms(value) -> int:
    """Czas zdarzenia w ms → `int`; `ValueError`, gdy wartość łamie regułę z docstringu modułu
    (bool, brak liczby, poza `[MIN_EVENT_MS, MAX_EVENT_MS]`)."""
    if isinstance(value, bool):
        raise ValueError(f"{short_repr(value)} nie jest liczbą ms")
    try:
        ms = int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{short_repr(value)} nie jest liczbą ms") from None
    if not MIN_EVENT_MS <= ms <= MAX_EVENT_MS:
        raise ValueError(f"{short_repr(ms)} poza zakresem {RANGE_TEXT}")
    return ms
