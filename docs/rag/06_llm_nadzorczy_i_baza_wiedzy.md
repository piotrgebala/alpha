# 06 — LLM offline/nadzorczo i baza wiedzy projektu (Faza 2+, na podstawie kursu AI_Devs 4)

## Zakres i status

Ten dokument rozwija dwie rzeczy, które w `IMPLEMENTATION_PLAN.md` i `01_hipoteza_i_architektura.md`
są dziś nazwane, ale nie zaprojektowane: (a) trzy komponenty Fazy 2/3 oparte o LLM offline/nadzorczo
(`ai_interpreter.py`, `post_trade_critic.py`, `test_mathematics.py`) oraz (b) `docs/rag/` jako baza
wiedzy, z której te komponenty (i ludzie, i Claude Code) faktycznie korzystają. Materiał źródłowy:
kurs AI_Devs 4 (`4th-devs/`, lekcje S01-S05) — katalog wzorców do przeczytania i selektywnego
przepisania, dokładnie tak samo jak freqtrade/LEAN w `04_narzedzia_zewnetrzne.md`, nigdy zależność
runtime.

**Nic z tego dokumentu nie jest budowane przed checkpointem go/no-go Commitu 6** (patrz
`IMPLEMENTATION_PLAN.md` §5). Zasada nadrzędna z CLAUDE.md (zasada 6: "LLM nigdy w hot-pathie
decyzyjnym. Offline/nadzorczo tylko") i z `01_hipoteza_i_architektura.md` obowiązuje bez wyjątków —
ten dokument tylko doprecyzowuje, JAK ta zasada ma być zrealizowana, gdy przyjdzie na to czas.

## Część A — ai_interpreter.py, post_trade_critic.py, test_mathematics.py

### Trzy komponenty, trzy różne odpowiedzi na pytanie "czy to potrzebuje LLM"

`01_hipoteza_i_architektura.md` stawia pytanie wprost: "rozstrzygnąć, czy każdy 'agent' z PRD
faktycznie potrzebuje LLM, czy część to czysto deterministyczna logika." Odpowiedź nie jest taka
sama dla wszystkich trzech nazw wymienionych w Fazie 2:

- **`test_mathematics.py` (Faza 2) → NIE potrzebuje LLM.** To rozszerzenie Warstwy 3 (property-based
  testing, `05_metodologia_wytwarzania_i_testow.md`) o weryfikację matematycznych niezmienników na
  realnych/backtestowych danych, nie na syntetycznych przykładach z `hypothesis`. Przykład: sprawdzić
  empirycznie, na całej historii backtestu, że `position_size` faktycznie nigdy nie przekroczyło
  `max_leverage × equity`, że `signal_confidence` faktycznie skalowało `risk_per_trade` monotonicznie,
  że żadna cecha nie miała wartości poza oczekiwanym zakresem. To jest kod weryfikujący kod — LLM nie
  wnosi tu nic, a wniosłoby niepotrzebne ryzyko halucynacji liczb, które łatwiej i pewniej policzyć
  programistycznie.
- **`ai_interpreter.py` (Faza 2) → tak, ale wąsko: on-demand, read-only Q&A.** Narzędzie do zadawania
  pytań o system w języku naturalnym ("dlaczego transakcja X trafiła stop-loss?", "podsumuj drift
  `atr_pctrank_20d` w ostatnim miesiącu", "wyjaśnij klasyfikację regime dla daty Y"), uruchamiane
  ręcznie przez człowieka, nigdy w tle, nigdy automatycznie.
- **`post_trade_critic.py` — Faza 3, NIE Faza 2.** `04_narzedzia_zewnetrzne.md` już to rozstrzygnął:
  wzorzec "verbal reinforcement" z FinCon (agenty krytykujące wynik w języku naturalnym po
  transakcji) pasuje do analizy PO FAKCIE, a "fakty" (realne albo paper trade'y) pojawiają się
  dopiero w Fazie 3 (paper trading/testnet). W Fazie 2 nie ma jeszcze czego krytykować poza foldami
  walk-forward, które i tak są objęte checkpointem Commitu 6. Ten dokument projektuje
  `post_trade_critic.py` razem z `ai_interpreter.py`, bo dzielą narzędzia, wiedzę i wzorce
  bezpieczeństwa — ale **nie zmienia to jego przypisania do Fazy 3**.

### Projekt agenta: Identity / Protocol / Voice / Tools / Knowledge (wzorzec z S02E05)

Kurs AI_Devs 4 (S02E05, "Projektowanie agentów") opisuje zachowanie agenta jako funkcję pięciu
warstw, nie jednej długiej instrukcji z regułami "zrób X, nie rób Y". Zastosowanie do
`ai_interpreter.py`/`post_trade_critic.py`:

- **Identity:** kwantytatywny audytor/analityk ryzyka, nie trader i nie doradca inwestycyjny.
  Priorytet: wykrycie rozbieżności między założeniami a rzeczywistością (drift cech, niezgodność
  sygnału z reżimem, stop-loss trafiony poza oczekiwanym zakresem ATR), nie generowanie rekomendacji
  "co kupić".
- **Protocol:** zawsze cytować źródło liczby (numer folda, data, nazwa cechy, plik `docs/rag/`) —
  nigdy "wydaje się, że"; zakaz sugerowania zmiany parametrów (`risk_per_trade`, progi regime,
  hiperparametry modelu) bez odwołania do formalnego checkpointu (Commit 6-podobnego); jeśli dane
  potrzebne do odpowiedzi nie istnieją w dostępnych narzędziach — powiedzieć to wprost, nie zgadywać
  (bezpośrednio z S01E05: "powiedz modelowi, że czegoś nie wie, zanim zacznie zgadywać").
- **Voice:** zwięzły, techniczny, liczby zawsze z jednostką i źródłem. Styl zgodny z tym, jak pisane
  są `docs/rag/*.md` — bez marketingowego tonu, bez nadmiernej pewności.
- **Tools:** patrz sekcja niżej.
- **Knowledge:** `docs/rag/*.md`, `agents/feature_registry.yaml`, `config/settings.yaml`, trade
  journal (patrz niżej), wyniki backtestu per fold (Commit 6). Żadnej wiedzy spoza tych źródeł —
  agent nie ma dostępu do internetu ani do żadnego API poza własnym repo.

### Projekt narzędzi (tools) — zasady z S01E02/S01E03

Zasada nadrzędna z kursu: schemat narzędzia to "dokumentacja" dla modelu — im mniej pól i mniej
dwuznaczności, tym mniej halucynacji. Konkretne zasady zastosowane tutaj:

- **Zero narzędzi zapisu/egzekucji.** Żadnego `execute_trade`, `modify_position`,
  `retrain_model`, `update_config`. To jedyna twarda gwarancja, że nawet całkowicie zmanipulowany
  (prompt injection) agent nie może wyrządzić realnej szkody — może co najwyżej napisać zły raport,
  który człowiek i tak weryfikuje przed jakąkolwiek akcją.
- **Scalanie pokrewnych akcji w mniejszą liczbę bogatszych narzędzi**, zamiast jednego narzędzia na
  każdą funkcję Pythona (zasada z S01E03 — "13 operacji plikowych scalonych w 4"). Przykładowy
  zestaw startowy:
  - `get_fold_metrics(commit, fold_id)` → Sharpe/drawdown/win-rate dla wskazanego folda
    walk-forward (Commit 6).
  - `get_feature_definition(name)` → odczyt z `feature_registry.yaml` (formula/window/role/
    leakage_note) — agent cytuje definicję, nie zgaduje wzoru.
  - `get_trade_journal(date_range, regime=None)` → wpisy dziennika transakcji (patrz niżej).
  - `get_rag_doc(topic)` → pełny tekst jednego z `docs/rag/*.md` — agent odpowiada na pytania
    architektoniczne cytatem ze źródła, nie z pamięci modelu.
- **Strukturalne błędy z podpowiedzią**, nie surowy stack trace — np. "fold_id 47 nie istnieje;
  dostępny zakres to 1-23" zamiast `KeyError`.

### Pamięć: trade journal (S02E03)

Zarówno `ai_interpreter.py`, jak i `post_trade_critic.py` potrzebują ustrukturyzowanego zapisu
każdej transakcji — nie tylko equity curve z backtestu, ale per-trade: powód wejścia
(`signal_confidence`, `regime` w momencie wejścia), powód wyjścia (stop/take-profit/timeout),
faktyczny PnL, zgodność z kontraktem `risk_controllera`. To dokładnie wzorzec "dokumenty i pamięć
długoterminowa jako narzędzia" z S02E03 — z dyscypliną metadanych (źródło, data, fold/sesja), żeby
agent (i człowiek) mógł filtrować i odróżnić świeże dane od nieaktualnych.

> **Jedyna uwaga w tym dokumencie dotykająca Fazy 0:** `backtest/engine.py` (Commit 5, jeszcze nie
> zaimplementowany) to naturalne miejsce, żeby już teraz emitować per-trade log w formacie, który
> `ai_interpreter.py`/`post_trade_critic.py` będzie mógł skonsumować bez przebudowy w Fazie 2/3. To
> nie jest nowe zadanie ani zmiana zakresu Commitu 5 — to heads-up do uwzględnienia, gdy Commit 5
> będzie faktycznie specyfikowany. Nie zmienia to niczego w tym, co dzieje się teraz.

### Observability i evals — nawet nadzorczy agent musi być oceniany (S03E01)

Kurs jest tu jednoznaczny: nawet najmniejsza zmiana instrukcji systemowej czy opisu narzędzia może
znacząco wpłynąć na zachowanie modelu — a "recenzja modeli" i "raporty post-trade" to dokładnie
takie miejsca, gdzie błędna, ale przekonująco brzmiąca odpowiedź jest gorsza niż jej brak.

- **Logowanie:** każda interakcja LLM (pytanie/kontekst wejściowy, narzędzia wywołane, odpowiedź)
  zapisywana jako structured JSON do pliku — uproszczona wersja taksonomii Session/Trace/Span/
  Generation/Tool z Langfuse (S03E01), bez zewnętrznej platformy na start. Spójne z zasadą projektu
  "proste narzędzia zamiast zależności produkcyjnych, dopóki nie udowodniono potrzeby"
  (`04_narzedzia_zewnetrzne.md`).
- **Eval dataset:** ~20-30 przykładowych pytań/scenariuszy (np. "wyjaśnij, dlaczego trade z
  2026-03-14 trafił stop-loss", "czy `direction_persistence_10` miała drift w marcu?") z listą
  faktów, które MUSZĄ pojawić się w poprawnej odpowiedzi. Ocena na start: **human-graded**, nie
  LLM-graded — zbyt mała skala (rzadkie, offline zapytania), żeby uzasadnić automatyzację oceny
  (koszt opracowania sędziego LLM > wartość przy tej częstotliwości użycia).
- **Kryterium gotowości do jakiegokolwiek zaufania:** zero halucynowanych liczb. Każda liczba w
  raporcie musi pochodzić bezpośrednio z wywołania narzędzia (widoczne w logu), nigdy z "pamięci"
  modelu. To weryfikowalne programistycznie — porównanie liczb w odpowiedzi z liczbami zwróconymi
  przez narzędzia w tej samej sesji.

### Bezpieczeństwo: prompt injection i izolacja (S03E02)

- **System prompt traktowany jako publiczny** — zero sekretów, kluczy API, danych kontowych w
  instrukcji systemowej.
- **Brak narzędzi zapisu = główna linia obrony.** Nawet gdyby agent został zmanipulowany przez
  spreparowaną treść (np. w przyszłości: newsy jako kontekst), nie ma fizycznej możliwości złożenia
  zlecenia, zmiany configu czy retreningu modelu — bo takich narzędzi po prostu nie ma w jego
  zestawie.
- **Jeśli kiedyś dojdzie zewnętrzny, nieufny input** (np. artykuły/newsy jako dodatkowy kontekst dla
  `post_trade_critic.py` w Fazie 3+) — osobny "firewall"-prompt klasyfikujący
  bezpieczne/niebezpieczne PRZED głównym wątkiem, w osobnym zapytaniu, zgodnie z wzorcem z S03E02.
  Dziś żadne takie źródło nie jest podłączone — cały kontekst pochodzi z własnych, kontrolowanych
  plików repo, więc ryzyko jest obecnie zerowe, nie tylko zminimalizowane.

### Świadomie wykluczone z Fazy 2/3 (żeby nie budować więcej niż potrzeba)

- **Autonomiczne triggery** (cron/webhooks/heartbeat, S03E03) — `post_trade_critic.py` uruchamiany
  ręcznie/na żądanie, nie w tle. Automatyzacja triggerów to osobny, późniejszy eksperyment, jeśli
  ręczne uruchamianie okaże się wąskim gardłem.
- **Multi-agent orchestration** (Orchestrator + subagenci, S02E04) — jeden, wąsko wyspecjalizowany
  agent na start. Rozbicie na wiele agentów dodaje złożoność koordynacji bez oczywistej korzyści
  przy obecnym, wąskim zakresie zadań.
- **MCP server** (S01E03) — niepotrzebny przy jednym, lokalnym konsumencie (ten sam deweloper,
  to samo repo). Zwykłe funkcje Pythona jako narzędzia wystarczą; MCP miałoby sens dopiero, gdyby
  inny proces/osoba miały konsumować te same narzędzia.

### Otwarte pytania (do rozstrzygnięcia bliżej realizacji Fazy 2, nie teraz)

- Wybór modelu/dostawcy LLM — przy rzadkich, niskoczęstotliwościowych zapytaniach offline
  prawdopodobnie wystarczy tańszy/mniejszy model (S01E05: routing prostszych zadań do tańszych
  modeli); do zweryfikowania na konkretnych przykładach z eval datasetu, nie z góry.
- Format raportów `post_trade_critic.py` — rekomendacja robocza: markdown w repo, wersjonowany
  Gitem, spójny stylistycznie z `docs/rag/` — ale ostateczna decyzja poczeka do Fazy 3, gdy będą
  realne raporty do sformatowania.

## Część B — docs/rag/ jako baza wiedzy gotowa pod AI (S04E04, S02E01, S02E03)

### Co już działa dobrze — nazwać istniejącą konwencję, nie wynajdywać nowej

`docs/rag/` w obecnej formie już spełnia większość zasad z S04E04 ("Projektowanie własnej bazy
wiedzy dla AI"), tylko nie zostało to dotąd nazwane wprost:

- **Zero-implicit-context:** każdy plik (`01_hipoteza_i_architektura.md` itd.) da się zrozumieć bez
  zakładania, że czytelnik (człowiek czy Claude Code) pamięta poprzednią rozmowę — dokładnie zasada
  "pisz notatki zakładając zero zewnętrznego kontekstu" z S04E04.
- **Jeden plik = jeden temat**, z jawnymi cross-referencjami po nazwie pliku (`patrz
  03_ryzyko_i_sizing.md`) zamiast duplikowania treści między dokumentami.
- **CLAUDE.md już odsyła do konkretnych plików** przy regułach dotyczących ryzyka zmiany
  architektury ("Przeczytaj odpowiedni plik w docs/rag/") — to jest dokładnie mechanizm, który
  S04E04 opisuje jako warunek konieczny, żeby agent (lub człowiek) mógł nawigować bazę wiedzy
  samodzielnie.

### Braki względem pełnego wzorca S04E04

- **Brak YAML frontmatter** w `docs/rag/*.md` — pola takie jak `status` (draft/stabilny),
  `last_verified` (data ostatniej weryfikacji względem realnych danych/kodu), `depends_on` (lista
  innych plików rag, od których dany dokument zależy) pomogłyby zarówno człowiekowi, jak i
  przyszłemu `ai_interpreter.py` szybko ocenić aktualność i zależności bez czytania całej treści.
- **Brak jednego pliku-indeksu (Mapa Treści)** linkującego `CLAUDE.md` + `IMPLEMENTATION_PLAN.md` +
  wszystkie `docs/rag/*.md` z jednozdaniowym opisem każdego. Dziś trzeba znać nazwy plików z góry —
  widać to nawet w tym, że `IMPLEMENTATION_PLAN.md` §11 ręcznie wylicza wygenerowane pliki zamiast
  odsyłać do indeksu.

Obie te braki są **czysto dokumentacyjne** — nie dotykają kodu, configu ani logiki tradingowej,
więc mogą być domknięte w dowolnym momencie, niezależnie od fazowania Commitów. Nie są jednak
wykonane w ramach tego dokumentu — to zadanie planistyczne, patrz `IMPLEMENTATION_PLAN.md` §12.

### IMPLEMENTATION_PLAN.md jako "Observational Memory" sesji Claude Code

Nagłówek `IMPLEMENTATION_PLAN.md` mówi wprost: "Jeśli zaczynasz nową sesję Claude Code, podepnij
ten plik jako kontekst — zastępuje potrzebę przewijania całej wcześniejszej rozmowy." To dokładnie
mechanizm **Observational Memory** (Observer/Reflector) z S02E03 — kompresja stanu projektu do
terse loga, żeby nowa sesja nie musiała odtwarzać kontekstu od zera. Definition of Done (pkt 7,
`05_metodologia_wytwarzania_i_testow.md`) już wymaga aktualizacji tego pliku po każdym Commicie —
to jest dyscyplina Observera, tylko nienazwana wprost.

**Rekomendacja na przyszłość (nie teraz):** gdy `IMPLEMENTATION_PLAN.md` znacząco urośnie (np. po
zamknięciu Fazy 1), rozważyć rozdzielenie na "aktualny stan" (krótki, na górze pliku — to, co nowa
sesja faktycznie potrzebuje przeczytać) i "archiwum decyzji" (historia, osobny plik) — analogicznie
do podziału Observer (świeże logi) / Reflector (kompresja starych logów) z S02E03. Dziś plik jest
wystarczająco krótki, żeby to rozdzielenie było przedwczesną optymalizacją.

## Źródła (kurs 4th-devs / AI_Devs 4)

- S01E02 — techniki łączenia modelu z narzędziami (projekt narzędzi, schemat = dokumentacja)
- S01E03 — projektowanie API dla efektywnej pracy z modelem (MCP, scalanie narzędzi)
- S01E05 — zarządzanie jawnymi oraz niejawnymi limitami modeli (routing do tańszych modeli,
  obrona przed halucynacją)
- S02E03 — dokumenty oraz pamięć długoterminowa jako narzędzia (Observational Memory, trade
  journal jako pamięć)
- S02E04 — organizowanie kontekstu dla wielu wątków (dlaczego NIE multi-agent orchestration tutaj)
- S02E05 — projektowanie agentów (Identity/Protocol/Voice/Tools/Knowledge)
- S03E01 — obserwowanie i ewaluacja (observability, evals, dataset design)
- S03E02 — ograniczenia modeli na etapie założeń projektu (scoping, prompt injection, sandbox)
- S03E03 — kontekstowy feedback wspierający skuteczność agentów (triggery, dlaczego NIE teraz)
- S04E04 — projektowanie własnej bazy wiedzy dla AI (frontmatter, zero-implicit-context, MoC)
