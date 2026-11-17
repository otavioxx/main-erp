# Publicação do PLUMA

Ferramentas de quem publica releases. Esta pasta não acompanha o download de instalação: o
instalador (`.pyz`) e o ZIP de código-fonte não a incluem. O que o instalador executa está em
[`../instalador`](../instalador/README.md).

Procedimento completo: [publicar uma release](../docs/publicar_release.md).

| Arquivo | Função |
|---|---|
| `criar_instalador.py` | Gera o instalador autocontido `MainERP-Instalador-<versão>.pyz`, com os arquivos de `instalador/` e o código da release. Usa `criar_release.py` de `instalador/`. |
| `instalador_bootstrap.py` | Torna-se o `__main__.py` do `.pyz`: extrai o pacote em uma pasta temporária e executa `instalador/instalar.py`. |
| `assinar_release.py` | Assina os pacotes de release com Ed25519 (chave no secret `MAINERP_ED25519_PRIVATE_KEY`). |
| `gerar_chave_assinatura.py` | Gera o par de chaves Ed25519 de assinatura de releases (uso único). |
| `publicar_atualizacao.bat` | Gera o ZIP da versão configurada e o coloca em `sistema\atualizacoes\` do usuário atual. |
