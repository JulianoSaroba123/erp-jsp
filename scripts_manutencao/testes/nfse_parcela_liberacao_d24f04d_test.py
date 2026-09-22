from pathlib import Path

from app import create_app


def test_rota_liberacao_esta_registrada():
    app = create_app("testing")

    rotas = {
        regra.endpoint: regra.rule
        for regra in app.url_map.iter_rules()
    }

    endpoint = (
        "ordem_servico."
        "liberar_nfse_parcela_para_envio"
    )

    assert endpoint in rotas

    assert rotas[endpoint] == (
        "/ordem_servico/<int:id>/fiscal/parcela/"
        "<int:parcela_id>/liberar-envio"
    )


def test_rota_usa_gate_sem_transmitir():
    fonte = Path(
        "app/ordem_servico/ordem_servico_routes.py"
    ).read_text(
        encoding="utf-8"
    )

    inicio = fonte.index(
        "def liberar_nfse_parcela_para_envio"
    )

    fim = fonte.index(
        "@ordem_servico_bp.route('/<int:id>/apontamento'",
        inicio,
    )

    bloco = fonte[inicio:fim]

    assert (
        "liberar_documento_nfse_geisweb_para_envio("
        in bloco
    )

    assert "db.session.commit()" in bloco

    assert "transmitir_documento_nfse" not in bloco
    assert "transmitir_payload" not in bloco
    assert "requests." not in bloco
    assert "SOAP" in bloco


def test_interface_expoe_botao_apenas_para_preparada():
    fonte = Path(
        "app/ordem_servico/templates/os/"
        "_painel_fiscal_parcelas.html"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "documento.status == 'PREPARADA'"
        in fonte
    )

    assert "Liberar para envio" in fonte

    assert (
        "documento.status == 'PENDENTE_ENVIO'"
        in fonte
    )

    assert "Ainda n&atilde;o transmitido" in fonte
