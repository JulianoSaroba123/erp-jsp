# 🗑️ RELATÓRIO COMPLETO DE LIMPEZA DO PROJETO

## 📊 ANÁLISE GERAL

**Data:** 25/05/2026  
**Total de arquivos .py encontrados:** 223

---

## ✅ ARQUIVOS JÁ DELETADOS (6 templates HTML)

- ❌ `app/energia_solar/templates/energia_solar/placas_listar.html`
- ❌ `app/energia_solar/templates/energia_solar/inversores_listar.html`
- ❌ `app/energia_solar/templates/energia_solar/kits_listar.html`
- ❌ `app/energia_solar/templates/energia_solar/pdf_proposta_solar.html`
- ❌ `app/energia_solar/templates/energia_solar/pdf_proposta_solar_v3.html`
- ❌ `app/energia_solar/templates/energia_solar/pdf_projeto_dashboard.html`

---

## 🗂️ CATEGORIZAÇÃO DE ARQUIVOS OBSOLETOS

### 📋 CATEGORIA 1: Scripts de Migração/Adição de Colunas (35 arquivos)
**Descrição:** Scripts usados UMA VEZ para adicionar colunas ao banco  
**Status:** ❌ OBSOLETOS - Não precisam mais ser executados  
**Ação:** DELETAR (mover para pasta `scripts_historico/` se quiser manter histórico)

```
adicionar_datasheet.py
adicionar_coluna_datasheet.py
adicionar_coluna_conteudo.py
adicionar_colaborador_os2.py
adicionar_campos_horarios_detalhados.py
adicionar_campos_financeiros_projeto.py
adicionar_tipo_os_render.py
adicionar_tipo_instalacao.py
adicionar_proposta_id.py
adicionar_numero_projeto_solar.py
adicionar_numero_endereco.py
adicionar_logo_base64.py
adicionar_kit_id_coluna.py
adicionar_intervalo_almoco.py
adicionar_datasheet_render.py
adicionar_variaveis_ao_template_usuario.py
ativar_os_render.py
configurar_colaborador_flask.py
configurar_colaborador.py
converter_os2_operacional.py
converter_logo_existente.py
corrigir_campo_ativo_os.py
corrigir_campo_ativo_render.py
corrigir_cliente_20_render.py
corrigir_formato_logo.py
corrigir_logo_base64.py
corrigir_logo_render.py
corrigir_logo_shell_render.py
corrigir_os_sem_lancamento.py
corrigir_paths_datasheets.py
corrigir_projeto_solar_render.py
corrigir_projetos_kit.py
corrigir_tipo_horas.py
corrigir_valores_os.py
atualizar_financeiro_direto.py
atualizar_placa_dm585.py
atualizar_projeto_direto.py
atualizar_tipo_usuario_render.py
```

### 📋 CATEGORIA 2: Scripts de Teste/Debug (40 arquivos)
**Descrição:** Scripts criados para testar funcionalidades específicas  
**Status:** ⚠️ MAIORIA OBSOLETA - Foram usados para debug pontual  
**Ação:** DELETAR os de debug pontual, MANTER os úteis para validação

**DELETAR (30):**
```
testar_visualizar_proposta.py
testar_url_render.py
testar_upload_logo.py
testar_upload_datasheet.py
testar_to_dict.py
testar_salvamento_padrao.py
testar_rota_proposta.py
testar_query_listar.py
testar_pwa.py
testar_pdf_projeto_6.py
testar_pdf_projeto_5.py
testar_pdf_projeto_2.py
testar_login.py
testar_erro_cliente_20.py
testar_energia_solar_render.py
testar_cliente_listagem.py
testar_cliente.py
testar_cadastro_cliente.py
testar_autocomplete.py
testar_get_placa.py
teste_sqlite.py
teste_login_direto.py
teste_layout_placas.py
teste_diagnostico.py
analisar_html_proposta.py
check_os_status.py
check_os_tipo.py
check_projeto_4.py
check_render_error.py
check_routes.py
check_tipo_mismatch.py
check_tipos_os.py
```

**MANTER (10):**
```
testar_placeholders_word.py ✅ (criado recentemente, útil)
testar_geracao_proposta_word.py ✅ (criado recentemente, útil)
testar_integracao_os_financeiro.py ✅ (teste importante)
testar_aliases_word.py ✅ (criado recentemente, útil)
validar_placeholders_word.py ✅ (criado recentemente, útil)
inspecionar_template_word.py ✅ (criado recentemente, útil)
listar_placeholders_word.py ✅ (criado recentemente, útil)
validate_solar.py ✅ (validação importante)
verificacao_completa.py ✅ (validação importante)
test_page.py ✅ (teste de rotas principais)
```

### 📋 CATEGORIA 3: Scripts de Diagnóstico Pontuais (20 arquivos)
**Descrição:** Scripts criados para diagnosticar problemas específicos no Render  
**Status:** ❌ OBSOLETOS - Problemas já foram resolvidos  
**Ação:** DELETAR

```
diagnostico_projetos_render.py
diagnostico_placas_render.py
diagnostico_os_completo.py
diagnostico_login.py
diagnostico_layout_render.py
diagnostico_kits.py
diagnostico_anexos.py
diagnosticar_os_financeiro.py
diagnosticar_cliente_20.py
diagnostico_status_os.py
diagnostico_render_energia.py
diagnostico_render.py
procurar_os_render.py
forcar_deploy_render.py
forcar_bifasico_render.py
setup_render.py
setup_colaborador_completo.py
criar_admin_render.py
popular_projeto_6_render.py
popular_equipamentos_render.py
```

### 📋 CATEGORIA 4: Scripts de Importação de Dados (15 arquivos)
**Descrição:** Scripts usados para migrar dados entre ambientes  
**Status:** ⚠️ PODEM SER ÚTEIS para migrações futuras  
**Ação:** MOVER para `scripts_manutencao/importacao/` (já existe uma pasta)

```
importar_tudo_ordem_correta.py
importar_todos_dados_render.py
importar_para_render.py
importar_os_local_para_render.py
importar_os_com_mapeamento.py
importar_erp_db_para_render.py
importar_dados_render_simples.py
importar_completo_render.py
sync_render_to_local.py
popular_banco_inicial.py
criar_banco_limpo.py
criar_banco_minimo.py
criar_banco_postgres.py
criar_banco_simples.py
criar_tabelas.py
```

### 📋 CATEGORIA 5: Scripts de Build/Launcher Obsoletos (10 arquivos)
**Descrição:** Múltiplas versões de launchers e builders  
**Status:** ⚠️ MANTER APENAS A VERSÃO MAIS RECENTE  
**Ação:** DELETAR versões antigas

**DELETAR (8):**
```
launcher.py (versão antiga)
launcher_simples.py (versão antiga)
launcher_pro_simples.py (versão antiga)
jsp_launcher.py (versão antiga)
build_jsp_exe.py (versão antiga)
build_simples.py (versão antiga)
app.py (duplicado do run.py)
server.py (duplicado)
```

**MANTER (2):**
```
launcher_profissional.py ✅ (versão atual)
jsp_launcher_v3.py ✅ (versão atual)
build_launcher_profissional.py ✅ (versão atual)
build_professional.py ✅ (versão atual)
```

### 📋 CATEGORIA 6: Scripts de Análise de Templates Word (5 arquivos)
**Descrição:** Scripts para encontrar/verificar placeholders em templates  
**Status:** ⚠️ CONSOLIDAR - Muitas versões fazendo a mesma coisa  
**Ação:** DELETAR versões antigas

**DELETAR (4):**
```
find_placeholders.py (versão antiga)
find_placeholders_v2.py (versão antiga)
find_placeholders_v3.py (versão antiga)
verify_placeholders.py (versão antiga)
normalize_placeholders.py (versão antiga)
extrair_variaveis_word.py (duplicado)
```

**MANTER (3):**
```
validar_placeholders_word.py ✅ (versão atual completa)
listar_placeholders_word.py ✅ (útil)
inspecionar_template_word.py ✅ (útil)
```

### 📋 CATEGORIA 7: Scripts de Listagem/Ver Dados (10 arquivos)
**Descrição:** Scripts simples para ver estrutura do banco  
**Status:** ⚠️ CONSOLIDAR - Muitos fazem a mesma coisa  
**Ação:** DELETAR versões duplicadas

**DELETAR (6):**
```
ver_tabelas_erp_db.py
ver_tabelas.py
ver_estrutura.py
ver_colunas.py
listar_tabelas.py
listar_propostas.py (script raiz - existe em scripts/)
listar_projetos.py
```

**MANTER (2):**
```
scripts/listar_propostas.py ✅ (versão em pasta correta)
scripts/diagnostico_estrutura_banco.py ✅ (mais completo)
```

### 📋 CATEGORIA 8: Scripts de Geração Específica (3 arquivos)
**Descrição:** Scripts para gerar propostas/documentos específicos  
**Status:** ❌ OBSOLETOS - Casos pontuais  
**Ação:** DELETAR

```
gerar_proposta_alessandro.py
gerar_icones_pwa.py (já tem ícones gerados)
deploy_pwa.py (obsoleto)
```

### 📋 CATEGORIA 9: Scripts de Reset/Reconfiguração (10 arquivos)
**Descrição:** Scripts para resetar partes do sistema  
**Status:** ⚠️ MANTER com cautela - Podem ser úteis  
**Ação:** MANTER em `scripts_manutencao/`

**MOVER para scripts_manutencao/ (não deletar):**
```
resetar_energia_solar.py
resetar_admin.py
resetar_login_completo.py
sync_calculo_energia_solar.py
recalcular_valores_colaboradores.py
recalcular_custos_projetos.py
inicializar_logo_padrao.py
menu_sync_db.py
```

---

## 📊 RESUMO DA LIMPEZA RECOMENDADA

| Categoria | Total | Deletar | Mover | Manter |
|-----------|-------|---------|-------|--------|
| **1. Migração/Adição Colunas** | 35 | 35 | 0 | 0 |
| **2. Teste/Debug** | 40 | 30 | 0 | 10 |
| **3. Diagnóstico Pontual** | 20 | 20 | 0 | 0 |
| **4. Importação Dados** | 15 | 0 | 15 | 0 |
| **5. Build/Launcher** | 10 | 8 | 0 | 2 |
| **6. Templates Word** | 7 | 4 | 0 | 3 |
| **7. Listagem/Ver Dados** | 10 | 6 | 0 | 4 |
| **8. Geração Específica** | 3 | 3 | 0 | 0 |
| **9. Reset/Reconfig** | 10 | 0 | 10 | 0 |
| **10. Templates HTML** | 6 | 6 | 0 | 0 |
| **TOTAIS** | **156** | **112** | **25** | **19** |

---

## 🎯 RECOMENDAÇÕES DE AÇÃO

### ✅ AÇÃO IMEDIATA (112 arquivos para deletar)
```powershell
# Ver lista completa no arquivo: ARQUIVOS_PARA_DELETAR.txt
```

### 📦 AÇÃO SECUNDÁRIA (25 arquivos para mover)
Mover scripts de importação/reset para subpastas organizadas

### ✅ AÇÃO FINALIZADA
- 6 templates HTML obsoletos JÁ FORAM DELETADOS ✅

---

## 💾 BACKUP

**IMPORTANTE:** Antes de deletar, certifique-se de que tem backup!
```bash
git add .
git commit -m "backup antes da limpeza"
git push
```

---

*Relatório gerado em: 25/05/2026*
