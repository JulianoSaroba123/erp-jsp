#!/usr/bin/env python3
"""
Teste que injeta JavaScript para simular seleção de cliente
"""

import requests
from urllib.parse import urljoin
import json

def test_client_selection():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # Login
    login_data = {'username': 'julia', 'senha': '1234'}
    login_response = session.post(urljoin(base_url, '/login'), data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        return
    
    # Acessar página
    page_response = session.get(urljoin(base_url, '/ordens/nova'))
    
    if page_response.status_code != 200:
        print(f"❌ Erro ao carregar página: {page_response.status_code}")
        return
    
    content = page_response.text
    
    print("🧪 CRIANDO TESTE DE SELEÇÃO DE CLIENTE...")
    
    # Criar JavaScript para testar
    test_js = '''
// Teste completo de seleção de cliente
console.log("🧪 INICIANDO TESTE DE SELEÇÃO DE CLIENTE");

// Aguardar 2 segundos para garantir que tudo carregou
setTimeout(function() {
    console.log("⏰ Executando teste após delay...");
    
    const selectCliente = document.getElementById('cliente_select');
    const clienteId = document.getElementById('cliente_id');
    
    if (!selectCliente) {
        console.error("❌ Select de cliente não encontrado!");
        return;
    }
    
    if (!clienteId) {
        console.error("❌ Campo cliente_id não encontrado!");
        return;
    }
    
    console.log("📊 Estado inicial:");
    console.log(`   Select: ${selectCliente.options.length} opções`);
    console.log(`   Cliente ID atual: "${clienteId.value}"`);
    
    if (selectCliente.options.length > 1) {
        console.log("🎯 Selecionando primeiro cliente...");
        
        // Selecionar primeira opção real (não "Selecione...")
        selectCliente.selectedIndex = 1;
        
        console.log("🔥 Disparando evento change...");
        
        // Criar e disparar evento
        const event = new Event('change', { bubbles: true, cancelable: true });
        const resultado = selectCliente.dispatchEvent(event);
        
        console.log(`📡 Evento disparado: ${resultado}`);
        
        // Aguardar um pouco e verificar resultado
        setTimeout(function() {
            console.log("📊 Estado após seleção:");
            console.log(`   Select selectedIndex: ${selectCliente.selectedIndex}`);
            console.log(`   Select value: "${selectCliente.value}"`);
            console.log(`   Cliente ID: "${clienteId.value}"`);
            
            // Verificar se dados foram preenchidos
            const campos = ['cpf', 'telefone', 'email', 'endereco'];
            console.log("📋 Dados preenchidos:");
            campos.forEach(campo => {
                const el = document.getElementById(campo);
                if (el) {
                    console.log(`   ${campo}: "${el.value}"`);
                } else {
                    console.log(`   ${campo}: CAMPO NÃO ENCONTRADO`);
                }
            });
            
            if (clienteId.value) {
                console.log("✅ TESTE PASSOU - Cliente selecionado com sucesso!");
            } else {
                console.log("❌ TESTE FALHOU - Cliente ID não foi preenchido");
            }
        }, 1000);
        
    } else {
        console.error("❌ Nenhuma opção de cliente disponível!");
    }
    
}, 2000);
'''
    
    print("📝 Código JavaScript gerado para teste manual:")
    print("=" * 60)
    print("Cole este código no console do navegador (F12):")
    print("=" * 60)
    print(test_js)
    print("=" * 60)
    
    print("\n📋 INSTRUÇÕES:")
    print("1. Abra http://127.0.0.1:5000/ordens/nova")
    print("2. Pressione F12 para abrir o console")
    print("3. Cole e execute o código JavaScript acima")
    print("4. Observe os logs para identificar o problema")

if __name__ == "__main__":
    test_client_selection()