# 🚀 ERP JSP - Automação Industrial e Solar

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![Licença](https://img.shields.io/badge/licen%C3%A7a-Privado-blueviolet)

Sistema ERP desenvolvido para a gestão completa da empresa **JSP Elétrica Industrial & Solar**, com foco em:

- Gestão de clientes
- Cadastro de produtos
- Ordens de serviço técnicas
- Login com autenticação
- Painel com gráficos e dashboard
- Interface responsiva e profissional

---

## 📸 Interface do Sistema

> Tela de login com identidade visual personalizada e painel administrativo com cards, gráficos e tabela de OS.

![Tela do Sistema - Login](https://via.placeholder.com/800x400?text=Prévia+Login+ERP+JSP)

*(Substitua pela imagem ou GIF real do sistema assim que disponível)*

---

## 🧱 Estrutura do Projeto

```bash
ERP_JSP/
├── aplicacao/
│   ├── painel/
│   ├── autenticacao/
│   ├── clientes/
│   ├── produtos/
│   ├── ordens_servico/
│   ├── fornecedores/
│   ├── __init__.py
│   ├── configuracoes.py
│   └── extensoes.py
├── static/
│   ├── imagens/
│   │   └── logo_atualizado.png
│   └── ...
├── templates/
│   └── base.html
├── run.py
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Tecnologias Utilizadas

- Python 3.10+
- Flask
- Jinja2
- SQLAlchemy
- Bootstrap 5
- Chart.js
- Git + GitHub

---

## 🚀 Como Executar o Projeto

1. Instale os pacotes:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o sistema localmente:
   ```bash
   python run.py
   ```

3. Acesse no navegador:
   ```
   http://localhost:5000
   ```

---

## 📊 Funcionalidades atuais

- Login com tela personalizada e logo
- Painel inicial com cards de resumo
- Gráficos de faturamento e ordens de serviço
- Tabela com últimas OS e alertas
- Estrutura modular para expansão futura

---

## 📌 Próximas funcionalidades

- Integração com banco de dados real
- Cadastro de usuários com permissões
- Emissão de relatórios em PDF
- Integração com API externa (ex: ViaCEP)
- Deploy no Render

---

## 🤝 Como Contribuir

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/erp-jsp.git
   ```
2. Crie uma branch:
   ```bash
   git checkout -b minha-feature
   ```
3. Faça suas alterações e commit:
   ```bash
   git commit -m "minha melhoria"
   ```
4. Envie a branch:
   ```bash
   git push origin minha-feature
   ```
5. Abra um Pull Request

---

## 🧪 Executando os testes locais e scripts

Alguns scripts de teste no diretório `scripts/` (ex: `scripts/test_api.py`) importam o pacote local `aplicacao`.
Para que esses imports funcionem, execute os scripts a partir da raiz do projeto (onde está o `README.md`).

Exemplo (PowerShell):

```powershell
cd C:\Users\julia\Desktop\ERP_JSP
python scripts/test_api.py
```

Alternativa para CI: configurar a variável de ambiente `PYTHONPATH` apontando para a raiz do repositório ou usar um módulo de teste via `python -m scripts.test_api` após transformar `scripts` em um package.


## 🔐 Licença

Este é um projeto privado de uso interno, desenvolvido exclusivamente para a **JSP Elétrica Industrial e Solar**.

---

> Desenvolvido com 💡 por Juliano Saroba e seu Engenheiro Virtual 🤖

ERP para controle de propostas, ordens de serviço e financeiro, voltado para empresas do setor industrial e de energia solar.
