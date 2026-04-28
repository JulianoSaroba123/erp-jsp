#!/usr/bin/env bash
# Build script para o Render
# Este script roda automaticamente a cada deploy

set -o errexit  # Parar se houver erro

echo "🚀 Iniciando build do ERP JSP no Render..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Aplicar migrações do banco de dados
echo "🔄 Aplicando migrações do banco de dados..."
python migrations/aplicar_todas_migracoes.py

echo "✅ Build concluído com sucesso!"
