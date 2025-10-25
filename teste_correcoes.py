import requests

try:
    # Testa se o parseMoney melhorado está presente
    r = requests.get('http://127.0.0.1:5001/propostas/nova')
    
    conteudo = r.text
    
    print('✅ Status:', r.status_code)
    print('🔍 parseMoney melhorado:', 'Parsing value:' in conteudo)
    print('🧹 Função de limpeza:', 'Cleaned:' in conteudo)
    print('💰 Debug de resultado:', 'Parsed result:' in conteudo)
    print('🎭 Máscara melhorada:', 'setSelectionRange' in conteudo)
    print('🔍 Debug de elementos:', 'Elementos encontrados:' in conteudo)
    print('❌ Tratamento de erros:', 'console.error' in conteudo)
    
    if all([
        'Parsing value:' in conteudo,
        'Cleaned:' in conteudo, 
        'Parsed result:' in conteudo,
        'setSelectionRange' in conteudo,
        'Elementos encontrados:' in conteudo,
        'console.error' in conteudo
    ]):
        print('\n🎉 CORREÇÕES APLICADAS COM SUCESSO!')
        print('✅ parseMoney melhorado com debug')
        print('✅ Máscara monetária aprimorada')
        print('✅ Debug detalhado adicionado')
        print('✅ Tratamento de erros implementado')
        print('\n🧪 TESTE NOVAMENTE:')
        print('1. Recarregue a página (F5)')
        print('2. Adicione produtos/serviços')
        print('3. Digite valores (ex: 15000 = R$ 150,00)')
        print('4. Veja os logs detalhados no console')
    else:
        print('\n⚠️ Algumas correções podem não ter sido aplicadas')
        
except Exception as e:
    print(f'❌ Erro: {e}')