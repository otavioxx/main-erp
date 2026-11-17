# Instalador do PLUMA

Tudo o que o instalador executa. Esta pasta acompanha o download de instalação (o `.pyz`
da release) e o ZIP de código-fonte. As ferramentas de publicação estão em
[`../publicacao`](../publicacao/README.md).

Procedimentos completos: [instalação e atualização](../docs/instalacao_e_atualizacao.md) e
[publicar uma release](../docs/publicar_release.md).

| Arquivo | Função |
|---|---|
| `launcher.pyw` | Ponto de entrada fixo instalado em `sistema\`. Aplica atualizações, escolhe a release, abre o sistema e faz o rollback de inicialização. Usa só a biblioteca padrão e exibe a janela de atualização (Tkinter). |
| `instalar.py`, `instalar.bat` | Instalador. Cria `sistema\` e `dados\`, copia o launcher e cria os atalhos; pode ser executado de novo sem apagar dados. `--sem-atalhos` pula os atalhos e `--destino` altera a pasta do sistema. |
| `criar_atalhos.ps1` | Cria os atalhos do Windows; é chamado por `instalar.py`. |
| `criar_release.py` | Gera `dist/MainERP-<versão>.zip` e `dist/version.json`. `--verificar-tag v<versão>` confere a tag contra `APP_VERSION`. Fica aqui porque o próprio instalador o usa para empacotar o código. |
