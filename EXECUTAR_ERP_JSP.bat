@echo off
title ERP JSP Sistema v3.0
echo 🚀 Iniciando ERP JSP Sistema...
echo.
echo ⚡ Carregando módulos Python...
cd /d "%~dp0"
if not exist "app" (
    echo ❌ ERRO: Pasta 'app' não encontrada!
    echo Certifique-se de que o executável está na pasta correta.
    pause
    exit /b 1
)

echo ✅ Estrutura verificada
echo 🌐 Iniciando servidor web...
echo.
echo ⏳ Por favor aguarde...
timeout /t 2 /nobreak >nul

start "" "http://127.0.0.1:5001/auth/login"
python run.py

echo.
echo 🔚 Sistema encerrado.
pause