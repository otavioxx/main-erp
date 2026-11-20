# PLUMA

Sistema de gestão desktop para pequenas empresas, com vendas, condicionais, pedidos de
compra, recebimentos, estoque e relatórios em PDF. Desenvolvido em Python, PyQt6 e SQLite
para Windows 10 e 11.

O nome do produto é **PLUMA**. `MainERP` permanece como identificador técnico em caminhos,
variáveis de ambiente e nomes de pacotes, como `%LOCALAPPDATA%\MainERP` e `MAINERP_DATA`.
A versão publicada é definida por `APP_VERSION` em `mainerp/core/config.py`.

## Recursos

- Registro de vendas à vista ou parceladas, recebimentos e movimentações de estoque.
- Controle de condicionais e pedidos de compra.
- Relatórios e etiquetas em PDF.
- Backups automáticos e manuais, com validação e fluxo de restauração.
- Temas claro e escuro, com preferência persistida.
- Atualizações online por launcher, com verificação de assinatura Ed25519 e SHA-256 e
  rollback automático quando uma nova versão falha ao iniciar.

O PLUMA foi projetado para uso offline em um único computador. O banco SQLite usa WAL.
Código e dados ficam separados; atualizações preservam a pasta de dados, embora uma nova
versão possa executar migrações do banco.

## Instalação

Requisitos: Windows 10/11, Python 3.10 ou superior (recomendado 3.12) e o Python Launcher
(`py`). O acesso à internet é necessário para instalar dependências e receber atualizações
online. As dependências de execução estão em `requirements.txt`; as de desenvolvimento,
em `requirements-dev.txt`. Baixe o instalador `.pyz` da release e execute no PowerShell:

```powershell
py -3 MainERP-Instalador-<versão>.pyz
```

Depois, abra o PLUMA pelo atalho criado. Em uma instalação nova, o banco começa vazio; para
recuperar dados, use a restauração em **Configurações**. Consulte o [guia de instalação,
atualização e rollback](docs/instalacao_e_atualizacao.md) antes de migrar uma instalação
existente.

## Dados do usuário

| Conteúdo | Local padrão |
|---|---|
| Banco de dados | `%LOCALAPPDATA%\MainERP\dados\erp.db` |
| Configurações e backups | `%LOCALAPPDATA%\MainERP\dados\` |
| Relatórios e logs do aplicativo | `%LOCALAPPDATA%\MainERP\dados\` |
| Launcher, runtimes e releases | `%LOCALAPPDATA%\MainERP\sistema\` |
| Log do launcher | `%LOCALAPPDATA%\MainERP\sistema\logs\launcher.log` |

As atualizações não removem a pasta `dados\`. `MAINERP_DATA` permite indicar outro local
para os dados. Backups automáticos ficam no mesmo computador; mantenha cópias manuais
externas e teste a restauração periodicamente. Veja [backup e recuperação](docs/backup_recuperacao.md).

## Documentação

Consulte o [índice da documentação](docs/README.md) para guias de uso, desenvolvimento,
backups, identidade visual e publicação. O histórico de mudanças está no
[CHANGELOG](CHANGELOG.md); após uma atualização, as novidades também são apresentadas no
aplicativo.

