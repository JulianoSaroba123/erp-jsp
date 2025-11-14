@echo off
title ERP JSP - Sistema de Gestão v3.0
color 0B
cls

echo ████████████████████████████████████████████████████████████████
echo ██                                                            ██
echo ██               ⚡ ERP JSP Sistema v3.0 ⚡                 ██
echo ██          Automação Industrial ^& Solar                     ██
echo ██                                                            ██
echo ████████████████████████████████████████████████████████████████
echo.
echo 🚀 Iniciando sistema...
echo.

:: Verificar se está na pasta correta
if not exist "app" (
    echo ❌ ERRO: Pasta 'app' não encontrada!
    echo    Certifique-se de que este arquivo está na pasta do ERP JSP.
    echo.
    pause
    exit /b 1
)

if not exist "run.py" (
    echo ❌ ERRO: Arquivo 'run.py' não encontrado!
    echo    Certifique-se de que este arquivo está na pasta do ERP JSP.
    echo.
    pause
    exit /b 1
)

:: Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERRO: Python não encontrado!
    echo    Instale o Python 3.8+ em: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Verificações OK
echo.
echo 🌐 Iniciando servidor Flask...
echo ⏳ Aguarde... (pode demorar alguns segundos na primeira vez)
echo.
echo 🔗 O navegador abrirá automaticamente
echo 📱 URL: http://127.0.0.1:5001
echo.
echo ⚠️  IMPORTANTE: Mantenha esta janela aberta!
echo    Para parar o sistema, feche esta janela ou pressione Ctrl+C
echo.

:: Aguardar 2 segundos e abrir navegador
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5001/auth/login

:: Executar o sistema
python run.py

echo.
echo 🔚 Sistema encerrado.
echo.
pause