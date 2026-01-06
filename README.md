# 🚀 ERP JSP v3.0

Sistema de Gestão Empresarial moderno e completo desenvolvido com Flask, Bootstrap 5 e tema futurista escuro.

## 📋 Características Principais

- ✅ **Arquitetura Modular**: Blueprints organizados por funcionalidade
- ✅ **Tema Futurista**: Interface escura com detalhes em azul ciano
- ✅ **Responsivo**: Bootstrap 5 com design mobile-first
- ✅ **Base Sólida**: SQLAlchemy + Migrations + Validações
- ✅ **Documentação Completa**: Código 100% comentado

## 🏗️ Estrutura do Projeto

```
ERP_JSP/
├── app/
│   ├── __init__.py
│   ├── app.py                  # Factory da aplicação
│   ├── config.py              # Configurações do sistema
│   ├── extensoes.py           # Extensões Flask
│   ├── models.py              # Models base
│   ├── static/                # CSS, JS, imagens
│   ├── templates/
│   │   ├── base.html          # Template base futurista
│   │   └── errors/            # Páginas de erro
│   ├── cliente/               # Módulo de clientes
│   │   ├── cliente_model.py
│   │   ├── cliente_routes.py
│   │   └── templates/cliente/
│   ├── fornecedor/            # Módulo de fornecedores
│   │   ├── fornecedor_model.py
│   │   ├── fornecedor_routes.py
│   │   └── templates/fornecedor/
│   ├── produto/               # Módulo de produtos
│   │   ├── produto_model.py
│   │   ├── produto_routes.py
│   │   └── templates/produto/
│   └── painel/                # Dashboard principal
│       ├── painel_routes.py
│       └── templates/painel/
├── database/                  # Banco de dados SQLite
├── scripts/                   # Scripts de manutenção
│   ├── criar_tabelas.py
│   └── debug_app.py
├── .env.example              # Configurações de ambiente
├── requirements.txt          # Dependências Python
└── run.py                   # Ponto de entrada
```

## 🛠️ Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd ERP_JSP
```

### 2. Crie o Ambiente Virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configure o Ambiente
```bash
# Copie o arquivo de exemplo
copy .env.example .env

# Edite o arquivo .env com suas configurações
```

### 5. Crie as Tabelas do Banco
```bash
python scripts/criar_tabelas.py
```

### 6. Execute a Aplicação
```bash
python run.py
```

A aplicação estará disponível em `http://localhost:5000`

## ⚙️ Configuração de Banco de Dados

### SQLite (Desenvolvimento)
```env
DATABASE_URL=sqlite:///database/database.db
```

### PostgreSQL (Produção e Desenvolvimento Local)
```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/erp_jsp
```

## 🔌 Integração com API do Distribuidor

O ERP JSP possui integração nativa com API de distribuidores de kits fotovoltaicos.

### Configuração da API

1. **Obtenha o Token de Acesso**
   - Entre em contato com seu distribuidor
   - Solicite um token de API para integração
   - O distribuidor fornecerá:
     - URL base da API (ex: `https://api.distribuidor.com/v1`)
     - Token de autenticação (Bearer Token)

2. **Configure as Variáveis de Ambiente**
   
   Adicione ao arquivo `.env`:
   ```env
   # API Distribuidor de Kits Fotovoltaicos
   DISTRIBUIDOR_API_URL=https://api.distribuidor.com/v1
   DISTRIBUIDOR_API_TOKEN=seu_token_aqui
   DISTRIBUIDOR_API_TIMEOUT=30
   ```

3. **Teste a Conexão**
   - Acesse: Menu **Energia Solar > Kits Distribuidor**
   - Clique em "Testar API"
   - Se configurado corretamente, verá mensagem de sucesso

4. **Sincronize os Kits**
   - Clique em "Sincronizar Kits"
   - O sistema importará todos os kits disponíveis
   - Os dados serão salvos localmente no banco de dados
   - Você pode re-sincronizar a qualquer momento para atualizar preços e disponibilidade

### Funcionalidades da Integração

- ✅ **Sincronização Automática**: Importa kits com um clique
- ✅ **Filtros Avançados**: Busca por potência, categoria, fabricante
- ✅ **Atualização em Tempo Real**: Preços e disponibilidade sempre atualizados
- ✅ **Cache Local**: Kits salvos no banco para acesso offline
- ✅ **Paginação**: Suporte para grandes catálogos
- ✅ **Tratamento de Erros**: Mensagens claras em caso de problemas

### Segurança

⚠️ **IMPORTANTE**: Nunca commite o arquivo `.env` com seu token!

O token de API é sensível e deve ser mantido em segredo. O arquivo `.env` já está no `.gitignore` para proteger suas credenciais.

## 🎨 Tema Visual

### Cores Principais
- **Primary**: `#00d4ff` (Azul ciano)
- **Secondary**: `#0099cc` (Azul escuro)
- **Background**: `#0a0a0a` (Preto)
- **Cards**: `#151515` (Cinza escuro)

### Componentes
- **Navbar**: Backdrop blur com bordas ciano
- **Cards**: Bordas arredondadas com hover effects
- **Botões**: Gradientes e animações
- **Formulários**: Inputs com glow effect
- **Tabelas**: Dark mode com hover highlights

## 📱 Módulos Implementados

### ✅ Cliente
- CRUD completo (Create, Read, Update, Delete)
- Validação de CPF/CNPJ
- Busca avançada
- Formulários responsivos
- Máscaras automáticas

### ✅ Fornecedor
- Gestão de fornecedores PF/PJ
- Dados comerciais e contato
- Categorização
- Filtros por categoria

### ✅ Produto
- Controle de estoque
- Gestão de preços e margens
- Códigos e códigos de barras
- Alertas de estoque baixo
- Categorização

### ✅ Dashboard
- Estatísticas em tempo real
- Cards informativos
- Ações rápidas
- Produtos com estoque baixo
- Valor total do estoque

## 📋 Módulos Futuros (v3.1+)

### 🔄 Ordem de Serviço
- Gestão de OS
- Controle de status
- Relatórios de produtividade

### 💰 Financeiro
- Contas a pagar/receber
- Fluxo de caixa
- Relatórios financeiros

### 💲 Precificação
- Cálculo de preços
- Análise de margem
- Simulações

### 🔍 Prospecção
- Busca de empresas por CNPJ
- Análise de CNAE
- Lead generation

## 🔧 Scripts Úteis

### Criar Tabelas
```bash
python scripts/criar_tabelas.py
```

### Debug da Aplicação
```bash
python scripts/debug_app.py
```

### Atualizar Banco (Futuro)
```bash
python scripts/atualizar_banco.py
```

## 🚀 Deploy no Render

### 1. Prepare o Ambiente
```env
# .env para produção
FLASK_ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=sua_chave_super_secreta
```

### 2. Configure o Render
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python run.py`
- **Environment**: Python 3

### 3. Variáveis de Ambiente
Adicione no painel do Render:
- `DATABASE_URL`: URL do PostgreSQL
- `SECRET_KEY`: Chave secreta forte
- `FLASK_ENV`: production

## 📚 API Endpoints

### Clientes
- `GET /cliente/` - Listar clientes
- `GET /cliente/novo` - Formulário novo cliente
- `POST /cliente/novo` - Criar cliente
- `GET /cliente/<id>` - Visualizar cliente
- `GET /cliente/<id>/editar` - Formulário editar
- `POST /cliente/<id>/editar` - Atualizar cliente
- `GET /cliente/<id>/excluir` - Excluir cliente
- `GET /cliente/api/buscar` - API busca (JSON)

### Fornecedores
- Mesma estrutura dos clientes em `/fornecedor/`

### Produtos
- Mesma estrutura em `/produto/`
- `GET /produto/estoque-baixo` - Produtos com estoque baixo

### Dashboard
- `GET /` ou `/dashboard` - Dashboard principal

## 🎯 Padrões de Desenvolvimento

### Models
```python
class MinhaEntidade(BaseModel):
    """Documentação da entidade."""
    __tablename__ = 'minha_tabela'
    
    # Campos
    nome = db.Column(db.String(100), nullable=False)
    
    # Propriedades
    @property
    def nome_display(self):
        return self.nome.title()
    
    # Métodos de classe
    @classmethod
    def buscar_por_nome(cls, nome):
        return cls.query.filter(cls.nome.ilike(f'%{nome}%')).all()
```

### Routes
```python
@blueprint.route('/rota')
def funcao():
    """Documentação da rota."""
    try:
        # Lógica aqui
        return render_template('template.html')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('blueprint.index'))
```

### Templates
```html
{% extends "base.html" %}

{% block title %}Título - {{ super() }}{% endblock %}

{% block breadcrumb %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/">Dashboard</a></li>
        <li class="breadcrumb-item active">Página</li>
    </ol>
</nav>
{% endblock %}

{% block content %}
<!-- Conteúdo aqui -->
{% endblock %}
```

## 🐛 Troubleshooting

### Erro de Import
```bash
# Verifique se está no diretório correto
cd ERP_JSP
python run.py
```

### Banco não Criado
```bash
# Execute o script de criação
python scripts/criar_tabelas.py
```

### Erro de Dependências
```bash
# Reinstale as dependências
pip install -r requirements.txt --force-reinstall
```

## 👥 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

---

## 📞 Suporte

**JSP Soluções**
- 📧 Email: contato@jspsolutions.com.br
- 🌐 Website: https://jspsolutions.com.br
- 📱 WhatsApp: (11) 99999-9999

---

**ERP JSP v3.0** - Sistema de Gestão Empresarial Moderno
*Desenvolvido com ❤️ por JSP Soluções*