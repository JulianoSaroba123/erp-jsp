// =====================================================
// SCRIPT DE ADICIONAR/REMOVER PRODUTOS E SERVIÇOS
// Versão limpa sem dependências externas
// =====================================================

console.log('🚀 Carregando script de produtos/serviços externo...');

// Contadores globais
let contadorServicos = 0;
let contadorProdutos = 0;

// Função para adicionar serviço
window.adicionarServico = function() {
    console.log('🔍 adicionarServico() foi chamada!');
    contadorServicos++;
    const container = document.getElementById('servicos-container');
    
    console.log('🔍 Container serviços:', container);
    
    if (!container) {
        console.error('❌ Container de serviços não encontrado!');
        alert('Container de serviços não encontrado!');
        return;
    }

    console.log('✅ Container encontrado, adicionando serviço...');
    
    const novoServico = `
        <div class="row item-servico mb-3" id="servico-${contadorServicos}">
            <div class="col-md-6">
                <label class="form-label text-white">Descrição do Serviço</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="servico_descricao[]" 
                       placeholder="Ex: Troca de óleo" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Horas</label>
                <input type="number" class="form-control bg-dark text-white border-secondary" 
                       name="servico_horas[]" 
                       value="0" step="0.25" min="0" placeholder="0">
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="servico_valor[]" 
                       placeholder="0,00" required>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger d-block w-100" 
                        onclick="removerServico(${contadorServicos})" title="Remover serviço">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', novoServico);
    console.log('✅ Serviço adicionado:', contadorServicos);
};

// Função para adicionar produto
window.adicionarProduto = function() {
    console.log('🔍 adicionarProduto() foi chamada!');
    contadorProdutos++;
    const container = document.getElementById('produtos-container');
    
    console.log('🔍 Container produtos:', container);
    
    if (!container) {
        console.error('❌ Container de produtos não encontrado!');
        alert('Container de produtos não encontrado!');
        return;
    }

    console.log('✅ Container encontrado, adicionando produto...');
    
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
                <input type="number" class="form-control bg-dark text-white border-secondary" 
                       name="produto_quantidade[]" 
                       value="1" step="0.001" min="0" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Valor Unit.</label>
                <input type="text" class="form-control bg-dark text-white border-secondary" 
                       name="produto_valor[]" 
                       placeholder="0,00" required>
            </div>
            <div class="col-md-2">
                <label class="form-label text-white">Total</label>
                <input type="text" class="form-control bg-secondary text-white" 
                       name="produto_total[]" 
                       value="R$ 0,00" readonly>
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-outline-danger d-block w-100" 
                        onclick="removerProduto(${contadorProdutos})" title="Remover produto">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', novoProduto);
    console.log('✅ Produto adicionado:', contadorProdutos);
};

// Função para remover serviço
window.removerServico = function(id) {
    const elemento = document.getElementById(`servico-${id}`);
    if (elemento) {
        elemento.remove();
        console.log('✅ Serviço removido:', id);
    }
};

// Função para remover produto
window.removerProduto = function(id) {
    const elemento = document.getElementById(`produto-${id}`);
    if (elemento) {
        elemento.remove();
        console.log('✅ Produto removido:', id);
    }
};

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Funções de adicionar/remover carregadas via arquivo externo');
    
    // Testa se os containers existem
    const containerProdutos = document.getElementById('produtos-container');
    const containerServicos = document.getElementById('servicos-container');
    
    console.log('🔍 Container produtos existe?', !!containerProdutos);
    console.log('🔍 Container serviços existe?', !!containerServicos);
    
    // Adiciona event listeners diretos aos botões como fallback
    const btnProduto = document.querySelector('button[onclick="adicionarProduto()"]');
    const btnServico = document.querySelector('button[onclick="adicionarServico()"]');
    
    console.log('🔍 Botão produto existe?', !!btnProduto);
    console.log('🔍 Botão serviço existe?', !!btnServico);
    
    // Fallback com event listeners para garantir funcionamento
    if (btnProduto) {
        btnProduto.addEventListener('click', function(e) {
            console.log('🔥 CLICK DETECTADO no botão produto via addEventListener!');
            e.preventDefault();
            window.adicionarProduto();
        });
    }
    
    if (btnServico) {
        btnServico.addEventListener('click', function(e) {
            console.log('🔥 CLICK DETECTADO no botão serviço via addEventListener!');
            e.preventDefault(); 
            window.adicionarServico();
        });
    }
});

console.log('✅ Script externo carregado completamente!');