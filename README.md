# MainERP

Sistema de gestão desktop (Windows) para vendas, condicionais, pedidos de compra,
recebimentos, estoque e relatórios/etiquetas em PDF. Feito em Python com PyQt6 e SQLite.

> Versão atual: veja `APP_VERSION` em `config.py`.

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

## Onde ficam as coisas

| O quê | Onde |
|---|---|
| Código instalado e versões | `%LOCALAPPDATA%\MainERP\sistema\releases\<versão>\` |
| Banco, config, backups e relatórios | `%LOCALAPPDATA%\MainERP\dados\` |
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

### Estrutura

```
main.py            ponto de entrada (splash, instância única, tema, janela principal)
paths.py           caminhos: código (CODE_DIR) x dados (DATA_DIR)
config.py          configurações (config.json) e APP_VERSION
app_logging.py     logging rotativo em dados/logs/sistema.log
database.py        conexão SQLite e migrações numeradas
styles.py          tema escuro
models/            entidades e acesso a dados (cliente, produto, venda, ...)
views/             telas principais (listagens, janela principal)
dialogs/           janelas de cadastro, seleção, backup e restauração
imprecoes/         geração de PDFs (vendas, pedidos, condicionais, etiquetas)
utils/             funções de apoio (cálculos, validações, exportação)
mixins/            comportamentos reutilizáveis de janelas
distribuicao/      launcher, instalador e geração de releases
```

### Banco de dados e migrações

O esquema é versionado por `PRAGMA user_version`. Para alterar o banco:

1. crie `_migracao_NNN_descricao` em `database.py`;
2. registre-a em `Database.MIGRACOES` com o próximo número;
3. mantenha a mudança **aditiva** (nova tabela/coluna), para que uma versão anterior do
   sistema continue funcionando com o banco já migrado.

Antes de qualquer migração pendente é criado um backup em `dados\backups\pre_migracao_*.db`.

## Publicar uma nova versão

1. Aumente `APP_VERSION` em `config.py`.
2. Execute `distribuicao\publicar_atualizacao.bat`.
3. Abra o MainERP: a versão nova é instalada e aberta automaticamente.

Para gerar apenas o pacote: `python distribuicao/criar_release.py` (cria `dist/MainERP-<versão>.zip`
e `dist/version.json`).

## Convenções

- Mensagens de commit no formato `tipo: descrição` (`feat`, `fix`, `refactor`, `chore`, `docs`).
- Dados do usuário nunca entram no Git (`*.db`, `config.json`, `backups/`, `relatorios/`).
- Logs da aplicação vão para `dados\logs\sistema.log` (arquivo de 5 MB e até 5 cópias).
- O launcher mantém seu próprio log em `sistema\logs\launcher.log`.

## Roadmap

Veja [`ROADMAP.md`](ROADMAP.md).
