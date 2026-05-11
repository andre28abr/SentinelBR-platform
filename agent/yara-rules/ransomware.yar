// Indicadores de ransomware — ransom notes tipicas + extensoes/strings comuns
// de families conhecidas (REvil, Conti, LockBit, BlackCat).

rule RansomNoteGeneric : malware ransomware critical
{
    meta:
        description = "Ransom note generico — palavras-chave de extorsao"
        author      = "SentinelBR"

    strings:
        $bitcoin     = "bitcoin" nocase
        $monero      = "monero" nocase
        $decrypt     = /your\s+files?\s+(have|are)\s+(been\s+)?encrypt/ nocase
        $tor_url     = /[a-z0-9]{16,56}\.onion/ nocase
        $contact     = /contact\s+us\s+(at|via)/ nocase
        $deadline    = /(payment|deadline|hours?\s+left)/ nocase

    condition:
        ($decrypt or $tor_url) and 2 of ($bitcoin, $monero, $contact, $deadline)
}

rule RansomwareKnownFamilies : malware ransomware critical
{
    meta:
        description = "Strings caracteristicas de families conhecidas de ransomware"

    strings:
        $revil    = "Sodinokibi" nocase
        $conti    = "CONTI_README" nocase
        $lockbit  = "LockBit_Ransomware" nocase
        $blackcat = "ALPHV-BlackCat" nocase

    condition:
        any of them
}
