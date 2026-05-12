"""indexes_pgcrypto_unique_enrollment_status_default

Revision ID: 681666197fba
Revises: df00caf3de9e
Create Date: 2026-05-11 23:24:59.016109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '681666197fba'
down_revision: Union[str, Sequence[str], None] = 'df00caf3de9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — consolidacao Fase 3 do hardening DB."""
    # 1. pgcrypto: gen_random_uuid() usado na migration multi-tenancy precisa
    # da extensao. Em Postgres 13+ vem instalada mas nao habilitada por default.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Indices compostos pra hot paths (cruzados com queries de api/* e workers/*).
    # alerts: dashboard filtra por (host_id, status, severity) ordenado por last_event_at.
    op.create_index(
        "ix_alerts_host_status_lastevent",
        "alerts",
        ["host_id", "status", sa.text("last_event_at DESC")],
    )
    # actions: idempotencia em api/{clamav,fail2ban,firewall,yara,tools}.py filtra
    # por (host_id, action_type, status IN pending/sent). Partial index reduz tamanho.
    op.create_index(
        "ix_actions_host_type_pending",
        "actions",
        ["host_id", "action_type"],
        postgresql_where=sa.text("status IN ('pending', 'sent')"),
    )
    # audit_logs: queries de compliance filtram por org_id + range de created_at.
    op.create_index(
        "ix_audit_logs_org_created",
        "audit_logs",
        ["org_id", sa.text("created_at DESC")],
    )

    # 3. enrollment_token UNIQUE WHERE NOT NULL (lookup O(1) em vez de scan).
    # CONCURRENTLY evita lock — mas aqui em migration eh OK (downtime planejado).
    op.create_index(
        "ix_hosts_enrollment_token_unique",
        "hosts",
        ["enrollment_token"],
        unique=True,
        postgresql_where=sa.text("enrollment_token IS NOT NULL"),
    )

    # 4. hosts.status: server_default='pending' (atualmente Python seta apos
    # enroll, mas null breaks NOT NULL constraint se INSERT bypass o ORM).
    op.alter_column("hosts", "status", server_default="pending")

    # 5. host_vulnerabilities.references: Text -> JSONB (lista estruturada
    # de URLs em vez de string com \n). 'references' eh palavra reservada
    # no SQL, precisa quotar com aspas duplas em todo lugar.
    op.alter_column(
        "host_vulnerabilities",
        "references",
        type_=sa.JSON(),
        postgresql_using=(
            'CASE WHEN "references" IS NULL OR "references" = \'\' THEN NULL '
            'ELSE to_jsonb(string_to_array("references", E\'\\n\')) END'
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "host_vulnerabilities",
        "references",
        type_=sa.Text(),
        postgresql_using=(
            'CASE WHEN "references" IS NULL THEN NULL '
            'ELSE array_to_string('
            'ARRAY(SELECT jsonb_array_elements_text("references")), E\'\\n\') END'
        ),
    )
    op.alter_column("hosts", "status", server_default=None)
    op.drop_index("ix_hosts_enrollment_token_unique", table_name="hosts")
    op.drop_index("ix_audit_logs_org_created", table_name="audit_logs")
    op.drop_index("ix_actions_host_type_pending", table_name="actions")
    op.drop_index("ix_alerts_host_status_lastevent", table_name="alerts")
    # pgcrypto fica — outros usos podem depender dela.
