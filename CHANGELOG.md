# Histórico de versões

## 0.10.7 - 2026-11-09

### Added

- Adicionadas opções de tema claro e escuro e ícones SVG monocromáticos.

### Changed

- Padronizados estilos, formulários, listagens e dimensões dos diálogos.
- Ajustadas a navegação e as margens dos campos numéricos.

### Fixed

- Corrigidos detalhes de apresentação e dimensionamento em diálogos de seleção e pedido.


## 0.10.5 - 2026-11-08

- O instalador prepara a dependência de assinatura no runtime principal do launcher,
  inclusive em instalações existentes, antes de tentar atualizar o aplicativo.

## 0.10.4 - 2026-11-08

- Corrigida a execução dos testes de atualização no Linux usado pelo pipeline.
- Backups automáticos recentes são verificados em segundo plano; arquivos inválidos ou
  inacessíveis geram alerta e nova tentativa. Datas futuras suspendem a retenção e
  geram aviso, sem impedir novos backups; cópias não sobrescrevem arquivos existentes.
- Backups manuais recentes são verificados antes de dispensar o diálogo ao fechar;
  arquivos ausentes, corrompidos ou inacessíveis geram aviso.
- O agendamento de backup automático é retomado após fechamento interrompido; a barra
  de status informa idade, resultado e falhas de agendamento ou retenção.
- Falhas na restauração não afirmam que houve reversão; orientam preservar o banco,
  a pendência e os snapshots para suporte.
- A validação de restauração recusa valores não inteiros nos campos de centavos e
  referências estrangeiras declaradas inconsistentes, antes de alterar o banco atual.
- A aquisição da trava de restauração reserva a escrita antes do modo exclusivo,
  evitando bloqueios mútuos observados em aplicações simultâneas no Windows.
- Preparações simultâneas de restauração deixam de sobrescrever a pendência existente.
- A restauração mantém um bloqueio SQLite exclusivo desde o snapshot anterior até a
  validação, impedindo escritas concorrentes nesse intervalo.
- Backups manuais criados no mesmo segundo usam nomes distintos, evitando sobrescrita.

## 0.10.2 - 2026-11-07

- O instalador autocontido usa uma pasta temporária removida após a execução, sem
  apagar arquivos do usuário, e cria um atalho adicional na pasta do sistema.
- Na instalação pelo ZIP de código, arquivos de desenvolvimento conhecidos são
  removidos da pasta extraída após o sucesso, sem alterar checkouts Git ou dados.

## 0.10.1 - 2026-11-07

- O instalador atribui aos atalhos a mesma identidade usada pela janela do MainERP,
  permitindo ao Windows associar o ícone correto à barra de tarefas.

## 0.10.0 - 2026-11-07

- Adotado o formato de versão estável MAJOR.MINOR.PATCH para novas releases.
- A geração de pacotes e o pipeline verificam o formato da versão e a tag.
- O backup manual usa um snapshot SQLite consistente, inclusive com WAL ativo.
- A restauração é validada e aplicada antes da abertura do banco, com snapshot anterior.
- As atualizações usam ambientes Python separados para preservar o rollback de dependências.
- O instalador verifica a versão ativa antes de informar que a instalação terminou.
- A geração de releases restringe os arquivos incluídos e corrige a altura das tabelas.

## 0.10 - 2026-11-07

- Pacotes publicados pelo GitHub Actions agora são assinados com Ed25519.
- O launcher valida assinatura, SHA256 e versão do pacote antes de instalar uma
  atualização online.

## 0.09 - 2026-11-07

- Configurado o launcher e o instalador para consultar atualizações públicas no GitHub
  Releases por padrão, preservando URLs personalizadas e a opção de desativar atualizações.
- Publicado o manifesto e o pacote da versão no GitHub para distribuição e atualização online.

## 0.08 - 2026-11-07

- Corrigida a exibição e a entrada dos valores de venda.
- Cálculos e persistência monetária em centavos para vendas, parcelas, recebimentos,
  produtos, pedidos e condicionais, preservando a compatibilidade das telas existentes.
- Pagamento parcial do saldo final passa a criar uma parcela para o valor restante.
- Banco de dados atualizado por migrações aditivas, com backup automático antes das
  alterações de esquema.

## 0.07

- Primeira versão distribuída pelo instalador com releases versionadas, atualização local
  e rollback automático.
