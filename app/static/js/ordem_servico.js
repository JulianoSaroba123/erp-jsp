/**
 * ERP JSP v3.0 - Ordem de Serviço JavaScript
 * ==========================================
 * 
 * Sistema completo para gerenciamento de Ordens de Serviço
 * - Adição/remoção dinâmica de serviços e produtos
 * - Cálculos automáticos em tempo real
 * - Formatação de moeda e validações
 * - Controle de tempo e parcelas
 * 
 * Autor: JSP Soluções
 * Data: 2025
 */

class OrdemServicoManager {
    constructor() {
        this.servicoIndex = 0;
        this.produtoIndex = 0;
        this.isCalculating = false;
        
        console.log('🚀 OrdemServicoManager iniciado');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeExistingItems();
        this.calculateTotals();
        this.setupTimeCalculation();
        this.setupPaymentConditions();
        console.log('✅ OrdemServicoManager inicializado');
    }

    setupEventListeners() {
        // Botões principais
        document.getElementById('btnAdicionarServico')?.addEventListener('click', () => this.addServico());
        document.getElementById('btnAdicionarProduto')?.addEventListener('click', () => this.addProduto());
        
        // Eventos de cálculo
        document.addEventListener('input', (e) => {
            if (e.target.matches('.servico-horas, .servico-valor')) {
                this.calculateServicoTotal(e.target.closest('.servico-item'));
            }
            if (e.target.matches('.produto-quantidade, .produto-valor')) {
                this.calculateProdutoTotal(e.target.closest('.produto-item'));
            }
            if (e.target.matches('#valorDesconto')) {
                this.calculateTotals();
            }
        });

        // Remoção de itens
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-remover-servico')) {
                this.removeServico(e.target.closest('.servico-item'));
            }
            if (e.target.closest('.btn-remover-produto')) {
                this.removeProduto(e.target.closest('.produto-item'));
            }
        });

        // Formatação de moeda
        document.addEventListener('input', (e) => {
            if (e.target.matches('.money')) {
                this.formatMoney(e.target);
            }
        });

        // Controles de status
        document.querySelector('.btn-iniciar-os')?.addEventListener('click', () => this.iniciarOS());
        document.querySelector('.btn-concluir-os')?.addEventListener('click', () => this.concluirOS());
        document.querySelector('.btn-cancelar-os')?.addEventListener('click', () => this.cancelarOS());

        console.log('🎯 Event listeners configurados');
    }

    initializeExistingItems() {
        // Inicializar índices baseados nos itens existentes
        const servicos = document.querySelectorAll('.servico-item');
        const produtos = document.querySelectorAll('.produto-item');
        
        this.servicoIndex = servicos.length;
        this.produtoIndex = produtos.length;

        // Recalcular totais dos itens existentes
        servicos.forEach(item => this.calculateServicoTotal(item));
        produtos.forEach(item => this.calculateProdutoTotal(item));
        
        console.log(`📊 Itens existentes: ${this.servicoIndex} serviços, ${this.produtoIndex} produtos`);
    }

    addServico() {
        console.log('➕ Adicionando novo serviço');
        
        const template = document.getElementById('servicoTemplate');
        if (!template) {
            console.error('❌ Template de serviço não encontrado');
            return;
        }

        const container = document.getElementById('servicosContainer');
        if (!container) {
            console.error('❌ Container de serviços não encontrado');
            return;
        }

        // Clonar template e substituir índice
        let html = template.innerHTML.replace(/__INDEX__/g, this.servicoIndex);
        
        // Criar elemento
        const div = document.createElement('div');
        div.innerHTML = html;
        const newItem = div.firstElementChild;
        
        // Adicionar ao container
        container.appendChild(newItem);
        
        // Focar no primeiro input
        const firstInput = newItem.querySelector('input[type="text"]');
        firstInput?.focus();
        
        this.servicoIndex++;
        console.log(`✅ Serviço adicionado com índice ${this.servicoIndex - 1}`);
    }

    addProduto() {
        console.log('➕ Adicionando novo produto');
        
        const template = document.getElementById('produtoTemplate');
        if (!template) {
            console.error('❌ Template de produto não encontrado');
            return;
        }

        const container = document.getElementById('produtosContainer');
        if (!container) {
            console.error('❌ Container de produtos não encontrado');
            return;
        }

        // Clonar template e substituir índice
        let html = template.innerHTML.replace(/__INDEX__/g, this.produtoIndex);
        
        // Criar elemento
        const div = document.createElement('div');
        div.innerHTML = html;
        const newItem = div.firstElementChild;
        
        // Adicionar ao container
        container.appendChild(newItem);
        
        // Focar no primeiro input
        const firstInput = newItem.querySelector('input[type="text"]');
        firstInput?.focus();
        
        this.produtoIndex++;
        console.log(`✅ Produto adicionado com índice ${this.produtoIndex - 1}`);
    }

    removeServico(item) {
        if (!item) return;
        
        if (confirm('Tem certeza que deseja remover este serviço?')) {
            item.remove();
            this.calculateTotals();
            console.log('🗑️ Serviço removido');
        }
    }

    removeProduto(item) {
        if (!item) return;
        
        if (confirm('Tem certeza que deseja remover este produto?')) {
            item.remove();
            this.calculateTotals();
            console.log('🗑️ Produto removido');
        }
    }

    calculateServicoTotal(item) {
        if (!item || this.isCalculating) return;
        
        const horasInput = item.querySelector('.servico-horas');
        const valorInput = item.querySelector('.servico-valor');
        const totalInput = item.querySelector('.servico-total');
        
        if (!horasInput || !valorInput || !totalInput) return;

        const horas = parseFloat(horasInput.value) || 0;
        const valor = this.parseMoneyValue(valorInput.value);
        const total = horas * valor;

        totalInput.value = this.formatCurrency(total);
        
        console.log(`🔧 Serviço calculado: ${horas}h × R$${valor} = R$${total}`);
        this.calculateTotals();
    }

    calculateProdutoTotal(item) {
        if (!item || this.isCalculating) return;
        
        const quantidadeInput = item.querySelector('.produto-quantidade');
        const valorInput = item.querySelector('.produto-valor');
        const totalInput = item.querySelector('.produto-total');
        
        if (!quantidadeInput || !valorInput || !totalInput) return;

        const quantidade = parseFloat(quantidadeInput.value) || 0;
        const valor = this.parseMoneyValue(valorInput.value);
        const total = quantidade * valor;

        totalInput.value = this.formatCurrency(total);
        
        console.log(`📦 Produto calculado: ${quantidade} × R$${valor} = R$${total}`);
        this.calculateTotals();
    }

    calculateTotals() {
        if (this.isCalculating) return;
        this.isCalculating = true;

        console.log('💰 Calculando totais gerais...');

        // Calcular total de serviços
        let totalServicos = 0;
        document.querySelectorAll('.servico-total').forEach(input => {
            totalServicos += this.parseMoneyValue(input.value);
        });

        // Calcular total de produtos
        let totalProdutos = 0;
        document.querySelectorAll('.produto-total').forEach(input => {
            totalProdutos += this.parseMoneyValue(input.value);
        });

        // Calcular desconto
        const desconto = this.parseMoneyValue(document.getElementById('valorDesconto')?.value || '0');
        
        // Calcular total geral
        const totalGeral = totalServicos + totalProdutos - desconto;

        // Atualizar campos
        this.updateField('totalServicos', totalServicos);
        this.updateField('totalProdutos', totalProdutos);
        this.updateField('valorServico', totalServicos);
        this.updateField('valorPecas', totalProdutos);
        this.updateField('valorTotal', totalGeral);

        console.log(`💰 Totais: Serviços R$${totalServicos}, Produtos R$${totalProdutos}, Total R$${totalGeral}`);
        
        this.isCalculating = false;
    }

    updateField(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = this.formatCurrency(value);
        }
    }

    parseMoneyValue(value) {
        if (!value) return 0;
        
        // Remove tudo exceto números, vírgula e ponto
        const cleaned = value.toString()
            .replace(/[^\d,.-]/g, '')
            .replace(',', '.');
            
        return parseFloat(cleaned) || 0;
    }

    formatCurrency(value) {
        return 'R$ ' + value.toFixed(2).replace('.', ',');
    }

    formatMoney(input) {
        let value = input.value.replace(/[^\d,]/g, '');
        
        // Adicionar vírgula para centavos
        if (value.length > 2) {
            value = value.slice(0, -2) + ',' + value.slice(-2);
        }
        
        // Adicionar pontos para milhares
        const parts = value.split(',');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        
        input.value = parts.join(',');
    }

    setupTimeCalculation() {
        const horaInicial = document.getElementById('horaInicial');
        const horaFinal = document.getElementById('horaFinal');
        const tempoTotal = document.getElementById('tempoTotal');

        if (!horaInicial || !horaFinal || !tempoTotal) return;

        const calculateTime = () => {
            const inicio = horaInicial.value;
            const fim = horaFinal.value;

            if (inicio && fim) {
                const [hInicio, mInicio] = inicio.split(':').map(Number);
                const [hFim, mFim] = fim.split(':').map(Number);

                const minutosInicio = hInicio * 60 + mInicio;
                const minutosFim = hFim * 60 + mFim;
                
                let diferenca = minutosFim - minutosInicio;
                if (diferenca < 0) diferenca += 24 * 60; // Adicionar 24h se passou da meia-noite

                const horas = Math.floor(diferenca / 60);
                const minutos = diferenca % 60;

                tempoTotal.value = `${horas.toString().padStart(2, '0')}:${minutos.toString().padStart(2, '0')}`;
                console.log(`⏱️ Tempo calculado: ${tempoTotal.value}`);
            } else {
                tempoTotal.value = '';
            }
        };

        horaInicial.addEventListener('change', calculateTime);
        horaFinal.addEventListener('change', calculateTime);
        
        // Calcular na inicialização se já houver valores
        calculateTime();
    }

    setupPaymentConditions() {
        const condicaoPagamento = document.getElementById('condicaoPagamento');
        const divNumeroParcelas = document.getElementById('divNumeroParcelas');

        if (!condicaoPagamento || !divNumeroParcelas) return;

        const toggleParcelas = () => {
            if (condicaoPagamento.value === 'parcelado') {
                divNumeroParcelas.style.display = 'block';
            } else {
                divNumeroParcelas.style.display = 'none';
            }
        };

        condicaoPagamento.addEventListener('change', toggleParcelas);
        
        // Verificar na inicialização
        toggleParcelas();
    }

    iniciarOS() {
        if (confirm('Tem certeza que deseja iniciar esta Ordem de Serviço?')) {
            window.location.href = window.location.pathname + '/iniciar';
        }
    }

    concluirOS() {
        if (confirm('Tem certeza que deseja concluir esta Ordem de Serviço?')) {
            window.location.href = window.location.pathname + '/concluir';
        }
    }

    cancelarOS() {
        if (confirm('Tem certeza que deseja cancelar esta Ordem de Serviço?')) {
            window.location.href = window.location.pathname + '/cancelar';
        }
    }

    // Validação antes do envio do formulário
    validateForm() {
        const errors = [];
        
        // Verificar se há pelo menos um cliente selecionado
        const clienteId = document.querySelector('select[name="cliente_id"]')?.value;
        if (!clienteId) {
            errors.push('Selecione um cliente');
        }

        // Verificar se há título
        const titulo = document.querySelector('input[name="titulo"]')?.value;
        if (!titulo?.trim()) {
            errors.push('Informe o título do serviço');
        }

        // Verificar se há pelo menos um serviço ou produto
        const servicos = document.querySelectorAll('.servico-item').length;
        const produtos = document.querySelectorAll('.produto-item').length;
        
        if (servicos === 0 && produtos === 0) {
            errors.push('Adicione pelo menos um serviço ou produto');
        }

        if (errors.length > 0) {
            alert('Erro de validação:\n\n' + errors.join('\n'));
            return false;
        }

        return true;
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM carregado - inicializando OrdemServicoManager...');
    
    // Aguardar um pouco para garantir que tudo está carregado
    setTimeout(() => {
        window.osManager = new OrdemServicoManager();
        
        // Configurar validação no formulário
        const form = document.getElementById('formOrdemServico');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (!window.osManager.validateForm()) {
                    e.preventDefault();
                }
            });
        }
        
        console.log('✅ Sistema de Ordem de Serviço totalmente inicializado!');
    }, 100);
});

// Função global para debug
window.debugOS = function() {
    console.log('🔍 Debug Ordem de Serviço:');
    console.log('Manager:', window.osManager);
    console.log('Serviços:', window.osManager?.servicoIndex);
    console.log('Produtos:', window.osManager?.produtoIndex);
};