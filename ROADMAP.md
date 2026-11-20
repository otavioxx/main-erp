# Roadmap do PLUMA

Roadmap do produto, organizado pela sequência de execução. O histórico de mudanças publicadas
está no [CHANGELOG](CHANGELOG.md); os guias estão no
[índice da documentação](docs/README.md).

## Regras de trabalho

- Uma fase por vez. Cada fase deve deixar o sistema funcionando e terminar com `verificar.bat` verde.
- Testes sempre com dados e instalações isolados, nunca com dados de produção.
- Cada item pendente deve ter um critério de pronto de uma linha. Notas longas ficam no CHANGELOG ou em `docs/`.

## Concluído (resumo)

- **Fases 0 a 3:** higiene do código, logging central, testes, banco em camada própria, centavos inteiros, pacote `mainerp/` e listagens com configuração comum.
- **Fase 4:** versionamento semântico, releases assinadas (Ed25519, SHA256), atualização online, GitHub Actions, tela Sobre e runtimes isolados por release.
- **Fase 4.1:** backup automático e manual verificados, restauração redesenhada e testada, travas do sistema operacional.
- **Fase 4.3:** tokens de tema claro e escuro, raio zero e estilos locais consolidados no tema central.

---

## Fase A: Proteção dos dados (prioridade máxima)

**Objetivo:** a perda do disco do PC não pode significar perda do sistema.

- [x] Verificar a cópia depois de gravar (tamanho e hash) e avisar na interface se falhar.
- [x] Evitar sobrescrever arquivos existentes ao testar a escrita no destino do backup manual.
- [x] Validar esquema e consistência dos backups automáticos recentes e dos novos antes da retenção.
- [x] Tratar destino ausente (pendrive desconectado, pasta indisponível): avisar sem travar o sistema e tentar de novo na próxima oportunidade.
- [x] Validar uma restauração a partir da cópia externa em instalação isolada, conferindo registros e totais.
- [x] Documentar a rotina de cópia externa e teste periódico de restauração em `docs/backup_recuperacao.md`.

**Pronto quando:** cópias externas forem verificadas e uma restauração completa puder ser realizada em instalação isolada.

## Fase B: Base técnica e estabilidade

**Objetivo:** corrigir pendências técnicas que podem comprometer a manutenção, a integridade e a evolução do sistema.

### Verificação e CI

- [x] Corrigir e incluir no CI o teste de interface Windows que falha nas escalas 1.25 e 1.5.
- [x] Executar Ruff e pytest em pull requests e exigir esses checks para integrar à `main`.
- [x] Declarar Pillow em `requirements.txt` e validar instalação limpa.
- [x] Corrigir o teste `test_release_updates` para não depender da codificação do PowerShell no Windows.

### Distribuição e compatibilidade

- [ ] Recusar publicação de versão igual ou inferior à última release antes de marcar como `latest`.
- [ ] `--destino` do instalador: corrigir (definir `MAINERP_DATA`) ou restringir explicitamente. Até lá, usar o destino padrão.
- [ ] Definir procedimento seguro para a trava legada `.update.lock`, sem apagar trava em uso.
- [ ] Decidir sobre as colunas `REAL` antigas, que hoje são preenchidas junto com `*_centavos`. Opção: migração 4 que remove as colunas antigas depois de confirmar que nenhuma leitura depende delas. Testar em cópia do banco.
- [ ] SQLite: o adaptador de datas padrão está obsoleto desde o Python 3.12. Hoje funciona, mas pode ser removido numa versão futura. Vale registrar adaptadores de data explicitamente.

### Regras de negócio e validações

- [ ] Unificar o cálculo do total do pedido (subtotal - desconto + frete) entre modelo, utilitários e tela.
- [ ] Restringir recebimento e cancelamento a pedidos pendentes, impedindo recebimento duplicado.
- [ ] Definir se o recebimento substitui custo e preço de venda do produto e se deve manter a margem padrão de 30%.
- [ ] Validar no modelo quantidades e valores dos itens do pedido, além das validações da tela.
- [ ] Adicionar testes para transições de status, recebimento duplicado e validação dos itens.
- [ ] Definir como itens em condicionais ativas afetam o estoque disponível e aplicar a regra na venda, devolução e conversão.
- [ ] Validar no modelo das condicionais quantidades, preços, descontos e transições de status.
- [ ] Unificar o prazo padrão de devolução e validar as datas informadas na condicional.
- [ ] Adicionar testes para estoque, validações, estados e prazos de condicionais.
- [ ] Definir a regra para desconto total e venda com valor zero, alinhando as formas de pagamento.
- [ ] Centralizar as validações da venda no fluxo comum e revalidar o estoque ao finalizar.
- [ ] Unificar as regras de cancelamento e exclusão, impedindo devolução duplicada de estoque e exclusão com parcelas pagas.
- [ ] Adicionar testes para validações, valor zero, estoque e transições de cancelamento/exclusão.
- [ ] Definir a regra para pagamentos parciais e excedentes no crediário, incluindo valores acima do saldo devedor.
- [ ] Validar no modelo valor, data e forma de pagamento dos recebimentos.
- [ ] Redistribuir diferenças entre parcelas em centavos, sem perda por arredondamento.
- [ ] Definir e padronizar o intervalo mensal dos vencimentos das parcelas.
- [ ] Adicionar testes para pagamentos parciais/excedentes, validações, arredondamento e vencimentos.
- [ ] Definir regras para devolução parcial, valor líquido após descontos, destino do item e opções de ressarcimento, respeitando os direitos do consumidor.
- [ ] Definir como devoluções de vendas a prazo reduzem parcelas em aberto antes de gerar crédito sobre valores já pagos.
- [ ] Definir regras do vale-troca: titularidade, uso parcial, saldo remanescente, validade e estorno em cancelamentos.
- [ ] Persistir o desconto da venda rateado por item para calcular corretamente devoluções parciais.
- [ ] Definir uma regra única para preço de venda zero, alinhando cadastro de produtos e validação da venda.
- [ ] Rejeitar estoque negativo no modelo de produto, inclusive em atualizações diretas.
- [ ] Impedir a inativação de produto quando não for possível verificar pedidos e condicionais vinculados.
- [ ] Definir a regra de inativação de clientes com vendas ou parcelas em aberto, preservando o recebimento de valores existentes.
- [ ] Exigir nome não vazio e validar CPF/CNPJ quando informado; normalizar o documento para impedir duplicidade por formatação.
- [ ] Diferenciar erros de integridade no cadastro de clientes, sem reportar toda falha como CPF/CNPJ duplicado.
- [ ] Validar email e telefone somente quando informados.
- [ ] Adicionar testes para validações de clientes, documentos duplicados com formatações diferentes e inativação.
- [ ] Definir a regra de inativação de fornecedores com pedidos pendentes, preservando o tratamento dos pedidos existentes.
- [ ] Exigir nome não vazio e validar CNPJ quando informado; normalizar o documento para impedir duplicidade por formatação.
- [ ] Diferenciar erros de integridade no cadastro de fornecedores, sem reportar toda falha como CNPJ duplicado.
- [ ] Validar email e telefone somente quando informados.
- [ ] Adicionar testes para validações de fornecedores, CNPJ duplicado com formatações diferentes e inativação.
- [ ] Exibir nas configurações avançadas somente valores reais, removendo informações fixas ou desatualizadas.
- [ ] Validar dados da empresa no modelo, não apenas na tela, incluindo CNPJ e contatos quando informados.
- [ ] Recusar logos inválidos antes de persistir os dados da empresa.
- [ ] Remover opções de configuração sem efeito ou implementar seu comportamento correspondente.
- [ ] Adicionar testes para validação dos dados da empresa, logo inválido e valores exibidos nas configurações.

### Persistência e tratamento de falhas

- [ ] Criar migração SQLite aditiva para registrar devoluções e movimentações de vale-troca vinculadas às vendas e clientes.
- [ ] Tornar atômicas as operações de venda, devolução, estoque, parcelas e vale-troca, além do recebimento de pedidos e conversão de condicionais; qualquer falha deve reverter todas as etapas.
- [ ] Remover ou alinhar o método legado de criação de tabelas de condicionais ao esquema versionado.
- [ ] Validar identificadores dinâmicos (tabelas, campos e ordenação) nos utilitários SQL; valores já devem continuar parametrizados.
- [ ] Substituir ou remover o helper legado de backup que copia o arquivo SQLite diretamente, sem snapshot consistente.
- [ ] Avisar quando não for possível remover um backup manual que falhou na verificação.
- [ ] Proteger a atualização do texto “Registros exibidos” em `listagem_modelo.py` quando a tabela já tiver sido destruída durante o encerramento após uma falha.

**Pronto quando:** as verificações automatizadas estiverem funcionando no CI e as pendências técnicas prioritárias estiverem corrigidas, sem regressões.

## Fase I: Licenciamento e ativação offline

**Objetivo:** controlar a validade e o uso do PLUMA por máquina, sem exigir conexão com a internet ou serviços pagos.

- [ ] Criar sistema de geração de licenças assinadas com Ed25519, usando chave exclusiva para licenciamento.
- [ ] Criar identificador de máquina para vincular cada licença a um único computador.
- [ ] Desenvolver License Manager local para cadastrar empresas, definir validade e emitir licenças.
- [ ] Implementar validação da licença na inicialização do PLUMA.
- [ ] Criar tela de ativação para importar o arquivo de licença.
- [ ] Implementar avisos de vencimento e regras de bloqueio após a expiração.
- [ ] Armazenar a licença em `dados/`, preservando-a durante atualizações.
- [ ] Implementar proteção básica contra retrocesso do relógio do Windows.
- [ ] Documentar o processo de emissão, ativação, renovação e transferência de licença.
- [ ] Testar ativação, validade, expiração, troca de máquina e funcionamento offline em instalações isoladas.

**Pronto quando:** o PLUMA exigir uma licença válida vinculada à máquina, funcionar offline e preservar a licença durante atualizações.

## Fase C: Relatórios e visualizador embutido

**Decisão registrada:** manter ReportLab. HTML/CSS com Jinja2, QtWebEngine e WeasyPrint foram descartados por peso e complexidade de instalação. As prioridades são aparência e visualização dentro do sistema.

### C1. Visualizador

- [ ] Inventariar os 9 relatórios: onde são abertos, tamanho de página, logos, totais e impressão.
- [ ] Prototipar `QPdfView` em diálogo independente: navegação, zoom, ajuste de largura, busca, salvar como, abrir externamente e imprimir. Confirmar que `QtPdf` e `QtPdfWidgets` vêm na instalação limpa do Windows.
- [ ] Integrar nos pontos de abertura (`ExportUtils.abrir_arquivo` e `ProdutoView._abrir_arquivo`), mantendo a abertura externa como opção e como alternativa em caso de falha.

### C2. Aparência

- [ ] Definir o padrão visual dos relatórios, alinhado a `docs/identidade_visual.md`: cabeçalho, tipografia, cores de tabela e rodapé.
- [ ] Registrar uma fonte TTF livre, com licença verificada, no ReportLab no lugar da Helvetica padrão, e incluí-la no gerador de release.
- [ ] Extrair componentes compartilhados (cabeçalho, estilos, tabelas, rodapé com paginação).

### C3. Estrutura

- [ ] Separar dados de layout: cada relatório passa a ter uma função que busca e calcula (em centavos) e outra que só desenha. Tirar o SQL de dentro dos `print_*.py`.
- [ ] Migrar um relatório por vez, começando por vendas, com comparação visual antes e depois. Os demais seguem em sequência.

**Pronto quando:** todos os relatórios abrem no visualizador do sistema, com o mesmo padrão visual, e a abertura externa continua disponível.

## Fase D: Identidade visual

**Objetivo:** concluir a validação visual e de usabilidade dos componentes do sistema.

- [ ] Validação visual das telas nos dois temas, somente em 100% no Windows.
- [ ] Padronizar botões de confirmação/cancelamento nos diálogos e configurações.
- [ ] Aplicar a classe semântica correta às ações de restauração e aos botões destrutivos.
- [ ] Corrigir o carregamento do ícone nos diálogos que usam caminho relativo.
- [ ] Validar contraste dos estados visíveis (foco, seleção, desativado e hover) nos dois temas.
- [ ] Conferir navegação por teclado e atalhos nas listagens e diálogos principais.
- [ ] Usar o mesmo conjunto de tokens nos relatórios (ligação com a C2).

**Pronto quando:** telas e relatórios estiverem consistentes nos dois temas e a navegação principal estiver validada.

## Fase C4: Impressão dos relatórios

- [ ] Validar em impressoras reais e tamanhos personalizados, incluindo etiquetas. Registrar os limites que os testes automatizados não cobrem.

## Fase E: Operação, distribuição e launcher

**Objetivo:** consolidar a distribuição e a atualização do sistema depois da estabilização técnica, dos relatórios e do licenciamento.

- [ ] Validar em Windows limpo ou VM: destino padrão, atalhos e avisos.
- [ ] Permitir releases somente de tags sobre commits de `main` e revisar a proteção da branch e o escopo do secret de assinatura.
- [ ] Fixar as GitHub Actions em SHAs imutáveis.
- [ ] Redesenhar a janela de espera do launcher (hoje em Tkinter), com testes antes de mexer.
- [ ] Planejar a atualização do launcher fixo e a rotação da chave de assinatura.
- [ ] Verificar a assinatura Ed25519 do instalador `.pyz` antes de executar o bootstrap inicial.
- [ ] Conferência automática do conteúdo do ZIP e do instalador antes de publicar.
- [ ] Ampliar a validação de tipos e regras de negócio na restauração, com bancos legados.

**Pronto quando:** instalação, atualização, recuperação e inicialização estiverem validadas em ambiente Windows limpo, sem comprometer os dados ou a licença.

## Fase H: Evolução do produto

**Objetivo:** priorizar recursos que melhorem a operação diária das pequenas empresas.

- [ ] **Prioridade alta:** registrar devoluções parciais vinculadas à venda original, com recebimento e destino explícito dos itens.
- [ ] **Prioridade alta:** emitir e resgatar vales-troca vinculados ao cliente, com saldo auditável, uso parcial e reversão em vendas canceladas.
- [ ] **Prioridade alta:** conciliar devoluções de vendas a prazo com parcelas em aberto e o valor já pago antes de emitir crédito.
- [ ] **Prioridade alta:** testar devolução, estoque, crediário, saldo do vale e cancelamento da venda.
- [ ] **Prioridade alta:** configurar estoque mínimo por produto e listar itens para reposição, considerando pedidos pendentes e fornecedor; criação do pedido continua manual.
- [ ] **Prioridade alta:** destacar parcelas vencidas com dias de atraso e saldo em aberto por cliente.
- [ ] **Prioridade média:** painel enxuto com vendas por período e produtos mais vendidos, estoque baixo e recebíveis vencidos.
- [ ] **Prioridade posterior:** avaliar contas a pagar e despesas, com visão simples de compromissos e fluxo de caixa.
- [ ] **Evolução futura:** auditar alterações de vendas, preços e estoque, registrando quem alterou o quê e quando.
- [ ] **Se houver uso em mais de um PC:** reavaliar a persistência compartilhada. A decisão atual é manter SQLite para uso em um único PC; PostgreSQL não está planejado enquanto esse cenário atender.

**Pronto quando:** os recursos forem implementados conforme a prioridade e validados nos fluxos reais de operação.

## Fase G: Futuro

**Objetivo:** manter ideias de evolução que não são necessárias para a operação atual.

- [ ] Frontend mais moderno: reavaliar só depois das fases anteriores. A decisão atual é seguir em Qt Widgets.

**Pronto quando:** cada item for reavaliado conforme a necessidade real do produto, antes de entrar em desenvolvimento.

## Fase F: Qualidade contínua

**Objetivo:** reduzir gradualmente a dívida técnica sem criar uma fase de refatoração extensa que atrase as entregas.

Estas tarefas são transversais: devem avançar aos poucos, junto com as demais fases.

- [ ] Revisar os 160 `except Exception` ao tocar em cada módulo, restringindo ou registrando.
- [ ] Evitar que falhas em consultas de persistência sejam retornadas como listas vazias ou ausência de registro.
- [ ] Diferenciar nos rótulos os percentuais de lucro sobre venda e markup sobre custo.
- [ ] Dividir arquivos grandes quando forem alterados (`produto_view`, `print_venda`, `styles`, `backup_dialog`, `duplicata`).

---

## Ordem sugerida

**A → B → I → C1 → C2 → C3 → D → C4 → E → H → G**

A Fase A protege os dados antes de qualquer evolução. A Fase B estabiliza a base técnica. A Fase I estabelece o licenciamento antes da consolidação da distribuição. As Fases C1–C3 estruturam o visualizador e os relatórios; D finaliza a identidade visual antes da validação de impressão C4. A Fase E consolida a operação e a distribuição já considerando o licenciamento. A Fase H prioriza recursos concretos do produto, enquanto a G permanece como planejamento futuro.

A Fase F é transversal e deve avançar continuamente, sem alterar a ordem principal.

## Observações de planejamento

- A Fase I deve usar uma chave Ed25519 exclusiva para licenciamento, independente da chave de assinatura das atualizações.
- A licença deve ficar na pasta `dados/`, fora das releases, para sobreviver às atualizações.
- O licenciamento será offline; a assinatura protege a autenticidade da licença, mas não torna impossível a alteração deliberada do código por alguém com acesso a ele.
- A decisão atual é manter o sistema desktop em Qt Widgets, com SQLite e ReportLab.
