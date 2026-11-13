# Instalação e atualização do PLUMA

Guia para instalar, atualizar, diagnosticar e voltar de versão no computador do usuário. Para
publicar uma nova release, veja [publicar_release.md](publicar_release.md).

O nome do produto é PLUMA; pastas, variáveis e pacotes mantêm o identificador técnico
`MainERP` (por exemplo, `%LOCALAPPDATA%\MainERP`, `MAINERP_DATA` e `MainERP-<versão>.zip`).

## Como funciona

```
%LOCALAPPDATA%\MainERP\
  sistema\                  <- launcher, runtime e releases
    MainERP.lnk             atalho de reserva
    runtime\                Python + bibliotecas (venv principal)
    runtimes\<versão>\      ambiente Python de cada atualização (versões antigas usam runtime\)
    launcher.pyw            o atalho aponta SEMPRE para ele
    releases\<versão>\      uma pasta por versão (as 3 últimas são mantidas)
    current.txt             versão ativa
    atualizacoes\           fila de pacotes .zip; aplicados\ e invalidas\ guardam histórico
    launcher.json           URL do manifesto de atualização online
    logs\                   launcher.log
  dados\                    <- NUNCA é tocada por atualizações
    erp.db, config.json, backup_settings.json, backups\, relatorios\, novidades\,
    logs\sistema.log
```

O launcher é fixo: o atalho sempre abre `sistema\launcher.pyw`. Antes de iniciar o
aplicativo, ele procura atualizações locais e consulta o servidor online, se configurado. O
código de cada versão fica isolado em `releases\<versão>\`; banco, configurações, backups e
relatórios ficam em `dados\`.

## Primeira instalação

1. Tenha o Python 3.10 ou superior instalado (recomendado: 3.12), com o "py launcher".
2. Baixe `MainERP-Instalador-<versão>.pyz` nos artefatos da release e execute no PowerShell:

   ```powershell
   py -3 MainERP-Instalador-<versão>.pyz
   ```

   O instalador extrai os arquivos necessários em uma pasta temporária própria, removida ao
   terminar, inclusive em falhas normais; interrupções abruptas podem deixar resíduos
   temporários. O arquivo baixado permanece e pode ser apagado manualmente depois. O ZIP
   `MainERP-<versão>.zip` é somente para atualização.
3. Abra o PLUMA pelo atalho (Área de Trabalho ou Menu Iniciar). Há também uma cópia em
   `%LOCALAPPDATA%\MainERP\sistema\MainERP.lnk`.
4. Em uma instalação nova, restaure seu backup pela tela de Configurações; o sistema reinicia
   sozinho. A instalação não apaga uma pasta `dados\` que já exista.
5. Se estiver migrando do executável antigo (PyInstaller), confira a restauração e os dados no
   novo sistema antes de remover a instalação antiga.

### Instalação pelo ZIP completo do código

Também é possível usar `distribuicao\instalar.bat` do ZIP completo do código. Após a
instalação bem-sucedida, o instalador remove da pasta extraída os arquivos de desenvolvimento
conhecidos, como `ROADMAP.md`, `verificar.bat` e os testes listados no instalador. O ZIP
original, outros arquivos, pastas e dados são preservados. Em repositórios Git, ou quando
origem e destino se sobrepõem, a limpeza é ignorada. O histórico instalado permanece
disponível em **Sobre**. Para reinstalar a partir do código-fonte, extraia novamente o ZIP
completo: a pasta já limpa não contém mais todos os arquivos originais.

### Local de instalação

Use o destino padrão. A opção `--destino` altera a pasta do sistema, mas não altera
automaticamente o local de dados usado pelo aplicativo; instalações existentes podem depender
desse comportamento. Não use essa opção para uma instalação nova do cliente.

### Atalhos

Os atalhos novos identificam o PLUMA para o Windows e usam o ícone da aplicação. Para corrigir
os atalhos de uma instalação existente, feche o sistema, execute novamente o instalador
atualizado e desafixe e fixe novamente o programa na barra de tarefas. O instalador preserva a
pasta de dados. Uma atualização automática de código, por si só, não substitui o instalador
nem recria os atalhos já existentes.

## Como a atualização funciona

Ao abrir pelo atalho com conexão à internet, o launcher consulta o manifesto antes de iniciar
o aplicativo. Se encontrar uma versão superior, baixa o ZIP, confere a assinatura Ed25519, o
SHA-256 e a versão, e instala. Se a consulta ou o download falharem, mantém a versão já
instalada e registra o erro em `sistema\logs\launcher.log`. Para atualizar, feche o sistema e
abra-o novamente pelo atalho.

O launcher cria um ambiente Python em `sistema\runtimes\<versão>` para cada atualização,
instala nele as dependências antes de ativar a release e preserva o ambiente das versões
anteriores para o rollback. Isso requer espaço em disco e acesso às dependências. Não apague
nem substitua esse ambiente durante uma atualização normal.

Pacotes locais colocados em `sistema\atualizacoes\` também são instalados na abertura
(consulte [publicar_release.md](publicar_release.md) para gerá-los). Os inválidos vão para
`atualizacoes\invalidas\` e os instalados para `atualizacoes\aplicadas\`.

### Janela de atualização

Enquanto instala uma atualização, o launcher mostra uma janela mínima (Tkinter, tema claro,
não a interface Qt do aplicativo): o símbolo da Pluma, uma barra de progresso e a palavra
"Atualizando". A barra avança com o trabalho realmente feito: bytes baixados (quando o
servidor informa o tamanho), arquivos extraídos e pacotes coletados pelo `pip`. A criação do
ambiente e a instalação final dos pacotes pelo `pip` não informam andamento, então a barra
pode permanecer parada nessas etapas por algum tempo. Se a janela não puder ser aberta, a
atualização continua sem ela.

A janela pertence ao launcher fixo: instalações existentes só a recebem ao executar o
instalador atualizado.

### Novidades após atualizar

Após atualizar e abrir a nova versão pelo launcher, o aplicativo apresenta uma vez as
novidades do `CHANGELOG.md`, incluindo as versões intermediárias disponíveis. A leitura é
registrada em `dados\novidades\`; falhas de leitura ou gravação são avisadas e permitem nova
tentativa. Instalações novas e regressões a versões anteriores não exibem o diálogo. A
detecção depende de uma release anterior confirmada ainda presente; por segurança, o diálogo
também é suprimido enquanto existir uma release mais nova, mesmo marcada como ruim.

### Atualizações que alteram o banco

Quando uma release inclui migração, o aplicativo cria automaticamente um backup
`dados\backups\pre_migracao_*.db` antes de atualizar o esquema. As migrações do projeto são
aditivas e executadas uma vez. Mesmo assim, faça um backup próprio antes de atualizar um
banco importante e confirme que ele pode ser restaurado; não confie em uma release de código
anterior para desfazer uma migração. Detalhes dos backups em
[banco_e_backups.md](banco_e_backups.md); para criar migrações, veja
[desenvolvimento.md](desenvolvimento.md).

## Atualização online: configuração

O instalador grava o manifesto padrão em `%LOCALAPPDATA%\MainERP\sistema\launcher.json` em
instalações novas ou quando a URL está vazia. Se o arquivo já tiver uma URL própria, ela é
preservada.

- **Atualizações anônimas:** o repositório e os artefatos da release precisam estar públicos.
  Enquanto o repositório estiver privado, os usuários sem acesso não conseguem baixar os
  arquivos; o aplicativo instalado continua abrindo e o launcher registra a falha em
  `sistema\logs\launcher.log`.
- **Desativar atualizações online:** defina `"disable_online_updates": true` no
  `launcher.json`. Pacotes locais continuam sendo processados.
- **Instalações antigas:** se o launcher não tiver o endereço padrão ou o suporte a Ed25519,
  atualize-o uma vez (por exemplo, executando o instalador atual) e confirme a configuração em
  `launcher.json`. Publicar uma release do código do aplicativo não substitui o launcher fixo
  instalado.

## Rollback

### Falha ao iniciar uma versão nova

Ao iniciar uma versão recém-instalada, o launcher verifica se a janela principal abriu. Se a
nova release falhar antes dessa confirmação, ela é marcada como ruim (`.ruim`) e o launcher
tenta abrir a versão anterior válida. Esse rollback cobre falha de inicialização; não é um
rollback do banco e não reverte migrações. Se o aplicativo já abriu e falhar depois, o launcher
não volta automaticamente à versão anterior.

### Voltar manualmente para uma versão anterior

1. Feche o sistema.
2. Faça uma cópia do banco atual e dos arquivos importantes em `dados\`.
3. Edite `%LOCALAPPDATA%\MainERP\sistema\current.txt` e informe a versão anterior, cuja pasta
   ainda exista em `releases\`.
4. Abra pelo atalho. O launcher usa o código selecionado, mas mantém o banco e as
   configurações atuais.

O launcher conserva as três releases válidas mais recentes e a versão atual; releases mais
antigas podem já ter sido removidas. Voltar o código não restaura o banco: se a versão anterior
não for compatível com o esquema migrado, feche o aplicativo e restaure um backup compatível
pela rotina de restauração. Não substitua arquivos do banco enquanto o programa estiver aberto.
Os backups pré-migração ficam em `dados\backups\`.

## Diagnóstico

- **Launcher e instalação:** `%LOCALAPPDATA%\MainERP\sistema\logs\launcher.log`.
- **Saída e erros do aplicativo:** `%LOCALAPPDATA%\MainERP\dados\logs\sistema.log` (ou a pasta
  definida por `MAINERP_DATA`).
- **A versão instalada não abre:** preserve os logs e a pasta `releases\` antes de qualquer
  remoção; confirme `current.txt` e o espaço livre em disco.
- **Não apague `.ruim` esperando reinstalar o mesmo ZIP:** releases já existentes não são
  instaladas novamente. Corrija o problema, aumente a versão e gere um novo pacote.

### Mensagem `No module named 'cryptography'`

Confira a mensagem e feche o sistema. No PowerShell da mesma conta do Windows, para uma
instalação no caminho padrão:

```powershell
$python = Join-Path $env:LOCALAPPDATA 'MainERP\sistema\runtime\Scripts\python.exe'
& $python -m pip install 'cryptography>=44,<47'
if ($LASTEXITCODE -eq 0) {
    & $python -c 'from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey'
}
```

O comando exige acesso ao repositório de pacotes configurado para o `pip`. Se falhar, preserve
a mensagem e consulte `sistema\logs\launcher.log`; não desative a verificação de assinatura.
Depois que o comando terminar sem erros, abra o atalho novamente. Para instalações em outro
destino, use o `python.exe` do runtime principal desse destino. Os instaladores que incluem
esta correção preparam a dependência no runtime principal antes de instalar ou atualizar o
launcher; as releases do código não substituem o launcher fixo.

## Dados em outro local

Defina a variável de ambiente `MAINERP_DATA` com a pasta desejada. As atualizações não
removem nem substituem essa pasta.

## Desinstalar

Apague `sistema\` e os atalhos. Preserve `%LOCALAPPDATA%\MainERP\dados\` se precisar do banco,
das configurações, dos backups ou dos relatórios.
