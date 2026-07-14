@echo off
chcp 65001 >nul
title Pipperfood POS - Servidor
cd /d "%~dp0backend"
echo ============================================
echo    Pipperfood POS - Iniciando...
echo ============================================
echo.
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual.
    echo         Ejecute primero instalar-nativo.bat
    pause
    exit /b 1
)
call venv\Scripts\activate
echo [OK] Entorno virtual activado.
echo.
echo Abriendo http://localhost:8000 ...
start http://localhost:8000
python socket_server.py
pause
