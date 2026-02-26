// VERSÃO SUPER SIMPLIFICADA - DEBUG INTENSIVO
console.log('🚀 CARREGANDO ordem_calculos_debug.js');

// Função SUPER SIMPLES para calcular serviço
function calcularServicoSimples(input) {
    console.log('🔧 CALCULANDO SERVIÇO SIMPLES:', input);
    
    const container = input.closest('.item-servico');
    if (!container) {
        console.error('❌ Container não encontrado');
        return;
    }
    
    const horasInput = container.querySelector('.servico-horas');
    const valorInput = container.querySelector('.servico-valor');
    const totalInput = container.querySelector('.servico-total');
    
    if (!horasInput || !valorInput || !totalInput) {
        console.error('❌ Inputs não encontrados');
        return;
    }
    
    const horas = parseFloat(horasInput.value) || 0;
    let valorStr = valorInput.value || '0';
    valorStr = valorStr.replace(',', '.').replace(/[^0-9.]/g, '');
    const valor = parseFloat(valorStr) || 0;
    const total = horas * valor;
    
    totalInput.value = 'R$ ' + total.toFixed(2).replace('.', ',');
    
    console.log('✅ CALCULADO:', { horas, valor, total });
    calcularTotalGeral();
}

// Função SUPER SIMPLES para calcular produto
function calcularProdutoSimples(input) {
    console.log('📦 CALCULANDO PRODUTO SIMPLES:', input);
    
    const container = input.closest('.item-produto');
    if (!container) {
        console.error('❌ Container não encontrado');
        return;
    }
    
    const qtdInput = container.querySelector('.produto-quantidade');
    const valorInput = container.querySelector('.produto-valor');
    const totalInput = container.querySelector('.produto-total');
    
    if (!qtdInput || !valorInput || !totalInput) {
        console.error('❌ Inputs não encontrados');
        return;
    }
    
    const quantidade = parseFloat(qtdInput.value) || 0;
    let valorStr = valorInput.value || '0';
    valorStr = valorStr.replace(',', '.').replace(/[^0-9.]/g, '');
    const valor = parseFloat(valorStr) || 0;
    const total = quantidade * valor;
    
    totalInput.value = 'R$ ' + total.toFixed(2).replace('.', ',');
    
    console.log('✅ CALCULADO:', { quantidade, valor, total });
    calcularTotalGeral();
}

// Função para calcular total geral
function calcularTotalGeral() {
    console.log('💰 CALCULANDO TOTAL GERAL');
    
    let totalServicos = 0;
    let totalProdutos = 0;
    
    // Somar serviços
    document.querySelectorAll('.servico-total').forEach(input => {
        const valor = input.value.replace(/[^0-9,]/g, '').replace(',', '.');
        totalServicos += parseFloat(valor) || 0;
    });
    
    // Somar produtos
    document.querySelectorAll('.produto-total').forEach(input => {
        const valor = input.value.replace(/[^0-9,]/g, '').replace(',', '.');
        totalProdutos += parseFloat(valor) || 0;
    });
    
    const totalGeral = totalServicos + totalProdutos;
    
    // Atualizar campos de total
    const totalServicoField = document.querySelector('input[name="total_servicos"]');
    if (totalServicoField) totalServicoField.value = 'R$ ' + totalServicos.toFixed(2).replace('.', ',');
    
    const totalProdutoField = document.querySelector('input[name="total_produtos"]');
    if (totalProdutoField) totalProdutoField.value = 'R$ ' + totalProdutos.toFixed(2).replace('.', ',');
    
    const valorTotalField = document.querySelector('input[name="valor_total"]');
    if (valorTotalField) valorTotalField.value = 'R$ ' + totalGeral.toFixed(2).replace('.', ',');
    
    console.log('💰 TOTAIS:', { totalServicos, totalProdutos, totalGeral });
}

// Aplicar eventos de forma SUPER SIMPLES
function aplicarEventosSimples() {
    console.log('🎯 APLICANDO EVENTOS SUPER SIMPLES');
    
    // Remover todos os eventos antigos
    document.querySelectorAll('.servico-horas, .servico-valor').forEach(input => {
        const newInput = input.cloneNode(true);
        input.parentNode.replaceChild(newInput, input);
    });
    
    document.querySelectorAll('.produto-quantidade, .produto-valor').forEach(input => {
        const newInput = input.cloneNode(true);
        input.parentNode.replaceChild(newInput, input);
    });
    
    // Aplicar novos eventos
    document.querySelectorAll('.servico-horas, .servico-valor').forEach(input => {
        console.log('📝 Aplicando evento SERVIÇO em:', input);
        input.addEventListener('input', function() {
            console.log('🔔 EVENTO SERVIÇO DISPARADO!', this.value);
            calcularServicoSimples(this);
        });
        input.addEventListener('change', function() {
            console.log('🔔 EVENTO CHANGE SERVIÇO!', this.value);
            calcularServicoSimples(this);
        });
        input.addEventListener('keyup', function() {
            console.log('🔔 EVENTO KEYUP SERVIÇO!', this.value);
            calcularServicoSimples(this);
        });
    });
    
    document.querySelectorAll('.produto-quantidade, .produto-valor').forEach(input => {
        console.log('📝 Aplicando evento PRODUTO em:', input);
        input.addEventListener('input', function() {
            console.log('🔔 EVENTO PRODUTO DISPARADO!', this.value);
            calcularProdutoSimples(this);
        });
        input.addEventListener('change', function() {
            console.log('🔔 EVENTO CHANGE PRODUTO!', this.value);
            calcularProdutoSimples(this);
        });
        input.addEventListener('keyup', function() {
            console.log('🔔 EVENTO KEYUP PRODUTO!', this.value);
            calcularProdutoSimples(this);
        });
    });
    
    console.log('✅ EVENTOS APLICADOS!');
}

// Testar se está funcionando
function testarEventos() {
    console.log('🧪 TESTANDO EVENTOS...');
    
    const servicoValor = document.querySelector('.servico-valor');
    if (servicoValor) {
        console.log('🧪 Testando serviço...');
        servicoValor.value = '50,00';
        servicoValor.dispatchEvent(new Event('input'));
        servicoValor.dispatchEvent(new Event('change'));
    }
    
    const produtoValor = document.querySelector('.produto-valor');
    if (produtoValor) {
        console.log('🧪 Testando produto...');
        produtoValor.value = '25,00';
        produtoValor.dispatchEvent(new Event('input'));
        produtoValor.dispatchEvent(new Event('change'));
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 INICIANDO SISTEMA SUPER SIMPLES...');
    
    setTimeout(function() {
        aplicarEventosSimples();
        calcularTotalGeral();
        
        // Disponibilizar funções globalmente
        window.testarEventos = testarEventos;
        window.aplicarEventosSimples = aplicarEventosSimples;
        window.calcularTotalGeral = calcularTotalGeral;
        
        console.log('✅ SISTEMA SUPER SIMPLES PRONTO!');
        console.log('💡 Para testar, digite no console: testarEventos()');
    }, 1000);
});