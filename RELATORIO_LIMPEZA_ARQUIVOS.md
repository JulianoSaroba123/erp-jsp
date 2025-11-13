# 🧹 Relatório de Limpeza de Arquivos - ERP JSP

## 📊 Resumo Executivo
- **Total de arquivos analisados**: ~400+
- **Arquivos candidatos para remoção**: ~350+
- **Categorias identificadas**: 15
- **Espaço estimado liberado**: Significativo (centenas de MB)

---

## 🗂️ Categorias de Arquivos para Limpeza

### 1. 📝 **ARQUIVOS DE TESTE** (Alta Prioridade para Remoção)
```
• teste_*.py (58 arquivos)
• test_*.py (47 arquivos)
• *_teste.py (12 arquivos)
• testar_*.py (21 arquivos)
```

**Exemplos importantes:**
- `teste_botoes.js` ✅ (pode manter temporariamente)
- `teste_calculos.html`
- `teste_ordem_servico.py`
- `test_page.py` ⚠️ (verificar se ainda é usado)
- `testar_botoes_final.py`

### 2. 🔧 **SCRIPTS DE MIGRAÇÃO/ATUALIZAÇÃO** (Média Prioridade)
```
• add_*.py (5 arquivos)
• adicionar_*.py (15 arquivos)
• atualizar_*.py (8 arquivos)
• migrar_*.py (8 arquivos)
• migrate_*.py (2 arquivos)
```

**Candidatos seguros:**
- `add_anexos_columns.py`
- `adicionar_campos_*.py`
- `atualizar_cliente_*.py`
- `migrar_dados.py`

### 3. 🐛 **ARQUIVOS DE DEBUG** (Alta Prioridade)
```
• debug_*.py (27 arquivos)
• check_*.py (23 arquivos)
• verificar_*.py (31 arquivos)
• diagnostico_*.py (4 arquivos)
```

**Candidatos principais:**
- `debug_botoes_os.py`
- `check_all_dbs.py`
- `verificar_banco.py`
- `diagnostico_ordem_servico.py`

### 4. 🔨 **ARQUIVOS DE CORREÇÃO** (Média Prioridade)
```
• corrigir_*.py (15 arquivos)
• correcao_*.py (3 arquivos)
• fix_*.py (16 arquivos)
```

**Exemplos:**
- `corrigir_cliente_*.py`
- `correcao_ordem_servico.py`
- `fix_calculos.js` ⚠️ (pode ter sido incorporado)

### 5. 🏗️ **ARQUIVOS DE BUILD/EXECUTÁVEL** (Baixa Prioridade)
```
• build_*.py (2 arquivos)
• launcher_*.py (8 arquivos)
• ERP_JSP_*.spec (6 arquivos)
• *_dist/ (4 pastas)
```

**Candidatos:**
- `build_exe.py`
- `launcher_*` (vários)
- Pastas: `build/`, `dist/`, `final_dist/`, etc.

### 6. 📄 **ARQUIVOS HTML/JS DE TESTE**
```
• teste_*.html (8 arquivos)
• test_*.html (3 arquivos)
• *.js de teste (2 arquivos)
```

### 7. 🗄️ **ARQUIVOS DE BANCO TEMPORÁRIOS**
```
• criar_*.py (12 arquivos - relacionados a DB)
• *_exemplo.py (4 arquivos)
• *.db temporários (3 arquivos)
```

### 8. 📋 **ARQUIVOS DE DEMONSTRAÇÃO**
```
• demonstracao_*.py (4 arquivos)
• demo_*.py (1 arquivo)
```

### 9. 📊 **ARQUIVOS DE ANÁLISE/RELATÓRIO**
```
• analisar_*.py (1 arquivo)
• analise_*.py (1 arquivo)
• relatorio_*.py (1 arquivo)
• resumo_*.py (5 arquivos)
```

### 10. 🔄 **ARQUIVOS DE LIMPEZA ANTIGOS**
```
• limpar_*.py (6 arquivos)
• limpeza_*.py (1 arquivo)
```

### 11. 🌐 **SERVIDORES DE TESTE**
```
• server_*.py (4 arquivos)
• servidor_*.py (4 arquivos)
• simple_*.py (4 arquivos)
```

### 12. 📁 **ARQUIVOS TEMPORÁRIOS**
```
• temp.html
• *.pdf de teste (3 arquivos)
• db_path
```

### 13. 🔧 **UTILITÁRIOS ÚNICOS**
```
• restart_server.* (2 arquivos)
• force_deploy.txt
• FORCE_UPDATE_NOW.txt
```

### 14. 📈 **ARQUIVOS DE STATUS/RESULTADO**
```
• status_*.py (1 arquivo)
• resultado_*.py (1 arquivo)
```

### 15. 🎨 **ARQUIVOS DE CONFIGURAÇÃO DE TEMA**
```
• configurar_*.py (2 arquivos relacionados a tema)
• resetar_*.py (1 arquivo)
```

---

## ⚠️ **ARQUIVOS CRÍTICOS - NÃO REMOVER**

### Core da Aplicação:
- `app/` (pasta principal)
- `run.py` ✅
- `app.py` ✅
- `requirements.txt` ✅
- `.env` e `.env.example` ✅
- `README.md` ✅
- Arquivos `.md` de documentação ✅

### Scripts Importantes:
- `scripts/criar_tabelas.py` ✅
- `scripts/debug_app.py` ✅
- `scripts/debug.py` ✅

### Configuração:
- `.gitignore` ✅
- `Procfile` ✅
- `render.yaml` ✅
- `runtime.txt` ✅

---

## 🎯 **PLANO DE LIMPEZA RECOMENDADO**

### Fase 1 - Remoção Segura (Imediata):
```bash
# Arquivos de teste óbvios
test_*.py (exceto test_page.py)
teste_*.py (exceto teste_botoes.js temporariamente)
testar_*.py
*_teste.py

# Debug antigos
debug_*.py (manter debug.py e debug_app.py)
check_*.py (manter alguns específicos se necessário)
```

### Fase 2 - Limpeza de Migrações (Após backup):
```bash
add_*.py
adicionar_*.py (arquivos antigos)
migrar_*.py (scripts já executados)
atualizar_*.py (correções já aplicadas)
```

### Fase 3 - Build e Temporários:
```bash
build/
dist/
*_dist/
*.spec (arquivos de build)
launcher_*.py (se não usar executável)
temp.*
*.pdf de teste
```

---

## 📋 **COMANDO DE LIMPEZA SUGERIDO**

Quer que eu crie um script para fazer a limpeza automaticamente? Posso criar categorias:

1. **Limpeza Básica** (100% segura)
2. **Limpeza Intermediária** (99% segura)  
3. **Limpeza Avançada** (95% segura - com backup)

**Espaço estimado liberado**: 60-80% dos arquivos atuais
**Benefícios**: Workspace mais limpo, deploys mais rápidos, menos confusão