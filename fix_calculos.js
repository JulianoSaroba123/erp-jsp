// Script para corrigir os cálculos automáticos na Ordem de Serviço

// Contadores para novos itens
let contadorServicos = 0;
let contadorProdutos = 0;

// Função para inicializar contadores
function inicializarContadores() {
    contadorServicos = document.querySelectorAll('.item-servico').length;
    contadorProdutos = document.querySelectorAll('.item-produto').length;
    console.log('Contadores inicializados:', { servicos: contadorServicos, produtos: contadorProdutos });
}

// Função para adicionar serviço CORRIGIDA
function adicionarServico() {
    contadorServicos++;
    const container = document.getElementById('servicos-container');
    
    const novoServico = `
        <div class="row item-servico mb-3" id="servico-${contadorServicos}">
            <div class="col-md-5">
                <label class="form-label text-white">Descrição do Serviço</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="servico_descricao[]" 
                       placeholder="Ex: Troca de óleo" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Horas</label>
                <input type="number" class="form-control bg-dark text-white border-secondary servico-horas" 
                       name="servico_horas[]" 
                       value="1" step="0.25" min="0" data-id="${contadorServicos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor/Hora</label>
                <input type="text" class="form-control money bg-dark text-white border-secondary servico-valor" 
                       name="servico_valor[]" 
                       placeholder="0,00" data-id="${contadorServicos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Total</label>
                <input type="text" class="form-control bg-secondary text-white servico-total" 
                       name="servico_total[]" data-id="${contadorServicos}"
                       value="R$ 0,00" readonly>
            </div>
            <div class="col-md-1">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger btn-sm d-block" 
                        onclick="removerServico(${contadorServicos})" title="Remover serviço">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', novoServico);
    
    // Aplicar máscara e eventos aos novos campos
    const novoContainer = document.getElementById(`servico-${contadorServicos}`);
    aplicarMascarasEEventos(novoContainer);
    
    console.log('Serviço adicionado:', contadorServicos);
}

// Função para adicionar produto CORRIGIDA
function adicionarProduto() {
    contadorProdutos++;
    const container = document.getElementById('produtos-container');
    
    const novoProduto = `
        <div class="row item-produto mb-3" id="produto-${contadorProdutos}">
            <div class="col-md-4">
                <label class="form-label text-white">Produto/Peça</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="produto_descricao[]" 
                       placeholder="Ex: Filtro de óleo" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Qtd.</label>
                <input type="number" class="form-control bg-dark text-white border-secondary produto-quantidade" 
                       name="produto_quantidade[]" 
                       value="1" step="0.001" min="0" data-id="${contadorProdutos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor Unit.</label>
                <input type="text" class="form-control money bg-dark text-white border-secondary produto-valor" 
                       name="produto_valor[]" 
                       placeholder="0,00" data-id="${contadorProdutos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Total</label>
                <input type="text" class="form-control bg-secondary text-white produto-total" 
                       name="produto_total[]" data-id="${contadorProdutos}"
                       value="R$ 0,00" readonly>
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger btn-sm d-block" 
                        onclick="removerProduto(${contadorProdutos})" title="Remover produto">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', novoProduto);
    
    // Aplicar máscara e eventos aos novos campos
    const novoContainer = document.getElementById(`produto-${contadorProdutos}`);
    aplicarMascarasEEventos(novoContainer);
    
    console.log('Produto adicionado:', contadorProdutos);
}

// Função para aplicar máscaras e eventos
function aplicarMascarasEEventos(container = document) {
    // Aplicar máscaras money
    $(container).find('.money').mask('#.##0,00', {
        reverse: true,
        translation: {'#': {pattern: /[0-9]/}}
    });
    
    // Eventos para serviços
    $(container).find('.servico-horas, .servico-valor').off('input change').on('input change', function() {
        const id = $(this).data('id');
        calcularServicoTotal(id);
    });
    
    // Eventos para produtos  
    $(container).find('.produto-quantidade, .produto-valor').off('input change').on('input change', function() {
        const id = $(this).data('id');
        calcularProdutoTotal(id);
    });
    
    // Evento para desconto
    $(container).find('input[name="valor_desconto"]').off('input change').on('input change', function() {
        calcularTotal();
    });
}

// Função para calcular total de serviço CORRIGIDA
function calcularServicoTotal(id) {
    const container = document.getElementById(`servico-${id}`);
    if (!container) return;
    
    const horasInput = container.querySelector('.servico-horas');
    const valorInput = container.querySelector('.servico-valor');
    const totalInput = container.querySelector('.servico-total');
    
    if (!horasInput || !valorInput || !totalInput) return;
    
    const horas = parseFloat(horasInput.value) || 0;
    const valorStr = valorInput.value.replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = horas * valor;
    
    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    console.log('Serviço calculado:', { id, horas, valor, total });
    calcularTotal();
}

// Função para calcular total de produto CORRIGIDA
function calcularProdutoTotal(id) {
    const container = document.getElementById(`produto-${id}`);
    if (!container) return;
    
    const quantidadeInput = container.querySelector('.produto-quantidade');
    const valorInput = container.querySelector('.produto-valor');
    const totalInput = container.querySelector('.produto-total');
    
    if (!quantidadeInput || !valorInput || !totalInput) return;
    
    const quantidade = parseFloat(quantidadeInput.value) || 0;
    const valorStr = valorInput.value.replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = quantidade * valor;
    
    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    console.log('Produto calculado:', { id, quantidade, valor, total });
    calcularTotal();
}

// Função para calcular total geral CORRIGIDA
function calcularTotal() {
    let totalServicos = 0;
    let totalProdutos = 0;
    
    // Somar serviços usando classe
    document.querySelectorAll('.servico-total').forEach(input => {
        const valor = input.value.replace('R$', '').replace(/\s/g, '').replace(/\./g, '').replace(',', '.');
        if (valor && !isNaN(valor)) {
            totalServicos += parseFloat(valor);
        }
    });
    
    // Somar produtos usando classe
    document.querySelectorAll('.produto-total').forEach(input => {
        const valor = input.value.replace('R$', '').replace(/\s/g, '').replace(/\./g, '').replace(',', '.');
        if (valor && !isNaN(valor)) {
            totalProdutos += parseFloat(valor);
        }
    });
    
    // Desconto
    const descontoInput = document.querySelector('input[name="valor_desconto"]');
    const descontoStr = descontoInput ? descontoInput.value.replace(/\./g, '').replace(',', '.') : '0';
    const desconto = parseFloat(descontoStr) || 0;
    
    console.log('Totais calculados:', { totalServicos, totalProdutos, desconto });
    
    // Atualizar campos de total
    const formatarMoeda = (valor) => 'R$ ' + valor.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    // Atualizar campos do resumo
    const totalServicoField = document.querySelector('input[name="total_servicos"]');
    if (totalServicoField) totalServicoField.value = formatarMoeda(totalServicos);
    
    const totalProdutoField = document.querySelector('input[name="total_produtos"]');
    if (totalProdutoField) totalProdutoField.value = formatarMoeda(totalProdutos);
    
    const valorServicoField = document.querySelector('input[name="valor_servico"]');
    if (valorServicoField) valorServicoField.value = formatarMoeda(totalServicos);
    
    const valorPecasField = document.querySelector('input[name="valor_pecas"]');
    if (valorPecasField) valorPecasField.value = formatarMoeda(totalProdutos);
    
    const totalGeral = totalServicos + totalProdutos - desconto;
    const valorTotalField = document.querySelector('input[name="valor_total"]');
    if (valorTotalField) valorTotalField.value = formatarMoeda(totalGeral);
}

// Função para remover serviço
function removerServico(id) {
    const elemento = document.getElementById(`servico-${id}`);
    if (elemento) {
        elemento.remove();
        calcularTotal();
        console.log('Serviço removido:', id);
    }
}

// Função para remover produto
function removerProduto(id) {
    const elemento = document.getElementById(`produto-${id}`);
    if (elemento) {
        elemento.remove();
        calcularTotal();
        console.log('Produto removido:', id);
    }
}

// Inicialização quando o documento carrega
$(document).ready(function() {
    console.log('🚀 Iniciando sistema de cálculos...');
    
    // Inicializar contadores baseado nos itens existentes
    inicializarContadores();
    
    // Aplicar máscaras e eventos a todos os campos existentes
    aplicarMascarasEEventos();
    
    // Calcular totais iniciais
    calcularTotal();
    
    console.log('✅ Sistema de cálculos inicializado!');
});