# PR #46 — recebimento de parcelas de OS
Atualização: 26/10/2026. Implementação validada para revisão de código; sem merge ou implantação.

## Comportamento
A visualização da OS oferece “Registrar recebimento” ao administrador para parcela pendente. Solicita data efetiva, valor previamente preenchido e imutável, forma de pagamento, conta ativa e observação opcional. O POST exige autenticação e CSRF.

A transação recebe apenas a parcela selecionada, vincula o título pelos IDs da OS e da parcela, registra usuário/data/operação e atualiza o status financeiro para parcial ou pago. O status operacional permanece inalterado. Erros revertem a transação; duplicidade e alteração destrutiva de parcela quitada são rejeitadas.

Os títulos pendentes são gerados antes da conclusão operacional. Repetir sincronização ou concluir a OS preserva o título e o pagamento existentes. Recebíveis não são convertidos automaticamente em receita por competência. A baixa manual não cria extrato nem acrescenta crédito ao saldo bancário; usa sem_movimentacao_bancaria=True e deixa a conciliação para o movimento bancário real já importado.

## Caso Jumirim: somente dados fictícios
Referências informadas pelo solicitante: OS real 619, proposta PROP20260021 e extrato real Cora 45. Nenhum desses registros reais foi consultado ou alterado nesta execução. Os testes criam cliente e OS artificiais; extrato ID 45 existe somente na fixture descartável.

| Parcela | Valor | Vencimento | Estado após o primeiro recebimento |
| --- | ---: | --- | --- |
| 1 | R$ 15.000,00 | 17/09/2026 | Recebida em 17/09/2026 |
| 2 | R$ 7.500,00 | 17/10/2026 | Pendente |
| 3 | R$ 7.500,00 | 17/11/2026 | Pendente |

Resultado validado: OS iniciada, R$ 15.000,00 recebidos, R$ 15.000,00 em aberto, três títulos e um histórico de pagamento. Conciliação N:N com o extrato fictício mantém o saldo em R$ 15.000,00.

## Alterações desta revisão
| Arquivo | Alteração |
| --- | --- |
| app/ordem_servico/recebimento_parcelas.py | CSRF com Unicode; releitura de OS, parcelas e título após obter lock, inclusive com objetos previamente carregados na sessão. |
| app/ordem_servico/ordem_servico_routes.py | Edição de parcelas usa o mesmo lock da baixa antes de conferir proteção de parcela quitada. |
| scripts_manutencao/testes/test_pr46_os_recebimento.py | Fixture PostgreSQL com schema exclusivo; autenticação/CSRF Unicode, quitação total em três estados operacionais e não reconhecimento automático de competência. |
| scripts_manutencao/testes/test_pr46_postgresql.py | Duas sessões reais: mesma parcela, parcelas distintas até quitação total e geração concorrente; conciliação e migration PostgreSQL. |
| .github/workflows/pr46_os_financeiro.yml | Jobs SQLite e PostgreSQL 16 descartável, sem configuração ou secrets de produção. |
| docs/regularizacao-os-financeiro-set2026.md | Relatório e evidências atualizados. |

Também revisados na implementação existente: financeiro_model.py (unicidade por parcela e marcador bancário), financeiro_utils.py (geração idempotente), saldo_bancario_events.py, formulário os/visualizar.html, migration 20261026_01, diagnóstico da porta local e testes de regressão.

## Evidências
Commit de código: 5ad51a4d4ae7fbe4c95988b14cdec101c73fcf7b.
[GitHub Actions — execução 40354025065](https://github.com/JulianoSaroba123/erp-jsp/actions/runs/40354025065), concluída com sucesso:

- SQLite CI, Python 3.11: **35 passed, 2 warnings, 8,75 s**.
- PostgreSQL 16 CI: **5 passed, 1 warning, 6,41 s**.
- Local isolado, Python 3.12: suíte original **31 passed** e quatro novos cenários **4 passed**. Há warnings de APIs legadas/UTC no Python 3.12; nenhum teste falhou.
- git diff --check sem erros antes da publicação do código.

A suíte SQLite cobre recebimento repetido, proteção de quitados, valores/formas/contas inválidos, autenticação, autorização administrativa, CSRF, falha de auditoria com rollback, conciliação e regressões OS/Financeiro/Proposta. PostgreSQL comprova concorrência com sessões independentes, inclusive objetos previamente carregados. Migration validada em SQLite e PostgreSQL, com valor padrão False preservando histórico e bloqueio de downgrade quando houver recebimento com marcador True.

## Segurança do ambiente e pendências
O serviço 127.0.0.1:5001 da máquina do solicitante não está acessível neste ambiente remoto. Portanto **o banco dessa instância permanece NÃO VERIFICADO**. Não se conclui que ele seja local ou que esteja isolado do Render. Não foram feitas gravações nessa instância.

Os testes locais usaram TestingConfig SQLite em memória, com DATABASE_URL SQLite temporária definida antes da importação do aplicativo. O PostgreSQL do CI é um serviço descartável; a fixture aceita apenas loopback, banco erp_jsp_pr46_test e schema exclusivo, recusando sinalização de Render. Nenhuma credencial de produção foi acessada.

Antes de merge/implantação:
1. Executar scripts_manutencao/diagnosticar_pr46_porta_local.py na máquina que hospeda a porta 5001. Resultado desconhecido/remoto bloqueia testes de escrita.
2. Revisar o diff e o procedimento Alembic no ambiente de destino; o teste isolado da migration não substitui o inventário do schema existente.
3. Obter autorização explícita para merge/implantação. Não regularizar OS 619 ou extrato 45 sem uma operação posterior específica e autorizada.

A migration não foi aplicada em produção. Não foram alterados contratos, valores, vencimentos ou ordens reais, nem criadas OS reais.
