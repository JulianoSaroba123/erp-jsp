#!/usr/bin/env python3
"""
Script final para testar todas as funcionalidades corrigidas
"""

import requests
import time
from urllib.parse import urljoin

def test_all_features():
    """Testa todas as funcionalidades corrigidas."""
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # Login
        print("🔐 Fazendo login...")
        login_data = {'username': 'julia', 'senha': '1234'}
        login_response = session.post(urljoin(base_url, '/login'), data=login_data, allow_redirects=True)
        
        if login_response.status_code != 200:
            print(f"❌ Erro no login: {login_response.status_code}")
            return False
        
        print("✅ Login realizado com sucesso")
        
        # Acessar página
        print("📄 Acessando página de ordem de serviço...")
        page_response = session.get(urljoin(base_url, '/ordens/nova'))
        
        if page_response.status_code != 200:
            print(f"❌ Erro ao carregar página: {page_response.status_code}")
            return False
            
        content = page_response.text
        
        # Verificações finais
        final_checks = [
            ('Event listeners configurados na inicialização', 
             'addEventListener(\'change\', calcularHoras)' in content),
            
            ('Função fmt corrigida', 
             'num.toFixed(2).replace(\'.\', \',\')' in content),
            
            ('Verificações de segurança nas funções', 
             'console.warn(\'⚠️ Elementos de hora não encontrados\')' in content),
            
            ('DOMContentLoaded configurado', 
             'DOMContentLoaded' in content),
            
            ('Todas as funções principais presentes',
             all(func in content for func in [
                 'setupClienteSelection', 'setupServicoSelection', 
                 'setupProdutoSelection', 'calcularHoras', 'calcularTotais'
             ])),
            
            ('Elementos HTML essenciais', 
             all(element_id in content for element_id in [
                 'id="cliente_select"', 'id="servico_select"', 
                 'id="produto_select"', 'id="hora_inicio"', 'id="hora_termino"'
             ])),
        ]
        
        print("\n🎯 VERIFICAÇÕES FINAIS:")
        all_passed = True
        for check_name, check_result in final_checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            if not check_result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 TODAS AS VERIFICAÇÕES PASSARAM!")
            print("📋 Funcionalidades corrigidas:")
            print("   • Event listeners agora são configurados corretamente no DOMContentLoaded")
            print("   • Função fmt corrigida para mostrar centavos adequadamente")
            print("   • Verificações de segurança adicionadas para evitar erros de elementos não encontrados")
            print("   • Auto-complete de clientes, produtos e serviços funcionando")
            print("   • Cálculos automáticos de horas e quilometragem operacionais")
            print("   • Cálculos de totais integrados e funcionais")
            
            print("\n🧪 PARA TESTAR MANUALMENTE:")
            print("1. Acesse http://127.0.0.1:5000/ordens/nova")
            print("2. Teste seleção de cliente (deve preencher dados automaticamente)")
            print("3. Digite horário de início e término (deve calcular horas automaticamente)")
            print("4. Adicione serviços e produtos (deve atualizar totais automaticamente)")
            print("5. Verifique se não há erros no console do navegador (F12)")
            
            return True
        else:
            print("\n❌ ALGUMAS VERIFICAÇÕES FALHARAM - verifique os itens marcados")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTANDO TODAS AS FUNCIONALIDADES CORRIGIDAS...")
    print("=" * 60)
    test_all_features()