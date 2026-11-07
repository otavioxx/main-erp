# Roadmap do MainERP

Baseado em uma análise estática do código (≈ 25,5 mil linhas, 0 testes). Cada fase deixa o
sistema funcionando; não faça duas fases ao mesmo tempo.

## Fase 0 — Higiene segura (1 a 2 dias)

- [x] Commitar o modelo de distribuição atual e criar a tag da primeira versão.
- [x] `ruff check . --select F401,F841,F541 --fix`: remove imports e variáveis não usados.
- [x] Remover módulos que nenhum arquivo importa (um commit só, fácil de reverter):
      `views/base_view.py`, `utils/table_utils.py`, `utils/produto_validation.py`,
      `utils/config_backup.py`, `utils/duplicata_utils.py`, `utils/resources.py`,
      `models/item_pedido.py`, `dialogs/frete_desconto_dialog.py` (≈ 1,5 mil linhas).
- [x] Remover `PRAGMA timezone` em `database.py` (não existe no SQLite, não faz nada).
- [x] Adicionar `ruff` e um `pyproject.toml` com a configuração.

## Fase 1 — Rede de segurança (1 a 2 semanas)

- [x] **Logging central** (arquivo rotativo em `dados\logs`) no lugar dos ≈ 68 `print()`.
- [x] Auditar os 164 `except Exception` amplos: restringir os tipos quando seguro e
      registrar as falhas com o logging central. Seis casos previsíveis foram estreitados;
      os demais permanecem amplos em limites de recuperação/propagação.
- [ ] **Testes com pytest** começando pelo que mais dói se quebrar:
      cálculos de venda/duplicata/estoque (`utils/`), regras dos `models/` e as migrações
      do banco (já testadas manualmente; transformar em testes automáticos).
- [ ] Script `verificar.bat` que roda ruff + pytest antes de cada release.
- [ ] Backup automático diário em `dados\backups` com retenção (ex.: 30 dias) e opção de
      cópia para uma pasta externa/nuvem.

## Fase 2 — Camada de dados (2 a 3 semanas)

- [ ] Hoje há 56 `Database()` espalhados (cada um abre sua própria conexão). Criar um
      gerenciador único (`with db.transacao() as cur:`) e migrar um model por vez.
- [ ] Tirar o SQL das telas (`recebimento_view`, `condicional_view`, `venda_view`,
      `pedido_view`) para os models/repositórios.
- [ ] **Dinheiro**: 23 colunas `REAL` (float) acumulam erro de arredondamento. Migrar para
      centavos inteiros (`INTEGER`) ou `Decimal`, com migração numerada e testes antes.
- [ ] Índices nas colunas mais filtradas (cliente, data, status) e `PRAGMA foreign_keys` já ativo.

## Fase 3 — Reestruturação (2 a 4 semanas)

- [ ] Criar o pacote `mainerp/` (estrutura abaixo), movendo com `git mv` uma pasta por vez e
      rodando os testes a cada passo.
- [ ] Unificar as 9 cópias de `NumericTableWidgetItem` e as 2 de `BackupConfig`.
- [ ] Quebrar os arquivos acima de 900 linhas (`condicional_dialog`, `venda_dialog`,
      `pedido_dialog`, `recebimento_view`, `condicional_view`) em componentes menores.
- [ ] Decidir sobre `BaseTableView`: adotar nas 7 telas de listagem (reduz código repetido)
      ou apagar.
- [ ] Splash: trocar os ≈ 6 s de `time.sleep` artificiais por progresso real.

Estrutura alvo:

```
MainERP/
  main.py                 # fino: chama mainerp.app.run()
  mainerp/
    app.py  config.py  paths.py
    data/        database.py, migracoes, repositórios (hoje models/)
    domain/      regras de negócio e cálculos (hoje utils/*_utils)
    ui/          main_window, views/, dialogs/, widgets/, styles.py, mixins/
    reports/     geração de PDF (hoje imprecoes/)
  tests/
  distribuicao/
  docs/
  pyproject.toml
```

> O launcher abre `main.py` na raiz do release; mantenha esse arquivo fino durante a mudança.

## Fase 4 — Operação e atualização online

- [ ] Versionamento semântico + `CHANGELOG.md`.
- [ ] Assinar os pacotes de release (ed25519) e validar a assinatura no launcher.
- [ ] Hospedar `version.json` e o zip em HTTPS e preencher `update_url` no `launcher.json`.
- [ ] Pipeline automático de release (GitHub Actions): ruff, testes, zip, SHA256.
- [ ] Tela "Sobre / Atualizações" mostrando versão, data e histórico.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
