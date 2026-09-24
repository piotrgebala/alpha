# 10 — Preferencje użytkownika i zasady pracy (przeniesione z pamięci lokalnej, 2026-09-24)

Po co: pamięć automatyczna Claude Code leży na maszynie (`~/.claude/projects/.../memory/`)
i nie przechodzi na serwer ani do innych środowisk. Te ustalenia zmieniają sposób raportowania
i wybór rund, więc mieszkają w repo. Źródło każdej: decyzja użytkownika w rozmowie (data w nawiasie).

## Sposób handlu (2026-09-23, doprecyzowane 2026-09-24)
- Perpetuale (futures bez daty), longi i shorty, **dźwignia 3× na CZĘŚCI kapitału** — depozyt na
  pozycję, nie 3× całego kapitału.
- Raportując strategię, przekładaj wynik na te realia: ekspozycja reguły (nominał/kapitał) →
  **depozyt przy 3× = ekspozycja / 3** (np. 0,75× → 25 % kapitału); likwidacja izolowana przy ruchu
  ~32 % przeciw pozycji (szczególnie altcoiny bez stopa). Nie pokazuj „brutto 3× kapitału” jako
  głównego przełożenia. 3× mnoży zysk, stratę i koszty; nie zmienia progu opłacalności ani znaku przewagi.
- Nie myl limitu `max_leverage: 3.0` z faktyczną ekspozycją w backteście.

## Cel zwrotów (2026-09-23)
- „Carry odpuszczamy — nie o takie zwroty mi chodzi”: strategie przepływowe rzędu kilku %/rok
  (carry, basis, cash-and-carry), nawet dodatnie i mierzalne, są poza celem. Cel: zwroty rzędu
  zakładu o kierunek (kierunkowe / relatywne).
- Przy wyborze rundy pomijaj rodziny carry/przepływ (katalog D2) bez pytania; wynik rzędu kilku
  %/rok opisuj wprost jako poniżej celu użytkownika.

## Rynek przed 2022 (2026-09-24)
- Dane sprzed 2022 to „średni temat do analizy” (inny rynek, większe wahania). Nie proponuj okresów
  sprzed 2021 jako testu poza próbą.
- Przy wynikach z bazy od 2021 (zasada 20) pokazuj opisowo „2021 vs od 2022”, ale NIE przesuwaj startu
  bazy na podstawie obejrzanych wyników (post hoc). Zmiana startu na 2022 = decyzja użytkownika dla
  wszystkiego naraz.
- Obserwacja na żywo 2–3 miesiące = sprawdzian mechaniki, nie przewagi.

## Skille i wtyczki
- Skille projektu (`clas5-runda`, `clas5-quant`, `quant-strategy-catalog`, `ta-toolkit`, `lean-research`,
  też `zarzadzanie-pozycja`, `doradca-inwestycyjny`) żyją w chmurze konta claude.ai, nie w repo
  (CLAUDE.md, wytyczne). Zmiana skilla = nowa wersja + paczka, użytkownik wgrywa na claude.ai; zdanie
  w STATUS.md. Nie twórz skilli w `.claude/skills/`.
- Na nowej maszynie (serwer) zaloguj Claude Code na to samo konto — skille konta synchronizują się
  same; sprawdź `/skills`, czy są `clas5-*`, `engineering:*`, `data:*`. Brak → zasada 19 („niedostępny
  w sesji” + procedura z `docs/skills/bramki-jakosci.md`).
- Tryb auto Claude Code blokuje edycję `~/.claude.json`, `~/.claude/settings.json` i `claude plugin
  install/uninstall` (samomodyfikacja) — wtyczki włączaj w `.claude/settings.json` projektu, resztę
  zostaw użytkownikowi z gotową komendą.

## Inne repo użytkownika
- `sigma` (osobne repo, QuantConnect): ML ETH 4h, wyniki na ~28 transakcjach; rodzina „ML na OHLCV”
  zamknięta w CLAS-5 (wniosek 11); jedyny nowy element to BTC→ETH lead-lag. Szczegóły:
  `docs/rag/Repo lessons i sigma — co przydatne dla alpha.md`.
