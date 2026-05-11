"""organizations + multi-tenancy

Revision ID: 2bbe18a54cc5
Revises: 83e4d681f6e1
Create Date: 2026-05-11 03:43:24.490070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bbe18a54cc5'
down_revision: Union[str, Sequence[str], None] = '83e4d681f6e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Estrategia segura pra dados existentes:
      1. Cria tabela organizations
      2. Cria org default (slug='default')
      3. Adiciona org_id como nullable em users/hosts
      4. Backfill: aponta tudo pra org default
      5. Set NOT NULL nas colunas
      6. Audit_logs.org_id eh nullable (login_failed nao tem org)
    """
    op.create_table('organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    # 2. cria org default. Os dados existentes vao todos pra ela. Em prod
    # multi-tenant real, esse seed eh substituido pelo admin setup proper.
    op.execute(
        "INSERT INTO organizations (id, name, slug) "
        "VALUES (gen_random_uuid(), 'Default Organization', 'default')"
    )

    # 3. adiciona como nullable
    op.add_column('users', sa.Column('org_id', sa.UUID(), nullable=True))
    op.add_column('hosts', sa.Column('org_id', sa.UUID(), nullable=True))
    op.add_column('audit_logs', sa.Column('org_id', sa.UUID(), nullable=True))

    # 4. backfill
    op.execute("UPDATE users SET org_id = (SELECT id FROM organizations WHERE slug='default')")
    op.execute("UPDATE hosts SET org_id = (SELECT id FROM organizations WHERE slug='default')")
    op.execute("UPDATE audit_logs SET org_id = (SELECT id FROM organizations WHERE slug='default')")

    # 5. NOT NULL pra users e hosts (audit_logs fica nullable)
    op.alter_column('users', 'org_id', nullable=False)
    op.alter_column('hosts', 'org_id', nullable=False)

    # 6. indexes + FKs
    op.create_index(op.f('ix_users_org_id'), 'users', ['org_id'], unique=False)
    op.create_index(op.f('ix_hosts_org_id'), 'hosts', ['org_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_org_id'), 'audit_logs', ['org_id'], unique=False)
    op.create_foreign_key(
        'fk_users_org_id', 'users', 'organizations', ['org_id'], ['id'], ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_hosts_org_id', 'hosts', 'organizations', ['org_id'], ['id'], ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_audit_logs_org_id', 'audit_logs', 'organizations',
        ['org_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_audit_logs_org_id', 'audit_logs', type_='foreignkey')
    op.drop_index(op.f('ix_audit_logs_org_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'org_id')

    op.drop_constraint('fk_hosts_org_id', 'hosts', type_='foreignkey')
    op.drop_index(op.f('ix_hosts_org_id'), table_name='hosts')
    op.drop_column('hosts', 'org_id')

    op.drop_constraint('fk_users_org_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_org_id'), table_name='users')
    op.drop_column('users', 'org_id')

    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
