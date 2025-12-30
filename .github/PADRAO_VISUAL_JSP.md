# 🎨 Padrão Visual JSP v3.0

## Objetivo
Estabelecer um padrão visual **consistente** e **moderno** em todos os módulos do ERP JSP, utilizando as cores da marca e um layout limpo.

## Paleta de Cores JSP

### Cores Principais
- **Ciano JSP**: `#06b6d4` (primária) e `#0891b2` (secundária)
- **Verde**: `#10b981` (sucesso) e `#059669` (dark)
- **Amarelo**: `#f59e0b` (atenção) e `#d97706` (dark)
- **Vermelho**: `#ef4444` (erro) e `#dc2626` (dark)

### Gradientes Padrão
```css
/* Ciano JSP - Headers principais */
background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);

/* Verde - Sucesso, Confirmações */
background: linear-gradient(135deg, #10b981 0%, #059669 100%);

/* Amarelo - Avisos, Atenção */
background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);

/* Vermelho - Erros, Exclusões */
background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
```

## Estrutura de Página VISUALIZAR

### 1. Cabeçalho Principal
```html
<div class="os-header">
    <div class="row align-items-center">
        <div class="col-lg-8">
            <h2 class="mb-2">
                <i class="fas fa-file-contract me-2"></i>
                Título do Documento
            </h2>
            <p class="mb-2 opacity-75">Subtítulo ou descrição</p>
            <!-- Badges de status -->
        </div>
        <div class="col-lg-4 text-lg-end">
            <!-- Botões de ação -->
        </div>
    </div>
</div>
```

### 2. Cards de Informação
```html
<div class="row g-4">
    <div class="col-md-3">
        <div class="stats-box">
            <i class="fas fa-user"></i>
            <h6 class="text-muted">Label</h6>
            <strong>Valor</strong>
        </div>
    </div>
</div>
```

### 3. Card de Valor Destacado
```html
<div class="value-highlight">
    <h6>Valor Total</h6>
    <div class="amount">R$ 1.500,00</div>
</div>
```

### 4. Seções com Headers Separados
```html
<!-- Header separado -->
<div class="mb-4 p-3 rounded-3" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); color: white; box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);">
    <h5 class="mb-0 fw-bold">
        <i class="fas fa-icon me-2"></i>
        Título da Seção
    </h5>
</div>

<!-- Card de conteúdo -->
<div class="card border-secondary shadow-sm mb-4">
    <div class="card-body">
        <!-- Conteúdo aqui -->
    </div>
</div>
```

## Estrutura de Página LISTAR

### 1. Cabeçalho com Botão de Ação
```html
<div class="mb-4 p-4 rounded-3" style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);">
    <div class="d-flex justify-content-between align-items-center">
        <h3 class="text-white mb-0 fw-bold">
            <i class="fas fa-icon me-2"></i>
            Título da Listagem
        </h3>
        <a href="#" class="btn btn-light btn-lg">
            <i class="fas fa-plus me-2"></i>Novo
        </a>
    </div>
</div>
```

### 2. Card de Filtros
```html
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body">
        <!-- Formulário de filtros -->
    </div>
</div>
```

## Estrutura de Página FORM

### Seções com Headers Coloridos
Cada seção usa gradientes específicos:
- **Informações Básicas**: Ciano
- **Dados Específicos**: Amarelo
- **Técnicos/Descrições**: Ciano  
- **Controle**: Verde
- **Valores/Pagamento**: Amarelo
- **Anexos**: Vermelho

## CSS Padrão JSP

```css
/* Cabeçalho Padrão */
.os-header {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    color: white;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(6,182,212,0.3);
}

/* Cards de Informação */
.info-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: transform 0.2s;
    background: white;
}

.info-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

/* Cards de Estatísticas */
.stats-box {
    background: white;
    border: 1px solid #e5e7eb;
    border-left: 4px solid #06b6d4;
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
}

.stats-box i {
    font-size: 2rem;
    color: #06b6d4;
}

/* Valor Destacado */
.value-highlight {
    background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(6,182,212,0.3);
}

.value-highlight .amount {
    font-size: 2.5rem;
    font-weight: bold;
    color: white;
}

/* Badges de Status */
.status-badge {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: 600;
    display: inline-flex;
    align-items-center;
    gap: 0.5rem;
}

/* Botões de Ação */
.action-btn {
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    transition: all 0.3s;
}

.action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
```

## Regras de Aplicação

### ✅ SEMPRE use:
1. **Gradiente ciano** para headers principais
2. **Headers separados** dos cards (mb-4 p-3 rounded-3)
3. **Cards brancos** com shadow-sm
4. **Ícones Font Awesome** em todos os títulos
5. **Espaçamento consistente**: mb-4 para seções

### ❌ NUNCA use:
1. Tema escuro/neon em páginas internas
2. Bordas sobrepostas (headers dentro de cards)
3. Cores aleatórias fora da paleta JSP
4. Espaçamentos inconsistentes

## Checklist de Padronização

- [ ] Header principal com gradiente ciano
- [ ] Headers de seções separados dos cards
- [ ] Cores da paleta JSP (ciano, verde, amarelo, vermelho)
- [ ] Ícones em todos os títulos
- [ ] Cards com shadow-sm e border-secondary
- [ ] Espaçamento mb-4 entre seções
- [ ] Botões com estilo action-btn
- [ ] Hover effects em cards
- [ ] Responsivo (col-md-*, d-none d-md-inline)

## Módulos Já Padronizados

✅ **Proposta**
- visualizar.html
- listar.html
- form.html

✅ **Ordem de Serviço**
- listar.html
- form.html
- ⏳ visualizar.html (em andamento)

## Próximos Módulos

- [ ] Cliente
- [ ] Fornecedor
- [ ] Produto
- [ ] Financeiro
- [ ] Dashboard

---
**Última atualização**: 29/12/2025
