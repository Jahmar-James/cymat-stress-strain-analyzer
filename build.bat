@echo off
IF NOT EXIST "venv" (
    echo Creating a virtual environment...
    python -m venv venv
) ELSE (
    echo Virtual environment already exists, skipping creation...
)

echo Activating the virtual environment...
call venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Creating an executable version of the stress_strain_app...
pyinstaller --onefile stress_strain_app.py
echo Executable created successfully!
pause
