@echo off
SETLOCAL

set "CLICKER_PATH=C:\Users\%USERNAME%\Downloads"

ECHO "Kirillica ne rabotaet, no vy derzhites("
ECHO "Kuda ustanovit kliker? Nazhmite Enter, esli vy hotite ustanovit v C:\Users\%USERNAME%\Downloads, libo vvedite drugoj put: "
SET /P CLICKER_PATH=""

SET "INSTALLER=%TEMP%\python-3.13.2-amd64.exe"
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; Get-ExecutionPolicy | Out-File -Encoding ASCII %TEMP%\sep.txt"
SET /P SEPVAR=<%TEMP%\sep.txt

%LOCALAPPDATA%\Programs\Python\Python313\python.exe --version >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
    ECHO "Python uzhe ustanovlen, teper ustanavlivaem kliker..."
    SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) ELSE (
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe -OutFile %INSTALLER% | Out-File -Encoding ASCII %TEMP%\pydl.txt"
    SET /P PYDLVAR=<%TEMP%\pydl.txt
    IF NOT EXIST %INSTALLER% (
        ECHO "Ne udalos skachat ustanovshik. Proverte, est li u vas internet. V krajnem sluchae, skachajte i ustanovite Python s zaneseniem v PATH samostoyatelno otsyuda: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    START /WAIT %INSTALLER% /quiet InstallAllUsers=0 PrependPath=0 TargetDir=%LOCALAPPDATA%\Programs\Python\Python313

    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) ELSE (
        ECHO "Ne udalos skachat ustanovshik. Proverte, est li u vas internet. V krajnem sluchae, skachajte i ustanovite Python s zaneseniem v PATH samostoyatelno otsyuda: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    SETX PATH "%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
)
"%PYTHON_PATH%" -V

powershell -Command "Invoke-WebRequest -Uri https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip -OutFile %TEMP%\chronoclicker-main.zip"
IF EXIST "%TEMP%\chronoclicker-main.zip" (
    ECHO "Kliker skachan s https://github.com/YaraRishar/chronoclicker"
) ELSE (
    ECHO "Ne udalos skachat kliker. Proverte, est li u vas internet. V krajnem sluchae, skachajte kliker samostoyatelno i polozhite arhiv v %TEMP%, kliker nahoditsya po ssylke: https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip"
    PAUSE
    EXIT /B 1
)

powershell Expand-Archive %TEMP%\chronoclicker-main.zip -DestinationPath %CLICKER_PATH%
ECHO "Kliker razarhivirovan v %CLICKER_PATH%..."
cd %CLICKER_PATH%
REN chronoclicker-main chronoclicker
cd chronoclicker
python -m venv .venv
ECHO "Sozdano okruzhenie Python (.venv) v %CLICKER_PATH%\chronoclicker"
call .venv\Scripts\activate.bat
ECHO "Okruzhenie Python (.venv) aktivirovano..."
call python -m pip install -r requirements.txt
ECHO "Kliker uspeshno ustanovlen! Chtoby ego zapustit, perejdite v %CLICKER_PATH%\chronoclicker i zapustite chronoclicker.bat"
ECHO "Nash chat v TG: https://t.me/+EEOrtd6QvVIzNWZi (nu ili naberite v poiske: chronoclicker | chit dlya catwar)"
ECHO "Gajd po komandam i otvety na chasto zadavaemye voprosy: https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker"
PAUSE
