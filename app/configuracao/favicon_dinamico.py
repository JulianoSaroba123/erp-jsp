# -*- coding: utf-8 -*-
"""Favicon do ERP JSP gerado a partir da logo das Configuracoes do Sistema.

A logo e lida do campo logo_base64 (banco), sem depender do filesystem
local, que pode ser efemero no Render. A rota permanece publica para
funcionar tambem na tela de login.
"""
import base64
import binascii
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from flask import current_app, send_file
from PIL import Image, ImageOps, UnidentifiedImageError


MAX_BASE64_CHARS = 3_000_000
MAX_IMAGE_PIXELS = 16_000_000


@lru_cache(maxsize=8)
def criar_favicon_png(logo_base64):
    """Converte a mesma logo do cadastro em PNG quadrado de 64 px.

    Retorna None para imagens invalidas, sem lancar excecao ao usuario.
    """
    if not isinstance(logo_base64, str):
        return None
    valor = logo_base64.strip()
    if not valor or len(valor) > MAX_BASE64_CHARS:
        return None

    if valor.lower().startswith("data:"):
        if "," not in valor:
            return None
        prefixo, valor = valor.split(",", 1)
        mime = prefixo.lower()
        if mime not in {
            "data:image/png;base64",
            "data:image/jpeg;base64",
            "data:image/jpg;base64",
            "data:image/gif;base64",
            "data:image/webp;base64",
        }:
            return None

    try:
        dados = base64.b64decode(valor, validate=True)
        if not dados or len(dados) > 2_250_000:
            return None
        with Image.open(BytesIO(dados)) as origem:
            if origem.format not in {"PNG", "JPEG", "GIF", "WEBP"}:
                return None
            if origem.width * origem.height > MAX_IMAGE_PIXELS:
                return None
            corrigida = ImageOps.exif_transpose(origem)
            logo = corrigida.convert("RGBA")
        logo.thumbnail((56, 56), Image.Resampling.LANCZOS)
        destino = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        posicao = ((64 - logo.width) // 2, (64 - logo.height) // 2)
        destino.alpha_composite(logo, posicao)
        saida = BytesIO()
        destino.save(saida, format="PNG", optimize=True)
        return saida.getvalue()
    except (ValueError, TypeError, binascii.Error, OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None


def init_favicon_dinamico(app):
    """Registra uma unica rota publica, sem criar tabela ou migration."""
    if "jsp_favicon_dinamico" in app.view_functions:
        return

    @app.get("/favicon-dinamico.png", endpoint="jsp_favicon_dinamico")
    def favicon_dinamico():
        imagem = None
        try:
            from app.configuracao.configuracao_utils import get_config
            # A cada consulta, evita cache de outras instancias do Render.
            conf = get_config(force_reload=True)
            imagem = criar_favicon_png(
                getattr(conf, "logo_base64", None) if conf else None
            )
        except Exception:
            current_app.logger.exception("Falha ao ler logo do favicon")

        if imagem is None:
            # Fallback oficial do proprio ERP, sem sobrescrever nenhum arquivo.
            caminho = Path(current_app.static_folder) / "icons" / "icon-192.png"
            imagem = caminho.read_bytes()

        response = send_file(
            BytesIO(imagem),
            mimetype="image/png",
            as_attachment=False,
            conditional=False,
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
