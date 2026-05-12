/*
 * persistence.yar — padrões de persistencia em Linux.
 *
 * Atacantes que ja invadiram tentam GARANTIR que reboot nao limpa o
 * acesso. Mecanismos classicos:
 *   - cron jobs em /etc/cron.d/, /var/spool/cron/, ou ~/.crontab
 *   - systemd unit files maliciosos em /etc/systemd/system/
 *   - .bashrc / .profile com payload no shell de algum user
 *   - LD_PRELOAD em /etc/ld.so.preload (rootkit)
 *
 * Severity: high — persistencia geralmente significa breach ja aconteceu.
 */

rule PersistenceCronBackdoor {
    meta:
        description = "Cron job com curl/wget pra IP/dominio (backdoor periodica)"
        severity = "high"
        family = "Persistence"
        mitre = "T1053.003"  // Scheduled Task: Cron
        author = "SentinelBR"

    strings:
        // 5 campos cron (*, */N, N-M, N) + curl/wget na mesma linha. Aceita
        // variacoes: "* * * * *", "*/5 * * * *", "0 */6 * * *", etc.
        $cron_curl = /[\*0-9\/\-,]+\s+[\*0-9\/\-,]+\s+[\*0-9\/\-,]+\s+[\*0-9\/\-,]+\s+[\*0-9\/\-,]+.{0,200}\b(curl|wget)\s+/
        // ex: @reboot bash -c "..." OU @reboot root /bin/bash -c "..."
        $reboot_bash = /@reboot\s+\S*\s*(\/[\w\/]+\/)?(sh|bash)\s+-c/

    condition:
        any of them
}

rule PersistenceLdPreload {
    meta:
        description = "ld.so.preload com .so suspeito (rootkit clássico)"
        severity = "critical"
        family = "Persistence"
        mitre = "T1574.006"  // Hijack Execution Flow: LD_PRELOAD
        author = "SentinelBR"

    strings:
        $ld_so_preload_path = "/etc/ld.so.preload"
        $suspicious_so = /\.\w+\.so/  // rootkits usam .libxxx.so (hidden)

    condition:
        // Casa se aparece /etc/ld.so.preload + arquivo .so com prefixo .
        $ld_so_preload_path and $suspicious_so
}

rule PersistenceSystemdUnit {
    meta:
        description = "Systemd unit com ExecStart suspeito (download remoto)"
        severity = "high"
        family = "Persistence"
        mitre = "T1543.002"  // Create or Modify System Process: systemd
        author = "SentinelBR"

    strings:
        $unit_marker = "[Service]" nocase
        $exec_curl = /ExecStart=.{0,200}\b(curl|wget)\s+(http|ftp)/ nocase
        $exec_b64 = /ExecStart=.{0,200}base64\s+(-d|--decode)/ nocase

    condition:
        $unit_marker and any of ($exec_curl, $exec_b64)
}
