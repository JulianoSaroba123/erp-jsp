# -*- coding: utf-8 -*-
"""Gera três amostras do checklist genérico G5 para homologação visual.

Uso: python -m scripts_manutencao.gerar_amostras_g5_generico
Não acessa o ERP nem escreve dados de OS: só cria PDFs numa pasta temporária única.
"""
import hashlib
from pathlib import Path
import tempfile

from app.geradores.gerador_checklist_generico_pdf_service import (
    gerar_pdf_modelo_generico,
)


def gerar_amostras(diretorio_temporario=None):
    raiz = Path(tempfile.mkdtemp(
        prefix="ERP_JSP_G5_GENERICO_REVISAO_",
        dir=diretorio_temporario,
    ))
    resultados = {}
    for tipo in ("BASICA", "INTERMEDIARIA", "AVANCADA"):
        arquivo = raiz / f"JSP_G5_GENERICO_{tipo}.pdf"
        pdf = gerar_pdf_modelo_generico(tipo)
        arquivo.write_bytes(pdf)
        resultados[tipo] = arquivo
        print(
            f"{tipo}: {arquivo} | {len(pdf)} bytes | "
            f"SHA256: {hashlib.sha256(pdf).hexdigest()}"
        )
    print(f"\nAMOSTRAS G5 GENERICO: {raiz}")
    return resultados


if __name__ == "__main__":
    gerar_amostras()
