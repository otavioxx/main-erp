# MainERP

Sistema de gestão desktop (Windows) para vendas, condicionais, pedidos de compra,
recebimentos, estoque e relatórios/etiquetas em PDF. Feito em Python com PyQt6 e SQLite.

> Versão atual: veja `APP_VERSION` em `mainerp/core/config.py`.

## Requisitos

- Windows 10/11
- Python 3.10 ou superior (recomendado 3.12), com o "py launcher" instalado
- Dependências de execução em `requirements.txt` (PyQt6, reportlab, pytz, psutil, pywin32)
- Desenvolvimento: `requirements-dev.txt` (dependências de execução + Ruff)

## Instalação (uso diário)

1. Dê dois cliques em `distribuicao\instalar.bat`.
2. Abra o **MainERP** pelo atalho criado na Área de Trabalho ou no Menu Iniciar.
3. Na primeira vez, restaure seu backup em *Configurações*.

Detalhes, atualizações e rollback: [`distribuicao/LEIAME.md`](distribuicao/LEIAME.md).
Histórico de versões: [`CHANGELOG.md`](CHANGELOG.md).

## Onde ficam as coisas

| O quê | Onde |
|---|---|
| Código instalado e versões | `%LOCALAPPDATA%\MainERP\sistema\releases\<versão>\` |
| Banco e configurações | `%LOCALAPPDATA%\MainERP\dados\` |
| Backups automáticos e de migração | `%LOCALAPPDATA%\MainERP\dados\backups\` |
| Relatórios | `%LOCALAPPDATA%\MainERP\dados\relatorios\` |
| Logs da aplicação | `%LOCALAPPDATA%\MainERP\dados\logs\sistema.log` (rotativo) |
| Logs do launcher | `%LOCALAPPDATA%\MainERP\sistema\logs\launcher.log` |

Nenhuma atualização altera a pasta `dados\`. Para usar outra pasta de dados, defina a
variável de ambiente `MAINERP_DATA`.

## Desenvolvimento

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt

:: IMPORTANTE: use uma pasta de dados separada, senão o desenvolvimento
:: mexe no mesmo banco que você usa no dia a dia.
set MAINERP_DATA=C:\dev\mainerp-dados

pytest
python main.py
```

Antes de gerar uma release, execute `verificar.bat` na raiz do projeto. O script usa
`.venv` quando disponível e interrompe com código de erro se Ruff ou pytest falhar.

### Estrutura

```
main.py            ponto de entrada compatível com o launcher
mainerp/app.py     inicialização, splash e ciclo principal do app
mainerp/core/      configuração, caminhos, logging e erros
mainerp/data/      conexão SQLite, migrações e modelos
mainerp/domain/    regras de negócio e utilitários
mainerp/ui/        janela principal, telas, diálogos, mixins e tema
mainerp/reports/   geração de PDFs (vendas, pedidos, condicionais, etiquetas)
tests/             testes automatizados
distribuicao/      launcher, instalador e geração de releases
```

### Banco de dados e migrações

O esquema é versionado por `PRAGMA user_version`. Para alterar o banco:

1. crie `_migracao_NNN_descricao` em `mainerp/data/database.py`;
2. registre-a em `Database.MIGRACOES` com o próximo número;
3. mantenha a mudança **aditiva** (nova tabela/coluna), para que uma versão anterior do
   sistema continue funcionando com o banco já migrado.

Antes de qualquer migração pendente é criado um backup em `dados\backups\pre_migracao_*.db`.
O sistema também cria snapshots SQLite automáticos nessa pasta, no máximo uma vez por dia
enquanto estiver aberto, e mantém somente os últimos 30 dias. Se o aplicativo ficar fechado
por mais de um dia, o backup vencido é feito na próxima inicialização; não há execução
enquanto o aplicativo e o Windows estiverem fechados. A opção de gerar um backup manual em
outra pasta (por exemplo, uma pasta sincronizada ou unidade externa) continua disponível no
fechamento do sistema.

## Publicar uma nova versão

1. Aumente `APP_VERSION` em `mainerp/core/config.py`.
2. Atualize também a versão e a data exibidas na linha 54 de
   `mainerp/ui/views/main_window.py` (barra de status).
3. Configure no repositório, em **Settings > Secrets and variables > Actions**, o secret
   `MAINERP_ED25519_PRIVATE_KEY` com o conteúdo PEM da chave privada. Gere essa chave uma
   única vez com `python distribuicao\gerar_chave_assinatura.py`; ela fica fora do repositório
   em `%LOCALAPPDATA%\MainERP\signing\ed25519-private.pem`. Nunca a versione nem a envie por
   chat. O launcher contém somente a chave pública.
4. Execute `verificar.bat` localmente. Atualize e envie o commit para `main`.
5. Crie e envie uma tag anotada que corresponda exatamente a `APP_VERSION`, por exemplo:
   `git tag -a v0.10 -m "MainERP 0.10"` e `git push origin v0.10`.
6. O GitHub Actions valida a tag, executa Ruff e pytest, gera o ZIP e o manifesto, assina o
   ZIP com Ed25519 e publica os três assets (`.zip`, `.zip.sig` e `version.json`) como latest.
   Não recicle tags já publicadas.
7. Usuários com o launcher configurado para o manifesto da GitHub Release recebem a versão
   ao fechar e abrir o MainERP pelo atalho.

Para gerar e inspecionar o pacote localmente: `python distribuicao/criar_release.py`
(cria `dist/MainERP-<versão>.zip` e `dist/version.json`; isso não publica a release).

## Convenções

- Mensagens de commit no formato `tipo: descrição` (`feat`, `fix`, `refactor`, `chore`, `docs`).
- Dados do usuário nunca entram no Git (`*.db`, `config.json`, `backups/`, `relatorios/`).
- Logs da aplicação vão para `dados\logs\sistema.log` (arquivo de 5 MB e até 5 cópias).
- O launcher mantém seu próprio log em `sistema\logs\launcher.log`.

## Roadmap

Veja [`ROADMAP.md`](ROADMAP.md).
