# MainERP - distribuição sem PyInstaller

## Novidades da versão 0.10

- Releases novas são assinadas com Ed25519 no GitHub Actions. O launcher verifica a
  assinatura, o SHA256 e a versão antes de instalar atualizações online.
- O launcher e o instalador configuram o manifesto público do GitHub Releases por padrão,
  preservando URLs personalizadas e a opção explícita de desativar atualizações.

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
2. Baixe e extraia o **Source code (zip)** da release correspondente no GitHub;
   o ZIP `MainERP-<versão>.zip` é somente para atualização e não contém o instalador.
   Na pasta extraída, dê dois cliques em `distribuicao\instalar.bat`.
3. Abra o MainERP pelo atalho (Área de Trabalho / Menu Iniciar).
4. Em uma instalação nova, restaure seu backup pela tela de Configurações; o sistema
   reinicia sozinho. A instalação não apaga uma pasta `dados\` que já exista.
5. Se estiver migrando do executável antigo (PyInstaller), confira a restauração e os
   dados no novo sistema antes de remover a instalação antiga.

Use o destino padrão. A opção `--destino` altera a pasta do sistema, mas não altera
automaticamente o local de dados usado pelo aplicativo; instalações existentes podem
depender desse comportamento. Não use essa opção para uma instalação nova do cliente.

Os atalhos novos identificam o MainERP para o Windows e usam o ícone da aplicação.
Para corrigir atalhos em uma instalação existente, feche o sistema, execute novamente
o instalador atualizado e desafixe e fixe novamente o MainERP na barra de tarefas.
O instalador preserva a pasta de dados. Uma atualização automática de código, por si
só, não substitui o instalador nem recria os atalhos já existentes.

## Preparar uma nova release

Antes de distribuir uma versão:

1. Faça e teste as alterações; atualize `APP_VERSION` em
   `mainerp/core/config.py` e a versão, data e histórico em `CHANGELOG.md`.
   A barra de status usa `APP_VERSION` automaticamente.
2. Execute `verificar.bat` na raiz do projeto. Corrija qualquer falha de Ruff ou pytest
   antes de continuar, atualize o commit em `main` e envie-o ao GitHub.
3. Teste a instalação/atualização em uma instalação de teste antes de distribuir aos
   usuários. Para versões que alteram o banco, use uma cópia dos dados, nunca o único
   banco de produção.
4. Antes da primeira publicação automatizada, configure em **Settings > Secrets and variables
   > Actions** o secret `MAINERP_ED25519_PRIVATE_KEY`. Gere a chave uma única vez com
   `python distribuicao\gerar_chave_assinatura.py`; o PEM privado fica fora do repositório em
   `%LOCALAPPDATA%\MainERP\signing\ed25519-private.pem`. Cadastre o conteúdo do arquivo como
   secret sem incluí-lo em commits, logs ou mensagens. O launcher contém somente a chave
   pública correspondente.
5. Crie e envie uma tag anotada igual à versão, por exemplo `git tag -a v0.10.1 -m "MainERP 0.10.1"`
   e `git push origin v0.10.1`. O GitHub Actions confere a tag com `APP_VERSION`,
   executa Ruff e pytest, gera ZIP e manifesto SHA256, assina o ZIP com Ed25519 e publica
   os três assets (`.zip`, `.zip.sig` e `version.json`) na GitHub Release mais recente.

Não reutilize uma tag já publicada. Se o workflow falhar, corrija o problema em um novo
commit e publique uma nova versão/tag; a release não deve ser montada manualmente com
artefatos de outro commit. O workflow precisa da permissão `contents: write` habilitada nas
configurações de Actions do repositório. O launcher exige assinatura válida para
atualizações online e também confere o hash SHA256 e a versão dentro do pacote. Pacotes
locais continuam sendo aceitos como transferência manual confiável.

Instalações anteriores ao launcher com suporte a Ed25519 precisam atualizar o launcher uma
vez (por exemplo, executando o instalador atualizado); releases de código não substituem o
launcher fixo instalado. A release 0.09 e anteriores não têm assinatura Ed25519. Proteja a
chave privada com acesso restrito e faça cópia segura; para rotacioná-la, atualize a chave
pública embutida no launcher e o secret do Actions antes de publicar a próxima release.

Novas versões usam `MAJOR.MINOR.PATCH`, somente números sem zeros à esquerda; não são
publicados pré-releases nem metadados. MAJOR indica mudanças incompatíveis, MINOR
funcionalidades compatíveis e PATCH correções compatíveis; com MAJOR zero, a API ainda está
em desenvolvimento. Reinicie os componentes inferiores ao aumentar MAJOR ou MINOR.
A geração do pacote e o workflow recusam versões fora desse formato, e a tag deve ser
`v` seguido da versão exata. A versão deve ser maior que as já instaladas: o launcher
compara componentes numéricos e continua reconhecendo as versões históricas de dois
componentes, como `0.10`, que é anterior a `0.10.0`. As releases antigas não são renomeadas.

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

O launcher atualizado cria um ambiente Python em `sistema\runtimes\<versão>` para cada
atualização, instala nele as dependências antes de ativar a release e preserva o runtime
das versões anteriores para rollback. Versões antigas continuam usando `sistema\runtime`.
Instalações existentes precisam receber o launcher atualizado pelo instalador; a mudança
requer espaço em disco e acesso às dependências. Não apague
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

Em cada release, publique os três assets na mesma GitHub Release:

- `MainERP-<versão>.zip`
- `MainERP-<versão>.zip.sig`, assinatura Ed25519 em Base64 do ZIP
- `version.json` gerado junto com esse ZIP.

Marque como **Latest** a release mais nova. O manifesto contém a versão, o nome do ZIP e
o SHA256. Mantenha o campo `url` como nome do ZIP (por exemplo,
`MainERP-0.10.1.zip`): o launcher resolve esse caminho relativo ao endpoint
`latest/download/version.json`, que leva ao asset da mesma release. Não edite manualmente
o SHA256 nem reutilize assets/version de builds diferentes. Se recriar o ZIP, regenere e
publique também o manifesto correspondente.

Fluxo de publicação:

1. Prepare e valide a versão conforme **Preparar uma nova release**; o GitHub Actions gera
   o ZIP, manifesto e assinatura ao receber a tag.
2. O workflow publica o ZIP, `.zip.sig` e `version.json` na release marcada como latest.
3. Verifique em uma janela anônima que os três assets podem ser baixados sem login.
4. Em uma instalação de teste, abra o MainERP pelo atalho. Instalações novas usam o
   endpoint padrão; confirme a versão instalada, a assinatura, o SHA256 e o log do launcher
   antes de anunciar a atualização.
5. Os usuários atualizam ao fechar e abrir o MainERP pelo atalho com conexão à internet.
   O launcher consulta o manifesto antes de iniciar o aplicativo; se encontrar versão
   superior, baixa o ZIP, confere o SHA256 e instala. Se a consulta/download falhar, mantém
   a versão já instalada e registra o erro no log.

Para instalações antigas cujo launcher não tenha o endpoint padrão ou suporte a Ed25519,
atualize-o uma vez (por exemplo, executando o instalador atual) e confirme a configuração
em `%LOCALAPPDATA%\MainERP\sistema\launcher.json`. Publicar uma release do código do
aplicativo não substitui o launcher fixo instalado. Releases anteriores ao bootstrap não
validam assinatura; depois dele, futuras atualizações online sem assinatura válida são
recusadas. Para desativar atualizações online, defina
`"disable_online_updates": true` no `launcher.json`; pacotes locais continuarão sendo
processados.

A assinatura Ed25519 valida a autenticidade do ZIP contra a chave pública embutida no
launcher; o SHA256 do manifesto também é verificado. O manifesto não é assinado, mas não
pode substituir um pacote assinado válido. Proteja a conta GitHub com autenticação
multifator e limite quem pode publicar releases. O instalador padrão é público e não usa
tokens de acesso.

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
