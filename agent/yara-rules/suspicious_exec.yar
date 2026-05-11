// Indicadores genericos de binarios suspeitos / suspeitos em diretorios incomuns
// (ex: /tmp, /var/tmp, /dev/shm — locais classicos de drop de payload).

rule SuspiciousExecutable : suspicious medium
{
    meta:
        description = "ELF/Mach-O em diretorios temporarios eh suspeito"
        author      = "SentinelBR"

    strings:
        $elf_magic  = { 7F 45 4C 46 }                   // \x7fELF
        $macho_64   = { CF FA ED FE }                   // Mach-O 64-bit LE

    condition:
        any of them
}
