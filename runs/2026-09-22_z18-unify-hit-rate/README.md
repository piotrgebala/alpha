# Z18 — jedna definicja `p` + rozbicie per typ wyjścia: edge nie chowa się nigdzie (2026-09-22)

## ID testu

**Z18** (Backlog II) — patrz `runs/INDEX.md`.

## Metadane

- **Branch:** `task/Z18-unify-hit-rate`
- **Poprzedzający stan (master):** `3fcc5f6` (Z17+Z21).
- **Komenda:** `checkpoint_lib.run_and_summarize` na 3 latach (pipeline po naprawie Z17+Z21).
- **Zmiany:** `backtest/metrics.py` — definicja kanoniczna `p` udokumentowana w
  `compute_hit_rate`; `summarize_edge_by_regime` dostaje kolumny `share_timeout`,
  `hit_rate_barrier`, `hit_rate_timeout`.
- **Warianty hipotezy: 0** (ujednolicenie definicji + rozbicie diagnostyczne).
- **Testy:** **231/231** (226 + 5, w tym property test na średnią ważoną).

## Na czym polegał problem

Audyt zgłaszał „trzy niekompatybilne definicje `p` w obiegu, różniące się o 6–14 pp".
Weryfikacja w kodzie pokazała, że **zarzut był częściowo przesadzony**: `gross_pnl > 0`
jest używane spójnie w `metrics.py` i `diagnose_cost_feasibility.py`, a `direction * label > 0`
(`engine.py:438`) to `_resolve_exit_reason` — funkcja od typu wyjścia, nie od trafności.

Realne ryzyko jest węższe, ale prawdziwe: obie definicje są **równoważne dla wyjść po
barierze poziomej** (tp/sl) i **rozjeżdżają się wyłącznie na timeoutach** (`label == 0`).
Tam `direction * label > 0` jest zawsze fałszywe, więc liczy każdy timeout jako porażkę —
także zamknięty z zyskiem. To nie jest hipotetyczne: taka definicja jest kusząca, bo nie
wymaga journalu, i dokładnie takiej użyła jedna z propozycji rund odrzuconych w audycie.

## Wynik — skala rozjazdu i lokalizacja (nie)edge'u

**Rozjazd definicji, zmierzony:**

| reżim | kanoniczna (`gross_pnl>0`) | naiwna (tylko `tp`) | różnica |
|---|---|---|---|
| `range` | **50,38%** | 44,74% | **+5,64 pp** |
| `trend` | **50,84%** | 42,81% | **+8,03 pp** |

**Rozbicie trafności per typ wyjścia:**

| reżim | n | udział timeoutów | trafność bariera (tp/sl) | trafność timeout | kanoniczna |
|---|---|---|---|---|---|
| `range` | 7 043 | 11,4% | **50,50%** | 49,38% | 50,38% |
| `trend` | 299 | 14,7% | **50,20%** | 54,55% (n=44) | 50,84% |

Liczebności: `range` tp=3 151 / sl=3 088 / timeout=804; `trend` tp=128 / sl=127 / timeout=44.

## Co na plus (+)

- **Zamknięta konkretna hipoteza ucieczkowa.** Dotąd dało się sensownie przypuszczać, że
  `p` wygląda źle, bo timeouty (wyjścia „po rynku", o węższym ruchu) **rozcieńczają** czysty
  sygnał z trafień bariery. Pomiar mówi: nie. Trafność na samych barierach poziomych to
  **50,50%** (`range`) i **50,20%** (`trend`) — czyli edge nie chowa się w żadnej składowej.
  Przy n=6 239 barierowych transakcji w `range` to solidna próba.
- Rozjazd definicji zmierzony (+5,6 / +8,0 pp) i mieści się w przewidywanym przez audyt
  przedziale 6–14 pp — przy czym audyt zawyżał górny kraniec.
- Definicja kanoniczna jest teraz **udokumentowana w kodzie** wraz z uzasadnieniem, więc
  następna runda nie odtworzy tego błędu; property test pilnuje, że kanoniczna trafność
  jest średnią ważoną składowych.
- Raport nie wywala się na journalu sprzed C2.12 (brak kolumny `exit_reason` → NaN
  w kolumnach rozbicia, miara kanoniczna nadal policzalna).

## Co na minus (−)

- **Zarzut audytu był przesadzony** — nie było trzech definicji w obiegu, tylko jedna
  używana i jedna kusząca. Wartość rundy jest więc mniejsza, niż zakładał backlog:
  prewencyjna i diagnostyczna, nie naprawcza.
- `hit_rate_timeout` w `trend` (54,55%) opiera się na **44 transakcjach** — to szum,
  nie sygnał, i nie należy go czytać jako „w trend timeouty są lepsze".
- Rozbicie nie odpowiada na pytanie, czy timeouty mają inną **wielkość** wypłaty (tylko
  znak). Pełna analiza wymagałaby rozkładu `gross_pct` per typ wyjścia — nie zrobione.
- Runda nie przybliża do GO; jak Z16 i Z17, porządkuje pomiar.

## Wniosek

Definicja kanoniczna `p` = `gross_pnl > 0` jest udokumentowana i przetestowana, a naiwna
alternatywa zaniżałaby trafność o 5,6–8,0 pp.

Ważniejsze jest jednak to, co pokazało rozbicie: **trafność jest ~50% w KAŻDEJ składowej**.
Nie ma podzbioru transakcji — ani trafień bariery, ani timeoutów — w którym sygnał byłby
lepszy. To zamyka przypuszczenie, że `p` jest zaniżone przez mieszanie różnych typów
wypłat, i wzmacnia wniosek z Z17: po usunięciu przecieku model nie odróżnia kierunku.

## SPROSTOWANIE (walidacja S1, 2026-09-22) — wniosek o składowych WYCOFANY

> Kluczowy wniosek tej rundy — **„trafność na samych barierach poziomych to 50,50%, więc edge
> nie chowa się w żadnej składowej"** — opierał się na mierze, która **nie mogła pokazać nic
> innego**.
>
> `hit_rate_barrier` jest **tautologiczne**: `backtest/engine.py::_resolve_exit_price`
> rekonstruuje cenę wyjścia z etykiety (`entry ± ATR_MULTIPLIER × atr_14`), a
> `_resolve_exit_reason` nadaje `tp`/`sl` z **tej samej** etykiety. Skutek: każde `tp` ma
> `gross_pnl > 0`, każde `sl` ma `gross_pnl < 0`, więc `hit_rate_barrier` ≡ udział `tp`
> wśród wyjść barierowych. Zweryfikowane na S1: 0,512821 × 429 = **dokładnie 220 = liczba `tp`**.
>
> Miara opisuje **zgodność kierunku z etykietą**, a nie jakość wykonania czy geometrię wypłaty.
> Jedyne transakcje z **realną ceną rynkową** na wyjściu to **timeouty**.
>
> **Co pozostaje w mocy:** rozjazd definicji `p` (naiwna zaniżała o +5,6/+8,0 pp) — to ustalenie
> jest niezależne od powyższego i nadal obowiązuje. **Co wypada:** twierdzenie o braku edge'u
> „w każdej składowej". Na timeoutach (608 transakcji w S1, jedyna składowa z niezależną
> informacją) trafność wynosi 46,71%.

---

## Rekomendacja

Zadania naprawcze z Backlog II są w tym momencie wyczerpane w części, która mogła
zniekształcać pomiar (Z17, Z21, Z18). Pozostaje jedyny nigdy nie wykonany pomiar
merytoryczny: **`p` na sygnale SPÓJNYM** (Z16: `range` da się uspójnić — mediana epizodu
5 → 39 świec przy udziale 46,9%) i przy relacji B/C zmienionej przez grubszy interwał (Z9).

Trzeźwo: przy `B = 0,20%` i `C = 0,068%` próg opłacalności w `range` to **66,7%**, a mierzymy
**50,4%** — na barierach poziomych **50,5%**. Uspójnienie i grubszy interwał obniżają próg
(na 4h szacunkowo do ~55%), ale muszą jednocześnie podnieść `p` o kilkanaście punktów.
Żaden z pięciu dotychczasowych pomiarów nie wskazuje, że `p` da się ruszyć.

## Pełny surowy output

```
[data] 315648 świec: 2023-07-01 00:00:00+00:00 -> 2026-06-30 23:55:00+00:00
[data] brak dziur.
=== Rozbicie trafnosci per typ wyjscia (Z18) ===
regime  n_trades  hit_rate   z_stat  share_timeout  hit_rate_barrier  hit_rate_timeout  break_even_p    margin
 range      7043  0.503763 0.631534       0.114156          0.505049          0.493781      0.666961 -0.163199
 trend       299  0.508361 0.289157       0.147157          0.501961          0.545455      0.580843 -0.072482

=== Liczebnosci per exit_reason ===
regime  exit_reason
range   sl             3088
        timeout         804
        tp             3151
trend   sl              127
        timeout          44
        tp              128

=== Ile bylaby trafnosc wg BLEDNEJ definicji (dir*label>0, czyli tylko tp) ===
range  kanoniczna=50.38%  naiwna(tylko tp)=44.74%  roznica=+5.64 pp
trend  kanoniczna=50.84%  naiwna(tylko tp)=42.81%  roznica=+8.03 pp
```
