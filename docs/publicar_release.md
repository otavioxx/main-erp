# Publicar uma release do PLUMA

Este é o procedimento único para preparar, publicar e conferir uma release. O processo é
automatizado pelo GitHub Actions: você prepara a versão, envia os commits e cria uma tag
anotada; o GitHub executa as verificações, gera os pacotes, assina e publica a release.
Não é necessário gerar os pacotes manualmente nem publicar pela interface do GitHub.

Para instalar, atualizar ou voltar de versão em um computador, veja
[instalacao_e_atualizacao.md](instalacao_e_atualizacao.md).

## Resumo da ordem

1. Atualizar `APP_VERSION` e o `CHANGELOG.md`.
2. Executar `.\verificar.bat`.
3. Testar a instalação e a atualização em uma instalação de teste.
4. Verificar as alterações, criar o commit e enviar `main` ao GitHub.
5. Validar a tag.
6. Criar e enviar a tag anotada.
7. Acompanhar o GitHub Actions.
8. Conferir os artefatos da release.

## 1. Preparar a versão

Atualize a versão em `mainerp/core/config.py`, por exemplo:

```python
APP_VERSION = "0.10.11"
```

A barra de status usa `APP_VERSION` automaticamente.

Registre as alterações em `CHANGELOG.md`, em uma seção com a versão e a data, usando as
categorias em português já adotadas no arquivo (Adicionado, Alterado, Corrigido, Removido,
Segurança):

```markdown
## [0.10.11] - 2026-11-12

### Adicionado

- Nova funcionalidade.

### Corrigido

- Correção de um problema.
```

A seção da versão deve ter itens: o pipeline interrompe a publicação se ela estiver vazia, e
as notas públicas da release vêm dela. O aplicativo também mostra essas novidades uma vez,
na primeira abertura após a atualização.

Se houver decisões ou alterações técnicas relevantes, registre-as no `docs/DEVLOG.md`.

### Regras de versão

- Use `MAJOR.MINOR.PATCH`, somente números sem zeros à esquerda; não são publicados
  pré-releases nem metadados.
- MAJOR indica mudanças incompatíveis, MINOR funcionalidades compatíveis e PATCH correções
  compatíveis. Enquanto MAJOR for zero, a API ainda está em desenvolvimento. Reinicie os
  componentes inferiores ao aumentar MAJOR ou MINOR.
- A geração do pacote e o workflow recusam versões fora desse formato, e a tag deve ser `v`
  seguido da versão exata (por exemplo, `v0.10.11`).
- A versão deve ser maior que as já instaladas. O launcher compara os componentes numéricos
  e continua reconhecendo as versões históricas de dois componentes, como `0.10`, que é
  anterior a `0.10.0`. As releases antigas não são renomeadas.

## 2. Verificar o projeto

No PowerShell, na raiz do projeto:

```powershell
.\verificar.bat
```

O script executa Ruff e pytest e interrompe com código de erro se algum falhar. Não prossiga
enquanto houver falhas.

## 3. Testar a instalação e a atualização

Teste em uma instalação de teste antes de distribuir aos usuários. Para versões que alteram
o banco, use uma cópia dos dados, nunca o único banco de produção.

Uma instalação de teste pode ser criada com:

```powershell
python distribuicao\instalar.py --destino C:\Temp\MainERP-teste --sem-atalhos
```

A opção `--destino` altera a pasta do sistema, mas não altera automaticamente o local de
dados usado pelo aplicativo. Antes de abrir o sistema dessa instalação, defina
`MAINERP_DATA` para uma pasta de teste. Não use `--destino` em uma instalação nova de
cliente.

## 4. Conferir e enviar os commits

```powershell
git status
git diff
```

Adicione somente os arquivos revisados e crie o commit:

```powershell
git add <arquivos revisados>
git commit -m "chore: prepara a versão 0.10.11"
git push origin main
```

## 5. Validar a tag

Confira que a tag ainda não existe e que a versão do código corresponde a ela:

```powershell
git tag --list v0.10.11
python distribuicao/criar_release.py --verificar-tag v0.10.11
```

O resultado esperado é `Tag v0.10.11 válida.`

## 6. Criar e enviar a tag

```powershell
git tag -a v0.10.11 -m "MainERP 0.10.11"
git push origin v0.10.11
```

O envio da tag inicia a publicação.

## 7. Acompanhar o GitHub Actions

O workflow **Release** executa automaticamente:

1. Validação da tag e da versão.
2. Verificação com Ruff.
3. Execução dos testes com pytest.
4. Geração do pacote ZIP de atualização.
5. Geração do instalador `.pyz`.
6. Geração do manifesto e dos hashes SHA-256.
7. Assinatura Ed25519 dos pacotes.
8. Publicação da GitHub Release como a mais recente (`latest`).

O workflow precisa da permissão `contents: write` habilitada nas configurações de Actions do
repositório. A chave privada de assinatura é fornecida pelo secret
`MAINERP_ED25519_PRIVATE_KEY`.

## 8. Conferir a publicação

Na página de Releases do repositório, confira se a versão foi publicada como `latest` e se
os artefatos estão presentes:

- `MainERP-<versão>.zip`
- `MainERP-<versão>.zip.sig`
- `MainERP-Instalador-<versão>.pyz`
- `MainERP-Instalador-<versão>.pyz.sig`
- `instalador.sha256`
- `version.json`

Depois:

1. Verifique, em uma janela anônima, que os artefatos podem ser baixados sem login.
2. Em uma instalação de teste, abra o sistema pelo atalho e confirme a versão instalada, a
   assinatura, o SHA-256 e o `sistema\logs\launcher.log` antes de anunciar a atualização.

## Se o GitHub Actions falhar

Antes de qualquer recuperação, verifique o estado real da publicação na página de Releases.
Não presuma que a versão não foi distribuída apenas porque o workflow apresentou uma falha.

**Falhou antes da publicação da GitHub Release e nenhum pacote foi distribuído.** É possível
corrigir o problema e reutilizar a mesma versão:

```powershell
git tag -d v0.10.11
git push origin :refs/tags/v0.10.11
```

Depois de corrigir e enviar os commits, crie e envie a tag novamente:

```powershell
git tag -a v0.10.11 -m "MainERP 0.10.11"
git push origin v0.10.11
```

**A GitHub Release já foi publicada ou seus pacotes foram distribuídos.** Não substitua os
arquivos nem reutilize a mesma versão para conteúdo diferente: corrija o problema em uma nova
versão (por exemplo, `0.10.12`), com nova tag e nova release. A release não deve ser montada
manualmente com artefatos de commits diferentes.

## Assinaturas e chaves

- As releases são assinadas com Ed25519. O launcher verifica a assinatura, o SHA-256 e a
  versão antes de instalar atualizações online; atualizações online sem assinatura válida são
  recusadas.
- Antes da primeira publicação automatizada, configure em **Settings > Secrets and variables >
  Actions** o secret `MAINERP_ED25519_PRIVATE_KEY` com o conteúdo do PEM da chave privada.
- Gere a chave uma única vez com `python distribuicao\gerar_chave_assinatura.py`. O PEM
  privado fica fora do repositório, em `%LOCALAPPDATA%\MainERP\signing\ed25519-private.pem`.
  Nunca o inclua em commits, logs, mensagens ou chats, e mantenha uma cópia segura. O
  launcher contém somente a chave pública.
- Para rotacionar a chave, atualize a chave pública embutida no launcher e o secret do Actions
  antes de publicar a próxima release. Instalações existentes só recebem um launcher novo
  pelo instalador.
- A chave de assinatura de releases é independente da chave de licenciamento: nunca
  reutilize uma para a outra.
- Releases até a 0.09 não têm assinatura Ed25519. Instalações anteriores ao launcher com
  suporte a Ed25519 precisam atualizá-lo uma vez (por exemplo, executando o instalador
  atualizado).
- O manifesto não é assinado, mas não pode substituir um pacote assinado válido. Proteja a
  conta do GitHub com autenticação multifator e limite quem pode publicar releases. O
  instalador padrão é público e não usa tokens de acesso.

## Manifesto de atualização

O launcher consulta, por padrão:

`https://github.com/otavioxx/main-erp/releases/latest/download/version.json`

- O repositório e os artefatos da release precisam estar públicos para as atualizações
  anônimas funcionarem.
- O manifesto contém a versão, o nome do ZIP e o SHA-256. Mantenha o campo `url` como o
  nome do ZIP (por exemplo, `MainERP-0.10.1.zip`): o launcher o resolve a partir do endereço
  `latest/download/version.json`, que leva ao artefato da mesma release.
- Não edite manualmente o SHA-256 nem reutilize artefatos ou `version.json` de builds
  diferentes. Se recriar o ZIP, regenere e publique também o manifesto correspondente.
- A configuração do launcher no computador do usuário (URL própria, desativar atualizações) está
  em [instalacao_e_atualizacao.md](instalacao_e_atualizacao.md).

## Conteúdo do pacote

O gerador inclui os arquivos de runtime da raiz e os arquivos Python dos pacotes listados em
`PACOTES`, em `distribuicao/criar_release.py`. Ao criar um pacote novo, atualize essa lista e
execute os testes. Não inclua arquivos locais ou dados pessoais entre os arquivos Python
desses pacotes.

## Pacote local, sem GitHub

Para gerar e inspecionar o pacote localmente, sem publicar:

```powershell
python distribuicao/criar_release.py
```

Isso cria `dist/MainERP-<versão>.zip` e `dist/version.json`; não publica a release.

Para atualizar o computador onde o código está disponível, execute
`distribuicao\publicar_atualizacao.bat`: ele gera o ZIP da versão configurada e o coloca em
`%LOCALAPPDATA%\MainERP\sistema\atualizacoes\` do usuário atual. Feche o sistema e abra-o
novamente pelo atalho; o launcher instala os pacotes da fila antes de abrir o aplicativo.

Para atualizar outro computador sem servidor online, copie o ZIP gerado para
`%LOCALAPPDATA%\MainERP\sistema\atualizacoes\` desse computador e abra o sistema pelo atalho.
Não copie o ZIP para `releases\` nem execute `main.py` diretamente: é o launcher que verifica
a estrutura do pacote, seleciona a versão e mantém o rollback. Transfira o arquivo por um
meio confiável e, antes de copiá-lo, compare o resultado de
`Get-FileHash .\MainERP-<versão>.zip -Algorithm SHA256` com o campo `sha256` do
`dist\version.json` gerado junto com ele. O instalador local não valida esse hash por conta
própria; pacotes locais são aceitos como transferência manual confiável.

Pacotes locais inválidos vão para `atualizacoes\invalidas\` e os instalados para
`atualizacoes\aplicadas\`. Se a versão já existir ou não for mais nova, o pacote é
ignorado e arquivado. Para corrigir uma release já distribuída, publique uma nova versão com
número maior.
