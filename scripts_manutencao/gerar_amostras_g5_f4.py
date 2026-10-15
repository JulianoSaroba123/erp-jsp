# -*- coding: utf-8 -*-
"""G5-F4: gera PDFs de demonstração SOMENTE COM DADOS FICTÍCIOS.

Uso:
    python -m scripts_manutencao.gerar_amostras_g5_f4

Saída: pasta temporária do Windows/Linux, fora da worktree.
Não envia dados, não usa registros reais, não modifica o banco.
"""
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

# Fundamental: antes de qualquer import do pacote app.
os.environ["FLASK_ENV"] = "testing"
os.environ["FLASK_CONFIG"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.geradores.gerador_checklist_catalogo import (
    VERSAO_CATALOGO, obter_modelo, validar_respostas,
)
from app.geradores.gerador_checklist_pdf_service import gerar_pdf_checklist


def execucao_ficticia(tipo):
    modelo = obter_modelo(tipo)
    identificacao = {
        "os": {
            "id": 1, "numero": "OS-AMOSTRA-0001",
            "titulo": "EXEMPLO DE HOMOLOGAÇÃO - SEM CLIENTE REAL",
            "data_abertura": date.today().isoformat(),
        },
        "cliente": {"id": 1, "nome": "CLIENTE DE TESTE - DADOS FICTÍCIOS"},
        "gerador": {
            "id": 1, "codigo": "GER-AMOSTRA-0001",
            "descricao": "Grupo gerador demonstrativo",
            "fabricante": "FABRICANTE DEMONSTRATIVO",
            "modelo": "MODELO SIMULADO",
            "numero_serie": "FICTICIO-123456",
            "potencia_kva": "360.00", "tensao": "380/220 V",
            "local_instalado": "AMBIENTE DE HOMOLOGAÇÃO",
        },
        "motor": {
            "fabricante": "MOTOR FICTÍCIO", "modelo": "MOTOR-TESTE",
            "numero_serie": "MOT-TESTE",
        },
        "alternador": {
            "fabricante": "ALTERNADOR FICTÍCIO", "modelo": "ALT-TESTE",
            "numero_serie": "ALT-TESTE",
        },
        "controladora": {"fabricante": "KVA (EXEMPLO)", "modelo": "K30i (EXEMPLO)"},
        "qta": {"fabricante": "FABRICANTE TESTE", "modelo": "ATS-TESTE"},
        "bateria": {
            "fabricante": "BATERIA TESTE", "modelo": "MODELO TESTE",
            "tensao_nominal_v": "24",
        },
        "carregador": {"fabricante": "MODELO TESTE", "modelo": "CARREGADOR TESTE"},
        "consumiveis": [
            {
                "tipo": tipo_consumivel, "fabricante": "FABRICANTE TESTE",
                "referencia": ref, "descricao": "Referência fictícia",
                "quantidade": "1", "unidade": "un",
            }
            for tipo_consumivel, ref in [
                ("FILTRO_OLEO", "REF-OLEO-TESTE"),
                ("FILTRO_COMBUSTIVEL", "REF-DIESEL-TESTE"),
                ("FILTRO_AR_PRIMARIO", "REF-AR-TESTE"),
            ]
        ],
    }

    # Leituras meramente demonstrativas, coerentes com as unidades dos itens.
    # Nunca confundir amostras com faixa de aceitação ou valores medidos reais.
    leituras_ficticias = {
        "MOT_HORIMETRO": "1534,2",
        "MOT_PRESSAO_OLEO": "3,8",
        "MOT_TEMPERATURA": "86",
        "ELE_BATERIA": "27,2",
        "ELE_TENSAO": "380",
        "ELE_FREQUENCIA": "60",
        "ELE_CORRENTE": "285",
    }
    respostas = {}
    for item in (
        item for secao in modelo["secoes"] for item in secao["itens"]
    ):
        status = "CONFORME"
        if item["id"] == "SEG_EPI":
            status = "NAO_CONFORME"
        elif item["id"] == "PROT_PRESSAO":
            status = "NAO_REALIZADO"
        respostas[item["id"]] = {
            "status": status,
            "medicao": (
                leituras_ficticias.get(item["id"], "0")
                if item["unidade"] and status == "CONFORME" else ""
            ),
            "observacao": (
                "ANOMALIA SIMULADA - apenas para validar paginação e campos."
                if status == "NAO_CONFORME"
                else "TESTE NÃO EXECUTADO - autorização fictícia ausente."
                if status == "NAO_REALIZADO"
                else "",
            ),
        }
    validado = validar_respostas(tipo, respostas, encerrar=True)
    return SimpleNamespace(
        id=9999, versao_catalogo=VERSAO_CATALOGO,
        tipo_plano=tipo, estado="CONCLUIDO",
        modelo_snapshot=modelo, identificacao_snapshot=identificacao,
        respostas_snapshot=validado,
        data_servico=date.today(),
        observacoes_gerais=(
            "ARQUIVO DE DEMONSTRAÇÃO. Dados inteiramente fictícios; "
            "não comprova manutenção real. Avaliar a impressão em A4."
        ),
        concluido_por_id=9999,
        concluido_em=datetime.now(),
    )


def main():
    destino = Path(tempfile.gettempdir()) / "ERP_JSP_G5_F4_AMOSTRAS"
    destino.mkdir(parents=True, exist_ok=True)

    exemplos = [
        ("AMOSTRA_BASICA_EM_BRANCO.pdf", "BASICA", "branco"),
        ("AMOSTRA_INTERMEDIARIA_PREENCHIDO.pdf", "INTERMEDIARIA", "preenchido"),
        ("AMOSTRA_AVANCADA_PREENCHIDO.pdf", "AVANCADA", "preenchido"),
    ]
    for nome, tipo, modo in exemplos:
        caminho = destino / nome
        arquivo = gerar_pdf_checklist(execucao_ficticia(tipo), modo=modo)
        caminho.write_bytes(arquivo)
        print(f"PDF DEMONSTRATIVO: {caminho} ({len(arquivo)} bytes)")

    print("HOMOLOGAÇÃO VISUAL: conferir margens, logo, caracteres e páginas A4.")
    print("Arquivos contêm exclusivamente dados fictícios.")


if __name__ == "__main__":
    main()
