# Como ver logs do erro 500 no Render

1. Acesse: https://dashboard.render.com
2. Entre no serviço **erp-jsp-th5o**
3. Clique na aba **Logs**
4. Role até o final para ver o erro mais recente
5. Procure por linhas com:
   - `ERROR`
   - `Traceback`
   - `500`
   - `ImportError`
   - `NameError`

## Possíveis causas:

1. **make_response não importado** - VERIFICADO ✓ (está importado)
2. **Erro de sintaxe no template** - logs adicionados
3. **Deploy não concluído** - aguardar build
4. **Cache de módulo Python** - Render precisa reiniciar

## Solução rápida:

Se for erro de import, basta fazer um novo deploy vazio para forçar rebuild.
