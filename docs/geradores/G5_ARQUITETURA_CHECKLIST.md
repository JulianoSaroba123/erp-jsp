# ERP JSP | G5 - Checklist digital e PDF de manutenção de grupos geradores

**Estado:** arquitetura e fundação G5-F1 em desenvolvimento, sem publicação.
**Escopo:** Grupo Gerador + Equipamento (quando vinculado) + Plano + OS + Checklist.
**Regra de segurança:** F1 não registra manutenções no banco, não altera OS, não gera PDF em produção, não movimenta peças nem cria receita.

## 1. Diagnóstico fundamentado no repositório (2026-10)

- `app/geradores/gerador_model.py`: `Gerador` referencia cliente, unidade e opcionalmente `Equipamento` genérico por `equipamento_id`.
- `app/geradores/gerador_plano_model.py`: `PlanoManutencao` com tipos **BASICA**, **INTERMEDIARIA**, **AVANCADA**, herança de plano e programação.
- `app/geradores/gerador_consumivel_model.py`: filtros/consumíveis e equivalentes do gerador, com referência opcional ao produto de estoque. Essa referência **não significa saída de estoque**.
- `app/geradores/gerador_plano_ui_routes.py`: relatório técnico G4 consultivo e interface de planos/horímetro.
- `app/ordem_servico/ordem_servico_model.py`: OS com `cliente_id`, `proposta_id` opcional, `equipamento`, `marca_modelo` e `numero_serie` como texto. **Ainda não há FK direta OS → Gerador**; não inferir pelo texto ou número de série.
- `app/app.py`: registro das rotas de Geradores e G4 já existentes, a manter inalteradas no F1.
- Colaboradores têm whitelist global restrita. O acesso futuro do técnico a checklist não pode abrir indiscriminadamente os demais módulos.

## 2. Jornada funcional proposta

1. Proposta aprovada pode originar OS; OS direta também é válida.
2. Usuário autorizado abre a OS e vincula **explicitamente** um ou mais geradores do **mesmo cliente**. Não escolher equipamento por coincidência de nome/série.
3. Seleciona plano (básica, intermediária ou avançada) e escopo contratual. O catálogo sugere itens; qualquer item não previsto no escopo é explicitamente marcado `NAO_APLICAVEL` com justificativa ao finalizar.
4. Pode imprimir o **checklist em branco** com cabeçalho preenchido do cadastro, para uso em campo.
5. Pode preencher pelo celular/computador, salvar rascunhos e registrar medições, resultados, observações, referências/quantidades de filtros e fotos anexadas com permissão.
6. Finaliza somente após classificação de todos os itens e justificativas de exceções. `NAO_REALIZADO` é um resultado legítimo, **nunca sinônimo de conforme**.
7. Gera o **PDF preenchido**, preservando uma cópia dos dados técnicos e das respostas na data do fechamento.
8. Relatório técnico geral continua independente. Checklist e relatório podem ser anexados/consultados na ficha do gerador e na OS.

## 3. Arquitetura por entregas com bloqueios de publicação

| Etapa | Entrega | Migração | Publicação |
|---|---|---|---|
| **G5-F1** | `gerador_checklist_catalogo.py` puro, itens por nível, IDs estáveis, validação do preenchimento, testes | Não | PR draft, somente após regressão |
| **G5-F2** | Associação explícita OS ↔ Gerador (N:N, inclusive múltiplos geradores na mesma OS); conferir `cliente_id`; modelos SQLAlchemy e migration Alembic controlada | Sim, em branch separada | Somente após revisão backup/migration |
| **G5-F3** | Formulário responsivo, salvamento de rascunho, validação no servidor, anexos controlados, histórico/auditoria | Conforme necessidade | Após testes de autorização e CSRF |
| **G5-F4** | Templates A4 JSP, PDF em branco e preenchido baseados no MESMO snapshot versionado; WeasyPrint via bytes/memória | Não obrigatória | Após validar impressão/renderização |
| **G5-F5** | Integração com OS/ficha gerador, assinatura/supervisão, exportação, trilha de revisões e regressão completa | Conforme necessidade | Deploy monitorado |

F1 **não** registra blueprint, não importa SQLAlchemy/Flask, não altera modelos, rotas ou templates existentes.

## 4. Modelo de dados futuro (não implementado em F1)

**`gerador_os_vinculos`**: `id, ordem_servico_id, gerador_id, vinculado_por, data_vinculo, ativo`. Único vínculo ativo por par; exigir `OS.cliente_id == Gerador.cliente_id`. Não aceitar OS cancelada ou cliente divergente sem tratamento explícito. A OS pode atender vários grupos.

**`gerador_checklist_execucoes`**: `id, gerador_os_vinculo_id, plano_id (opcional), tipo_plano, versao_catalogo, modelo_snapshot (JSONB), estado (RASCUNHO/EM_EXECUCAO/CONCLUIDO/CANCELADO), horimetro_inicial/final, datas, responsavel_id, observacoes, resultado_snapshot (JSONB), finalizado_por/em, criacao/atualizacao, ativo`. No início, congelar identificação do cliente, OS, gerador, motor/alternador/controladora, especificação dos consumíveis e versão do modelo. Garantir versão para auditoria mesmo após mudança cadastral.

**`gerador_checklist_respostas`**: `id, execucao_id, item_id, status, medicao, unidade, observacao, atualizado_por/em`; `UNIQUE(execucao_id, item_id)`. Rejeitar itens estranhos ao snapshot do modelo e status fora do domínio. Em fechamento, congelar snapshot e bloquear edição direta; correções exigem revisão auditável.

**`gerador_checklist_anexos`** (etapa posterior): imagens com validação MIME/tamanho, origem segura e associação à execução; não injetar dados arbitrários no PDF.

**Assinaturas:** nome, função, momento e evidência de consentimento quando implantadas. Campos de assinatura manual permanecem no PDF imprimível, sem simular assinatura eletrônica.

## 5. Contrato do catálogo G5-F1

`obter_modelo(tipo)` retorna dicionário novo com `versao`, `tipo` e `secoes[]` com itens ordenados (`id`, `descricao`, `unidade`, `status=None`). Herança é **aditiva**: intermediária agrega básica e avançada agrega intermediária.

`validar_respostas(tipo, respostas, encerrar=False)` normaliza/valida os dados, sem persistir:
- status explícitos: `CONFORME`, `NAO_CONFORME`, `NAO_APLICAVEL`, `NAO_REALIZADO`;
- rascunho pode deixar itens sem resposta, conclusão **não**;
- NC, NA e NR exigem justificativa ao encerrar;
- medição numérica é exigida no encerramento para item mensurável marcado conforme/não conforme;
- unidade apresentada não é limite técnico. **Faixas de aceitação vêm do manual do motor/alternador/controladora, do plano e das condições de teste**;
- títulos e itens técnicos são modelo inicial, revisáveis com versionamento e responsável técnico; nenhuma ação com risco é disparada por software;
- rejeitar chaves desconhecidas, medições não numéricas e payloads excessivos.

**Não é seguro marcar automaticamente todos os itens como CONFORME**, nem concluir execução porque um PDF foi baixado.

## 6. Integração com consumíveis e peças

O cadastro existente fornece referência original/equivalente, quantidade e unidade. O checklist terá campos **previsto**, **aplicado**, **lote/referência** e **observações**, porém isso **não fará baixa de estoque** no G5. Eventual saída de material usará o fluxo próprio Estoque/OS com vinculação e idempotência, em projeto posterior.

## 7. Segurança

- `login_required` e autorização por objeto para técnico, gestor e auditor, verificando acesso à OS/gerador; colaboradores só em OS próprias, via alteração explícita da whitelist.
- GET para visualizar/imprimir; POST com CSRF para salvar; impedir IDOR, usar IDs internos validados, nunca confiar em `cliente_id` vindo do form.
- Campos de engenharia não devem aparecer no Financeiro automaticamente; o checklist não altera pedido/proposta/OS/Financeiro/Fiscal.
- A conclusão é um ato técnico humano. Exames de trip, partida, transferência, isolamento e carga só com procedimento de segurança e autorização específicos; `NAO_REALIZADO` e `NAO_APLICAVEL` devem permanecer auditáveis.
- Migrações futuras com Alembic head único, backup, `upgrade` testado e estratégia de rollback/compatibilidade. Evitar alterar produção por experimentos.

## 8. PDF

Dois modos de impressão A4:
- **Em branco**: logo JSP, cliente/unidade, proposta/OS, gerador, motor/alternador/controladora, horímetro (em branco quando não medido), filtros especificados, caixas de status vazias, leituras, recomendações e assinaturas.
- **Preenchido**: identificação congelada, status marcado, valores/unidades, observações, anomalias, consumíveis utilizados, data e responsável; rodapé de versão e identificador de execução. Exibir situação real, inclusive pendências e itens não realizados.

A implementação gerará o PDF em memória, validará `%PDF-`, layout, margens, quebra de página e caracteres PT-BR. Não embutir recursos externos não confiáveis e não permitir SVG/HTML arbitrário nos registros.

## 9. Critérios de aceite para avançar F1 → F2

- Testes unitários do catálogo e validador aprovados; regressão G1/G2/G3/G4 preservada.
- Conferir com técnico responsável as listas de itens dos três níveis, sem presumir que todos sejam aplicáveis a todos os motores e QTA.
- Nenhum arquivo preexistente do sistema modificado em F1; sem migration, BD, menu, botões falsos, novas rotas nem side effects.
- Somente depois da homologação definir associação OS↔Gerador e modelo de dados.
- Manter fora do stage `launcher/`, `run.py.bak_encoding`, `run.py.bak_utf8`; jamais `git add .` ou `git add -A`.
