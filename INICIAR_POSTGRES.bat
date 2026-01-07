@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   🚀 INICIANDO ERP JSP v3.0 COM POSTGRESQL
echo ============================================================
echo.

REM Para todos os processos Python que possam estar rodando
taskkill /F /IM python.exe 2>nul

REM Aguarda um pouco
timeout /t 2 /nobreak > nul

REM Remove banco SQLite antigo se existir
if exist erp.db (
    del /F erp.db
    echo ✅ Banco SQLite antigo removido
)

echo.
echo 📊 Verificando PostgreSQL...
echo DATABASE_URL=postgresql://postgres:postgres@localhost/erp_jsp_local
echo.

REM Inicia o servidor
python run.py

pause
