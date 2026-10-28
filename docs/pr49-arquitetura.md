# PR49 — arquitetura, preservação e migração

## Revisão do ponto de partida

A PR49 inicial tinha preservação parcial de IDs e uma checagem de administrador no fechamento. Faltavam histórico, proteção contra formulário antigo, custo/rateio, migração, interface e testes de integração. Os sete testes iniciais extraíam funções por AST com mocks; foram substituídos por testes com Flask/SQLAlchemy reais e banco isolado.

Reaproveitados: `Colaborador`, `OrdemServicoColaborador`, produtos da OS, lançamentos, parcelas, extratos e conciliação N:N. A estrutura `RateioDespesa` existente foi examinada: exige centro de custo, percentuais totalizando 100%, exclui/recria os rateios e faz commit próprio. Não representa trabalho por hora/diária/serviço, estimativas sem pagamento, destino OS/interno ou histórico imutável. Alterá-la ampliaria os efeitos nos relatórios por centro de custo. Por isso a nova estrutura é administrativa e independente; rateios por centro de custo continuam sendo outra dimensão de análise, não somada ao painel da OS.

## Modelo e transações

`os_custos_internos`: um registro é um custo e, quando associado a um pagamento, também sua alocação. OS nula significa trabalho interno, sem criar OS artificial. Valor é total histórico explícito. Não há geração de lançamento, alteração de banco/estoque ou atualização de NFS-e.

`os_custos_auditoria`: eventos de criação/edição/inativação de custos e edição/inativação de apontamentos, com usuário, motivo, data e snapshots. A aplicação proíbe alteração/exclusão do histórico e exclusão física dos custos. FKs RESTRICT preservam referências históricas. Isso também pode bloquear exclusão física de OS/material que possua histórico; não contornar a proteção.

Ordem de locks: OS → custo/apontamento → pagamentos em ordem crescente de ID. Operações em serviços não fazem commit: a rota confirma uma única transação ou reverte. Um SELECT FOR UPDATE do pagamento serializa o cálculo de saldo de rateio em PostgreSQL. A versão do custo rejeita formulários antigos. Chave de operação única e índice parcial por assinatura de custo ativo impedem repetição, inclusive com novas chaves em solicitações concorrentes. Registros semelhantes são sinalizados sem correção automática.

O formulário administrativo de apontamentos envia revisão do conjunto. A edição preserva registros e valores horários históricos, cria apenas inclusões e inativa apenas remoções explícitas do conjunto vigente. Apontamento com custo ativo não pode ser removido. A edição de produtos preserva IDs enviados; materiais com custos históricos não podem ser excluídos ou mudar identidade/quantidade.

## Confidencialidade

Novas rotas exigem login e `tipo_usuario=admin`, além de CSRF por sessão, confirmação e motivo. O PDF interno tem template distinto; o template comercial não possui a seção de fechamento. Parâmetros de URL não concedem privilégio. O módulo de colaboradores restringe suas páginas com salários/fechamento a administradores, e a API de seleção não fornece salário mensal aos demais perfis. Valores históricos de custo/margem não são renderizados para usuários comuns no formulário da OS.

## Migração aditiva 20261028_01

Parent: `20261026_01`; branch label: `os_custos`. Cria somente duas tabelas novas, índices, checks e FKs. Não altera tabelas financeiras existentes, não preenche histórico retroativo e não cria custos a partir de OS antigas. Não foi executada em produção.

Após aprovação futura, a equipe de implantação deve revisar backup, revisão Alembic atual e o DDL antes de aplicar **`os_custos@head`** no ambiente aprovado. Não executar comandos de migração em produção durante esta revisão. A inicialização legada do ERP contém `create_all` e ajustes automáticos; eles não substituem o controle de revisão Alembic e precisam ser considerados no planejamento da implantação.

Se a PR48 também for incorporada, ambas as migrações partem de `20261026_01`: existirão dois heads válidos. A PR49 não aplica a migração da PR48 como dependência. A implantação futura deve escolher os alvos aprovados explicitamente ou usar uma revisão de união devidamente revisada; não usar `upgrade head` ambíguo. Testes compõem as árvores e aplicam/revertem as duas migrações em banco efêmero, preservando dados preexistentes.

Rollback: downgrade físico só é permitido com **ambas as tabelas novas vazias**. Com qualquer custo ou evento de histórico, o downgrade é bloqueado; preserve as tabelas, reverta a aplicação e planeje uma reversão de dados específica. Não apagar registros para liberar downgrade. A versão antiga da aplicação desconhece os novos vínculos: durante uma reversão, mantenha o financeiro e a edição de OS sem escritas até revisar as proteções equivalentes; não liberar uma aplicação antiga para modificar pagamentos rateados.

## Limites e riscos para revisão

- Migração/ativação precisam de aprovação separada. PostgreSQL valida a concorrência; SQLite não oferece a mesma semântica de FOR UPDATE.
- Valor histórico de material exige documento/valor informado. Não há ligação inequívoca entre toda compra/estoque e a OS; não se infere custo histórico do preço atual.
- O vínculo pagamento–colaborador depende de conferência do responsável. Descrições antigas e possíveis duplicidades financeiras não são corrigidas pelo desenvolvimento.
- Identificação de recebimento legado usa títulos ativos quitados com data quando a OS não tem parcelas. Não resolve inconsistências históricas automaticamente.
- A margem é operacional sobre contrato e custos registrados. Não completa a DRE da PR48 e não equivale a lucro líquido.
- Alterações SQL diretas/bulk fora dos serviços e do ORM não são uma interface suportada para custos/rateios; permissões de banco e operação continuam necessárias. As proteções de imutabilidade são aplicadas pelo backend ORM; não são triggers universais contra administradores do banco.
- Serviços gerais existentes e exportações comerciais continuam independentes; textos e anexos inseridos manualmente não são automaticamente saneados.

## Arquivos principais

Modelos/serviços/rotas novos: `app/ordem_servico/custos_model.py`, `custos_service.py`, `custos_routes.py`. Integração: modelos/rotas da OS, rotas de colaboradores, formulário/visualização/PDF da OS, templates novos de custos e fechamento. Migração: `migrations/versions/20261028_01_os_custos_internos.py`. Testes: `scripts_manutencao/testes/test_pr49_*`, fixture de homologação N:N e workflow `.github/workflows/pr49_custos.yml`. Manual, relatório e prévia estão em `docs/pr49-*`.
