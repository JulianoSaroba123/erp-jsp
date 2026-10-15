# -*- coding: utf-8 -*-
"""S26-D1 | Configuração segura Flask / Render.

Teste isolado da seleção de ambiente sem importar a aplicação, inicializar
Flask-SQLAlchemy, executar migrations ou acessar bancos externos.
"""
import importlib.util
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def config_isolada():
    spec = importlib.util.spec_from_file_location(
        "jsp_config_seguranca_isolada", ROOT / "app" / "config.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_sem_flask_env_usa_producao_por_padrao(config_isolada):
    assert config_isolada.resolver_configuracao_flask(environ={}) == "production"


@pytest.mark.parametrize("valor", ["development", "testing", "production"])
def test_perfis_locais_exigem_escolha_explicita(config_isolada, valor):
    assert config_isolada.resolver_configuracao_flask(
        environ={"FLASK_ENV": valor}
    ) == valor


@pytest.mark.parametrize("valor", ["development", "testing"])
def test_render_bloqueia_perfil_inseguro(config_isolada, valor):
    with pytest.raises(RuntimeError, match="Render exige"):
        config_isolada.resolver_configuracao_flask(
            environ={"RENDER": "true", "FLASK_ENV": valor}
        )


@pytest.mark.parametrize("campo,valor", [
    ("RENDER", "true"),
    ("RENDER", "1"),
    ("RENDER_SERVICE_ID", "srv-exemplo"),
])
def test_render_aceita_somente_producao(config_isolada, campo, valor):
    assert config_isolada.resolver_configuracao_flask(
        environ={campo: valor, "FLASK_ENV": "production"}
    ) == "production"


def test_render_sem_flask_env_continua_producao(config_isolada):
    assert config_isolada.resolver_configuracao_flask(
        environ={"RENDER": "true"}
    ) == "production"


def test_render_nao_aceita_config_nomeada_testing(config_isolada):
    with pytest.raises(RuntimeError, match="Render exige"):
        config_isolada.resolver_configuracao_flask(
            "testing", environ={"RENDER": "true", "FLASK_ENV": "production"}
        )


def test_selecao_explicita_local_testing_preservada(config_isolada):
    assert config_isolada.resolver_configuracao_flask(
        "testing", environ={}
    ) == "testing"


@pytest.mark.parametrize("valor", ["", "default", "invalid", "produção"])
def test_config_invalida_nao_cai_silenciosamente_em_development(config_isolada, valor):
    if valor == "":
        assert config_isolada.resolver_configuracao_flask(
            environ={"FLASK_ENV": valor}
        ) == "production"
    else:
        with pytest.raises(RuntimeError, match="Perfil Flask inválido"):
            config_isolada.resolver_configuracao_flask(
                environ={"FLASK_ENV": valor}
            )


def test_flask_production_debug_desativado_e_cookie_seguro(config_isolada):
    flask = Flask("jsp_seguro_test")
    flask.config.from_object(config_isolada.config["production"])
    assert flask.debug is False
    assert flask.testing is False
    assert flask.config["SESSION_COOKIE_SECURE"] is True


def test_development_preserva_debug_apenas_quando_pedido(config_isolada):
    flask = Flask("jsp_dev_test")
    flask.config.from_object(config_isolada.config["development"])
    assert flask.debug is True


def test_factory_registra_perfil_real_sem_inferir_env_flask_antigo():
    fonte = (ROOT / "app" / "app.py").read_text(encoding="utf-8")
    assert "resolver_configuracao_flask(config_name)" in fonte
    assert "app.config['JSP_CONFIG_PROFILE'] = config_name" in fonte
    assert "DEBUG=True bloqueado" in fonte


def test_log_mostra_perfil_real_da_factory():
    fonte = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
    assert "app.config.get('JSP_CONFIG_PROFILE'" in fonte
    assert "app.config.get('ENV', 'production')" not in fonte


def test_launcher_local_nao_forca_debug():
    fonte = (ROOT / "run.py").read_text(encoding="utf-8-sig")
    assert "debug=modo_desenvolvimento" in fonte
    assert "app.config['DEBUG'] = modo_desenvolvimento" in fonte
    assert "debug=True" not in fonte
    assert "app.config['DEBUG'] = True" not in fonte


def test_render_blueprint_declara_ambiente_e_debug_zero():
    fonte = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "FLASK_ENV\n        value: production" in fonte
    assert 'FLASK_DEBUG\n        value: "0"' in fonte
