# PLUMA

Sistema de gestão desktop para Windows, voltado a pequenas empresas: vendas,
condicionais, pedidos de compra, recebimentos, estoque e relatórios/etiquetas em PDF.

Feito em Python com PyQt6 e SQLite. Distribuído como instalador autocontido com
atualização online verificada, assinatura Ed25519 dos pacotes e rollback automático
em caso de falha de inicialização.

> Versão atual: veja `APP_VERSION` em `mainerp/core/config.py`.

O nome do produto é **PLUMA**. Pastas, variáveis de ambiente e pacotes mantêm o
identificador técnico `MainERP` (por exemplo, `%LOCALAPPDATA%\MainERP` e `MAINERP_DATA`).

## O que o PLUMA faz

- **Vendas:** registro com pagamento à vista ou parcelado e emissão de PDF.
- **Condicionais:** controle de mercadorias em condicional e fechamento.
- **Pedidos de compra:** pedidos a fornecedores com recebimento no estoque.
- **Recebimentos:** controle de parcelas, saldo em aberto e baixa.
- **Estoque:** cadastro e movimentação por produto.
- **Relatórios e etiquetas:** geração de PDFs de vendas, pedidos, condicionais e etiquetas.
- **Backup:** automático e manual, com verificação de integridade e restauração testável.
- **Atualização online:** o launcher consulta releases públicas, verifica assinatura e
  SHA-256 antes de instalar, e mantém as versões anteriores para rollback.
- **Temas claro e escuro**, com preferência persistida.

O PLUMA é pensado para operação offline em um único PC, com banco em SQLite (WAL).
Cada release preserva a pasta `dados\`; a atualização é aplicada apenas ao código.

## Requisitos

- Windows 10/11
- Python 3.10 ou superior (recomendado 3.12), com o "py launcher" instalado
- Dependências de execução em `requirements.txt` (incluindo PyQt6, reportlab e cryptography)
- Desenvolvimento: `requirements-dev.txt` (dependências de execução, pytest e Ruff)
- Acesso à internet para instalar dependências e receber atualizações online

## Instalação (uso diário)

1. Baixe o instalador `.pyz` da release e execute `py -3 MainERP-Instalador-<versão>.pyz`
   no PowerShell.
2. Abra o **PLUMA** pelo atalho da Área de Trabalho ou do Menu Iniciar.
3. Se já tiver dados, restaure seu backup em *Configurações*. Uma instalação nova sem
   dados anteriores começa com o banco vazio.

Instalação pelo ZIP completo, atalhos, atualizações, rollback e diagnóstico:
[`docs/instalacao_e_atualizacao.md`](docs/instalacao_e_atualizacao.md).

Após uma atualização pelo launcher, as novidades são apresentadas uma vez na primeira
abertura; o histórico completo continua disponível em **Sobre** e em
[`CHANGELOG.md`](CHANGELOG.md). O tema claro ou escuro é escolhido em
**Configurações > Aparência** (veja [identidade visual](docs/identidade_visual.md)).

## Onde ficam as coisas

| O quê | Onde |
|---|---|
| Código instalado e versões | `%LOCALAPPDATA%\MainERP\sistema\releases\<versão>\` |
| Banco de dados padrão | `%LOCALAPPDATA%\MainERP\dados\erp.db` |
| Configurações | `%LOCALAPPDATA%\MainERP\dados\` |
| Backups automáticos, anteriores a migrações e restaurações | `%LOCALAPPDATA%\MainERP\dados\backups\` |
| Backups manuais | Pasta escolhida no diálogo; por padrão, Área de Trabalho |
| Relatórios | `%LOCALAPPDATA%\MainERP\dados\relatorios\` |
| Logs da aplicação | `%LOCALAPPDATA%\MainERP\dados\logs\sistema.log` (rotativo) |
| Logs do launcher | `%LOCALAPPDATA%\MainERP\sistema\logs\launcher.log` |

As atualizações de código preservam a pasta `dados\`; ao abrir uma nova versão, migrações
pendentes podem alterar o esquema do banco. Para usar outra pasta de dados, defina a
variável de ambiente `MAINERP_DATA`.

## Estrutura do projeto
