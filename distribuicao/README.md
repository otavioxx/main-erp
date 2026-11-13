# Distribuição do PLUMA

Scripts de instalação, atualização e geração de releases. O sistema é distribuído sem
PyInstaller. Os procedimentos completos estão em
[instalação e atualização](../docs/instalacao_e_atualizacao.md) e em
[publicar uma release](../docs/publicar_release.md).

| Arquivo | Função |
|---|---|
| `launcher.pyw` | Ponto de entrada fixo instalado em `sistema\`. Aplica atualizações, escolhe a release, abre o sistema e faz o rollback de inicialização. Usa só a biblioteca padrão e exibe a janela de atualização (Tkinter). |
| `instalar.py`, `instalar.bat` | Instalador. Cria `sistema\` e `dados\`, copia o launcher e cria os atalhos; pode ser executado de novo sem apagar dados. `--sem-atalhos` pula os atalhos e `--destino` altera a pasta do sistema. |
| `criar_atalhos.ps1` | Cria os atalhos do Windows; é chamado por `instalar.py`. |
| `criar_release.py` | Gera `dist/MainERP-<versão>.zip` e `dist/version.json`. `--verificar-tag v<versão>` confere a tag contra `APP_VERSION`. |
| `publicar_atualizacao.bat` | Gera o ZIP da versão configurada e o coloca em `sistema\atualizacoes\` do usuário atual. |
| `gerar_chave_assinatura.py` | Gera o par de chaves Ed25519 de assinatura de releases (uso único). |
| `assinar_release.py` | Assina os pacotes de release com Ed25519. |
| `criar_instalador.py` | Gera o instalador autocontido `.pyz`. |
| `instalador_bootstrap.py` | Ponto de entrada do instalador `.pyz`. |
