@echo off
REM Dziennik na zywo CLAS-5: pobranie danych + zapis pozycji i wyniku (dziennik/README.md)
cd /d "%~dp0.."
set PYTHONUTF8=1
py -m backtest.live_journal >> dziennik\ostatni_wydruk.txt 2>&1
