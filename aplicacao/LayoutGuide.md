Guia rápido para reaplicar o layout/estilo e filtros em outros módulos

Objetivo
- Centralizar o estilo e as convenções usadas no módulo de Clientes para reaplicá-las facilmente em outros módulos (ex.: Produtos, Fornecedores, Ordens).

Principais ativos já prontos
- `static/css/estilo_base.css` — Folha de estilo central com paleta 'robotic blue', classes utilitárias (`.card-jsp`, `.table-erp`, `.neo-thead`, `.btn-acao`, etc.).
- Filtro Jinja global `|tidy` registrado em `aplicacao/__init__.py` — remove a renderização literal de "None".
- Templates base:
  - `autenticacao/base.html` — layout base que todas as outras templates devem estender.
  - `aplicacao/cliente/templates/cliente/lista.html` — exemplo de lista transformada em linhas-card com `.table-erp`.
  - `aplicacao/cliente/templates/cliente/cadastro.html` — exemplo de formulário usando `|tidy` e integrações de CEP/CNPJ.

Como reaplicar no novo módulo (passo-a-passo)
1. Layout e herança
   - Garanta que as suas templates estendam `autenticacao/base.html`.
   - Evite duplicar seções de KPI — use o base para cards globais.

2. Estilos
   - Use classes existentes: contêiner principal `card-jsp`, cabeçalho `.card-header`, e tabelas com `.table-erp`.
   - Para headers de tabela use `.neo-thead` para aplicar o gradiente azul.
   - Mova estilos específicos do componente para `static/css/estilo_base.css` se precisar de ajustes.

3. Campos e valores
   - Use o filtro global `|tidy` ao renderizar campos que podem ser None: `{{ obj.campo|tidy }}`.
   - Remova macros locais `tidy` e padronize o uso do filtro.

4. Ações (editar/excluir)
   - Use formulários POST ou AJAX para ações destrutivas (excluir) e retorne JSON para chamadas AJAX.
   - No servidor, verifique vínculos antes de excluir, mas trate exceções quando o banco de desenvolvimento não tiver todas as tabelas.

5. Integrações úteis
   - Reaproveite o JS de busca ViaCEP e BrasilAPI (CNPJ) do arquivo de cliente; adapte os seletores dos campos do novo formulário.
   - Reutilize máscaras de input (jquery.mask) onde necessário.

6. Substituições automáticas (opcional)
   - Para converter templates antigas: procurar por macros `tidy` e substituí-las por `|tidy` e remover a macro. Exemplo de comando (no dev):
     - `grep -R "{% macro tidy" -n aplicacao | sed -n '1,200p'` (Unix) — no Windows PowerShell use ferramentas equivalentes ou um script Python simples.

7. Testes rápidos
   - Inicie a app e valide:
     - As listas aparecem (dados devem vir em `items` se usar paginate).
     - Campos não exibem "None".
     - A aparência segue o gradiente azul e as linhas ficam com cantos arredondados.

Notas finais
- Se quiser, eu posso automatizar a substituição em todo o projeto (remover macros e converter para `|tidy`) e aplicar a estrutura de layout para módulos existentes — diga quais módulos quer atualizar e eu faço em lote.

Arquivo gerado automaticamente para facilitar reaplicação do layout - commitado com as últimas alterações.
