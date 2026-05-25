@echo off
:: ERP JSP v3.0 - Launcher Profissional
:: ===================================
:: 
:: Este launcher inicia o sistema ERP JSP com interface profissional
:: sem mostrar janelas de comando durante a execução.
::
:: Autor: JSP Soluções
:: Data: 2025

title ERP JSP v3.0 - Iniciando...

:: Verificar se Python está disponível
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python não encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    echo.
    pause
    exit /b 1
)

:: Navegar para a pasta do script
cd /d "%~dp0"

:: Verificar se está na pasta correta
if not exist "app" (
    echo.
    echo ❌ Pasta 'app' não encontrada!
    echo Certifique-se de que está executando na pasta correta do ERP JSP.
    echo.
    pause
    exit /b 1
)

:: Verificar se o launcher existe
if not exist "launcher.py" (
    echo.
    echo ❌ Arquivo launcher.py não encontrado!
    echo O sistema precisa do arquivo launcher.py para funcionar.
    echo.
    pause
    exit /b 1
)

:: Limpar tela e iniciar launcher profissional
cls

:: Encerrar possíveis processos Python órfãos na porta 5001
echo Verificando processos anteriores...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo 🚀 Iniciando ERP JSP v3.0...
echo.
echo Interface profissional será exibida em instantes.
echo.

:: Iniciar launcher Python (interface gráfica) sem mostrar CMD
pythonw launcher.py

:: Se pythonw não funcionar, tentar python normal
if %errorlevel% neq 0 (
    python launcher.py
)

:: Se chegou aqui, o launcher foi encerrado
echo.
echo Sistema ERP JSP encerrado.
timeout /t 2 /nobreak >nul