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

// Função para aplicar máscaras e eventos (simplificada e mais robusta)
function aplicarMascarasEEventos(container = document) {
    console.log('🎭 Aplicando máscaras e eventos...', container);
    
    // Aplicar máscaras money (se jquery.mask estiver disponível)
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.mask) {
        $(container).find('.money').each(function() {
            if (!$(this).data('masked')) {
                $(this).mask('#.##0,00', {
                    reverse: true,
                    translation: {'#': {pattern: /[0-9]/}}
                });
                $(this).data('masked', true);
                console.log('🎭 Máscara aplicada ao campo:', this);
            }
        });
        console.log('✅ Máscaras jQuery aplicadas');
    }

    // Função para garantir data-id
    function garantirDataId(elemento) {
        if (!elemento.dataset.id) {
            const parent = elemento.closest('.item-servico, .item-produto');
            if (parent && parent.id) {
                const match = parent.id.match(/(?:servico|produto)-(\d+)/);
                if (match) {
                    elemento.dataset.id = match[1];
                    console.log('🆔 Data-id adicionado:', elemento, 'ID:', match[1]);
                }
            }
        }
        return elemento.dataset.id;
    }

    // Eventos para SERVIÇOS (usando event delegation mais robusto)
    container.querySelectorAll('.servico-horas, .servico-valor').forEach(input => {
        // Garantir data-id
        garantirDataId(input);
        
        // Remover eventos antigos
        const oldHandler = input._osHandler;
        if (oldHandler) {
            input.removeEventListener('input', oldHandler);
            input.removeEventListener('change', oldHandler);
            input.removeEventListener('keyup', oldHandler);
        }
        
        // Criar novo handler
        const newHandler = function(e) {
            console.log('📝 Evento SERVIÇO disparado:', e.type, input, 'Valor:', input.value);
            const id = input.dataset.id;
            if (id) {
                calcularServicoTotal(parseInt(id));
            } else {
                console.warn('⚠️ Serviço sem data-id:', input);
            }
        };
        
        // Adicionar múltiplos eventos para garantir captura
        input.addEventListener('input', newHandler);
        input.addEventListener('change', newHandler);
        input.addEventListener('keyup', newHandler);
        input._osHandler = newHandler;
        
        console.log('✅ Eventos serviço registrados para:', input, 'ID:', input.dataset.id);
    });

    // Eventos para PRODUTOS (usando event delegation mais robusto)
    container.querySelectorAll('.produto-quantidade, .produto-valor').forEach(input => {
        // Garantir data-id
        garantirDataId(input);
        
        // Remover eventos antigos
        const oldHandler = input._osHandler;
        if (oldHandler) {
            input.removeEventListener('input', oldHandler);
            input.removeEventListener('change', oldHandler);
            input.removeEventListener('keyup', oldHandler);
        }
        
        // Criar novo handler
        const newHandler = function(e) {
            console.log('📝 Evento PRODUTO disparado:', e.type, input, 'Valor:', input.value);
            const id = input.dataset.id;
            if (id) {
                calcularProdutoTotal(parseInt(id));
            } else {
                console.warn('⚠️ Produto sem data-id:', input);
            }
        };
        
        // Adicionar múltiplos eventos
        input.addEventListener('input', newHandler);
        input.addEventListener('change', newHandler);
        input.addEventListener('keyup', newHandler);
        input._osHandler = newHandler;
        
        console.log('✅ Eventos produto registrados para:', input, 'ID:', input.dataset.id);
    });

    // Evento para desconto
    const desconto = container.querySelector('input[name="valor_desconto"]');
    if (desconto) {
        const oldHandler = desconto._osHandler;
        if (oldHandler) {
            desconto.removeEventListener('input', oldHandler);
            desconto.removeEventListener('change', oldHandler);
        }
        
        const newHandler = function() {
            console.log('📝 Evento DESCONTO disparado:', desconto.value);
            calcularTotal();
        };
        
        desconto.addEventListener('input', newHandler);
        desconto.addEventListener('change', newHandler);
        desconto._osHandler = newHandler;
        
        console.log('✅ Eventos desconto registrados');
    }
    
    console.log('🎯 Eventos aplicados com sucesso!');
}

// Função para calcular total de serviço
function calcularServicoTotal(id) {
    console.log('🔧 Calculando serviço total para ID:', id);
    const container = document.getElementById(`servico-${id}`);
    if (!container) {
        console.error('❌ Container não encontrado para servico-' + id);
        return;
    }

    const horasInput = container.querySelector('.servico-horas');
    const valorInput = container.querySelector('.servico-valor');
    const totalInput = container.querySelector('.servico-total');

    if (!horasInput || !valorInput || !totalInput) {
        console.error('❌ Inputs não encontrados para serviço', id, {horasInput, valorInput, totalInput});
        return;
    }

    const horas = parseFloat(horasInput.value) || 0;
    const valorStr = (valorInput.value || '').toString().replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = horas * valor;

    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    console.log('🔧 Serviço calculado:', { id, horas, valorStr, valor, total, valorFormatado: totalInput.value });
    calcularTotal();
}

// Função para calcular total de produto
function calcularProdutoTotal(id) {
    console.log('📦 Calculando produto total para ID:', id);
    const container = document.getElementById(`produto-${id}`);
    if (!container) {
        console.error('❌ Container não encontrado para produto-' + id);
        return;
    }

    const quantidadeInput = container.querySelector('.produto-quantidade');
    const valorInput = container.querySelector('.produto-valor');
    const totalInput = container.querySelector('.produto-total');

    if (!quantidadeInput || !valorInput || !totalInput) {
        console.error('❌ Inputs não encontrados para produto', id, {quantidadeInput, valorInput, totalInput});
        return;
    }

    const quantidade = parseFloat(quantidadeInput.value) || 0;
    const valorStr = (valorInput.value || '').toString().replace(/\./g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = quantidade * valor;

    totalInput.value = 'R$ ' + total.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });

    console.log('📦 Produto calculado:', { id, quantidade, valorStr, valor, total, valorFormatado: totalInput.value });
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

    // Inicializar estado de parcelas
    try { toggleParcelas(); } catch (e) { console.warn('toggleParcelas não disponível ainda'); }

    console.log('✅ Sistema de cálculos inicializado!');
    
    // Função de debug disponível no console
    window.debugOS = function() {
        console.log('🔍 DEBUG DO SISTEMA OS:');
        console.log('Serviços encontrados:', document.querySelectorAll('.item-servico').length);
        console.log('Produtos encontrados:', document.querySelectorAll('.item-produto').length);
        
        document.querySelectorAll('.servico-horas, .servico-valor').forEach((input, index) => {
            console.log(`Serviço input ${index}:`, {
                elemento: input,
                dataId: input.dataset.id,
                valor: input.value,
                eventos: input._osHandler ? 'SIM' : 'NÃO'
            });
        });
        
        document.querySelectorAll('.produto-quantidade, .produto-valor').forEach((input, index) => {
            console.log(`Produto input ${index}:`, {
                elemento: input,
                dataId: input.dataset.id,
                valor: input.value,
                eventos: input._osHandler ? 'SIM' : 'NÃO'
            });
        });
        
        console.log('Para testar eventos, use: testEventos()');
    };
    
    // Função para testar eventos manualmente
    window.testEventos = function() {
        console.log('🧪 Testando eventos...');
        
        const servicoValor = document.querySelector('.servico-valor');
        if (servicoValor) {
            console.log('Testando evento em serviço valor:', servicoValor);
            servicoValor.value = '99,99';
            servicoValor.dispatchEvent(new Event('input'));
        }
        
        const produtoValor = document.querySelector('.produto-valor');
        if (produtoValor) {
            console.log('Testando evento em produto valor:', produtoValor);
            produtoValor.value = '88,88';
            produtoValor.dispatchEvent(new Event('input'));
        }
    };
    
    // Função para re-aplicar eventos
    window.reapplyEvents = function() {
        console.log('🔄 Re-aplicando eventos...');
        aplicarMascarasEEventos();
    };
});

// Sanitiza valores antes do envio do formulário: remove máscaras e formata números
function sanitizeBeforeSubmit(event) {
    // Produtos: quantidade (number) e valor (money)
    document.querySelectorAll('.produto-quantidade').forEach(input => {
        if (!input) return;
        // Remover espaços e trocar vírgula por ponto
        let v = (input.value || '').toString().trim();
        // Se contém vírgula, assumimos formato brasileiro (pontos = milhares, vírgula = decimal)
        if (v.indexOf(',') !== -1) {
            v = v.replace(/\./g, ''); // remove separadores de milhares
            v = v.replace(',', '.');
        } else {
            // Não contém vírgula: ponto pode ser separador decimal — NÃO remover pontos
            // Apenas garantir que não haja espaços
            v = v.replace(/\s+/g, '');
        }
        // Se for vazio, manter 0
        if (v === '' || v === '.' ) v = '0';
        input.value = v;
    });

    document.querySelectorAll('.produto-valor').forEach(input => {
        if (!input) return;
        let v = (input.value || '').toString().trim();
        v = v.replace(/R\$\s?/g, '');
        v = v.replace(/\./g, '');
        v = v.replace(',', '.');
        if (v === '' || v === '.' ) v = '0';
        input.value = v;
    });

    // Serviços: horas e valor
    document.querySelectorAll('.servico-horas').forEach(input => {
        if (!input) return;
        let v = (input.value || '').toString().trim();
        // Manuseio igual ao de quantidade: tratar vírgula como decimal
        if (v.indexOf(',') !== -1) {
            v = v.replace(/\./g, '');
            v = v.replace(',', '.');
        } else {
            v = v.replace(/\s+/g, '');
        }
        if (v === '' || v === '.' ) v = '0';
        input.value = v;
    });

    document.querySelectorAll('.servico-valor').forEach(input => {
        if (!input) return;
        let v = (input.value || '').toString().trim();
        v = v.replace(/R\$\s?/g, '');
        v = v.replace(/\./g, '');
        v = v.replace(',', '.');
        if (v === '' || v === '.' ) v = '0';
        input.value = v;
    });

    // Desconto
    const desconto = document.querySelector('input[name="valor_desconto"]');
    if (desconto) {
        let v = (desconto.value || '').toString().trim();
        v = v.replace(/R\$\s?/g, '');
        v = v.replace(/\./g, '');
        v = v.replace(',', '.');
        if (v === '' || v === '.' ) v = '0';
        desconto.value = v;
    }

    // Parcelas: sanitizar valores e datas
    document.querySelectorAll('input[name="parcela_valor[]"]').forEach(input => {
        if (!input) return;
        let v = (input.value || '').toString().trim();
        v = v.replace(/R\$\s?/g, '');
        v = v.replace(/\./g, '');
        v = v.replace(',', '.');
        if (v === '' || v === '.') v = '0';
        input.value = v;
    });

    document.querySelectorAll('input[name="parcela_data[]"]').forEach(input => {
        if (!input) return;
        // garante formato YYYY-MM-DD (já é o formato do input date)
        input.value = (input.value || '').toString();
    });

    // Entrada
    const entrada = document.getElementById('entrada');
    if (entrada) {
        let v = (entrada.value || '').toString().trim();
        v = v.replace(/R\$\s?/g, '');
        v = v.replace(/\./g, '');
        v = v.replace(',', '.');
        if (v === '' || v === '.') v = '0';
        entrada.value = v;
    }

    // Nota: não prevenir submit; apenas sanitiza valores in-place
}

// Anexa sanitização ao submit do formulário, se existir
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('formOrdemServico');
    if (form) {
        form.addEventListener('submit', sanitizeBeforeSubmit, true);
        console.log('🔒 Sanitização antes do submit ativada');
    }
});

// Função utilitária para parsear textos no formato 'R$ 1.234,56' ou '1.234,56' para número
function parseMoneyString(str) {
    if (!str) return 0;
    let s = String(str).replace(/R\$\s?/g, '').trim();
    s = s.replace(/\./g, '');
    s = s.replace(',', '.');
    const n = parseFloat(s);
    return isNaN(n) ? 0 : n;
}

// Habilita/desabilita controles de parcelas baseado na condição de pagamento
function toggleParcelas() {
    // suporta tanto ordem (condicao_pagamento) quanto proposta (forma_pagamento)
    let cond = document.querySelector('select[name="condicao_pagamento"]');
    if (!cond) cond = document.querySelector('select[name="forma_pagamento"]');
    const numParcelas = document.getElementById('numero_parcelas');
    const btnCalc = document.getElementById('btnCalcularParcelas');
    const btnAtual = document.getElementById('btnAtualizarParcelas');
    if (!cond || !numParcelas) return;
    if (cond.value === 'parcelado') {
        numParcelas.disabled = false;
        if (btnCalc) btnCalc.disabled = false;
        if (btnAtual) btnAtual.disabled = false;
    } else {
        numParcelas.disabled = true;
        if (btnCalc) btnCalc.disabled = true;
        if (btnAtual) btnAtual.disabled = true;
        // limpar container de parcelas
        const cont = document.getElementById('parcelas-container');
        if (cont) cont.innerHTML = '';
    }
}

// Adiciona meses a uma data (Date object)
function addMonths(dateObj, months) {
    const d = new Date(dateObj.valueOf());
    const day = d.getDate();
    d.setMonth(d.getMonth() + months);
    // Ajuste para meses curtos
    if (d.getDate() !== day) {
        d.setDate(0);
    }
    return d;
}

// Calcula parcelas baseado no valor total, entrada e número de parcelas
function calcularParcelas() {
    const valorTotalField = document.querySelector('input[name="valor_total"]');
    const entradaField = document.getElementById('entrada');
    const numParcelasField = document.getElementById('numero_parcelas');
    const cont = document.getElementById('parcelas-container');
    if (!valorTotalField || !cont || !numParcelasField) return;

    const total = parseMoneyString(valorTotalField.value);
    const entrada = parseMoneyString(entradaField ? entradaField.value : 0);
    const num = parseInt(numParcelasField.value || '1', 10) || 1;

    let restante = total - entrada;
    if (restante < 0) restante = 0;

    const parcelaValor = Math.round((restante / num) * 100) / 100;

    // data base para vencimento: data_prevista se existir, senão data_abertura_sidebar, senão hoje
    let baseDate = new Date();
    const dataPrev = document.querySelector('input[name="data_prevista"]');
    const dataAbert = document.querySelector('input[name="data_abertura"]') || document.querySelector('input[name="data_abertura_sidebar"]');
    if (dataPrev && dataPrev.value) baseDate = new Date(dataPrev.value + 'T00:00:00');
    else if (dataAbert && dataAbert.value) baseDate = new Date(dataAbert.value + 'T00:00:00');

    cont.innerHTML = '';
    for (let i = 0; i < num; i++) {
        const venc = addMonths(baseDate, i + 1); // parcelas começam 1 mês após a base
        const vencStr = venc.toISOString().slice(0, 10);
        const valorStr = 'R$ ' + parcelaValor.toFixed(2).replace('.', ',');

        const row = document.createElement('div');
        row.className = 'mb-2 d-flex gap-2 align-items-center';
        row.innerHTML = `
            <div style="flex:1">
                <label class="form-label text-white">Vencimento</label>
                <input type="date" class="form-control bg-dark text-white border-secondary" name="parcela_data[]" value="${vencStr}">
            </div>
            <div style="width:160px">
                <label class="form-label text-white">Valor</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" name="parcela_valor[]" value="${valorStr}">
            </div>
            <div style="width:48px; display:flex; align-items:end">
                <button type="button" class="btn btn-outline-danger btn-sm mt-3" onclick="this.closest('.mb-2').remove();">X</button>
            </div>
        `;
        cont.appendChild(row);
    }

    console.log('Parcelas geradas:', { total, entrada, num, parcelaValor });
}

// Expõe funções globalmente para chamadas inline no template
window.toggleParcelas = toggleParcelas;
window.calcularParcelas = calcularParcelas;
