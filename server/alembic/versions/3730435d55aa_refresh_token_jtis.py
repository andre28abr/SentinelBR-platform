"""refresh_token_jtis

Revision ID: 3730435d55aa
Revises: 681666197fba
Create Date: 2026-05-12 01:29:24.119774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3730435d55aa'
down_revision: Union[str, Sequence[str], None] = '681666197fba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria refresh_token_jtis pra suportar token rotation/revocation."""
    op.create_table(
        "refresh_token_jtis",
        sa.Column("jti", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "issued_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("refresh_token_jtis")
