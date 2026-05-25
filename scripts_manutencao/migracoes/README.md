# Scripts de Migração e Importação

Scripts para migrar dados entre ambientes (local ↔ Render) e importar dados.

## Quando usar:
- Migração de dados do SQLite local para PostgreSQL Render
- Sincronização de dados entre ambientes
- Importação de dados de backup
- Correção de estrutura de banco de dados

## Arquivos principais:
- `importar_*.py` - Importação de dados
- `migrar_*.py` - Migrações de estrutura e dados
- `fix_*.py` - Correções específicas no banco
- `sync_*.py` - Sincronização entre ambientes

**AVISO:** Execute com cuidado! Sempre faça backup antes de rodar scripts de migração.
