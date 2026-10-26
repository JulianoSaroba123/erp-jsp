"""PR46: sinaliza baixas de OS sem nova movimentacao no saldo bancario.

Revision ID: 20261026_01
Revises: 20261015_01

Aditiva. Registros historicos mantem sem_movimentacao_bancaria=False.
A implementacao de recebimento manual define True quando o comprovante
ja representa evento bancario externo, evitando incrementar saldo duas vezes.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261026_01"
down_revision = "20261015_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "lancamentos_financeiros",
        sa.Column(
            "sem_movimentacao_bancaria", sa.Boolean(), nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    bind = op.get_bind()
    quantidade = bind.execute(sa.text(
        "SELECT COUNT(*) FROM lancamentos_financeiros "
        "WHERE sem_movimentacao_bancaria = :sim"
    ), {"sim": True}).scalar()
    if quantidade:
        raise RuntimeError(
            "Downgrade bloqueado: existem recebimentos sem impacto "
            "bancario. Necessaria reconciliacao financeira manual."
        )
    op.drop_column("lancamentos_financeiros", "sem_movimentacao_bancaria")
