# 📦 Módulos Removidos do ERP JSP

**Data da Remoção:** 26/05/2026  
**Motivo:** Separação de responsabilidades - Módulo Energia Solar movido para aplicação independente

---

## 🎯 **Objetivo da Remoção**

O ERP JSP agora é focado **exclusivamente em:**
- ⚡ **Gestão Elétrica** (equipamentos, ordens de serviço, estoque)
- 💰 **Gestão Financeira** (contas a pagar/receber, fluxo de caixa, relatórios)

O módulo de **Energia Solar** foi separado em uma **aplicação independente** para:
- Melhor manutenibilidade
- Isolamento de funcionalidades
- Facilidade de deploy independente
- Código mais limpo e organizado

---

## 📁 **Módulos Movidos para Backup**

### 🌞 **Energia Solar (app/energia_solar/)**
- `energia_solar_model.py` - Modelo principal de cálculos
- `catalogo_model.py` - Placas, inversores, kits e projetos
- `custo_fixo_model.py` - Custos padrão
- `orcamento_model.py` - Itens de orçamento
- `energia_solar_routes.py` - Rotas principais
- `exportacao_routes.py` - Sistema de exportação/importação
- `proposta_word_service.py` - Geração de propostas Word
- `word_utils.py` - Utilitários Word
- `templates/` - 20+ templates HTML
- `templates_word/` - Templates Word para propostas
- `documentos_gerados/` - Arquivos gerados

### 🏢 **Concessionárias (app/concessionaria/)**
- `concessionaria_model.py` - Modelo de concessionárias
- `concessionaria_routes.py` - Rotas CRUD
- `templates/` - Forms e listagem

### 📦 **Kits Distribuidor (app/kits_distribuidor/)**
- `kits_model.py` - Modelo de kits de distribuidores
- `kits_routes.py` - Rotas de listagem
- `templates/` - Interface de kits

### 📜 **Scripts Relacionados**
- `exportar_energia_solar.py` - Exportação CLI
- `importar_energia_solar.py` - Importação CLI
- `scripts_manutencao/migracoes/sync_calculo_energia_solar.py`
- `scripts_manutencao/correcoes/resetar_energia_solar.py`
- `scripts_manutencao/correcoes/extrair_energia_solar_app.py`

### 📄 **Documentação**
- `MODULO_ENERGIA_SOLAR.md`
- `MAPEAMENTO_ENERGIA_SOLAR_V3.md`
- `LIMPEZA_ENERGIA_SOLAR.md`
- `SOLUCAO_ERRO_500_ENERGIA_SOLAR.md`

---

## ✅ **Alterações no Código Principal**

### **app/app.py**
- ✓ Comentados imports de modelos energia solar
- ✓ Comentados registros de blueprints (energia_solar_bp, exportacao_bp, concessionaria_bp, kits_bp)
- ✓ Comentadas migrações específicas (calculo_energia_solar)

### **app/templates/base.html**
- ✓ Comentado menu "Energia Solar"
- ✓ Comentado JavaScript `toggleEnergiaSolarMenu()`
- ✓ CSS de submenus mantido para reutilização

---

## 🗄️ **Banco de Dados**

**⚠️ IMPORTANTE:** As tabelas de energia solar **NÃO foram excluídas** do banco de dados:
- `calculo_energia_solar`
- `projetos_solar`
- `kits_solar`
- `placas_solar`
- `inversores_solar`
- `custos_padrao_solar`
- `orcamento_itens`

**Motivo:** Preservação de dados históricos e possibilidade de reuso futuro.

---

## 🔄 **Como Restaurar (Se Necessário)**

### **1. Restaurar Módulos**
```powershell
# Mover de volta para app/
Move-Item modulos_removidos/energia_solar app/
Move-Item modulos_removidos/concessionaria app/
Move-Item modulos_removidos/kits_distribuidor app/

# Mover scripts de volta
Move-Item modulos_removidos/exportar_energia_solar.py .
Move-Item modulos_removidos/importar_energia_solar.py .
```

### **2. Descomentar Código**
- Em `app/app.py`: Remover comentários dos imports e registros de blueprints
- Em `app/templates/base.html`: Remover comentários do menu e JavaScript

### **3. Reinstalar Dependências**
```powershell
pip install -r requirements.txt
```

### **4. Testar**
```powershell
python run.py
```

---

## 📊 **Estatísticas da Remoção**

- **60 arquivos** afetados
- **79 inserções** (comentários)
- **77 deleções** (imports, registros)
- **~15.000 linhas de código** movidas
- **0 erros** após remoção

---

## 🚀 **Status Atual do ERP JSP**

✅ **Funcionando perfeitamente com:**
- ⚡ Módulo Equipamentos (produtos, estoque, movimentações)
- 💰 Módulo Financeiro (9 tabelas, contas, lançamentos, relatórios)
- 👥 Módulo Clientes
- 🏭 Módulo Fornecedores
- 📋 Módulo Ordens de Serviço
- 📊 Painel de Controle
- 👤 Sistema de Usuários e Login

---

## 📝 **Notas Finais**

- ✅ Código principal está **limpo e funcional**
- ✅ Separação de responsabilidades implementada
- ✅ Deploy simplificado
- ✅ Manutenção facilitada
- ✅ Dados preservados no banco

**🎯 ERP JSP agora é focado 100% em Gestão Elétrica e Financeira!**
