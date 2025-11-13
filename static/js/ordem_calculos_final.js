// VERSÃO FINAL SEM JQUERY - GARANTIDA PARA FUNCIONAR
console.log('🚀 CARREGANDO ordem_calculos_final.js - SEM JQUERY');

// Variáveis globais
let contadorServicos = 0;
let contadorProdutos = 0;

// Função para calcular serviço (MUITO SIMPLES)
function calcularServicoTotal(id) {
    console.log('🔧 Calculando serviço ID:', id);
    
    const container = document.getElementById(`servico-${id}`);
    if (!container) {
        console.error('❌ Container servico-' + id + ' não encontrado');
        return;
    }

    const horasInput = container.querySelector('.servico-horas');
    const valorInput = container.querySelector('.servico-valor');
    const totalInput = container.querySelector('.servico-total');

    if (!horasInput || !valorInput || !totalInput) {
        console.error('❌ Inputs do serviço não encontrados');
        return;
    }

    // Parse dos valores de forma simples
    const horas = parseFloat(horasInput.value) || 0;
    let valorStr = valorInput.value || '0';
    valorStr = valorStr.replace(/[^\d,]/g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = horas * valor;

    // Formatar resultado
    totalInput.value = 'R$ ' + total.toFixed(2).replace('.', ',');

    console.log('✅ Serviço calculado:', { id, horas, valor, total });
    calcularTotal();
}

// Função para calcular produto (MUITO SIMPLES)
function calcularProdutoTotal(id) {
    console.log('📦 Calculando produto ID:', id);
    
    const container = document.getElementById(`produto-${id}`);
    if (!container) {
        console.error('❌ Container produto-' + id + ' não encontrado');
        return;
    }

    const quantidadeInput = container.querySelector('.produto-quantidade');
    const valorInput = container.querySelector('.produto-valor');
    const totalInput = container.querySelector('.produto-total');

    if (!quantidadeInput || !valorInput || !totalInput) {
        console.error('❌ Inputs do produto não encontrados');
        return;
    }

    // Parse dos valores de forma simples
    const quantidade = parseFloat(quantidadeInput.value) || 0;
    let valorStr = valorInput.value || '0';
    valorStr = valorStr.replace(/[^\d,]/g, '').replace(',', '.');
    const valor = parseFloat(valorStr) || 0;
    const total = quantidade * valor;

    // Formatar resultado
    totalInput.value = 'R$ ' + total.toFixed(2).replace('.', ',');

    console.log('✅ Produto calculado:', { id, quantidade, valor, total });
    calcularTotal();
}

// Função para calcular total geral
function calcularTotal() {
    console.log('💰 Calculando totais...');
    
    let totalServicos = 0;
    let totalProdutos = 0;

    // Somar serviços
    document.querySelectorAll('.servico-total').forEach(input => {
        const valor = input.value.replace(/[^\d,]/g, '').replace(',', '.');
        totalServicos += parseFloat(valor) || 0;
    });

    // Somar produtos
    document.querySelectorAll('.produto-total').forEach(input => {
        const valor = input.value.replace(/[^\d,]/g, '').replace(',', '.');
        totalProdutos += parseFloat(valor) || 0;
    });

    const totalGeral = totalServicos + totalProdutos;

    // Atualizar campos
    const formatarMoeda = (valor) => 'R$ ' + valor.toFixed(2).replace('.', ',');

    const totalServicoField = document.querySelector('input[name="total_servicos"]');
    if (totalServicoField) totalServicoField.value = formatarMoeda(totalServicos);

    const totalProdutoField = document.querySelector('input[name="total_produtos"]');
    if (totalProdutoField) totalProdutoField.value = formatarMoeda(totalProdutos);

    const valorServicoField = document.querySelector('input[name="valor_servico"]');
    if (valorServicoField) valorServicoField.value = formatarMoeda(totalServicos);

    const valorPecasField = document.querySelector('input[name="valor_pecas"]');
    if (valorPecasField) valorPecasField.value = formatarMoeda(totalProdutos);

    const valorTotalField = document.querySelector('input[name="valor_total"]');
    if (valorTotalField) valorTotalField.value = formatarMoeda(totalGeral);

    console.log('💰 Totais calculados:', { totalServicos, totalProdutos, totalGeral });
}

// Função para aplicar eventos (SEM JQUERY) - VERSÃO MAIS ROBUSTA
function aplicarEventos() {
    console.log('🎯 Aplicando eventos SEM jQuery...');

    // Função para aplicar evento único em um elemento
    function aplicarEventoUnico(input, tipo) {
        let id = input.dataset.id;
        
        // Determinar ID se não estiver presente
        if (!id) {
            const parent = input.closest('.item-servico, .item-produto');
            if (parent && parent.id) {
                const match = parent.id.match(/(servico|produto)-(\d+)/);
                if (match) {
                    id = match[2];
                    input.dataset.id = id;
                    console.log(`🆔 ID adicionado automaticamente: ${tipo}-${id}`);
                }
            }
        }

        if (!id) {
            console.warn('⚠️ Não foi possível determinar ID para:', input);
            return;
        }

        // Limpar eventos anteriores
        ['input', 'change', 'keyup', 'blur', 'focus'].forEach(event => {
            input.removeEventListener(event, input._handler);
        });

        // Criar handler específico
        const handler = function(e) {
            console.log(`📝 EVENTO ${tipo.toUpperCase()} (${e.type}):`, 'ID', id, 'Valor:', this.value);
            
            if (tipo === 'servico') {
                calcularServicoTotal(parseInt(id));
            } else if (tipo === 'produto') {
                calcularProdutoTotal(parseInt(id));
            }
        };

        // Aplicar múltiplos eventos para garantir captura
        ['input', 'change', 'keyup', 'blur'].forEach(event => {
            input.addEventListener(event, handler);
        });
        
        input._handler = handler;
        console.log(`✅ Eventos aplicados: ${tipo} ID ${id}`, input);
    }

    // Aplicar eventos para serviços
    document.querySelectorAll('.servico-horas, .servico-valor').forEach(input => {
        aplicarEventoUnico(input, 'servico');
    });

    // Aplicar eventos para produtos
    document.querySelectorAll('.produto-quantidade, .produto-valor').forEach(input => {
        aplicarEventoUnico(input, 'produto');
    });

    // Eventos para desconto
    const desconto = document.querySelector('input[name="valor_desconto"]');
    if (desconto) {
        desconto.removeEventListener('input', desconto._handler);
        desconto.removeEventListener('change', desconto._handler);
        
        const handler = function() {
            console.log('📝 Evento DESCONTO:', this.value);
            calcularTotal();
        };
        
        desconto.addEventListener('input', handler);
        desconto.addEventListener('change', handler);
        desconto._handler = handler;
        
        console.log('✅ Eventos desconto aplicados');
    }

    console.log('🎯 Todos os eventos aplicados com sucesso!');
}

// Função para adicionar serviço
function adicionarServico() {
    contadorServicos++;
    console.log('➕ Adicionando serviço', contadorServicos);
    
    const container = document.getElementById('servicos-container');
    if (!container) {
        console.error('❌ Container de serviços não encontrado');
        return;
    }

    const html = `
        <div class="row item-servico g-3 align-items-end mb-3" id="servico-${contadorServicos}">
            <div class="col-md-6">
                <label class="form-label text-white">Descrição do Serviço</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" name="servico_descricao[]" value="Novo Serviço ${contadorServicos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Dias/Horas</label>
                <input type="number" class="form-control bg-dark text-white border-secondary servico-horas" name="servico_horas[]" value="1" step="0.25" min="0" data-id="${contadorServicos}">
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor</label>
                <input type="text" class="form-control bg-dark text-white border-secondary servico-valor" name="servico_valor[]" value="50,00" data-id="${contadorServicos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Total</label>
                <input type="text" class="form-control bg-secondary text-white servico-total" name="servico_total[]" data-id="${contadorServicos}" value="R$ 0,00" readonly>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger d-block w-100" onclick="removerServico(${contadorServicos})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', html);
    aplicarEventos();
    calcularServicoTotal(contadorServicos);
}

// Função para adicionar produto
function adicionarProduto() {
    contadorProdutos++;
    console.log('➕ Adicionando produto', contadorProdutos);
    
    const container = document.getElementById('produtos-container');
    if (!container) {
        console.error('❌ Container de produtos não encontrado');
        return;
    }

    const html = `
        <div class="row item-produto g-3 align-items-end mb-3" id="produto-${contadorProdutos}">
            <div class="col-md-4">
                <label class="form-label text-white">Produto/Peça</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" name="produto_descricao[]" value="Novo Produto ${contadorProdutos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Qtd.</label>
                <input type="number" class="form-control bg-dark text-white border-secondary produto-quantidade" name="produto_quantidade[]" value="1" step="0.001" min="0" data-id="${contadorProdutos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor Unit.</label>
                <input type="text" class="form-control bg-dark text-white border-secondary produto-valor" name="produto_valor[]" value="25,00" data-id="${contadorProdutos}" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Total</label>
                <input type="text" class="form-control bg-secondary text-white produto-total" name="produto_total[]" data-id="${contadorProdutos}" value="R$ 0,00" readonly>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger d-block w-100" onclick="removerProduto(${contadorProdutos})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', html);
    aplicarEventos();
    calcularProdutoTotal(contadorProdutos);
}

// Função para remover serviço (CORRIGIDA)
function removerServico(id) {
    console.log('🗑️ Removendo serviço', id);
    const elemento = document.getElementById(`servico-${id}`);
    if (elemento) {
        // Confirmar remoção
        if (confirm('Tem certeza que deseja remover este serviço?')) {
            elemento.remove();
            calcularTotal();
            console.log('✅ Serviço', id, 'removido com sucesso');
        }
    } else {
        console.error('❌ Elemento servico-' + id + ' não encontrado');
    }
}

// Função para remover produto (CORRIGIDA)
function removerProduto(id) {
    console.log('🗑️ Removendo produto', id);
    const elemento = document.getElementById(`produto-${id}`);
    if (elemento) {
        // Confirmar remoção
        if (confirm('Tem certeza que deseja remover este produto?')) {
            elemento.remove();
            calcularTotal();
            console.log('✅ Produto', id, 'removido com sucesso');
        }
    } else {
        console.error('❌ Elemento produto-' + id + ' não encontrado');
    }
}

// Funções auxiliares (mantidas para compatibilidade)
function calcularKM() {
    const kmIn = parseFloat(document.getElementById('km_inicial')?.value) || 0;
    const kmFi = parseFloat(document.getElementById('km_final')?.value) || 0;
    const diff = kmFi - kmIn;
    const kmTotalField = document.getElementById('km_total');
    if (kmTotalField) kmTotalField.value = diff >= 0 ? `${diff} km` : '0 km';
}

function calcularTempo() {
    const hi = document.getElementById('hora_inicial')?.value;
    const hf = document.getElementById('hora_final')?.value;
    const tempoField = document.getElementById('tempo_total');
    if (!hi || !hf || !tempoField) return;

    const [hiH, hiM] = hi.split(':').map(x => parseInt(x, 10));
    const [hfH, hfM] = hf.split(':').map(x => parseInt(x, 10));
    let dtHi = new Date(); dtHi.setHours(hiH, hiM, 0, 0);
    let dtHf = new Date(); dtHf.setHours(hfH, hfM, 0, 0);

    if (dtHf <= dtHi) dtHf.setDate(dtHf.getDate() + 1);

    const diffMs = dtHf - dtHi;
    const diffMin = Math.floor(diffMs / 60000);
    const hours = Math.floor(diffMin / 60);
    const minutes = diffMin % 60;
    const formatted = `${String(hours).padStart(2,'0')}:${String(minutes).padStart(2,'0')}`;
    tempoField.value = formatted;
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando sistema FINAL sem jQuery...');

    // Inicializar contadores
    document.querySelectorAll('.item-servico').forEach(el => {
        const match = el.id?.match(/servico-(\d+)/);
        if (match) contadorServicos = Math.max(contadorServicos, parseInt(match[1]));
    });
    document.querySelectorAll('.item-produto').forEach(el => {
        const match = el.id?.match(/produto-(\d+)/);
        if (match) contadorProdutos = Math.max(contadorProdutos, parseInt(match[1]));
    });

    console.log('📊 Contadores inicializados:', { contadorServicos, contadorProdutos });

    // Aguardar um pouco para garantir que o DOM esteja completamente carregado
    setTimeout(function() {
        console.log('⏱️ Aplicando eventos após timeout...');
        
        // Aplicar eventos
        aplicarEventos();

        // Calcular totais iniciais - FORÇAR RECÁLCULO
        console.log('💰 Calculando totais iniciais...');
        document.querySelectorAll('.item-servico').forEach(el => {
            const match = el.id?.match(/servico-(\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                console.log('🔧 Calculando serviço inicial', id);
                calcularServicoTotal(id);
            }
        });
        
        document.querySelectorAll('.item-produto').forEach(el => {
            const match = el.id?.match(/produto-(\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                console.log('📦 Calculando produto inicial', id);
                calcularProdutoTotal(id);
            }
        });

        calcularKM();
        calcularTempo();
        calcularTotal();
        
        console.log('✅ Inicialização completa com timeout finalizada!');
    }, 500);

    // Disponibilizar funções para debug E para os botões onclick
    window.aplicarEventos = aplicarEventos;
    window.calcularTotal = calcularTotal;
    window.removerServico = removerServico;
    window.removerProduto = removerProduto;
    window.adicionarServico = adicionarServico;
    window.adicionarProduto = adicionarProduto;
    window.calcularServicoTotal = calcularServicoTotal;
    window.calcularProdutoTotal = calcularProdutoTotal;
    
    window.debugEventos = function() {
        console.log('🔍 DEBUG DE EVENTOS:');
        console.log('Campos de serviço com eventos:');
        document.querySelectorAll('.servico-horas, .servico-valor').forEach((input, i) => {
            console.log(`  ${i+1}:`, input, 'ID:', input.dataset.id, 'Handler:', !!input._handler);
        });
        console.log('Campos de produto com eventos:');
        document.querySelectorAll('.produto-quantidade, .produto-valor').forEach((input, i) => {
            console.log(`  ${i+1}:`, input, 'ID:', input.dataset.id, 'Handler:', !!input._handler);
        });
    };
    
    // Função para testar eventos manualmente
    window.testarCampos = function() {
        console.log('🧪 Testando campos manualmente...');
        
        const servicoValor = document.querySelector('.servico-valor');
        if (servicoValor) {
            console.log('🧪 Alterando valor do serviço...');
            servicoValor.focus();
            servicoValor.value = '99,99';
            servicoValor.dispatchEvent(new Event('input', { bubbles: true }));
            servicoValor.dispatchEvent(new Event('change', { bubbles: true }));
            servicoValor.blur();
        }
        
        const produtoValor = document.querySelector('.produto-valor');
        if (produtoValor) {
            console.log('🧪 Alterando valor do produto...');
            produtoValor.focus();
            produtoValor.value = '88,88';
            produtoValor.dispatchEvent(new Event('input', { bubbles: true }));
            produtoValor.dispatchEvent(new Event('change', { bubbles: true }));
            produtoValor.blur();
        }
    };
    
    // Função para forçar recálculo de todos os itens
    window.forcarRecalculo = function() {
        console.log('🔄 Forçando recálculo de todos os itens...');
        
        document.querySelectorAll('.item-servico').forEach(el => {
            const match = el.id?.match(/servico-(\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                console.log('🔧 Recalculando serviço', id);
                calcularServicoTotal(id);
            }
        });
        
        document.querySelectorAll('.item-produto').forEach(el => {
            const match = el.id?.match(/produto-(\d+)/);
            if (match) {
                const id = parseInt(match[1]);
                console.log('📦 Recalculando produto', id);
                calcularProdutoTotal(id);
            }
        });
        
        calcularTotal();
        console.log('✅ Recálculo completo finalizado');
    };

    console.log('✅ Sistema FINAL inicializado!');
    console.log('💡 Funções disponíveis no console:');
    console.log('  - debugEventos() - verificar status dos eventos');
    console.log('  - testarCampos() - testar eventos automaticamente');
    console.log('  - forcarRecalculo() - recalcular todos os totais');
    console.log('  - aplicarEventos() - re-aplicar eventos');
    console.log('🎯 Tente alterar os valores nos campos agora!');
});