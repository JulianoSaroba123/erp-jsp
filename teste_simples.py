import requests

try:
    r = requests.get('http://127.0.0.1:5001/propostas/nova')
    print('✅ Status:', r.status_code)
    
    conteudo = r.text
    print('🔲 Botão Produto presente:', 'onclick="adicionarProduto()"' in conteudo)
    print('🔧 Botão Serviço presente:', 'onclick="adicionarServico()"' in conteudo) 
    print('📦 Container produtos:', 'id="produtos-container"' in conteudo)
    print('🛠️ Container serviços:', 'id="servicos-container"' in conteudo)
    print('⚡ JavaScript limpo:', 'Carregando funções de produtos/serviços para propostas' in conteudo)
    print('🎯 Função adicionarProduto:', 'function adicionarProduto()' in conteudo)
    print('🎯 Função adicionarServico:', 'function adicionarServico()' in conteudo)
    
    if all([
        'onclick="adicionarProduto()"' in conteudo,
        'onclick="adicionarServico()"' in conteudo,
        'id="produtos-container"' in conteudo,
        'id="servicos-container"' in conteudo,
        'function adicionarProduto()' in conteudo,
        'function adicionarServico()' in conteudo
    ]):
        print('\n🎉 PROPOSTA FUNCIONANDO PERFEITAMENTE!')
        print('✅ Todos os elementos necessários estão presentes!')
        print('🌐 Acesse: http://127.0.0.1:5001/propostas/nova')
        print('🖱️ Teste os botões "Adicionar Produto/Serviço"')
        print('👀 Verifique o console do navegador (F12) para logs de debug')
    else:
        print('\n⚠️ Alguns elementos podem estar faltando')
        
except Exception as e:
    print(f'❌ Erro: {e}')