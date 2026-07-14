@echo off
cd /d "%~dp0"
chcp 65001 >nul
title Pipperfood - Instalar AutoInicio

echo ============================================
echo    Pipperfood POS - AutoInicio en Windows
echo ============================================
echo.
echo Este script agrega Pipperfood al inicio de Windows.
echo Se ejecutara automaticamente cuando inicies sesion.
echo.
echo Instalando...

set "origen=%CD%\iniciar.bat"
set "destino=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Pipperfood-Iniciar.bat"

copy "%origen%" "%destino%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo instalar el autoinicio.
    echo         Intentá ejecutar como Administrador.
    pause
    exit /b 1
)

echo.
echo ============================================
echo    LISTO!
echo ============================================
echo.
echo  Pipperfood se iniciara automaticamente
echo  al iniciar sesion en Windows.
echo.
echo  Para desinstalar el autoinicio:
echo    Elimina el archivo:
echo    %destino%
echo.
pause
