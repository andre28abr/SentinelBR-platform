/*
 * reverse_shell.yar — padrões de reverse shells em varios runtimes.
 *
 * Reverse shell = atacante "vira o cliente" — programa na vitima conecta
 * ao atacante (em vez do contrario) pra escapar de firewalls inbound.
 * Padroes comuns: bash com /dev/tcp, python socket, perl IO::Socket.
 *
 * Severity: critical — quase nunca legitimos. Aparecem em scripts maliciosos
 * pos-RCE.
 */

rule ReverseShellBashTCP {
    meta:
        description = "Reverse shell via /dev/tcp do bash"
        severity = "critical"
        family = "ReverseShell"
        mitre = "T1059.004"
        author = "SentinelBR"

    strings:
        // bash -i >& /dev/tcp/IP/PORT 0>&1
        $bash_tcp = /bash\s+-i\s*>\&?\s*\/dev\/tcp\/[\d\.]+\/\d+\s+0>\&1/ nocase
        // /dev/tcp/HOST/PORT em qualquer ordem
        $dev_tcp_redir = /\/dev\/tcp\/[\d\.a-z\-]+\/\d{1,5}/ nocase

    condition:
        any of them
}

rule ReverseShellPython {
    meta:
        description = "Reverse shell em Python (socket + subprocess)"
        severity = "critical"
        family = "ReverseShell"
        mitre = "T1059.006"  // Python
        author = "SentinelBR"

    strings:
        // import socket; ... s.connect; subprocess.call(["/bin/sh"...])
        $py_socket = "import socket" nocase
        $py_connect = ".connect((" nocase
        $py_subproc = /subprocess\.(call|Popen|run)\(\s*\[?\s*["']?\/bin\/(sh|bash)/ nocase
        $py_dup2 = /os\.dup2\(\s*s\.fileno\(\)/ nocase

    condition:
        ($py_socket and $py_connect and ($py_subproc or $py_dup2))
}

rule ReverseShellNetcat {
    meta:
        description = "nc/ncat com -e (executa shell ao conectar)"
        severity = "critical"
        family = "ReverseShell"
        mitre = "T1059.004"
        author = "SentinelBR"

    strings:
        $nc_e = /\b(nc|ncat)\s+(-[a-z]*e[a-z]*)\s+\S+\s+\d{1,5}/ nocase
        // mkfifo trick
        $mkfifo_tcp = /mkfifo\s+\/tmp\/\S+.{0,200}\bnc\b/

    condition:
        any of them
}
