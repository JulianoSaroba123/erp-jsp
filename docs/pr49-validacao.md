# PR49 — relatório de validação

## Ambientes e escopo

Testes usam SQLite em memória, bootstrap SQLite em `/tmp` e PostgreSQL 16 descartável no GitHub Actions. O fixture PostgreSQL exige host local, banco de teste com nome fixo e schema exclusivo por teste, e rejeita ambiente Render. Nenhum teste usa a conexão de produção.

O cenário OS20260101 e os pagamentos 165/166 são recriados artificialmente: total de pagamentos R$ 1.100, custo da OS R$ 800 e interno R$ 300. Asserções comparam registros financeiros, extratos, itens de conciliação, saldos e despesas do período antes/depois. Foram preservados. Não se aplicaram rateios aos registros reais.

A investigação solicitada em produção foi exclusivamente por ferramenta de SQL read-only, sem obter credenciais. Há divergências documentais que precisam de conferência do responsável antes de vincular pagamentos reais. Dados internos dessa consulta não são publicados neste repositório. Nenhum lançamento suspeito foi inativado ou corrigido.

## Resultados locais executados

- **83 aprovados, 6 ignorados** na bateria principal. Os seis ignorados correspondem a PostgreSQL indisponível neste host e cenários que só existem na árvore combinada com a PR48; são cobertos nos jobs específicos do CI.
- **28 aprovados, 2 ignorados** em uma árvore temporária com a PR48 aplicada. Os dois ignorados dependiam do PostgreSQL; a compatibilidade também é executada em PostgreSQL no CI. As 17 versões de arquivos da PR48 foram conferidas pelo SHA contra o head remoto `bee214378a91c786111f86cc3cfbbe4edb03d416`. A árvore combinada não foi publicada nem incorporada à PR49.
- Scripts independentes de homologação N:N `homologacao_conciliacao_adapter_a24.py` e `homologacao_mr_jacky_a3.py` passaram. A fixture antiga não definia `Pedido`; a definição mínima de teste foi adicionada, sem alteração no código financeiro.
- Compilação dos módulos novos/rotas alteradas e `git diff --check` sem erros nos checkpoints executados.
- A prévia HTML foi exportada pelo teste funcional com dados artificiais; a autorização e os formulários são testados contra as rotas reais. Os estilos offline da prévia são simplificados; não é uma captura do ERP de produção.

Os resultados locais acima são checkpoints da implementação. Os **checks do commit mais recente da PR49** são a validação final da versão entregue. O primeiro CI desta implementação já aprovou 55 testes SQLite (2 ignorados) e 18 PostgreSQL: [execução inicial](https://github.com/JulianoSaroba123/erp-jsp/actions/runs/40613209987). O workflow foi ampliado para a bateria principal completa, scripts legados e compatibilidade com a PR48.

## Comandos da bateria principal

Executar na raiz do repositório, com Python/dependências de teste e bootstrap isolado:

```sh
DATABASE_URL=sqlite:////tmp/erp_jsp_pr49_bootstrap.sqlite FLASK_ENV=testing RENDER=false python -m pytest -q \
  scripts_manutencao/testes/test_pr49_custos.py \
  scripts_manutencao/testes/test_pr49_migration.py \
  scripts_manutencao/testes/test_pr49_compat48.py \
  scripts_manutencao/testes/test_pr46_os_recebimento.py \
  scripts_manutencao/testes/test_atividade_financeira.py \
  scripts_manutencao/testes/test_os_gatilho_financeiro.py \
  scripts_manutencao/testes/test_proposta_os_financeiro.py \
  scripts_manutencao/testes/test_conciliacao_baixa_proposta.py \
  scripts_manutencao/testes/pedido_compra_test.py \
  scripts_manutencao/testes/pedido_estoque_service_d26f03_test.py \
  scripts_manutencao/testes/nfse_parcela_preparacao_d24f04c_test.py --disable-warnings
```

PostgreSQL: o job `postgresql` de `.github/workflows/pr49_custos.yml` provisiona banco efêmero e executa:

```sh
python -m pytest -q scripts_manutencao/testes/test_pr49_postgresql.py \
  scripts_manutencao/testes/test_pr49_migration.py \
  scripts_manutencao/testes/test_pr46_postgresql.py \
  scripts_manutencao/testes/test_atividade_postgresql.py
```

Compatibilidade: em checkout temporário da PR49, o job `compatibilidade-pr48` busca o SHA fixado da PR48, aplica seu diff por `git apply --3way` (sem merge) e executa:

```sh
python -m pytest -q scripts_manutencao/testes/test_pr49_compat48.py \
  scripts_manutencao/testes/test_pr49_custos.py \
  scripts_manutencao/testes/test_receita_etapas.py \
  scripts_manutencao/testes/test_fluxo_projecao.py \
  scripts_manutencao/testes/test_etapas_migration.py
```

O workflow mantém explícitos os serviços descartáveis e variáveis de teste. Não usar uma conexão Render para preencher essas variáveis.

## Cobertura funcional

Inclusão/edição/inativação de apontamentos com ID preservado; proteção de valor horário histórico e formulário antigo; edição HTTP de OS com material vinculado; custo de horista/diarista/serviço fechado sem pagamento; custo histórico de material independente do preço/estoque atual; alocação OS/interno; limite de pagamento; chave repetida e assinatura de custo duplicado; versão concorrente; rollback após falha de auditoria; proteção de pagamento com histórico; margem e pendências; login/admin/CSRF/confirmação/filtros; bloqueio de IDs de outro destino; API sem salário para não administrador; PDFs comerciais sem dados internos, inclusive parâmetros de URL; coexistência com reconhecimento por etapas, sem somar receita ou caixa; migrações aditivas e downgrade vazio/guardado; parcelas, conciliação, inativação, compras, estoque e preparação fiscal.

## Limites

Não foi executada toda a suíte histórica do repositório nem teste de transmissão fiscal externa. Não houve emissão de NFS-e, importação bancária real, merge ou deploy. Não se pode inferir ausência absoluta de erros: revisão humana do DDL, permissões, regras contábeis e homologação visual no ambiente aprovado continuam necessárias. Warnings legados de datetime/SQLAlchemy e inicialização do ERP permanecem fora do escopo.

A funcionalidade não completa a DRE histórica da PR48. Migração aditiva, rollback seguro, limitações de auditoria e riscos estão em [pr49-arquitetura.md](pr49-arquitetura.md). Uso administrativo está em [pr49-manual.md](pr49-manual.md); [prévia offline](pr49-previa.html).
