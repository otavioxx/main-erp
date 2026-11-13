# Banco de dados, backups e restauração

Funcionamento técnico do banco SQLite, dos backups e da restauração do PLUMA. Para o passo a
passo do usuário (cópia externa e teste de restauração em um ambiente isolado), veja
[backup_recuperacao.md](backup_recuperacao.md). Para criar migrações, veja
[desenvolvimento.md](desenvolvimento.md).

## Esquema e migrações

O esquema é versionado por `PRAGMA user_version`. As migrações do projeto são aditivas.

Antes de migrar um banco existente com tabelas, é criado um backup em
`dados\backups\pre_migracao_*.db`.

## Backup automático

- **Quando:** o sistema verifica os backups automáticos ao abrir e a cada hora enquanto estiver
  aberto. Se não houver um arquivo recente, ou se o último tiver ao menos 24 horas, tenta criar
  um snapshot SQLite.
- **Verificação:** um arquivo recente é verificado em segundo plano; se estiver inválido ou
  inacessível, o sistema avisa e tenta criar outro.
- **Relógio:** arquivos com data mais de um minuto no futuro provocam um alerta para conferir o
  relógio: não contam como recentes e suspendem a retenção, mas não impedem novos backups. Sem
  uma fonte de tempo confiável, não é possível detectar todas as alterações incorretas do
  relógio.
- **Retenção:** após uma criação bem-sucedida, normalmente aplica retenção de 30 dias aos
  backups automáticos.
- **Gravação:** a publicação exige suporte a hard links no volume de backups e não sobrescreve
  arquivos anteriores. Falhas são exibidas e a tentativa é repetida.
- **Aplicativo fechado:** se o aplicativo ficar fechado por mais de um dia, a tentativa ocorre
  na próxima inicialização; não há execução enquanto estiver fechado.
- **Barra de status:** mostra a idade do backup elegível mais recente e o resultado da sessão;
  alertas persistentes podem ser consultados ao passar o mouse sobre o indicador.

A verificação SQLite não garante a validade de todas as regras de negócio nem substitui testes
de restauração.

## Backup manual

Um backup manual pode ser iniciado em **Configurações > Criar Backup**.

- **Ao fechar:** o sistema solicita um backup manual se não houver data registrada ou se ela
  tiver pelo menos um dia; o backup automático não substitui essa exigência.
- **Destino:** o diálogo usa a última pasta válida ou a Área de Trabalho e permite escolher
  outra.
- **Dispensa de backup recente:** antes de dispensar um backup recente, o sistema verifica se o
  ZIP está acessível e íntegro e confere o hash quando disponível; se a verificação falhar,
  avisa e solicita um novo backup. Isso não substitui um teste de restauração.

O ZIP manual contém um snapshot SQLite verificado, inclusive dados confirmados em WAL, um
`README.txt` e, se presente no diretório de trabalho, `config.ini`. Não é uma cópia completa de
`dados\`: a restauração aplica o banco, não configurações ou relatórios.

Os backups automáticos ficam no mesmo computador que o banco; mantenha cópias manuais externas,
com acesso protegido, e teste periodicamente sua recuperação em uma instalação isolada. Os
backups não são criptografados pelo aplicativo.

## Restauração

Uma restauração é preparada enquanto o sistema está aberto e aplicada na próxima inicialização,
antes de abrir o banco; um snapshot anterior é mantido em `dados\backups`.

- **Trava:** durante a aplicação, uma trava SQLite exclusiva impede gravações de outros
  processos até a validação; feche os demais programas que usam o banco antes de restaurar. Se a
  trava não puder ser adquirida, o sistema bloqueia a abertura e preserva a restauração
  pendente.
- **Pendência:** a publicação da pendência exige suporte a hard links no volume de dados; se não
  houver suporte, a preparação falha sem substituir uma pendência.
- **Launcher:** o launcher precisa ser atualizado pelo instalador para usar esse fluxo. Em
  execução direta de `main.py`, abra o sistema novamente após solicitar a restauração.
- **Falha:** se ocorrer falha na restauração, o sistema não abre e o estado do banco pode ter
  sido alterado; não se presume que houve reversão. Preserve o banco, o backup anterior e os
  arquivos pendentes e procure suporte antes de tentar novamente.

## Validação de um backup

A validação verifica integridade, tabelas, nomes de colunas, valores inteiros em centavos e
referências estrangeiras declaradas, após migrar uma cópia temporária. Backups com referências
órfãs ou valores inválidos em centavos são recusados; preserve o original para diagnóstico.

A validação não garante a correção de todos os dados, tipos, restrições ou regras de negócio,
nem detecta relacionamentos não declarados no esquema.
