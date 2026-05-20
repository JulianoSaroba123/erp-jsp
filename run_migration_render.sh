#!/bin/bash
# Script para rodar no Render Shell e adicionar coluna kit_id no PostgreSQL

echo "🚀 MIGRAÇÃO RENDER: Adicionar coluna kit_id"
echo ""

# Rodar o script Python
python adicionar_kit_id_coluna.py

echo ""
echo "✅ Migração concluída no Render!"
echo ""
echo "📋 PRÓXIMO PASSO:"
echo "1. Verifique se o Projeto #6 agora tem kit_id"
echo "2. Acesse: https://erp-jsp-th5o.onrender.com/energia-solar/projetos/6/dashboard"
echo "3. Pressione Ctrl+F5 para limpar cache"
echo "4. Abra o modal 'Editar Orçamento'"
echo "5. Verifique no console do navegador se o kit aparece"
