/*
 * dropper_bash.yar — padrões de droppers / loaders shell.
 *
 * Droppers sao scripts pequenos cuja unica funcao eh BAIXAR um payload
 * mais elaborado e executar. Indicador classico:
 *   - curl/wget direto piped pra sh/bash (nao revisa antes de executar)
 *   - download pra /tmp + chmod +x + exec
 *   - base64 decode + eval
 *
 * Severity: high — droppers raramente sao falsos positivos em /tmp /var/www.
 */

rule DropperBashCurlPipe {
    meta:
        description = "Bash dropper via curl/wget piped pra shell"
        severity = "high"
        family = "Dropper"
        mitre = "T1059.004"  // Command and Scripting Interpreter: Unix Shell
        author = "SentinelBR"

    strings:
        $curl_pipe_sh = /curl\s+[^|]+\|\s*(sh|bash)/ nocase
        $wget_pipe_sh = /wget\s+[^|]+\|\s*(sh|bash)/ nocase
        $curl_o_chmod = /curl\s+-[oO]\s+\/tmp\/\S+.{0,200}chmod\s+\+x/ nocase

    condition:
        any of them
}

rule DropperBase64Eval {
    meta:
        description = "Bash com base64 decode + eval (obfuscation)"
        severity = "high"
        family = "Dropper"
        mitre = "T1059.004"
        author = "SentinelBR"

    strings:
        // echo "..." | base64 -d | bash
        $base64_pipe_bash = /base64\s+(-d|--decode)\s*\|\s*(sh|bash)/ nocase
        // eval "$(echo ... | base64 -d)"
        $eval_base64 = /eval\s+["']?\$\(.{0,200}base64\s+(-d|--decode)/ nocase

    condition:
        any of them
}
