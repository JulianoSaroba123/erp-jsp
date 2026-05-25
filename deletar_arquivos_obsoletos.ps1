# Script PowerShell para deletar arquivos obsoletos do ERP JSP
# ATENÇÃO: Execute com cuidado! Faça backup antes!

Write-Host "🗑️ LIMPEZA DE ARQUIVOS OBSOLETOS DO ERP JSP" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$total_deletados = 0

# CATEGORIA 1: Scripts de Migração/Adição de Colunas (35 arquivos)
Write-Host "📋 Categoria 1: Scripts de Migração/Adição de Colunas..." -ForegroundColor Yellow
$arquivos_cat1 = @(
    "adicionar_datasheet.py",
    "adicionar_coluna_datasheet.py",
    "adicionar_coluna_conteudo.py",
    "adicionar_colaborador_os2.py",
    "adicionar_campos_horarios_detalhados.py",
    "adicionar_campos_financeiros_projeto.py",
    "adicionar_tipo_os_render.py",
    "adicionar_tipo_instalacao.py",
    "adicionar_proposta_id.py",
    "adicionar_numero_projeto_solar.py",
    "adicionar_numero_endereco.py",
    "adicionar_logo_base64.py",
    "adicionar_kit_id_coluna.py",
    "adicionar_intervalo_almoco.py",
    "adicionar_datasheet_render.py",
    "adicionar_variaveis_ao_template_usuario.py",
    "ativar_os_render.py",
    "configurar_colaborador_flask.py",
    "configurar_colaborador.py",
    "converter_os2_operacional.py",
    "converter_logo_existente.py",
    "corrigir_campo_ativo_os.py",
    "corrigir_campo_ativo_render.py",
    "corrigir_cliente_20_render.py",
    "corrigir_formato_logo.py",
    "corrigir_logo_base64.py",
    "corrigir_logo_render.py",
    "corrigir_logo_shell_render.py",
    "corrigir_os_sem_lancamento.py",
    "corrigir_paths_datasheets.py",
    "corrigir_projeto_solar_render.py",
    "corrigir_projetos_kit.py",
    "corrigir_tipo_horas.py",
    "corrigir_valores_os.py",
    "atualizar_financeiro_direto.py",
    "atualizar_placa_dm585.py",
    "atualizar_projeto_direto.py",
    "atualizar_tipo_usuario_render.py"
)

foreach ($arquivo in $arquivos_cat1) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 2: Scripts de Teste/Debug Obsoletos (30 arquivos)
Write-Host ""
Write-Host "📋 Categoria 2: Scripts de Teste/Debug Obsoletos..." -ForegroundColor Yellow
$arquivos_cat2 = @(
    "testar_visualizar_proposta.py",
    "testar_url_render.py",
    "testar_upload_logo.py",
    "testar_upload_datasheet.py",
    "testar_to_dict.py",
    "testar_salvamento_padrao.py",
    "testar_rota_proposta.py",
    "testar_query_listar.py",
    "testar_pwa.py",
    "testar_pdf_projeto_6.py",
    "testar_pdf_projeto_5.py",
    "testar_pdf_projeto_2.py",
    "testar_login.py",
    "testar_erro_cliente_20.py",
    "testar_energia_solar_render.py",
    "testar_cliente_listagem.py",
    "testar_cliente.py",
    "testar_cadastro_cliente.py",
    "testar_autocomplete.py",
    "testar_get_placa.py",
    "teste_sqlite.py",
    "teste_login_direto.py",
    "teste_layout_placas.py",
    "teste_diagnostico.py",
    "analisar_html_proposta.py",
    "check_os_status.py",
    "check_os_tipo.py",
    "check_projeto_4.py",
    "check_render_error.py",
    "check_routes.py",
    "check_tipo_mismatch.py",
    "check_tipos_os.py"
)

foreach ($arquivo in $arquivos_cat2) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 3: Scripts de Diagnóstico Pontuais (20 arquivos)
Write-Host ""
Write-Host "📋 Categoria 3: Scripts de Diagnóstico Pontuais..." -ForegroundColor Yellow
$arquivos_cat3 = @(
    "diagnostico_projetos_render.py",
    "diagnostico_placas_render.py",
    "diagnostico_os_completo.py",
    "diagnostico_login.py",
    "diagnostico_layout_render.py",
    "diagnostico_kits.py",
    "diagnostico_anexos.py",
    "diagnosticar_os_financeiro.py",
    "diagnosticar_cliente_20.py",
    "diagnostico_status_os.py",
    "diagnostico_render_energia.py",
    "diagnostico_render.py",
    "procurar_os_render.py",
    "forcar_deploy_render.py",
    "forcar_bifasico_render.py",
    "setup_render.py",
    "setup_colaborador_completo.py",
    "criar_admin_render.py",
    "popular_projeto_6_render.py",
    "popular_equipamentos_render.py"
)

foreach ($arquivo in $arquivos_cat3) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 5: Build/Launcher Obsoletos (8 arquivos)
Write-Host ""
Write-Host "📋 Categoria 5: Build/Launcher Obsoletos..." -ForegroundColor Yellow
$arquivos_cat5 = @(
    "launcher.py",
    "launcher_simples.py",
    "launcher_pro_simples.py",
    "jsp_launcher.py",
    "build_jsp_exe.py",
    "build_simples.py",
    "app.py",
    "server.py"
)

foreach ($arquivo in $arquivos_cat5) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 6: Templates Word Obsoletos (4 arquivos)
Write-Host ""
Write-Host "📋 Categoria 6: Scripts de Templates Word Obsoletos..." -ForegroundColor Yellow
$arquivos_cat6 = @(
    "find_placeholders.py",
    "find_placeholders_v2.py",
    "find_placeholders_v3.py",
    "verify_placeholders.py",
    "normalize_placeholders.py",
    "extrair_variaveis_word.py"
)

foreach ($arquivo in $arquivos_cat6) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 7: Listagem/Ver Dados Duplicados (6 arquivos)
Write-Host ""
Write-Host "📋 Categoria 7: Scripts de Listagem Duplicados..." -ForegroundColor Yellow
$arquivos_cat7 = @(
    "ver_tabelas_erp_db.py",
    "ver_tabelas.py",
    "ver_estrutura.py",
    "ver_colunas.py",
    "listar_tabelas.py",
    "listar_propostas.py",
    "listar_projetos.py"
)

foreach ($arquivo in $arquivos_cat7) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# CATEGORIA 8: Geração Específica Obsoleta (3 arquivos)
Write-Host ""
Write-Host "📋 Categoria 8: Scripts de Geração Específica Obsoletos..." -ForegroundColor Yellow
$arquivos_cat8 = @(
    "gerar_proposta_alessandro.py",
    "gerar_icones_pwa.py",
    "deploy_pwa.py"
)

foreach ($arquivo in $arquivos_cat8) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "   ✅ $arquivo" -ForegroundColor Green
        $total_deletados++
    }
}

# RESUMO
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "✅ LIMPEZA CONCLUÍDA!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Total de arquivos deletados: $total_deletados" -ForegroundColor Green
Write-Host ""
Write-Host "📦 PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "   1. Verifique se o sistema ainda funciona normalmente"
Write-Host "   2. Execute: git status"
Write-Host "   3. Se tudo OK, faça commit e push dos arquivos deletados"
Write-Host ""
