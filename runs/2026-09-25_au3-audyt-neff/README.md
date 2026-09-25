# AU3 — naprawa kanonicznego N_eff i audyt dawnych werdyktów (2026-09-25)

> **STATUS: PRE-REJESTRACJA** (przed uruchomieniem audytu). Kalibracja przyrządu / audyt — POZA
> licznikami hipotez, 0 wariantów. Decyzja użytkownika 2026-09-25: „tak” (naprawa w jednym miejscu + audyt).

## W skrócie — prostym językiem (CLAUDE.md zasada 17)

AU2 wykazał błąd we wzorze, którym projekt liczy „ile naprawdę niezależnych obserwacji” ma wynik (N_eff).
Na krótkich szeregach wzór potrafił dać liczbę ujemną, a program zamieniał ją na 1 — i wtedy prawdziwy
wynik wyglądał na nierozstrzygnięty. Naprawiamy wzór w jednym miejscu i sprawdzamy WSZYSTKIE dawne
rundy: w których ten błąd w ogóle wystąpił i czy zmienia to ich werdykt. Błąd mógł tylko zaniżać
pewność, więc zmienić mogą się wyłącznie werdykty „nierozstrzygnięty” (albo sam zapis liczb t_neff).

## ID testu

**AU3** — audyt przyrządu (jak AU1). Następca AU2 kroków 1–2 (wniosek 93).

## Metadane

- Branch `au3-naprawa-neff` (z `master` `014d627`).
- **Naprawa:** `agents/labeling.py::effective_sample_size` — gdy `1 + 2Σρ ≤ 0`, N_eff = n (zamiast ujemnego).
  Wywołujący (`carry_hedged.summarize_pnl`: `max(1, min(N_eff, n))`, `checkpoint_lib.summarize_trade_returns`:
  `min(N_eff, n)`) bez zmian. Testy: `tests/test_neff_au3.py` (regresja + test właściwości `hypothesis`:
  N_eff > 0 i skończone, |t_neff| ≤ |t|), `tests/test_au3_audit.py`.
- **Audyt:** `tools/au3_audit.py` — 55 komend `py -m backtest.X …` z README rund, filtr: skrypt sięga po N_eff
  (tekst lub import, rekurencyjnie); bez `run_au2_ml` (własna pula procesów; błąd obsłużony w AU2).
  Każdy skrypt w osobnej kopii roboczej (`git worktree`, dane podlinkowane), 1 wątek numeryczny, ≤ 20 naraz,
  limit 45 min. Tryb `old` = wzór sprzed AU3 + licznik wywołań z mianownikiem ≤ 0; tryb `new` (tylko gdy licznik > 0)
  = wzór naprawiony. Komenda: `py tools/au3_audit.py exec <worktree> runs/2026-09-25_au3-audyt-neff/logi`.
- Dziennik papierowy: moduł `labeling` jest importowany pośrednio (`run_coinbase_cp1` → `carry_hedged`), ale
  dziennik nie liczy N_eff — jego wyniki się nie zmieniają; wpis „Poprawka 6” w `dziennik/README.md`.

## Poprzedzające wyniki

- **AU2 kroki 1–2 (93):** błąd odtworzony (N_eff = −990 → 1); ~25–30 % przebiegów kalibracji dotkniętych.
- **Wniosek 50 (A1, Poprawka 2):** N_eff ≤ n — korekta tylko odejmuje pewność; naprawa jest z nim zgodna.
- **AU1 (87):** poprzedni audyt metodologii — nie wykrył tego błędu (dotyczył obliczeń na konkretnych danych).

## Pre-rejestracja

- **Pytanie:** które zamrożone rundy wywołały N_eff z mianownikiem ≤ 0 i czy po naprawie zmienia się ich werdykt?
- **Odczyt per skrypt:** (a) licznik `bad_denominator` w trybie `old`; 0 → wynik rundy nietknięty (koniec);
  (b) > 0 → porównanie wydruków `old` vs `new`: linie z t_neff / werdyktem („ODCZYT KRYTERIUM”, „POZYTYWNY”,
  „NEGATYWNY”, „NIEROZSTRZYGNIĘTY”, GO/NO-GO).
- **Reguła:** werdykt zmieniony → korekta wniosku w `runs/INDEX.md` (dopisek „[korekta AU3]”) i w README rundy
  NIE (skrypty i README zamrożonych rund zostają; korekta tylko w INDEX i w tym README). Nowy POZYTYWNY =
  odczyt z zastrzeżeniem multiple testing jak w oryginalnej rundzie (licznik rundy bez zmian — to nie nowy wariant).
- **Kontrola odtwarzalności przy okazji:** wydruk `old` porównany z `raw_output` rundy (inne wersje bibliotek
  albo dane na serwerze → różnice opisowo).
- **Czego runda NIE robi:** nie zmienia kryteriów werdyktów, nie stroi niczego, nie przelicza rund bez zdarzeń.

---

_(sekcje poniżej po audycie)_
