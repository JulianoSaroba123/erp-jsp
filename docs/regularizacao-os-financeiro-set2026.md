# Regularização OS -> Financeiro | setembro/2026

## Caso de referência
OS interna 619 (Jumirim, PROP20260021), contrato R$ 30.000,00.
Parcelas na tabela `ordem_servico_parcelas`: #22 R$ 15.000,00 (17/09/2026, efetivamente recebida no Cora, extrato ID 45), #30 R$ 7.500,00 (17/10/2026), #31 R$ 7.500,00 (17/11/2026). No banco, todas ainda estão marcadas como não pagas e não há `lancamentos_financeiros` para OS 619. NÃO executar baixa direta no banco como parte deste documento.

## Diagnóstico confirmado
`app/financeiro/financeiro_utils.py::gerar_lancamento_ordem_servico` só cria contas a receber pendentes quando a OS está concluída; OS iniciada processa apenas parcelas já recebidas ou com lançamentos existentes. Por isso as parcelas da OS 619 não aparecem em Contas a Receber.

## Requisitos de implementação (pendentes)
1. Criar fluxo transacional e autenticado de **Receber parcela da OS** a partir da visualização da OS ou do financeiro. Exigir data de recebimento, valor da parcela e conta bancária; permitir conciliação com extrato importado, sem lançar movimentação bancária fictícia.
2. Em uma única transação: bloquear a parcela contra concorrência, conferir valor e não duplicidade, marcar `pago` e `data_pagamento`, criar/atualizar `LancamentoFinanceiro` de tipo `conta_receber`, origem `ORDEM_SERVICO`, com `ordem_servico_id` e `ordem_servico_parcela_id`, status `recebido`, data real; sincronizar `status_pagamento` da OS. Repetir operação não pode duplicar lançamento nem saldo.
3. Exibir parcelas pendentes em Contas a Receber mesmo com OS iniciada, mas sem contabilizá-las como recebidas ou reconhecer receita de competência indevidamente. Verificar regras existentes de geração automática para evitar lançamentos duplos ao concluir a OS.
4. Proteger parcelas recebidas de alterações destrutivas, preservar auditoria e tratar erro com rollback. Não permitir baixa total da OS quando apenas a primeira parcela foi recebida.
5. Cobrir com testes: OS iniciada com três parcelas, recebimento da primeira, segunda/terceira pendentes, reenvio idempotente, conclusão posterior, concorrência, conciliação do extrato ID 45 e nenhuma duplicação de saldo.

## Critérios de aceite para OS 619
- OS permanece **Iniciada**, valor total R$ 30.000,00.
- Parcela #22 recebida em 17/09/2026 por R$ 15.000,00, vinculada a um único lançamento financeiro e ao extrato Cora ID 45.
- Parcelas #30 e #31 continuam pendentes, R$ 7.500,00 cada.
- Contas a Receber e fluxo de caixa exibem valores corretamente; setembro não apresenta entrada duplicada.
- Implantação e regularização de produção exigem revisão, testes, backup e autorização explícita.

**Estado:** apenas especificação técnica, sem implementação nem migração aplicada.
