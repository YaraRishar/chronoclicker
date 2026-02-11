SETLOCAL
SET "INSTALLER=%TEMP%\python-3.13.2-amd64.exe"
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force; Get-ExecutionPolicy | Out-File -Encoding ASCII %TEMP%\sep.txt"
SET /P SEPVAR=<%TEMP%\sep.txt

%LOCALAPPDATA%\Programs\Python\Python313\python.exe --version >NUL 2>&1
IF %ERRORLEVEL% EQU 0 (
    SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
) ELSE (
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe -OutFile %INSTALLER% | Out-File -Encoding ASCII %TEMP%\pydl.txt"
    SET /P PYDLVAR=<%TEMP%\pydl.txt
    IF NOT EXIST %INSTALLER% (
        PAUSE
        EXIT /B 1
    )
    START /WAIT %INSTALLER% /quiet InstallAllUsers=0 PrependPath=0 TargetDir=%LOCALAPPDATA%\Programs\Python\Python313

    IF EXIST "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        SET "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) ELSE (
        PAUSE
        EXIT /B 1
    )
    SETX PATH "%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"
)
"%PYTHON_PATH%" -V

powershell -Command "Invoke-WebRequest -Uri https://github.com/YaraRishar/chronoclicker/archive/refs/heads/main.zip -OutFile %TEMP%\chronoclicker-main.zip"
powershell Expand-Archive %TEMP%\chronoclicker-main.zip -DestinationPath C:\Users\%USERNAME%\Downloads
cd C:\Users\%USERNAME%\Downloads
REN chronoclicker-main chronoclicker
cd chronoclicker
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py