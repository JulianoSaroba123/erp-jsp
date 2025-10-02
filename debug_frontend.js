// Script de debug para testar funcionalidades JavaScript da ordem de serviço
// Cole este código no console do navegador (F12) na página /ordens/nova

console.log('🐛 INICIANDO DEBUG ORDEM DE SERVIÇO...');

// Testar se funções principais existem
const funcoesEssenciais = [
    'setupClienteSelection',
    'setupServicoSelection', 
    'setupProdutoSelection',
    'calcularHoras',
    'calcularKm',
    'calcularTotais',
    'adicionarServico',
    'adicionarProduto',
    'fmt'
];

console.log('📋 Verificando funções essenciais:');
funcoesEssenciais.forEach(funcao => {
    const existe = typeof window[funcao] === 'function';
    console.log(`${existe ? '✅' : '❌'} ${funcao}: ${existe ? 'OK' : 'NÃO ENCONTRADA'}`);
});

// Testar se elementos HTML essenciais existem
const elementosEssenciais = [
    'cliente_select',
    'cliente_busca', 
    'cliente_id',
    'servico_select',
    'produto_select',
    'hora_inicio',
    'hora_termino',
    'total_horas',
    'valor_total',
    'valor_servicos',
    'valor_produtos'
];

console.log('🎯 Verificando elementos HTML:');
elementosEssenciais.forEach(elementId => {
    const elemento = document.getElementById(elementId);
    console.log(`${elemento ? '✅' : '❌'} #${elementId}: ${elemento ? 'ENCONTRADO' : 'NÃO ENCONTRADO'}`);
});

// Testar função fmt
console.log('💰 Testando função fmt:');
try {
    const testesFmt = [0, 10.5, 123.45, 1000.99];
    testesFmt.forEach(valor => {
        const resultado = fmt(valor);
        console.log(`  fmt(${valor}) = "${resultado}"`);
    });
} catch (e) {
    console.error('❌ Erro na função fmt:', e);
}

// Testar cálculo de horas manualmente
console.log('⏰ Testando cálculo de horas:');
try {
    // Simular valores
    const horaInicio = document.getElementById('hora_inicio');
    const horaTermino = document.getElementById('hora_termino');
    const totalHoras = document.getElementById('total_horas');
    
    if (horaInicio && horaTermino && totalHoras) {
        horaInicio.value = '08:00';
        horaTermino.value = '17:00';
        
        // Chamar função
        calcularHoras();
        
        console.log(`  Início: ${horaInicio.value}`);
        console.log(`  Término: ${horaTermino.value}`);
        console.log(`  Total calculado: ${totalHoras.value}`);
    } else {
        console.warn('⚠️ Elementos de hora não encontrados para teste');
    }
} catch (e) {
    console.error('❌ Erro no teste de cálculo de horas:', e);
}

// Testar auto-complete de cliente
console.log('👤 Testando auto-complete de cliente:');
try {
    const clienteSelect = document.getElementById('cliente_select');
    if (clienteSelect && clienteSelect.options.length > 1) {
        console.log(`  ${clienteSelect.options.length} clientes disponíveis`);
        console.log(`  Primeiro cliente: "${clienteSelect.options[1].text}"`);
        
        // Testar seleção
        clienteSelect.selectedIndex = 1;
        clienteSelect.dispatchEvent(new Event('change'));
        
        const clienteId = document.getElementById('cliente_id');
        console.log(`  Cliente ID após seleção: ${clienteId ? clienteId.value : 'CAMPO NÃO ENCONTRADO'}`);
    } else {
        console.warn('⚠️ Select de cliente vazio ou não encontrado');
    }
} catch (e) {
    console.error('❌ Erro no teste de auto-complete:', e);
}

console.log('🏁 DEBUG CONCLUÍDO!');