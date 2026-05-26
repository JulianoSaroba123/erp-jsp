# 🗑️ LIMPEZA DO MÓDULO ENERGIA SOLAR

## 📊 ANÁLISE REALIZADA

**Data:** 25/05/2026  
**Módulo:** `app/energia_solar/`

---

## ✅ ARQUIVOS EM USO (10 arquivos .py + 22 templates)

### Python Files:
- ✅ `energia_solar_routes.py` - Rotas principais
- ✅ `catalogo_model.py` - ProjetoSolar, KitSolar, PlacaSolar, InversorSolar
- ✅ `energia_solar_model.py` - CalculoEnergiaSolar
- ✅ `custo_fixo_model.py` - CustoPadraoSolar
- ✅ `orcamento_model.py` - OrcamentoItem
- ✅ `proposta_word_service.py` - Geração Word
- ✅ `word_utils.py` - Utilitários Word
- ✅ `__init__.py` - Inicialização do módulo

### Templates HTML Ativos:
- ✅ `dashboard.html` - Dashboard principal
- ✅ `calculadora.html` - Calculadora solar
- ✅ `listar.html` - Lista de cálculos
- ✅ `visualizar.html` - Visualizar cálculo
- ✅ `placas_crud.html` - CRUD de placas (usado por placas_listar)
- ✅ `inversores_crud.html` - CRUD de inversores (usado por inversores_listar)
- ✅ `kits_crud.html` - CRUD de kits (usado por kits_listar)
- ✅ `projetos_lista.html` - Lista de projetos
- ✅ `projeto_dashboard.html` - Dashboard do projeto
- ✅ `projeto_detalhes.html` - Detalhes do projeto
- ✅ `projeto_wizard.html` - Wizard de criação
- ✅ `custos_fixos_lista.html` - Lista de custos fixos
- ✅ `custo_fixo_form.html` - Formulário de custo
- ✅ `chaves_documentos.html` - Chaves de documentos
- ✅ `upload_template_word.html` - Upload de template
- ✅ `admin_recalcular_custos.html` - Admin de custos
- ✅ `pdf_proposta_solar_v2.html` - ⭐ TEMPLATE PDF ATIVO (linha 2607)
- ✅ `pdf_proposta_solar_comercial.html` - PDF comercial (linha 2728)
- ✅ `pdf_projeto_dashboard_v2.html` - PDF dashboard ativo (linha 2947)
- ✅ `_form_placa.html` - Form parcial placa
- ✅ `_form_inversor.html` - Form parcial inversor
- ✅ `_form_kit.html` - Form parcial kit

---

## ❌ ARQUIVOS OBSOLETOS IDENTIFICADOS (6 arquivos)

### Templates HTML Não Usados:

#### 1. `placas_listar.html`
**Status:** ❌ NUNCA USADO  
**Motivo:** A rota `placas_listar()` usa `placas_crud.html` (linha 654)  
**Ação:** DELETAR ✅

#### 2. `inversores_listar.html`
**Status:** ❌ NUNCA USADO  
**Motivo:** A rota `inversores_listar()` usa `inversores_crud.html` (linha 886)  
**Ação:** DELETAR ✅

#### 3. `kits_listar.html`
**Status:** ❌ NUNCA USADO  
**Motivo:** A rota `kits_listar()` usa `kits_crud.html` (linha 1136)  
**Ação:** DELETAR ✅

#### 4. `pdf_proposta_solar.html`
**Status:** ❌ VERSÃO ANTIGA OBSOLETA  
**Motivo:** Substituída por `pdf_proposta_solar_v2.html` (commit bed4a40)  
**Ação:** DELETAR ✅

#### 5. `pdf_proposta_solar_v3.html` ⚠️
**Status:** ❌ VERSÃO INCOMPLETA  
**Motivo:** Tinha apenas 2 de 11 páginas. Revertida para v2 (commit 93d0668)  
**Nota:** Você está com este arquivo aberto no editor  
**Ação:** DELETAR ✅

#### 6. `pdf_projeto_dashboard.html`
**Status:** ❌ VERSÃO ANTIGA OBSOLETA  
**Motivo:** Substituída por `pdf_projeto_dashboard_v2.html` (linha 2947)  
**Ação:** DELETAR ✅

---

## 📈 IMPACTO DA LIMPEZA

**Antes:**
- 28 templates HTML no módulo

**Depois:**
- 22 templates HTML ativos
- **-6 arquivos obsoletos** (limpeza de ~21% dos templates)

**Benefícios:**
- ✅ Código mais limpo e organizado
- ✅ Menos confusão sobre qual versão usar
- ✅ Facilita manutenção futura
- ✅ Reduz tamanho do repositório

---

## ✅ ARQUIVOS DELETADOS

Os seguintes arquivos foram removidos com segurança:

```bash
app/energia_solar/templates/energia_solar/placas_listar.html
app/energia_solar/templates/energia_solar/inversores_listar.html
app/energia_solar/templates/energia_solar/kits_listar.html
app/energia_solar/templates/energia_solar/pdf_proposta_solar.html
app/energia_solar/templates/energia_solar/pdf_proposta_solar_v3.html
app/energia_solar/templates/energia_solar/pdf_projeto_dashboard.html
```

---

## 🎯 RECOMENDAÇÕES

1. ✅ **Manter apenas v2 dos templates PDF** - Está funcionando perfeitamente
2. ✅ **Usar templates _crud.html unificados** - Já está sendo feito
3. ✅ **Documentar mudanças** - Este relatório serve como documentação
4. 📝 **Considerar renomear v2 para sem sufixo** - Opcional, quando estiver 100% estável

---

*Limpeza realizada em: 25/05/2026*  
*Nenhum arquivo em uso foi afetado - operação segura*
