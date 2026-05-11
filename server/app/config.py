from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SENTINELBR_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SentinelBR"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://sentinelbr:sentinelbr@localhost:5433/sentinelbr"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    loki_url: str = Field(default="http://localhost:3100")

    jwt_secret: str = Field(default="change-me-in-prod-with-32-bytes-min")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    public_endpoint: str = Field(default="http://localhost:8000")
    grpc_public_endpoint: str = Field(default="localhost:9443")
    grpc_listen_addr: str = Field(default="[::]:9443")

    # CORS: dominios que podem chamar a API. Em dev, Vite escuta em 5173.
    # Em prod, lista os FQDNs da UI publicada. Aceita lista separada por
    # virgula via env: SENTINELBR_CORS_ALLOWED_ORIGINS=https://app.x.com,https://staging.x.com
    cors_allowed_origins: str = Field(default="http://localhost:5173")

    # Server cert SAN: hostnames/IPs que o cert mTLS do server precisa cobrir.
    # Em dev: localhost + sentinelbr-server (SNI usado pelo agent). Em prod,
    # adicione o FQDN publico: SENTINELBR_SERVER_CERT_SAN=server.empresa.com,sentinelbr-server.
    # Pra agents em VMs OrbStack, adicione host.orb.internal.
    # IMPORTANTE: mudar essa setting requer apagar server/data/server.crt e
    # server/data/server.key pro novo cert ser gerado.
    server_cert_san: str = Field(default="localhost,sentinelbr-server")
    server_cert_san_ips: str = Field(default="127.0.0.1")

    # LGPD: retencao de audit logs em dias. Default 180 (~6 meses).
    audit_retention_days: int = Field(default=180)

    # YARA scheduled scan: paths default a escanear em todos hosts ativos (1x/dia).
    # Pode ser sobrescrito via env: SENTINELBR_YARA_SCHEDULED_PATHS="/var/www,/tmp"
    yara_scheduled_paths: str = Field(default="/var/www,/tmp,/home")
    yara_scheduled_interval_seconds: int = Field(default=86400)  # 24h

    # Fase H8 — scheduled audits das ferramentas hardening. Defaults:
    # rkhunter/chkrootkit/aide diario (86400s), lynis semanal (604800s).
    # 0 desabilita o agendamento.
    rkhunter_scheduled_interval_seconds: int = Field(default=86400)
    chkrootkit_scheduled_interval_seconds: int = Field(default=86400)
    aide_scheduled_interval_seconds: int = Field(default=86400)
    lynis_scheduled_interval_seconds: int = Field(default=604800)


@lru_cache
def get_settings() -> Settings:
    return Settings()
