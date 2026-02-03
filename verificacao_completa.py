# -*- coding: utf-8 -*-
"""
Verificação completa do deploy
"""
import requests
import time
import json

BASE_URL = "https://erp-jsp-th5o.onrender.com"

print("\n" + "="*60)
print("🔍 VERIFICAÇÃO COMPLETA DO DEPLOY")
print("="*60 + "\n")
print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. Endpoint de debug
print("1️⃣ Testando endpoint de debug:")
print(f"   {BASE_URL}/debug/cliente/20")
try:
    r = requests.get(f"{BASE_URL}/debug/cliente/20", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Query funciona: {data.get('teste_query')}")
        print(f"   Cliente encontrado: {data.get('cliente_encontrado')}")
        print(f"   Mensagem: {data.get('mensagem', 'N/A')}")
    else:
        print(f"   ❌ Erro: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Exceção: {e}")

print()

# 2. Endpoint de diagnóstico
print("2️⃣ Testando endpoint de diagnóstico:")
print(f"   {BASE_URL}/diagnostico/status")
try:
    r = requests.get(f"{BASE_URL}/diagnostico/status", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Correção aplicada: {data.get('correcao_404_aplicada')}")
        print(f"   Última atualização: {data.get('ultima_atualizacao_routes')}")
        print(f"   Mensagem: {data.get('mensagem')}")
    else:
        print(f"   ❌ Erro: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Exceção: {e}")

print()

# 3. Rota real do cliente 20
print("3️⃣ Testando rota real /cliente/20:")
print(f"   {BASE_URL}/cliente/20")
try:
    r = requests.get(f"{BASE_URL}/cliente/20", timeout=10, allow_redirects=False)
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 302:
        print(f"   ✅ REDIRECIONAMENTO! → {r.headers.get('Location')}")
        print("\n   🎉 PROBLEMA RESOLVIDO!")
    elif r.status_code == 500:
        print(f"   ❌ Ainda com erro 500")
        print(f"   HTML retornado: {r.text[:300]}")
    else:
        print(f"   ⚠️ Status inesperado: {r.status_code}")
        
except Exception as e:
    print(f"   ❌ Exceção: {e}")

print("\n" + "="*60)
print("📊 RESULTADO FINAL")
print("="*60 + "\n")

# Teste final
try:
    r = requests.get(f"{BASE_URL}/cliente/20", timeout=10, allow_redirects=False)
    if r.status_code == 302:
        print("✅ SUCESSO! O erro foi corrigido!")
        print(f"   A rota /cliente/20 agora redireciona corretamente.\n")
    else:
        print(f"⚠️ Status: {r.status_code}")
        print("   O deploy pode ainda não ter sido aplicado.")
        print("   Aguarde mais 1-2 minutos e execute este script novamente.\n")
except Exception as e:
    print(f"❌ Erro na conexão: {e}\n")
