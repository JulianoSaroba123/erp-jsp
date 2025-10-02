#!/usr/bin/env python3
"""
Diagnóstico avançado para identificar o problema dos botões de edição
"""
import requests
import re

def diagnostico_avancado():
    print("=== DIAGNÓSTICO AVANÇADO DOS BOTÕES ===\n")
    
    base_url = "http://127.0.0.1:5000"
    
    # 1. Verificar a página da lista em detalhes
    print("1. ANALISANDO PÁGINA DA LISTA...")
    try:
        response = requests.get(f"{base_url}/ordens", timeout=10)
        if response.status_code == 200:
            content = response.text
            print("   ✓ Página carregada")
            
            # Extrair todos os links de edição
            edit_links = re.findall(r'href="([^"]*editar[^"]*)"', content)
            print(f"   ✓ {len(edit_links)} links de edição encontrados")
            
            # Verificar se há JavaScript que pode interferir
            if 'addEventListener' in content:
                print("   ⚠️ Event listeners encontrados")
            if 'preventDefault' in content:
                print("   ⚠️ preventDefault encontrado")
            if 'onclick' in content:
                print("   ⚠️ onclick handlers encontrados")
            
            # Verificar estrutura dos botões
            btn_groups = re.findall(r'<div class="btn-group[^>]*>.*?</div>', content, re.DOTALL)
            print(f"   ✓ {len(btn_groups)} grupos de botões encontrados")
            
            # Verificar se há overlays ou elementos que podem interceptar
            if 'modal' in content.lower():
                print("   ⚠️ Modais detectados")
            if 'overlay' in content.lower():
                print("   ⚠️ Overlays detectados")
                
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 2. Testar cada link de edição individualmente
    print("\n2. TESTANDO LINKS INDIVIDUALMENTE...")
    
    test_orders = [1, 2, 3, 4, 5]  # Testar primeiras 5 ordens
    
    for ordem_id in test_orders:
        try:
            url = f"{base_url}/ordens/{ordem_id}/editar"
            response = requests.get(url, timeout=5, allow_redirects=False)
            
            if response.status_code == 200:
                print(f"   ✓ Ordem {ordem_id}: OK (200)")
            elif response.status_code in [301, 302]:
                redirect_url = response.headers.get('Location', 'N/A')
                print(f"   ⚠️ Ordem {ordem_id}: Redirect -> {redirect_url}")
            else:
                print(f"   ❌ Ordem {ordem_id}: Erro {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ordem {ordem_id}: Erro {e}")
    
    # 3. Verificar se há problemas no template base
    print("\n3. VERIFICANDO TEMPLATE BASE...")
    try:
        # Tentar detectar problemas no HTML
        response = requests.get(f"{base_url}/ordens", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Verificar estrutura HTML
            if '<html' in content and '</html>' in content:
                print("   ✓ HTML estruturado corretamente")
            else:
                print("   ⚠️ Estrutura HTML pode estar incompleta")
            
            # Verificar CSS/JS
            if 'bootstrap' in content.lower():
                print("   ✓ Bootstrap detectado")
            if 'jquery' in content.lower():
                print("   ✓ jQuery detectado")
            
            # Procurar por possíveis interferências
            if 'form' in content and 'method="post"' in content:
                forms = re.findall(r'<form[^>]*method="post"[^>]*>', content)
                print(f"   ⚠️ {len(forms)} formulários POST encontrados")
                
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n=== CRIANDO SOLUÇÃO ALTERNATIVA ===")
    
    # Criar um JavaScript de debug que pode ser injetado
    debug_js = '''
// DEBUG: Teste dos links de edição
console.log("=== DEBUG LINKS DE EDIÇÃO ===");

// Encontrar todos os links de edição
const editLinks = document.querySelectorAll('a[href*="editar"]');
console.log("Links de edição encontrados:", editLinks.length);

// Verificar se estão visíveis e clicáveis
editLinks.forEach((link, index) => {
    console.log(`Link ${index + 1}:`, {
        href: link.href,
        visible: link.offsetWidth > 0 && link.offsetHeight > 0,
        style: window.getComputedStyle(link).pointerEvents,
        hasListeners: link.onclick !== null
    });
});

// Testar clique programático no primeiro link
if (editLinks.length > 0) {
    console.log("Testando clique programático...");
    editLinks[0].click();
}
'''
    
    print("\n💡 JAVASCRIPT DE DEBUG CRIADO")
    print("Cole este código no Console do navegador (F12):")
    print("-" * 50)
    print(debug_js)
    print("-" * 50)
    
    print("\n🔧 POSSÍVEIS SOLUÇÕES:")
    print("1. Verificar se há event.preventDefault() interceptando")
    print("2. Verificar CSS pointer-events")
    print("3. Verificar se há overlays invisíveis")
    print("4. Testar em modo incógnito")
    print("5. Verificar console do navegador para erros")

if __name__ == "__main__":
    diagnostico_avancado()