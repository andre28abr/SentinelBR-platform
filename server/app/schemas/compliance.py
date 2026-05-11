from datetime import datetime

from pydantic import BaseModel


class ComplianceReport(BaseModel):
    period_start: datetime
    period_end: datetime
    period_days: int

    # Auth
    total_logins: int
    failed_logins: int
    distinct_users_logged_in: int

    # Hosts
    hosts_total: int
    hosts_active: int
    hosts_created_in_period: int
    hosts_deleted_in_period: int

    # Detection / response
    alerts_created_in_period: int
    alerts_open: int
    alerts_acknowledged_in_period: int
    alerts_resolved_in_period: int
    actions_executed_in_period: int

    # MTTR (mean time to respond) — diferenca media entre alert.created_at e action.executed_at
    mttr_seconds: float | None

    # Auditoria
    audit_log_entries_in_period: int
    audit_retention_days: int

    # Disclaimer pra ANPD
    note: str = (
        "Relatorio gerado automaticamente. Atende LGPD Art. 37 (registro de operacoes). "
        "Para questoes formais, apresentar este relatorio + log auditoria completo."
    )
