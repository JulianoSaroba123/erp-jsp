#!/usr/bin/env python3
"""
Diagnóstico específico para o problema dos botões
"""
import requests
import time
import re

def diagnostico_especifico():
    print("=== DIAGNÓSTICO ESPECÍFICO DOS BOTÕES ===\n")
    
    time.sleep(2)  # Aguardar servidor
    
    try:
        url = "http://127.0.0.1:5000/ordens"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            print("1. VERIFICANDO ESTRUTURA DA PÁGINA:")
            
            # Verificar se há sobreposições de event listeners
            if 'addEventListener' in content:
                listeners = content.count('addEventListener')
                print(f"   Event listeners encontrados: {listeners}")
                
            # Verificar Bootstrap/jQuery
            if 'bootstrap' in content.lower():
                print("   Bootstrap detectado")
            if 'jquery' in content.lower():
                print("   jQuery detectado")
                
            # Verificar se há conflitos com table-hover
            if 'table-hover' in content:
                print("   ⚠️ table-hover encontrado (pode interferir)")
                
            print("\n2. VERIFICANDO BOTÕES:")
            
            # Extrair botões específicos
            button_pattern = r'<button[^>]*onclick="navegarPara\([^)]+\)"[^>]*>'
            buttons = re.findall(button_pattern, content)
            print(f"   Botões navegarPara encontrados: {len(buttons)}")
            
            if buttons:
                print("   Primeiro botão:", buttons[0][:100] + "...")
                
            # Verificar se há problemas com quotes
            if "navegarPara('" in content and "navegarPara(\"" in content:
                print("   ⚠️ Mistura de quotes detectada")
                
            print("\n3. VERIFICANDO JAVASCRIPT:")
            
            # Verificar se as funções estão definidas
            if 'window.navegarPara = function' in content:
                print("   ✓ Função navegarPara definida")
            else:
                print("   ❌ Função navegarPara NÃO definida")
                
            if 'window.abrirPDF = function' in content:
                print("   ✓ Função abrirPDF definida")
            else:
                print("   ❌ Função abrirPDF NÃO definida")
                
            print("\n4. POSSÍVEIS INTERFERÊNCIAS:")
            
            # Verificar se há eventos em elementos pais
            if 'tr>' in content and ('onclick' in content or 'addEventListener' in content):
                print("   ⚠️ Possível interferência de eventos em TR")
                
            # Verificar se há overlays
            if any(word in content.lower() for word in ['modal', 'overlay', 'backdrop']):
                print("   ⚠️ Modais/overlays detectados")
                
            print(f"\n5. TAMANHO DA RESPOSTA: {len(content)} bytes")
            
        else:
            print(f"Erro ao acessar página: {response.status_code}")
            
    except Exception as e:
        print(f"Erro: {e}")

    print(f"\n=== TESTE MANUAL RECOMENDADO ===")
    print("1. Abra F12 -> Console")
    print("2. Digite: window.navegarPara")
    print("3. Deve mostrar: function(url) { ... }")
    print("4. Digite: navegarPara('/ordens/2/editar')")
    print("5. Deve navegar para edição")
    print("\nSe não funcionar, há conflito de JavaScript!")

if __name__ == "__main__":
    diagnostico_especifico()