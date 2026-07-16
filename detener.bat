@echo off
chcp 65001 >nul
title karuAPP - Detener Servidores

echo ========================================
echo   Deteniendo servidores karuAPP...
echo ========================================
echo.

taskkill /f /im pythonw.exe >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Servidores detenidos.
) else (
    echo [INFO] No se encontraron servidores en ejecucion.
)

echo.
pause
