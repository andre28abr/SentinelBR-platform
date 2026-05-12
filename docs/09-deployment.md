# SentinelBR — Deployment e Instalação

> Guia completo de como instalar, configurar e operar o SentinelBR em diferentes ambientes. Cobre desde "rodar localmente em 2 minutos" até "produção em Kubernetes com alta disponibilidade".

---

## 📋 Sumário

1. [Visão geral dos cenários](#visão-geral-dos-cenários)
2. [Requisitos de sistema](#requisitos-de-sistema)
3. [Cenário 1: Desenvolvimento local](#cenário-1-desenvolvimento-local)
4. [Cenário 2: VPS standalone (recomendado para SMBs)](#cenário-2-vps-standalone)
5. [Cenário 3: Self-hosted em servidor próprio](#cenário-3-self-hosted-em-servidor-próprio)
6. [Cenário 4: Kubernetes (produção)](#cenário-4-kubernetes-produção)
7. [Cenário 5: Cloud (AWS/GCP/Azure)](#cenário-5-cloud-awsgcpazure)
8. [Configuração](#configuração)
9. [Instalação do agente nos hosts](#instalação-do-agente-nos-hosts)
10. [HTTPS e certificados](#https-e-certificados)
11. [Backup e disaster recovery](#backup-e-disaster-recovery)
12. [Monitoramento e operação](#monitoramento-e-operação)
13. [Atualizações e migrações](#atualizações-e-migrações)
14. [Troubleshooting](#troubleshooting)
15. [Hardening de segurança](#hardening-de-segurança)
16. [Checklists](#checklists)

---

## Visão geral dos cenários

| Cenário | Para quem | Tempo de setup | Custo |
|---------|-----------|----------------|-------|
| Desenvolvimento local | Desenvolvedores | 5 min | $0 |
| VPS standalone | SMBs (até 50 hosts) | 30 min | R$ 30-100/mês |
| Self-hosted (servidor próprio) | Empresas com infra | 1-2h | hardware existente |
| Kubernetes | Empresas grandes (100+ hosts) | 2-4h | $50-500/mês |
| Cloud gerenciada | Quem prefere serviços gerenciados | 1-2h | $100-1000/mês |

---

## Requisitos de sistema

### Mínimo (até 10 hosts)

- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Disco**: 40 GB SSD
- **OS**: Ubuntu 22.04 LTS, Debian 12, Rocky Linux 9
- **Rede**: IP público ou VPN para acesso dos agentes

### Recomendado (até 50 hosts)

- **CPU**: 4 vCPU
- **RAM**: 8 GB
- **Disco**: 100 GB SSD
- **Backup**: storage adicional 200 GB

### Para 100+ hosts

- **CPU**: 8 vCPU
- **RAM**: 16 GB
- **Disco**: 250 GB SSD
- **Considerar**: Kubernetes ou múltiplas VMs

### Requisitos do agente (em cada host monitorado)

- **CPU**: ~2% em idle, picos de 5% durante coleta
- **RAM**: ~30 MB em idle, ~80 MB em load
- **Disco**: 500 MB para buffer (configurável)
- **OS suportados**: Ubuntu 20.04+, Debian 11+, RHEL/Rocky/Alma 8+, CentOS 7+ (legacy)
- **Rede**: saída para o servidor central na porta 9090 (gRPC)

---

## Cenário 1: Desenvolvimento local

### Pré-requisitos

- Docker 24+ e Docker Compose v2
- Git
- 8 GB RAM disponível

### Setup em 5 minutos

```bash
# 1. Clone o repositório
git clone https://github.com/sentinelbr/sentinelbr.git
cd sentinelbr

# 2. Copie o template de configuração
cp .env.example .env

# 3. Suba o ambiente
make dev-up
# ou: docker compose -f docker-compose.dev.yml up -d

# 4. Execute as migrations
make migrate

# 5. Seed dos dados iniciais (admin, regras starter)
make seed

# 6. Acesse
echo "Frontend: http://localhost:5173"
echo "API: http://localhost:8000/docs"
echo "Grafana: http://localhost:3000 (admin/admin)"
```

### Credenciais default

```
Admin: admin@sentinelbr.local
Senha: (mostrada no terminal após `make seed`)
```

### Hot reload

- **Backend**: `uvicorn` com `--reload` ativo no compose dev
- **Frontend**: Vite com HMR
- **Agente**: precisa rebuild manual (`make agent-build`)

### Estrutura dos serviços (docker-compose.dev.yml)

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]
    
  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]
  
  loki:
    image: grafana/loki:3.0
    ports: ["3100:3100"]
  
  grafana:
    image: grafana/grafana:10
    ports: ["3000:3000"]
  
  minio:
    image: minio/minio
    ports: ["9000:9000", "9001:9001"]
  
  api:
    build: ./server
    ports: ["8000:8000"]
    volumes: ["./server:/app"]
    command: uvicorn sentinelbr.api.main:app --reload
  
  worker:
    build: ./server
    command: celery -A sentinelbr.workers.celery_app worker -l info
  
  web:
    build: ./web
    ports: ["5173:5173"]
    volumes: ["./web:/app"]
```

### Resetar ambiente

```bash
make dev-reset  # apaga volumes e recria
```

---

## Cenário 2: VPS standalone

**Cenário ideal**: SMBs com até 50 hosts, querem self-hosted barato.

### Provedores recomendados (em maio/2026)

| Provedor | Plano sugerido | Preço aprox |
|----------|----------------|-------------|
| Hetzner | CPX21 (4 vCPU, 8 GB) | €8/mês (~R$ 50) |
| DigitalOcean | Premium 4GB | $24/mês (~R$ 120) |
| Vultr | High Performance 4GB | $24/mês |
| AWS Lightsail | 4GB | $24/mês |
| Oracle Cloud | Free tier (4 vCPU ARM, 24GB!) | $0 |

### Passo a passo (Ubuntu 22.04)

#### 1. Acesso inicial e hardening básico

```bash
# Conectar como root
ssh root@SEU_IP

# Atualizar sistema
apt update && apt upgrade -y

# Criar usuário não-root
adduser sentinel
usermod -aG sudo sentinel

# Configurar SSH para esse usuário
mkdir -p /home/sentinel/.ssh
cp ~/.ssh/authorized_keys /home/sentinel/.ssh/
chown -R sentinel:sentinel /home/sentinel/.ssh
chmod 700 /home/sentinel/.ssh
chmod 600 /home/sentinel/.ssh/authorized_keys

# Desabilitar login root
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# Sair e reconectar como sentinel
exit
ssh sentinel@SEU_IP
```

#### 2. Firewall básico

```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 9090/tcp  # gRPC para agentes
sudo ufw enable
```

#### 3. Instalar Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker sentinel
newgrp docker

# Verificar
docker run hello-world
```

#### 4. Baixar e configurar SentinelBR

```bash
# Diretório de instalação
sudo mkdir -p /opt/sentinelbr
sudo chown sentinel:sentinel /opt/sentinelbr
cd /opt/sentinelbr

# Baixar release oficial
curl -fsSL https://get.sentinelbr.io | bash
# (esse script baixa docker-compose.yml e cria estrutura inicial)

# Editar .env
nano .env
```

**Variáveis obrigatórias no `.env`:**

```bash
# Domínio
DOMAIN=sentinelbr.suaempresa.com.br

# Email para Let's Encrypt
ACME_EMAIL=admin@suaempresa.com.br

# Senhas (gerar com `openssl rand -hex 32`)
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
MINIO_ROOT_PASSWORD=...
SECRET_KEY=...

# Email para alertas
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=...
```

#### 5. Subir os serviços

```bash
docker compose pull
docker compose up -d

# Aguardar serviços ficarem ready
docker compose logs -f api | grep "Application startup complete"
# Ctrl+C quando aparecer
```

#### 6. Inicializar banco

```bash
# Migrations
docker compose exec api alembic upgrade head

# Seed (admin + regras starter)
docker compose exec api python -m sentinelbr.scripts.seed

# Anote a senha do admin que aparecer
```

#### 7. Configurar HTTPS (Caddy faz automático)

O `docker-compose.yml` já vem com Caddy que pega cert do Let's Encrypt automaticamente. Basta apontar o DNS do domínio para o IP da VPS.

```bash
# Aguardar 1-2 min após DNS propagar
curl https://sentinelbr.suaempresa.com.br/health/live
# Deve retornar {"status":"alive"}
```

#### 8. Acessar

Abra `https://sentinelbr.suaempresa.com.br` e faça login.

### Backup automático

Adicionar ao crontab:

```bash
sudo crontab -e

# Backup diário às 3h
0 3 * * * /opt/sentinelbr/scripts/backup.sh

# Limpeza de backups antigos > 30 dias
0 4 * * * find /opt/sentinelbr/backups -name "*.dump" -mtime +30 -delete
```

`scripts/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/opt/sentinelbr/backups"

mkdir -p "$BACKUP_DIR"

# PostgreSQL
docker compose exec -T postgres pg_dump -U sentinelbr sentinelbr | gzip > "$BACKUP_DIR/pg_${DATE}.sql.gz"

# Volumes do MinIO (incremental, com mc)
docker compose exec -T minio mc mirror /data /backup/minio_${DATE}

echo "Backup ${DATE} concluído"
```

---

## Cenário 3: Self-hosted em servidor próprio

Para empresas que já têm infra Linux e querem rodar on-premise.

### Diferenças do VPS

- **Rede**: cuide de NAT/proxy reverso para que agentes externos consigam conectar (ou use VPN)
- **Storage**: provavelmente RAID/LVM disponíveis (use!)
- **Backup**: integre com solução de backup existente
- **Monitoramento**: integre com Zabbix/Nagios/Prometheus existentes

### Considerações de storage

Recomendação para servidor com storage abundante:

```
/opt/sentinelbr/
├── postgres/         ← SSD (performance)
├── redis/            ← SSD (RAM mostly)
├── loki/
│   ├── chunks/       ← HDD ou storage barato (volume)
│   └── index/        ← SSD (queries)
├── minio/            ← HDD/storage volumoso
└── backups/          ← outro disco/NFS para isolar
```

Use volumes nomeados do Docker mapeados a paths específicos:

```yaml
# docker-compose.yml (override)
services:
  postgres:
    volumes:
      - /mnt/ssd/sentinelbr/postgres:/var/lib/postgresql/data
  loki:
    volumes:
      - /mnt/ssd/sentinelbr/loki/index:/loki/index
      - /mnt/hdd/sentinelbr/loki/chunks:/loki/chunks
```

### Integração com VPN

Se servidor está em rede privada, agentes em hosts diversos precisam acessar:

**Opção A: VPN (WireGuard)**

```bash
# Cada host instala WireGuard e ganha IP da VPN
# Agente conecta no IP VPN do servidor central
```

**Opção B: Proxy reverso público + autenticação forte**

- Caddy/Nginx público encaminha porta 9090 para servidor interno
- mTLS já garante autenticação dos agentes (não precisa VPN)

### Bare-metal ou VM?

- **VM**: mais flexível, snapshots, migração entre hosts
- **Bare-metal**: ~10-15% performance maior, sem overhead

Para MVP, VM é mais que suficiente.

---

## Cenário 4: Kubernetes (produção)

**Quando faz sentido**: 100+ hosts monitorados, equipe que opera K8s, requisitos de HA.

### Pré-requisitos

- Cluster K8s 1.28+ (managed: GKE, EKS, AKS, ou self-hosted: kubeadm, k3s, RKE2)
- `kubectl` configurado
- `helm` 3.13+
- Storage class com support a `ReadWriteOnce` (default)
- Ingress controller (nginx-ingress, traefik, etc.)
- cert-manager (para HTTPS)

### Helm chart

```bash
# Adicionar repositório
helm repo add sentinelbr https://charts.sentinelbr.io
helm repo update

# Criar values customizado
cat > values-prod.yaml <<EOF
global:
  domain: sentinelbr.suaempresa.com.br
  
api:
  replicas: 3
  resources:
    requests: {cpu: 500m, memory: 512Mi}
    limits: {cpu: 2000m, memory: 2Gi}

worker:
  queues:
    correlation: {replicas: 2}
    enrichment: {replicas: 2}
    ml: {replicas: 1}
    notification: {replicas: 1}

postgres:
  enabled: true
  persistence:
    size: 50Gi
    storageClass: fast-ssd
  primary:
    resources:
      requests: {cpu: 1000m, memory: 2Gi}

redis:
  enabled: true
  architecture: replication
  
loki:
  enabled: true
  persistence:
    size: 200Gi

minio:
  enabled: true
  persistence:
    size: 500Gi
  mode: distributed
  replicas: 4

ingress:
  enabled: true
  className: nginx
  certManager:
    issuer: letsencrypt-prod
EOF

# Instalar
helm install sentinelbr sentinelbr/sentinelbr \
  -f values-prod.yaml \
  -n sentinelbr --create-namespace

# Verificar
kubectl -n sentinelbr get pods
kubectl -n sentinelbr get ingress
```

### Recursos criados pelo Helm

```
sentinelbr namespace
├── Deployments
│   ├── api (3 replicas)
│   ├── worker-correlation (2)
│   ├── worker-enrichment (2)
│   ├── worker-ml (1)
│   ├── worker-notification (1)
│   ├── stream-processor (2)
│   └── web (2)
│
├── StatefulSets
│   ├── postgres-primary
│   ├── postgres-replica (2)
│   ├── redis-master
│   ├── redis-replica (2)
│   ├── loki (3)
│   └── minio (4)
│
├── Services
│   ├── api (ClusterIP)
│   ├── grpc-agent (LoadBalancer ou NodePort)
│   ├── web (ClusterIP)
│   └── ... (internos)
│
├── Ingress
│   └── sentinelbr.suaempresa.com.br
│
├── Secrets
│   ├── postgres-credentials
│   ├── jwt-keys
│   └── ...
│
├── ConfigMaps
│   ├── api-config
│   └── ...
│
├── HPAs (auto-scaling)
│   ├── api (cpu 70%)
│   └── workers (queue depth)
│
├── PodDisruptionBudgets
│   └── api (minAvailable: 2)
│
└── NetworkPolicies
    └── (isolation entre componentes)
```

### Auto-scaling

API escala por CPU:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
spec:
  scaleTargetRef:
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Workers escalam por profundidade de fila (com KEDA):

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-correlation
spec:
  scaleTargetRef:
    name: worker-correlation
  minReplicaCount: 2
  maxReplicaCount: 20
  triggers:
    - type: redis
      metadata:
        address: redis:6379
        listName: queue:correlation
        listLength: "100"
```

### Observabilidade no K8s

Stack recomendada:
- **Prometheus** (kube-prometheus-stack) para métricas
- **Loki** para logs do K8s (separado do Loki da plataforma!)
- **Tempo** para tracing
- **Grafana** unificando

ServiceMonitors para coletar métricas do SentinelBR:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: sentinelbr-api
spec:
  selector:
    matchLabels: {app: sentinelbr-api}
  endpoints:
    - port: metrics
      interval: 30s
```

---

## Cenário 5: Cloud (AWS/GCP/Azure)

Para quem prefere serviços gerenciados em vez de self-hosted.

### AWS — arquitetura sugerida

```
┌──────────────────────────────────────────────────┐
│                    Route 53 (DNS)                │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
        ┌────────────────────────────────┐
        │ Application Load Balancer       │
        │ + ACM (TLS)                     │
        └────────────┬───────────────────┘
                     │
        ┌────────────┴───────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│ ECS Fargate      │    │ NLB (gRPC)       │
│ Service: api     │    │ porta 9090       │
│ Service: web     │    └────────┬─────────┘
│ Service: workers │             │
└────┬─────────────┘             ▼
     │                  ┌──────────────────┐
     │                  │ ECS Fargate      │
     ▼                  │ Service: grpc    │
┌──────────┐            └──────────────────┘
│ RDS PG   │            
│ (Multi-AZ)│           ┌──────────────────┐
└──────────┘            │ ElastiCache      │
                        │ (Redis cluster)  │
                        └──────────────────┘

S3 (substitui MinIO)
CloudWatch Logs (alternativa ao Loki para logs internos)
```

### Custo estimado AWS (10 hosts)

| Recurso | Especificação | Mensal |
|---------|---------------|--------|
| ECS Fargate | 4 services, 0.5 vCPU each | $40 |
| RDS PostgreSQL | db.t3.medium Multi-AZ | $80 |
| ElastiCache Redis | cache.t3.micro | $15 |
| S3 | 50 GB | $1 |
| Data transfer | 100 GB | $9 |
| ALB + NLB | 2 LBs | $30 |
| Route 53 | 1 hosted zone | $0.50 |
| **Total** | | **~$175 (~R$ 870)** |

Comparação: VPS Hetzner = ~R$ 50/mês. **17x mais caro!** Mas com tudo gerenciado.

### Terraform

```bash
# Modules pré-prontos no repositório
cd deploy/terraform/aws

# Configurar
cp terraform.tfvars.example terraform.tfvars
# editar com seus valores

# Deploy
terraform init
terraform plan
terraform apply
```

---

## Configuração

### Hierarquia de configuração

```
1. Defaults no código (config.py)
2. Arquivo de config principal (/etc/sentinelbr/config.yml)
3. Variáveis de ambiente (.env ou systemd Environment=)
4. Secrets em runtime (variáveis dinâmicas)
```

Quanto mais embaixo, maior prioridade.

### Variáveis principais

```yaml
# /etc/sentinelbr/config.yml

server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  debug: false

database:
  url: postgresql+asyncpg://user:pass@host/db
  pool_size: 20
  max_overflow: 10

redis:
  url: redis://:password@host:6379

loki:
  url: http://loki:3100
  retention_days: 30

minio:
  url: http://minio:9000
  access_key: ...
  secret_key: ...
  buckets:
    evidences: sentinelbr-evidences
    reports: sentinelbr-reports
    backups: sentinelbr-backups

security:
  jwt_secret: ...        # gerar com `openssl rand -hex 64`
  jwt_access_ttl: 900    # 15min
  jwt_refresh_ttl: 604800 # 7 dias
  password_min_length: 12
  mfa_required_for_admin: true

agent:
  grpc_port: 9090
  ca_cert_path: /etc/sentinelbr/ca/ca.crt
  ca_key_path: /etc/sentinelbr/ca/ca.key
  cert_validity_days: 90

retention:
  alerts_resolved: 365
  audit_events: 2555     # 7 anos
  agent_heartbeats: 90
  
notifications:
  email:
    enabled: true
    smtp_host: ...
    from: alerts@suaempresa.com.br
  telegram:
    enabled: true
    bot_token: ...
```

---

## Instalação do agente nos hosts

### Método 1: Via UI (recomendado)

1. Faça login no SentinelBR
2. **Hosts** → **+ Adicionar host**
3. Preencha hostname, tags
4. Copie o comando gerado
5. Execute no host alvo:

```bash
curl -fsSL https://sentinelbr.suaempresa.com.br/install.sh | \
  sudo bash -s -- \
  --token=enr_xyz123abc \
  --server=https://sentinelbr.suaempresa.com.br
```

6. Em ~30s o host aparece como "online" na UI

### Método 2: Manual

```bash
# Baixar binário
sudo curl -fsSL -o /usr/local/bin/sentinelbr-agent \
  https://github.com/sentinelbr/sentinelbr/releases/latest/download/agent-linux-amd64
sudo chmod +x /usr/local/bin/sentinelbr-agent

# Criar diretórios
sudo mkdir -p /etc/sentinelbr /var/lib/sentinelbr /var/log/sentinelbr

# Configurar
sudo tee /etc/sentinelbr/agent.yml <<EOF
server:
  url: https://sentinelbr.suaempresa.com.br
  port: 9090
  
buffer:
  path: /var/lib/sentinelbr/buffer.db
  max_size_mb: 500
  
collectors:
  auditd: {enabled: true}
  syslog: {enabled: true}
  ssh: {enabled: true}
  nginx: {enabled: false}
EOF

# Enrollment
sudo sentinelbr-agent enroll --token=enr_xyz123abc

# Systemd unit
sudo tee /etc/systemd/system/sentinelbr-agent.service <<EOF
[Unit]
Description=SentinelBR Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sentinelbr-agent run --config /etc/sentinelbr/agent.yml
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now sentinelbr-agent

# Verificar
sudo systemctl status sentinelbr-agent
sudo journalctl -u sentinelbr-agent -f
```

### Método 3: Ansible (instalação em massa)

```yaml
# playbook.yml
- hosts: all
  become: true
  collections:
    - sentinelbr.platform
  
  tasks:
    - name: Install SentinelBR agent
      include_role:
        name: sentinelbr.platform.agent
      vars:
        sentinelbr_server: https://sentinelbr.suaempresa.com.br
        sentinelbr_enrollment_token: "{{ enrollment_token_per_host[inventory_hostname] }}"
        sentinelbr_tags: ['prod', '{{ host_role }}']
```

### Método 4: Docker (para hosts containerizados)

```bash
docker run -d \
  --name sentinelbr-agent \
  --restart unless-stopped \
  --network host \
  --pid host \
  -v /var/log:/host/var/log:ro \
  -v /etc:/host/etc:ro \
  -v sentinelbr-buffer:/var/lib/sentinelbr \
  -e SBR_SERVER=https://sentinelbr.suaempresa.com.br \
  -e SBR_TOKEN=enr_xyz... \
  ghcr.io/sentinelbr/agent:latest
```

### Método 5: Kubernetes DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: sentinelbr-agent
spec:
  selector:
    matchLabels: {app: sentinelbr-agent}
  template:
    metadata:
      labels: {app: sentinelbr-agent}
    spec:
      hostNetwork: true
      hostPID: true
      containers:
        - name: agent
          image: ghcr.io/sentinelbr/agent:latest
          env:
            - name: SBR_SERVER
              value: https://sentinelbr.suaempresa.com.br
            - name: SBR_TOKEN
              valueFrom: {secretKeyRef: {name: sentinelbr-token, key: token}}
          volumeMounts:
            - {name: var-log, mountPath: /host/var/log, readOnly: true}
      volumes:
        - {name: var-log, hostPath: {path: /var/log}}
```

---

## HTTPS e certificados

### Opção 1: Caddy (mais simples)

`docker-compose.yml` já vem com Caddy que pega cert automático do Let's Encrypt:

```yaml
caddy:
  image: caddy:2-alpine
  ports: ["80:80", "443:443"]
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - caddy_data:/data
```

`Caddyfile`:
```
${DOMAIN} {
    encode gzip
    
    handle /api/* {
        reverse_proxy api:8000
    }
    
    handle /ws {
        reverse_proxy api:8000
    }
    
    handle {
        reverse_proxy web:80
    }
}
```

### Opção 2: Nginx + Certbot

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d sentinelbr.suaempresa.com.br
```

### Opção 3: Cert-manager (Kubernetes)

```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@suaempresa.com.br
    privateKeySecretRef: {name: letsencrypt-account}
    solvers:
      - http01:
          ingress: {class: nginx}
```

### Cert para gRPC (mTLS)

CA própria gerada na primeira inicialização. Não usa Let's Encrypt — é interno.

```bash
# Verificar CA
openssl x509 -in /etc/sentinelbr/ca/ca.crt -noout -text
```

---

## Backup e disaster recovery

### Estratégia 3-2-1

- **3** cópias dos dados (1 produção + 2 backups)
- **2** mídias diferentes (disco local + storage externo)
- **1** offsite (S3, B2, ou outro datacenter)

### Backup automático

Script `scripts/backup.sh` (rodar via cron):

```bash
#!/bin/bash
set -e

DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_DIR="/opt/sentinelbr/backups"
S3_BUCKET="s3://meu-backup/sentinelbr"

mkdir -p "$BACKUP_DIR"

# 1. PostgreSQL
docker compose exec -T postgres \
  pg_dump -U sentinelbr --format=custom --compress=9 sentinelbr \
  > "$BACKUP_DIR/pg_${DATE}.dump"

# 2. MinIO (mirror para outro storage)
docker compose exec -T minio \
  mc mirror /data backup/minio_${DATE}

# 3. Configurações
tar -czf "$BACKUP_DIR/configs_${DATE}.tar.gz" \
  /etc/sentinelbr \
  /opt/sentinelbr/.env \
  /opt/sentinelbr/docker-compose.yml

# 4. Upload para offsite
aws s3 cp "$BACKUP_DIR/" "$S3_BUCKET/" --recursive --exclude "*" --include "*${DATE}*"

# 5. Limpar backups locais > 7 dias
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup ${DATE} concluído"
```

### Restore

```bash
# Parar serviços que dependem do banco
docker compose stop api worker stream

# Restaurar PostgreSQL
docker compose exec -T postgres \
  pg_restore -U sentinelbr -d sentinelbr --clean \
  < /opt/sentinelbr/backups/pg_2026-05-09_03-00.dump

# Restaurar configs
tar -xzf /opt/sentinelbr/backups/configs_2026-05-09_03-00.tar.gz -C /

# Restaurar MinIO (se necessário)
docker compose exec minio mc mirror backup/minio_2026-05-09 /data

# Subir tudo
docker compose up -d

# Validar
curl https://sentinelbr.suaempresa.com.br/health/ready
```

### Teste de restore mensal (obrigatório)

Backup nunca testado = backup que provavelmente não funciona. Mensalmente:

```bash
# Cria container temporário, restaura backup, valida
./scripts/test-restore.sh /opt/sentinelbr/backups/latest.dump
```

---

## Monitoramento e operação

### Métricas essenciais para acompanhar

| Métrica | Saudável | Alerta |
|---------|----------|--------|
| API latência p95 | < 200ms | > 1s |
| Workers backlog | < 100 | > 1000 |
| PostgreSQL conexões | < 80% | > 95% |
| Disco | < 80% | > 90% |
| Agentes online | > 95% | < 90% |
| Eventos/segundo | varia | drop súbito |
| Erros 5xx/min | < 1 | > 10 |

### Dashboard Grafana

Importar dashboards prontos (IDs):
- 12345: SentinelBR Overview
- 12346: Performance & Latency
- 12347: Worker queues
- 12348: Database health
- 12349: Storage usage

### Alertas Prometheus

```yaml
groups:
- name: sentinelbr
  rules:
    - alert: APIHighLatency
      expr: histogram_quantile(0.95, sentinelbr_api_request_duration_seconds_bucket) > 1
      for: 5m
      annotations: {summary: "API p95 latency > 1s"}
    
    - alert: WorkerQueueBacklog
      expr: sentinelbr_worker_queue_length > 1000
      for: 10m
      
    - alert: AgentOffline
      expr: sentinelbr_active_agents / sentinelbr_total_agents < 0.9
      for: 5m
```

### Logs estruturados

Todos os componentes emitem JSON. Para consultar:

```bash
# API logs
docker compose logs api | jq 'select(.level == "ERROR")'

# Workers
docker compose logs worker | jq 'select(.task_name)'
```

---

## Atualizações e migrações

### Update menor (patch)

```bash
cd /opt/sentinelbr

# Backup primeiro!
./scripts/backup.sh

# Pull novas imagens
docker compose pull

# Rolling restart
docker compose up -d

# Migrations (se houver)
docker compose exec api alembic upgrade head
```

### Update maior (com breaking changes)

1. **Ler CHANGELOG.md** com atenção
2. **Backup completo**
3. **Testar em staging** se possível
4. **Janela de manutenção** anunciada
5. **Pull + restart**
6. **Migrations**
7. **Smoke tests**
8. **Rollback plan** se falhar

### Rollback

```bash
# Parar
docker compose down

# Voltar para versão anterior
sed -i 's/v1.2.0/v1.1.5/' docker-compose.yml

# Restaurar banco do backup pré-update
docker compose up -d postgres
docker compose exec -T postgres pg_restore ... < backup_pre_update.dump

# Subir resto
docker compose up -d
```

### Atualização de agentes

Agentes podem ser configurados para auto-update, ou atualizados manualmente:

```bash
# Em cada host
sudo sentinelbr-agent update

# Ou via UI: Hosts → Selecionar → "Atualizar agente"
```

---

## Troubleshooting

### Sintoma: "Não consigo acessar a UI"

**Diagnósticos:**

```bash
# 1. Containers rodando?
docker compose ps

# 2. API respondendo?
curl http://localhost:8000/health/live

# 3. Logs do Caddy
docker compose logs caddy

# 4. DNS aponta certo?
dig sentinelbr.suaempresa.com.br

# 5. Firewall
sudo ufw status
```

### Sintoma: "Agente não conecta"

```bash
# No host com agente
sudo systemctl status sentinelbr-agent
sudo journalctl -u sentinelbr-agent -n 100

# Testar conectividade
nc -zv sentinelbr.suaempresa.com.br 9090

# Verificar cert
openssl x509 -in /etc/sentinelbr/agent.crt -noout -text

# Re-enrollment se cert corrompido
sudo sentinelbr-agent enroll --token=NOVO_TOKEN
```

### Sintoma: "PostgreSQL com 100% CPU"

```bash
# Top queries
docker compose exec postgres psql -U sentinelbr -c "
  SELECT query, calls, mean_exec_time, total_exec_time 
  FROM pg_stat_statements 
  ORDER BY total_exec_time DESC LIMIT 10;
"

# Conexões ativas
docker compose exec postgres psql -U sentinelbr -c "
  SELECT count(*) FROM pg_stat_activity;
"

# Provavelmente: PgBouncer não configurado, ou índice faltando
```

### Sintoma: "Loki está lento"

- Cardinalidade muito alta de labels (verificar)
- Storage lento (HDD em vez de SSD para index)
- Retenção muito longa (mover para S3 cold)

### Sintoma: "Disco enchendo"

```bash
# Onde está enchendo?
du -sh /var/lib/docker/volumes/*

# Provavelmente Loki
docker compose exec loki du -sh /loki/*

# Ajustar retenção
# Editar config.yml:
# loki: retention_days: 15  # antes era 30
```

---

## Hardening de segurança

### Checklist de segurança em produção

- [ ] HTTPS obrigatório (HSTS habilitado)
- [ ] 2FA para todos os admins
- [ ] Senhas fortes obrigatórias (mínimo 12 chars)
- [ ] Firewall fechando portas desnecessárias
- [ ] SSH com chave (sem senha)
- [ ] Login root SSH desabilitado
- [ ] Fail2ban ou similar
- [ ] Atualizações de segurança automáticas (`unattended-upgrades`)
- [ ] Backups testados mensalmente
- [ ] Logs centralizados (ironia: SentinelBR monitorando o servidor que roda SentinelBR)
- [ ] Rate limiting em todos endpoints
- [ ] Secrets em Vault ou variáveis de ambiente (nunca em código)
- [ ] Containers rodando com user não-root
- [ ] Network policies restritas (K8s)
- [ ] mTLS funcionando entre componentes
- [ ] CORS configurado com whitelist
- [ ] Headers de segurança (CSP, X-Frame-Options, etc.)
- [ ] Audit log habilitado e protegido contra delete
- [ ] Vulnerability scanning de imagens Docker (Trivy)
- [ ] CodeQL ativo no repo
- [ ] Dependabot ativo
- [ ] SBOM gerado nas releases

### Headers de segurança (Caddy/Nginx)

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; ...
```

### Atualização automática de segurança

```bash
# Ubuntu
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### Revisão periódica de acessos

Mensalmente:
- Listar usuários ativos
- Listar API tokens em uso
- Listar sessões SSH no servidor
- Revogar tudo que não é mais necessário

---

## Checklists

### Pré-instalação

- [ ] Servidor com requisitos mínimos
- [ ] Domínio comprado e DNS configurável
- [ ] Email para Let's Encrypt
- [ ] Telegram bot token (opcional mas recomendado)
- [ ] Plan de backup (onde guardar offsite)

### Durante instalação

- [ ] Hardening básico aplicado (SSH, firewall, usuário não-root)
- [ ] Docker instalado
- [ ] SentinelBR baixado
- [ ] `.env` preenchido com senhas fortes
- [ ] Serviços subidos e healthy
- [ ] Migrations rodadas
- [ ] Senha do admin guardada em local seguro
- [ ] HTTPS funcionando

### Pós-instalação

- [ ] Login funciona
- [ ] 2FA habilitado
- [ ] Primeiro host adicionado e online
- [ ] Primeiro alerta gerado (testar)
- [ ] Notificações chegando (Telegram/email)
- [ ] Backup automático configurado e testado
- [ ] Monitoramento configurado

### Manutenção mensal

- [ ] Backups testados
- [ ] Logs revisados
- [ ] Acessos auditados
- [ ] Atualizações de imagem disponíveis
- [ ] Disco e RAM com folga
- [ ] Métricas dentro do esperado

---

## Por que essa documentação impressiona

- **Cobertura completa**: do dev local ao K8s em produção
- **Pragmática**: comandos reais que funcionam, não pseudocódigo
- **Custo-consciente**: mostra alternativas baratas (R$ 50/mês) e caras
- **Operacional**: backup, restore, troubleshooting, não só install
- **Segurança séria**: hardening como parte do deploy, não afterthought
- **Múltiplos provedores**: AWS, Hetzner, K8s, on-premise

Posts potenciais no LinkedIn:

- "Deploy de plataforma open-source em VPS de R$ 50: o tutorial que faltava"
- "Auto-scaling de workers Celery com KEDA: queue-depth based scaling"
- "Backup 3-2-1 explicado: por que muito backup ainda não é suficiente"
- "mTLS na prática: PKI própria sem Let's Encrypt"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
