@echo off
REM Dziennik na zywo CLAS-5 (dziennik/README.md). Harmonogram zadan Windows: "CLAS5 dziennik", 02:30.
REM Dziala w OSOBNYM klonie C:\Users\pitge\GIT\alpha-dziennik (zawsze master, nikt w nim nie pracuje).
REM 1) aktualizacja kodu z origin/master, 2) przebieg z ponowieniami (3 proby co 30 min - Harmonogram
REM    nie widzi kodu wyjscia przez conhost --headless), 3) zapis wynikow do gita (poprawka 5).
cd /d "%~dp0.."
set PYTHONUTF8=1
set PY=py
where py >nul 2>nul || set PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
set BASH="%ProgramFiles%\Git\bin\bash.exe"
set LOG=dziennik\ostatni_wydruk.txt
if exist %BASH% (
  %BASH% -c "export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never; git pull -q --rebase --no-autostash origin master || { git rebase --abort 2>/dev/null; echo '===== aktualizacja kodu nieudana - przebieg na dotychczasowym kodzie'; }" >> %LOG% 2>&1
)
set N=0
:proba
set /a N+=1
echo ===== start %date% %time% (proba %N%) >> %LOG%
%PY% -m backtest.live_journal >> %LOG% 2>&1
set RC=%errorlevel%
echo ===== koniec %date% %time%, kod %RC% >> %LOG%
if "%RC%"=="0" goto zapis
if %N% GEQ 3 goto koniec
powershell -NoProfile -Command "Start-Sleep -Seconds 1800"
goto proba
:zapis
if exist %BASH% (
  %BASH% dziennik/zapisz_do_gita.sh >> %LOG% 2>&1
) else (
  echo ===== zapis do gita: pominiety - brak Git Bash >> %LOG%
)
:koniec
exit /b %RC%
