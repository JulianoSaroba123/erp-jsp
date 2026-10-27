# DRE e fluxo de caixa — diagnóstico e limitações

## Fluxo projetado
A tela e Excel usam o mesmo cálculo. Títulos ativos pendentes são projetados pelo vencimento, com tipo normalizado, após dedução das conciliações ativas. Pagamentos/recebimentos concluídos, títulos cancelados e inativos e transferências bancárias não integram a projeção futura. Títulos vencidos são informados separadamente e não são supostos como recebidos hoje. O saldo inicial é o saldo cadastrado nas contas, que deve ser confrontado com o extrato.

Testes usam dados fictícios para contas a pagar e receber, baixas antecipadas, cancelados, inativos, atraso e conciliação parcial N:N e legado. Tela e Excel são comparados pelo mesmo período. Nenhum valor real é alterado.

## DRE: ainda não concluído
O modelo LancamentoFinanceiro não tem data de competência nem indicação explícita de reconhecimento, e títulos de OS podem ser recebidos antes da prestação do serviço. Data de lançamento, vencimento, pagamento ou baixa de parcelas não demonstram por si sós quando a receita foi auferida. Categoria textual também não identifica com segurança custos, investimentos, transferências e deduções. Portanto, somar conta_receber e conta_pagar com base nas datas existentes fabricaria resultado de competência e poderia reconhecer antecipações e parcelas em duplicidade.

A tela e o Excel do DRE existente recebem aviso de limitação. Não foram alterados o cálculo ou os registros reais do DRE. Antes de liberar como definitivo: definir campos e fluxo auditável de competência, classe contábil, evento de reconhecimento, tratamento de antecipações, parcelas, custos/investimentos, notas fiscais e duplicidade; conciliar com o responsável/contador; testar dados históricos e migração aditiva sem preencher dados presumidos. Os agrupamentos reais de setembro devem ser avaliados somente após o mapeamento, com confronto de extratos e documentos.

## Implantação
PR para revisão sem merge/deploy automático. Fica pendente verificar o saldo bancário cadastrado comparado ao extrato, e a semântica de conciliações parciais. Não modificar dados de produção durante a validação.

## Etapas de receita — implementação em revisão
Conforme preferência do responsável, a versão proposta permite a um administrador registrar explicitamente a descrição, a data e o valor de uma etapa executada na OS. A etapa integra o período correspondente do DRE e é independente dos recebimentos. Não há reconhecimento automático de antecipações nem alteração do extrato ou das parcelas. O total das etapas não pode exceder o valor atual da OS, e operações repetidas são bloqueadas. A nova tabela tem migration aditiva, sem preenchimento automático de dados históricos.

A solução continua parcial: DRE e classificações de custos, despesas, investimentos e competência histórica exigem definição e validação; a verificação da proteção contra reduções do valor contratual em todos os demais fluxos precisa ser concluída antes de disponibilizar em produção. A tela e o Excel preservam aviso de que o DRE não é definitivo. Consultar o contador sobre a aplicação da regra de reconhecimento à empresa.
