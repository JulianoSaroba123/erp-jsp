# ERP JSP | G5-F5 | Fechamento integrado de checklists de geradores

**Status:** em desenvolvimento/homologação. F5 depende de F4 (#39), que depende de F3 (#38) e F2 (#37). Nenhum destes PRs está publicado.

## Objetivo da entrega

Entregar a primeira versão operacional completa **para administradores**:
OS -> associação de geradores -> abertura do checklist básico/intermediário/avançado ->
rascunhos -> conclusão -> consulta histórica -> PDF A4 em branco/preenchido.

Não confundir com assinatura eletrônica: o PDF possui campos **para assinatura manuscrita**.
Não foi implementada coleta digital de assinatura, anexos, liberação a colaboradores,
ou baixa automática de estoque; funcionalidades que demandariam controles adicionais.
A ausência dessas funções deve ser comunicada antes de uso comercial.

## Auditoria G5-F5

- Nova tabela aditiva `gerador_checklist_eventos`, migration `20261015_01`,
  `down_revision = 20261014_02`, com chave única `(execucao_id, sequencia)`,
  vínculos FK para checklist e usuário (o nome é congelado no evento).
- Toda abertura nova gera `CRIADO`; cada salvamento gera `RASCUNHO_SALVO`;
  a conclusão válida gera `CONCLUIDO`.
- O evento é gravado na **mesma transação** do checklist; se a transação for
  revertida, não fica auditoria órfã e não há falsa confirmação de operação.
- Histórico administrativo somente GET, login obrigatório, filtros por checklist;
  informa usuário, data/hora em UTC, ação, estado e SHA-256 das respostas.
- SHA-256 é conferência interna de integridade, **não assinatura eletrônica,
  prova de autoria, atestado de execução nem mecanismo inviolável**.
- PDF preenchido só é gerado se o último evento coincidir com o estado e
  as respostas do checklist. Divergência retorna HTTP 409 sem PDF.
- Não altera proposta/financeiro/fiscal/estoque/status da OS e não gera
  movimentação de materiais por selecionar uma referência técnica.
- A consulta de histórico de checklist concluído permanece disponível após
  inativação posterior de equipamento, por preservar registro histórico.

## Sequência obrigatória de integração

1. Homologar PR #37 (G5-F2), baseado em main. Executar suíte F2 + regressão
   e conferir migration head local F2 `20261014_01`.
2. Com autorização, integrar #37; confirmar Render live e Alembic em produção.
3. Rebase/retarget seguro de PR #38 à main e homologar novamente antes do merge;
   confirmar migration head `20261014_02` e Render live.
4. Rebase/retarget seguro do PR #39 à main depois de F3. Homologar PDF
   automatizado e visual; F4 **não adiciona migration**.
5. Depois das etapas anteriores, retarget do PR F5 à main, regressão completa,
   conferir head `20261015_01`, homologar fluxo real com dados fictícios e
   políticas de acesso, e pedir autorização de merge/deploy. Nunca publicar PRs
   dependentes fora de ordem nem aplicar migração manual em produção.
6. Após cada deploy, executar inspeções **read-only** e smoke HTTP autenticado
   com dados autorizados, sem criar OS, financeiro ou registros reais sem instrução.

## Critérios técnicos para homologação integrada de F5

- `python -m alembic heads`: exatamente um head `20261015_01`.
- Testes `geradores_g5_f5_historico_auditoria_test.py` e regressões
  `geradores_g5_f4_pdf_checklist_test.py`,
  `geradores_g5_f3_checklist_digital_test.py`,
  `geradores_g5_f2_vinculo_os_test.py`,
  `geradores_g5_f1_catalogo_test.py`,
  `geradores_g3_planos_horimetro_test.py`,
  `geradores_g2_componentes_test.py`,
  `geradores_g1_dominio_test.py`.
- Smoke G4 já presente nos testes F4, mas reexecutar via suíte.
- Validar em SQLite fictício: administradores conseguem criar, listar,
  preencher e visualizar histórico; usuários comuns recebem 403.
- Conferir tentativa de mutação de registro concluído e adulteração de JSON:
  PDF preenchido deve retornar 409 se SHA divergir.
- Revisar console para warnings novos em relação às versões anteriores
  e verificar worktree limpa após testes.
- A4: amostras de F4 no commit homologado: básica em branco 4 páginas,
  intermediária preenchida 4 páginas, avançada preenchida 4 páginas.
- Confirmar não existência de POST nos endpoints de exportação e histórico.
- Validar explicitamente que não há e-signature, coleta biométrica de assinatura
  nem anexos. A assinatura manuscrita do PDF é um campo, não uma assinatura capturada.

## Limites de segurança / escopo

- Esta versão é somente para administrador até elaborar autorização contextual
  para colaboradores por cliente, OS e vínculo de equipamento.
- Gerador duplicado na mesma OS é bloqueado; OS cancelada/inativa não recebe
  novas associações ou checklists.
- Os planos são checklists padronizados, não um parecer automático do estado
  de segurança. O técnico confirma os resultados, dados de sensores e condições
  reais dos testes, seguindo fabricante e procedimentos autorizados.
- Congelamento de snapshot mantém informações no PDF independente de futuras
  atualizações cadastrais.
- Hash apenas compara o **último** snapshot com o **último** evento registrado.
  Não prova que eventos antigos ou ambos os dados nunca sofreram edição direta
  por usuário com privilégio de banco.
- Ainda não há interface de retificação de histórico; correções em checklist
  concluído exigirão fluxo formal em implementação futura.
