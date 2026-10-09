# -*- coding: utf-8 -*-
"""G3 - Testes de dominio de planos e horimetro."""

from __future__ import annotations

import ast
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest


os.environ["FLASK_ENV"] = "testing"


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():

        # Registrar explicitamente os models envolvidos
        # antes de create_all().
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.equipamento.equipamento_model import Equipamento  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401
        from app.auth.usuario_model import Usuario  # noqa: F401

        from app.geradores.gerador_model import (
            ClienteUnidade,  # noqa: F401
            Gerador,  # noqa: F401
        )

        from app.geradores.gerador_componente_model import (
            GeradorMotor,  # noqa: F401
            GeradorAlternador,  # noqa: F401
            GeradorControladora,  # noqa: F401
            GeradorQTA,  # noqa: F401
        )

        from app.geradores.gerador_partida_model import (
            GeradorBateria,  # noqa: F401
            GeradorCarregador,  # noqa: F401
        )

        from app.geradores.gerador_consumivel_model import (
            GeradorConsumivel,  # noqa: F401
            GeradorConsumivelEquivalente,  # noqa: F401
        )

        from app.geradores.gerador_plano_model import (
            PlanoManutencao,  # noqa: F401
            GeradorPlanoManutencao,  # noqa: F401
        )

        from app.geradores.gerador_horimetro_model import (
            GeradorHorimetro,  # noqa: F401
        )

        db.drop_all()
        db.create_all()

        yield app

        db.session.rollback()
        db.session.remove()
        db.drop_all()


def _cliente(db):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(
        nome="Cliente G3",
        tipo="PJ",
        cpf_cnpj="66777888000199",
        ativo=True,
    )

    db.session.add(cliente)
    db.session.commit()

    return cliente


def _gerador(db, cliente, *, ativo=True):
    from app.geradores.gerador_model import Gerador

    gerador = Gerador(
        codigo="GER-930001",
        cliente_id=cliente.id,
        descricao="Grupo gerador teste G3",
        status=Gerador.STATUS_ATIVO,
        ativo=ativo,
    )

    db.session.add(gerador)
    db.session.commit()

    return gerador


def _plano_basico(service, *, codigo="PM-BAS-001"):
    return service.criar_plano_manutencao(
        codigo=codigo,
        nome="Preventiva Basica",
        tipo="BASICA",
        intervalo_horas=500,
        intervalo_meses=12,
    )


def test_g3_service_sem_commit():
    arquivo = Path(
        "app/geradores/gerador_plano_service.py"
    )

    source = arquivo.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(source)

    chamadas = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            chamadas.append(
                ast.get_source_segment(source, node) or ""
            )

    codigo_chamadas = "\n".join(chamadas)

    assert "db.session.commit(" not in codigo_chamadas


def test_g3_tipos_planos():
    from app.geradores.gerador_plano_model import (
        PlanoManutencao,
    )

    assert PlanoManutencao.TIPOS_VALIDOS == (
        "BASICA",
        "INTERMEDIARIA",
        "AVANCADA",
    )


def test_g3_cria_plano_basico(app_ctx):
    from app.geradores import gerador_plano_service as service

    plano = _plano_basico(service)

    assert plano.id is not None
    assert plano.codigo == "PM-BAS-001"
    assert plano.tipo == "BASICA"
    assert plano.plano_pai_id is None
    assert Decimal(str(plano.intervalo_horas)) == Decimal("500")
    assert plano.intervalo_meses == 12


def test_g3_heranca_basica_intermediaria_avancada(app_ctx):
    from app.geradores import gerador_plano_service as service

    basica = _plano_basico(service)

    intermediaria = service.criar_plano_manutencao(
        codigo="PM-INT-001",
        nome="Preventiva Intermediaria",
        tipo="INTERMEDIARIA",
        plano_pai_id=basica.id,
        intervalo_horas=500,
        intervalo_meses=6,
    )

    avancada = service.criar_plano_manutencao(
        codigo="PM-AVA-001",
        nome="Preventiva Avancada",
        tipo="AVANCADA",
        plano_pai_id=intermediaria.id,
        intervalo_horas=1000,
        intervalo_meses=12,
    )

    assert intermediaria.plano_pai_id == basica.id
    assert avancada.plano_pai_id == intermediaria.id


def test_g3_rejeita_heranca_invalida(app_ctx):
    from app.geradores import gerador_plano_service as service

    basica = _plano_basico(service)

    with pytest.raises(
        service.GeradorG3DominioError,
        match="AVANCADA deve herdar de INTERMEDIARIA",
    ):
        service.criar_plano_manutencao(
            codigo="PM-AVA-ERR",
            nome="Avancada invalida",
            tipo="AVANCADA",
            plano_pai_id=basica.id,
            intervalo_meses=12,
        )


def test_g3_plano_exige_periodicidade(app_ctx):
    from app.geradores import gerador_plano_service as service

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Informe intervalo em horas, meses ou ambos",
    ):
        service.criar_plano_manutencao(
            codigo="PM-SEM-PER",
            nome="Plano sem periodicidade",
            tipo="BASICA",
        )


def test_g3_vincula_plano_e_bloqueia_duplicidade(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    plano = _plano_basico(service)

    vinculo = service.vincular_plano_gerador(
        gerador_id=gerador.id,
        plano_id=plano.id,
        data_base_programacao=date(2026, 1, 1),
        horimetro_base_programacao=1200,
    )

    assert vinculo.id is not None
    assert vinculo.gerador_id == gerador.id
    assert vinculo.plano_id == plano.id

    with pytest.raises(
        service.GeradorG3DominioError,
        match="ja possui este plano ativo",
    ):
        service.vincular_plano_gerador(
            gerador_id=gerador.id,
            plano_id=plano.id,
            data_base_programacao=date(2026, 1, 1),
            horimetro_base_programacao=1200,
        )


def test_g3_plano_exige_bases_compativeis(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    plano = _plano_basico(service)

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Plano por meses exige data base",
    ):
        service.vincular_plano_gerador(
            gerador_id=gerador.id,
            plano_id=plano.id,
            horimetro_base_programacao=1200,
        )

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Plano por horas exige horimetro base",
    ):
        service.vincular_plano_gerador(
            gerador_id=gerador.id,
            plano_id=plano.id,
            data_base_programacao=date(2026, 1, 1),
        )


def test_g3_horimetro_primeira_leitura_e_progressao(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    primeira = service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1200,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    segunda = service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1250,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 2, 1, 8, 0),
    )

    assert primeira.leitura_anterior is None
    assert Decimal(str(primeira.horas_acumuladas)) == Decimal("1200")

    assert Decimal(str(segunda.leitura_anterior)) == Decimal("1200")
    assert Decimal(str(segunda.leitura_atual)) == Decimal("1250")
    assert Decimal(str(segunda.horas_acumuladas)) == Decimal("1250")


def test_g3_rejeita_horimetro_regressivo_normal(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=3800,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Horimetro atual menor que o anterior",
    ):
        service.registrar_horimetro(
            gerador_id=gerador.id,
            leitura_atual=100,
            responsavel="Tecnico JSP",
            data_leitura=datetime(2026, 2, 1, 8, 0),
        )


def test_g3_evento_excepcional_exige_justificativa(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=3800,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Evento excepcional exige justificativa",
    ):
        service.registrar_horimetro(
            gerador_id=gerador.id,
            leitura_atual=0,
            responsavel="Tecnico JSP",
            tipo_evento="RESET",
            data_leitura=datetime(2026, 2, 1, 8, 0),
        )


def test_g3_reset_preserva_acumulado_e_retomada(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=3800,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    reset = service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=0,
        responsavel="Tecnico JSP",
        tipo_evento="RESET",
        justificativa="Horimetro substituido/resetado.",
        data_leitura=datetime(2026, 2, 1, 8, 0),
    )

    depois = service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=100,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 3, 1, 8, 0),
    )

    assert Decimal(str(reset.leitura_anterior)) == Decimal("3800")
    assert Decimal(str(reset.horas_acumuladas)) == Decimal("3800")

    assert Decimal(str(depois.leitura_anterior)) == Decimal("0")
    assert Decimal(str(depois.horas_acumuladas)) == Decimal("3900")


def test_g3_vencimento_por_horas(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    plano = _plano_basico(service)

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1200,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    vinculo = service.vincular_plano_gerador(
        gerador_id=gerador.id,
        plano_id=plano.id,
        data_base_programacao=date(2026, 1, 1),
        horimetro_base_programacao=1200,
    )

    antes = service.calcular_programacao(
        vinculo_id=vinculo.id,
        data_referencia=date(2026, 6, 1),
    )

    assert antes["data_limite"] == date(2027, 1, 1)
    assert antes["horas_limite"] == Decimal("1700")
    assert antes["manutencao_necessaria"] is False

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1700,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 6, 2, 8, 0),
    )

    vencida = service.calcular_programacao(
        vinculo_id=vinculo.id,
        data_referencia=date(2026, 6, 2),
    )

    assert vencida["vencida_por_horas"] is True
    assert vencida["vencida_por_data"] is False
    assert vencida["manutencao_necessaria"] is True


def test_g3_vencimento_por_data_mesmo_sem_vencer_horas(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    plano = _plano_basico(service)

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1200,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 1, 1, 8, 0),
    )

    vinculo = service.vincular_plano_gerador(
        gerador_id=gerador.id,
        plano_id=plano.id,
        data_base_programacao=date(2026, 1, 1),
        horimetro_base_programacao=1200,
    )

    service.registrar_horimetro(
        gerador_id=gerador.id,
        leitura_atual=1300,
        responsavel="Tecnico JSP",
        data_leitura=datetime(2026, 12, 31, 8, 0),
    )

    resultado = service.calcular_programacao(
        vinculo_id=vinculo.id,
        data_referencia=date(2027, 1, 1),
    )

    assert resultado["horas_atuais"] == Decimal("1300")
    assert resultado["horas_limite"] == Decimal("1700")
    assert resultado["vencida_por_horas"] is False

    assert resultado["data_limite"] == date(2027, 1, 1)
    assert resultado["vencida_por_data"] is True

    assert resultado["manutencao_necessaria"] is True


def test_g3_soma_meses_preserva_fim_do_mes(app_ctx):
    from app.geradores import gerador_plano_service as service

    assert service._somar_meses(
        date(2026, 1, 31),
        1,
    ) == date(2026, 2, 28)


def test_g3_rejeita_gerador_inativo(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_plano_service as service

    cliente = _cliente(db)

    gerador = _gerador(
        db,
        cliente,
        ativo=False,
    )

    with pytest.raises(
        service.GeradorG3DominioError,
        match="Gerador nao encontrado ou inativo",
    ):
        service.registrar_horimetro(
            gerador_id=gerador.id,
            leitura_atual=100,
            responsavel="Tecnico JSP",
        )
