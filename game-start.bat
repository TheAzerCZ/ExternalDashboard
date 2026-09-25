@echo off
rem Spoustec pro Steam: parametry spusteni ETS2 ->  "C:\cesta\k\ets2-dash\game-start.bat" %command%
cd /d "%~dp0"

rem Dashboard pustime jen jednou (kdyz uz na portu 8088 bezi, novy nespoustime ani neotvirame prohlizec)
netstat -ano | findstr /r /c:"127\.0\.0\.1:8088 .*LISTENING" >nul
if errorlevel 1 (
    rem pythonw = Python bez okna; kdyz neni k dispozici, pouzije se python v minimalizovanem okne
    where pythonw >nul 2>nul
    if errorlevel 1 (
        start "ETS2 Dashboard" /min python dash.py --exit-with-game
    ) else (
        start "" pythonw dash.py --exit-with-game
    )
    rem chvili pockame, nez server nabehne, a otevreme dashboard v prohlizeci
    timeout /t 2 /nobreak >nul
    start "" http://127.0.0.1:8088
)

rem Spusti samotnou hru (Steam sem dosadi %command%)
start "" %*
