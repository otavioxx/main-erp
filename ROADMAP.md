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

- [ ] Validar integralmente o backup manual e sua recuperação. O ZIP agora usa snapshot
      SQLite com verificação de integridade e testes de WAL, banco inválido e falha do
      snapshot. Ainda faltam testes de escritas concorrentes, falhas de disco durante
      publicação e restauração completa do ZIP pelo fluxo da aplicação.
- [ ] Redesenhar a restauração em `mainerp/data/db_utils.py` e
      `mainerp/ui/dialogs/restore_backup_dialog.py`: coordenar o encerramento das conexões
      e do backup automático. A restauração agora é preparada e aplicada antes da abertura,
      após snapshot SQLite anterior; falhas bloqueiam a abertura e preservam a pendência.
      O launcher precisa ser atualizado pelo instalador. A validação verifica integridade,
      tabelas e nomes de colunas após migrar uma cópia, mas não confere todos os dados,
      tipos e restrições. Testes terminam
      o processo durante cópia em WAL e journal padrão e verificam a recuperação.
      Testar falhas de disco e concorrência de outros processos.
- [ ] Não prometer reversão bem-sucedida quando a recuperação também falhar:
      a nova restauração preserva snapshot anterior e pendência caso a aplicação falhe;
      o sistema bloqueia a abertura. Validar recuperação e mensagens em falhas e
      interrupções reais, inclusive durante a confirmação da escrita no SQLite.
- [x] Tratar falhas de persistência de `backup_settings.json` na interface. Salvar o
      caminho preserva os demais campos e rejeita configurações inválidas; falhas ao
      salvar o caminho ou metadados do backup são informadas ao usuário.
- [ ] Testar e corrigir o ciclo de fechamento/backup em `MainWindow`: o timer do backup
      automático é parado antes de abrir o diálogo de backup, mas não é reiniciado caso
      o fechamento seja interrompido. Verificar também falhas de agendamento/retenção e
      tornar visível a idade e o resultado do último backup.
- [ ] Definir política e testes de recuperação externa: os snapshots diários ficam no
      mesmo diretório de dados e só são executados com o aplicativo aberto; não substituem
      uma cópia externa. Validar periodicamente restauração em instalação isolada e
      documentar quais dados e configurações são incluídos em cada tipo de backup.

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

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
