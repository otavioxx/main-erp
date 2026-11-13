# Histórico de Desenvolvimento

## 2026-11-12

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
