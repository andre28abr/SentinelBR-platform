"""actions_updated_at_check_constraints

Revision ID: feaf61234b1f
Revises: 3730435d55aa
Create Date: 2026-05-12 01:48:41.815669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'feaf61234b1f'
down_revision: Union[str, Sequence[str], None] = '3730435d55aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """actions.updated_at + CHECK constraints em alerts/actions.

    updated_at em actions: estava faltando (alerts ja tinha). Permite audit
    trail de transitions pending -> sent -> executed sem precisar comparar
    sent_at/executed_at.

    CHECK constraints: defesa em DB layer contra valores invalidos. Se algum
    bug de codigo escrever severity='criticla' (typo), DB rejeita em vez de
    silenciosamente quebrar a UI.
    """
    op.add_column(
        "actions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_actions_status",
        "actions",
        "status IN ('pending', 'sent', 'executed', 'failed', 'reverted')",
    )
    op.create_check_constraint(
        "ck_alerts_severity",
        "alerts",
        "severity IN ('critical', 'high', 'medium', 'low', 'info')",
    )
    op.create_check_constraint(
        "ck_alerts_status",
        "alerts",
        "status IN ('open', 'acknowledged', 'resolved')",
    )

    # Roda ANALYZE pra atualizar planner stats apos schema change.
    op.execute("ANALYZE actions")
    op.execute("ANALYZE alerts")


def downgrade() -> None:
    op.drop_constraint("ck_alerts_status", "alerts", type_="check")
    op.drop_constraint("ck_alerts_severity", "alerts", type_="check")
    op.drop_constraint("ck_actions_status", "actions", type_="check")
    op.drop_column("actions", "updated_at")
