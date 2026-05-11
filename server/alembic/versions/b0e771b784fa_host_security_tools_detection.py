"""host_security_tools_detection

Revision ID: b0e771b784fa
Revises: c35ab947eb39
Create Date: 2026-05-11 19:48:41.293330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0e771b784fa'
down_revision: Union[str, Sequence[str], None] = 'c35ab947eb39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('hosts', sa.Column('fail2ban_installed', sa.Boolean(), nullable=True))
    op.add_column('hosts', sa.Column('fail2ban_banned_ips', sa.Integer(), nullable=True))
    op.add_column('hosts', sa.Column('fail2ban_jails_active', sa.Integer(), nullable=True))
    op.add_column('hosts', sa.Column('firewall_active', sa.String(length=20), nullable=True))
    op.add_column('hosts', sa.Column('auditd_active', sa.Boolean(), nullable=True))
    op.add_column('hosts', sa.Column('rkhunter_installed', sa.Boolean(), nullable=True))
    op.add_column('hosts', sa.Column('lynis_installed', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('hosts', 'lynis_installed')
    op.drop_column('hosts', 'rkhunter_installed')
    op.drop_column('hosts', 'auditd_active')
    op.drop_column('hosts', 'firewall_active')
    op.drop_column('hosts', 'fail2ban_jails_active')
    op.drop_column('hosts', 'fail2ban_banned_ips')
    op.drop_column('hosts', 'fail2ban_installed')
