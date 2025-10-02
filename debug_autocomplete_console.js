// Script para colar no console do navegador (F12) na página /ordens/nova
// Para testar se as funções de auto-complete estão funcionando

console.log('🧪 TESTANDO AUTO-COMPLETE...');

// 1. Verificar se as funções existem
const funcoesAutoComplete = ['setupClienteSelection', 'setupServicoSelection', 'setupProdutoSelection'];
console.log('🔍 Verificando funções:');
funcoesAutoComplete.forEach(func => {
    const existe = typeof window[func] === 'function';
    console.log(`${existe ? '✅' : '❌'} ${func}: ${existe ? 'OK' : 'NÃO ENCONTRADA'}`);
});

// 2. Verificar se os elementos existem
const elementos = [
    'cliente_select', 'cliente_busca', 'cliente_id',
    'servico_select', 'servico_busca', 
    'produto_select', 'produto_busca'
];
console.log('🎯 Verificando elementos:');
elementos.forEach(id => {
    const el = document.getElementById(id);
    console.log(`${el ? '✅' : '❌'} #${id}: ${el ? 'ENCONTRADO' : 'NÃO ENCONTRADO'}`);
});

// 3. Verificar dados nos selects
console.log('📊 Verificando dados:');
const clienteSelect = document.getElementById('cliente_select');
if (clienteSelect) {
    console.log(`👤 Cliente Select: ${clienteSelect.options.length} opções`);
    if (clienteSelect.options.length > 1) {
        console.log(`   Primeiro: "${clienteSelect.options[1].text}"`);
    }
}

const servicoSelect = document.getElementById('servico_select');
if (servicoSelect) {
    console.log(`🔧 Serviço Select: ${servicoSelect.options.length} opções`);
}

const produtoSelect = document.getElementById('produto_select');
if (produtoSelect) {
    console.log(`📦 Produto Select: ${produtoSelect.options.length} opções`);
}

// 4. Testar auto-complete de cliente
console.log('🧪 TESTANDO CLIENTE AUTO-COMPLETE:');
try {
    if (clienteSelect && clienteSelect.options.length > 1) {
        console.log('Selecionando primeiro cliente...');
        clienteSelect.selectedIndex = 1;
        
        // Disparar evento change
        const changeEvent = new Event('change', { bubbles: true });
        clienteSelect.dispatchEvent(changeEvent);
        
        // Verificar se cliente_id foi preenchido
        const clienteId = document.getElementById('cliente_id');
        console.log(`Cliente ID após seleção: ${clienteId ? clienteId.value : 'CAMPO NÃO ENCONTRADO'}`);
        
        // Verificar se dados foram preenchidos
        const campos = ['cpf', 'telefone', 'email', 'endereco'];
        campos.forEach(campo => {
            const el = document.getElementById(campo);
            if (el) {
                console.log(`   ${campo}: "${el.value}"`);
            }
        });
    } else {
        console.warn('Cliente select vazio ou não encontrado');
    }
} catch (e) {
    console.error('❌ Erro no teste de cliente:', e);
}

// 5. Testar busca de cliente
console.log('🔍 TESTANDO BUSCA DE CLIENTE:');
try {
    const buscaCliente = document.getElementById('cliente_busca');
    if (buscaCliente) {
        console.log('Testando busca com "SANTOS"...');
        buscaCliente.value = 'SANTOS';
        
        // Disparar evento input
        const inputEvent = new Event('input', { bubbles: true });
        buscaCliente.dispatchEvent(inputEvent);
        
        setTimeout(() => {
            const clienteId = document.getElementById('cliente_id');
            console.log(`Cliente ID após busca: ${clienteId ? clienteId.value : 'NÃO ENCONTRADO'}`);
        }, 500);
    }
} catch (e) {
    console.error('❌ Erro no teste de busca:', e);
}

console.log('🏁 TESTE CONCLUÍDO! Verifique os resultados acima.');