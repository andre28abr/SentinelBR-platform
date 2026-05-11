// Indicadores de cryptominer (XMRig, ccminer, similar). Pools Monero comuns,
// strings de configuracao, comandos de mineracao.

rule CryptoMinerXMRig : miner high
{
    meta:
        description = "XMRig / Monero miner indicators"
        author      = "SentinelBR"

    strings:
        $stratum  = "stratum+tcp://" nocase
        $stratum2 = "stratum+ssl://" nocase
        $xmrig    = "xmrig" nocase
        $minexmr  = "minexmr.com" nocase
        $monerohash = "monerohash" nocase
        $nanopool = "nanopool.org" nocase

    condition:
        any of them
}

rule CryptoMinerGenericConfig : miner medium
{
    meta:
        description = "Configuracao tipica de miner — donate-level, pools, threads/cpu"

    strings:
        $a = /\"donate-level\"\s*:\s*\d+/ nocase
        $b = /\"url\"\s*:\s*\"stratum/ nocase
        $c = /\"algo\"\s*:\s*\"(rx|cn|argon)/ nocase

    condition:
        2 of them
}
