import requests

try:
    r = requests.get('http://127.0.0.1:5001/propostas/nova')
    print('✅ Status:', r.status_code)
    
    conteudo = r.text
    
    # Testa elementos básicos
    print('🔲 Botão Produto presente:', 'onclick="adicionarProduto()"' in conteudo)
    print('🔧 Botão Serviço presente:', 'onclick="adicionarServico()"' in conteudo)
    
    # Testa funções de cálculo
    print('🧮 Função calcularTotalProduto:', 'function calcularTotalProduto(' in conteudo)
    print('🧮 Função calcularTotalServico:', 'function calcularTotalServico(' in conteudo)
    print('💰 Função calcularTotaisGerais:', 'function calcularTotaisGerais(' in conteudo)
    print('💱 Função parseMoney:', 'function parseMoney(' in conteudo)
    print('💲 Função formatMoney:', 'function formatMoney(' in conteudo)
    print('🎭 Função aplicarMascaraMonetaria:', 'function aplicarMascaraMonetaria(' in conteudo)
    
    # Testa event listeners
    print('👂 Event listeners produtos:', 'addEventListener' in conteudo and 'calcularTotalProduto' in conteudo)
    print('👂 Event listeners serviços:', 'addEventListener' in conteudo and 'calcularTotalServico' in conteudo)
    
    # Conta quantas funções de cálculo temos
    funcoes_calculo = [
        'function calcularTotalProduto(',
        'function calcularTotalServico(',
        'function calcularTotaisGerais(',
        'function parseMoney(',
        'function formatMoney(',
        'function aplicarMascaraMonetaria('
    ]
    
    funcoes_presentes = sum(1 for f in funcoes_calculo if f in conteudo)
    print(f'\n📊 Funções de cálculo implementadas: {funcoes_presentes}/6')
    
    if funcoes_presentes == 6:
        print('\n🎉 SISTEMA DE CÁLCULOS IMPLEMENTADO!')
        print('✅ Agora os totais devem ser calculados automaticamente!')
        print('💡 Teste: adicione produtos/serviços e digite valores!')
    else:
        print('\n⚠️ Algumas funções de cálculo podem estar faltando')
        
except Exception as e:
    print(f'❌ Erro: {e}')