"""
costs.py

Modelowanie kosztów transakcyjnych Binance USDS-M Futures (perpetuals) — docs/rag/04
_narzedzia_zewnetrzne.md i STATUS.md §5 Commit 5. Wartości startowe, do
kalibracji, gdy dostępne będą realne dane funding rate (Faza 1, LEAN
`Lean.DataSource.BinanceFundingRate`) — źródło prawdy: config/settings.yaml sekcja
`costs`.

Trzy składniki pełnego obrotu (round-trip):
    fee       - taker fee, wejście I wyjście (zakładamy market order w obie strony)
    funding   - funding rate za czas trzymania pozycji (long płaci dodatni funding,
                short otrzymuje, i odwrotnie przy funding ujemnym)
    slippage  - stały bps, wejście I wyjście

Uproszczenie Fazy 0 (jawne): funding_rate_8h to JEDNA stała średnia historyczna, nie
modelowanie zmienności funding w czasie — Faza 1 podłączy realne dane.
"""

from __future__ import annotations

# Źródło prawdy: config/settings.yaml, sekcja `costs`. Wartości startowe.
TAKER_FEE_RATE = 0.0005  # 0.05% za stronę (Binance USDS-M Futures, VIP0 taker)
MAKER_FEE_RATE = 0.0002  # 0.02% za stronę (Binance USDS-M Futures, VIP0 maker) — Commit 2.12/Z6
FUNDING_RATE_8H = 0.0001  # 0.01% / 8h — przybliżenie, brak jeszcze realnych danych funding
SLIPPAGE_BPS = 2.0  # 2 bps = 0.02%, stała wartość startowa

CANDLE_MINUTES = 5  # timeframe — config/settings.yaml data.timeframe="5m"
FUNDING_PERIOD_HOURS = 8  # Binance USDS-M Futures rozlicza funding 3x/dzień


def round_trip_fee_cost(notional: float, taker_fee_rate: float = TAKER_FEE_RATE) -> float:
    """Koszt fee za pełny obrót (wejście + wyjście), 2x taker fee — zakładamy market orders."""
    return 2.0 * notional * taker_fee_rate


# --- Commit 2.12 (Backlog Z6): koszt zależny od TYPU ZLECENIA per noga ---

MAKER = "maker"
TAKER = "taker"
_VALID_LEGS = (MAKER, TAKER)

# --- H3: powody wyjścia i modele wykonania mieszkają TUTAJ, nie w engine.py ---
#
# Do H3 stałe `EXECUTION_*` żyły w `backtest/engine.py`, a bramka kosztowa miała WŁASNĄ,
# ręczną kopię reguły "maker_limit ⇒ wejście maker". Dwie kopie tej samej wiedzy w dwóch
# modułach są powodem, dla którego bramka mogła po cichu rozjechać się z journalem.
# "Model wykonania" jest pojęciem KOSZTOWYM — jego miejsce jest w tym module.
EXIT_REASON_TP = "tp"
EXIT_REASON_SL = "sl"
EXIT_REASON_TIMEOUT = "timeout"
VALID_EXIT_REASONS = (EXIT_REASON_TP, EXIT_REASON_SL, EXIT_REASON_TIMEOUT)

EXECUTION_TAKER_ONLY = "taker_only"
EXECUTION_MAKER_LIMIT = "maker_limit"
VALID_EXECUTION_MODELS = (EXECUTION_TAKER_ONLY, EXECUTION_MAKER_LIMIT)

# Wartość BASELINE. Patrz `exit_leg_for_reason` — dlaczego to jest wartość domyślna
# i dlaczego runda H3 jej NIE zmieniła (reguła D1 w runs/2026-09-22_h3-noga-timeout-pasmo/).
DEFAULT_TIMEOUT_LEG = TAKER


def leg_fee_rate(
    leg: str,
    maker_fee_rate: float = MAKER_FEE_RATE,
    taker_fee_rate: float = TAKER_FEE_RATE,
) -> float:
    """Stawka fee dla jednej nogi. Podnosi ValueError na nieznanym typie — literówka
    w nazwie nogi musi być błędem głośnym, nie cichym wyborem droższej/tańszej stawki."""
    if leg not in _VALID_LEGS:
        raise ValueError(f"leg musi być jednym z {_VALID_LEGS}, dostałem: {leg!r}")
    return maker_fee_rate if leg == MAKER else taker_fee_rate


def exit_leg_for_reason(exit_reason: str, timeout_leg: str = DEFAULT_TIMEOUT_LEG) -> str:
    """
    Typ zlecenia nogi WYJŚCIA wynika z powodu wyjścia — to nie jest wybór strategii,
    tylko mechanika giełdy.

    KRYTERIUM (H3, `docs/rag/04`): **noga maker jest dobrze zdefiniowana tylko wtedy,
    gdy CENA zlecenia jest znana w momencie jego składania.** Zlecenie limit to para
    (cena, czas ważności) — nie da się złożyć limitu "na tę świecę, po cenie jaka wyjdzie".

        tp      -> maker: cena ZNANA w chwili wejścia (`entry ± ATR_MULTIPLIER × ATR`);
                   brak wypełnienia = po prostu nie było TP, transakcja trwa dalej
        sl      -> taker: cena znana, ale wyjście PRZYMUSOWE — stop-loss musi być market,
                   inaczej nie ma gwarancji wyjścia
        timeout -> `timeout_leg`: jedyna noga, gdzie znamy CZAS (świeca t+V), a NIE cenę

    Stąd asymetria kosztu: wygrana transakcja jest TAŃSZA niż przegrana. To realistyczne
    i działa na niekorzyść strategii o niskiej trafności — czyli konserwatywnie wobec
    naszej hipotezy, nie na jej korzyść.

    `timeout_leg` to NAZWANY WARIANT do analizy wrażliwości, nie pokrętło do strojenia
    (ta sama konwencja co `execution_model`). Domyślne `TAKER` odtwarza baseline co do bitu.
    Runda H3 zmierzyła oba krańce i **domyślnej nie zmieniła** — bo `MAKER` jest tu
    optymistyczny nie tylko na opłatach, ale i na CENIE: `engine._resolve_exit_price`
    liczy wyjście timeoutu jako `close` świecy timeoutu, a żeby dostać *ten* `close`
    zleceniem limit, trzeba by znać go z wyprzedzeniem albo skrosować księgę. Naliczenie
    stawki maker za cenę osiągalną wyłącznie taker-em to policzenie tej samej korzyści
    dwa razy.

    Trzecia wartość albo ciągła stopa wypełnienia wymaga ŹRÓDŁA DANYCH o fillach.
    Bez niego nie wchodzi do repo (`docs/rag/04`).

    Raises:
        ValueError: na nieznanym `exit_reason` albo `timeout_leg`. Do H3 była tu
            konstrukcja `else`, więc KAŻDY string ≠ "tp" (w tym literówka `"TP"` czy
            `"vertical"`) cicho zwracał TAKER.
    """
    if exit_reason not in VALID_EXIT_REASONS:
        raise ValueError(
            f"exit_reason musi być jednym z {VALID_EXIT_REASONS}, dostałem: {exit_reason!r}"
        )
    if timeout_leg not in _VALID_LEGS:
        raise ValueError(f"timeout_leg musi być jednym z {_VALID_LEGS}, dostałem: {timeout_leg!r}")
    if exit_reason == EXIT_REASON_TP:
        return MAKER
    if exit_reason == EXIT_REASON_SL:
        return TAKER
    return timeout_leg


def execution_legs(
    execution_model: str,
    exit_reason: str,
    timeout_leg: str = DEFAULT_TIMEOUT_LEG,
) -> tuple[str, str]:
    """
    Para (noga wejścia, noga wyjścia) dla danego modelu wykonania i powodu wyjścia.

    JEDNO źródło prawdy o nogach — zarówno dla kosztu w journalu, jak (pośrednio, przez
    `gate_cost_fraction`) dla bramki kosztowej. Do H3 ta wiedza była zduplikowana:
    `engine._execution_legs` znało ją w całości, a `engine._collect_candidate_signals`
    miało własną, ręczną kopię dla wejścia i literał `TAKER` dla wyjścia.

        taker_only   — wszystko market; IGNORUJE `timeout_leg` (regresja baseline'u
                       C2.10/C2.11 sprzed wprowadzenia modelu maker/taker)
        maker_limit  — wejście limit, wyjście wg `exit_leg_for_reason`

    Raises:
        ValueError: na nieznanym `execution_model` (albo, z `exit_leg_for_reason`,
            na nieznanym `exit_reason`/`timeout_leg`).
    """
    if execution_model == EXECUTION_TAKER_ONLY:
        # Walidujemy mimo nieużywania, żeby literówka nie przechodziła cicho tylko
        # dlatego, że akurat wybrano model, który tego argumentu nie czyta.
        exit_leg_for_reason(exit_reason, timeout_leg)
        return TAKER, TAKER
    if execution_model == EXECUTION_MAKER_LIMIT:
        return MAKER, exit_leg_for_reason(exit_reason, timeout_leg)
    raise ValueError(
        f"execution_model musi być jednym z {VALID_EXECUTION_MODELS}, "
        f"dostałem: {execution_model!r}"
    )


def funding_cost(
    notional: float,
    holding_candles: float,
    direction: int,
    funding_rate_8h: float = FUNDING_RATE_8H,
    candle_minutes: int = CANDLE_MINUTES,
) -> float:
    """
    Koszt (albo przychód, jeśli ujemny) funding rate za czas trzymania pozycji.

    direction: +1 long (płaci dodatni funding), -1 short (otrzymuje dodatni funding
    — stąd znak `direction` bezpośrednio we wzorze, nie wartość absolutna).

    Args:
        notional: wartość nominalna pozycji (position_size * entry_price).
        holding_candles: liczba świec trzymania pozycji (np. exit_bar_offset).
        direction: +1 (long) albo -1 (short).
        funding_rate_8h: stopa funding za jeden okres rozliczeniowy (8h).
        candle_minutes: długość świecy w minutach (timeframe).
    """
    holding_hours = holding_candles * candle_minutes / 60.0
    periods = holding_hours / FUNDING_PERIOD_HOURS
    return direction * notional * funding_rate_8h * periods


def slippage_cost(notional: float, slippage_bps: float = SLIPPAGE_BPS) -> float:
    """Koszt poślizgu dla JEDNEGO wykonania (nie round-trip) — stała liczba bps."""
    return notional * (slippage_bps / 10_000.0)


def round_trip_cost_fraction(
    taker_fee_rate: float = TAKER_FEE_RATE,
    slippage_bps: float = SLIPPAGE_BPS,
    entry_leg: str = TAKER,
    exit_leg: str = TAKER,
    maker_fee_rate: float = MAKER_FEE_RATE,
) -> float:
    """
    Koszt pełnego obrotu jako UŁAMEK NOMINAŁU, niezależny od wielkości pozycji,
    kierunku i czasu trzymania:

        fee(entry_leg) + fee(exit_leg) + slippage (tylko nogi taker)

    Commit 2.12 (Z6): domyślne `entry_leg`/`exit_leg` = taker/taker, żeby ta funkcja
    pozostała wstecznie zgodna (baseline C2.10/C2.11 odtwarzalny co do cyfry). Wywołanie
    z `backtest.engine` podaje typy nóg jawnie.

    Ta funkcja obsługuje decyzję PRZED wejściem w pozycję (bramka kosztowa, Commit 2d),
    więc NIE MOŻE znać powodu wyjścia — a ten decyduje o typie nogi wyjścia
    (`exit_leg_for_reason`). Wywołujący powinien więc podać założenie KONSERWATYWNE:
    wyjście jako taker (czyli tak, jakby każda transakcja kończyła się stopem albo
    timeoutem). Zaniżanie kosztu tutaj przepuszczałoby przez bramkę sygnały, których
    bariera nie pokrywa realnego kosztu — dokładnie ten błąd, który bramka ma łapać.

    Świadomie BEZ funding: funding zależy od `direction` i `holding_candles`, więc nie
    da się go wyrazić jako stały ułamek nominału. Empirycznie (C2c.1, realne transakcje)
    funding to ~0,0004% nominału wobec ~0,140% dla fee+slippage — pomijalny w roli, do
    której ta funkcja służy (Commit 2d: porównanie szerokości bariery triple-barrier z
    kosztem, `agents.risk_controller.is_cost_feasible`). Pełny, dokładny koszt konkretnej
    transakcji liczy `total_round_trip_cost` — ta funkcja jest jego konserwatywnym
    (zaniżonym) przybliżeniem do decyzji PRZED wejściem w pozycję, kiedy czas trzymania
    nie jest jeszcze znany.

    Returns:
        Ułamek nominału (np. 0.0014 = 0.14%).
    """
    slip_per_leg = slippage_bps / 10_000.0
    total = 0.0
    for leg in (entry_leg, exit_leg):
        total += leg_fee_rate(leg, maker_fee_rate, taker_fee_rate)
        if leg == TAKER:
            total += slip_per_leg
    return total


def gate_cost_fraction(
    execution_model: str,
    timeout_leg: str = DEFAULT_TIMEOUT_LEG,
    taker_fee_rate: float = TAKER_FEE_RATE,
    slippage_bps: float = SLIPPAGE_BPS,
    maker_fee_rate: float = MAKER_FEE_RATE,
) -> float:
    """
    Koszt dla BRAMKI KOSZTOWEJ: **maksimum** `round_trip_cost_fraction` po wszystkich
    osiągalnych powodach wyjścia przy danym modelu wykonania.

    Bramka działa PRZED wejściem w pozycję, więc nie zna powodu wyjścia — a ten decyduje
    o typie nogi. Musi więc założyć **najdroższy osiągalny**. To nie jest ostrożność
    z dyscypliny, tylko z konstrukcji: gdyby liczyła koszt OCZEKIWANY (tańszy, bo `tp`
    kosztuje mniej), przepuszczałaby świece, na których stop-out jest arytmetycznie nie
    do pokrycia — dokładnie ten błąd, który bramka ma łapać (Commit 2d).

    Do H3 `engine._collect_candidate_signals` liczyło to samo literałem `exit_leg=TAKER`,
    obok własnej kopii reguły wejścia. Nic nie wiązało tej wartości z journalem, więc
    rozjazd był kwestią czasu. Teraz bramka **nie ma własnej wiedzy o nogach** —
    konsumuje wyjście tej samej funkcji co journal, a dodanie czwartego powodu wyjścia
    albo zmiana mapowania automatycznie ją przesuwa.

    Wartości baseline: `maker_limit` → **0,0009**, `taker_only` → **0,0014**.

    Bramka pomija funding — i H3 sprawdziła, czy to jej nie psuje. Przed rundą
    prognoza brzmiała: na 4h/V=3 funding sięgnie ~+0,015% nominału (~17% bramki 0,090%),
    co czyniłoby ją ANTY-konserwatywną. **Pomiar to obalił:** funding wyszedł
    **−0,00243% nominału** (2,7% bramki, znak UJEMNY — pozycja średnio funding
    inkasuje, bo w próbie są obie strony). Pominięcie działa więc w stronę
    konserwatywną i osobny kandydat na rundę został wycofany
    (`runs/2026-09-22_h3-noga-timeout-pasmo/`, sekcja 6).

    Returns:
        Ułamek nominału — górne oszacowanie kosztu obrotu, bez funding.
    """
    return max(
        round_trip_cost_fraction(
            taker_fee_rate=taker_fee_rate,
            slippage_bps=slippage_bps,
            entry_leg=entry_leg,
            exit_leg=exit_leg,
            maker_fee_rate=maker_fee_rate,
        )
        for entry_leg, exit_leg in (
            execution_legs(execution_model, reason, timeout_leg) for reason in VALID_EXIT_REASONS
        )
    )


def total_round_trip_cost(
    notional: float,
    holding_candles: float,
    direction: int,
    taker_fee_rate: float = TAKER_FEE_RATE,
    funding_rate_8h: float = FUNDING_RATE_8H,
    slippage_bps: float = SLIPPAGE_BPS,
    candle_minutes: int = CANDLE_MINUTES,
    entry_leg: str = TAKER,
    exit_leg: str = TAKER,
    maker_fee_rate: float = MAKER_FEE_RATE,
) -> float:
    """
    Suma wszystkich kosztów pełnego obrotu: fee (wejście+wyjście) + funding (czas
    trzymania) + slippage.

    Commit 2.12 (Z6): fee jest liczone PER NOGA wg jej typu (`leg_fee_rate`), a slippage
    tylko dla nóg taker — zlecenie limit spoczywające w księdze z definicji nie płaci
    poślizgu, bo to ONO wyznacza cenę. Domyślne taker/taker zachowują wsteczną zgodność.

    ZAŁOŻENIE JAWNE (ograniczenie modelu, nie wynik): noga maker zakłada, że zlecenie
    limit SIĘ WYPEŁNIA. Pomija adverse selection — limit wypełnia się częściej wtedy,
    gdy rynek idzie przeciw pozycji, a nie wypełnia się, gdy cena od razu ucieka
    w korzystną stronę. Realny koszt maker jest więc wyższy niż modelowany tutaj o
    składnik, którego backtest Fazy 0 nie mierzy.
    """
    fee = notional * (
        leg_fee_rate(entry_leg, maker_fee_rate, taker_fee_rate)
        + leg_fee_rate(exit_leg, maker_fee_rate, taker_fee_rate)
    )
    funding = funding_cost(notional, holding_candles, direction, funding_rate_8h, candle_minutes)
    n_taker_legs = sum(1 for leg in (entry_leg, exit_leg) if leg == TAKER)
    slip = n_taker_legs * slippage_cost(notional, slippage_bps)
    return fee + funding + slip
