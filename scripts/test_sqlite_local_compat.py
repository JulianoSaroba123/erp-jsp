from pathlib import Path

import sqlalchemy as sa


def test_sqlite_sem_prepare_threshold_e_requisicao_http(monkeypatch, tmp_path):
    db_path = tmp_path / "sqlite_compat.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from app.app import create_app
    from app.extensoes import db

    app = create_app("production")

    with app.app_context():
        assert db.engine.url.get_backend_name() == "sqlite"
        with db.engine.connect() as conn:
            assert conn.execute(sa.text("SELECT 1")).scalar() == 1

    with app.test_client() as client:
        resposta = client.get("/", follow_redirects=False)
        assert resposta.status_code in (200, 302)
