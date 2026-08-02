import ast
from pathlib import Path


def _load_env_helpers():
    env_path = Path(__file__).resolve().parents[2] / "migrations" / "env.py"
    source = env_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    wanted = {"_normalize_database_url", "_resolve_database_url"}
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]

    module = ast.Module(body=selected, type_ignores=[])
    namespace = {}
    exec(compile(module, str(env_path), "exec"), namespace)
    return namespace["_normalize_database_url"], namespace["_resolve_database_url"]


def test_normaliza_prefixos_postgres_para_psycopg3():
    normalize, _ = _load_env_helpers()
    assert normalize("postgres://u:p@h:5432/db") == "postgresql+psycopg://u:p@h:5432/db"
    assert normalize("postgresql://u:p@h:5432/db") == "postgresql+psycopg://u:p@h:5432/db"
    assert normalize("postgresql+psycopg2://u:p@h:5432/db") == "postgresql+psycopg://u:p@h:5432/db"


def test_resolve_prioriza_database_url_e_faz_fallback():
    _, resolve = _load_env_helpers()
    assert resolve("postgresql://a:b@x:5432/y", "sqlite:///tmp/fallback.db") == "postgresql+psycopg://a:b@x:5432/y"
    assert resolve(None, "postgresql://f:g@z:5432/w") == "postgresql+psycopg://f:g@z:5432/w"
    assert resolve(None, "sqlite:///tmp/local.db") == "sqlite:///tmp/local.db"
