---
id: 024
tytul: Nazwy plików w data/raw/universe_full w kodowaniu cp866 — naprawa nazw bez zmiany treści
typ: naprawa
status: w_toku
zlecil: orkiestrator
decyzja_uzytkownika: "2026-09-29: „Wykonaj” (zgoda na dopisanie luk danych z LP1 i wykonanie zadań z tablicy)"
utworzono: 2026-09-29
zalezy_od: [017]
budzet: "Opus, 1 wykonawca"
---

# 024 — Nazwy plików koszyka w złym kodowaniu

## Po co

Runda LP1 (zadanie 017, `runs/2026-09-29_lp1-likwidacja-progi-binance/README.md`) znalazła na serwerze 4 pliki
w `data/raw/universe_full` z nazwą w cp866 zamiast UTF-8. Skład koszyka dostaje przez to zniekształcony symbol
(币安人生), który w LP1 wypada z kroku 2 na 1 miesiąc. Inne skrypty czytające koszyk mogą gubić go tak samo.

## Zakres

1. Wypisać pliki w `data/raw/universe_full` (i w innych katalogach `data/raw`, jeśli dotyczy) z nazwą spoza UTF-8
   albo zniekształconą; dla każdego: obecna nazwa (bajty), poprawna nazwa, sha256 treści.
2. Sprawdzić, czy plik o poprawnej nazwie już istnieje (duplikat) i czy treść jest ta sama.
3. Skrypt naprawy z trybem `--sprawdz` (tylko plan) i `--wykonaj` (zmiana nazw, bez zmiany treści), z testem na
   sztucznym katalogu. Zmianę nazw w katalogu głównym repo wykonuje orkiestrator po przeglądzie.
4. Wypisać skrypty, które czytają te pliki (także zamrożone rundy), i czy zmiana może zmienić ich wynik na serwerze.

## Czego NIE robić

- Nie zmieniać treści plików, nie pobierać ich ponownie, nie usuwać.
- Nie pisać w `data/raw` katalogu głównego repo (tylko odczyt); nie dotykać klonu dziennika ani kodu dziennika.

## Kryteria odbioru (dowody)

- Plan zmian (stara → nowa nazwa, sha256 treści), testy zielone, powtarzalna komenda.
- Po wykonaniu przez orkiestratora: te same sumy sha256 treści, poprawne nazwy, lista skryptów, których to dotyczy.

## Wynik

(dopisuje orkiestrator)
