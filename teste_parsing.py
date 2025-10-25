import requests

try:
    r = requests.get('http://127.0.0.1:5001/propostas/nova')
    
    # Testa se a função parseMoney melhorada está no código
    conteudo = r.text
    print('✅ Status:', r.status_code)
    print('🔍 parseMoney melhorada:', 'replace(/[^0-9.,]/g' in conteudo)
    print('🧪 Debug de parsing:', 'Parsing value:' in conteudo)
    print('🔧 Event listeners:', 'calcularTotalServico' in conteudo and 'addEventListener' in conteudo)
    
    # Simula teste da função parseMoney
    if 'replace(/[^0-9.,]/g' in conteudo:
        print('\n🧮 SIMULAÇÃO DE PARSING:')
        
        # Simula os valores do exemplo
        test_values = ['R$ 500,00', '500,00', '500']
        for test_val in test_values:
            # Simula o processo da função
            cleaned = ''.join(c for c in test_val if c.isdigit() or c in '.,')
            if ',' in cleaned:
                numero = cleaned.replace('.', '').replace(',', '.')
            else:
                numero = cleaned
            
            try:
                resultado = float(numero) if numero else 0
                print(f'  "{test_val}" → "{cleaned}" → "{numero}" → {resultado}')
            except:
                print(f'  "{test_val}" → ERRO')
        
        print('\n💡 Se "R$ 500,00" → 500.0, a função deveria funcionar!')
        print('🔎 Verifique o console do navegador (F12) para ver os logs reais')
    
    print('\n🚀 TESTE NO NAVEGADOR:')
    print('1. Acesse: http://127.0.0.1:5001/propostas/nova')
    print('2. Abra F12 → Console')
    print('3. Adicione um serviço')
    print('4. Digite 1 em horas e 50000 no valor (vai virar R$ 500,00)')
    print('5. Veja os logs no console mostrando o parsing')
        
except Exception as e:
    print(f'❌ Erro: {e}')