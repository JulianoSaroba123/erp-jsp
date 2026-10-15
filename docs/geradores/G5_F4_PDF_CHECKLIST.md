# ERP JSP | G5-F4 | PDF A4 de Checklists de Geradores

**Estado:** implementação em branch dependente de G5-F3. Nenhum merge/deploy autorizado.

## Base e dependências
- G5-F1: catálogo versionado já publicado na main.
- G5-F2: PR #37, vínculo explícito OS↔geradores, migration `20261014_01`.
- G5-F3: PR #38, execução digital versionada, migration `20261014_02`.
- G5-F4: PDF de um checklist existente, **sem migration nova**.
- Dependência no projeto: `reportlab==4.0.7`, já presente no `requirements.txt`.

## Funcionamento
1. Na OS, entrar em **Geradores atendidos (G5)**, em seguida **Checklists digitais**.
2. Abrir ou iniciar checklist básico, intermediário ou avançado para um gerador vinculado à OS.
3. Na listagem ou página do checklist, clicar **PDF em branco** para impressão em campo:
   - dados da OS, cliente, gerador e componentes já identificados pelo snapshot;
   - referência dos consumíveis cadastrados claramente rotulada;
   - itens por seção, caixas de classificação vazias, medições e espaços de justificativa;
   - espaço para assinatura manual. O título declara que não há prova de execução.
4. Preencher o checklist digital e concluir após validação.
5. Selecionar **PDF preenchido**; este arquivo só existe quando o estado é `CONCLUIDO`.
   - exibe status reais, inclusive NC/NA/NR, medições e observações;
   - apresenta data, ID e momento de conclusão, identificação de usuário de conclusão;
   - assinatura manual permanece em branco. **Nenhuma assinatura eletrônica é simulada**.
6. O PDF preenchido continua acessível mesmo quando um gerador foi posteriormente inativado,
   pois usa somente as informações congeladas na execução.

## Implementação
- `app/geradores/gerador_checklist_pdf_service.py`: serviço sem banco, recebe execução
  com snapshots e retorna PDF A4 em bytes, diretamente de memória.
- `app/geradores/gerador_checklist_pdf_routes.py`: GET autenticado admin,
  modo `branco` / `preenchido`, resposta `application/pdf` e cabeçalhos `no-store`.
- `app/app.py`: blueprint adicional, sem alteração das rotas anteriores.
- Links nas telas G5-F3 para ambos os PDFs. PDF preenchido somente aparece após concluir.
- `scripts_manutencao/testes/geradores_g5_f4_pdf_checklist_test.py`:
  testes reais de geração e HTTP.
- `scripts_manutencao/gerar_amostras_g5_f4.py`: gera amostras em PDF no diretório temporário,
  com dados 100% fictícios e sem gravação no ERP. Executar para inspecionar visualmente
  A4 básico em branco, intermediário preenchido e avançado preenchido.

## Proteções
- Não há escrita no BD, arquivo temporário, uso de APIs externas ou movimentação
  financeira/estoque para gerar PDF.
- Dados cadastrais para impressão são obtidos do `identificacao_snapshot`,
  itens de `modelo_snapshot` e resultados de `respostas_snapshot`.
- Valida versão/tipo, IDs únicos, modo, situação de conclusão e completude da execução.
- Identificação é escapada antes de chegar ao renderizador ReportLab para não
  interpretar HTML de descrição/observações.
- Os links exigem login de administrador. Nada fica em cache HTTP público.
- O status CONFORME é registrado pelo técnico, sem avaliação automática contra
  valores normativos, que dependem de manual do fabricante e condições de ensaio.
- Consumíveis exibidos são **referências cadastradas**, nunca confirmação de troca.
- Renderização A4 usa paginação automática e cabeçalho/rodapé em todas as páginas;
  logo JSP local com fallback tipográfico, sem recursos de rede.

## Homologação obrigatória antes de integrar
1. Criar worktree isolada da F4 e verificar head `20261014_02` do Alembic.
2. Rodar testes F4 e toda a regressão F1/F2/F3 + G1/G2/G3.
3. Executar smoke HTTP do relatório G4 com dados fictícios.
4. Verificar visualmente os dois PDFs impressos A4 (quebras, status, unidades, nomes,
   caracteres PT-BR e logo) e PDF de preventiva avançada com várias páginas.
   Use `python -m scripts_manutencao.gerar_amostras_g5_f4` e abra os arquivos da pasta temporária exibida no console.
5. Conferir que não há vazamento de respostas em branco e que documento concluído
   preserva os valores do snapshot.
6. Manter PR em rascunho, sem publicação até autorização expressa. Como o Render
   aplica `alembic upgrade head` automaticamente, não antecipar migrações F2/F3.

## Limites conhecidos e próximos passos
- A função F4 não faz assinatura digital e não comprova execução sozinha.
- No F5, planejar histórico avançado, anexos autorizados, materiais efetivamente
  aplicados, assinatura e eventual liberação controlada a colaboradores.
- Não inferir execução, assinaturas ou notas de conformidade automaticamente.


## Revisão visual das três amostras (15/10/2026)
Arquivos analisados: básica em branco (4 páginas), intermediária preenchida (5 páginas),
avançada preenchida (5 páginas). Correções realizadas no código, ainda não homologadas:
1. No texto de observações, expressão de f-string gerava tupla Python `('',)`
   / `('ANOMALIA...',)` em vez do valor da observação.
2. Para formulários preenchidos, omitir linha de observação vazia e reduzir
   espaçamento de itens, sem ocultar qualquer anomalia ou justificativa registrada.
3. Agrupar título da seção ao seu primeiro item para não deixar títulos soltos
   no rodapé de páginas.
4. Corrigir os valores de medições das amostras fictícias: abandonar `12,5`
   repetido indiscriminadamente para pressão, temperatura, frequência, tensão
   e horímetro; usar exemplos identificados como fictícios.
5. Adicionar testes de regressão de observações e layout de blocos agrupados.

**Portão atual:** refazer testes e amostras no HEAD mais recente da branch F4,
revisar se a página final vazia/intermediária foi eliminada e aprovar somente
após inspeção dos novos PDFs A4. Nenhum merge/deploy autorizado.


## G5-F4-A2 | Falha Windows na gravação de amostras (15/10/2026)
A execução de homologação informou **53 testes aprovados** (PDF F4 + digital F3),
mas a geração de amostras falhou ao salvar no disco com `PermissionError:
[Errno 13] Permission denied` no caminho temporário fixo
`ERP_JSP_G5_F4_AMOSTRAS/AMOSTRA_BASICA_EM_BRANCO.pdf`.
Esse resultado não caracteriza erro na geração de PDF em memória;
a causa provável é um arquivo antigo bloqueado por um visualizador Windows,
ainda não confirmada definitivamente.

O script `scripts_manutencao/gerar_amostras_g5_f4.py` foi corrigido:
agora cada execução cria uma pasta única
`ERP_JSP_G5_F4_REVISAO_*` em `tempfile.gettempdir()`, imprime o caminho
e **nunca sobrescreve ou remove as amostras anteriores**.
Adicionado teste de isolamento entre duas pastas de revisão.

**Portão pendente:** validar o teste atualizado, executar o gerador no
commit corrigido e inspecionar as novas amostras. O PR não está pronto
para merge apenas com os 53 testes da revisão anterior.
