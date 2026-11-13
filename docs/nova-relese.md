## Como publicar uma Release do PLUMA

O processo é automatizado pelo GitHub Actions. Você prepara a versão, envia os commits e cria uma tag anotada. O GitHub executa os testes, gera os pacotes, assina e publica a release.

1. Preparar a versão
Antes de tudo, atualize a versão em:

`mainerp/core/config.py`

Atualize também o `CHANGELOG.md`, registrando as alterações da versão.

Exemplo:
`APP_VERSION = "0.10.11"`


## No CHANGELOG:

## [0.00.00] - 2026-11-12

### Added
- Nova funcionalidade.

### Fixed
- Correção de um problema.

Atualize o DEVLOG.md se houver decisões ou alterações técnicas relevantes.

2. Verificar o projeto
No PowerShell, execute:
`.\verificar.bat`


Esse processo executa Ruff e Pytest.

Não prossiga enquanto houver falhas relacionadas à versão.

3. Conferir e enviar os commits
Verifique as alterações:
git status
git diff


Adicione os arquivos:
git add .


Crie o commit:
git commit -m "release: prepara versão 0.10.11"


Envie para o GitHub:
git push origin main


4. Verificar a tag
Confira se a tag ainda não existe:
git tag --list v0.10.11


Valide se a versão do código corresponde à tag:
python distribuicao/criar_release.py --verificar-tag v0.10.11


O resultado esperado é:
Tag v0.10.11 válida.


5. Criar e enviar a tag
Crie uma tag anotada:
git tag -a v0.10.11 -m "MainERP 0.10.11"


Envie ao GitHub:
git push origin v0.10.11


Publicação iniciada

6. Acompanhar o GitHub Actions
Acesse:
GitHub Actions — MainERP
O workflow Release executará automaticamente:
    1. Validação da tag e da versão.
    2. Verificação com Ruff.
    3. Execução dos testes Pytest.
    4. Geração do pacote ZIP.
    5. Geração do instalador .pyz.
    6. Geração dos hashes SHA-256.
    7. Assinatura Ed25519 dos pacotes.
    8. Publicação da GitHub Release.
A chave privada de assinatura é fornecida pelo segredo MAINERP_ED25519_PRIVATE_KEY do GitHub Actions.

7. Conferir a publicação
Acesse:
Releases do MainERPConfira se a versão foi publicada e se os seguintes artefatos estão disponíveis:
    - MainERP-0.10.11.zip
    - MainERP-0.10.11.zip.sig
    - MainERP-Instalador-0.10.11.pyz
    - MainERP-Instalador-0.10.11.pyz.sig
    - instalador.sha256
    - version.json

## Atenção: se o GitHub Actions falhar

Existem duas situações:

1. Falhou antes da publicação da GitHub Release e nenhum pacote foi distribuído.

Você pode corrigir o problema e reutilizar a mesma versão:
git tag -d v0.10.11
git push origin :refs/tags/v0.10.11


Depois, após corrigir e enviar os commits:
git tag -a v0.10.11 -m "MainERP 0.10.11"
git push origin v0.10.11


2. A GitHub Release já foi publicada ou seus pacotes foram distribuídos.

Não substitua os arquivos. Corrija o problema em uma nova versão, por exemplo 0.10.12.

Resumo rápido
Ordem de publicação
    1. Atualizar APP_VERSION e CHANGELOG.md.
    2. Executar .\verificar.bat.
    3. Verificar alterações e criar commit.
    4. Enviar main ao GitHub.
    5. Validar a tag.
    6. Criar e enviar a tag anotada.
    7. Acompanhar o GitHub Actions.
    8. Conferir os artefatos da Release.

O ponto principal: você não precisa gerar os pacotes manualmente nem publicar a release pela interface do GitHub. Basta preparar o código, enviar a tag e deixar o workflow cuidar do restante.
