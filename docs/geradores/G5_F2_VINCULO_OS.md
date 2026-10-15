# G5-F2 | Associação explícita OS ↔ Geradores | ERP JSP

**Estado:** branch de desenvolvimento, aguardando testes locais. **Não publicar antes de homologar.**

## Finalidade
Permitir que uma Ordem de Serviço comercial ou operacional registre um ou vários
grupos geradores do mesmo cliente. O objetivo é criar chaves confiáveis para o
checklist digital e os PDFs G5-F3/G5-F4, sem alterar valores, status ou fluxos
existentes da OS.

## Arquivos da etapa
- `app/geradores/gerador_os_vinculo_model.py`: model independente.
- `app/geradores/gerador_os_vinculo_service.py`: regras, idempotência e comparação por cliente.
- `app/geradores/gerador_os_vinculo_routes.py`: GET e POST protegidos por sessão, administrador e CSRF.
- `app/geradores/templates/geradores/geradores_da_os_g5.html`: tela de associação.
- `migrations/versions/20261014_01_geradores_g5_vinculo_os.py`: **migração aditiva** após `cdbaf09054ac`.
- `scripts_manutencao/testes/geradores_g5_f2_vinculo_os_test.py`: testes isolados.
- Registrado no `app/app.py`, `app/geradores/__init__.py` e botão somente admin no detalhe da OS.

## Regras implementadas
1. Chave composta única `(ordem_servico_id, gerador_id)` no PostgreSQL.
2. Mesmo gerador pode ser associado a diferentes OS, mas nunca duas vezes à mesma OS.
3. Gerador somente se `ativo=True`, `cliente_id` igual ao da OS.
4. OS ativa, não cancelada. Não altera status operacional, fiscal nem financeiro.
5. Repetição do mesmo vínculo retorna existente, sem criar segunda associação.
6. Associação inativa não é reativada silenciosamente.
7. Administração via formulário protegido com CSRF. Colaboradores não recebem acesso nesta fase.
8. Model e service não realizam commit; commit restrito à rota protegida.
9. Apenas tabela nova; nenhuma atualização/correção retroativa nos dados de OS/geradores.
10. Downgrade bloqueado se houver vínculos registrados, preservando dados históricos.

## Fluxo do usuário após deploy autorizado
- Abrir uma OS → **Geradores atendidos (G5)**.
- Conferir cliente e equipamentos vinculados.
- Selecionar um gerador do mesmo cliente e clicar **Vincular à OS**.
- Repetir para outros geradores da OS.
- A lista mostra o código do gerador, modelo/série e acesso à ficha técnica.
- O botão de preencher checklist não aparece em F2; será ativado após F3/F4.

## Pré-produção obrigatória
- `python -m alembic heads`: confirmar head único `20261014_01`.
- `python -m pytest -q --disable-warnings scripts_manutencao/testes/geradores_g5_f2_vinculo_os_test.py`.
- Regressão G1-G3, G5-F1 e smoke HTTP G4. Verificar GET admin, POST com CSRF,
  permissão negada a usuários comuns, cliente alheio, duplicidade, OS cancelada,
  OS com dois geradores.
- Testar cópia de banco ou SQLite descartável. Validar revisão Alembic e DDL
  conforme estratégia segura de produção. **Não rodar migration manual em produção**.
- Sem `git add .`, sem limpar worktrees, sem tocar em `launcher/`, `run.py.bak_encoding`
  ou `run.py.bak_utf8`.

## Próximas etapas para sistema completo
**G5-F3:** execução digital por vínculo, modelo versionado e dados congelados,
resultados de cada item, rascunhos, auditoria e controle por técnico autorizado.
**G5-F4:** PDF JSP A4 imprimível vazio e preenchido, baseado no mesmo snapshot.
**G5-F5:** anexos, assinatura e visão histórica, conforme homologação.

**Nenhuma destas etapas posteriores foi implementada neste PR.**
