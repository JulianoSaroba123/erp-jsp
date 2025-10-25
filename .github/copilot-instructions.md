# 🤖 Copilot Instructions for ERP JSP v3.0

These guidelines help AI coding agents work productively in this codebase. Focus on the project’s modular Flask architecture, conventions, and developer workflows.

## 🏗️ Project Architecture
- **Modular Flask App**: Each business domain (cliente, fornecedor, produto, painel, financeiro, etc.) is a subpackage in `app/`, with its own `*_model.py`, `*_routes.py`, and `templates/`.
- **Blueprints**: All routes are registered as Flask blueprints, grouped by module.
- **Database**: Uses SQLAlchemy ORM. Default is SQLite for dev (`database/database.db`), PostgreSQL for production (see `.env`).
- **Static & Templates**: Shared assets in `app/static/` and `app/templates/`. Each module has its own template folder.
- **Scripts**: Utility scripts for DB migration, debugging, and maintenance are in `scripts/`.

## ⚙️ Developer Workflows
- **Run App (dev)**: `python run.py` (uses `app/app.py` as entrypoint)
- **Create DB**: `python scripts/criar_tabelas.py`
- **Debug**: Use `python scripts/debug_app.py` for interactive debug menu, or `python scripts/debug.py` for full-stack checks.
- **Test Page**: `python test_page.py` checks if main endpoints are up.
- **Install Deps**: `pip install -r requirements.txt`
- **Deploy**: See `README.md` for Render instructions and required env vars.

## 📦 Conventions & Patterns
- **File Naming**: `snake_case.py` for files, `PascalCase` for classes, `snake_case` for functions/vars, `UPPER_CASE` for constants.
- **Blueprint Registration**: Each module’s routes are registered in `app/app.py`.
- **Templates**: Always extend `base.html`. Use blocks: `title`, `breadcrumb`, `content`.
- **Colors/Branding**: Use the color palette in `CORES_JSP_IMPLEMENTADAS.md` and `README.md`.
- **Cache Control**: For PDFs and proposal routes, set anti-cache headers (see `CACHE_MANAGEMENT.md`).
- **Environment Config**: Use `app/config.py` and `.env` for all secrets and DB URLs. See `PADRAO_JSP_v3.md` for variable examples.

## 🔗 Integration Points
- **PDF Generation**: Proposal PDFs use custom templates and logo logic (see `LOGO_RESOLVIDA.md`).
- **Financeiro Module**: Fully integrated, see `MODULO_FINANCEIRO_COMPLETO.md` for structure and status.
- **API Endpoints**: Documented in `README.md`.

## 📝 Examples
- **Add new module**: Copy structure from `app/cliente/` or `app/financeiro/`.
- **Add route**: Create `*_routes.py` in module, register blueprint in `app/app.py`.
- **Add template**: Place in `app/<module>/templates/<module>/`, extend `base.html`.

## 🐛 Troubleshooting
- See `README.md` for common errors and fixes (import errors, DB creation, dependencies).

---
For more details, see: `README.md`, `PADRAO_JSP_v3.md`, and module-specific markdown files.
