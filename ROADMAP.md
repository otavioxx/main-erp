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
- [ ] Unificar as 9 cópias de `NumericTableWidgetItem` e as 2 de `BackupConfig`.
- [x] Quebrar os arquivos grandes de diálogos e telas em componentes separados de
      layout, entrada, operações, filtros, ações e persistência.
- [ ] Decidir sobre `BaseTableView`: adotar nas 7 telas de listagem (reduz código repetido)
      ou apagar.
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
- [ ] Adotar versionamento semântico estrito (MAJOR.MINOR.PATCH).
- [ ] Assinar os pacotes de release (ed25519) e validar a assinatura no launcher.
- [x] Implementar no launcher a consulta opcional do manifesto, o download e a validação
      SHA256 dos pacotes de atualização.
- [x] Publicar `MainERP-0.09.zip` e `version.json` no GitHub público e validar o endpoint
      latest; o ZIP baixado confere com o SHA256 do manifesto.
- [x] Publicar o padrão do endpoint no launcher/instalador e validar a atualização online
      isolada de 0.08 para 0.09; instalações antigas podem precisar do bootstrap do launcher.
- [x] Gerar manualmente o ZIP e o manifesto `version.json` com SHA256 por
      `distribuicao/criar_release.py`, e executar Ruff/pytest por `verificar.bat`.
- [ ] Automatizar o pipeline de release no GitHub Actions (Ruff, testes, ZIP e SHA256).
- [ ] Tela "Sobre / Atualizações" mostrando versão, data e histórico.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
