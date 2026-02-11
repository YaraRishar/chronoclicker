@echo off
SETLOCAL

setlocal EnableDelayedExpansion

for /f "tokens=2" %%a in ('chcp') do set "OLDCP=%%a"
chcp 65001 >nul 2>&1
if errorlevel 1 (
    chcp 1251 >nul 2>&1
)

:echo_cyr
powershell -Command "& {[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); [Console]::WriteLine('%~1')}" 2>nul
exit /b

set "CLICKER_PATH=C:\Users\%USERNAME%\Downloads"

call :echo_cyr "Куда установить кликер? Нажмите Enter, если вы хотите установить в C:\Users\%USERNAME%\Downloads, либо введите другой путь: "
SET /P CLICKER_PATH=""

SET "INSTALLER=%TEMP%\python-3.13.2-amd64.exe"
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; Get-ExecutionPolicy | Out-File -Encoding ASCII %TEMP%\sep.txt"
SET /P SEPVAR=<%TEMP%\sep.txt

%LOCALAPPDATA%\Programs\Python\Python313\python.exe --version >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
    call :echo_cyr "Python уже установлен, теперь устанавливаем кликер..."
    SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) ELSE (
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe -OutFile %INSTALLER% | Out-File -Encoding ASCII %TEMP%\pydl.txt"
    SET /P PYDLVAR=<%TEMP%\pydl.txt
    IF NOT EXIST %INSTALLER% (
        call :echo_cyr "Не удалось скачать установщик. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте и установите Python с занесением в PATH самостоятельно отсюда: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    START /WAIT %INSTALLER% /quiet InstallAllUsers=0 PrependPath=0 TargetDir=%LOCALAPPDATA%\Programs\Python\Python313

    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) ELSE (
        call :echo_cyr "Не удалось скачать установщик. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте и установите Python с занесением в PATH самостоятельно отсюда: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    SETX PATH "%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
)
"%PYTHON_PATH%" -V

powershell -Command "Invoke-WebRequest -Uri https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip -OutFile %TEMP%\chronoclicker-main.zip"
IF EXIST "%TEMP%\chronoclicker-main.zip" (
    call :echo_cyr "Кликер скачан с https://github.com/YaraRishar/chronoclicker"
) ELSE (
    call :echo_cyr "Не удалось скачать кликер. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте кликер самостоятельно и положите архив в %TEMP%, кликер находится по ссылке: https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip"
    PAUSE
    EXIT /B 1
)

powershell Expand-Archive %TEMP%\chronoclicker-main.zip -DestinationPath %CLICKER_PATH%
call :echo_cyr "Кликер разархивирован в %CLICKER_PATH%..."
cd %CLICKER_PATH%
REN chronoclicker-main chronoclicker
cd chronoclicker
python -m venv .venv
call :echo_cyr "Создано окружение Python (.venv) в %CLICKER_PATH%\chronoclicker"
call .venv\Scripts\activate.bat
call :echo_cyr "Окружение Python (.venv) активировано..."
call python -m pip install -r requirements.txt
call :echo_cyr "Кликер успешно установлен! Чтобы его запустить, перейдите в %CLICKER_PATH%\chronoclicker и запустите chronoclicker.bat"
call :echo_cyr "Наш чат в ТГ: https://t.me/+EEOrtd6QvVIzNWZi (ну или наберите в поиске: chronoclicker | чит для catwar)"
call :echo_cyr "Гайд по командам и ответы на часто задаваемые вопросы: https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker"
PAUSE
