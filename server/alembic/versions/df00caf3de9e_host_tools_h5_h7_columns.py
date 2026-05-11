"""host_tools_h5_h7_columns

Revision ID: df00caf3de9e
Revises: 46e7f27bd1c2
Create Date: 2026-05-11 20:14:29.927408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df00caf3de9e'
down_revision: Union[str, Sequence[str], None] = '46e7f27bd1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('hosts', sa.Column('auditd_status_json', sa.Text(), nullable=True))
    op.add_column('hosts', sa.Column('selinux_mode', sa.String(length=20), nullable=True))
    op.add_column('hosts', sa.Column('apparmor_mode', sa.String(length=20), nullable=True))
    op.add_column('hosts', sa.Column('chkrootkit_installed', sa.Boolean(), nullable=True))
    op.add_column('hosts', sa.Column('aide_installed', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('hosts', 'aide_installed')
    op.drop_column('hosts', 'chkrootkit_installed')
    op.drop_column('hosts', 'apparmor_mode')
    op.drop_column('hosts', 'selinux_mode')
    op.drop_column('hosts', 'auditd_status_json')
