# CHECKPOINT | ERP JSP | Saldo bancário Cora | 09/11/2026

**Estado:** PR #58 em rascunho; sem merge, sem deploy e sem modificação da produção.
**Conta:** Cora SCFI, conta bancaria ID 1.
**Fonte independente:** extrato oficial Cora do período 25/10/2026 a 31/10/2026 fornecido pelo responsável, saldo final R$ 3.282,73.
**Corte bancário:** extratos importados de 01/11/2026 a 09/11/2026, 40/40 conciliados.

## Conferência matemática

| Item | R$ |
|---|---:|
| Saldo em 31/10/2026, extrato oficial | 3.282,73 |
| Créditos importados em novembro | +13.949,00 |
| Débitos importados em novembro | -8.722,96 |
| Saldo final em 09/11/2026 | **8.508,77** |
| Saldo legado de `contas_bancarias.saldo_atual`, ID 1 | -24.544,59 |
| Diferença interna necessária para correção | **+33.053,36** |

O KPI legado de R$ 5.226,04 representa variação líquida no período, **não** saldo bancário nem lucro.
Os dois Pix de R$ 130,00 relativos à JSP Personalizados possuem entrada/saída conciliadas, não constituem receita operacional nem retirada de sócio.

## Implementação preparada

- Migração Alembic `20261109_01`, dependente de `20261107_01`.
- Cria referência auditada na tabela `saldo_bancario_referencias` (origem, data, saldos anterior/reparado e justificativa).
- Atualiza **somente** `contas_bancarias.saldo_atual` da conta #1, se o saldo antigo ainda for exatamente -24.544,59 e os 40 extratos persistirem inalterados e conciliados.
- Caso haja transações novas, status alterado, saldos alterados, outra conta ou outro valor: **abortar**, recalcular novo checkpoint com extrato oficial e preparar revisão. Nunca aplicar o valor de 09/11 a um dia posterior sem reconciliação.
- Serviço `app/financeiro/saldo_extrato_service.py` calcula saldo por referência bancária + extratos importados (inclusive pendentes, com aviso), sem duplicar títulos financeiros.
- Painel principal diferencia **Entradas**, **Saídas**, **Variação líquida** e **Saldo bancário até o último extrato importado**; exibe alerta para divergência do campo legado.

## Pré e pós-implantação (somente após aprovação)

1. Registrar em checkpoint os resultados read-only: Cora ID 1; saldo legado esperado; 40/40 extratos; soma entrada e saída; último movimento 09/11.
2. Conferir novamente extrato oficial Cora. Se houve qualquer novo movimento, **não mesclar esta migração sem atualizar os dados e testes**.
3. CI PostgreSQL descartável e SQLite aprovado; conferir único Alembic head.
4. Autorizar separadamente merge e deploy. Observar o job de migração: falha fechada caso o snapshot tenha mudado.
5. Validar em produção, apenas leitura: checkpoint registrado, conta.saldo_atual = saldo bancário calculado, 40/40 conciliações preservadas e dashboard com indicador independente.
6. Monitorar se lançamentos pagos, importações ou alterações de títulos geram nova divergência; não lançar ajuste fictício.

**Nunca alterar:** saldo_inicial histórico, extratos, parcelas, valores financeiros, status de OS ou conciliações N:N.

## Pendência de apresentação contábil

`Valores Transitórios de Terceiros` e `Retirada de Sócio` devem ficar apartados de receita operacional e lucro; os cartões de **entradas/saídas de caixa** incluem legitimamente esses movimentos, mas não representam faturamento/despesa tributável.
