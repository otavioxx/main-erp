# Histórico de Desenvolvimento

## 2026-11-18

### Preparação da release 0.12.0

- Consolidadas as melhorias compatíveis de verificação de backups, acompanhamento do backup manual, dimensionamento do diálogo de seleção de produtos e entrada digitada no crediário.
- Ruff e suíte completa aprovados no Windows (383 testes aprovados, 1 ignorado) e no Linux com Python 3.12 (380 aprovados, 4 ignorados).

### Documentação — organização e navegação

- Criado `docs/README.md` como índice para guias de uso, desenvolvimento, recuperação,
  identidade visual e publicação.
- Melhorado o `README.md` da raiz para destacar recursos, instalação, preservação dos dados
  e acesso aos guias, sem duplicar os procedimentos detalhados.
- Criado `docs/backup_recuperacao.md` com orientação para cópia externa e teste isolado de
  restauração; o item correspondente do ROADMAP foi concluído.
- Organizada a navegação de `docs/identidade_visual.md` por seções e removidas referências
  a imagens e documentos que não existem no repositório.
- Corrigidas as instruções das categorias do CHANGELOG para corresponder ao padrão em
  português já utilizado.

### ROADMAP — reorganização por sequência

- Organizadas as fases pela ordem planejada de execução; a Fase F ficou separada como
  trabalho transversal.
- Agrupadas as pendências da Fase B por verificação/CI, distribuição/compatibilidade,
  regras de negócio e persistência.
- Consolidadas em H as referências duplicadas de auditoria, painel e evolução para uso em
  múltiplos computadores; os itens preexistentes do arquivo foram preservados.

### Entrada no crediário

- O campo de entrada mantém o editor numérico e a validação; o tema oculta os botões e o campo desativa incrementos por teclado e roda do mouse. Evitado `NoButtons`, que reduz a largura do editor com o tema Qt.

### Diálogo de backup manual

- Corrigido o ícone para usar `CODE_DIR`, independentemente da pasta de execução.
- Progresso, sucesso, erros e falha ao salvar preferências agora aparecem no diálogo; o fechamento fica disponível após a verificação do ZIP.
- Seguidos os padrões de título, botão primário e estados semânticos do tema. A barra usa o mesmo trilho e acento do splash; mensagens têm fonte maior e janela dimensionada para comportá-las.
- A tela mantém o estado atual do backup visível, como na referência de [Windows Backup](https://support.microsoft.com/en-gb/windows/experience/backup-recovery/back-up-and-restore-with-windows-backup).

### Verificação pós-gravação de backups

- [Backup automático](../mainerp/data/automatic_backup.py): após publicar o snapshot, a cópia é relida (tamanho e SHA-256 do temporário) e passa por `integrity_check`; se falhar, o arquivo é removido e o erro chega à interface via `backup_falhou`.
- [Backup manual](../mainerp/ui/dialogs/backup_dialog.py): o ZIP publicado é relido (tamanho, SHA-256, `testzip` e integridade do banco dentro do ZIP); se falhar, é descartado e o erro é exibido no diálogo, sem registrar a data do último backup.
- Antes de publicar, o arquivo temporário passa por `fsync` nos dois fluxos, para que a releitura não dependa só do cache do sistema.
- Removida a leitura integral do ZIP em memória no `BackupThread`.

### Dialogo de seleção de produto

- Ajustado dimensionamento da janela de [diálogo de seleção de produtos](../mainerp/ui/dialogs/produto_selection_dialog.py) de Medio para Large.

## 2026-11-17

### Preparação da release 0.11.2

- A tentativa de publicar 0.11.1 falhou no teste de backup manual no GitHub Actions, antes do empacotamento; nenhuma release foi publicada.
- A coleta de lixo podia encerrar o `QApplication` durante o teste e destruir o objeto Qt de backup. Os testes de backup manual agora mantêm a aplicação Qt viva durante o módulo e verificam o tratamento da falha mesmo com coleta de lixo.
- Preparada a versão 0.11.2, preservando as tags das tentativas anteriores.
- Ruff aprovado e testes completos aprovados no Windows (375, com 1 ignorado) e no Linux com Python 3.12 (372, com 4 ignorados). Instalação limpa e atualização local de 0.10.10 para 0.11.2 foram verificadas em pastas isoladas, preservando os dados de teste e a release anterior.
- A release 0.11.2 foi publicada pelo GitHub Actions como a mais recente. Os seis artefatos foram baixados sem autenticação; manifesto, hashes SHA-256 e assinaturas Ed25519 foram verificados.
- Em instalação isolada, o launcher da 0.10.10 baixou e instalou a 0.11.2 online, preservando os dados de teste e a release anterior. O teste executou o launcher diretamente com `--somente-atualizar`, sem criar atalho.

### Preparação da release 0.11.1

- Preparada a versão 0.11.1 com as alterações posteriores à 0.10.10 e a correção da disputa de travas WAL. A tag da tentativa anterior foi preservada.
- Validada a instalação limpa e a atualização local de 0.10.10 para 0.11.1 em pastas isoladas, preservando dados de teste e a release anterior. Ruff e testes no Windows passaram novamente (375 aprovados e 1 ignorado).

### Restauração — disputa de travas em WAL

- Reproduzida no Linux a falha com dois processos sincronizados: ambos retinham conexões enquanto aguardavam a trava exclusiva, e uma aplicação terminava com `database is locked`.
- A tentativa de trava exclusiva passa a falhar imediatamente em caso de disputa, fechando a conexão antes de repetir com intervalo variável. O prazo total de 30 segundos, a reserva de escrita inicial e a trava exclusiva durante o snapshot, a cópia e a validação foram mantidos.
- O teste determinístico falhou antes da correção e passou 30 vezes no Linux após ela. Os testes de restauração passaram no Linux (37) e no Windows (36, com o teste específico do Linux ignorado).
- Verificação completa: Ruff aprovado; Windows com 375 testes aprovados e 1 ignorado; Linux em ambiente Python 3.12 isolado com 372 aprovados e 4 ignorados. O GitHub Actions não foi reexecutado.

### Preparação da release 0.11.0

- Preparada a versão 0.11.0 com as funcionalidades e melhorias posteriores à 0.10.10.
- Corrigida a preparação do teste de backups simultâneos para manter a instância do Qt ativa antes da criação dos workers; uma execução completa havia falhado devido à destruição dos objetos Qt.
- O workflow já utiliza os novos caminhos de `instalador/` e `publicacao/`.
- Validação no Windows: Ruff e 375 testes aprovados. Instalador 0.11.0 e atualização local da 0.10.10 foram testados em pastas isoladas, preservando um arquivo de dados de teste e a release anterior.
- A publicação falhou no teste Linux de restauração concorrente em WAL com `database is locked`. O empacotamento e a publicação não foram executados; a release 0.11.0 não foi publicada e sua tag permanece no remoto. As alterações voltaram para `[Unreleased]`, e a versão do código foi restabelecida para 0.10.10 até a correção.

### Vendas em crediário

- Restaurada a entrada no diálogo de pagamento, com validação e cálculo do saldo em centavos; as parcelas usam o valor financiado e exibem o ajuste da última parcela.
- A entrada continua registrada na venda, sem gerar recebimento. Não houve alteração no banco.
- Adicionados testes da regra, da interface e do fechamento em banco temporário.
- O editor da entrada seleciona o valor numérico ao receber clique, mantendo os botões do campo.

## 2026-11-15

### Distribuição — pastas `instalador/` e `publicacao/`

- A pasta `distribuicao/` foi dividida por quem usa cada arquivo. `instalador/` reúne o que o instalador executa e acompanha o download de instalação: `instalar.py`, `instalar.bat`, `criar_atalhos.ps1`, `launcher.pyw` e `criar_release.py` (o instalador usa o `criar_release.py` para empacotar o código). `publicacao/` reúne as ferramentas de quem publica e não vai no `.pyz`: `criar_instalador.py`, `instalador_bootstrap.py`, `assinar_release.py`, `gerar_chave_assinatura.py` e `publicar_atualizacao.bat`.
- O formato instalado (`sistema\launcher.pyw`, `releases\`, `dados\`) e os nomes dos pacotes (`MainERP-<versão>.zip`, `MainERP-Instalador-<versão>.pyz`) não mudaram. Instaladores `.pyz` já publicados continuam funcionando, pois levam o próprio bootstrap e os próprios arquivos.
- publicacao/criar_instalador.py insere a raiz do projeto no sys.path e importa from instalador import criar_release, para que o Pylance resolva o módulo.; `instalador_bootstrap.py` passou a executar `instalador/instalar.py`; `publicar_atualizacao.bat` chama `..\instalador\criar_release.py`. `pyproject.toml`: a exceção E402 vale para `instalador/instalar.py` e `publicacao/criar_instalador.py`.
- Novo `.gitattributes` com `export-ignore` para `.github`, `docs`, `tests`, `publicacao` e arquivos só de desenvolvimento, de modo que o "Source code (zip)" gerado pelo GitHub leve só o necessário para instalar. Substitui, na origem, a limpeza que o instalador fazia e foi removida.
- Substituídos `distribuicao/README.md` por `instalador/README.md` e `publicacao/README.md`; caminhos atualizados em `docs/`, nos testes e em comentários.
- `tests/test_launcher_progresso.py`: o carregador do `launcher.pyw` passou a ser informado de forma explícita (`SourceFileLoader`). Sem isso o teste falha fora do Windows, onde o Python não reconhece `.pyw`, e o workflow de release executa o pytest em Linux.
- Pendente: o workflow `.github/workflows/release.yml` precisa dos novos caminhos (não estava no pacote analisado), e a conferência no Windows com `verificar.bat` e uma instalação de teste isolada.

## 2026-11-12

### Documentação — reorganização, etapa 2 (README e documentos de apoio)

- `README.md` enxugado para a apresentação do sistema: requisitos, instalação resumida, onde ficam os dados, estrutura do projeto e índice de documentos. Tudo o que saiu foi movido para os documentos abaixo; nenhuma das afirmações removidas foi descartada.
- Criado `docs/banco_e_backups.md` com o funcionamento técnico do banco, do backup automático e manual, da restauração e da validação de backups, antes em um único bloco do README. Os parágrafos foram divididos por assunto, sem alterar o conteúdo.
- Criado `docs/desenvolvimento.md` com o ambiente, a verificação (`verificar.bat` e os comandos de Ruff e pytest, conforme o `copilot-instructions.md`), como criar migrações e as convenções de commit, dados e logs.
- Criado `docs/README.md`, índice dos documentos. A seção sobre o tema claro ou escuro foi removida do README porque já consta em `docs/identidade_visual.md`; o README mantém uma frase com o link.
- `docs/instalacao_e_atualizacao.md`: a referência às migrações passou a apontar para `docs/banco_e_backups.md` e `docs/desenvolvimento.md`.
- Conferência: as frases-chave do README original foram buscadas nos documentos novos por script, e os links relativos dos documentos entregues foram verificados. Não foi executado nenhum teste de código, pois só houve alteração de documentação.
- Pendente (etapas 3 e 4): dividir o `docs/identidade_visual.md`, arquivar os documentos históricos da Fase 4.3, ajustar `CHANGELOG.md` e `ROADMAP.md`, e atualizar o `copilot-instructions.md`.

### Documentação — reorganização, etapa 1 (release e instalação)

- Criado `docs/publicar_release.md`, que passa a ser a única descrição do procedimento de release. Reúne o que estava no `README.md`, no `distribuicao/LEIAME.md` e em `docs/nova-relese.md`. A política para falhas segue o `.github/copilot-instructions.md`: a mesma versão só pode ser reutilizada se a GitHub Release não foi publicada, e o estado real da publicação deve ser verificado antes. O exemplo de commit deixou de usar `git add .`.
- Criado `docs/instalacao_e_atualizacao.md` com a instalação, a estrutura de pastas, a atualização, o rollback e o diagnóstico (conteúdo do `distribuicao/LEIAME.md`). Corrigido o que estava desatualizado: o `launcher.json` já recebe a URL padrão do instalador, a estrutura de pastas inclui `runtimes\` e `dados\novidades\`, e a janela de espera do launcher agora é descrita com a barra de progresso implementada.
- Criado `distribuicao/README.md`, curto, com a função de cada script da pasta. As descrições de `assinar_release.py`, `criar_instalador.py` e `instalador_bootstrap.py` foram inferidas dos nomes e da documentação anterior, e precisam ser conferidas nos arquivos.
- `README.md`: a seção "Publicar uma nova versão" virou um ponteiro para `docs/publicar_release.md`, e o link do LEIAME foi trocado. `.github/copilot-instructions.md`: a lista de responsabilidade dos documentos foi atualizada.
- Removidos `distribuicao/LEIAME.md` e `docs/nova-relese.md`. Antes, `git grep` por `LEIAME`, `nova-relese`, `identidade_visual` e `backup_recuperacao` em `tests`, `distribuicao`, `mainerp` e `.github` encontrou apenas a lista do `copilot-instructions.md` e um comentário em `splash_pluma.py`.
- Pendente (etapas 2 a 4): enxugar o `README.md`, criar `docs/README.md`, `docs/desenvolvimento.md` e `docs/banco_e_backups.md`, dividir o `docs/identidade_visual.md`, arquivar os documentos históricos da Fase 4.3, ajustar `CHANGELOG.md` e `ROADMAP.md` e conferir todos os links.

## 2026-11-11

### Splash — identidade Pluma e progresso real

- Nova splash em `mainerp/ui/splash_pluma.py` (`PlumaSplash`), no lugar do desenho que ficava em `show_splash` (`mainerp/app.py`): símbolo e marca Pluma, lema, barra de progresso reta, mensagem da etapa, percentual e rodapé com `© Digital Solutions - <APP_NAME> v<APP_VERSION>`.
- Segue `docs/identidade_visual.md`: cores apenas por tokens de `CoresTema` do tema ativo (sem hexadecimais no componente), superfícies planas, bordas retas e sem gradientes decorativos. A barra usa `border` no trilho e `accent_text` no preenchimento, que mantém contraste nos dois temas. O símbolo é o `pluma-simbolo.svg` da identidade, embutido no módulo e desenhado com `QSvgRenderer`; por isso a release não depende de arquivos de assets, já que o gerador inclui apenas os arquivos Python dos pacotes.
- Progresso sem simulação: `PlumaSplash.atualizar(mensagem, percentual=None)` só move a barra quando o percentual é informado e nunca a faz retroceder. Em `app.py`, as etapas iniciais informam valores fixos (0, 5, 10, 15 e 20%) e as 8 telas da `MainWindow` dividem a faixa de 20% a 100%: `percentual_carregamento_telas` converte a mensagem `Carregando tela i/n: ...` na fração de telas já concluídas. Mensagens sem posição não alteram a barra. A `MainWindow` não foi alterada. Os pesos das etapas são uma escolha de projeto, não uma medição de tempo.
- O tamanho lógico (450 × 300) e o desenho na escala da tela principal foram preservados. `show_splash` não recebe mais parâmetros.
- `tests/test_splash.py` reescrito para a nova splash (tema, escalas 100%, 125% e 150%, barra, percentual que não retrocede e conversão das mensagens de tela).
- Verificação: no Windows, o `verificar.bat` foi aprovado (Ruff e 369 testes aprovados, com 1 ignorado), incluindo os 7 testes de `tests/test_splash.py`. Antes disso, Ruff e esses testes tinham sido executados em um ambiente isolado com módulos do projeto substituídos por stubs. Pendente: conferência visual em 100%, 125% e 150% no Windows.
- O rodapé com o copyright, que a splash anterior exibia, foi mantido.

### Launcher — janela de atualização com progresso real

- A janela `Aviso` de `distribuicao/launcher.pyw` (tkinter, só biblioteca padrão) foi redesenhada: 320 × 180, sem barra de título, borda de 1 px, símbolo Pluma, barra reta e a palavra "Atualizando". O texto detalhado das etapas passou a ir apenas para o `launcher.log`.
- Tema fixo claro. O launcher não importa o aplicativo; as quatro cores usadas são constantes copiadas de `CLARO` (`surface`, `border`, `accent_text`, `text_secondary`), com comentário no código. O símbolo é um PNG com transparência (47 × 49 px) embutido, pois o tkinter não lê SVG.
- Progresso real, informado por uma variável do módulo (`_aviso_progresso`) para não mudar as assinaturas de `baixar`, `extrair_seguro`, `instalar_dependencias` e `instalar_zip`: download em bytes recebidos (quando o servidor informa `Content-Length`), extração arquivo a arquivo, e o `pip` lido linha a linha, com um passo por "Collecting ..." e conclusão em "Successfully installed". O total de pacotes do `pip` só é conhecido no fim da coleta; por isso o avanço da coleta usa os pacotes diretos de `requirements.txt` como base e a instalação em si conta como uma etapa única. As faixas por etapa são uma escolha de projeto, não uma medição de tempo.
- Caminhos originais preservados: sem janela ativa (ou com um objeto sem `progresso`), `baixar` usa `shutil.copyfileobj`, `extrair_seguro` usa `extractall` e `instalar_dependencias` usa `subprocess.run`, como antes. A janela só é registrada em `atualizar()` e é liberada no `finally`.
- Novo `tests/test_launcher_progresso.py` (download por servidor local, extração, caminho inseguro, `pip` simulado com sucesso e falha, caminho original sem janela, registro da janela em `atualizar()` e janela tkinter real, ignorada sem ambiente gráfico).
- Verificação: no Windows, o `verificar.bat` foi aprovado (Ruff e 369 testes aprovados, com 1 ignorado), incluindo os 9 testes de `tests/test_launcher_progresso.py` com a janela tkinter real. Antes disso, no Linux com tkinter 8.6 sob Xvfb, a captura da janela foi conferida visualmente. Pendente: instalação isolada com atualização real (`pip` e pacote) e conferência da janela em 100%, 125% e 150%. O `.pyw` não é coberto pelo Ruff.
- A nova janela só chega às instalações existentes quando o launcher for reinstalado pelo instalador; uma atualização de código não substitui o launcher.

## 2026-11-09

### Preparação da release 0.10.9

- Preparada a versão 0.10.9 com as alterações posteriores à 0.10.7; a tag 0.10.8 não será reutilizada.
- O pipeline usa a seção da versão no CHANGELOG para as notas da release e interrompe a publicação se ela não tiver itens.
- Publicação concluída: Ruff e testes passaram no GitHub Actions em Linux. Downloads públicos, assinaturas e hashes dos pacotes foram verificados; o ZIP de código-fonte não contém a prévia HTML.

### Restauração — concorrência em WAL

- A disputa entre o fim da reserva de escrita e a obtenção da trava exclusiva podia gerar `SQLITE_BUSY`. A aquisição é repetida dentro do prazo de 30 segundos, fechando a conexão anterior; erros diferentes e o esgotamento do prazo continuam sendo informados.
- Adicionado teste que força a disputa e verifica snapshot, banco restaurado e remoção da pendência, além de testes para prazo e outros erros.
- Validação no Windows: Ruff aprovado e 359 testes aprovados, com 1 ignorado. No WSL, 10 disputas WAL forçadas passaram na aquisição da trava; a suíte completa do CI Linux não foi executada.

### Tentativa de release 0.10.8

- Removida a prévia HTML de paleta apontada pelo Microsoft Defender no ZIP do código-fonte e ajustada a referência na documentação. A causa da detecção não foi confirmada.
- A publicação foi interrompida: no GitHub Actions, o teste de restauração concorrente em WAL falhou com `database is locked`. A tag `v0.10.8` permanece, mas a release não foi publicada.

### Interface — ajustes em diálogos

- **Recuo de campos numéricos:** aplicado `setTextMargins` (`DIMENSOES.espacamento`) no editor interno dos spinboxes em venda, condicional (desconto, quantidade e preço), recebimento, parcelas do pagamento e diálogos de quantidade/preço de custo/preço de venda do pedido; `solicitar_preco_venda` ganhou o parâmetro `ajustar_recuo_campo`.
- **Tamanho de janelas:** `FornecedorSelectionDialog` (médio) e `ProdutoSelectionDialog` (grande) passaram a usar `DialogSizeMixin`.
- **Pagamento:** removido o frame "Valor de Entrada"; `valor_entrada` permanece 0.0 em `get_dados()` por compatibilidade com a venda.
- **Ícone:** removido `setWindowIcon` relativo de `ClienteSelectionDialog`, que anulava o ícone da aplicação na barra de título.
- **Pedido:** botões do diálogo "Frete e Desconto" trocados por `QDialogButtonBox`, igual aos demais diálogos.
- **Teste Windows:** a asserção de largura da coluna Nome agora verifica a regra de dimensionamento responsivo, em vez de exigir largura fixa.
- **ROADMAP:** Fase D ajustada com validação de estados visíveis de contraste e conferência de navegação por teclado.

### Release 0.10.7

- Inclui as melhorias de interface, os ajustes em diálogos, a inclusão de recursos visuais no pacote e a validação isolada dos instaladores e do launcher registrados abaixo.
- A tag `v0.10.6` não publicou a release porque dois testes de diálogo falharam no runner Linux ao acessar `QLineEdit.cursorRect()`. O teste agora verifica as margens públicas do editor; a tag não foi reutilizada.
- Validação local em Windows: Ruff passou; pytest aprovou 353 testes (1 ignorado).

## 2026-11-08

### Alterações após 0.10.5

- **Interface:** implementados tokens centralizados para temas claro e escuro, preferência de tema persistida e estilos consolidados. Foram adicionados ícones SVG com licenças, componentes compartilhados para formulários e listagens, navegação mais compacta e ajustes de rolagem e dimensionamento de diálogos.
- **Empacotamento:** o gerador de releases passou a incluir os novos ícones e arquivos de licença; Pillow foi declarado nas dependências.
- **Testes e validação:** ajustes em testes de backup e atualização; validação em diretórios isolados no Windows dos instaladores 0.10.4/0.10.5 e do launcher, cobrindo atualização assinada, abertura da versão nova, preservação de banco fictício, rollback após falha, reparo de `cryptography` e preservação do launcher quando a instalação de dependências falha.

As alterações foram consolidadas na release 0.10.7. Os itens ainda pendentes permanecem no `ROADMAP.md`.
