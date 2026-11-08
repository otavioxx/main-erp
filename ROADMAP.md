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

Os itens marcados registram o que já foi feito; os pendentes separam validações e riscos
remanescentes. Priorizar recuperação e atualização antes das melhorias estruturais, sem
exigir testes destrutivos de hardware para prosseguir. Usar bancos, instalações e dados
temporários nos testes, nunca dados de produção.

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
      do último arquivo automático elegível e o resultado nesta sessão. A verificação de
      integridade do arquivo recente ocorre em segundo plano, conforme item abaixo.
- [x] Orientar uma rotina simples de cópia externa e teste periódico de restauração:
      `docs/backup_recuperacao.md` descreve o conteúdo e os limites dos backups e um
      procedimento manual com dados isolados. Teste automatizado cria um ZIP em pasta
      externa simulada e restaura em dados temporários separados na inicialização.
      Falta validar o procedimento em uma instalação isolada com o instalador e o
      launcher. A verificação periódica das cópias reais permanece operacional.
- [x] Evitar que um backup manual recente ausente ou corrompido dispense o aviso ao
      fechar: o ZIP e o hash disponível são verificados antes de dispensar o diálogo.
      Testes cobrem remoção, corrupção, hash divergente e destino indisponível simulado;
      o usuário recebe aviso e pode escolher outra pasta para um novo backup.
- [x] Verificar em segundo plano a integridade SQLite do backup automático recente;
      avisar e tentar outra cópia se estiver inválido ou inacessível. Datas futuras
      geram alerta e suspendem a retenção sem bloquear novos backups. Testes cobrem
      falhas, repetição e publicação concorrente sem sobrescrever arquivos. Alterações
      de relógio sem arquivos futuros e regras de negócio não são totalmente detectáveis.

### Prioridade alta — atualizações e distribuição

- [x] Isolar dependências de atualizações em runtimes por release e testar rollback,
      falha parcial de instalação e versões incompatíveis. A instalação inicial ainda
      usa o runtime principal; instalações antigas precisam atualizar o launcher.
- [x] Usar trava do sistema operacional, sem expiração por tempo. Testes cobrem
      concorrência, idade da trava e liberação após saída abrupta do processo.
- [x] Restringir o conteúdo do ZIP de release a arquivos de runtime e pacotes
      explicitados, com testes de exclusão de caches e dados. O gerador ainda aceita
      qualquer arquivo Python presente nos diretórios de pacotes permitidos.
- [x] Preparar `cryptography` no runtime principal pelo instalador 0.10.5, inclusive
      em instalações existentes; testes cobrem o preparo e a falha. A instalação pela
      release de código não atualiza o instalador nem o launcher fixo.
- [x] Exibir novidades do histórico na primeira abertura após atualização pelo launcher,
      com registro por versão após fechar; falhas são avisadas e não impedem nova tentativa.
- [ ] Redesenhar a janela de espera do launcher com a identidade visual e progresso real
      quando mensurável, ou indicador indeterminado responsivo. O launcher usa Tkinter,
      executa operações bloqueantes e só é substituído pelo instalador; planejar testes
      de falhas, atualização e compatibilidade antes de alterar esse fluxo.

### Rota pendente — operação e segurança

1. [x] Validar em diretórios isolados no Windows os instaladores publicados 0.10.4 e
       0.10.5 e o launcher: atualização online assinada de 0.10.4 para 0.10.5,
       abertura da versão atualizada e preservação de banco fictício. Uma falha
       simulada de runtime na versão nova reativou e abriu a anterior. Sem
       `cryptography`, houve aviso e preservação da versão anterior; o instalador
       0.10.5 reparou o runtime. Com instalação de dependências bloqueada, informou
       a falha e preservou o launcher existente. Os avisos foram capturados em
       console; a interface foi aberta offscreen e sem criar atalhos.
   - [ ] Complementar em Windows limpo ou máquina virtual: testar destino padrão,
         atalhos e apresentação visual dos avisos, sem dados de produção. A validação
         em diretórios isolados não comprova esses aspectos nem uma falha real de rede.
2. [ ] Validar uma cópia externa e sua restauração em instalação isolada com instalador
       e launcher, conferindo registros e totais. Manter a rotina periódica descrita em
       `docs/backup_recuperacao.md`; não usar dados de produção nos testes automatizados.
3. [ ] Definir um procedimento seguro para a trava legada `.update.lock`, que atualmente
       adia atualizações enquanto existir. Distinguir instalação antiga ativa de resíduo
       antes de qualquer remoção; testar concorrência e recuperação sem apagar uma trava
       em uso.
4. [ ] Corrigir ou restringir explicitamente `--destino`: o instalador cria uma pasta
       de dados no destino, mas o launcher não define `MAINERP_DATA` para ela. Preservar
       o local de dados de instalações existentes e testar reinstalação, falhas e atalho
       com destino não padrão. Até lá, usar o destino padrão para instalações novas.
5. [ ] Planejar atualização segura do launcher fixo e eventual rotação da chave de
       assinatura, com migração de instalações antigas e recuperação. Já há testes de
       assinatura ausente, inválida e pacote alterado; complementar com manifesto
       indisponível e rollback após migrações do banco, sem enfraquecer a assinatura.
6. [ ] Antes de cada publicação, revisar o conteúdo efetivo do ZIP e do instalador,
       versões, hashes e assinaturas; os testes de seleção não excluem automaticamente
       todos os arquivos Python locais em diretórios permitidos. Considerar automatizar
       essa conferência se a rotina passar a ser frequente.
7. [ ] Avaliar gradualmente validações adicionais de tipos, restrições e regras de
       negócio na restauração, com casos representativos de bancos legados. Os testes
       atuais não reproduzem falhas reais de hardware/energia nem interrupções na
       confirmação nativa do SQLite; documentar limites, sem alegar garantia total.

### Manutenção relacionada

- [ ] Declarar e validar Pillow como dependência direta enquanto os relatórios importarem
      `PIL`; testar instalação limpa e compatibilidade com as versões de Python usadas.
- [ ] Confirmar alturas das listagens com fontes e escalas diferentes no Windows,
      em conjunto com o protótipo visual da Fase 4.3.

## Fase 4.2 — Relatórios e visualizador embutido

Os nove módulos atuais geram PDFs com ReportLab/Platypus e usam Pillow; a abertura é
externa. Não foram encontrados motor de templates nem visualizador PDF embutido.
Esta fase pode começar após as validações prioritárias de instalação e recuperação da
Fase 4.1, e avançar junto com a Fase 4.3 sem depender de uma troca de motor. Para uso
pessoal, manter o ReportLab é a alternativa inicial de menor mudança.

### Rota proposta

1. [ ] Inventariar os nove relatórios, seus pontos de abertura, tamanhos de página,
       totais, logos e impressão. Criar uma linha de base de geração e comparação visual
       em dados isolados, incluindo tabelas longas e valores em centavos.
2. [ ] Prototipar `QPdfView` em diálogo independente, mantendo ReportLab: navegação,
       zoom, ajuste de largura, busca, salvar como, abrir externamente e impressão com
       `QPdfDocument`/`QPrinter`. Verificar disponibilidade e instalação no Windows,
       falhas de carregamento e alternativa externa, sem substituir o fluxo existente.
3. [ ] Integrar gradualmente o visualizador após o protótipo: chamadas de
       `ExportUtils.abrir_arquivo` incluem vendas, pedidos, condicionais e recebimentos;
       produtos usa `ProdutoView._abrir_arquivo`. Preservar abertura externa como opção
       e alternativa em falhas, e testar os pontos de entrada e arquivos gerados.
4. [ ] Validar impressão em impressoras reais e tamanhos personalizados, incluindo
       etiquetas, quando aplicável. Registrar limites: testes automatizados não cobrem
       drivers ou todas as impressoras.
5. [ ] Comparar um protótipo de vendas em HTML/CSS + Jinja2 com o ReportLab atual e uma
       refatoração compartilhada em ReportLab. Avaliar fidelidade, paginação, tabelas
       longas, peso e instalação limpa no Windows; QtWebEngine e WeasyPrint são candidatos,
       não decisões. Registrar a escolha antes de migrar ou adicionar dependências.
6. [ ] Conforme a escolha, extrair componentes compartilhados de cabeçalho, estilos e
       tabelas e migrar um relatório por vez, preservando centavos e resultados. Se for
       escolhido HTML, definir `engine.py` e templates compartilhados; alinhar cores
       aos tokens da Fase 4.3. Testar geração, páginas, totais e comparação visual.
7. [ ] Se houver novas dependências ou arquivos HTML/CSS, declará-los com limites de
       versão e incluí-los explicitamente no gerador de release; testar instalação limpa,
       runtime por release e conteúdo do ZIP. Remover ReportLab ou Pillow somente quando
       não houver mais uso direto ou indireto necessário.
8. [ ] Avaliar as condições de licença aplicáveis ao PyQt6 e às dependências antes de
       distribuir a terceiros; considerar alternativas apenas se necessário.

Os relatórios gerenciais da Fase 5 devem reutilizar os componentes compartilhados
efetivamente escolhidos, sem pressupor templates HTML.

## Fase 4.3 — Identidade visual e padrão de ERP

Decisão: manter o frontend em PyQt6/Qt Widgets, sem migrar para web ou QML, e investir em
estilo e melhoria geral de usabilidade. A referência é o padrão visual de ERPs corporativos
consolidados (como o TOTVS): aparência plana, sóbria e densa, bordas retas e hierarquia por
contraste. É inspiração de padrão de uso; não copiar logotipos, ícones, textos ou outros
ativos de terceiros. A fundação dos temas claro e escuro já foi aplicada, mas a
validação visual e a migração de estilos locais continuam pendentes.

- [x] Registrar os princípios de design em `docs/identidade_visual.md`: raio de borda zero, bordas de 1 px,
      sem sombras nem gradientes, controles e linhas compactos, cor usada para significado
      (acento, estado, alerta) e não para decoração, ícones monocromáticos e texto sóbrio.
- [x] Definir a paleta de ERP em `docs/identidade_visual.md`, com tokens para os temas
      claro e escuro. A implementação e a validação de contraste continuam pendentes.
- [x] Reestruturar `CoresPaleta` e `ConstrutorEstilos` para tokens (superfície, texto,
      borda, acento, estados, semânticas, altura de controle, espaçamento, raio igual a
      zero e fonte) com tema claro como padrão e o escuro como opção, e persistir a
      escolha nas configurações. Testes Qt aplicam cada tema e instanciam cada tela e
      diálogo sem erro. A escolha passa a valer na próxima abertura; configurações
      antigas sem preferência mantêm o escuro.
- [x] Consolidar os `setStyleSheet` locais no tema central, incluindo backup,
      restauração e itens das tabelas de vendas e produtos. Estados dinâmicos são
      repolidos ao mudar; testes verificam cores, altura das linhas e ausência de
      estilos locais, cores hexadecimais fixas e raios fora dos módulos de tema.
- [x] Adotar Fusion e raio zero no QSS dos controles, abas, tabelas, barras, menus e
      conteúdo dos diálogos. Testes cobrem temas, interação e escalas Qt simuladas;
      inspeção de controles em Windows foi feita a 100%. A seta das listas usa Fusion.
  - [x] Validar visualmente em 125% e 150% no Windows. Bordas externas de janelas e
        diálogos nativos de arquivos são controladas pelo sistema operacional e podem
        continuar arredondadas; não trocar por janelas sem moldura sem avaliar o impacto.
        Em 125% reais no monitor principal (1920 × 1080), foram inspecionadas visões
        gerais das oito telas na janela maximizada, nos dois temas, com banco vazio
        isolado; os botões de navegação mudaram para as telas esperadas. Clientes e
        seu diálogo também foram inspecionados isoladamente com dados fictícios. Com
        largura de 1000 unidades Qt, a coluna “Nome” ficou com 34–36 unidades e
        cortou o cabeçalho e o nome; com 1400, ficou com 434 unidades e o exemplo
        apareceu completo. A coluna usa `Stretch` e as demais têm larguras fixas;
        investigar a distribuição. O diálogo coube na área disponível nessa posição,
        mas a captura não incluiu a moldura nativa. Foram ainda inspecionados os
        conteúdos de backup, restauração, fornecedor, pedido, produto e nova venda
        isolados, sem operações reais, nos dois temas. Em Nova Venda, também com a
        janela principal como pai, a geometria externa ultrapassou a área disponível
        em 13 unidades Qt na parte inferior; investigar o impacto da barra de tarefas.
        Em 150% reais no mesmo monitor, a área disponível era 1280 × 672 unidades
        Qt. Inspeção geral das oito telas maximizadas e de sete diálogos, nos dois
        temas, com banco isolado: em Clientes, a coluna “Nome” tinha 74 unidades e
        abreviou um nome longo. Com dados fictícios, busca, limpeza, F11 e seleção
        responderam nos dois temas; ao redimensionar a tela isolada de 1000 para
        1200 unidades Qt, a coluna passou de 34–36 para 234 unidades.
        Com os diálogos abertos sobre a janela principal,
        os botões OK e Cancelar de Fornecedor ficaram totalmente abaixo da área
        disponível; em Nova Venda e Restauração, os botões inferiores ficaram
        parcialmente fora dela. A geometria externa de Cliente e Pedido também
        ultrapassou a área, mas seus botões medidos ficaram dentro. Investigar e
        corrigir posicionamento e dimensionamento; capturas de conteúdo não mostram
        a composição com a barra de tarefas nem as molduras nativas. O diálogo de
        Fornecedor impunha altura mínima de 750 unidades; o dimensionador compartilhado
        de Nova Venda usava a geometria total do monitor, não sua área disponível;
        Restauração também centralizava pela geometria total.
        Correções aplicadas: nome de Clientes com largura inicial de 200 unidades,
        redimensionamento manual e rolagem horizontal; formulários de Cliente e
        Fornecedor com rolagem e ações fixas; dimensionador compartilhado e
        Restauração usam a área útil do monitor. Testes no backend Windows, com
        escalas Qt simuladas de 125% e 150%, cobrem os botões e a rolagem nesses
        diálogos. Revalidar as correções nas escalas reais: o monitor retornou a
        100% antes da aplicação das alterações.
        Permanecem pendentes a inspeção detalhada das demais telas e diálogos,
        redimensionamento, interações e diálogos nativos nas duas escalas, além de
        validar novamente após as correções. Simulações Qt não substituem a validação
        real do Windows.
- [x] Substituir emojis por ícones SVG monocromáticos Lucide 0.468.0 na navegação e nas
      ações, com cores do tema e licenças ISC/MIT incluídas no instalador e na release.
      Mensagens usam texto explícito e avisos nativos. Inspeção nos dois temas a 100%;
      a conferência visual em 125% e 150% permanece pendente.
- [ ] Definir a tela-modelo de ERP e aplicá-la às listagens: cabeçalho da tela, barra de
      ações com ícone e texto (Incluir, Alterar, Excluir, Pesquisar, Imprimir) e atalhos
      de teclado, filtros em painel, grade com cabeçalho destacado e linhas zebradas,
      totais no rodapé e barra de status com empresa e versão. Formulários com grupos de
      título reto e botões primário, secundário e de perigo consistentes.
- [ ] Revisar a navegação lateral (botões grandes) para um menu compacto de
      ERP, com item ativo marcado por faixa reta, e rever o tamanho base da fonte (hoje
      12 pt, Segoe UI) e a altura de linhas e controles para maior densidade, mantendo a
      legibilidade em 125% e 150%. Fazer junto com a confirmação das alturas das
      listagens, prevista em "Manutenção relacionada" na Fase 4.1.
- [ ] Prototipar antes de estender: aplicar o tema novo a Clientes e ao diálogo de cliente,
      capturar imagens em 100%, 125% e 150% e só então seguir. Ordem sugerida: janela
      principal e navegação, listagens, diálogos de entrada, diálogos de relatório e, por
      fim, configurações e backup.
  - [x] Registrar capturas do tema atual em 100% e medir combinações candidatas da
        paleta em `docs/base_clientes_contraste.md`; há pares que exigem revisão.
        Capturas do tema novo e validação em 125% e 150% continuam pendentes.
- [ ] Alinhar os relatórios em PDF à mesma identidade (cabeçalho, cores, tabela), usando os
      tokens nos componentes compartilhados escolhidos na Fase 4.2. Definir a paleta antes
      de migrar os relatórios.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
