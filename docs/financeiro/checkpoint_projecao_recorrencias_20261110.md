# CHECKPOINT DE HOMOLOGAÇÃO | ERP JSP | Projeção de Caixa 30/60/90 dias
**Data:** 10/11/2026 (America/Sao_Paulo)  
**Branch:** `feat/jsp-projecao-recorrencias-90d-20261109`  
**PR:** #59 (rascunho; não fazer merge ou deploy sem checkpoint final de aprovação)
**Origem:** inspeção read-only de `custos_fixos`, `lancamentos_financeiros`, `extratos_bancarios` do Render e revisão da regra do ERP.

## Situação de produção

- 11 custos ativos: **R$ 7.943,78/mês** (soma CADASTRAL, não DRE nem conta paga)
- Conta Cora: extratos até **09/11/2026**, **40/40 conciliados**; saldo bancário apurado no checkpoint anterior: **R$ 8.508,77**
- Não havia `lancamentos_financeiros` ativos vinculados a `custo_fixo_id`; os quatro antigos provisionados em fevereiro de 2026 estão **inativos**. Não reativar, nem gerar novamente retroativamente.
- Fluxo caixa projetado anterior ainda não contempla corretamente `conta_pagar`/`conta_receber` nem gastos fixos virtuais.
- **O valor de orçamento é uma estimativa, não obrigação fiscal/documental nem movimentação bancária.**

## Revisão individual dos cadastros ativos

| ID | Despesa | Valor cadastrado | Dia | Tratamento proposto |
|---:|---|---:|---:|---|
| 1 | Dr. Adinho Imóveis (aluguel) | R$ 1.000,00 | 10 | Aproxima-se da divisão acordada a partir de 11/2026; projetar. Não reclassificar outubro retroativamente |
| 2 | Energia elétrica | R$ 400,00 | 19 | Projetar **estimativa**; conferir fatura exata antes da baixa |
| 4 | Internet TVAC | R$ 130,00 | 20 | Projetar **estimativa**; out/2026 pago R$ 102,12; revisar orçamento |
| 5 | Vivo | R$ 119,00 | 10 | Projetar **estimativa** e conferir se não é a mesma linha do cadastro “Celular” |
| 6 | Samae água | R$ 120,76 | 13 | Projetar **estimativa**; substituir pelo documento real |
| 7 | Pró-labore | R$ 3.000,00 | 10 | **REVISAR**: referência informada R$ 2.800; separar remuneração do sócio de gasto comum |
| 8 | Contabilidade | R$ 350,00 | 10 | Projetar, valor cadastral consistente com referência informada |
| 9 | Cartão de crédito | R$ 341,31 | 10 | **REVISAR**: cartão é meio de pagamento; parcelas/fatura e compras já lançadas podem ser duplicadas |
| 10 | Celular | R$ 62,71 | 10 | **REVISAR**: verificar se já está contido na despesa Vivo |
| 11 | Sem Parar | R$ 220,00 | 10 | **REVISAR**: valor varia com uso de veículo; classificar orçamento variável |
| 12 | Auxiliar de manutenção | R$ 2.200,00 | 10 | **REVISAR**: auxiliares diaristas em custo direto; estimativa habitual 15 x R$120 = R$1.800, evitar misturar com salário fixo |

**Subtotal usado na simulação de contas fixas após separar os 5 cadastros em revisão:** R$ **2.119,76/mês**, antes de pró-labore, diaristas e outros compromissos. *Não representa o orçamento total da JSP*.

## Regras de proteção implementadas na PR #59

1. **Projeção SEM escrita** de 30/60/90 dias calcula mensalidades virtuais, com aviso claro de valor previsto.
2. Para cada competência, **um título financeiro ativo previamente vinculado impede a simulação do custo novamente**.
3. Título financeiro manual com correspondência documental de descrição/fornecedor impede estimativa paralela e gera alerta de revisão.
4. Títulos com status pago/recebido não entram como novas saídas ou entradas. Pendentes e vencidos entram sem alterar o banco.
5. A consulta bancária usa a referência documental Cora + extratos importados, deixando claro que não é consulta bancária em tempo real.
6. O botão **Provisionar Próximo Mês** exige administrador e token CSRF, grava somente `conta_pagar` **pendente** com vínculo ao custo fixo, lock, e verificações de duplicidade. Não baixa, não concilia e não atualiza extratos.
7. **Nenhum agendamento cron é habilitado**. Não fazer provisionamento em massa antes da revisão do cadastro.
8. A exportação Excel usa o mesmo cálculo da tela e informa as estimativas e pendências.

## Validação e liberação

- Executar CI completa SQLite e PostgreSQL da PR #59 na última versão.
- Revisar manualmente os valores de cada despesa e validar classificação pró-labore/diaristas.
- Exigir autorização específica para merge/deploy. O comando “pode seguir” autoriza a continuidade da revisão e desenvolvimento; não equivale a autorização para criar títulos reais em produção.
- Após eventual deploy, verificar que o saldo Cora e 40/40 conciliações não mudaram; testar somente a **visualização** e exportação da projeção, **sem clicar provisionar** até aprovação dos valores.

**Atenção:** previsões podem conter despesas fora das categorias atuais do ERP ou contas vencidas antigas; sinalizar em alertas e não assumir quitação.
