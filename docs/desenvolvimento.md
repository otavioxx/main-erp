# Desenvolvimento do PLUMA

Guia para preparar o ambiente, verificar o código e seguir as convenções do projeto. Para
publicar uma versão, veja [publicar_release.md](publicar_release.md).

## Ambiente

No Prompt de Comando (`cmd`):

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

No PowerShell, ative o ambiente com `.\.venv\Scripts\Activate.ps1` e defina a pasta de dados
com `$env:MAINERP_DATA = 'C:\dev\mainerp-dados'`.

A execução direta de `main.py` não consulta atualizações: essa verificação é feita pelo
launcher do atalho instalado.

As dependências de execução ficam em `requirements.txt` e as de desenvolvimento (execução,
pytest e Ruff) em `requirements-dev.txt`.

## Verificação

Antes de gerar uma release, execute `verificar.bat` na raiz do projeto. O script usa `.venv`
quando disponível e interrompe com código de erro se Ruff ou pytest falhar.

Os comandos individuais são:

```powershell
python -m ruff check .
python -m ruff format .
python -m pytest
```

Testes sempre com dados e instalações isolados, nunca com dados de produção.

## Criar uma migração do banco

O esquema é versionado por `PRAGMA user_version`. Para alterar o banco:

1. crie `_migracao_NNN_descricao` em `mainerp/data/database.py`;
2. registre-a em `Database.MIGRACOES` com o próximo número;
3. mantenha a mudança **aditiva** (nova tabela ou coluna), para que uma versão anterior do
   sistema continue funcionando com o banco já migrado.

Teste migrações em bancos isolados ou temporários. O funcionamento dos backups criados antes da
migração está em [banco_e_backups.md](banco_e_backups.md).

## Convenções

- Mensagens de commit no formato `tipo: descrição` (`feat`, `fix`, `refactor`, `chore`,
  `docs`).
- Dados do usuário nunca entram no Git (`*.db`, `config.json`, `backups/`, `relatorios/`).
- Os logs da aplicação vão para `dados\logs\sistema.log` (arquivo de 5 MB e até 5 cópias).
- O launcher mantém seu próprio log em `sistema\logs\launcher.log`.
