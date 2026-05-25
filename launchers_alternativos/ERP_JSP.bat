@echo off
:: ERP JSP v3.0 - Launcher Silencioso
:: =================================

:: Iniciar diretamente sem mostrar CMD
pythonw launcher.py

:: Se falhar, tentar com python normal
if %errorlevel% neq 0 (
    python launcher.py
)