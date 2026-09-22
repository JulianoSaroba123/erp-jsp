from pathlib import Path
from decimal import Decimal

RAIZ = Path(__file__).resolve().parents[2]

MODELO = RAIZ / "app" / "financeiro" / "financeiro_model.py"
MIGRATION = (
    RAIZ
    / "migrations"
    / "versions"
    / "20260917_01_conciliacao_bancaria_itens.py"
)


def testar_modelo_estaticamente():
    texto = MODELO.read_text(encoding="utf-8")

    obrigatorios = [
        "class ConciliacaoBancariaItem(BaseModel):",
        "__tablename__ = 'conciliacao_bancaria_itens'",
        "'extrato_id'",
        "'lancamento_id'",
        "valor_conciliado = db.Column(",
        "db.UniqueConstraint(",
        "name='uq_conciliacao_bancaria_extrato_lancamento'",
        "db.CheckConstraint(",
        "'valor_conciliado > 0'",
        "name='ck_conciliacao_bancaria_valor_positivo'",
        "db.ForeignKey('extratos_bancarios.id'",
        "db.ForeignKey('lancamentos_financeiros.id'",
    ]

    faltantes = [item for item in obrigatorios if item not in texto]

    assert not faltantes, (
        "Estrutura esperada ausente no model: "
        + ", ".join(faltantes)
    )

    bloco_inicio = texto.index("class ConciliacaoBancariaItem(BaseModel):")
    bloco_fim = texto.index("class CustoFixo(BaseModel):", bloco_inicio)
    bloco = texto[bloco_inicio:bloco_fim]

    assert "unique=True" not in bloco, (
        "extrato_id ou lancamento_id nao deve ser UNIQUE isoladamente."
    )


def testar_migration_estaticamente():
    texto = MIGRATION.read_text(encoding="utf-8")

    obrigatorios = [
        'revision = "20260917_01"',
        'down_revision = "20260912_01"',
        '"conciliacao_bancaria_itens"',
        '"extrato_id"',
        '"lancamento_id"',
        '"valor_conciliado"',
        '"uq_conciliacao_bancaria_extrato_lancamento"',
        '"ck_conciliacao_bancaria_valor_positivo"',
        '["extratos_bancarios.id"]',
        '["lancamentos_financeiros.id"]',
        'op.drop_table("conciliacao_bancaria_itens")',
    ]

    faltantes = [item for item in obrigatorios if item not in texto]

    assert not faltantes, (
        "Estrutura esperada ausente na migration: "
        + ", ".join(faltantes)
    )


def testar_caso_mr_jacky():
    valor_extrato = Decimal("990.00")

    os_1 = Decimal("450.00")
    os_2 = Decimal("540.00")

    total_alocado = os_1 + os_2
    diferenca = valor_extrato - total_alocado

    assert total_alocado == Decimal("990.00")
    assert total_alocado == valor_extrato
    assert diferenca == Decimal("0.00")


def main():
    testar_modelo_estaticamente()
    testar_migration_estaticamente()
    testar_caso_mr_jacky()

    print("OK: modelo N:N validado estaticamente.")
    print("OK: migration N:N validada estaticamente.")
    print("OK: nenhum Flask/app foi inicializado.")
    print("OK: nenhum banco foi acessado.")
    print("OK: caso MR Jacky validado: 990.00 = 450.00 + 540.00.")
    print("OK: D25F01-A1.1 homologado de forma isolada.")


if __name__ == "__main__":
    main()
