# Gałąź danych strony „Tokeny CLAS-5”

Ta gałąź nie ma kodu. Plik `stan.json` to dzienne liczby tokenów Claude Code w projekcie alpha: dni, modele,
źródła kosztu, wielkość kontekstu i liczba sesji, bez treści rozmów. Zapisuje go automat serwera
(`tools/odswiez_tokeny.sh` z gałęzi `master`, cron 04:30 UTC), a rutyna Cowork przepisuje go na stronę o 05:00 UTC.
Opis i zasady: `docs/rag/12_zuzycie_tokenow.md` na gałęzi `master`. Nie edytować ręcznie.
