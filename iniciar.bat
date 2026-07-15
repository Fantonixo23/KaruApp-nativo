@echo off
chcp 65001 >nul
title Pipperfood POS - Servidores
cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual.
    echo         Ejecute primero instalar-nativo.bat
    pause
    exit /b 1
)

call venv\Scripts\activate

if not exist "print_service\certs\qz-private-key.pem" (
    echo [*] Generando certificados para QZ Tray...
    python generar_certificados_qz.py
)

echo ============================================
echo    Iniciando servidores...
echo ============================================
echo   Django:  http://localhost:8000
echo   Print:   http://localhost:5123
echo.

start "Pipperfood - Django" /D "%~dp0backend" cmd /k "venv\Scripts\activate && python socket_server.py"
start "Pipperfood - Print"  /D "%~dp0backend" cmd /k "venv\Scripts\activate && python print_service\print_server.py"

timeout /t 3 >nul
start http://localhost:8000

echo [OK] Servidores iniciados en ventanas separadas.
pause
