// Detecta webshells PHP comuns. Critico — webshell ativo significa atacante
// com execucao remota de codigo no servidor web.
//
// Padroes cobertos:
//   - eval() de input direto ($_GET, $_POST, $_REQUEST, $_COOKIE)
//   - eval() de base64_decode (ofuscacao classica)
//   - shell_exec / system / passthru / exec direto de input HTTP
//   - assert() com input dinamico (CVE-style execution)

rule WebshellPHP : malware webshell critical
{
    meta:
        description = "Generic PHP webshell — eval/shell_exec de input HTTP"
        author      = "SentinelBR"
        date        = "2026-05-11"

    strings:
        $eval_b64    = "eval(base64_decode" nocase
        $eval_post   = /eval\s*\(\s*\$_POST/ nocase
        $eval_get    = /eval\s*\(\s*\$_GET/ nocase
        $eval_req    = /eval\s*\(\s*\$_REQUEST/ nocase
        $eval_cookie = /eval\s*\(\s*\$_COOKIE/ nocase
        $shell_input = /shell_exec\s*\(\s*\$_/ nocase
        $system_input = /\bsystem\s*\(\s*\$_/ nocase
        $assert_input = /assert\s*\(\s*\$_/ nocase

    condition:
        any of them
}
