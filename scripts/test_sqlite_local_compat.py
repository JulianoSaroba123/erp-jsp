import os
import subprocess
import sys
from pathlib import Path


def test_sqlite_sem_prepare_threshold_e_requisicao_http(monkeypatch, tmp_path):
    db_path = tmp_path / "sqlite_compat.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    # Run in a subprocess so DATABASE_URL is read before importing app.config.
    script = """
import sqlalchemy as sa
from app.app import create_app
from app.extensoes import db

app = create_app('production')
with app.app_context():
    assert db.engine.url.get_backend_name() == 'sqlite'
    with db.engine.connect() as conn:
        assert conn.execute(sa.text('SELECT 1')).scalar() == 1

with app.test_client() as client:
    resposta = client.get('/', follow_redirects=False)
    assert resposta.status_code in (200, 302)
"""

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    env.setdefault("FLASK_CONFIG", "production")
    env.setdefault("FLASK_ENV", "production")

    subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
