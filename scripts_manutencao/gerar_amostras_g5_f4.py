# -*- coding: utf-8 -*-
"""G5-F4: gera PDFs de demonstração SOMENTE COM DADOS FICTÍCIOS.

Uso:
    python -m scripts_manutencao.gerar_amostras_g5_f4

Saída: pasta temporária do Windows/Linux, fora da worktree.
Não envia dados, não usa registros reais, não modifica o banco.
"""
import hashlib
import inspect
import json
import os
import subprocess
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
from app.geradores.gerador_checklist_pdf_service import (
    _estilos, _item_documento, gerar_pdf_checklist,
)


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
                else ""
            ),
        }
    # Impede que vírgulas acidentais criem tuplas/listas de observações
    # que seriam transformadas em "('',)" pela normalização do catálogo.
    for item_id, resposta in respostas.items():
        if not isinstance(resposta["observacao"], str):
            raise TypeError(
                f"{item_id}: observação da amostra deve ser string, "
                f"recebido {type(resposta['observacao']).__name__}."
            )
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


def pasta_nova_amostras(*, diretorio_temporario=None):
    """Cria pasta única para não sobrescrever PDFs abertos no Windows.

    Nunca remove, substitui ou altera as amostras de revisões anteriores.
    """
    return Path(tempfile.mkdtemp(
        prefix="ERP_JSP_G5_F4_REVISAO_",
        dir=diretorio_temporario,
    ))


def validar_procedencia_renderizador():
    """Evita amostras feitas por uma cópia antiga/importada de outro worktree."""
    raiz = Path(__file__).resolve().parents[1]
    esperado = (raiz / "app/geradores/gerador_checklist_pdf_service.py").resolve()
    modulo_carregado = Path(inspect.getfile(gerar_pdf_checklist)).resolve()
    helper_carregado = Path(inspect.getfile(_item_documento)).resolve()
    if modulo_carregado != esperado or helper_carregado != esperado:
        raise RuntimeError(
            "GERADOR PDF INCORRETO: Python carregou módulo de outra worktree. "
            f"Esperado: {esperado}; usado: {modulo_carregado}"
        )

    codigo = inspect.getsource(_item_documento)
    if (
        'observacao = str(resposta.get("observacao") or "").strip()' not in codigo
        or "f\"{_seguro(resposta.get('observacao'), 'Sem observações.')}\"" in codigo
    ):
        raise RuntimeError(
            "GERADOR PDF DESATUALIZADO: função de observações não contém "
            "a correção do PR #39. Confira o commit e a origem do import."
        )

    item = obter_modelo("BASICA")["secoes"][0]["itens"][0]
    for observacao in ("", "ANOMALIA SIMULADA - VALIDAÇÃO"):
        resposta = {
            "status": "NAO_CONFORME" if observacao else "CONFORME",
            "medicao": None, "observacao": observacao,
        }
        bloco = _item_documento(item, resposta, "preenchido", _estilos())
        texto = bloco._content[0]._cellvalues[1][0].text
        if "('',)" in texto or "('ANOMALIA" in texto:
            raise RuntimeError(
                "GERADOR PDF COM DEFEITO: observação renderizada como tupla."
            )
        if observacao and observacao not in texto:
            raise RuntimeError("Observação de teste não foi preservada.")
        if not observacao and "Observações / justificativa" in texto:
            raise RuntimeError("Observação vazia ocupa espaço indevido.")

    revisao = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=raiz, capture_output=True, text=True, check=False,
    )
    commit = revisao.stdout.strip() if revisao.returncode == 0 else "indisponivel"
    hash_modulo = hashlib.sha256(esperado.read_bytes()).hexdigest()
    print(f"WORKTREE DE EXECUCAO: {raiz}")
    print(f"COMMIT DE EXECUCAO: {commit}")
    print(f"MODULO REAL DO PDF: {modulo_carregado}")
    print(f"SHA256 DO MODULO PDF: {hash_modulo}")
    print("VERIFICACAO DO TEXTO DAS OBSERVACOES: APROVADA")
    return {
        "commit": commit,
        "worktree": str(raiz),
        "modulo": str(modulo_carregado),
        "sha256_modulo": hash_modulo,
    }


def main():
    procedencia = validar_procedencia_renderizador()
    destino = pasta_nova_amostras()
    print(f"PASTA DOS NOVOS PDFs: {destino}")

    exemplos = [
        ("AMOSTRA_BASICA_EM_BRANCO.pdf", "BASICA", "branco"),
        ("AMOSTRA_INTERMEDIARIA_PREENCHIDO.pdf", "INTERMEDIARIA", "preenchido"),
        ("AMOSTRA_AVANCADA_PREENCHIDO.pdf", "AVANCADA", "preenchido"),
    ]
    manifesto = dict(procedencia)
    manifesto["arquivos"] = {}
    for nome, tipo, modo in exemplos:
        caminho = destino / nome
        arquivo = gerar_pdf_checklist(execucao_ficticia(tipo), modo=modo)
        caminho.write_bytes(arquivo)
        hash_pdf = hashlib.sha256(arquivo).hexdigest()
        manifesto["arquivos"][nome] = {"bytes": len(arquivo), "sha256": hash_pdf}
        print(f"PDF DEMONSTRATIVO: {caminho} ({len(arquivo)} bytes)")
        print(f"SHA256 DO PDF: {hash_pdf}")

    (destino / "AUDITORIA_G5_F4.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"AUDITORIA DO RENDERIZADOR: {destino / 'AUDITORIA_G5_F4.json'}")
    print("HOMOLOGAÇÃO VISUAL: conferir margens, logo, caracteres e páginas A4.")
    print("Arquivos contêm exclusivamente dados fictícios.")
    print(f"ABRA ESTA PASTA: {destino}")
    return destino


if __name__ == "__main__":
    main()
