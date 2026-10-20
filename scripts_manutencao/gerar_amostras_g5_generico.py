# -*- coding: utf-8 -*-
"""Gera amostras A4 G5 com banco SQLite descartável ao executar no Windows.

Uso: python -m scripts_manutencao.gerar_amostras_g5_generico
A inicialização implícita de app/__init__.py cria o Flask e verifica tabelas.
Por isso, antes de importar app, o modo CLI isola DATABASE_URL em um banco
temporário exclusivo, sem tocar no erp.db existente ou no Render.
"""
import hashlib
import os
from pathlib import Path
import tempfile


def gerar_amostras(diretorio_temporario=None):
    """Gera três PDFs em pasta única. Função também utilizável em testes."""
    # Import tardio: o __init__.py do ERP executa create_app() no import.
    # O entrypoint __main__ configura um SQLite isolado ANTES de chegar aqui.
    from app.geradores.gerador_checklist_generico_pdf_service import (
        gerar_pdf_modelo_generico,
    )

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


def _preparar_banco_descartavel_cli():
    """Não usa DATABASE_URL fornecida pelo ambiente nem o arquivo erp.db."""
    if (
        str(os.environ.get("RENDER", "")).lower() in {"true", "1", "yes"}
        or os.environ.get("RENDER_SERVICE_ID")
    ):
        raise RuntimeError("Script de amostras permitido apenas fora do Render.")

    pasta = Path(tempfile.mkdtemp(prefix="ERP_JSP_G5_GENERICO_SQLITE_"))
    arquivo_db = pasta / "homologacao_descartavel.db"
    os.environ["DATABASE_URL"] = "sqlite:///" + arquivo_db.as_posix()
    print("G5: importação do Flask isolada em SQLite temporário.")
    print(f"G5: banco descartável: {arquivo_db}")
    return arquivo_db


if __name__ == "__main__":
    _preparar_banco_descartavel_cli()
    gerar_amostras()
