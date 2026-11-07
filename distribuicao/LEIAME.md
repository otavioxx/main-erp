# MainERP 0.08 - distribuição sem PyInstaller

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
   antes de continuar.
3. Gere o pacote com `python distribuicao\criar_release.py`. O ZIP
   `dist\MainERP-<versão>.zip` e o `dist\version.json` são criados. O manifesto contém a
   versão, o nome do ZIP e seu SHA256.
4. Confira que o número da versão está correto e que o ZIP corresponde ao código validado.
   Se alterar ou recriar o ZIP depois de gerar o manifesto, gere o manifesto novamente.
5. Teste a instalação/atualização em uma instalação de teste antes de distribuir aos
   usuários. Para versões que alteram o banco, use uma cópia dos dados, nunca o único
   banco de produção.

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

## Atualização online (opcional; servidor ainda precisa ser configurado)

O suporte no launcher já existe, mas a instalação vem com `update_url` vazio: não há um
servidor de atualização configurado por padrão. Para habilitar:

1. Gere e teste a release conforme a seção **Preparar uma nova release**.
2. Publique o ZIP e o `version.json` correspondentes em um servidor confiável com HTTPS.
   O valor `url` do manifesto deve apontar para o ZIP acessível pelo launcher; prefira URL
   relativa ao manifesto ou HTTPS. Mantenha os dois arquivos disponíveis enquanto os
   clientes precisarem baixar essa versão.
3. Em cada instalação, configure
   `%LOCALAPPDATA%\MainERP\sistema\launcher.json` com a URL HTTPS do manifesto:

   ```json
   {
     "update_url": "https://servidor-confiavel.example/mainerp/version.json"
   }
   ```

4. Abra o MainERP pelo atalho. Antes de iniciar o sistema, o launcher consulta o manifesto;
   se a versão for mais nova, baixa o ZIP, confere o SHA256 e só então instala. Se não
   houver conexão ou o manifesto/pacote falhar, a versão instalada continua disponível e
   o erro é registrado em `sistema\logs\launcher.log`.

O SHA256 detecta pacote diferente ou corrompido, mas não substitui assinatura digital:
quem controla o manifesto também pode publicar outro hash. Assinatura dos pacotes ainda
não está implementada. Por isso, distribua somente por HTTPS sob seu controle e proteja
o acesso de publicação ao servidor. O modo online aceita caminhos locais e URLs HTTP,
mas HTTP não protege contra alteração em trânsito e não deve ser usado para releases.

Para desativar atualizações online, deixe `update_url` vazio. Os pacotes locais em
`sistema\atualizacoes\` continuam sendo processados normalmente.

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
