/**
 * ERP JSP v3.0 - Gráficos do Módulo Financeiro
 * ============================================
 * 
 * Script para renderização de gráficos interativos no dashboard financeiro.
 * Utiliza Chart.js para criar visualizações modernas e responsivas.
 * 
 * Autor: JSP Soluções
 * Data: 2026
 */

// Configuração global do Chart.js
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.color = '#758491';

// Paleta de cores JSP
const JSP_COLORS = {
    primary: '#163A5C', success: '#23845F', danger: '#C44848', warning: '#B7861D',
    info: '#2D78A8', neon: '#2CA9C5', dark: '#1F2A33', light: '#F8FAFC',
    receita: 'rgba(35, 132, 95, 0.78)', receitaBorder: '#23845F',
    despesa: 'rgba(196, 72, 72, 0.78)', despesaBorder: '#C44848',
    gradientReceita: ['rgba(35, 132, 95, 0.78)', 'rgba(44, 169, 197, 0.30)'],
    gradientDespesa: ['rgba(196, 72, 72, 0.78)', 'rgba(232, 135, 47, 0.30)']
};

/**
 * Formata valor monetário para exibição em BRL
 */
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor || 0);
}

/**
 * Cria gráfico de pizza: Receitas vs Despesas
 */
function criarGraficoPizza(canvasId, dados) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const receitas = dados.total_receitas || 0;
    const despesas = dados.total_despesas || 0;

    // Se não houver dados, mostrar gráfico vazio
    const labels = receitas === 0 && despesas === 0 
        ? ['Sem dados'] 
        : ['Receitas', 'Despesas'];
    
    const data = receitas === 0 && despesas === 0 
        ? [1] 
        : [receitas, despesas];
    
    const backgroundColor = receitas === 0 && despesas === 0 
        ? ['rgba(108, 117, 125, 0.3)'] 
        : [JSP_COLORS.receita, JSP_COLORS.despesa];
    
    const borderColor = receitas === 0 && despesas === 0 
        ? ['rgba(108, 117, 125, 1)'] 
        : [JSP_COLORS.receitaBorder, JSP_COLORS.despesaBorder];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.label === 'Sem dados') return 'Nenhum lançamento';
                            const valor = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentual = ((valor / total) * 100).toFixed(1);
                            return `${context.label}: ${formatarMoeda(valor)} (${percentual}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de barras: Evolução Mensal
 */
function criarGraficoBarras(canvasId, dados) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const meses = dados.meses || [];
    const receitas = dados.receitas || [];
    const despesas = dados.despesas || [];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: meses,
            datasets: [
                {
                    label: 'Receitas',
                    data: receitas,
                    backgroundColor: JSP_COLORS.receita,
                    borderColor: JSP_COLORS.receitaBorder,
                    borderWidth: 1
                },
                {
                    label: 'Despesas',
                    data: despesas,
                    backgroundColor: JSP_COLORS.despesa,
                    borderColor: JSP_COLORS.despesaBorder,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 10,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatarMoeda(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatarMoeda(value);
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de linha: Resultado Acumulado dos Últimos 6 Meses
 */
function criarGraficoFluxoCaixa(canvasId, dados) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const meses = dados.meses || [];
    const saldos = dados.saldos || [];

    // Criar gradiente
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(44, 169, 197, 0.30)');
    gradient.addColorStop(1, 'rgba(44, 169, 197, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: meses,
            datasets: [{
                label: 'Resultado Acumulado',
                data: saldos,
                borderColor: JSP_COLORS.neon,
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: JSP_COLORS.neon,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Resultado Acumulado: ${formatarMoeda(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatarMoeda(value);
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Cria gráfico de barras horizontais: Categorias
 */
function criarGraficoCategorias(canvasId, dados) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const categorias = dados.categorias || [];
    const valores = dados.valores || [];
    const cores = dados.cores || [];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categorias,
            datasets: [{
                label: 'Valor',
                data: valores,
                backgroundColor: cores.length > 0 ? cores : JSP_COLORS.info,
                borderWidth: 0
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatarMoeda(context.raw);
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatarMoeda(value);
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Atualiza cards com animação
 */
function animarValor(elementId, valorFinal, duracao = 1000) {
    const elemento = document.getElementById(elementId);
    if (!elemento) return;

    const valorInicial = 0;
    const incremento = valorFinal / (duracao / 16); // 60 FPS
    let valorAtual = valorInicial;

    const animacao = setInterval(() => {
        valorAtual += incremento;
        if (valorAtual >= valorFinal) {
            valorAtual = valorFinal;
            clearInterval(animacao);
        }
        elemento.textContent = formatarMoeda(valorAtual);
    }, 16);
}

/**
 * Carrega dados do dashboard via API
 */
async function carregarDadosDashboard() {
    try {
        const mes = window.FINANCEIRO_DASHBOARD_MES || new Date().getMonth() + 1;
        const ano = window.FINANCEIRO_DASHBOARD_ANO || new Date().getFullYear();
        const url = `/financeiro/api/dashboard-dados?mes=${encodeURIComponent(mes)}&ano=${encodeURIComponent(ano)}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Erro ao carregar dados');
        
        const dados = await response.json();
        
        // Atualizar gráficos
        if (dados.status === 'success') {
            const data = dados.data;
            
            // Gráfico de Pizza (usando exatamente os mesmos dados consolidados)
            criarGraficoPizza('graficoPizza', {
                total_receitas: data.resumo_mes?.total_receitas || 0,
                total_despesas: data.resumo_mes?.total_despesas || 0
            });
            
            // Gráfico de Barras (Evolução)
            if (data.evolucao_mensal) {
                criarGraficoBarras('graficoBarras', data.evolucao_mensal);
            }
            
            // Gráfico de Resultado Acumulado
            if (data.fluxo_caixa) {
                criarGraficoFluxoCaixa('graficoFluxoCaixa', data.fluxo_caixa);
            }
            
            // Gráfico de Categorias (Despesas pagas do mês selecionado)
            if (data.top_categorias) {
                criarGraficoCategorias('graficoCategorias', data.top_categorias);
            }
        }
    } catch (erro) {
        console.error('Erro ao carregar dashboard:', erro);
    }
}

/**
 * Inicialização quando o DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se Chart.js está carregado
    if (typeof Chart === 'undefined') {
        console.error('Chart.js não está carregado!');
        return;
    }
    
    // Carregar dados do dashboard
    carregarDadosDashboard();
});
