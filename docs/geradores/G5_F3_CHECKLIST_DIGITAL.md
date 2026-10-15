# ERP JSP | G5-F3 Execução digital de checklists (pré-homologação)

## Estado e dependência
F3 está em uma branch **derivada da F2**, que ainda não foi integrada à main.
A migration F3 (`20261014_02`) depende da F2 (`20261014_01`).
**Não publicar/migrar F3 em produção antes da homologação e integração da F2.**

## Fluxo entregue em desenvolvimento
1. Administrador abre OS e associa geradores usando G5-F2.
2. Clica **Checklists digitais**, escolhe gerador e manutenção básica, intermediária ou avançada.
3. Sistema cria no máximo um checklist de cada nível para o mesmo vínculo OS-gerador. Repetição recupera o existente.
4. Criação captura snapshot da OS, cliente, gerador, motor, alternador, controladora, QTA,
   bateria, carregador, referências de consumíveis e catálogo `G5-1.0`.
5. Na página responsiva, usuário registra status por item, medições com unidades,
   observações e data. Os itens são apresentados sem marcações iniciais.
6. `Salvar rascunho` permite formulário incompleto. `Concluir checklist`
   valida todos os itens, justificativas e medições; bloqueia novas edições.
7. Tentativa de concluir incompleto preserva, quando válido, o preenchimento em rascunho.
8. Documento concluído continua consultável por administrador mesmo depois
   de inativação do gerador, sem permitir sua edição.

## Segurança e limites
- No F3, somente **administradores**; colaboradores requerem política específica de autorização
  por OS e gerador, a desenvolver antes de liberar acesso.
- Formulários POST exigem CSRF; consulta exige sessão válida.
- Vínculos continuam garantindo mesmo `cliente_id`, OS ativa e gerador ativo durante criação/edição.
- Não altera status da OS, financeiro, fiscal ou movimentos de estoque.
- Conclusão do checklist **não é atestado automático de conformidade**: itens NC/NR/NA permanecem registrados.
- Conclusão registra usuário, data/hora, versão e snapshots imutáveis via interface.
- A futura página PDF deve usar **exclusivamente snapshots congelados**, nunca dados atuais do cadastro;
  deve disponibilizar versão em branco e preenchida, identificada por checklist/OS/gerador.
- Material cadastrado aparece como referência técnica, não significa que tenha sido consumido.
- Limitações conscientemente postergadas: assinatura eletrônica, anexos, controle de peças realmente
  aplicadas, liberação aos técnicos e revisões administrativas com trilha de retificação.

## Critérios de homologação
- Alembic head único `20261014_02`, dependência exata de `20261014_01`.
- Rodar `geradores_g5_f3_checklist_digital_test.py` com SQLite in-memory.
- Rodar junto G5-F2, G5-F1, G1-G3 e HTTP smoke G4.
- Testar manualmente no navegador com OS+geradores fictícios: 
  criar, reabrir, salvar incompleto, fechar com NC justificada, e tentar editar fechado.
- Inspecionar headers, erros de formulário, cobertura de frontend e controle de acesso.
- F3 não contém rota de PDF e não deve ser anunciado como produto completo.
- Merge/Render somente com autorização posterior; Alembic de produção é automático.
