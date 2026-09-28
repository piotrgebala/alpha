"""
journal_strategies.py — poprawka 10 dziennika (decyzja użytkownika 2026-09-26): JEDNO źródło opisu
i dokładnych założeń każdej aktywnej strategii dziennika papierowego. Liczby w opisach biorą się ze
stałych silników (czytanych w chwili budowy opisu: `ts_momentum`, `xs_momentum`, `run_coinbase_cp1`,
`rebalance_premium`, `journal_carry`, domyślne parametry `sizing.apply_rules`, koszty z `config/settings.yaml`)
i z parametrów dziennika przekazanych przez `live_journal` — opis nie może rozjechać się z kodem.

Z tego źródła powstają: blok „STRATEGIE AKTYWNE” w każdym raporcie dziennika, plik
`dziennik/strategie.csv` (nadpisywany w każdym przebiegu) i `dziennik/STRATEGIE.md`:

    PYTHONUTF8=1 py -m backtest.journal_strategies > dziennik/STRATEGIE.md

Test (`tests/test_live_journal.py`) pilnuje, że każda składowa dziennika ma opis, a STRATEGIE.md
jest aktualne względem kodu. Zmiana tego modułu = zmiana kodu dziennika (poprawka w `dziennik/README.md`).
"""

from __future__ import annotations

import sys
from inspect import signature

import backtest.rebalance_premium as rp
import backtest.run_coinbase_cp1 as cp
import backtest.ts_momentum as tsm
import backtest.xs_momentum as xsm
from backtest.checkpoint_lib import load_config
from backtest.journal_carry import CARRY_SYMBOL, carry_costs
from backtest.sizing import apply_rules
from data.fetch_universe import STABLE_BASES

LEDGER_TO_ID = {
    "trend": "trend",
    "premia_coinbase": "coinbase",
    "x1": "x1",
}  # nazwy z transakcje*.csv
CSV_COLS = ["id", "skrot", "nazwa", "opis", "zalozenia", "status", "wynik_od", "wynik_w"]


def _p(x: float, d: int = 0) -> str:
    """Procent po polsku: 0,4 → „40 %”, 0,4933 (d=1) → „49,3 %”."""
    return f"{100 * x:.{d}f}".replace(".", ",") + " %"


def _n(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def build(j: dict) -> list[dict]:
    """
    Opisy aktywnych strategii. `j` — parametry dziennika: JOURNAL_START, X1_START, CARRY_START, LEV_TREND,
    LEV_CB, MMR, WARN_DD, STOP_DD, X1_WARN_DD, X1_STOP_DD (z `live_journal`).
    """
    costs = load_config()["costs"]
    fee = costs["taker_fee_rate"] + costs["slippage_bps"] / 10_000.0
    carry_entry = carry_costs(costs).switch_cost
    r1 = {k: v.default for k, v in signature(apply_rules).parameters.items() if k != "returns"}
    start = j["JOURNAL_START"].date().isoformat()
    x1_start = j["X1_START"].date().isoformat()
    carry_start = j["CARRY_START"].date().isoformat()
    basket = (
        f"Koszyk: {rp.TOP_N} kontraktów wieczystych USDT-M Binance o największym średnim obrocie z "
        f"{rp.VOLUME_LOOKBACK_DAYS} dni przed początkiem miesiąca (min. {rp.MIN_HISTORY_DAYS} dni notowań), "
        f"bez stablecoinów ({', '.join(sorted(STABLE_BASES))}) i kontraktów na akcje/surowce (TRADIFI); "
        "skład stały przez cały miesiąc."
    )
    schedule = (
        f"Harmonogram: {tsm.PHASES} faz, każda przebudowuje swój koszyk co {tsm.HOLD_DAYS} dni (każda w inny "
        f"dzień tygodnia) i ma 1/{tsm.PHASES} kapitału składowej; wejście po zamknięciu dnia przebudowy "
        f"(00:00 UTC, cena zamknięcia), trzymanie {tsm.HOLD_DAYS} dni."
    )
    cost = (
        f"Koszty: {_p(fee, 2)} od obrotu (opłata taker {_p(costs['taker_fee_rate'], 2)} + poślizg "
        f"{_n(costs['slippage_bps'])} pb); funding naliczany codziennie (long płaci dodatni, short dostaje)."
    )
    sizing = (
        f"Wielkość: znak × min({_n(tsm.CAP)}; {_p(tsm.TARGET_VOL)} / zmienność roczna monety), w koszyku "
        f"dzielone przez liczbę monet z sygnałem; zmienność = EWMA kwadratów dziennych zmian ceny "
        f"(środek masy {tsm.EWMA_COM} dni, min. {tsm.VOL_MIN_PERIODS} dni)."
    )
    return [
        {
            "id": "trend",
            "skrot": "TS1",
            "nazwa": "Trend tygodniowy na koszyku top-20",
            "opis": (
                f"Gra z kierunkiem ostatnich {tsm.LOOKBACK_DAYS} dni na {rp.TOP_N} najpłynniejszych kontraktach: "
                "moneta rosła → long, spadała → short."
            ),
            "zalozenia": [
                basket,
                f"Sygnał: znak zmiany ceny z {tsm.LOOKBACK_DAYS} dni (zamknięcie dziś / zamknięcie "
                f"{tsm.LOOKBACK_DAYS} dni temu − 1): plus → long, minus → short, brak danych → bez pozycji.",
                sizing,
                schedule,
                f"Dźwignia: izolowany depozyt {_n(j['LEV_TREND'])}× na każdą pozycję; likwidacja, gdy cena odejdzie "
                f"od wejścia o ≥ {_p(1 / j['LEV_TREND'] - j['MMR'])} przeciw pozycji — tracony cały depozyt pozycji.",
                cost,
                "Bez stop-lossów, celów zysku i zarządzania w trakcie tygodnia (N1, TP1).",
            ],
            "status": (
                "Ślad bez dowodu: +11 %/rok [−4; +26] na historii 2021–2026 (t 1,43), dodatni 6/6 lat i 7/7 faz; "
                "rozstrzygnie dziennik."
            ),
            "wynik_od": start,
            "wynik_w": "wyniki.csv (r_trend; w portfelu R1)",
        },
        {
            "id": "coinbase",
            "skrot": "CP1",
            "nazwa": "Premia Coinbase → BTC",
            "opis": (
                "Gdy kupujący na Coinbase (USA) płacą za BTC relatywnie więcej niż zwykle, long BTC; "
                "gdy mniej — short BTC."
            ),
            "zalozenia": [
                "Premia dnia = zamknięcie Coinbase BTC-USD / zamknięcie spot Binance BTC/USDT (świeca 8h "
                "16:00–24:00 UTC) − 1.",
                f"Sygnał: znak(średnia premii z {cp.SHORT} dni − średnia premii z {cp.LONG} dni): plus → long, "
                "minus → short kontraktu BTCUSDT.",
                f"Wielkość w fazie: znak × min({_n(tsm.CAP)}; {_p(tsm.TARGET_VOL)} / zmienność roczna BTC) "
                f"(zmienność jak w trendzie).",
                schedule.replace("swój koszyk", "pozycję BTC"),
                f"Dźwignia: izolowany depozyt {_n(j['LEV_CB'])}×; likwidacja przy ruchu ≥ "
                f"{_p(1 / j['LEV_CB'] - j['MMR'], 1)} przeciw pozycji.",
                cost,
                "Bez stop-lossów, celów zysku i zarządzania w trakcie tygodnia.",
            ],
            "status": (
                "Jedyny odczyt spełniający kryterium (+32 %/rok, t 2,09), ale po korekcie na ~28–40 prób (DSR 0,52) "
                "nieodróżnialny od szczęścia; rozstrzygnie dziennik."
            ),
            "wynik_od": start,
            "wynik_w": "wyniki.csv (r_coinbase; w portfelu R1)",
        },
        {
            "id": "portfel_r1",
            "skrot": "R1",
            "nazwa": "Portfel dziennika: trend + premia Coinbase",
            "opis": (
                "Łączy obie nogi tak, żeby każda wnosiła podobne ryzyko, a cały portfel miał zmienność "
                f"ok. {_p(r1['target_vol'])} rocznie."
            ),
            "zalozenia": [
                f"Mnożniki k (osobno dla trendu i premii): wagi ∝ 1/zmienność nogi (kowariancja EWMA, środek masy "
                f"{_n(r1['com'])} dni, tylko dane sprzed dnia), skalowane do zmienności portfela "
                f"{_p(r1['target_vol'])}/rok; sufit k ≤ {_n(r1['cap'])} na nogę (zasada 5).",
                f"Przeliczenie co {r1['step']} dni; pierwsze {r1['warmup']} dni po równo.",
                "Bez hamulca po stracie (runda SZ1: szkodził) i bez przełączania nóg po stanie rynku.",
                f"Progi obsunięcia od szczytu: ostrzeżenie {_p(j['WARN_DD'], 1)}, STOP {_p(j['STOP_DD'], 1)} "
                "(1,5 × największe historyczne); STOP = żadnych nowych pozycji.",
                "Realne pieniądze (szczebel 4 ADR-09, decyzja użytkownika): depozyt ≤ 5 % całego kapitału → "
                "strategia ≈ 10 % kapitału (runda PR1).",
            ],
            "status": "Przy dwóch nogach wagi z korelacjami = wagi 1/σ (PR1); wynik papierowy liczony od startu.",
            "wynik_od": start,
            "wynik_w": "wyniki.csv (r_port, equity, drawdown)",
        },
        {
            "id": "x1",
            "skrot": "X1",
            "nazwa": "Momentum przekrojowe top-20 (osobno, tylko papier)",
            "opis": (
                f"Co tydzień long {xsm.LEG_SIZE} monet, które najbardziej zyskały przez {xsm.SIGNAL_LOOKBACK_DAYS} dni, "
                f"i short {xsm.LEG_SIZE} najsłabszych — zakład, że liderzy dalej wygrywają z maruderami."
            ),
            "zalozenia": [
                basket,
                f"Sygnał: zmiana ceny z {xsm.SIGNAL_LOOKBACK_DAYS} dni; ranking wśród członków (min. "
                f"{2 * xsm.LEG_SIZE} z sygnałem): long {xsm.LEG_SIZE} najlepszych, short {xsm.LEG_SIZE} najgorszych "
                "(remis → alfabetycznie).",
                f"Kapitał fazy: {_p(xsm.CAPITAL_PER_LEG)} na nogę long i {_p(xsm.CAPITAL_PER_LEG)} na nogę short "
                f"(po {_p(xsm.CAPITAL_PER_LEG / xsm.LEG_SIZE)} na monetę); bez dźwigni i bez likwidacji; wartość "
                "nóg wyrównywana codziennie.",
                f"Harmonogram: {tsm.PHASES} faz, przebudowa co {xsm.HOLD_DAYS} dni, trzymanie {xsm.HOLD_DAYS} dni.",
                cost,
                f"Progi obsunięcia od szczytu: ostrzeżenie {_p(j['X1_WARN_DD'], 1)}, STOP {_p(j['X1_STOP_DD'], 1)}.",
            ],
            "status": (
                "Ślad słaby: +9,5 %/rok [−21; +40] (t 0,61) jako średnia 7 faz; poza portfelem R1 "
                "(decyzja użytkownika), tylko papier."
            ),
            "wynik_od": x1_start,
            "wynik_w": "x1_wyniki.csv",
        },
        {
            "id": "carry",
            "skrot": "D1",
            "nazwa": "Carry COIN-M na BTC (osobno, tylko papier, do weryfikacji)",
            "opis": (
                f"Trzymamy 1 BTC i krótki kontrakt {CARRY_SYMBOL} rozliczany w bitcoinie na tę samą kwotę: "
                "wartość w dolarach stoi w miejscu, a zarabia opłata funding, którą płacą longi."
            ),
            "zalozenia": [
                f"Konstrukcja z rundy D1: 1 BTC zabezpieczenia kupione na spot przy starcie + short {CARRY_SYMBOL} "
                "(COIN-M, kontrakt odwrotny) o nominale równym wartości zabezpieczenia; dźwignia 1×; zawsze w pozycji — "
                "bez przełączania po znaku fundingu (C1b, wniosek 55) i bez parametrów do strojenia.",
                "Wartość USD pozycji stała (tożsamość P + N·(1/P − 1/P₀)·P = P₀): brak likwidacji i dopłat depozytu "
                "z konstrukcji; kapitał = wartość zabezpieczenia (1×).",
                "Dochód: funding COIN-M rozliczany co 8 h (00:00, 08:00, 16:00 UTC); dzień UTC = te trzy rozliczenia; "
                "stawka dodatnia — short dostaje, ujemna — płaci. Wynik = suma stawek w ułamku nominału, bez procentu "
                "składanego (jak w D1).",
                f"Koszt wejścia raz, pierwszego dnia: {_p(carry_entry, 2)} nominału (spot {_p(costs['spot_fee_rate'], 2)} "
                f"+ kontrakt taker {_p(costs['taker_fee_rate'], 2)} + poślizg {_n(costs['slippage_bps'])} pb na każdej "
                "nodze), jak w D1; koszt wyjścia (drugie tyle) nie jest naliczany, dopóki noga trwa.",
                "Dane: historia funding COIN-M z Binance (`dapi/v1/fundingRate`), pobierana w każdym przebiegu; dzień "
                "zapisywany, gdy jest zamknięty w danych; dzień z liczbą rozliczeń ≠ 3 oznaczony `komplet = False`.",
            ],
            "status": (
                "Kontraktowy przepływ, nie przewaga: D1 +9,07 %/rok [5,88; 12,26] za 2021–2026 H1, zawyżone przez "
                "2021 (+22,2 %); od 2022 rocznie +1,8 / +7,5 / +12,2 / +5,1 / +2,1 % (2026 H1), średnio +5,7 % wobec "
                "T-bill 3,95 %. Dziennik sprawdza mechanikę (kompletność rozliczeń, zgodność z giełdą), nie wynik."
            ),
            "wynik_od": carry_start,
            "wynik_w": "carry_wyniki.csv",
        },
    ]


COMMON = [
    "Dane: kontrakty wieczyste Binance USDT-M, świece dzienne UTC, tylko zamknięte; dzień odczytu (`as_of`) = "
    "ostatnia zamknięta świeca wspólna dla Binance i premii Coinbase; pozycje ogłaszane na następny dzień.",
    "Dziennik papierowy: bez realnych pieniędzy; wynik w `wyniki.csv` / `x1_wyniki.csv`, pozycje w `sygnaly.csv` / "
    "`x1_sygnaly.csv`, lista transakcji w `transakcje.csv` / `transakcje_otwarte.csv` (poprawka 9); etykiety "
    "`stan_rynku.csv` i `fng.csv` tylko zapisywane (poprawki 7–8), nie wpływają na pozycje; noga carry COIN-M "
    "(poprawka 12) ma tylko `carry_wyniki.csv` — bez sygnałów i transakcji.",
    "O realnym kapitale decyduje drabina dowodów (ADR-09) i użytkownik; odczyt dziennika ~2026-12-25.",
]


def summarize(book: list[dict]) -> str:
    """Blok raportu: krótki opis każdej aktywnej strategii (zawsze drukowany)."""
    lines = ["  STRATEGIE AKTYWNE (poprawka 10; pełne założenia: dziennik/STRATEGIE.md):"]
    lines += [f"    {s['skrot']} — {s['nazwa']}: {s['opis']}" for s in book]
    return "\n".join(lines)


def to_rows(book: list[dict]) -> list[dict]:
    """Wiersze `dziennik/strategie.csv` w kolejności CSV_COLS (założenia sklejone znakiem ` | `)."""
    return [{k: " | ".join(s[k]) if k == "zalozenia" else s[k] for k in CSV_COLS} for s in book]


def render_markdown(book: list[dict]) -> str:
    out = [
        "# Strategie dziennika — dokładne założenia",
        "",
        "> Plik GENEROWANY z `backtest/journal_strategies.py` (poprawka 10) — nie edytuj ręcznie:",
        "> `PYTHONUTF8=1 py -m backtest.journal_strategies > dziennik/STRATEGIE.md`. Liczby pochodzą ze stałych",
        "> silników i parametrów dziennika; test pilnuje, że plik jest aktualny względem kodu.",
        "",
        "## Wspólne",
        "",
        *[f"- {c}" for c in COMMON],
        "",
    ]
    for s in book:
        out += [
            f"## {s['skrot']} — {s['nazwa']}",
            "",
            f"**Opis:** {s['opis']}",
            "",
            "**Założenia:**",
            "",
            *[f"{i}. {z}" for i, z in enumerate(s["zalozenia"], 1)],
            "",
            f"**Stan dowodów:** {s['status']}",
            "",
            f"**Wynik w dzienniku:** od {s['wynik_od']} — `{s['wynik_w']}`",
            "",
        ]
    return "\n".join(out)


def main() -> int:
    from backtest.live_journal import strategy_book

    sys.stdout.write(render_markdown(strategy_book()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
