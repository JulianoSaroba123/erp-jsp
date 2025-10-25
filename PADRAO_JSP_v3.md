# 📘 Padrão Oficial JSP v3.0

## Boas Práticas para Desenvolvimento com GitHub Copilot

Este documento estabelece os padrões de desenvolvimento para o ERP JSP v3.0, garantindo código limpo, consistente e bem documentado.

---

## 🏗️ Estrutura de Arquivos

### Organização por Módulos
```
app/
├── modulo/
│   ├── modulo_model.py      # Models e lógica de dados
│   ├── modulo_routes.py     # Rotas e controllers
│   └── templates/modulo/    # Templates específicos
│       ├── listar.html      # Lista de registros
│       ├── form.html        # Formulário (novo/editar)
│       └── visualizar.html  # Detalhes do registro
```

### Nomenclatura
- **Arquivos**: `snake_case.py`
- **Classes**: `PascalCase`
- **Funções**: `snake_case()`
- **Variáveis**: `snake_case`
- **Constantes**: `UPPER_CASE`

---

## 🗄️ Padrões de Models

### Estrutura Base
```python
# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de [Entidade]
===================================

Descrição clara da funcionalidade do model.
Inclui relacionamentos e validações.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel

class MinhaEntidade(BaseModel):
    """
    Model para representar [entidade] do sistema.
    
    Descrição detalhada da entidade e seu propósito
    no contexto do sistema.
    """
    __tablename__ = 'minha_tabela'
    
    # Campos principais (sempre documentados)
    nome = db.Column(db.String(100), nullable=False, index=True)
    descricao = db.Column(db.Text)
    
    def __repr__(self):
        """Representação string da entidade."""
        return f'<MinhaEntidade {self.nome}>'
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        return self.nome.title() if self.nome else ''
    
    @classmethod
    def buscar_por_nome(cls, nome):
        """
        Busca entidades por nome (busca parcial).
        
        Args:
            nome (str): Nome ou parte do nome
            
        Returns:
            list: Lista de entidades encontradas
        """
        return cls.query.filter(
            cls.nome.ilike(f'%{nome}%'),
            cls.ativo == True
        ).all()
```

### Campos Obrigatórios
- `id`: Chave primária (herdada de BaseModel)
- `criado_em`: Timestamp de criação (herdada)
- `atualizado_em`: Timestamp de atualização (herdada)
- `ativo`: Flag para soft delete (herdada)

### Relacionamentos
```python
# Um para muitos
categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
categoria = db.relationship('Categoria', backref='produtos')

# Muitos para muitos
tags = db.relationship('Tag', secondary='produto_tags', backref='produtos')
```

---

## 🛣️ Padrões de Routes

### Estrutura Base
```python
# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de [Módulo]
==================================

Rotas para gerenciamento de [entidade].
CRUD completo com validações.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.modulo.modulo_model import MinhaEntidade

# Cria o blueprint
modulo_bp = Blueprint('modulo', __name__, template_folder='templates')

@modulo_bp.route('/')
@modulo_bp.route('/listar')
def listar():
    """
    Lista todas as entidades ativas.
    
    Suporte para busca e filtros.
    """
    # Implementação aqui
    pass

@modulo_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """
    Cria uma nova entidade.
    
    GET: Exibe formulário
    POST: Processa criação
    """
    # Implementação aqui
    pass
```

### Rotas Padrão (CRUD)
- `GET /modulo/` - Listar registros
- `GET /modulo/novo` - Formulário de criação
- `POST /modulo/novo` - Processar criação
- `GET /modulo/<id>` - Visualizar registro
- `GET /modulo/<id>/editar` - Formulário de edição
- `POST /modulo/<id>/editar` - Processar edição
- `GET /modulo/<id>/excluir` - Excluir registro
- `GET /modulo/api/buscar` - API para autocomplete

### Tratamento de Erros
```python
try:
    # Lógica principal
    entidade.save()
    flash('Operação realizada com sucesso!', 'success')
    return redirect(url_for('modulo.listar'))
except Exception as e:
    flash(f'Erro: {str(e)}', 'error')
    return render_template('modulo/form.html', entidade=entidade)
```

---

## 🎨 Padrões de Templates

### Estrutura Base
```html
{% extends "base.html" %}

{% block title %}Título da Página - {{ super() }}{% endblock %}

{% block breadcrumb %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{{ url_for('painel.dashboard') }}">Dashboard</a></li>
        <li class="breadcrumb-item"><a href="{{ url_for('modulo.listar') }}">Módulo</a></li>
        <li class="breadcrumb-item active">Página Atual</li>
    </ol>
</nav>
{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0">
                    <i class="fas fa-icon me-2"></i>
                    Título da Seção
                </h4>
            </div>
            <div class="card-body">
                <!-- Conteúdo aqui -->
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // JavaScript específico da página
</script>
{% endblock %}
```

### Componentes Padrão

#### Tabela de Listagem
```html
<div class="table-responsive">
    <table class="table table-dark table-hover">
        <thead>
            <tr>
                <th>Campo 1</th>
                <th>Campo 2</th>
                <th width="180">Ações</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.campo1 }}</td>
                <td>{{ item.campo2 }}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <a href="{{ url_for('modulo.visualizar', id=item.id) }}" 
                           class="btn btn-outline-info" title="Visualizar">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="{{ url_for('modulo.editar', id=item.id) }}" 
                           class="btn btn-outline-warning" title="Editar">
                            <i class="fas fa-edit"></i>
                        </a>
                        <a href="javascript:void(0)" 
                           class="btn btn-outline-danger" 
                           onclick="confirmarExclusao('{{ item.nome }}', '{{ url_for('modulo.excluir', id=item.id) }}')"
                           title="Excluir">
                            <i class="fas fa-trash"></i>
                        </a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

#### Formulário Padrão
```html
<form method="POST" novalidate>
    <div class="row mb-3">
        <div class="col-md-6">
            <label for="campo" class="form-label">Campo *</label>
            <input type="text" 
                   class="form-control" 
                   id="campo" 
                   name="campo" 
                   value="{{ entidade.campo or '' }}" 
                   required>
        </div>
    </div>
    
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between">
                <a href="{{ url_for('modulo.listar') }}" class="btn btn-outline-secondary">
                    <i class="fas fa-arrow-left me-2"></i>
                    Voltar
                </a>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save me-2"></i>
                    Salvar
                </button>
            </div>
        </div>
    </div>
</form>
```

---

## 📱 Padrões de Interface

### Cores do Sistema
```css
:root {
    --primary-color: #00d4ff;    /* Azul ciano */
    --secondary-color: #0099cc;  /* Azul escuro */
    --accent-color: #ff6b6b;     /* Vermelho suave */
    --dark-bg: #0a0a0a;          /* Preto */
    --card-bg: #151515;          /* Cinza escuro */
    --success-color: #00ff88;    /* Verde */
    --warning-color: #ffaa00;    /* Laranja */
    --danger-color: #ff4757;     /* Vermelho */
}
```

### Ícones Padrão
- **Dashboard**: `fas fa-tachometer-alt`
- **Clientes**: `fas fa-users`
- **Fornecedores**: `fas fa-truck`
- **Produtos**: `fas fa-box`
- **Financeiro**: `fas fa-dollar-sign`
- **Relatórios**: `fas fa-chart-bar`
- **Configurações**: `fas fa-cog`

### Status e Badges
```html
<!-- Status simples -->
<span class="badge bg-success">Ativo</span>
<span class="badge bg-secondary">Inativo</span>
<span class="badge bg-danger">Cancelado</span>

<!-- Estoque -->
<span class="badge bg-success">Normal</span>
<span class="badge bg-warning">Alto</span>
<span class="badge bg-danger">Baixo</span>
```

---

## 🔍 Padrões de Busca e Filtros

### Busca Simples
```python
# No route
busca = request.args.get('busca', '').strip()
if busca:
    query = query.filter(
        db.or_(
            Entidade.nome.ilike(f'%{busca}%'),
            Entidade.codigo.ilike(f'%{busca}%')
        )
    )
```

### API de Autocomplete
```python
@modulo_bp.route('/api/buscar')
def api_buscar():
    """API para busca de entidades (autocomplete)."""
    termo = request.args.get('q', '').strip()
    
    if not termo or len(termo) < 2:
        return jsonify([])
    
    entidades = Entidade.query.filter(
        Entidade.nome.ilike(f'%{termo}%'),
        Entidade.ativo == True
    ).limit(10).all()
    
    resultado = []
    for entidade in entidades:
        resultado.append({
            'id': entidade.id,
            'nome': entidade.nome,
            'texto': f'{entidade.nome} - {entidade.codigo}'
        })
    
    return jsonify(resultado)
```

---

## ✅ Padrões de Validação

### Validação de Dados
```python
# Validações básicas
if not entidade.nome:
    flash('Nome é obrigatório!', 'error')
    return render_template('form.html', entidade=entidade)

# Validação de unicidade
existe = Entidade.buscar_por_codigo(entidade.codigo)
if existe and existe.id != entidade.id:
    flash('Código já existe!', 'error')
    return render_template('form.html', entidade=entidade)
```

### Sanitização
```python
# Limpar dados do formulário
nome = request.form.get('nome', '').strip()
codigo = request.form.get('codigo', '').upper()
preco = request.form.get('preco', '0').replace(',', '.')
```

---

## 🔧 Padrões de Configuração

### Variáveis de Ambiente
```env
# Desenvolvimento
FLASK_ENV=development
FLASK_DEBUG=True
DATABASE_URL=sqlite:///database/database.db

# Produção
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=chave_super_secreta
```

### Configuração de Logs
```python
import logging

if app.config['DEBUG']:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

---

## 📝 Padrões de Documentação

### Docstrings
```python
def funcao_exemplo(parametro1, parametro2=None):
    """
    Descrição clara do que a função faz.
    
    Args:
        parametro1 (str): Descrição do parâmetro
        parametro2 (int, optional): Parâmetro opcional. Default None.
        
    Returns:
        bool: Descrição do retorno
        
    Raises:
        ValueError: Quando ocorre erro específico
    """
    pass
```

### Comentários
```python
# Comentário explicativo sobre lógica complexa
resultado = calcular_complexo(dados)

# TODO: Implementar cache para melhor performance
# FIXME: Corrigir bug na validação
# NOTE: Este código será refatorado na v3.1
```

---

## 🚀 Padrões de Deploy

### Preparação para Produção
1. **Configurar variáveis de ambiente**
2. **Otimizar assets estáticos**
3. **Configurar banco PostgreSQL**
4. **Definir SECRET_KEY forte**
5. **Desabilitar DEBUG**

### Checklist de Deploy
- [ ] Todas as migrations aplicadas
- [ ] Variáveis de ambiente configuradas
- [ ] SSL/HTTPS configurado
- [ ] Backup do banco configurado
- [ ] Logs configurados
- [ ] Monitoramento ativo

---

## 🔄 Padrões de Versionamento

### Estrutura de Versão
- **Major.Minor.Patch** (ex: 3.1.2)
- **Major**: Mudanças incompatíveis
- **Minor**: Novas funcionalidades
- **Patch**: Correções de bugs

### Changelog
```markdown
## [3.1.0] - 2025-01-XX
### Adicionado
- Módulo de Ordens de Serviço
- API de integração

### Modificado
- Interface do dashboard
- Performance das consultas

### Corrigido
- Bug na validação de CPF
- Erro no cálculo de estoque
```

---

## 📚 Boas Práticas Gerais

### Código Limpo
- Funções pequenas e focadas
- Nomes descritivos
- Evitar comentários óbvios
- Extrair constantes mágicas

### Performance
- Usar índices no banco
- Paginar resultados grandes
- Cache para dados frequentes
- Otimizar queries N+1

### Segurança
- Validar todos os inputs
- Usar prepared statements
- Sanitizar dados de saída
- Implementar rate limiting

### Manutenibilidade
- Testes automatizados
- Documentação atualizada
- Código versionado
- Logs detalhados

---

**JSP Soluções** - Padrão Oficial v3.0
*Garantindo qualidade e consistência no desenvolvimento*