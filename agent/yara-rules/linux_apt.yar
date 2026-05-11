// Tecnicas comuns de APT em Linux: persistencia via cron, download-then-execute,
// reverse shells em scripts.

rule SuspiciousCurlBash : malware apt high
{
    meta:
        description = "curl|bash / wget|sh — padrao classico de download-then-execute"
        author      = "SentinelBR"

    strings:
        $curl_pipe  = /curl\s+(-[A-Za-z]+\s+)*\S+\s*\|\s*(bash|sh|python)/ nocase
        $wget_pipe  = /wget\s+(-[A-Za-z]+\s+)*\S+\s*-O\s*-\s*\|\s*(bash|sh|python)/ nocase
        $wget_short = /wget\s+\S+\s*\|\s*(bash|sh|python)/ nocase

    condition:
        any of them
}

rule ReverseShellPattern : malware apt high
{
    meta:
        description = "Reverse shell — bash /dev/tcp ou nc -e"

    strings:
        $bash_tcp   = "/dev/tcp/" nocase
        $bash_udp   = "/dev/udp/" nocase
        $nc_e       = /\bnc\s+-[A-Za-z]*e\b/ nocase
        $bash_iZ    = /bash\s+-i\s*>\s*&\s*\/dev\/tcp/ nocase

    condition:
        any of them
}
