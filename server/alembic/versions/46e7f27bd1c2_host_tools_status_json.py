"""host_tools_status_json

Revision ID: 46e7f27bd1c2
Revises: b0e771b784fa
Create Date: 2026-05-11 19:57:42.364560

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46e7f27bd1c2'
down_revision: Union[str, Sequence[str], None] = 'b0e771b784fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('hosts', sa.Column('fail2ban_status_json', sa.Text(), nullable=True))
    op.add_column('hosts', sa.Column('firewall_status_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('hosts', 'firewall_status_json')
    op.drop_column('hosts', 'fail2ban_status_json')
