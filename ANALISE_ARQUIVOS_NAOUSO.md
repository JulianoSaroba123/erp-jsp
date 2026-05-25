# 📋 ANÁLISE DE ARQUIVOS NÃO UTILIZADOS - ERP JSP v3.0

**Data da Análise:** 25/05/2026  
**Objetivo:** Identificar arquivos que não afetam o funcionamento do sistema

---

## 📌 RESUMO EXECUTIVO

### Arquivos Essenciais (NÃO DELETAR):
- `run.py` - Ponto de entrada principal
- `app/` - Pasta principal da aplicação
- `app/app.py` - Factory da aplicação Flask
- `app/config.py` - Configurações do sistema
- `requirements.txt` - Dependências Python
- `.env` - Variáveis de ambiente
- `database/` - Banco de dados SQLite local
- `erp.db` - Banco SQLite principal
- `Procfile` - Configuração para deploy Render
- `render.yaml` - Configuração para deploy Render
- `runtime.txt` - Versão do Python para Render
- `🚀 INICIAR ERP JSP.bat` - Launcher principal do sistema

### Total de Arquivos Não Essenciais: **~150 arquivos**

---

## 🗂️ CATEGORIA 1: SCRIPTS DE DEBUG E DIAGNÓSTICO (25 arquivos)
**Descrição:** Scripts usados apenas para troubleshooting e debugging  
**Impacto no Sistema:** ❌ ZERO - Não afetam o funcionamento  
**Ação Sugerida:** ✅ PODEM SER MOVIDOS para `scripts_manutencao/debug/` ou DELETADOS

```
debug_cliente.py
debug_login.py
debug_projeto_dados.py
debug_proposta.py
debug_query_render.py
debug_render_completo.py
diagnosticar_projeto_8.py
test_autocomplete_final.py
test_cliente_debug.py
test_cnpj_api.py
test_equipamentos.py
test_final.py
test_fornecedor_autocomplete.py
test_http.py
test_imports.py
test_modelo_orm_render.py
test_produtos_os.py
test_render.py
test_snippet.py
test_url.py
verificacao_completa.py
validate_solar.py
diagnostico_navegador.html
teste_kit.html
comparar_projetos.py
```

---

## 🗂️ CATEGORIA 2: SCRIPTS DE MIGRAÇÃO/IMPORTAÇÃO (30 arquivos)
**Descrição:** Scripts usados para migrar dados entre ambientes  
**Impacto no Sistema:** ❌ ZERO - Foram usados apenas durante migrações passadas  
**Ação Sugerida:** ⚠️ MOVER para `scripts_manutencao/migracoes/` (podem ser úteis no futuro)

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
sync_calculo_energia_solar.py
popular_banco_inicial.py
migrar_anexos_blob.py
migrar_completo_render.py
migrar_dados_render.py
migrar_horarios_detalhados_postgres.py
migrar_intervalo_almoco_flask.py
migrar_os_para_render.py
migrar_os_sqlalchemy.py
migrar_plano_contas_render.py
migrar_schema_completo_render.py
migrar_status_ordens.py
migrate_db.py
menu_sync_db.py
fix_cliente_20_render.sh
fix_render.sh
fix_db_final.py
fix_db_render_agora.py
fix_logo_render.py
fix_render_campos_faltantes.py
fix_render_projetos.py
```

---

## 🗂️ CATEGORIA 3: SCRIPTS DE VERIFICAÇÃO E TESTES (40 arquivos)
**Descrição:** Scripts para verificar estrutura do banco e dados  
**Impacto no Sistema:** ❌ ZERO - Apenas consultam dados  
**Ação Sugerida:** ✅ MOVER para `scripts_manutencao/verificacao/` ou DELETAR

```
verificar_admin_render.py
verificar_banco_local.py
verificar_banco_render.py
verificar_campos_padrao.py
verificar_clientes_render.py
verificar_colaboradores_os2.py
verificar_colaboradores_sistema.py
verificar_colabs_final.py
verificar_datasheets.py
verificar_deploy_render.py
verificar_erro_render.py
verificar_estrutura.py
verificar_estrutura_bancos.py
verificar_e_corrigir_ativo.py
verificar_e_corrigir_logo_render.py
verificar_logo_atual.py
verificar_logo_db.py
verificar_nome_fantasia.py
verificar_placa.py
verificar_precos_kits.py
verificar_projeto_2.py
verificar_projeto_6.py
verificar_proposta_render.py
verificar_render_agora.py
verificar_status_ordens.py
verificar_status_render.py
verificar_tipo_usuario.py
verificar_ultimo_cliente.py
verificar_usuarios_simples.py
verify_placeholders.py
ver_colunas.py
ver_estrutura.py
ver_tabelas.py
ver_tabelas_erp_db.py
listar_projetos.py
listar_propostas.py
listar_tabelas.py
listar_todos_projetos.py
find_placeholders.py
find_placeholders_v2.py
find_placeholders_v3.py
```

---

## 🗂️ CATEGORIA 4: SCRIPTS DE CRIAÇÃO DE DADOS EXEMPLO (15 arquivos)
**Descrição:** Scripts para popular banco com dados de teste  
**Impacto no Sistema:** ❌ ZERO - Apenas criam dados exemplo  
**Ação Sugerida:** ⚠️ MOVER para `scripts_manutencao/exemplos/` (úteis para testes)

```
criar_colaboradores_exemplo.py
criar_contas_bancarias.py
criar_contas_render.py
criar_equipamentos_exemplo.py
criar_equipamentos_render.py
criar_servicos_exemplo.py
criar_tabela_custos_fixos.py
criar_tabela_energia_solar.py
criar_tabela_kits.py
criar_tabela_unidades_consumidoras.py
criar_tabelas_energia_solar_completo.py
criar_template_word_completo.py
criar_usuario_colaborador.py
criar_usuario_rapido.py
criar_banco_postgres.py
```

---

## 🗂️ CATEGORIA 5: SCRIPTS DE RECÁLCULO E ATUALIZAÇÃO (10 arquivos)
**Descrição:** Scripts para recalcular valores e corrigir dados  
**Impacto no Sistema:** ❌ ZERO - Usados apenas uma vez para correções  
**Ação Sugerida:** ⚠️ MOVER para `scripts_manutencao/correcoes/`

```
recalcular_custos_projetos.py
recalcular_valores_colaboradores.py
resetar_admin.py
resetar_energia_solar.py
resetar_login_completo.py
inicializar_logo_padrao.py
normalize_placeholders.py
sql_render_add_conteudo.py
extrair_energia_solar_app.py
extrair_variaveis_word.py
```

---

## 🗂️ CATEGORIA 6: LAUNCHERS ALTERNATIVOS (8 arquivos)
**Descrição:** Versões alternativas de launchers  
**Impacto no Sistema:** ⚠️ BAIXO - O único usado é `🚀 INICIAR ERP JSP.bat`  
**Ação Sugerida:** ✅ MOVER para `launchers_alternativos/` ou DELETAR

```
launcher.py
launcher_profissional.py
launcher_pro_simples.py
launcher_simples.py
jsp_launcher.py
jsp_launcher_v3.py
ERP_JSP.bat
EXECUTAR_ERP_JSP.bat
```

**NOTA:** O launcher principal usado é `🚀 INICIAR ERP JSP.bat`

---

## 🗂️ CATEGORIA 7: ARQUIVOS EXECUTÁVEIS (.exe) (4 arquivos)
**Descrição:** Executáveis compilados com PyInstaller  
**Impacto no Sistema:** ❌ ZERO - Versões standalone  
**Ação Sugerida:** ⚠️ MOVER para `dist/` ou DELETAR (ocupam muito espaço)

```
ERP_JSP_Professional.exe (~150 MB)
ERP_JSP_SIMPLES.exe
JSP_Sistema_FUNCIONAL.exe
launcher_config.ini
```

---

## 🗂️ CATEGORIA 8: PASTAS DE BUILD E TEMPORÁRIOS
**Descrição:** Arquivos gerados durante build e execução  
**Impacto no Sistema:** ❌ ZERO - Gerados automaticamente  
**Ação Sugerida:** ✅ PODEM SER DELETADOS (são regenerados automaticamente)

```
build/                  (pasta de build do PyInstaller)
build_temp/             (arquivos temporários de build)
dist/                   (distribuíveis do PyInstaller)
temp_docx/              (arquivos temporários de Word)
temp_docx_check/        (verificação de Word)
temp_docx.zip
temp_docx_check.zip
instance/               (instância Flask - pode ser regenerado)
__pycache__/            (cache Python - em várias pastas)
```

---

## 🗂️ CATEGORIA 9: ARQUIVOS DE BACKUP (.db antigos) (2 arquivos)
**Descrição:** Backups antigos do banco de dados  
**Impacto no Sistema:** ❌ ZERO - Apenas backups  
**Ação Sugerida:** ⚠️ MOVER para `backups/` ou DELETAR

```
erp_OLD_20260105_140114.db
test.db
```

---

## 🗂️ CATEGORIA 10: ARQUIVOS SQL E SCRIPTS DIVERSOS (5 arquivos)
**Descrição:** Scripts SQL e utilitários diversos  
**Impacto no Sistema:** ❌ ZERO - Usados apenas manualmente  
**Ação Sugerida:** ✅ MOVER para `scripts_manutencao/sql/`

```
adicionar_datasheet.sql
fix_db_render.sql
deletar_arquivos_obsoletos.ps1
sincronizar_render.bat
run_migration_render.sh
```

---

## 🗂️ CATEGORIA 11: ARQUIVOS DE DOCUMENTAÇÃO (.md) (60+ arquivos)
**Descrição:** Documentação técnica e guias  
**Impacto no Sistema:** ❌ ZERO - Apenas documentação  
**Ação Sugerida:** ⚠️ MANTER - São úteis para consulta (não afetam funcionamento)

```
AJUSTE_VALOR_KIT_CUSTOS.md
ANALISE_SISTEMA_FINANCEIRO_COMPLETA.md
APLICAR_NO_RENDER.md
BACKLOG_FINANCEIRO.md
check_render_logs.md
COMANDO_RENDER_DIRETO.md
COMO_CORRIGIR_DATASHEET.md
COMO_INSTALAR_APP.md
CORRECAO_AUTOCOMPLETE_FORNECEDOR.md
CORRECAO_CONTAGEM_ORDENS.md
CORRECAO_DROPDOWN_EQUIPAMENTOS.md
CORRECAO_ESTRUTURA_PROPOSTAS.md
CORRECAO_LAYOUT_PLACAS_RENDER.md
CORRECAO_LOGIN_LOOP.md
CORRECAO_LOGO_PDF.md
CORRECOES_IMPLEMENTADAS.md
DEPLOY_RAPIDO.md
DIAGNOSTICO_BUGS.md
diagnostico_render.md
DISTINCAO_CONTAS_PAGAR_CUSTOS_FIXOS.md
ESTRUTURA_PDF_COMPLETO.md
EXEMPLOS_CUSTOS_FIXOS.md
FASE2_INTERFACE_VISUAL.md
FIX_CLIENTE_20_RENDER.md
FIX_CONTAS_BANCARIAS.md
FIX_DADOS_FINANCEIROS_RENDER.md
GUIA_ADICIONAR_COLUNA_RENDER.md
GUIA_CORRECAO_ERRO_500_PROJETOS.md
GUIA_LOGO.md
GUIA_MIGRACAO_DEFINITIVA.md
GUIA_PWA.md
GUIA_RAPIDO_CORRECAO.md
GUIA_RENDER_DBEAVER.md
GUIA_WIZARD_MELHORADO.md
INSTRUCOES_MIGRACAO_RENDER.md
LIMPEZA_ENERGIA_SOLAR.md
MANUAL_USUARIO.md
MAPEAMENTO_ENERGIA_SOLAR_V3.md
MELHORIAS_IMPLEMENTADAS_20260512.md
MIGRACAO_CAMPOS_PROPOSTA.md
MIGRACAO_README.md
MIGRACAO_STATUS.md
MIGRAR_RENDER_INTERVALO.md
MODULO_CONCILIACAO_BANCARIA.md
MODULO_CUSTOS_FIXOS.md
MODULO_DRE.md
MODULO_ENERGIA_SOLAR.md
MODULO_FLUXO_CAIXA.md
MODULO_NFSE_COMPLETO.md
MODULO_SERVICOS_COMPLETO.md
NOVAS_FUNCIONALIDADES_v3.1.md
PARCELAMENTO_PROPOSTAS.md
PLACEHOLDERS_WORD_VALIDADO.md
PROBLEMAS_PROJETOS_NOVOS.md
PROBLEMA_OS_FINANCEIRO.md
PROFISSIONALIZACAO_PDF_PROPOSTA.md
PROJETO_6_IDS_NULL.md
PWA_INICIO_RAPIDO.md
README.md (ESSENCIAL - MANTER)
RELATORIO_ENGENHARIA.md
RELATORIO_LIMPEZA_COMPLETO.md
RELATORIO_PLACEHOLDERS_WORD.md
RENDER_32_COLUNAS_HOTFIX.md
RESOLUCAO_PROBLEMAS_FINANCEIRO.md
SISTEMA_ADICIONAIS_HORAS.md
SISTEMA_ADICIONAIS_INTERFACE.md
SISTEMA_HORARIOS_DETALHADO.md
SOLUCAO_BANCO_RENDER.md
SOLUCAO_ERRO_500_ENERGIA_SOLAR.md
SOLUCAO_PARCELAS_PROPOSTA.md
TUTORIAL_VISUAL_INSTALACAO.md
UPLOAD_DATASHEETS.md
VARIAVEIS_COMPLETAS_PROPOSTA.md
VARIAVEIS_TEMPLATE_WORD.md
VARIAVEIS_WORD.md
WIZARD_MELHORIAS_IMPLEMENTADAS.md
WIZARD_PROJETOS_SOLARES.md
```

**NOTA:** Os arquivos .md NÃO afetam o funcionamento, mas são úteis para consulta

---

## 🗂️ CATEGORIA 12: ARQUIVOS DE DADOS E CONFIGURAÇÃO DIVERSOS (8 arquivos)
**Descrição:** Arquivos de dados exemplo e configuração  
**Impacto no Sistema:** ❌ ZERO  
**Ação Sugerida:** ⚠️ Avaliar individualmente

```
dados_para_render.json
exemplo_extrato_bancario.csv
CREDENCIAIS_LOGIN.txt (⚠️ MANTER - contém credenciais de acesso)
ngrok_recovery_codes.txt
.render-force-rebuild-20260209-095454
.render-rebuild
alembic.ini.old
search_colabs.py
```

---

## 🗂️ CATEGORIA 13: SCRIPTS OBSOLETOS DE START (5 arquivos)
**Descrição:** Scripts de inicialização alternativos/obsoletos  
**Impacto no Sistema:** ❌ ZERO - Não são usados  
**Ação Sugerida:** ✅ DELETAR

```
start.py
server.py
run_debug.py
run_postgres.py
app.py (raiz - obsoleto, o correto é app/app.py)
create_tables.py (obsoleto - tabelas são criadas automaticamente)
```

---

## 🗂️ CATEGORIA 14: SCRIPTS DE GERAÇÃO DE PROPOSTAS E TESTES (5 arquivos)
**Descrição:** Scripts para testar geração de propostas  
**Impacto no Sistema:** ❌ ZERO - Apenas testes  
**Ação Sugerida:** ✅ MOVER para `scripts_manutencao/testes/`

```
gerar_proposta_alessandro.py
testar_geracao_proposta_word.py
testar_integracao_os_financeiro.py
testar_placeholders_word.py
gerar_icones_pwa.py
deploy_pwa.py
```

---

## 🗂️ CATEGORIA 15: PASTAS DE MIGRAÇÃO OBSOLETAS
**Descrição:** Pastas antigas de migração Alembic  
**Impacto no Sistema:** ❌ ZERO - Migrações são feitas automaticamente em app.py  
**Ação Sugerida:** ⚠️ MOVER para `backups/` ou DELETAR

```
migrations_old/
alembic.ini
alembic.ini.old
```

---

## 🗂️ CATEGORIA 16: PASTAS ESPECIAIS
**Descrição:** Pastas que podem conter arquivos importantes  
**Ação Sugerida:** ⚠️ REVISAR antes de deletar

```
backups/               (⚠️ MANTER - pode conter backups importantes)
logs/                  (⚠️ MANTER - logs do sistema)
uploads/               (⚠️ MANTER - arquivos enviados pelos usuários)
static/                (⚠️ MANTER - arquivos estáticos do sistema)
final_working/         (❓ Revisar - pode ser backup de código funcionando)
scripts_manutencao/    (⚠️ MANTER - scripts de manutenção organizados)
.github/               (⚠️ MANTER - configurações do GitHub)
```

---

## ✅ RECOMENDAÇÕES FINAIS

### 🔴 CRÍTICO - NÃO DELETAR:
- `run.py`
- `app/` (pasta completa)
- `requirements.txt`
- `.env`
- `erp.db`
- `database/`
- `Procfile`, `render.yaml`, `runtime.txt`
- `README.md`
- `🚀 INICIAR ERP JSP.bat`
- `.gitignore`

### 🟡 PODEM SER ORGANIZADOS:
1. **Criar estrutura organizada:**
   ```
   scripts_manutencao/
   ├── debug/          (scripts de debug)
   ├── migracoes/      (scripts de migração)
   ├── verificacao/    (scripts de verificação)
   ├── exemplos/       (dados exemplo)
   ├── correcoes/      (scripts de correção)
   ├── testes/         (scripts de teste)
   └── sql/            (scripts SQL)
   ```

2. **Mover executáveis:**
   - Mover .exe para pasta `dist/` ou deletar

3. **Limpar temporários:**
   - Deletar `build/`, `build_temp/`, `__pycache__/`, `temp_docx/`

### 🟢 PODEM SER DELETADOS COM SEGURANÇA:
- Scripts de debug (categoria 1) - ~25 arquivos
- Scripts de teste (categoria 3 - parte) - ~20 arquivos
- Arquivos temporários - ~10 arquivos
- Scripts obsoletos de start - ~5 arquivos

**Total estimado que pode ser removido/organizado: ~150 arquivos**

---

## 📊 ESTATÍSTICAS

| Categoria | Quantidade | Pode Deletar | Deve Mover | Deve Manter |
|-----------|------------|--------------|------------|-------------|
| Debug/Diagnóstico | 25 | ✅ 20 | ⚠️ 5 | - |
| Migração/Importação | 30 | - | ⚠️ 30 | - |
| Verificação/Testes | 40 | ✅ 30 | ⚠️ 10 | - |
| Dados Exemplo | 15 | - | ⚠️ 15 | - |
| Recálculo/Atualização | 10 | - | ⚠️ 10 | - |
| Launchers Alternativos | 8 | ✅ 6 | - | ⚠️ 2 |
| Executáveis | 4 | ✅ 3 | ⚠️ 1 | - |
| Build/Temporários | 8 | ✅ 8 | - | - |
| Backups DB | 2 | - | ⚠️ 2 | - |
| SQL/Diversos | 5 | - | ⚠️ 5 | - |
| Documentação | 60+ | - | - | ⚠️ 60+ |
| Dados/Config | 8 | - | - | ⚠️ 8 |
| Start Obsoletos | 5 | ✅ 5 | - | - |
| Propostas/Testes | 5 | - | ⚠️ 5 | - |
| **TOTAL** | **~225** | **~72** | **~83** | **~70** |

---

## 🎯 PLANO DE AÇÃO SUGERIDO

### Fase 1 - LIMPEZA SEGURA (Pode fazer agora):
1. Deletar pastas temporárias: `build/`, `build_temp/`, `temp_docx/`
2. Deletar scripts obsoletos de start (5 arquivos)
3. Deletar arquivos temporários (.zip)

### Fase 2 - ORGANIZAÇÃO (Recomendado):
1. Criar estrutura em `scripts_manutencao/`
2. Mover scripts de debug, verificação, migração
3. Mover executáveis para `dist/`

### Fase 3 - LIMPEZA AVANÇADA (Opcional):
1. Avaliar e deletar scripts de debug nunca mais usados
2. Deletar launchers alternativos não utilizados
3. Deletar backups antigos do banco (.db)

---

**FIM DA ANÁLISE**
