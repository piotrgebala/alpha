@echo off
REM Dziennik na zywo CLAS-5 (dziennik/README.md). Harmonogram zadan Windows: "CLAS5 dziennik", 02:30.
REM Dziala w OSOBNYM klonie C:\Users\pitge\GIT\alpha-dziennik (zawsze master, nikt w nim nie pracuje).
REM 1) aktualizacja kodu z origin/master (z samonaprawa: aktualizuj.sh), 2) przekazanie na serwer:
REM    jesli inna maszyna zapisala dziennik w ostatnich 3 dniach - wylacz zadanie i nie licz (przejete.sh),
REM 3) przebieg z ponowieniami (3 proby co 30 min - conhost --headless nie oddaje kodu Harmonogramowi),
REM 4) zapis wynikow do gita (poprawka 5, zapisz_do_gita.sh).
REM Dziala z KOPII w %TEMP%: git pull podmienia ten plik w trakcie, a cmd czyta .bat linia po linii.
if "%~1"=="--kopia" goto kopia
copy /y "%~f0" "%TEMP%\clas5_dziennik_uruchom.bat" >nul && "%TEMP%\clas5_dziennik_uruchom.bat" --kopia "%~dp0"
set REPO=%~dp0
goto dalej
:kopia
set REPO=%~2
:dalej
cd /d "%REPO%.."
set PYTHONUTF8=1
set PY=py
where py >nul 2>nul || set PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
set BASH="%ProgramFiles%\Git\bin\bash.exe"
set LOG=dziennik\ostatni_wydruk.txt
if not exist %BASH% goto start
%BASH% dziennik/aktualizuj.sh >> %LOG% 2>&1
%BASH% dziennik/przejete.sh
if "%errorlevel%"=="0" goto przejete
goto start
:przejete
echo ===== dziennik przejety przez inna maszyne - wylaczam zadanie na komputerze >> %LOG%
schtasks /change /tn "CLAS5 dziennik" /disable >> %LOG% 2>&1 && echo ===== zadanie wylaczone >> %LOG% || echo ===== wylaczenie zadania NIEUDANE - komputer i tak nie liczy >> %LOG%
exit /b 0
:start
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
