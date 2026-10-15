# ERP JSP | S26-D1 | Flask debug desativado em produção

## Incidente observado
Após publicar G5-F5 em 15/10/2026, o Render (serviço `erp-jsp`)
iniciou Flask com `Debug: True`, apesar de o console imprimir
`Configuracao: production`.

### Diagnóstico
- `app/app.py` escolhia `FLASK_ENV` com fallback `development`.
- `DevelopmentConfig.DEBUG=True`, `ProductionConfig.DEBUG=False`.
- `app/__init__.py` imprimia `app.config.get('ENV','production')`, mas Flask 3
  não fornece necessariamente a chave ENV. O rótulo era enganoso.
- O comando do Render é `gunicorn app:app`, não `python run.py`;
  contudo, `run.py` habilitava debugger incondicionalmente.
- `render.yaml` já declarava `FLASK_ENV=production`, mas o serviço
  existente não estava refletindo essa configuração.

## Contenção concluída no Render
Atualizadas **somente** as variáveis `FLASK_ENV=production` e `FLASK_DEBUG=0`,
mescladas às existentes (`replace=false`, sem consultar/exibir credenciais).
Deploy disparado automaticamente `dep-db8jtlu7bikc739bogbg`, commit G5 `2500261`.
Após publicação, logs confirmaram:
`Configuracao: production` e `Debug: False`, servidor **live** e
login HTTP 200. Nenhuma alteração no schema ou na migration G5.

## Defesa em profundidade (este PR)
- Factory Flask usa **production** quando `FLASK_ENV` não é declarada;
  desenvolvimento/testes precisam ser selecionados explicitamente.
- Execução detectada no Render (`RENDER=true` ou `RENDER_SERVICE_ID`)
  rejeita perfil diferente de production, interrompendo startup inseguro.
- A factory grava `JSP_CONFIG_PROFILE` com a seleção real.
- Log de startup mostra o perfil real, não um fallback arbitrário.
- `run.py` só habilita debugger em `development` local explícito.
- `render.yaml` declara `FLASK_DEBUG=0` para novas instalações.
- `scripts_manutencao/testes/seguranca_config_debug_render_test.py`
  valida a seleção do ambiente isoladamente sem inicializar banco.

## Gates de integração
1. Em worktree limpa e isolada, executar:
   `python -m pytest -q --disable-warnings scripts_manutencao/testes/seguranca_config_debug_render_test.py`
2. Regressão dos checklists G1-G5, ou smoke controlado da factory se
   disponível; não inicializar sistema apontando para PostgreSQL real.
3. Revisar diff: somente `app/app.py`, `app/config.py`, `app/__init__.py`,
   `run.py`, `render.yaml`, documentação e teste.
4. Integrar apenas após testes aprovados e autorização de merge/deploy.
5. Após deploy, confirmar Render live, `Configuracao: production`,
   `Debug: False`, endpoint /auth/login HTTP 200 e Alembic `20261015_01`.

## Observações de segurança
- Não imprimir, copiar, substituir nem rotacionar `DATABASE_URL` ou
  `SECRET_KEY` neste ajuste.
- Aplicação em produção deve sempre usar Gunicorn; o servidor embutido do
  Flask é apenas para desenvolvimento local.
- Mudança do padrão para production exige que o desenvolvedor defina
  `FLASK_ENV=development` **explicitamente** em sua máquina para modo de debug.
- O fallback local de `SECRET_KEY` é um tema de endurecimento separado:
  avaliar sem derrubar sessões de produção, nunca modificar inadvertidamente.
