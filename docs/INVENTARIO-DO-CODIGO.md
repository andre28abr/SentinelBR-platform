# Inventário do código: SentinelBR-platform

> Gerado por `raiz/maquina/inventario.py` em 2026-09-20, direto do código. Não editar à mão: regenerar ao fechar um bloco de trabalho. Serve de mapa para quem vai mexer no projeto; a explicação do porquê está no README, no CLAUDE.md e nos docs do repositório. Testes são contados por função declarada; o pytest e o cargo podem reportar mais execuções por causa de parametrização.

## Resumo

| Linguagem | Números |
|---|---|
| Python | 97 módulos, 253 funções, 55 rotas, 10 modelos, 146 testes em 19 arquivos |
| Go | 26 pacotes, 370 funções/métodos exportados, 87 tipos exportados, 45 testes |
| Web | 41 componentes, 7 módulos JS/TS, 31 testes em 5 arquivos |

## Python

### Módulos

| Arquivo | O que é (docstring) | Classes | Funções | Linhas |
|---|---|---|---|---|
| `server/alembic/env.py` |  | 0 | 4 | 59 |
| `server/alembic/versions/2bbe18a54cc5_organizations_multi_tenancy.py` | organizations + multi-tenancy | 0 | 2 | 95 |
| `server/alembic/versions/3730435d55aa_refresh_token_jtis.py` | refresh_token_jtis | 0 | 2 | 51 |
| `server/alembic/versions/46e7f27bd1c2_host_tools_status_json.py` | host_tools_status_json | 0 | 2 | 31 |
| `server/alembic/versions/681666197fba_indexes_pgcrypto_unique_enrollment_.py` | indexes_pgcrypto_unique_enrollment_status_default | 0 | 2 | 95 |
| `server/alembic/versions/7040cb7e2799_hosts_enrollment_token_expires_at_.py` | hosts: enrollment_token_expires_at + enrolled_at | 0 | 2 | 35 |
| `server/alembic/versions/746dbef1e94d_host_clamav_fields.py` | host clamav fields | 0 | 2 | 33 |
| `server/alembic/versions/7fcb043197cb_audit_logs_table.py` | audit_logs table | 0 | 2 | 55 |
| `server/alembic/versions/83e4d681f6e1_host_packages_host_vulnerabilities.py` | host_packages + host_vulnerabilities | 0 | 2 | 72 |
| `server/alembic/versions/89fb15616be2_users_hosts_tables.py` | users + hosts tables | 0 | 2 | 64 |
| `server/alembic/versions/94c2ac6b5b34_host_kernel_arch_location.py` | host kernel arch location | 0 | 2 | 37 |
| `server/alembic/versions/b0e771b784fa_host_security_tools_detection.py` | host_security_tools_detection | 0 | 2 | 41 |
| `server/alembic/versions/baf5f2039064_host_stats_columns.py` | host stats columns | 0 | 2 | 47 |
| `server/alembic/versions/c35ab947eb39_host_admin_panel_counts.py` | host admin panel counts | 0 | 2 | 47 |
| `server/alembic/versions/df00caf3de9e_host_tools_h5_h7_columns.py` | host_tools_h5_h7_columns | 0 | 2 | 37 |
| `server/alembic/versions/df8d8b55ce2d_alerts_table.py` | alerts table | 0 | 2 | 61 |
| `server/alembic/versions/f5f6459df882_actions_table.py` | actions table | 0 | 2 | 55 |
| `server/alembic/versions/feaf61234b1f_actions_updated_at_check_constraints.py` | actions_updated_at_check_constraints | 0 | 2 | 67 |
| `server/app/__init__.py` |  | 0 | 0 | 1 |
| `server/app/api/__init__.py` |  | 0 | 0 | 1 |
| `server/app/api/actions.py` | REST endpoints de Actions — listagem por host + revert (unblock). | 0 | 4 | 93 |
| `server/app/api/agents.py` | Endpoints publicos consumidos pelo agente (sem auth — autorizacao por enrollment token). | 0 | 1 | 59 |
| `server/app/api/alerts.py` | REST endpoints de alertas — listagem, ack, resolve. | 0 | 7 | 118 |
| `server/app/api/audit.py` | REST endpoints de auditoria + relatorio de compliance LGPD. | 1 | 4 | 259 |
| `server/app/api/auth.py` |  | 0 | 8 | 246 |
| `server/app/api/clamav.py` | REST endpoints ClamAV — dispara scan manual via Action. | 1 | 2 | 71 |
| `server/app/api/deps.py` |  | 0 | 3 | 71 |
| `server/app/api/docs.py` | REST endpoints pra servir os docs em markdown que ficam em /docs do repo. | 2 | 7 | 122 |
| `server/app/api/events.py` | REST GET /api/v1/hosts/:id/events — consulta eventos do Loki para a UI. | 0 | 1 | 57 |
| `server/app/api/fail2ban.py` | REST endpoints fail2ban — unban/ban IP via Action enviada ao agente. | 1 | 5 | 97 |
| `server/app/api/firewall.py` | REST endpoints firewall — adicionar/remover regra via Action (Fase H6). | 2 | 5 | 126 |
| `server/app/api/health.py` |  | 1 | 1 | 18 |
| `server/app/api/hosts.py` |  | 0 | 7 | 113 |
| `server/app/api/kb.py` | REST endpoints da Knowledge Base — MITRE ATT&CK PT-BR + hunting + playbooks. | 0 | 5 | 69 |
| `server/app/api/lab.py` | REST endpoints do Lab Mode — controle de VMs OrbStack pra demo. | 4 | 7 | 196 |
| `server/app/api/organizations.py` | REST endpoints de Organization (tenant). Cada user pertence a 1 org. | 3 | 4 | 113 |
| `server/app/api/tools.py` | REST endpoints rkhunter + chkrootkit + lynis + AIDE — scans via Action. | 1 | 5 | 115 |
| `server/app/api/vulnerabilities.py` | REST endpoints de inventario e vulnerabilidades por host. | 0 | 3 | 95 |
| `server/app/api/yara.py` | REST endpoints YARA — dispara scan manual e quarentena via Action. | 1 | 2 | 86 |
| `server/app/config.py` |  | 1 | 1 | 98 |
| `server/app/db.py` |  | 1 | 1 | 21 |
| `server/app/grpc_server/__init__.py` |  | 0 | 0 | 1 |
| `server/app/grpc_server/agent_servicer.py` | Implementacao do AgentService gRPC. | 1 | 9 | 381 |
| `server/app/grpc_server/pb/__init__.py` |  | 0 | 0 | 1 |
| `server/app/grpc_server/pb/agent_pb2.py` | Generated protocol buffer code. | 0 | 0 | 101 |
| `server/app/grpc_server/pb/agent_pb2_grpc.py` | Client and server classes corresponding to protobuf-defined services. | 3 | 10 | 240 |
| `server/app/grpc_server/server.py` | Roda o gRPC server (mTLS) em paralelo ao FastAPI. | 0 | 3 | 69 |
| `server/app/main.py` |  | 0 | 2 | 84 |
| `server/app/models/__init__.py` |  | 0 | 0 | 15 |
| `server/app/models/action.py` |  | 1 | 1 | 54 |
| `server/app/models/alert.py` |  | 1 | 1 | 68 |
| `server/app/models/audit_log.py` |  | 1 | 0 | 60 |
| `server/app/models/host.py` |  | 1 | 0 | 94 |
| `server/app/models/host_package.py` |  | 1 | 0 | 36 |
| `server/app/models/host_vulnerability.py` |  | 1 | 0 | 47 |
| `server/app/models/organization.py` |  | 1 | 0 | 32 |
| `server/app/models/refresh_token_jti.py` | Tabela de JTIs de refresh tokens — suporte a rotation/revocation. | 1 | 0 | 42 |
| `server/app/models/user.py` |  | 1 | 0 | 30 |
| `server/app/schemas/__init__.py` |  | 0 | 0 | 1 |
| `server/app/schemas/action.py` |  | 2 | 0 | 27 |
| `server/app/schemas/alert.py` |  | 2 | 0 | 28 |
| `server/app/schemas/audit_log.py` |  | 1 | 0 | 22 |
| `server/app/schemas/auth.py` |  | 5 | 0 | 39 |
| `server/app/schemas/compliance.py` |  | 1 | 0 | 41 |
| `server/app/schemas/enrollment.py` |  | 4 | 0 | 37 |
| `server/app/schemas/event.py` |  | 1 | 0 | 13 |
| `server/app/schemas/host.py` |  | 3 | 0 | 64 |
| `server/app/schemas/vulnerability.py` |  | 4 | 0 | 42 |
| `server/app/scripts/__init__.py` |  | 0 | 0 | 1 |
| `server/app/scripts/seed.py` | Cria o primeiro usuario admin + a org default se ainda nao existirem. | 0 | 1 | 68 |
| `server/app/services/__init__.py` |  | 0 | 0 | 1 |
| `server/app/services/actions.py` | Helpers compartilhados pra criar Actions com idempotencia + audit. | 0 | 3 | 116 |
| `server/app/services/audit.py` | Audit service: registra cada operacao relevante na tabela audit_logs. | 0 | 3 | 98 |
| `server/app/services/auth.py` |  | 1 | 6 | 80 |
| `server/app/services/ca.py` | PKI: CA propria gerada na primeira execucao + assinatura de certs de cliente para mTLS gRPC. | 1 | 9 | 206 |
| `server/app/services/enrollment.py` | Geracao e validacao de enrollment tokens. | 0 | 4 | 87 |
| `server/app/services/kb.py` | Loader da Knowledge Base (MITRE ATT&CK PT-BR + hunting + playbooks). | 0 | 10 | 98 |
| `server/app/services/lab.py` | Lab service — wrapper sobre `orb` (OrbStack CLI) pra controlar VMs do | 3 | 7 | 206 |
| `server/app/services/loki.py` | Cliente HTTP do Loki: push de eventos + query de leitura. | 2 | 5 | 153 |
| `server/app/services/observability.py` | Observabilidade — structlog + request_id middleware + Prometheus metrics. | 2 | 5 | 125 |
| `server/app/services/osv.py` | Cliente HTTP do OSV.dev (Open Source Vulnerabilities) — base aberta agregada | 2 | 7 | 212 |
| `server/app/services/pdf_report.py` | Gerador de PDF do relatorio de compliance LGPD. | 0 | 4 | 158 |
| `server/app/services/pii.py` | Mascaramento de PII pra atender LGPD Art. 6 (minimizacao) na exibicao. | 0 | 6 | 64 |
| `server/app/services/policy.py` | Policy module: dado um Alert recem-criado/atualizado, decide se cria uma Action. | 0 | 4 | 102 |
| `server/app/services/ratelimit.py` | Rate limit configuration via slowapi. | 0 | 1 | 48 |
| `server/app/services/rules/__init__.py` |  | 0 | 0 | 1 |
| `server/app/services/rules/engine.py` | Orquestra a avaliacao das regras contra todos os hosts ativos. | 0 | 5 | 149 |
| `server/app/services/rules/evaluator.py` | Avalia uma regra contra uma lista de eventos e retorna AlertCandidates. | 1 | 7 | 87 |
| `server/app/services/rules/loader.py` | Carrega regras de deteccao a partir de arquivos YAML em app/rules/. | 2 | 3 | 97 |
| `server/app/services/vuln_scan.py` | Servico de scan de vulnerabilidades: cross-ref host_packages com OSV | 0 | 3 | 128 |
| `server/app/workers/__init__.py` |  | 0 | 0 | 1 |
| `server/app/workers/celery_app.py` | Celery app + beat schedule. | 0 | 1 | 87 |
| `server/app/workers/detect.py` | Tarefa Celery que roda o ciclo de deteccao de regras. | 0 | 1 | 25 |
| `server/app/workers/retention.py` | Tarefa Celery de retencao: apaga audit_logs antigos (LGPD Art. 16 — descarte | 0 | 2 | 45 |
| `server/app/workers/tools_schedule.py` | Celery tasks: agenda audits periodicos das ferramentas Tier 1+2 (Fase H8). | 0 | 5 | 110 |
| `server/app/workers/vuln.py` | Celery task pra rodar scan de vulnerabilidades de forma assincrona. | 0 | 1 | 27 |
| `server/app/workers/yara_schedule.py` | Celery task: agenda scans YARA periodicos pra todos os hosts ativos. | 0 | 3 | 85 |

### Rotas HTTP

| Blueprint/Router | Métodos | Caminho | Handler | Arquivo |
|---|---|---|---|---|
| router | PATCH | `/api/v1/actions/{action_id}` | `revert_action` | `server/app/api/actions.py` |
| router | DELETE | `/api/v1/actions/{action_id}` | `delete_action` | `server/app/api/actions.py` |
| router | GET | `/api/v1/hosts/{host_id}/actions` | `list_actions_for_host` | `server/app/api/actions.py` |
| router | POST | `/api/v1/agents/enroll` | `enroll` | `server/app/api/agents.py` |
| router | GET | `/api/v1/alerts` | `list_alerts` | `server/app/api/alerts.py` |
| router | GET | `/api/v1/alerts/count` | `count_alerts` | `server/app/api/alerts.py` |
| router | GET | `/api/v1/alerts/{alert_id}` | `get_alert` | `server/app/api/alerts.py` |
| router | PATCH | `/api/v1/alerts/{alert_id}` | `update_alert` | `server/app/api/alerts.py` |
| router | DELETE | `/api/v1/alerts/{alert_id}` | `delete_alert` | `server/app/api/alerts.py` |
| router | GET | `/api/v1/audit-logs` | `list_audit_logs` | `server/app/api/audit.py` |
| router | GET | `/api/v1/compliance/login-timeline` | `login_timeline` | `server/app/api/audit.py` |
| router | GET | `/api/v1/compliance/report` | `compliance_report` | `server/app/api/audit.py` |
| router | GET | `/api/v1/compliance/report/pdf` | `compliance_report_pdf` | `server/app/api/audit.py` |
| router | POST | `/api/v1/auth/login` | `login` | `server/app/api/auth.py` |
| router | POST | `/api/v1/auth/logout` | `logout` | `server/app/api/auth.py` |
| router | GET | `/api/v1/auth/me` | `me` | `server/app/api/auth.py` |
| router | POST | `/api/v1/auth/refresh` | `refresh` | `server/app/api/auth.py` |
| router | POST | `/api/v1/hosts/{host_id}/clamav-scan` | `trigger_clamav_scan` | `server/app/api/clamav.py` |
| router | GET | `/api/v1/docs` | `list_docs` | `server/app/api/docs.py` |
| router | GET | `/api/v1/docs/{slug}` | `get_doc` | `server/app/api/docs.py` |
| router | GET | `/api/v1/hosts/{host_id}/events` | `list_events` | `server/app/api/events.py` |
| router | POST | `/api/v1/hosts/{host_id}/fail2ban-ban` | `trigger_fail2ban_ban` | `server/app/api/fail2ban.py` |
| router | POST | `/api/v1/hosts/{host_id}/fail2ban-unban` | `trigger_fail2ban_unban` | `server/app/api/fail2ban.py` |
| router | POST | `/api/v1/hosts/{host_id}/firewall-rule` | `add_firewall_rule` | `server/app/api/firewall.py` |
| router | DELETE | `/api/v1/hosts/{host_id}/firewall-rule` | `remove_firewall_rule` | `server/app/api/firewall.py` |
| router | GET | `/api/v1/health` | `health` | `server/app/api/health.py` |
| router | GET | `/api/v1/hosts` | `list_hosts` | `server/app/api/hosts.py` |
| router | POST | `/api/v1/hosts` | `create_host` | `server/app/api/hosts.py` |
| router | GET | `/api/v1/hosts/{host_id}` | `get_host` | `server/app/api/hosts.py` |
| router | PUT | `/api/v1/hosts/{host_id}` | `update_host` | `server/app/api/hosts.py` |
| router | DELETE | `/api/v1/hosts/{host_id}` | `delete_host` | `server/app/api/hosts.py` |
| router | POST | `/api/v1/hosts/{host_id}/enrollment-token` | `mint_enrollment_token` | `server/app/api/hosts.py` |
| router | GET | `/api/v1/kb/explain` | `explain` | `server/app/api/kb.py` |
| router | GET | `/api/v1/kb/hunting` | `list_hunting_queries` | `server/app/api/kb.py` |
| router | GET | `/api/v1/kb/playbooks` | `list_playbooks` | `server/app/api/kb.py` |
| router | GET | `/api/v1/kb/techniques` | `list_techniques` | `server/app/api/kb.py` |
| router | GET | `/api/v1/kb/techniques/{tid}` | `get_technique` | `server/app/api/kb.py` |
| router | POST | `/api/v1/lab/reset` | `reset_demo` | `server/app/api/lab.py` |
| router | GET | `/api/v1/lab/status` | `status_endpoint` | `server/app/api/lab.py` |
| router | GET | `/api/v1/lab/vms` | `list_vms_endpoint` | `server/app/api/lab.py` |
| router | POST | `/api/v1/lab/vms/{name}/attack` | `attack_vm_endpoint` | `server/app/api/lab.py` |
| router | POST | `/api/v1/lab/vms/{name}/start` | `start_vm_endpoint` | `server/app/api/lab.py` |
| router | POST | `/api/v1/lab/vms/{name}/stop` | `stop_vm_endpoint` | `server/app/api/lab.py` |
| router | GET | `/api/v1/organizations` | `list_organizations` | `server/app/api/organizations.py` |
| router | POST | `/api/v1/organizations` | `create_organization` | `server/app/api/organizations.py` |
| router | GET | `/api/v1/organizations/{org_id}` | `get_organization` | `server/app/api/organizations.py` |
| router | PUT | `/api/v1/organizations/{org_id}` | `update_organization` | `server/app/api/organizations.py` |
| router | POST | `/api/v1/hosts/{host_id}/aide-check` | `trigger_aide_check` | `server/app/api/tools.py` |
| router | POST | `/api/v1/hosts/{host_id}/chkrootkit-scan` | `trigger_chkrootkit_scan` | `server/app/api/tools.py` |
| router | POST | `/api/v1/hosts/{host_id}/lynis-audit` | `trigger_lynis_audit` | `server/app/api/tools.py` |
| router | POST | `/api/v1/hosts/{host_id}/rkhunter-scan` | `trigger_rkhunter_scan` | `server/app/api/tools.py` |
| router | GET | `/api/v1/hosts/{host_id}/packages` | `list_packages` | `server/app/api/vulnerabilities.py` |
| router | POST | `/api/v1/hosts/{host_id}/scan` | `trigger_scan` | `server/app/api/vulnerabilities.py` |
| router | GET | `/api/v1/hosts/{host_id}/vulnerabilities` | `list_vulnerabilities` | `server/app/api/vulnerabilities.py` |
| router | POST | `/api/v1/hosts/{host_id}/yara-scan` | `trigger_yara_scan` | `server/app/api/yara.py` |

### Modelos (ORM)

| Modelo | Tabela | Campos | Principais campos | Arquivo |
|---|---|---|---|---|
| `Base` |  | 0 |  | `server/app/db.py` |
| `Action` | actions | 13 | id, host_id, alert_id, action_type, target, reason, status, error_message, created_at, updated_at, sent_at, executed_at, reverted_at | `server/app/models/action.py` |
| `Alert` | alerts | 13 | id, host_id, rule_id, rule_name, severity, description, count, first_event_at, last_event_at, status, dedup_key, created_at, updated_at | `server/app/models/alert.py` |
| `AuditLog` | audit_logs | 11 | id, org_id, actor_user_id, actor_email, action, target_type, target_id, ip_address, user_agent, success, created_at | `server/app/models/audit_log.py` |
| `Host` | hosts | 48 | id, org_id, name, hostname, os_family, os_distro, os_version, kernel, arch, location, status, last_heartbeat, enrollment_token, enrollment_token_expires_at … | `server/app/models/host.py` |
| `HostPackage` | host_packages | 7 | id, host_id, name, version, arch, source, last_seen_at | `server/app/models/host_package.py` |
| `HostVulnerability` | host_vulnerabilities | 11 | id, host_id, cve_id, package_name, installed_version, fixed_version, severity, cvss_score, summary, discovered_at, last_seen_at | `server/app/models/host_vulnerability.py` |
| `Organization` | organizations | 5 | id, name, slug, created_at, updated_at | `server/app/models/organization.py` |
| `RefreshTokenJti` | refresh_token_jtis | 5 | jti, user_id, issued_at, expires_at, revoked_at | `server/app/models/refresh_token_jti.py` |
| `User` | users | 9 | id, org_id, email, password_hash, name, role, is_active, created_at, updated_at | `server/app/models/user.py` |

### Testes

| Arquivo | Testes | O que cobre |
|---|---|---|
| `server/tests/test_alerts.py` | 6 | Testes do REST /api/v1/alerts (CRUD + filters + count). |
| `server/tests/test_audit_and_compliance.py` | 13 | Testes do audit log + compliance report + PII masking. |
| `server/tests/test_auth.py` | 6 |  |
| `server/tests/test_ca.py` | 5 | Testes do servico de PKI: idempotencia e validacao de assinatura. |
| `server/tests/test_docs.py` | 6 | Testes do /api/v1/docs — serve markdown do diretorio docs/ do repo. |
| `server/tests/test_enrollment.py` | 4 |  |
| `server/tests/test_events_endpoint.py` | 3 | Test do REST GET /hosts/:id/events. Exige Loki disponivel pra fluxo completo. |
| `server/tests/test_health.py` | 1 |  |
| `server/tests/test_hosts.py` | 3 |  |
| `server/tests/test_inventory_grpc.py` | 4 | Testes do RPC SubmitInventory: upsert host_packages + agendamento de scan OSV. |
| `server/tests/test_kb.py` | 22 | Testes da Knowledge Base — loader + REST endpoints. |
| `server/tests/test_lab.py` | 9 | Testes do /api/v1/lab — controle de VMs OrbStack + reset demo. |
| `server/tests/test_loki.py` | 2 | Testes integrados do cliente Loki — exigem Loki rodando. |
| `server/tests/test_policy_and_actions.py` | 14 | Testes da policy de auto-block + endpoints REST de actions. |
| `server/tests/test_rbac_and_new_endpoints.py` | 12 | Cobertura RBAC + endpoints novos (Fase H2/H3/H6/H7) + cross-tenant. |
| `server/tests/test_rules.py` | 8 | Testes do loader + evaluator de regras (sem dependencia de DB ou Loki). |
| `server/tests/test_tenant_isolation.py` | 8 | Tenant isolation: usuario da Org A nao consegue ver/modificar recursos da Org B. |
| `server/tests/test_vulnerabilities.py` | 15 | Testes do scan de vulnerabilidades + endpoints + OSV mapping (sem rede). |
| `server/tests/test_yara_dispatch.py` | 5 | Testes do mapeamento Action -> pb.Command e da task de scheduled scan YARA. |

## Go

| Pacote | O que é (doc) | Arquivos | Tipos exp. | Funções exp. | Testes |
|---|---|---|---|---|---|
| `agent/cmd/sentinel-agent` |  | 1 | 0 | 0 | 0 |
| `agent/internal/agentstate` | gerencia o estado persistente do agente apos enrollment: | 1 | 2 | 4 | 0 |
| `agent/internal/clamavdetect` | verifica se ClamAV esta instalado no host e retorna | 1 | 1 | 1 | 0 |
| `agent/internal/cmddispatcher` | recebe pb.Command vindos do server (no HeartbeatResponse) | 3 | 1 | 3 | 16 |
| `agent/internal/collectors` | implementa as fontes de eventos do agente. Uma `Source` produz | 4 | 6 | 12 | 2 |
| `agent/internal/config` |  | 1 | 2 | 1 | 0 |
| `agent/internal/enrollclient` | faz o POST /api/v1/agents/enroll para trocar token por certs. | 1 | 1 | 1 | 0 |
| `agent/internal/events` | define o evento normalizado que o agente envia ao server via gRPC StreamEvents. | 1 | 2 | 1 | 0 |
| `agent/internal/eventstream` | gerencia o canal bidirecional gRPC StreamEvents: | 1 | 1 | 1 | 0 |
| `agent/internal/filewatcher` | monitora diretorios via fsnotify e dispara YARA scans | 1 | 1 | 1 | 2 |
| `agent/internal/firewall` | abstrai o gerenciador de firewall do OS. | 10 | 4 | 16 | 0 |
| `agent/internal/grpc/pb` |  | 2 | 49 | 282 | 0 |
| `agent/internal/grpcclient` | encapsula o cliente gRPC do agente, configurado com mTLS | 1 | 0 | 1 | 0 |
| `agent/internal/heartbeat` | roda o loop de heartbeat do agente: a cada N segundos, | 1 | 1 | 1 | 0 |
| `agent/internal/hoststats` | coleta snapshot de stats do host (CPU, memoria, disco, IP, | 1 | 0 | 1 | 0 |
| `agent/internal/logging` |  | 1 | 0 | 1 | 0 |
| `agent/internal/mac` | abstrai o sistema de Mandatory Access Control: SELinux ou AppArmor. | 4 | 5 | 4 | 0 |
| `agent/internal/osdetect` |  | 2 | 1 | 1 | 0 |
| `agent/internal/packagemgr` | abstrai o gerenciador de pacotes do OS. | 8 | 4 | 25 | 0 |
| `agent/internal/parsers/apparmor` | extrai eventos de denials AppArmor do dmesg/journald/audit.log. | 1 | 0 | 1 | 4 |
| `agent/internal/parsers/selinux` | extrai eventos de denials AVC do auditd (linhas type=AVC em | 1 | 0 | 1 | 5 |
| `agent/internal/parsers/sshd` | extrai eventos de seguranca de logs do sshd (auth.log, /var/log/secure, journald). | 1 | 0 | 1 | 7 |
| `agent/internal/quarantine` | isola arquivos maliciosos: move pra um diretorio | 1 | 2 | 2 | 4 |
| `agent/internal/sysadmin` | coleta counts pra dashboard "estado do sistema": | 1 | 0 | 4 | 0 |
| `agent/internal/toolsdetect` | verifica quais ferramentas de seguranca/hardening estao | 1 | 2 | 1 | 0 |
| `agent/internal/yarascanner` | roda o binario `yara` contra um diretorio alvo e parseia | 1 | 2 | 3 | 5 |

## Web (JS/TS/Svelte/React)

| Pasta | Arquivos |
|---|---|
| `web/src` | App.tsx, main.tsx |
| `web/src/components` | ActionsTab.tsx, AidePanel.tsx, AppArmorPanel.tsx, AppHeader.tsx, AuditdPanel.tsx, Breadcrumbs.tsx, ChkrootkitPanel.tsx, ClamavPanel.tsx, ConfirmDialog.tsx, ErrorBoundary.tsx, EventsTab.tsx, ExplainPopover.tsx, Fail2banPanel.tsx, FirewallPanel.tsx, Logo.tsx, LynisPanel.tsx, Modal.tsx, OsIcon.tsx, RkhunterPanel.tsx, RowActionsMenu.tsx, SELinuxPanel.tsx, ScanProgressBadge.tsx, SessionTimer.tsx, TableLimit.tsx, Tabs.tsx, ToolsPanel.tsx, Tooltip.tsx, VulnerabilitiesTab.tsx, YaraPanel.tsx |
| `web/src/pages` | AlertsPage.tsx, CompliancePage.tsx, DocsPage.tsx, HostDetailPage.tsx, HostsPage.tsx, HuntingPage.tsx, KbPage.tsx, LabPage.tsx, LoginPage.tsx, PurpleTeamPage.tsx |
| `web/src/lib` | api.ts, useLabMode.ts, useModalShell.ts, usePolling.ts, utils.ts |
| `web/src/stores` | auth.ts |
| `web/src/test` | setup.ts |

### Testes web

| Arquivo | Testes |
|---|---|
| `web/src/App.test.tsx` | 4 |
| `web/src/lib/api.test.ts` | 13 |
| `web/src/lib/usePolling.test.ts` | 5 |
| `web/src/pages/LoginPage.test.tsx` | 6 |
| `web/src/stores/auth.test.ts` | 3 |

## Scripts de shell

| Arquivo | Primeira linha de comentário |
|---|---|
| `start-dev.command` | Double-click esse arquivo no Finder pra subir TODO o ambiente de dev: |
| `stop-dev.command` | Double-click pra parar tudo: dev servers + docker stack. |
