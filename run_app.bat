@echo off
setlocal
pushd "%~dp0"

:: Ensure venv exists
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    py -m venv .venv || goto :error
)

:: Activate venv
call .venv\Scripts\activate || goto :error

:: Install dependencies
pip install -r requirements.txt || goto :error

echo Starting web server on http://localhost:5000 ...
python web_app.py
goto :eof

:error
echo Failed. See messages above.
exit /b 1
