from app.fiscal.providers.geisweb_tiete_config import (
    CODIGO_PROVIDER,
    ConfiguracaoGeisWebTieteInvalida,
    obter_configuracao_geisweb_tiete,
)
from app.fiscal.providers.geisweb_tiete_xml import (
    montar_xml_envio_lote_rps_serializado,
)
from app.fiscal.providers.geisweb_tiete_xsd import (
    validar_xml_envio_lote_rps,
)


def _dados_validos():
    return {
        "cnpj_cpf": "11111111000191",
        "numero_lote": "1",
        "rps": [
            {
                "numero_rps": "1",
                "data_emissao": "2026-09-19T09:00:00",
                "servico": {
                    "valores": {
                        "valor_servicos": "100.00",
                        "base_calculo": "100.00",
                        "aliquota": "2.00",
                    },
                    "codigo_servico": "140601",
                    "tipo_lancamento": "1",
                    "discriminacao": "Teste local ERP JSP",
                    "municipio_prestacao_servico": "3554508",
                },
                "prestador": {
                    "cnpj_cpf": "11111111000191",
                    "inscricao_municipal": "12345",
                    "regime": "1",
                },
                "tomador": {
                    "cnpj_cpf": "22222222000191",
                    "nif": "",
                    "nao_nif": "",
                    "razao_social": "CLIENTE TESTE",
                    "endereco": {
                        "rua": "RUA TESTE",
                        "numero": "100",
                        "bairro": "CENTRO",
                        "cidade": "TIETE",
                        "estado": "SP",
                        "cep": "18530000",
                        "pais": "BR",
                        "prov_reg": "",
                        "telefone": "",
                        "email": "",
                    },
                },
                "orgao_gerador": {
                    "codigo_municipio": "3554508",
                    "uf": "SP",
                },
                "outros_impostos": {
                    "pis": "0.00",
                    "cofins": "0.00",
                    "csll": "0.00",
                    "irrf": "0.00",
                    "inss": "0.00",
                },
                "ncm": "",
                "nbs": "",
                "codigo_nacional": "140601",
                "ibs_cbs": {
                    "c_class_trib": "000001",
                    "ibs": "0.00",
                    "cbs": "0.00",
                    "c_class_trib_reg": "000001",
                },
            }
        ],
    }


def test_configuracao_homologacao_geisweb_tiete():
    config = obter_configuracao_geisweb_tiete(
        "HOMOLOGACAO"
    )

    assert config["provider"] == CODIGO_PROVIDER
    assert config["municipio_ibge"] == "3554508"
    assert config["versao_layout"] == "1.01"
    assert "/homologacao/reforma/modelo/" in config["endpoint"]
    assert config["soap_version"] == "1.1"
    assert config["soap_style"] == "rpc"
    assert config["soap_use"] == "encoded"


def test_producao_permanece_bloqueada():
    try:
        obter_configuracao_geisweb_tiete(
            "PRODUCAO"
        )
    except ConfiguracaoGeisWebTieteInvalida:
        return

    raise AssertionError(
        "PRODUCAO deveria permanecer bloqueada."
    )


def test_xml_envio_lote_rps_valida_no_xsd():
    xml = montar_xml_envio_lote_rps_serializado(
        _dados_validos()
    )

    resultado = validar_xml_envio_lote_rps(
        xml
    )

    assert resultado.valido, resultado.erros

    assert b"EnviaLoteRps" in xml
    assert b"NumeroRps" in xml
    assert b"CodigoNacional" in xml
    assert b"IBSCBS" in xml
