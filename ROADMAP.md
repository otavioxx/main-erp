# Roadmap do MainERP (revisado)

Versão reorganizada a partir da análise do projeto (v0.10.5). Mantém só o que está pendente ou decidido; o histórico concluído fica resumido, porque o detalhe já está no CHANGELOG.

## Regras de trabalho

- Uma fase por vez. Cada fase deixa o sistema funcionando e termina com `verificar.bat` verde.
- Testes sempre com dados e instalações isolados, nunca com dados de produção.
- Cada item pendente tem um critério de pronto de uma linha. Notas longas vão para o CHANGELOG ou para `docs/`.

## Concluído (resumo)

- **Fases 0 a 3:** higiene do código, logging central, testes, banco em camada própria, centavos inteiros, pacote `mainerp/`, listagens com configuração comum.
- **Fase 4:** versionamento semântico, releases assinadas (Ed25519, SHA256), atualização online, GitHub Actions, tela Sobre, runtimes isolados por release.
- **Fase 4.1:** backup automático e manual verificados, restauração redesenhada e testada, travas do sistema operacional.
- **Fase 4.3:** tokens de tema claro e escuro, raio zero, estilos locais consolidados no tema central.

## Fase A: Proteção dos dados (prioridade máxima)

Objetivo: a perda do disco do PC não pode significar perda do sistema.

- [ ] Destino da cópia: pasta sincronizada de nuvem (OneDrive, Google Drive etc.), pendrive/HD externo, ou os dois. A pasta sincronizada é o caminho mais simples, porque não exige API.
      1. Quando o usuário abrir o MainERP pela primeira vez, o sistema já terá uma pasta padrão para backups locais
      2. O usuário poderia selecionar, por exemplo:
            - C:\Users\Usuario\OneDrive\MainERP
            - C:\Users\Usuario\Google Drive\MainERP
            - D:\Dropbox\MainERP
            O ERP não precisaria saber qual serviço está sendo utilizado.
            Ele simplesmente gravaria os backups naquela pasta.
      3. E se o usuário não tiver sincronização instalada?
            Não acontece nada de errado.
            O sistema continuaria funcionando normalmente com os backups locais.
      4. Um detalhe técnico importante
            Eu recomendaria que o MainERP verificasse:
                  Se a pasta selecionada ainda existe.
                  Se o Windows permite gravar nela.
                  Se há espaço disponível.
                  Se o arquivo de backup foi criado corretamente.
                  Se o arquivo foi efetivamente gravado antes de sinalizar sucesso.
            Uma ressalva: gravar na pasta não significa que a nuvem já recebeu o arquivo. O ERP deve distinguir backup criado localmente de sincronização confirmada pelo serviço.
- [ ] Copiar automaticamente cada backup diário para o destino externo, com retenção própria.
- [ ] Verificar a cópia depois de gravar (tamanho e hash) e avisar na interface se falhar.
- [ ] Tratar destino ausente (pendrive desconectado, pasta indisponível): avisar sem travar o sistema e tentar de novo na próxima oportunidade.
- [ ] Mostrar na barra de status a idade da última cópia externa, junto com a do backup automático.
- [ ] Validar uma restauração a partir da cópia externa em instalação isolada, conferindo registros e totais (antigo item 2 da rota pendente).
- [ ] Atualizar `docs/backup_recuperacao.md` com a rotina e um lembrete periódico de teste de restauração.

*Pronto quando:* um backup novo aparece no destino externo sozinho, e uma restauração a partir dele já foi testada.

## Fase B: Base técnica (itens rápidos)

- [ ] Confirmar a versão do Python usada no desenvolvimento e nos releases. Os `__pycache__` indicam 3.15, ainda pré-lançamento. Fixar uma versão estável (3.12 ou 3.13) e validar PyQt6, pywin32, cryptography e ReportLab nela.
- [ ] Declarar Pillow em `requirements.txt` e validar instalação limpa.
- [ ] `--destino` do instalador: corrigir (definir `MAINERP_DATA`) ou restringir explicitamente. Até lá, usar o destino padrão.
- [ ] Definir procedimento seguro para a trava legada `.update.lock`, sem apagar trava em uso.
- [ ] Decidir sobre as colunas `REAL` antigas, que hoje são preenchidas junto com `*_centavos`. Opção: migração 4 que remove as colunas antigas depois de confirmar que nenhuma leitura depende delas. Testar em cópia do banco.
- [ ] SQLite: o adaptador de datas padrão está obsoleto desde o Python 3.12. Hoje funciona, mas pode ser removido numa versão futura. Vale registrar adaptadores de data explicitamente.
- [ ] Erro após a falha: o RuntimeError em listagem_modelo.py (linha 41) indica que o texto “Registros exibidos” tenta ler uma tabela já destruída. É provável que só apareça no encerramento depois da falha, mas vale proteger essa chamada quando mexer nessa tela.
- [ ] Aviso em test_release_updates: o teste lê a saída de um subprocesso como UTF-8, e o Windows devolve outra codificação (o byte 0x87 é o “ç”). É só um aviso, mas dá para corrigir informando o encoding.

## Fase C: Relatórios e visualizador embutido

Decisão registrada: **manter ReportLab**. HTML/CSS com Jinja2, QtWebEngine e WeasyPrint foram descartados por peso e complexidade de instalação. As prioridades são aparência e visualização dentro do sistema.

### C1. Visualizador (ganho mais visível, risco baixo)

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

### C4. Impressão

- [ ] Validar em impressoras reais e tamanhos personalizados, incluindo etiquetas. Registrar os limites que os testes automatizados não cobrem.

*Pronto quando:* todos os relatórios abrem no visualizador do sistema, com o mesmo padrão visual, e a abertura externa continua disponível.

## Fase D: Identidade visual (4.3 restante)

- [ ] Validação visual das telas nos dois temas, somente em 100% no Windows.
- [ ] Revisar contraste da paleta.
- [ ] Usar o mesmo conjunto de tokens nos relatórios (ligação com a C2).

## Fase E: Operação e launcher (adiar até A, B e C estarem concluídas)

- [ ] Validar em Windows limpo ou VM: destino padrão, atalhos e avisos.
- [ ] Redesenhar a janela de espera do launcher (hoje em Tkinter), com testes antes de mexer.
- [ ] Planejar a atualização do launcher fixo e a rotação da chave de assinatura.
- [ ] Conferência automática do conteúdo do ZIP e do instalador antes de publicar.
- [ ] Ampliar a validação de tipos e regras de negócio na restauração, com bancos legados.

## Fase F: Qualidade contínua (aos poucos, junto com outras fases)

- [ ] Revisar os 160 `except Exception` ao tocar em cada módulo, restringindo ou registrando.
- [ ] Dividir arquivos grandes quando forem alterados (`produto_view`, `print_venda`, `styles`, `backup_dialog`, `duplicata`).
- [ ] Revisar a licença do PyQt6 se o sistema um dia for distribuído a terceiros.

## Fase G: Futuro

- [ ] **Auditoria**: registro de quem alterou o quê e quando nas tabelas principais.
- [ ] **Painel** com indicadores, reaproveitando os componentes dos relatórios.
- [ ] Frontend mais moderno: reavaliar só depois das fases anteriores. A decisão atual é seguir em Qt Widgets.
- ~~PostgreSQL~~: retirado do planejamento, porque o banco é usado em um único PC e o SQLite em WAL atende. Reavaliar apenas se surgir uso em múltiplos PCs.

## Ordem sugerida

**A → B → C1 → C2 → C3 → D → C4 → E → F/G.**

A Fase A vem primeiro por ser pequena e proteger tudo o que vem depois. A C1 entrega o primeiro ganho visível, e a C2/C3 resolvem a aparência sem trocar de motor.
efinir a paleta antes
      de migrar os relatórios.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
efinir a paleta antes
      de migrar os relatórios.

## Fase 5 — Produto (conforme a necessidade)

- [ ] Auditoria: registrar quem alterou o quê (vendas, preços, estoque).
- [ ] Relatórios gerenciais e painel inicial (vendas, estoque baixo, contas a receber).
- [ ] Se mais de um PC precisar usar o mesmo banco: migrar de SQLite para um servidor
      (PostgreSQL), o que a Fase 2 deixa muito mais simples.
