#!/usr/bin/env python3
"""
Script para forçar atualização do cache do navegador
"""

print("=== SOLUÇÃO PARA CACHE DO NAVEGADOR ===\n")

print("O template foi atualizado no servidor, mas seu navegador está")
print("mostrando a versão antiga por causa do cache.\n")

print("🔧 SOLUÇÕES (teste nesta ordem):\n")

print("1. HARD REFRESH:")
print("   - Pressione Ctrl + F5")
print("   - Ou Ctrl + Shift + R")
print("   - Isso força recarregamento sem cache\n")

print("2. LIMPAR CACHE:")
print("   - Pressione F12 (abrir DevTools)")
print("   - Clique com botão direito no botão de atualizar")
print("   - Escolha 'Esvaziar cache e recarregar forçadamente'\n")

print("3. MODO INCÓGNITO:")
print("   - Pressione Ctrl + Shift + N")
print("   - Acesse: http://localhost:5000/ordens")
print("   - No modo incógnito não há cache\n")

print("4. DESABILITAR CACHE (TEMPORÁRIO):")
print("   - Abra F12 (DevTools)")
print("   - Vá na aba Network")
print("   - Marque 'Disable cache'")
print("   - Recarregue a página\n")

print("5. SE NADA FUNCIONAR:")
print("   - Feche completamente o navegador")
print("   - Abra novamente e acesse a página")
print("   - Ou teste em outro navegador\n")

print("📋 TESTE DOS BOTÕES:")
print("Depois de limpar o cache, os botões devem estar:")
print("- SEM bordas azuis (era <a href>)")
print("- COM aparência de botões normais")
print("- Clicáveis e funcionais\n")

print("💡 CONFIRMAÇÃO:")
print("Se mesmo assim não funcionar, abra F12 -> Console")
print("e digite: document.querySelectorAll('button[onclick]')")
print("Deve mostrar os botões onclick em vez de links <a>")

if __name__ == "__main__":
    pass