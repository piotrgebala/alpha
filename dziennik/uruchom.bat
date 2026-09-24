@echo off
REM Dziennik na zywo CLAS-5: pobranie danych + zapis pozycji i wyniku (dziennik/README.md)
REM Uruchamiany przez Harmonogram zadan Windows ("CLAS5 dziennik", codziennie 02:30; README: "Codziennie")
REM Poprawka 5 (2026-09-24): po udanym przebiegu commit plikow dziennika i push na master (zapisz_do_gita.sh)
cd /d "%~dp0.."
set PYTHONUTF8=1
set PY=py
where py >nul 2>nul || set PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
echo ===== start %date% %time% >> dziennik\ostatni_wydruk.txt
%PY% -m backtest.live_journal >> dziennik\ostatni_wydruk.txt 2>&1
set RC=%errorlevel%
echo ===== koniec %date% %time%, kod %RC% >> dziennik\ostatni_wydruk.txt
if not "%RC%"=="0" exit /b %RC%
set BASH="%ProgramFiles%\Git\bin\bash.exe"
if exist %BASH% (
  %BASH% dziennik/zapisz_do_gita.sh >> dziennik\ostatni_wydruk.txt 2>&1
) else (
  echo ===== zapis do gita pominiety: brak Git Bash >> dziennik\ostatni_wydruk.txt
)
exit /b 0
