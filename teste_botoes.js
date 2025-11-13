// SISTEMA SUPER SIMPLES PARA TESTAR BOTÕES
console.log('🔥 SISTEMA SIMPLES CARREGADO');

function testeBasico() {
    console.log('🚨 TESTE BÁSICO: Função foi chamada!');
    
    const template = document.getElementById('servicoTemplate');
    const container = document.getElementById('servicosContainer');
    
    console.log('🔍 Template encontrado:', template);
    console.log('🔍 Container encontrado:', container);
    
    if (!template) {
        alert('ERRO: Template servicoTemplate não encontrado!');
        return;
    }
    
    if (!container) {
        alert('ERRO: Container servicosContainer não encontrado!');
        return;
    }
    
    try {
        const clone = template.content.cloneNode(true);
        console.log('✅ Clone criado:', clone);
        
        container.appendChild(clone);
        console.log('✅ Clone adicionado ao container');
        alert('SUCESSO: Serviço adicionado!');
        
    } catch (error) {
        console.error('❌ ERRO na clonagem:', error);
        alert('ERRO: ' + error.message);
    }
}

function testeProduto() {
    console.log('🚨 TESTE PRODUTO: Função foi chamada!');
    
    const template = document.getElementById('produtoTemplate');
    const container = document.getElementById('produtosContainer');
    
    console.log('🔍 Template encontrado:', template);
    console.log('🔍 Container encontrado:', container);
    
    if (!template) {
        alert('ERRO: Template produtoTemplate não encontrado!');
        return;
    }
    
    if (!container) {
        alert('ERRO: Container produtosContainer não encontrado!');
        return;
    }
    
    try {
        const clone = template.content.cloneNode(true);
        console.log('✅ Clone criado:', clone);
        
        container.appendChild(clone);
        console.log('✅ Clone adicionado ao container');
        alert('SUCESSO: Produto adicionado!');
        
    } catch (error) {
        console.error('❌ ERRO na clonagem:', error);
        alert('ERRO: ' + error.message);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Sistema carregado - verificando elementos:');
    console.log('- servicoTemplate:', !!document.getElementById('servicoTemplate'));
    console.log('- servicosContainer:', !!document.getElementById('servicosContainer'));
    console.log('- produtoTemplate:', !!document.getElementById('produtoTemplate'));
    console.log('- produtosContainer:', !!document.getElementById('produtosContainer'));
    console.log('- btnAdicionarServico:', !!document.getElementById('btnAdicionarServico'));
    console.log('- btnAdicionarProduto:', !!document.getElementById('btnAdicionarProduto'));
});