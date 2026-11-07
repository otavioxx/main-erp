# MainERP 0.09 - distribuição sem PyInstaller

## Novidades da versão 0.09

- O launcher e o instalador usam o manifesto público do GitHub Releases como padrão para
  verificar atualizações online.
- URLs personalizadas existentes e a opção explícita de desativar as atualizações são
  preservadas.

## Novidades da versão 0.08

- Corrigida a exibição e a edição do valor no diálogo **Preço de Venda**.
- Valores monetários de vendas, parcelas, recebimentos, produtos, pedidos e
  condicionais são calculados e persistidos em centavos, reduzindo erros de
  arredondamento.
- Ao pagar parcialmente a última parcela, o saldo restante passa a gerar uma
  nova parcela.
- A atualização do banco é feita por migrações aditivas, com backup automático
  antes da alteração do esquema.

## Como funciona

```
%LOCALAPPDATA%\MainERP\
  sistema\                  <- launcher, runtime e releases
    runtime\                Python + bibliotecas (venv)
    launcher.pyw            o atalho aponta SEMPRE para ele
    releases\<versão>\      uma pasta por versão (as 3 últimas são mantidas)
    current.txt             versão ativa
    atualizacoes\           fila de pacotes .zip; aplicados\ e invalidas\ guardam histórico
    launcher.json           URL do manifesto online (vazio por padrão)
    logs\                   launcher.log
  dados\                    <- NUNCA é tocada por atualizações
    erp.db, config.json, backup_settings.json, backups\, relatorios\, logs\sistema.log
```

O launcher é fixo: o atalho sempre abre `sistema\launcher.pyw`. Antes de iniciar o
aplicativo, ele procura atualizações locais e, se configurado, consulta o servidor online.
O código de cada versão fica isolado em `releases\<versão>\`; banco, configurações,
backups e relatórios ficam em `dados\`.

## Primeira instalação

1. Python 3.10 ou superior instalado (recomendado: 3.12), com o "py launcher".
2. Dê dois cliques em `distribuicao\instalar.bat`.
3. Abra o MainERP pelo atalho (Área de Trabalho / Menu Iniciar).
4. Em uma instalação nova, restaure seu backup pela tela de Configurações; o sistema
   reinicia sozinho. A instalação não apaga uma pasta `dados\` que já exista.
5. Se estiver migrando do executável antigo (PyInstaller), confira a restauração e os
   dados no novo sistema antes de remover a instalação antiga.

## Preparar uma nova release

Antes de distribuir uma versão:

1. Faça e teste as alterações; atualize `APP_VERSION` em
   `mainerp/core/config.py`, o texto da versão/data na linha 54 de
   `mainerp\ui\views\main_window.py` e o histórico em `CHANGELOG.md`.
2. Execute `verificar.bat` na raiz do projeto. Corrija qualquer falha de Ruff ou pytest
   antes de continuar, atualize o commit em `main` e envie-o ao GitHub.
3. Teste a instalação/atualização em uma instalação de teste antes de distribuir aos
   usuários. Para versões que alteram o banco, use uma cópia dos dados, nunca o único
   banco de produção.
4. Crie e envie uma tag anotada igual à versão, por exemplo `git tag -a v0.10 -m "MainERP 0.10"`
   e `git push origin v0.10`. O GitHub Actions confere a tag com `APP_VERSION`,
   executa Ruff e pytest e, somente se passarem, gera o ZIP e o manifesto com SHA256 e
   publica os dois assets na GitHub Release mais recente.

Não reutilize uma tag já publicada. Se o workflow falhar, corrija o problema em um novo
commit e publique uma nova versão/tag; a release não deve ser montada manualmente com
artefatos de outro commit. O workflow precisa da permissão `contents: write` habilitada nas
configurações de Actions do repositório.

O nome da versão precisa ser novo e maior que as versões já instaladas. O launcher compara
as sequências numéricas encontradas no nome (por exemplo, `0.08` e `0.09`); versão igual ou
menor é ignorada. A adoção de SemVer estrito ainda não está configurada.

## Publicar uma atualização (no mesmo PC)

No computador onde o código-fonte e o ambiente de desenvolvimento estão disponíveis:

1. Conclua a preparação e as verificações da release acima.
2. Execute `distribuicao\publicar_atualizacao.bat`. Ele gera o ZIP da versão configurada e
   o coloca em `%LOCALAPPDATA%\MainERP\sistema\atualizacoes\` do usuário atual.
3. Feche o MainERP se estiver aberto e inicie-o novamente pelo atalho. O launcher instala
   os pacotes da fila antes de abrir o aplicativo.

Para atualizar outro computador sem servidor online, copie o ZIP gerado para
`%LOCALAPPDATA%\MainERP\sistema\atualizacoes\` desse computador e abra o MainERP pelo
atalho. Não copie o ZIP para `releases\` nem execute `main.py` diretamente: é o launcher
que verifica a estrutura do pacote, seleciona a versão e mantém o rollback.
Transfira o arquivo por um meio confiável. Antes de copiá-lo, compare o resultado de
`Get-FileHash .\MainERP-<versão>.zip -Algorithm SHA256` com o campo `sha256` do
`dist\version.json` gerado junto com ele. O instalador local não valida esse hash por conta
própria.

Pacotes locais que não sejam válidos são movidos para `atualizacoes\invalidas\`; os
instalados vão para `atualizacoes\aplicadas\`. Se a versão já existir ou não for mais nova,
o pacote é ignorado/arquivado. Para corrigir uma release já distribuída, publique uma nova
versão, com número maior, em vez de reutilizar o mesmo número.

Ao iniciar uma versão recém-instalada, o launcher verifica se a janela principal abriu.
Se a nova release falhar antes dessa confirmação, ela é marcada como ruim (`.ruim`) e o
launcher tenta abrir a versão anterior válida. Esse rollback cobre falha de inicialização;
não é um rollback do banco e não reverte migrações. Se o aplicativo já abriu e falhar
depois, o launcher não volta automaticamente à versão anterior.

Se `requirements.txt` mudar, o launcher atualiza as dependências no ambiente isolado
`sistema\runtime\` durante a instalação (é necessária conexão com a internet). Não apague
nem substitua esse ambiente durante uma atualização normal.

## Mudanças no banco (migrações)

Quando uma release inclui migração, o aplicativo cria automaticamente um backup
`dados\backups\pre_migracao_*.db` antes de atualizar o esquema. As migrações do projeto
são aditivas e executadas uma vez. Mesmo assim, faça um backup próprio antes de atualizar
um banco importante e confirme que ele pode ser restaurado; não confie em uma release de
código anterior para desfazer uma migração.

Ao desenvolver uma migração, crie `_migracao_NNN_descricao` em
`mainerp/data/database.py`, registre-a em `MIGRACOES` com o próximo número e mantenha a
alteração aditiva (nova tabela/coluna), para preservar compatibilidade sempre que possível.

## Voltar para uma versão anterior

1. Feche o MainERP.
2. Faça uma cópia do banco atual e dos arquivos importantes em `dados\`.
3. Edite `%LOCALAPPDATA%\MainERP\sistema\current.txt` e informe a versão anterior, cuja
   pasta ainda exista em `releases\`.
4. Abra pelo atalho. O launcher usa o código selecionado, mas mantém o banco e as
   configurações atuais.

O launcher conserva as três releases válidas mais recentes e a versão atual. Releases
mais antigas podem já ter sido removidas. Voltar o código não restaura o banco: se a versão
anterior não for compatível com o esquema migrado, feche o aplicativo e restaure um backup
compatível pela rotina de restauração. Não substitua arquivos do banco enquanto o programa
estiver aberto. Backups pré-migração ficam em `dados\backups\`.

## Atualização automática via GitHub Releases

O launcher usa por padrão o manifesto:

`https://github.com/otavioxx/main-erp/releases/latest/download/version.json`

O instalador grava esse endereço em
`%LOCALAPPDATA%\MainERP\sistema\launcher.json` em instalações novas ou quando a URL está
vazia. Se o arquivo já tiver uma URL própria, ela é preservada. Para as atualizações
anônimas funcionarem, o repositório e os assets
da release precisam estar públicos. Enquanto o repositório estiver privado, os usuários
sem acesso não conseguem baixar os arquivos; o aplicativo instalado continua abrindo e o
launcher registra a falha em `sistema\logs\launcher.log`.

Em cada release, publique **os dois assets** na mesma GitHub Release:

- `MainERP-<versão>.zip`
- `version.json` gerado junto com esse ZIP.

Marque como **Latest** a release mais nova. O manifesto contém a versão, o nome do ZIP e
o SHA256. Mantenha o campo `url` como nome do ZIP (por exemplo,
`MainERP-0.09.zip`): o launcher resolve esse caminho relativo ao endpoint
`latest/download/version.json`, que leva ao asset da mesma release. Não edite manualmente
o SHA256 nem reutilize assets/version de builds diferentes. Se recriar o ZIP, regenere e
publique também o manifesto correspondente.

Fluxo de publicação:

1. Prepare, valide e gere os artefatos conforme **Preparar uma nova release**.
2. Na página **Releases** do GitHub, crie uma release para a nova versão/tag e anexe o ZIP
   e o `version.json`. Publique-a como a versão mais recente (não como pre-release).
3. Verifique em uma janela anônima que os dois assets podem ser baixados sem login.
4. Em uma instalação de teste, abra o MainERP pelo atalho. Instalações novas usam o
   endpoint padrão; confirme a versão instalada, o SHA256 e o log do launcher antes de
   anunciar a atualização.
5. Os usuários atualizam ao fechar e abrir o MainERP pelo atalho com conexão à internet.
   O launcher consulta o manifesto antes de iniciar o aplicativo; se encontrar versão
   superior, baixa o ZIP, confere o SHA256 e instala. Se a consulta/download falhar, mantém
   a versão já instalada e registra o erro no log.

Para instalações antigas cujo launcher não tenha o endpoint padrão, atualize uma vez o
launcher e o `%LOCALAPPDATA%\MainERP\sistema\launcher.json` (por exemplo, executando o
instalador atual ou colocando o endereço acima em `update_url`). Publicar uma release do
código do aplicativo não substitui o launcher instalado. Depois desse bootstrap, futuras
releases são detectadas automaticamente. Para desativar atualizações online, defina
`"disable_online_updates": true` no `launcher.json`; pacotes locais continuarão sendo
processados.

O SHA256 detecta pacote diferente ou corrompido, mas não substitui assinatura digital:
quem controla o manifesto também pode publicar outro hash. Assinatura dos pacotes ainda
não está implementada. Proteja a conta GitHub com autenticação multifator e limite quem
pode publicar releases. O instalador padrão é público e não usa tokens de acesso.

## Diagnóstico de atualização

- Launcher/instalação: consulte `%LOCALAPPDATA%\MainERP\sistema\logs\launcher.log`.
- Saída e erros do aplicativo: consulte `%LOCALAPPDATA%\MainERP\dados\logs\sistema.log`
  (ou a pasta definida por `MAINERP_DATA`).
- Se a versão instalada não abrir, preserve os logs e a pasta `releases\` antes de
  qualquer remoção; confirme `current.txt` e o espaço livre em disco.
- Não apague `.ruim` esperando reinstalar o mesmo ZIP: releases já existentes não são
  instaladas novamente. Corrija o problema, aumente a versão e gere um novo pacote.

## Dados em outro local

Defina a variável de ambiente `MAINERP_DATA` com a pasta desejada. Atualizações não removem
nem substituem essa pasta.

## Desinstalar

Apague `sistema\` e os atalhos. Preserve `%LOCALAPPDATA%\MainERP\dados\` se precisar do
banco, das configurações, dos backups ou dos relatórios.
