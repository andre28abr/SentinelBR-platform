# Política de segurança

## Reportando vulnerabilidades

Por favor **NÃO abra issue pública** se você achar uma vulnerabilidade de
segurança. Em vez disso, abra um [GitHub Security Advisory privado](https://github.com/andre28abr/SentinelBR-platform/security/advisories/new)
ou envie email para o mantenedor (perfil no [GitHub](https://github.com/andre28abr)).

Tento responder em até 7 dias. Como este é um projeto pessoal de
portfólio sem SLA comercial, mantenha expectativas calibradas — a
gravidade do problema vai pautar a prioridade.

## Escopo

Este projeto inclui **propositalmente** componentes vulneráveis para fins
de demonstração:

- VMs em `samples/labs/` são **intencionalmente** vulneráveis (Metasploitable-style)
- Fixtures em `samples/malicious-fixtures/` são iscas inertes (EICAR + texto que casa YARA)
- `SENTINELBR_LAB_MODE=true` habilita endpoints `/api/v1/lab/*` que rodam
  comandos shell no host (controle de VMs OrbStack) — NUNCA habilite em produção

**Não são vulnerabilidades**:
- Que VMs do lab sejam vulneráveis (é o objetivo do lab)
- Que `SENTINELBR_LAB_MODE=true` permita shell exec (é o objetivo do flag)
- Credenciais default de seed (`admin@sentinelbr.io` / `admin1234`) em
  ambiente dev — código exige `SEED_PASSWORD` em prod

**São vulnerabilidades reportáveis**:
- Path traversal, SQL injection, command injection em endpoints reais
- Quebra de tenant isolation (cross-org leakage)
- Auth bypass, privilege escalation
- XSS, CSRF, deserialization, SSRF
- Vulnerabilidade em deps que afete o projeto (rode `make security` localmente
  primeiro pra ver se já estamos cientes via govulncheck / pip-audit / pnpm audit)

## Mecanismos de defesa existentes

- JWT secret obrigatório em prod (boot fail se default)
- Rate limiting em `/auth/login` (10/min) e `/agents/enroll` (20/min)
- Refresh tokens em cookie httpOnly + JTI rotation com revogação
- bcrypt com dummy hash em login (anti enumeração de usuário)
- mTLS no gRPC do agente (CA própria, CN = host_id)
- CSP + CORS estritos (sem wildcards em prod)
- LGPD: audit log append-only, retenção configurável (`SENTINELBR_AUDIT_RETENTION_DAYS`)
- CHECK constraints DB em campos enum (severity, status)
- Scans de CVE automáticos no CI: govulncheck (Go) + pip-audit (Python) + pnpm audit + Trivy fs
- Tenant isolation enforced em todos os endpoints REST (404 leakage-safe)

## Histórico de divulgações

Nenhuma vulnerabilidade reportada ainda.
