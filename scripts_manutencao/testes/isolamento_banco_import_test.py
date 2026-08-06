# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _db_fingerprint(db_path: Path) -> tuple[int, str, str]:
    script = (
        "import hashlib, pathlib, subprocess, sys\n"
        "p = pathlib.Path(sys.argv[1])\n"
        "data = p.read_bytes()\n"
        "size = len(data)\n"
        "sha1 = hashlib.sha1(data).hexdigest()\n"
        "git_hash = subprocess.check_output(['git', 'hash-object', str(p)], text=True).strip()\n"
        "print(f'{size}|{sha1}|{git_hash}')\n"
    )
    output = subprocess.check_output(
        [sys.executable, "-c", script, str(db_path)],
        text=True,
        cwd=str(db_path.parent),
    ).strip()
    size_str, sha1, git_hash = output.split("|")
    return int(size_str), sha1, git_hash


def _run_import(module_name: str, project_root: Path) -> None:
    env = os.environ.copy()
    env["FLASK_CONFIG"] = "testing"
    env["FLASK_ENV"] = "testing"
    env["PYTHONPATH"] = str(project_root)
    subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        cwd=str(project_root),
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_flask_config_tem_prioridade_sobre_flask_env():
    env = os.environ.copy()
    env["FLASK_CONFIG"] = "testing"
    env["FLASK_ENV"] = "production"
    script = (
        "from app.app import create_app\n"
        "app = create_app()\n"
        "print(app.config['TESTING'])\n"
        "print(app.config['SQLALCHEMY_DATABASE_URI'])\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert "True" in lines
    assert "sqlite:///:memory:" in lines


@pytest.mark.parametrize("module_name", ["app", "app.app"])
def test_import_nao_altera_erp_db_com_ambiente_testing(module_name: str):
    project_root = Path(__file__).resolve().parents[2]
    db_path = project_root / "erp.db"
    before = _db_fingerprint(db_path)
    _run_import(module_name, project_root)
    after = _db_fingerprint(db_path)
    assert before == after
    assert after == (
        0,
        "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
    )


def test_app_reexporta_mesma_instancia_global():
    env = os.environ.copy()
    env["FLASK_CONFIG"] = "testing"
    env["FLASK_ENV"] = "testing"
    script = (
        "import app as pkg\n"
        "import importlib\n"
        "mod = importlib.import_module('app.app')\n"
        "print(pkg.app is mod.app)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert "True" in result.stdout.splitlines()


def test_create_app_testing_usa_sqlite_memoria():
    env = os.environ.copy()
    env["FLASK_CONFIG"] = "testing"
    env["FLASK_ENV"] = "testing"
    script = (
        "from app.app import create_app\n"
        "app = create_app()\n"
        "print(app.config['TESTING'])\n"
        "print(app.config['SQLALCHEMY_DATABASE_URI'])\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert "True" in lines
    assert "sqlite:///:memory:" in lines
