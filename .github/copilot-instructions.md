# Instruções do GitHub Copilot — PLUMA

Estas instruções definem os padrões que devem ser seguidos pelo GitHub Copilot durante o desenvolvimento, manutenção e evolução do PLUMA.

## 1. Registro de alterações e documentação

- Considere o `CHANGELOG.md` como o histórico oficial das alterações das versões publicadas.
- Utilize o `DEVLOG.md` para registrar o progresso técnico do desenvolvimento, decisões de arquitetura, implementações e detalhes relevantes.
- Registre no DEVLOG funcionalidades, correções, melhorias, refatorações e decisões técnicas relevantes.
- Registre no CHANGELOG somente alterações relevantes para o usuário final.
- Organize o CHANGELOG utilizando as categorias: Added, Changed, Fixed, Removed e Security, respeitando o padrão já estabelecido no arquivo.
- Utilize a seção `[Unreleased]` para alterações ainda não publicadas.
- Não remova, reescreva ou modifique registros de versões anteriores sem autorização.
- Não duplique informações desnecessariamente entre documentos.
- Atualize a documentação somente quando houver alterações relevantes.
- Nunca invente funcionalidades, resultados, decisões ou alterações.
- Não altere números de versão automaticamente.
- Não registre como concluída uma funcionalidade que ainda esteja parcialmente implementada.

### Responsabilidade de cada documento

- `README.md`: apresentação do PLUMA, requisitos, instalação, estrutura e orientações gerais.
- `CHANGELOG.md`: alterações relevantes para o usuário final.
- `DEVLOG.md`: histórico técnico do desenvolvimento e decisões de implementação.
- `distribuicao/LEIAME.md`: instalação, distribuição, atualização, releases e manutenção.
- `.github/copilot-instructions.md`: regras e orientações para o desenvolvimento com IA.

## 2. Alterações de código

- Analise o código existente antes de modificá-lo.
- Preserve a arquitetura, os padrões e as convenções estabelecidas.
- Prefira alterações pequenas, localizadas e objetivas.
- Reutilize funcionalidades, componentes e serviços existentes.
- Não reescreva arquivos inteiros sem necessidade.
- Não remova funcionalidades sem autorização.
- Não crie abstrações, dependências ou arquivos desnecessários.
- Não altere arquivos fora do escopo solicitado.
- Preserve a compatibilidade com dados, funcionalidades e versões anteriores.
- Não introduza soluções temporárias sem justificativa.
- Evite duplicação de código e responsabilidades.
- Não presuma a existência de funções, classes, módulos ou arquivos sem verificar.
- Antes de alterar uma implementação, verifique onde ela é utilizada e quais componentes dependem dela.

### Entrega de código

- Ao corrigir ou modificar arquivos, apresente o código completo de cada arquivo afetado.
- Não entregue apenas trechos, fragmentos ou instruções de substituição.
- Não utilize reticências para omitir partes do código.
- Garanta que os arquivos entregues sejam compatíveis entre si.
- Informe claramente quais arquivos foram criados, modificados ou removidos.
- Não apresente código fictício como se fosse parte da implementação existente.

## 3. Fluxo de trabalho

O desenvolvimento deve ser incremental e controlado.

Para cada tarefa:

1. Identifique os arquivos envolvidos.
2. Analise as implementações relacionadas.
3. Identifique dependências e possíveis efeitos colaterais.
4. Avalie a solução mais simples e adequada.
5. Implemente somente o escopo solicitado ou aprovado.
6. Execute os testes pertinentes.
7. Verifique se a implementação funcionou.
8. Atualize o DEVLOG.md e, quando aplicável, o CHANGELOG.md.
9. Informe os arquivos alterados, testes executados e eventuais limitações.

### Regras de execução

- Trabalhe uma etapa por vez.
- Conclua e valide a etapa atual antes de iniciar outra.
- Não misture refatorações não relacionadas à tarefa.
- Não amplie o escopo por iniciativa própria.
- Não considere uma alteração concluída enquanto houver falhas relacionadas a ela.
- Quando uma tarefa depender de decisões importantes, apresente as alternativas e aguarde aprovação.
- Não execute operações irreversíveis sem autorização.

## 4. Banco de dados e integridade

O PLUMA utiliza SQLite e controla a versão do banco por meio de `PRAGMA user_version`.

### Regras obrigatórias

- Preserve a integridade e a consistência dos dados.
- Analise os impactos antes de alterar estruturas, tabelas, colunas ou relacionamentos.
- Não execute operações destrutivas sem autorização.
- Preserve a compatibilidade com bancos de dados existentes.
- Considere migrações sempre que houver alterações estruturais.
- Utilize migrações incrementais e, preferencialmente, aditivas.
- Não recrie o banco de dados para implementar atualizações.
- Não remova ou altere dados existentes sem justificativa e autorização.
- Trate transações e falhas de operações adequadamente.
- Preserve os mecanismos de backup e restauração.
- Teste migrações utilizando bancos isolados ou temporários.
- Não utilize o banco de produção nos testes.

### Localização dos dados

Os dados do usuário ficam separados dos arquivos do programa:

`%LOCALAPPDATA%\MainERP\dados\`

Essa estrutura contém o banco de dados, configurações, backups, relatórios, logs e outros arquivos persistentes.

- Nunca remova, substitua ou limpe essa pasta durante uma atualização.
- Respeite a variável de ambiente `MAINERP_DATA`, utilizada para definir um local alternativo para os dados.
- Preserve os dados durante atualizações, reinstalações e substituições de releases.

## 5. Dependências e arquitetura

### Tecnologias do projeto

- Python 3.10 ou superior, preferencialmente Python 3.12.
- PyQt6 para a interface gráfica.
- SQLite para armazenamento de dados.
- ReportLab para geração de documentos PDF.
- Ruff para lint, formatação e organização de imports.
- Pytest para testes automatizados.

### Diretrizes de arquitetura

- O PLUMA é uma aplicação desktop para Windows 10 e 11.
- Utilize PyQt6 e Qt Widgets para a interface.
- Não transforme o sistema em aplicação web, mesmo que local.
- Preserve a separação entre interface, regras de negócio, acesso a dados e infraestrutura.
- Respeite a organização de diretórios existente.
- Prefira bibliotecas e recursos já disponíveis no projeto.
- Consulte o ambiente e as dependências antes de instalar novos pacotes.
- Não adicione dependências para resolver problemas simples.
- Priorize bibliotecas gratuitas e de código aberto.
- Verifique a compatibilidade de novas dependências com Windows e Python.
- Atualize o arquivo de dependências correspondente quando adicionar pacotes.
- Não introduza mudanças arquiteturais sem necessidade ou autorização.

### Organização do projeto

Respeite as responsabilidades atuais dos principais diretórios:

- `mainerp/app.py`: inicialização e ciclo principal do aplicativo.
- `mainerp/core/`: configurações, caminhos, logging e tratamento de erros.
- `mainerp/data/`: conexão SQLite, migrações e modelos de dados.
- `mainerp/domain/`: regras de negócio e utilitários.
- `mainerp/ui/`: janela principal, telas, diálogos, mixins e tema.
- `mainerp/reports/`: geração de relatórios e PDFs.
- `tests/`: testes automatizados.
- `distribuicao/`: geração de pacotes, instalador e ferramentas de distribuição.

Não altere essa organização sem avaliar os impactos e justificar a necessidade.

## 6. Testes e qualidade

- Utilize Ruff como referência para lint, formatação e organização de imports Python.
- Utilize Pytest para testes automatizados.
- Crie ou atualize testes quando necessário.
- Execute os testes pertinentes à alteração, ampliando a verificação quando houver impactos relevantes.
- Não ignore falhas de testes sem investigar.
- Não desative ou enfraqueça testes para aprovar uma implementação.
- Não declare uma funcionalidade como concluída sem verificar seu comportamento.
- Diferencie testes executados, não executados e resultados esperados.
- Não afirme que uma verificação foi aprovada sem executá-la.

### Comandos de verificação

Verificar o projeto com Ruff:

```powershell
python -m ruff check .
```

Formatar o código:

```powershell
python -m ruff format .
```

Executar os testes:

```powershell
python -m pytest
```

Executar a verificação geral:

```powershell
.\verificar.bat
```

### Pylance

Manter compatibilidade com o nível `basic` de análise do Pylance.

- Evite erros de importação e referências inexistentes.
- Utilize tipagem coerente.
- Evite variáveis e parâmetros sem utilização.
- Não ignore diagnósticos sem justificativa técnica.
- Respeite a versão mínima de Python definida pelo projeto.

Não modifique as configurações do Ruff, Pylance ou VSCode apenas para ocultar problemas introduzidos pelo código.

## 7. Segurança

- Nunca exponha credenciais, tokens, chaves ou informações sensíveis.
- Não armazene segredos diretamente no código.
- Não remova mecanismos de proteção existentes.
- Valide entradas e operações que envolvam arquivos e dados.
- Não execute comandos destrutivos sem autorização.
- Preserve a segurança dos backups e dos processos de restauração.
- Não inclua arquivos locais, ambientes virtuais, bancos de produção ou segredos nos pacotes de distribuição.
- Não enfraqueça mecanismos de verificação de integridade ou autenticidade.

### Assinaturas digitais

O sistema utiliza Ed25519 e SHA-256 para verificar a autenticidade e a integridade dos pacotes de distribuição.

Existem duas finalidades independentes:

1. Assinatura de releases: autenticação dos pacotes de atualização.
2. Assinatura de licenças: validação das licenças do aplicativo.

Regras:

- As chaves privadas dessas duas finalidades nunca devem ser compartilhadas ou reutilizadas.
- Nunca inclua chaves privadas no repositório.
- Nunca distribua chaves privadas aos clientes.
- Nunca exponha segredos em logs, mensagens ou documentação pública.
- Preserve os mecanismos de validação existentes.
- Não substitua chaves públicas incorporadas ao aplicativo sem avaliar a compatibilidade com instalações existentes.

A chave privada de assinatura das releases é utilizada pelo GitHub Actions por meio do segredo `MAINERP_ED25519_PRIVATE_KEY`. Sua cópia local deve permanecer protegida e fora do repositório.

### Licenciamento

O licenciamento deve ser independente do mecanismo de atualização.

- Não utilizar a chave de assinatura de releases para licenciar o aplicativo.
- Preservar a licença durante atualizações.
- Priorizar validação offline.
- Não introduzir dependência de servidor, autenticação online ou serviços pagos sem autorização.
- Não comprometer o acesso aos dados do usuário em caso de expiração da licença.
- Preservar os mecanismos de integridade e validação das licenças.

## 8. Git, versionamento e distribuição

### Git

- Não execute commits, pushes, merges ou releases sem autorização.
- Não descarte alterações existentes do usuário.
- Verifique o estado do Git antes de operações que possam afetar arquivos.
- Preserve o histórico de versões.
- Não execute `git reset --hard` sem autorização.
- Não exclua branches ou tags sem autorização.
- Não sobrescreva commits ou arquivos remotos sem autorização.
- Utilize Conventional Commits quando solicitado a preparar mensagens de commit.
- Não altere arquivos de configuração do Git sem necessidade.

### Versionamento

A versão do aplicativo deve permanecer sincronizada entre:

- `mainerp/core/config.py`
- `CHANGELOG.md`
- Tag Git.
- Manifesto de distribuição `version.json`.

As tags devem seguir o padrão:

`vMAJOR.MINOR.PATCH`

Exemplo: `v0.10.10`.

Não altere a versão automaticamente. Atualizações de versão devem fazer parte de uma tarefa ou processo de publicação autorizado.

### Distribuição

O PLUMA utiliza distribuição própria, sem PyInstaller.

A instalação segue esta estrutura:

`%LOCALAPPDATA%\MainERP\`

Com separação entre:

- `sistema\`: launcher, runtimes e releases.
- `dados\`: banco, configurações, backups, relatórios e logs.

O launcher oficial fica em:

`sistema\launcher.pyw`

Os atalhos devem apontar para o launcher, e não diretamente para `main.py`.

As releases ficam em:

`sistema\releases\<versão>\`

Os runtimes isolados ficam em:

`sistema\runtimes\<versão>\`

### Regras do sistema de atualização

- Preserve o funcionamento do launcher.
- Preserve os runtimes isolados por versão.
- Preserve o mecanismo de rollback.
- Preserve a separação entre sistema e dados.
- Não introduza dependência de PyInstaller.
- Não altere o processo de atualização sem avaliar compatibilidade com instalações existentes.
- Não comprometa a verificação Ed25519, SHA-256 ou a validação dos pacotes.
- Considere que o launcher mantém as três releases válidas mais recentes.
- A atualização deve preservar os dados e a licença do usuário.

As atualizações online utilizam GitHub Releases públicas, sem autenticação ou token no cliente.

Manifesto oficial:

`https://github.com/otavioxx/main-erp/releases/latest/download/version.json`

Não introduza autenticação ou dependências externas no mecanismo de atualização sem autorização.

### Publicação de releases

As releases oficiais são geradas pelo GitHub Actions após o envio de uma tag anotada.

O workflow deve:

1. Validar a tag e a versão do aplicativo.
2. Executar Ruff.
3. Executar Pytest.
4. Gerar o pacote ZIP.
5. Gerar o instalador `.pyz`.
6. Gerar manifestos e hashes.
7. Assinar os pacotes com Ed25519.
8. Publicar a GitHub Release com os artefatos correspondentes.

Não monte manualmente pacotes de release com arquivos provenientes de commits diferentes.

### Política para falhas de publicação

Diferencie o envio de uma tag ao GitHub da publicação efetiva da GitHub Release.

**Quando o workflow falhar antes da publicação efetiva da GitHub Release e nenhum pacote tiver sido distribuído:**

- Identifique e corrija o problema.
- Atualize o commit de origem.
- Se necessário, remova a tag incorreta local e remotamente.
- Recrie a mesma tag apontando para o commit corrigido.
- Execute novamente o workflow.

Esse procedimento é permitido porque nenhum pacote daquela versão foi efetivamente publicado ou distribuído.

**Quando a GitHub Release já tiver sido publicada ou seus pacotes tiverem sido distribuídos:**

- Não substitua silenciosamente os arquivos.
- Não reutilize a mesma versão para distribuir conteúdo diferente.
- Corrija o problema em uma nova versão.
- Gere uma nova tag e uma nova release.

Antes de qualquer recuperação, verifique o estado real da publicação. Não presuma que uma versão não foi distribuída apenas porque o workflow apresentou uma falha.

Toda criação ou exclusão de tags, envio de commits e publicação de releases exige autorização expressa.

## 9. Interface e experiência do usuário

### Identidade do aplicativo

- Preserve a identidade visual estabelecida no MainERP.
- Mantenha consistência entre telas, componentes, diálogos e interações.
- Utilize PyQt6 e Qt Widgets.
- Não introduza tecnologias web para construir telas.
- Evite duplicar componentes, estilos e comportamentos.
- Priorize interfaces claras, intuitivas e consistentes.
- Preserve acessibilidade, legibilidade e usabilidade.
- Não altere comportamentos existentes sem avaliar seus impactos.

### Comportamento da interface

- Evite bloquear a interface durante operações demoradas.
- Utilize mecanismos adequados para operações em segundo plano quando necessário.
- Apresente mensagens claras para erros, confirmações e operações concluídas.
- Preserve os padrões de navegação existentes.
- Verifique atalhos de teclado, estados de carregamento e interações relacionadas.
- Considere tamanhos, posicionamentos e redimensionamento das janelas.
- Evite mudanças visuais que não tenham relação com a tarefa solicitada.

## 10. Comunicação e respostas

- Utilize português brasileiro nas respostas e documentações.
- Seja objetivo, técnico e evite explicações repetitivas.
- Não apresente análises extensas quando uma resposta direta for suficiente.
- Explique termos técnicos quando necessário.
- Considere que o usuário entende os fundamentos de programação, mas não é programador profissional.
- Apresente soluções simples e explique riscos ou limitações relevantes.
- Informe claramente os arquivos modificados.
- Informe os testes executados e seus resultados.
- Sinalize problemas não resolvidos e limitações.
- Não afirme que uma operação foi realizada sem confirmação.
- Ao fornecer código para substituição, apresente o código completo de cada arquivo afetado.
- Não gere documentação, relatórios ou arquivos adicionais sem necessidade.
- Não solicite novamente informações já fornecidas.
- Quando faltar código ou contexto necessário para uma alteração segura, solicite os arquivos ou informações correspondentes.

---

## Princípio geral

O PLUMA deve continuar sendo um sistema simples, confiável, seguro, organizado e fácil de manter e atualizar.

Toda implementação deve priorizar:

- Preservação dos dados dos usuários.
- Estabilidade e compatibilidade.
- Facilidade de instalação e manutenção.
- Baixo custo de operação.
- Independência de serviços pagos ou servidores externos.
- Simplicidade arquitetural.
- Segurança da distribuição e das atualizações.
- Manutenção futura pelo próprio desenvolvedor.

**Não introduza complexidade sem necessidade. Não sacrifique a estabilidade por conveniência. Não altere o escopo sem aprovação.**
