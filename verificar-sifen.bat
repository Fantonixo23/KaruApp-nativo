@echo off
chcp 65001 >nul
title karuAPP - Verificar SIFEN
setlocal enabledelayedexpansion
echo ============================================================
echo    karuAPP - Diagnostico de Facturacion Electronica SIFEN
echo ============================================================
echo.

set ERRORES=0

:: --- 1. Node.js instalado ---
echo [1/5] Node.js ...
where node >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%v in ('node --version') do set NODE_VERSION=%%v
    echo        [OK] Node.js !NODE_VERSION!
) else (
    echo        [ERROR] Node.js NO instalado. Descargalo de https://nodejs.org/
    set /a ERRORES+=1
)

:: --- 2. Dependencias del sifen-service ---
echo.
echo [2/5] Dependencias del sifen-service ...
if exist "%~dp0sifen-service\server.js" (
    echo        [OK] sifen-service\server.js encontrado.
) else (
    echo        [ERROR] No se encontro "sifen-service\server.js".
    echo               Asegurate de copiar la carpeta completa del proyecto.
    set /a ERRORES+=1
)
if exist "%~dp0sifen-service\node_modules" (
    echo        [OK] Dependencias npm instaladas.
) else (
    echo        [ERROR] Falta node_modules. Ejecuta "instalar-nativo.bat" o
    echo               dentro de sifen-service: npm install
    set /a ERRORES+=1
)

:: --- 3. Archivo .env del sifen-service ---
echo.
echo [3/5] Configuracion del sifen-service ...
if exist "%~dp0sifen-service\.env" (
    echo        [OK] Archivo .env presente.
    findstr /i "MOCK=true" "%~dp0sifen-service\.env" >nul 2>&1
    if !errorlevel! equ 0 (
        echo        [OK] Modo SIMULACION MOCK=true activo.
    ) else (
        echo        [INFO] MOCK no esta en true, o se usa modo produccion real.
    )
) else (
    echo        [ERROR] Falta sifen-service\.env. Copiarlo desde .env.example.
    set /a ERRORES+=1
)

:: --- 4. sifen-service respondiendo ---
echo.
echo [4/5] sifen-service en http://127.0.0.1:4000 ...
set PUERTO_ABIERTO=
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":4000" ^| findstr "LISTENING"') do set PUERTO_ABIERTO=%%p
if defined PUERTO_ABIERTO (
    echo        [OK] Puerto 4000 escuchando - proceso PID !PUERTO_ABIERTO!.
) else (
    echo        [ERROR] El sifen-service NO esta corriendo.
    echo               Arrancalo con iniciar.bat o iniciar-silencioso.vbs.
    set /a ERRORES+=1
)

:: --- 5. Endpoint de estado de Django ---
echo.
echo [5/5] Endpoint /api/sifen/status (Django) ...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/sifen/status' -UseBasicParsing -TimeoutSec 5; Write-Output ('HTTP ' + $r.StatusCode); $r.Content } catch { Write-Output ('FALLO: ' + $_.Exception.Message) }"
echo.

echo ============================================================
if %ERRORES% equ 0 (
    echo    RESUMEN: Todo OK. SIFEN listo para usarse.
) else (
    echo    RESUMEN: Se encontraron %ERRORES% problema/s de configuracion.
    echo            Revisa los mensajes [ERROR] de arriba.
)
echo ============================================================
echo.
echo  Sugerencia: el sifen-service debe estar corriendo (iniciar.bat
echo  abre las 3 ventanas: Django, Print y SIFEN) para poder facturar.
echo.
pause
