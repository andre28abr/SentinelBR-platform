"""Roda o gRPC server (mTLS) em paralelo ao FastAPI.

Uso:
    uv run python -m app.grpc_server.server

Listen padrao: [::]:9443. Override com SENTINELBR_GRPC_LISTEN_ADDR.
"""

from __future__ import annotations

import asyncio
import logging
import signal

import grpc

from app.config import get_settings
from app.grpc_server.agent_servicer import AgentServicer
from app.grpc_server.pb import agent_pb2_grpc
from app.services.ca import get_ca_cert_pem, load_or_create_server_cert

log = logging.getLogger(__name__)


def _server_credentials() -> grpc.ServerCredentials:
    bundle = load_or_create_server_cert()
    ca_pem = get_ca_cert_pem()
    return grpc.ssl_server_credentials(
        private_key_certificate_chain_pairs=[(bundle.key_pem, bundle.cert_pem)],
        root_certificates=ca_pem,
        require_client_auth=True,
    )


async def serve() -> None:
    settings = get_settings()
    # MaxRecv 16MB (default 4MB) — InventoryReport com 5k+ pacotes (Fedora
    # full) facilmente passa de 4MB. MaxSend 4MB (default) chega.
    # Anti-DoS: agente comprometido nao pode enviar payload arbitrariamente
    # grande; 16MB eh teto razoavel pra inventory + safety margin.
    server = grpc.aio.server(options=[
        ("grpc.max_receive_message_length", 16 * 1024 * 1024),
        ("grpc.max_send_message_length", 4 * 1024 * 1024),
    ])
    agent_pb2_grpc.add_AgentServiceServicer_to_server(AgentServicer(), server)
    server.add_secure_port(settings.grpc_listen_addr, _server_credentials())
    await server.start()
    log.info("gRPC mTLS server escutando em %s", settings.grpc_listen_addr)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    await stop.wait()
    log.info("shutdown solicitado, draining...")
    await server.stop(grace=5)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(serve())


if __name__ == "__main__":
    main()
