# Custos e Rentabilidade por OS — manual administrativo

Funcionalidade da PR #49. Este manual descreve a versão em desenvolvimento; não significa que ela esteja implantada. Acesso exclusivo ao perfil `admin`.

## Onde acessar

Na visualização administrativa da OS, abra **Custos e Rentabilidade → Gerenciar custos e rateios**. Para despesas de trabalhos internos sem OS de cliente, use **Serviços internos**. Os apontamentos continuam no formulário existente de edição da OS.

## Registrar custo

1. Informe atividade, data, categoria e modalidade: hora, diária, serviço fechado ou unidade/material.
2. Informe a quantidade e o **valor total histórico**. Exemplo fictício: duas diárias de R$ 200 correspondem a quantidade 2 e total R$ 400. O campo de valor não é preço por diária/hora.
3. Selecione o colaborador cadastrado para mão de obra, inclusive auxiliares e prestadores. Apontamento e material da própria OS podem ser vinculados quando existentes.
4. Escolha **realizado**, **estimado** ou **não informado**. Neste último caso, deixe o valor vazio. Um valor estimado não é somado aos realizados. Zero é um valor explicitamente informado, não uma suposição para dados ausentes.
5. Identifique a fonte: acordo de diária, nota de compra, documento de custo histórico etc. O sistema não usa o preço atual de estoque nem o valor de venda como custo histórico.
6. Informe motivo e confirme. **Nenhum lançamento financeiro, pagamento, extrato ou movimento de estoque é criado.**

Um custo realizado sem vínculo de pagamento não deve ser considerado comprovadamente pago. O painel sinaliza essa situação. Materiais, combustível/deslocamento, alimentação, terceirizações e outros custos usam o mesmo registro administrativo.

## Vincular e ratear pagamento existente

Se o custo já existe, **edite sua linha** e selecione o pagamento; não registre o custo novamente. Somente despesas/contas a pagar ativas, pagas e com data de pagamento são elegíveis. A descrição e a origem devem ser conferidas pelo responsável: a ferramenta não presume que pagamentos de valores iguais sejam a mesma operação.

Exemplo **fictício de homologação**, não uma orientação para modificar registros reais:

| Pagamento de teste | Destino | Custo atribuído |
|---|---|---:|
| 165 — total R$ 600 | OS20260101 | R$ 400 |
| 165 — mesmo pagamento | Serviços internos | R$ 200 |
| 166 — total R$ 500 | OS20260101 | R$ 400 |
| 166 — mesmo pagamento | Serviços internos | R$ 100 |

O total bancário continua R$ 1.100; o custo da OS é R$ 800 e o interno R$ 300. O rateio registra a destinação, sem movimentar dinheiro. O valor total do pagamento permanece igual. Valores já atribuídos e presença de conciliação aparecem na seleção; presença de conciliação pode ser parcial e não significa quitação integral pelo extrato.

O sistema impede exceder o valor do pagamento, reenviar a mesma operação, associar apontamento de outra OS e cadastrar custo exatamente repetido. Também sinaliza possíveis duplicidades semelhantes para revisão humana. Confira sempre colaborador, atividade, data, documento e destino.

## Editar ou inativar

Use **Editar**, informe motivo e confirme. Se outra sessão alterou o registro, recarregue a tela: a versão antiga é rejeitada. Para corrigir uma duplicidade, use **Inativar custo** com motivo e confirmação. Isso retira somente o custo/rateio dos indicadores operacionais e preserva o histórico; não inativa o lançamento financeiro nem desfaz a conciliação.

O destino de um registro existente não pode ser trocado para outra OS. Para corrigir destino, inative o custo errado e registre a destinação correta com justificativa. Não há exclusão física nem reativação automática. Pagamentos que possuam rateio ou histórico de custo ficam protegidos contra alterações financeiras pela aplicação; exigem procedimento administrativo específico.

Um apontamento com custo ativo não pode ser removido: revise/inative o custo antes. Apontamentos removidos pelo formulário são inativados e preservam seu ID. Materiais com custo histórico não podem ser apagados ou trocar identidade/quantidade; o valor de venda pode ser editado sem reescrever o custo registrado. Recarregue formulários abertos antes da atualização da funcionalidade.

## Ler os indicadores

- **Contratada:** valor contratual da OS, sem alteração pelo registro de custos.
- **Recebida registrada:** parcelas ativas baixadas. Nas OS antigas sem parcelas, usa títulos ativos recebidos/pagos com data. Títulos legados sem vínculo em uma OS parcelada são sinalizados e não são somados às parcelas, evitando dupla contagem. Duplicidades históricas precisam de auditoria própria.
- **Custos realizados:** custos diretos reais registrados, pagos ou não; não são novas saídas do caixa.
- **Estimados e não informados:** separados, sem assumir zero para ausência de dados.
- **Margem de contribuição sobre custos registrados:** contratada menos custos diretos realizados; percentual dividido pelo valor contratado. Não é lucro líquido, saldo bancário nem uma DRE por competência.
- **Resultado após tributos atribuídos:** somente quando foram informados tributos realizados e não há pendências identificadas. Continua sendo parcial; não inclui custos gerais que não tenham sido registrados.

A ausência de pendências detectadas não prova que todos os custos foram cadastrados. O mecanismo de etapas da PR #48 continua independente: registrar custo ou pagamento não cria reconhecimento de receita por competência.

## Auditoria e documentos

Use filtros **Ativos**, **Inativos** e **Todos** e abra **Histórico de auditoria** para consultar usuário, data/hora, motivo e estados anterior/novo. Datas técnicas de auditoria são registradas em UTC.

O PDF de fechamento de mão de obra exige administrador no servidor e é um documento separado, explicitamente interno. Sua referência horária não comprova pagamento. O PDF normal e o PDF do cliente com preços de mão de obra não contêm custos internos, rateios ou margens. Os registros novos não são inseridos em propostas, NFS-e, e-mails ou exportações comerciais.

Não anexe documentos internos a uma área compartilhada com clientes: a segregação desta funcionalidade não reclassifica anexos históricos ou textos digitados manualmente pelo usuário.
