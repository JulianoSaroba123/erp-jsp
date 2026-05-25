@echo off
chcp 65001 >nul
echo.
echo ═══════════════════════════════════════════════════════════
echo  🔄 SINCRONIZAR ERP JSP COM RENDER
echo ═══════════════════════════════════════════════════════════
echo.
echo Este script vai:
echo  1. Adicionar erp.db atualizado ao Git
echo  2. Fazer commit com timestamp
echo  3. Enviar para o Render (auto-deploy)
echo.
echo ═══════════════════════════════════════════════════════════
echo.

echo 📦 Adicionando erp.db ao Git...
git add -f erp.db

echo 📝 Fazendo commit...
git commit -m "🔄 Sincroniza erp.db - %date% %time:~0,5%"

echo 🚀 Enviando para o Render...
git push origin main

echo.
echo ═══════════════════════════════════════════════════════════
echo  ✅ SINCRONIZAÇÃO CONCLUÍDA!
echo ═══════════════════════════════════════════════════════════
echo.
echo Aguarde 2-3 minutos para o Render fazer deploy
echo Depois, as novas OS aparecerão automaticamente!
echo.
pause
