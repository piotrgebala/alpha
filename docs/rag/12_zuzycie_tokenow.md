---
status: active
last_verified: 2026-09-28
depends_on: [10_preferencje_uzytkownika.md]
---

# 12 — Zużycie tokenów: pomiar i zasady oszczędzania (2026-09-28)

Prośba użytkownika: „monitorować zużycie i optymalizować bez utraty jakości”, z wytycznymi do sprawdzenia
(Headroom, `explain-usage`, `/clear` między rundami, subagenci, progresywne ujawnianie w skillach).
Pomiar: `PYTHONUTF8=1 python3 tools/zuzycie_tokenow.py` (zapisy Claude Code na serwerze, 2026-09-24 → 28).
Koszt ważony w jednostkach wejścia: wejście 1, zapis cache 1 h 2, odczyt cache 0,1, wyjście 5.

## Co zjadło tokeny (104 mln jednostek w 4 dni)

| źródło | udział | dlaczego |
|---|---|---|
| główna sesja | 57 % | jedna sesja od 4 dni: kontekst na wywołanie mediana 0,5–0,8 mln tokenów, maks. 0,97 mln; każde wywołanie czyta go z cache |
| — w tym przepisania kontekstu po przerwie > 1 h | 9 % | 9 razy cały kontekst (250–860 tys.) zapisany od nowa po podwójnej cenie; jedno wznowienie = 0,5–1,7 mln |
| workflow wieloagentowe | 43 % | przegląd kandydatów 24 %, wykonanie ETAP 6 15 % (tryb ultracode był włączony) |
| subagenci pojedynczy | 1 % | |

Treść dodana do kontekstu głównej sesji (znaki): argumenty moich narzędzi 25 %, wyniki poleceń Bash 24 %,
skille 23 % (104 wczytania, bo zasada 19 każe wczytywać skill na każdej gałęzi, także gdy już jest
w kontekście; po streszczeniu rozmowy harness dokleja treść wszystkich wczytanych skilli jeszcze raz,
~90 tys. znaków), odczyty plików 8 %, przypomnienia 10 %.

## Ocena wytycznych

| wytyczna | ocena na danych | decyzja |
|---|---|---|
| Headroom (kompresja wyjść narzędzi) | wyjścia narzędzi to ~⅓ dodanej treści, ≈ 5 % całego kosztu; kompresja 20–60 % dałaby 1–3 % | **nie** — zysk mały, a wspólna warstwa kompresji na drodze liczb łamie niezależność drugiej drogi (bramka 16a, pułapka H3) |
| `explain-usage` | skill niedostępny w tej sesji | zastąpiony `tools/zuzycie_tokenow.py` (powtarzalny, per dzień i źródło) |
| `/clear` / nowa sesja między zadaniami | największa dźwignia: kontekst świeżej sesji ~90 tys. wobec 500–800 tys.; szacunek −25–35 % kosztu całości, plus znika większość przepisań po przerwie | **tak** — praktyka użytkownika (nowa sesja na zadanie i po przerwie > 1 h); wiedza przechodzi przez `runs/INDEX.md`, `STATUS.md`, pamięć |
| subagenci do przeszukiwania | pojedynczy subagenci tanio (1 %), ale workflow = 43 % | **tak, z umiarem** — workflow tylko na wyraźne życzenie; weryfikacja „jeden agent, trzy soczewki” zamiast trzech agentów, gdy liczby nie są kluczowe |
| progresywne ujawnianie w skillach | już jest (SKILL.md + `references/`); największy `clas5-quant` SKILL.md 18 KB ma nieaktualną sekcję „Stan projektu (2026-09-23)” | **opcjonalnie** — odchudzić przy następnej wersji skilla (~−10 KB na wczytanie) |

## Zasady oszczędzania bez utraty jakości

1. **Nowa sesja na każde nowe zadanie** i po każdej przerwie > 1 h (cache wygasa; wznowienie długiej sesji
   kosztuje pełny zapis kontekstu). Kontynuacja tej samej sesji tylko, gdy zadanie trwa.
2. **Workflow wieloagentowe tylko na wyraźne życzenie** (tryb ultracode wyłączony domyślnie). Przy
   przeglądach: niezależni recenzenci dla kluczowych liczb i kodu dziennika; resztę jeden agent w soczewkach.
3. **Wąskie wyjścia narzędzi**: `grep`/`head`/`tail` zamiast całych plików i diffów; duże wyniki do pliku,
   do kontekstu tylko podsumowanie.
4. **Pomiar co tydzień** albo po dużym zadaniu: `tools/zuzycie_tokenow.py --od <data>`; porównanie z tabelą wyżej.
5. **Do decyzji użytkownika:** zasada 19 — gdy skill wczytano w tej samej sesji i jego treść jest nadal
   w kontekście (bez streszczenia po drodze), rejestracja na nowej gałęzi bez ponownego wczytania
   (osobne polecenie w `tools/skill_audit.py`). Oszczędność: część z ~23 % treści skilli w głównej sesji.
