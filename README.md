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

1. Baixe o instalador `.pyz` da release e execute `py -3 MainERP-Instalador-<versão>.pyz`
   no PowerShell. O instalador remove sua pasta temporária ao terminar normalmente;
   o arquivo baixado permanece e pode ser excluído depois.
   Na instalação pelo ZIP completo, arquivos de desenvolvimento conhecidos são
   removidos da pasta extraída após o sucesso, exceto em checkouts Git.
2. Abra o **MainERP** pelo atalho da Área de Trabalho ou do Menu Iniciar. Também há
   um atalho de reserva em `%LOCALAPPDATA%\MainERP\sistema\MainERP.lnk`.
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
fechamento do sistema. O ZIP manual contém um snapshot SQLite verificado, inclusive dados
confirmados em WAL; mantenha cópias externas e verifique periodicamente sua recuperação.
Uma restauração é preparada enquanto o sistema está aberto e aplicada na próxima
inicialização, antes de abrir o banco; um snapshot anterior é mantido em `dados\backups`.
Durante a aplicação, uma trava SQLite exclusiva impede gravações de outros processos
até a validação; feche os demais programas que usam o banco antes de restaurar.
Se a trava não puder ser adquirida, o sistema bloqueia a abertura e preserva a
restauração pendente. A publicação da pendência exige suporte a hard links no volume
de dados; se não houver suporte, a preparação falha sem substituir uma pendência.
O launcher precisa ser atualizado pelo instalador para usar esse fluxo. Em execução direta
de `main.py`, abra o sistema novamente após solicitar a restauração. Se ocorrer falha na
restauração, o sistema não abre; preserve o backup anterior e os arquivos pendentes para
diagnóstico. A validação verifica integridade, tabelas, nomes de colunas, valores inteiros
em centavos e referências estrangeiras declaradas após migrar uma cópia temporária.
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
6. O GitHub Actions valida a tag, executa Ruff e pytest, gera o ZIP e o manifesto, assina o
   ZIP com Ed25519 e publica os três assets (`.zip`, `.zip.sig` e `version.json`) como latest.
   Não recicle tags já publicadas.
7. Usuários com o launcher configurado para o manifesto da GitHub Release recebem a versão
   ao fechar e abrir o MainERP pelo atalho.

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
