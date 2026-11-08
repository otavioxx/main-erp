# Roadmap do MainERP

Baseado em uma análise estática do código (≈ 25,5 mil linhas; cobertura automatizada
inicial). Cada fase deixa o sistema funcionando; não faça duas fases ao mesmo tempo.

## Fase 0 — Higiene segura (1 a 2 dias)

- [x] Commitar o modelo de distribuição atual e criar a tag da primeira versão.
- [x] `ruff check . --select F401,F841,F541 --fix`: remove imports e variáveis não usados.
- [x] Remover módulos que nenhum arquivo importa (um commit só, fácil de reverter):
      `views/base_view.py`, `utils/table_utils.py`, `utils/produto_validation.py`,
      `utils/config_backup.py`, `utils/duplicata_utils.py`, `utils/resources.py`,
      `models/item_pedido.py`, `dialogs/frete_desconto_dialog.py` (≈ 1,5 mil linhas).
- [x] Remover `PRAGMA timezone` em `mainerp/data/database.py` (não existe no SQLite, não faz nada).
- [x] Adicionar `ruff` e um `pyproject.toml` com a configuração.

## Fase 1 — Rede de segurança (1 a 2 semanas)

- [x] **Logging central** (arquivo rotativo em `dados\logs`) no lugar dos ≈ 68 `print()`.
- [x] Auditar os 164 `except Exception` amplos: restringir os tipos quando seguro e
      registrar as falhas com o logging central. Seis casos previsíveis foram estreitados;
      os demais permanecem amplos em limites de recuperação/propagação.
- [x] **Testes com pytest** para os principais cálculos de venda, criação de parcelas,
      operações/verificação de estoque, regras de inativação de produto e exclusão de venda,
      e migrações do banco novo e legado. Expandir a cobertura em `mainerp/domain/utils/`
      e `mainerp/data/models/` conforme novas mudanças.
- [x] Script `verificar.bat` que roda Ruff e pytest antes de cada release.
- [x] Backup automático diário em `dados\backups`, independente do backup manual do usuário,
      com retenção de 30 dias. A opção de backup manual para pasta externa/nuvem foi mantida.

## Fase 2 — Camada de dados (2 a 3 semanas)

- [x] Centralizar as conexões SQLite em `obter_database()` (gerenciador por thread) e
      adicionar transações com commit/rollback e savepoints em `mainerp/data/database.py`.
      Models, utilitários, telas e relatórios usam o gerenciador compartilhado.
- [x] Tirar o SQL das telas (`mainerp/ui/views/recebimento_view`, `condicional_view`,
      `venda_view`, `pedido_view`) para `mainerp/data/models/` e repositórios.
- [x] **Dinheiro**: concluir a migração dos 19 campos monetários `REAL` do esquema atual
      para centavos inteiros (`INTEGER`), incluindo cálculos e leituras da aplicação.
      - [x] Migração 3 cria colunas `*_centavos`, converte os dados existentes e mantém
            os centavos sincronizados em escritas antigas; cálculos e leituras ainda
            precisam passar a usar os campos inteiros.
      - [x] Cálculos centrais de venda agora operam em centavos; os métodos legados
            continuam retornando valores em reais para preservar os contratos da UI.
      - [x] O model de venda grava e recarrega os valores monetários pelos campos
            `*_centavos`, mantendo as colunas antigas preenchidas para compatibilidade.
      - [x] Itens de venda são gravados em centavos e lidos pelo repositório inteiro,
            convertendo para reais apenas na interface legada de tuplas.
      - [x] A criação de parcelas divide o financiado em centavos e aloca qualquer
            resto na última parcela, garantindo que a soma corresponda ao total.
      - [x] Pagamento parcial sem parcelas abertas cria uma nova parcela para o
            saldo pendente, com vencimento 30 dias após a parcela quitada.
      - [x] Recebimentos usam centavos para consultar e registrar valores pagos;
            a UI continua recebendo os mesmos valores em reais.
      - [x] Condicionais persistem desconto e preço dos itens em centavos, leem
            os campos inteiros e calculam o subtotal/total sem aritmética em ponto flutuante.
      - [x] Produtos e pedidos persistem e consultam preços, descontos, frete e totais
            pelos campos inteiros; os atributos e tuplas legados continuam em reais.
      - [x] Itens e recebimentos de pedidos calculam e atualizam preços/subtotais em
            centavos, incluindo a atualização do custo, preço de venda e estoque.
      - [x] Diálogos, agregações e relatórios usam centavos nos cálculos e leituras;
            conversões para reais ficam nas fronteiras da interface e dos relatórios.
- [x] Índices nas colunas mais filtradas (cliente, data, status); `PRAGMA foreign_keys`
      permanece ativo.

## Fase 3 — Reestruturação (2 a 4 semanas)

- [x] Corrigir os campos de inserção de valores da venda e da condicional, incluindo
      a exibição do valor no diálogo "Preço de Venda"; aceitar vírgula ou ponto decimal,
      separador de milhar e prefixo `R$`.
- [x] Criar o pacote `mainerp/` com núcleo, dados, domínio, UI e relatórios; manter `main.py`
      na raiz para o launcher.
- [x] Unificar as implementações de `NumericTableWidgetItem` em `mainerp/ui/table_items.py`,
      preservando a ordenação de números, moedas e valores vazios nas telas e diálogos.
- [x] Quebrar os arquivos grandes de diálogos e telas em componentes separados de
      layout, entrada, operações, filtros, ações e persistência.
- [x] Avaliar um componente compartilhado para as telas de listagem: preferir funções
      pequenas e composição, em vez de uma `BaseTableView` que concentre navegação,
      filtros e regras de negócio. Clientes, fornecedores, pedidos e condicionais
      compartilham seleção de linha única, edição bloqueada, cores alternadas e altura
      fixa; vendas inicia com ordenação desligada, produtos preserva a ordenação e tem
      menu contextual, e recebimentos tem lógica própria de altura. Já existem
      `TableScrollNavigationMixin`, `fixar_altura_linhas` e `NumericTableWidgetItem`.
- [x] Extrair a configuração comum de `QTableWidget` em clientes e fornecedores,
      preservando colunas, cabeçalhos, seleção, sinais e ordem de configuração, com
      testes Qt de ordenação, navegação, seleção, altura e estilos.
- [x] Estender a configuração comum de listagens a pedidos e condicionais; compartilhar
      apenas a interação em vendas, produtos e recebimentos, mantendo estilos, altura,
      timers, ordenação inicial e sinais próprios. Testes Qt verificam cada tela.
- [x] Splash: substituir os atrasos artificiais por progresso das etapas reais de
      inicialização e informar o carregamento individual das oito telas.

Estrutura alvo:

```
MainERP/
  main.py                 # fino: bootstrap compatível com o launcher
  mainerp/
    app.py
    core/        config.py, paths.py, logging, exceções
    data/        database.py, migrações, models/
    domain/      regras de negócio e utilitários
    ui/          views/, dialogs/, mixins/, styles.py
    reports/     geração de PDF
  tests/
  distribuicao/
  docs/
  pyproject.toml
```

> O launcher abre `main.py` na raiz do release; mantenha esse arquivo fino.

## Fase 4 — Operação e atualização online

- [x] Manter o `CHANGELOG.md` com o histórico das versões 0.07 e 0.08.
- [x] Adotar versionamento semântico estrito (MAJOR.MINOR.PATCH).
- [x] Assinar releases com Ed25519 e validar assinatura, SHA256 e versão no launcher.
- [x] Implementar no launcher a consulta opcional do manifesto, o download e a validação
      SHA256 dos pacotes de atualização.
- [x] Publicar `MainERP-0.09.zip` e `version.json` no GitHub público e validar o endpoint
      latest; o ZIP baixado confere com o SHA256 do manifesto.
- [x] Publicar o padrão do endpoint no launcher/instalador e validar a atualização online
      isolada de 0.08 para 0.09; instalações antigas podem precisar do bootstrap do launcher.
- [x] Gerar manualmente o ZIP e o manifesto `version.json` com SHA256 por
      `distribuicao/criar_release.py`, e executar Ruff/pytest por `verificar.bat`.
- [x] Automatizar o pipeline de release no GitHub Actions (Ruff, testes, ZIP e SHA256).
- [x] Tela "Sobre" mostrando versão, data e histórico.

## Fase 4.1 — Pontos de atenção identificados na revisão

Os itens abaixo são propostas de trabalho, não correções já aplicadas. Priorizar proteção
dos dados e recuperação antes das melhorias estruturais. Os testes de backup e restauração
devem usar apenas bancos e instalações temporários, nunca dados de produção.

### Prioridade alta — backup e restauração

- [x] Validar o backup manual e sua recuperação nos cenários definidos: snapshot com
      transação concorrente em WAL, falhas simuladas na compactação e publicação,
      preservação do backup anterior e restauração do ZIP na inicialização da aplicação.
      Nomes únicos evitam a sobrescrita de dois backups criados no mesmo segundo.
      Falhas simuladas não equivalem a testar falhas reais de hardware ou energia;
      os demais riscos de restauração e recuperação externa permanecem nos itens abaixo.
- [x] Redesenhar a restauração em `mainerp/data/db_utils.py` e
      `mainerp/ui/dialogs/restore_backup_dialog.py`: coordenar o encerramento das conexões
      e do backup automático. A restauração agora é preparada e aplicada antes da abertura,
      após snapshot SQLite anterior; falhas bloqueiam a abertura e preservam a pendência.
      O launcher precisa ser atualizado pelo instalador. A validação verifica integridade,
      tabelas, colunas, centavos inteiros e chaves estrangeiras declaradas após migrar
      uma cópia; não verifica relacionamentos não declarados. Testes terminam
      o processo durante cópia em WAL e journal padrão e verificam a recuperação.
      Falhas simuladas em fsync, publicação e cópia preservam a pendência e permitem
      repetição; testes em WAL e journal padrão verificam a integridade. Preparações e
      aplicações concorrentes não substituem nem aplicam duas vezes a pendência. A
      aquisição da trava reserva a escrita antes do modo exclusivo; testes exercitam
      aplicações simultâneas em WAL e journal padrão. A restauração mantém bloqueio
      SQLite exclusivo entre o snapshot e a validação;
      testes verificam escritores externos ativos e bloqueados antes e depois da cópia.
      Ainda é necessário validar os demais tipos, restrições e regras de negócio;
      falhas reais de hardware e processos que alterem arquivos fora do SQLite não são
      cobertos pelos testes.
- [x] Não prometer reversão bem-sucedida quando a recuperação também falhar:
      a nova restauração preserva snapshot anterior e pendência caso a aplicação falhe;
      falhas antes da cópia e após sua conclusão (confirmação ambígua simulada) mantêm
      snapshot e pendência, bloqueiam a abertura e permitem nova tentativa; a mensagem
      não afirma que houve reversão e orienta preservar os arquivos. Testes terminam
      o processo durante a cópia e após sua conclusão em WAL e journal padrão e
      verificam a recuperação. Ainda faltam falhas reais de hardware/energia e
      interrupções durante a confirmação nativa do SQLite.
- [x] Tratar falhas de persistência de `backup_settings.json` na interface. Salvar o
      caminho preserva os demais campos e rejeita configurações inválidas; falhas ao
      salvar o caminho ou metadados do backup são informadas ao usuário.
- [x] Testar e corrigir o ciclo de fechamento/backup em `MainWindow`: o agendamento
      volta a funcionar se o fechamento for interrompido e aguarda backups em andamento.
      Falhas de agendamento e retenção são informadas; a barra de status mostra a idade
      do último arquivo automático e o resultado nesta sessão. Arquivos encontrados na
      inicialização não são apresentados como novamente verificados.

### Prioridade alta — atualizações e distribuição

- [ ] Isolar ou recuperar as dependências no rollback: `launcher.pyw` instala dependências
      no runtime compartilhado na instalação inicial e o rollback troca apenas o código.
      O launcher atualizado cria runtimes por release; testes usam dependências locais
      incompatíveis, falha parcial do pip e rollback. Instalações existentes precisam do
      bootstrap. Validar o fluxo completo de distribuição no ambiente do cliente.
- [ ] Tornar a trava de atualização resistente a operações demoradas e interrupções:
      o launcher atualizado usa trava do sistema operacional, sem prazo de expiração;
      teste com processos concorrentes verifica que uma trava antiga permanece ativa.
      Testar interrupção abrupta do processo e tratar o diretório de trava legado.
- [ ] Revisar o conteúdo de cada release antes da publicação. O gerador agora limita
      arquivos da raiz e pacotes Python, com testes de exclusão de caches e dados; ele
      ainda inclui arquivos Python locais presentes nos diretórios permitidos.
- [ ] Corrigir o destino personalizado: o instalador agora confere se a versão ativa é
      válida e não é anterior à versão solicitada, mesmo se o launcher ocultar uma falha.
      A opção `--destino` cria outra pasta de dados, mas o launcher não define
      `MAINERP_DATA` para ela; para novas instalações, usar o destino padrão. Uma correção deve
      preservar o local de dados de instalações existentes. Testar reinstalação,
      falha de pacote/dependências e uso do atalho com destino não padrão.
- [ ] Planejar a atualização segura do launcher fixo e a rotação da chave de assinatura,
      com migração de instalações antigas e procedimento de recuperação. Uma release de
      código não substitui `launcher.pyw`; testar também manifesto indisponível,
      assinatura ausente/inválida e compatibilidade de rollback com migrações do banco.

### Qualidade e manutenção

- [ ] Confirmar as alturas das listagens com diferentes fontes e escalas no Windows.
      A altura padrão agora é definida após os limites mínimo e máximo, evitando que
      o Qt nativo a limite ao mínimo anterior de 24 pixels.
- [ ] Aplicar uma política de formatação e integrá-la à verificação automatizada.
      `ruff check .` passou nesta revisão, mas `ruff format --check .` apontou seis
      arquivos; formatar separadamente de mudanças funcionais para facilitar a revisão.
- [ ] Corrigir o diagnóstico Pylance `reportArgumentType` em
      `tests/test_release_updates.py`, no carregamento de `SourceFileLoader`, mantendo
      a execução do teste em Windows e Linux. Não havia imports não resolvidos no
      interpretador selecionado durante esta revisão.
- [ ] Declarar e validar dependências usadas diretamente: relatórios importam `PIL`,
      mas Pillow não está listado diretamente em `requirements.txt`. Testar instalação
      limpa com as versões de Python suportadas e avaliar limites/pinos para builds
      reproduzíveis e atualizações seguras de dependências.
- [ ] Adicionar CI em pushes e pull requests, incluindo Windows e testes de instalação,
      inicialização, backup/restauração e atualização em ambiente isolado. O workflow
      atual executa Ruff e testes apenas ao enviar tags, em Ubuntu.
- [ ] Refatorar gradualmente componentes ainda extensos, como `produto_view.py`,
      `pedido_view.py`, `backup_dialog.py` e `restore_backup_dialog.py`, com testes de
      comportamento. Em `main_window.py`, reduzir a duplicação entre cadastro de botões,
      criação de views e atualização por aba, preservando a ordem, sinais e progresso.
- [ ] Revisar progressivamente os `except Exception` e os caminhos com falha silenciosa,
      priorizando backup, restauração e atualização; manter exceções amplas apenas em
      limites de recuperação justificados, com registro e sinalização ao usuário.

## Fase 4.2 — Relatórios e visualizador embutido

Prioridade atual do projeto, junto com a Fase 4.3. Os itens abaixo são propostas, não
alterações já aplicadas. Os itens de proteção de dados da Fase 4.1 continuam tendo
precedência sobre melhorias estruturais: decidir se esta fase começa depois deles ou em
paralelo. Os nove módulos de `mainerp/reports/` (≈ 4,9 mil linhas, ReportLab/Platypus)
repetem estilos, cabeçalho da empresa e tabelas, e o PDF pronto é aberto fora do sistema.
O frontend permanece em PyQt6/Qt Widgets (Fase 4.3): o `QPdfView` é o visualizador
escolhido e ser independente de Qt deixa de ser critério para o motor de geração; o peso
da instalação continua sendo.

- [ ] Prototipar o relatório de vendas (`mainerp/reports/print_relat_venda.py`) em
      HTML/CSS + Jinja2 e comparar o PDF com o atual: fidelidade visual, cabeçalho/rodapé
      e numeração de páginas, tabelas longas com quebra de página e instalação limpa no
      Windows sem dependências de sistema. Motores candidatos: QtWebEngine (`printToPdf`,
      assíncrono) e WeasyPrint (exige Pango/GTK no Windows). Manter o ReportLab refatorado
      como alternativa de menor risco. Registrar a escolha neste roadmap.
- [ ] Criar `mainerp/reports/engine.py` com `render_pdf(template, contexto) -> Path` e
      `mainerp/reports/templates/` com um `base.html` compartilhado (cabeçalho da empresa,
      estilos, tabela zebrada, rodapé), eliminando a repetição entre os módulos.
      As cores e a identidade visual seguem os tokens da Fase 4.3.
- [ ] Migrar um relatório por vez, cada módulo reduzido a consulta + contexto (centavos
      convertidos apenas na formatação): vendas, pedidos, condicionais, recebimentos,
      produtos, comprovante de recebimento e documentos individuais (venda, condicional,
      pedido). Cada migração com teste de geração (arquivo criado e não vazio, número de
      páginas, totais formatados) e comparação visual com o PDF anterior.
- [ ] Criar `mainerp/ui/dialogs/pdf_viewer_dialog.py` com `QPdfView`
      (`PyQt6.QtPdfWidgets`): zoom, ajustar à largura, navegação por página, busca,
      salvar como, abrir no programa externo e imprimir (renderizando as páginas do
      `QPdfDocument` em um `QPrinter`).
- [ ] Trocar a abertura externa pelo visualizador embutido. Os pontos de entrada são
      `ExportUtils.abrir_arquivo` (pedidos, condicionais e recebimentos) e
      `ProdutoView._abrir_arquivo`; manter "abrir externo" como botão e como alternativa
      se o visualizador falhar.
- [ ] Validar a impressão a partir do visualizador em impressoras reais e em tamanhos de
      página personalizados (etiquetas), no ambiente do cliente. Testes automatizados não
      cobrem drivers de impressora.
- [ ] Declarar as novas dependências em `requirements.txt` com limites de versão (Jinja2 e
      o motor escolhido, como `PyQt6-WebEngine` ou WeasyPrint) e validar instalação limpa e
      o runtime por release do launcher. Verificar se `distribuicao/criar_release.py`, que
      restringe os arquivos incluídos, empacota `mainerp/reports/templates/` (HTML/CSS) e
      testar o ZIP gerado.
- [ ] Remover o ReportLab de `requirements.txt` ao concluir a migração de todos os
      relatórios, revendo junto o item sobre Pillow na seção de qualidade.
- [ ] Avaliar a licença antes de distribuir o ERP a terceiros: o PyQt6 é GPL e o PySide6
      (LGPL) é a alternativa. Sem impacto para uso pessoal em um único PC.

Os relatórios gerenciais da Fase 5 devem reutilizar o `engine.py` e o `base.html`.

## Fase 4.3 — Identidade visual e padrão de ERP

Decisão: manter o frontend em PyQt6/Qt Widgets, sem migrar para web ou QML, e investir em
estilo e melhoria geral de usabilidade. A referência é o padrão visual de ERPs corporativos
consolidados (como o TOTVS): aparência plana, sóbria e densa, bordas retas e hierarquia por
contraste. É inspiração de padrão de uso; não copiar logotipos, ícones, textos ou outros
ativos de terceiros. Os itens abaixo são propostas, não alterações já aplicadas. Hoje o
tema é único e escuro (`mainerp/ui/styles.py`, fundo `#1a1a1a`), há 32 chamadas de
`setStyleSheet` em 12 arquivos, ≈ 77 cores hexadecimais fixas em `mainerp/ui/`,
`border-radius` em 23 pontos de `styles.py` e nos diálogos de backup e restauração, e
emojis como ícones (barra lateral em `main_window.py`, botões em `config_view.py`).

- [ ] Registrar os princípios de design em `docs/`: raio de borda zero, bordas de 1 px,
      sem sombras nem gradientes, controles e linhas compactos, cor usada para significado
      (acento, estado, alerta) e não para decoração, ícones monocromáticos e texto sóbrio.
- [ ] Definir a paleta de ERP conforme em docs/identidade_visual.md.
- [ ] Reestruturar `CoresPaleta` e `ConstrutorEstilos` para tokens (superfície, texto,
      borda, acento, estados, semânticas, altura de controle, espaçamento, raio igual a
      zero e fonte) com tema claro como padrão e o escuro como opção, e persistir a
      escolha nas configurações. Testes Qt aplicam cada tema e instanciam cada tela e
      diálogo sem erro.
- [ ] Mover os `setStyleSheet` soltos e as cores fixas de `mainerp/ui/` para o tema
      central, incluindo `backup_dialog.py` e `restore_backup_dialog.py`. Adicionar um
      teste que falhe se aparecer `border-radius` diferente de zero ou cor hexadecimal
      fora de `styles.py`, para o padrão não se perder nas próximas telas.
- [ ] Zerar os arredondamentos em botões, campos, listas suspensas, abas, tabelas, barras
      de rolagem, menus e diálogos. Avaliar `app.setStyle("Fusion")` como base, para o QSS
      renderizar igual entre versões do Windows.
- [ ] Substituir os emojis por ícones SVG monocromáticos de um conjunto livre (conferir a
      licença; Lucide, Phosphor e Material Symbols são opções), em `mainerp/ui/icons/`,
      coloridos pelo tema. Conferir se o gerador de release empacota esses arquivos.
- [ ] Definir a tela-modelo de ERP e aplicá-la às listagens: cabeçalho da tela, barra de
      ações com ícone e texto (Incluir, Alterar, Excluir, Pesquisar, Imprimir) e atalhos
      de teclado, filtros em painel, grade com cabeçalho destacado e linhas zebradas,
      totais no rodapé e barra de status com empresa e versão. Formulários com grupos de
      título reto e botões primário, secundário e de perigo consistentes.
- [ ] Revisar a navegação lateral (botões grandes com emoji) para um menu compacto de
      ERP, com item ativo marcado por faixa reta, e rever o tamanho base da fonte (hoje
      12 pt, Segoe UI) e a altura de linhas e controles para maior densidade, mantendo a
      legibilidade em 125% e 150%. Fazer junto com a confirmação das alturas das
      listagens, já prevista em "Qualidade e manutenção".
- [ ] Prototipar antes de estender: aplicar o tema novo a Clientes e ao diálogo de cliente,
      capturar imagens em 100%, 125% e 150% e só então seguir. Ordem sugerida: janela
      principal e navegação, listagens, diálogos de entrada, diálogos de relatório e, por
      fim, configurações e backup.
- [ ] Alinhar os relatórios em PDF à mesma identidade (cabeçalho, cores, tabela), usando os
      mesmos tokens no `base.html` da Fase 4.2. Definir a paleta antes de migrar os
      templates.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
