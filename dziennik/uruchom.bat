@echo off
REM Dziennik na zywo CLAS-5: pobranie danych + zapis pozycji i wyniku (dziennik/README.md)
REM Uruchamiany przez Harmonogram zadan Windows ("CLAS5 dziennik", codziennie 02:30; README: "Codziennie")
cd /d "%~dp0.."
set PYTHONUTF8=1
set PY=py
where py >nul 2>nul || set PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
echo ===== start %date% %time% >> dziennik\ostatni_wydruk.txt
%PY% -m backtest.live_journal >> dziennik\ostatni_wydruk.txt 2>&1
set RC=%errorlevel%
echo ===== koniec %date% %time%, kod %RC% >> dziennik\ostatni_wydruk.txt
exit /b %RC%
