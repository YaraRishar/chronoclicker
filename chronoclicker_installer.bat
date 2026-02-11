@echo off
SETLOCAL

set "CLICKER_PATH=C:\Users\%USERNAME%\Downloads"
SET /P CLICKER_PATH="Куда установить кликер? Нажмите Enter, если вы хотите установить в C:\Users\%USERNAME%\Downloads, либо введите другой путь: "

SET "INSTALLER=%TEMP%\python-3.13.2-amd64.exe"
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; Get-ExecutionPolicy | Out-File -Encoding ASCII %TEMP%\sep.txt"
SET /P SEPVAR=<%TEMP%\sep.txt

%LOCALAPPDATA%\Programs\Python\Python313\python.exe --version >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
    ECHO "Python уже установлен, теперь устанавливаем кликер..."
    SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) ELSE (
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe -OutFile %INSTALLER% | Out-File -Encoding ASCII %TEMP%\pydl.txt"
    SET /P PYDLVAR=<%TEMP%\pydl.txt
    IF NOT EXIST %INSTALLER% (
        ECHO "Не удалось скачать установщик. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте и установите Python с занесением в PATH самостоятельно отсюда: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    START /WAIT %INSTALLER% /quiet InstallAllUsers=0 PrependPath=0 TargetDir=%LOCALAPPDATA%\Programs\Python\Python313

    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) ELSE (
        ECHO "Не удалось скачать установщик. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте и установите Python с занесением в PATH самостоятельно отсюда: https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
        PAUSE
        EXIT /B 1
    )
    SETX PATH "%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
)
"%PYTHON_PATH%" -V

powershell -Command "Invoke-WebRequest -Uri https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip -OutFile %TEMP%\chronoclicker-main.zip"
IF EXIST "%TEMP%\chronoclicker-main.zip" (
    ECHO "Кликер скачан с https://github.com/YaraRishar/chronoclicker"
) ELSE (
    ECHO "Не удалось скачать кликер. Проверьте, есть ли у вас интернет. В крайнем случае, скачайте кликер самостоятельно и положите архив в %TEMP%, кликер находится по ссылке: https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip"
    PAUSE
    EXIT /B 1
)

powershell Expand-Archive %TEMP%\chronoclicker-main.zip -DestinationPath %CLICKER_PATH%
ECHO "Кликер разархивирован в %CLICKER_PATH%..."
cd %CLICKER_PATH%
REN chronoclicker-main chronoclicker
cd chronoclicker
python -m venv .venv
ECHO "Создано окружение Python (.venv) в %CLICKER_PATH%\chronoclicker"
call .venv\Scripts\activate.bat
ECHO "Окружение Python (.venv) активировано..."
call python -m pip install -r requirements.txt
ECHO "Кликер успешно установлен! Чтобы его запустить, перейдите в %CLICKER_PATH%\chronoclicker и запустите chronoclicker.bat"
ECHO "Наш чат в ТГ: https://t.me/+EEOrtd6QvVIzNWZi (ну или наберите в поиске: chronoclicker | чит для catwar)"
ECHO "Гайд по командам и ответы на часто задаваемые вопросы: https://github.com/YaraRishar/chronoclicker?tab=readme-ov-file#chronoclicker"
PAUSE