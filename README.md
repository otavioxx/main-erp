# MainERP

Sistema de gestão desktop (Windows) para vendas, condicionais, pedidos de compra,
recebimentos, estoque e relatórios/etiquetas em PDF. Feito em Python com PyQt6 e SQLite.

> Versão atual: veja `APP_VERSION` em `mainerp/core/config.py`.

## Requisitos

- Windows 10/11
- Python 3.10 ou superior (recomendado 3.12), com o "py launcher" instalado
- Dependências de execução em `requirements.txt` (incluindo PyQt6, reportlab e cryptography)
- Desenvolvimento: `requirements-dev.txt` (dependências de execução, pytest e Ruff)
- Acesso à internet para instalar dependências e receber atualizações online

## Instalação (uso diário)

1. Baixe o instalador `.pyz` da release e execute `py -3 MainERP-Instalador-<versão>.pyz`
   no PowerShell. O instalador remove sua pasta temporária ao terminar normalmente;
   o arquivo baixado permanece e pode ser excluído depois.
   Na instalação pelo ZIP completo, arquivos de desenvolvimento conhecidos são
   removidos da pasta extraída após o sucesso, exceto em checkouts Git.
2. Abra o **MainERP** pelo atalho da Área de Trabalho ou do Menu Iniciar. Também há
   um atalho de reserva em `%LOCALAPPDATA%\MainERP\sistema\MainERP.lnk`.
3. Se já tiver dados, restaure seu backup em *Configurações*. Uma instalação nova sem
   dados anteriores começa com o banco vazio.

Detalhes, atualizações e rollback: [`distribuicao/LEIAME.md`](distribuicao/LEIAME.md).
Histórico de versões: [`CHANGELOG.md`](CHANGELOG.md).

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

Os comandos acima usam o Prompt de Comando (`cmd`). No PowerShell, ative com
`.\.venv\Scripts\Activate.ps1` e defina a pasta com
`$env:MAINERP_DATA = 'C:\dev\mainerp-dados'`. A execução direta de `main.py` não
consulta atualizações: essa verificação é feita pelo launcher do atalho instalado.

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

Antes de migrar um banco existente com tabelas, é criado um backup em
`dados\backups\pre_migracao_*.db`. O sistema também verifica backups automáticos ao abrir
e a cada hora enquanto estiver aberto: se não houver um arquivo recente ou o último tiver
ao menos 24 horas, tenta criar um snapshot SQLite. Após uma criação bem-sucedida, aplica
retenção de 30 dias aos backups automáticos. Se o aplicativo ficar fechado por mais de
um dia, a tentativa ocorre na próxima inicialização; não há execução enquanto estiver
fechado. A barra de status mostra a idade
do arquivo automático mais recente e o resultado da operação nesta sessão, inclusive
falhas de agendamento ou retenção. Ao reiniciar, um arquivo existente é informado sem
afirmar que foi verificado novamente; essa informação não substitui testes de restauração.
Um backup manual pode ser iniciado em **Configurações > Criar Backup**. Ao fechar, o
sistema solicita um backup manual se não houver data registrada ou se ela tiver pelo menos
um dia; o backup automático não substitui essa exigência. O diálogo usa a última pasta
válida ou a Área de Trabalho e permite escolher outra. Antes de dispensar um backup
recente, o sistema verifica se o ZIP está acessível e íntegro e confere o hash quando
disponível; se a verificação falhar, avisa e solicita um novo backup. Isso não substitui
um teste de restauração.

O ZIP manual contém um snapshot SQLite verificado, inclusive dados confirmados em WAL,
um `README.txt` e, se presente no diretório de trabalho, `config.ini`. Não é uma cópia
completa de `dados\`: a restauração aplica o banco, não configurações ou relatórios.
Os backups automáticos ficam no mesmo computador que o banco; mantenha cópias manuais
externas, com acesso protegido, e teste periodicamente sua recuperação em uma instalação
isolada. Os backups não são criptografados pelo aplicativo.
Consulte o [guia de cópia externa e restauração isolada](docs/backup_recuperacao.md)
para uma rotina prática e os limites de cada tipo de backup.
Uma restauração é preparada enquanto o sistema está aberto e aplicada na próxima
inicialização, antes de abrir o banco; um snapshot anterior é mantido em `dados\backups`.
Durante a aplicação, uma trava SQLite exclusiva impede gravações de outros processos
até a validação; feche os demais programas que usam o banco antes de restaurar.
Se a trava não puder ser adquirida, o sistema bloqueia a abertura e preserva a
restauração pendente. A publicação da pendência exige suporte a hard links no volume
de dados; se não houver suporte, a preparação falha sem substituir uma pendência.
O launcher precisa ser atualizado pelo instalador para usar esse fluxo. Em execução direta
de `main.py`, abra o sistema novamente após solicitar a restauração. Se ocorrer falha na
restauração, o sistema não abre e o estado do banco pode ter sido alterado; não se presume
que houve reversão. Preserve o banco, o backup anterior e os arquivos pendentes e procure
suporte antes de tentar novamente. A validação verifica integridade, tabelas, nomes de
colunas, valores inteiros em centavos e referências estrangeiras declaradas após migrar
uma cópia temporária.
Backups com referências órfãs ou valores inválidos em centavos são recusados; preserve o
original para diagnóstico. A validação não garante a correção de todos os dados, tipos,
restrições ou regras de negócio, nem detecta relacionamentos não declarados no esquema.

## Publicar uma nova versão

1. Aumente `APP_VERSION` em `mainerp/core/config.py` usando `MAJOR.MINOR.PATCH`
   (por exemplo, `0.10.1`) e registre a versão, data e alterações em `CHANGELOG.md`.
   A barra de status usa `APP_VERSION` automaticamente.
2. Use MAJOR para mudanças incompatíveis, MINOR para funcionalidades compatíveis e PATCH
   para correções compatíveis; enquanto MAJOR for zero, a API ainda está em desenvolvimento.
   Reinicie os componentes inferiores ao aumentar MAJOR ou MINOR. Releases publicadas usam
   apenas números sem zeros à esquerda, sem sufixos de pré-release ou metadados.
3. Configure no repositório, em **Settings > Secrets and variables > Actions**, o secret
   `MAINERP_ED25519_PRIVATE_KEY` com o conteúdo PEM da chave privada. Gere essa chave uma
   única vez com `python distribuicao\gerar_chave_assinatura.py`; ela fica fora do repositório
   em `%LOCALAPPDATA%\MainERP\signing\ed25519-private.pem`. Nunca a versione nem a envie por
   chat. O launcher contém somente a chave pública.
4. Execute `verificar.bat` localmente. Atualize e envie o commit para `main`.
5. Crie e envie uma tag anotada que corresponda exatamente a `APP_VERSION`, por exemplo:
   `git tag -a v0.10.1 -m "MainERP 0.10.1"` e `git push origin v0.10.1`.
6. O GitHub Actions valida a tag, executa Ruff e pytest, gera o ZIP de atualização, o
   instalador `.pyz` e o manifesto, assina ambos os pacotes com Ed25519 e publica esses
   arquivos, as assinaturas, `instalador.sha256` e `version.json` como latest. Não recicle
   tags já publicadas.
7. Ao abrir pelo atalho, o launcher configurado consulta o manifesto e tenta instalar
   versões superiores após validar assinatura, SHA256 e versão. Sem rede, com atualização
   desativada ou se ela falhar, o sistema permanece na versão instalada; consulte
   `sistema\logs\launcher.log` em caso de dúvida.

O launcher atualizado instala cada atualização em um runtime próprio, preservando as
dependências das versões anteriores para rollback. Isso requer espaço em disco e acesso
às dependências na instalação. Instalações existentes precisam primeiro atualizar o
launcher pelo instalador; uma atualização de código não substitui o launcher fixo.

Para gerar e inspecionar o pacote localmente: `python distribuicao/criar_release.py`
(cria `dist/MainERP-<versão>.zip` e `dist/version.json`; isso não publica a release).
O gerador inclui os arquivos de runtime da raiz e os arquivos Python dos pacotes listados
em `PACOTES`; ao criar um pacote novo, atualize essa lista e execute os testes. Não inclua
arquivos locais ou dados pessoais entre os arquivos Python desses pacotes.

## Convenções

- Mensagens de commit no formato `tipo: descrição` (`feat`, `fix`, `refactor`, `chore`, `docs`).
- Dados do usuário nunca entram no Git (`*.db`, `config.json`, `backups/`, `relatorios/`).
- Logs da aplicação vão para `dados\logs\sistema.log` (arquivo de 5 MB e até 5 cópias).
- O launcher mantém seu próprio log em `sistema\logs\launcher.log`.

## Roadmap

Veja [`ROADMAP.md`](ROADMAP.md).
