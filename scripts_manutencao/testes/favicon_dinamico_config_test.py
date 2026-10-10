# -*- coding: utf-8 -*-
"""Regressao do favicon dinamico sem acessar banco ou dados reais."""
import base64
import importlib.util
from io import BytesIO
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest
from flask import Flask
from PIL import Image


ARQUIVO = (
    Path(__file__).resolve().parents[2]
    / "app" / "configuracao" / "favicon_dinamico.py"
)


def imagem_b64(cor, formato="PNG", data_uri=True):
    imagem = Image.new("RGB", (180, 90), cor)
    saida = BytesIO()
    imagem.save(saida, format=formato)
    texto = base64.b64encode(saida.getvalue()).decode("ascii")
    mime = "image/jpeg" if formato == "JPEG" else "image/png"
    return f"data:{mime};base64,{texto}" if data_uri else texto


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("jsp_favicon_teste", ARQUIVO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    diretorio = tmp_path / "static"
    (diretorio / "icons").mkdir(parents=True)
    fallback = Image.new("RGB", (192, 192), "blue")
    fallback.save(diretorio / "icons" / "icon-192.png", format="PNG")
    app = Flask("jsp_favicon_isolado", static_folder=str(diretorio))
    app.config.update(TESTING=True, SECRET_KEY="teste-favicon")
    conf = SimpleNamespace(logo_base64=None)
    utils = ModuleType("app.configuracao.configuracao_utils")
    def get_config(force_reload=False):
        assert force_reload is True
        return conf
    utils.get_config = get_config
    monkeypatch.setitem(sys.modules, "app.configuracao.configuracao_utils", utils)
    modulo.init_favicon_dinamico(app)
    return app, app.test_client(), conf, modulo


def test_sem_logo_usa_icone_padrao(ambiente):
    _, client, _, _ = ambiente
    resposta = client.get("/favicon-dinamico.png")
    assert resposta.status_code == 200
    assert resposta.mimetype == "image/png"
    assert "no-store" in resposta.headers["Cache-Control"]
    with Image.open(BytesIO(resposta.data)) as icone:
        assert icone.size == (192, 192)


def test_logo_passa_a_ser_png_quadrado(ambiente):
    _, client, conf, _ = ambiente
    conf.logo_base64 = imagem_b64("red")
    resposta = client.get("/favicon-dinamico.png")
    assert resposta.status_code == 200
    with Image.open(BytesIO(resposta.data)) as icone:
        assert icone.size == (64, 64)
        assert icone.mode == "RGBA"
        assert icone.getpixel((32, 32))[0] > 200


def test_atualiza_quando_troca_a_logo_no_banco(ambiente):
    _, client, conf, _ = ambiente
    conf.logo_base64 = imagem_b64("red")
    anterior = client.get("/favicon-dinamico.png?v=1").data
    conf.logo_base64 = imagem_b64("green")
    novo = client.get("/favicon-dinamico.png?v=2").data
    assert novo != anterior
    with Image.open(BytesIO(novo)) as imagem:
        assert imagem.getpixel((32, 32))[1] > 100


def test_base64_antigo_sem_prefixo(ambiente):
    _, client, conf, _ = ambiente
    conf.logo_base64 = imagem_b64("yellow", data_uri=False)
    resposta = client.get("/favicon-dinamico.png")
    with Image.open(BytesIO(resposta.data)) as imagem:
        assert imagem.size == (64, 64)


def test_logo_invalida_nao_quebra_login(ambiente):
    _, client, conf, _ = ambiente
    conf.logo_base64 = "data:text/html;base64,PHNjcmlwdD4="
    resposta = client.get("/favicon-dinamico.png")
    assert resposta.status_code == 200
    with Image.open(BytesIO(resposta.data)) as imagem:
        assert imagem.size == (192, 192)


def test_favicon_e_publico_no_login(ambiente):
    _, client, conf, _ = ambiente
    conf.logo_base64 = imagem_b64("white", formato="JPEG")
    resposta = client.get("/favicon-dinamico.png")
    assert resposta.status_code == 200
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"


def test_registrar_duas_vezes_nao_duplica_rota(ambiente):
    app, client, _, modulo = ambiente
    modulo.init_favicon_dinamico(app)
    assert client.get("/favicon-dinamico.png").status_code == 200
    assert [r.rule for r in app.url_map.iter_rules()].count(
        "/favicon-dinamico.png"
    ) == 1


def test_templates_usam_mesma_rota():
    raiz = Path(__file__).resolve().parents[2]
    login = (raiz / "app/auth/templates/auth/login.html").read_text("utf-8-sig")
    base = (raiz / "app/templates/base.html").read_text("utf-8-sig")
    for html in (login, base):
        assert "url_for('jsp_favicon_dinamico')" in html
        assert "rel=\"icon\"" in html
