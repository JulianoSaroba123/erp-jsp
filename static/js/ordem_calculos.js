// Script para cálculos da Ordem de Serviço

// Contadores para novos itens
let contadorServicos = 0;
let contadorProdutos = 0;

// Função para inicializar contadores (usa o maior índice existente)
function inicializarContadores() {
    contadorServicos = 0;
    contadorProdutos = 0;

    document.querySelectorAll('.item-servico').forEach(el => {
        const id = el.id || '';
        const m = id.match(/servico-(\d+)/);
        if (m) contadorServicos = Math.max(contadorServicos, parseInt(m[1], 10));
    });

    document.querySelectorAll('.item-produto').forEach(el => {
        const id = el.id || '';
        const m = id.match(/produto-(\d+)/);
        if (m) contadorProdutos = Math.max(contadorProdutos, parseInt(m[1], 10));
    });

    console.log('Contadores inicializados:', { servicos: contadorServicos, produtos: contadorProdutos });
}

// Função para adicionar serviço
function adicionarServico() {
    contadorServicos++;
    const container = document.getElementById('servicos-container');

    const novoServico = `
        <div class="row item-servico mb-3" id="servico-${contadorServicos}">
            <div class="col-md-6">
                <label class="form-label text-white">Descrição do Serviço</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="servico_descricao[]" 
                       placeholder="Ex: Troca de óleo" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Horas <small class="text-muted">(opcional)</small></label>
                <input type="number" class="form-control bg-dark text-white border-secondary servico-horas" 
                       name="servico_horas[]" 
                       value="0" step="0.25" min="0" data-id="${contadorServicos}" placeholder="0" title="Deixe vazio ou 0 para serviço fechado">
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor <small class="text-muted">(R$/hora ou total)</small></label>
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
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger d-block w-100" 
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

    // já calcula o total do novo serviço
    calcularServicoTotal(contadorServicos);

    console.log('Serviço adicionado:', contadorServicos);
}

// Função para adicionar produto
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
                <button type="button" class="btn btn-outline-danger d-block w-100" 
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

    // já calcula o total do novo produto
    calcularProdutoTotal(contadorProdutos);

    console.log('Produto adicionado:', contadorProdutos);
}

// Função para aplicar máscaras e eventos
function aplicarMascarasEEventos(container = document) {
    // Aplicar máscaras money (se jquery.mask estiver disponível)
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.mask) {
        $(container).find('.money').each(function() {
            $(this).mask('#.##0,00', {
                reverse: true,
                translation: {'#': {pattern: /[0-9]/}}
            });
        });
    }

    // Função utilitária para atribuir data-id a elementos renderizados pelo servidor
    function ensureDataId(elem, prefix) {
        if (!elem.dataset.id) {
            const parentId = elem.closest(`.${prefix}`).id || '';
            const m = parentId.match(new RegExp(`${prefix}-(\\d+)`));
            if (m) elem.dataset.id = parseInt(m[1], 10);
        }
    }

    // Registrar eventos com jQuery se disponível, caso contrário usar vanilla JS
    if (window.jQuery) {
        // Garantir data-id nos inputs existentes
        $(container).find('.servico-horas, .servico-valor').each(function() {
            ensureDataId(this, 'servico');
        });
        $(container).find('.produto-quantidade, .produto-valor').each(function() {
            ensureDataId(this, 'produto');
        });

        // Eventos para serviços
        $(container).find('.servico-horas, .servico-valor').off('input change').on('input change', function() {
            const id = $(this).data('id');
            if (id) calcularServicoTotal(id);
            else {
                const parent = $(this).closest('.item-servico');
                const pid = parent.attr('id') ? parent.attr('id').match(/servico-(\d+)/) : null;
                if (pid) calcularServicoTotal(parseInt(pid[1], 10));
            }
        });

        // Eventos para produtos
        $(container).find('.produto-quantidade, .produto-valor').off('input change').on('input change', function() {
            const id = $(this).data('id');
            if (id) calcularProdutoTotal(id);
            else {
                const parent = $(this).closest('.item-produto');
                const pid = parent.attr('id') ? parent.attr('id').match(/produto-(\d+)/) : null;
                if (pid) calcularProdutoTotal(parseInt(pid[1], 10));
            }
        });

        // Evento para desconto
        $(container).find('input[name="valor_desconto"]').off('input change').on('input change', function() {
            calcularTotal();
        });
    } else {
        // Vanilla JS event binding
        container.querySelectorAll('.servico-horas, .servico-valor').forEach(el => {
            ensureDataId(el, 'servico');
            el.removeEventListener('input', el._os_input_handler || (()=>{}));
            const handler = function() {
                const id = el.dataset.id;
                if (id) calcularServicoTotal(id);
                else {
                    const parent = el.closest('.item-servico');
                    const pid = parent && parent.id ? parent.id.match(/servico-(\d+)/) : null;
                    if (pid) calcularServicoTotal(parseInt(pid[1], 10));
                }
            };
            el.addEventListener('input', handler);
            el._os_input_handler = handler;
        });

        container.querySelectorAll('.produto-quantidade, .produto-valor').forEach(el => {
            ensureDataId(el, 'produto');
            el.removeEventListener('input', el._os_input_handler || (()=>{}));
            const handler = function() {
                const id = el.dataset.id;
                if (id) calcularProdutoTotal(id);
                else {
                    const parent = el.closest('.item-produto');
                    const pid = parent && parent.id ? parent.id.match(/produto-(\d+)/) : null;
                    if (pid) calcularProdutoTotal(parseInt(pid[1], 10));
                }
            };
            el.addEventListener('input', handler);
            el._os_input_handler = handler;
        });

        const desconto = container.querySelector('input[name="valor_desconto"]');
        if (desconto) {
            desconto.removeEventListener('input', desconto._os_input_handler || (()=>{}));
            const dHandler = function() { calcularTotal(); };
            desconto.addEventListener('input', dHandler);
            desconto._os_input_handler = dHandler;
        }
    }
}

// Função para calcular total de serviço
function calcularServicoTotal(id) {
    const container = document.getElementById(`servico-${id}`);
    if (!container) return;

    const horasInput = container.querySelector('.servico-horas');
    const valorInput = container.querySelector('.servico-valor');
    const totalInput = container.querySelector('.servico-total');

    if (!horasInput || !valorInput || !totalInput) return;

    const horas = parseFloat(horasInput.value) || 0;
    const valorStr = (valorInput.value || '').toString().replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = horas * valor;

    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    console.log('Serviço calculado:', { id, horas, valor, total });
    calcularTotal();
}

// Função para calcular total de produto
function calcularProdutoTotal(id) {
    const container = document.getElementById(`produto-${id}`);
    if (!container) return;

    const quantidadeInput = container.querySelector('.produto-quantidade');
    const valorInput = container.querySelector('.produto-valor');
    const totalInput = container.querySelector('.produto-total');

    if (!quantidadeInput || !valorInput || !totalInput) return;

    const quantidade = parseFloat(quantidadeInput.value) || 0;
    const valorStr = (valorInput.value || '').toString().replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = quantidade * valor;

    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    console.log('Produto calculado:', { id, quantidade, valor, total });
    calcularTotal();
}

// Função para calcular total geral
function calcularTotal() {
    let totalServicos = 0;
    let totalProdutos = 0;

    // Somar serviços usando classe
    document.querySelectorAll('.servico-total').forEach(input => {
        const valor = (input.value || '').toString().replace('R$', '').replace(/\s/g, '').replace(/\./g, '').replace(',', '.');
        if (valor && !isNaN(valor)) {
            totalServicos += parseFloat(valor);
        }
    });

    // Somar produtos usando classe
    document.querySelectorAll('.produto-total').forEach(input => {
        const valor = (input.value || '').toString().replace('R$', '').replace(/\s/g, '').replace(/\./g, '').replace(',', '.');
        if (valor && !isNaN(valor)) {
            totalProdutos += parseFloat(valor);
        }
    });

    // Desconto
    const descontoInput = document.querySelector('input[name="valor_desconto"]');
    const descontoStr = descontoInput ? (descontoInput.value || '').toString().replace(/\./g, '').replace(',', '.') : '0';
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

// Cálculo de KM
function calcularKM() {
    const kmIn = parseFloat((document.getElementById('km_inicial') || {value:0}).value) || 0;
    const kmFi = parseFloat((document.getElementById('km_final') || {value:0}).value) || 0;
    const diff = kmFi - kmIn;
    const kmTotalField = document.getElementById('km_total');
    if (kmTotalField) kmTotalField.value = diff >= 0 ? `${diff} km` : '0 km';
}

// Cálculo de tempo entre dois inputs type=time
function calcularTempo() {
    const hi = (document.getElementById('hora_inicial') || {value:''}).value;
    const hf = (document.getElementById('hora_final') || {value:''}).value;
    const tempoField = document.getElementById('tempo_total');
    if (!hi || !hf) {
        if (tempoField) tempoField.value = '00:00';
        return null;
    }

    // Parse HH:MM
    const [hiH, hiM] = hi.split(':').map(x => parseInt(x, 10));
    const [hfH, hfM] = hf.split(':').map(x => parseInt(x, 10));
    let dtHi = new Date(); dtHi.setHours(hiH, hiM, 0, 0);
    let dtHf = new Date(); dtHf.setHours(hfH, hfM, 0, 0);

    // Se horário final for menor que inicial, assume passagem de dia
    if (dtHf <= dtHi) dtHf.setDate(dtHf.getDate() + 1);

    const diffMs = dtHf - dtHi;
    const diffMin = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMin / 60);
    const minutes = diffMin % 60;
    const formatted = `${String(hours).padStart(2,'0')}:${String(minutes).padStart(2,'0')}`;
    if (tempoField) tempoField.value = formatted;
    return formatted;
}

// Inicialização quando o documento carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Iniciando sistema de cálculos da OS...');

    inicializarContadores();
    aplicarMascarasEEventos();

    // Calcular totais iniciais para itens renderizados
    document.querySelectorAll('.item-servico').forEach(el => {
        const m = el.id ? el.id.match(/servico-(\d+)/) : null;
        if (m) calcularServicoTotal(parseInt(m[1], 10));
    });
    document.querySelectorAll('.item-produto').forEach(el => {
        const m = el.id ? el.id.match(/produto-(\d+)/) : null;
        if (m) calcularProdutoTotal(parseInt(m[1], 10));
    });

    // Calcular KM e tempo iniciais
    calcularKM();
    calcularTempo();
    calcularTotal();

    console.log('✅ Sistema de cálculos inicializado!');
});
