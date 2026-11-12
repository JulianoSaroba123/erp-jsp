"""H4-F19 - contrato da auditoria local de prontidão operacional."""

import importlib.util
from pathlib import Path
import sys


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f19_auditoria_prontidao_operacional.py"
)


def _modulo():
    nome = "h4f19_auditoria_prontidao_testado"
    spec = importlib.util.spec_from_file_location(
        nome,
        SCRIPT,
    )
    modulo = importlib.util.module_from_spec(
        spec
    )
    sys.modules[
        nome
    ] = modulo
    spec.loader.exec_module(
        modulo
    )
    return modulo


def test_h4f19_001_classificacao_atual_e_backend_pronto_ui_legada():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert resultado[
        "classificacao"
    ] == (
        "BACKEND_SEFIN_PRONTO_UI_ROTAS_LEGADAS_PRODUCAO_BLOQUEADA"
    )


def test_h4f19_002_fundacao_sefin_esta_pronta():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert all(
        resultado[
            "fundacao_sefin"
        ].values()
    )


def test_h4f19_003_precheck_geisweb_foi_neutralizado():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert resultado[
        "acoplamentos_legados"
    ][
        "precheck_rota_geisweb"
    ] is False

    assert resultado[
        "protecoes"
    ][
        "precheck_rota_generica"
    ] is True

    assert (
        "PRECHECK_ROUTE_GEISWEB"
        not in resultado[
            "bloqueios"
        ]
    )


def test_h4f19_004_detecta_transmissao_geisweb_na_rota():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert resultado[
        "acoplamentos_legados"
    ][
        "transmissao_rota_geisweb"
    ] is True

    assert (
        "TRANSMISSION_ROUTE_GEISWEB"
        in resultado[
            "bloqueios"
        ]
    )


def test_h4f19_005_detecta_ui_legada():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert resultado[
        "acoplamentos_legados"
    ][
        "ui_menciona_geisweb"
    ] is True

    assert (
        "UI_GEISWEB"
        in resultado[
            "bloqueios"
        ]
    )


def test_h4f19_006_producao_continua_bloqueada():
    modulo = _modulo()

    resultado = modulo.executar_auditoria()

    assert resultado[
        "protecoes"
    ][
        "integracao_desativada_ao_salvar"
    ] is True

    assert resultado[
        "protecoes"
    ][
        "sem_rota_producao_explicita"
    ] is True


def test_h4f19_007_script_nao_usa_rede_ou_banco():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    ).lower()

    assert "import requests" not in texto
    assert "requests." not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto
    assert 'method="post"' not in texto
    assert ".post(" not in texto


def test_h4f19_008_auditoria_e_somente_leitura():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert ".write_text(" not in texto
    assert ".write_bytes(" not in texto
    assert "open(" not in texto
