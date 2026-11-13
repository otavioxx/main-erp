# Histórico de versões

Este arquivo registra as alterações relevantes do PLUMA a cada versão, seguindo as recomendações do [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

As alterações são organizadas nas categorias:

- **Adicionado:** novas funcionalidades.
- **Alterado:** mudanças em funcionalidades existentes.
- **Descontinuado:** funcionalidades que serão removidas em versões futuras.
- **Removido:** funcionalidades retiradas.
- **Corrigido:** correções de erros e comportamentos inesperados.
- **Segurança:** melhorias relacionadas à proteção e segurança do sistema.

## [Unreleased]

### Adicionado

### Alterado

- Redesenhada a tela de abertura do sistema com a identidade visual Pluma, barra de progresso e indicação da etapa de carregamento.
- Redesenhada a janela exibida durante as atualizações, com a identidade visual Pluma e barra de progresso do download e da instalação.

### Corrigido

### Segurança

### Removido

## [0.10.10] - 2026-11-10

### Alterado
- Reformulada a janela Sobre, com informações institucionais e canal de suporte.

### Adicionado
- Link clicável para contato com o suporte por e-mail.
- Exibição automática da versão instalada e da data de lançamento.

## [0.10.9] - 2026-11-09

### Corrigido

- Corrigida uma falha na restauração do banco de dados causada por disputas momentâneas pelo acesso exclusivo ao arquivo.

### Removido

- Removida a prévia HTML da paleta de cores do código-fonte após alerta do Microsoft Defender.

## [0.10.7] - 2026-11-09

### Adicionado

- Adicionados temas claro e escuro.
- Adicionados ícones SVG monocromáticos.

### Alterado

- Padronizados os estilos, formulários, listagens e dimensões dos diálogos.
- Ajustadas a navegação e as margens dos campos numéricos.
- Aprimorados o dimensionamento e a apresentação dos diálogos de seleção e pedidos.

## [0.10.5] - 2026-11-08

### Corrigido

- Corrigida a preparação da dependência de assinatura no runtime principal do launcher, garantindo seu funcionamento também em instalações existentes antes da atualização do aplicativo.

## [0.10.4] - 2026-11-08

### Adicionado

- Adicionada verificação em segundo plano dos backups automáticos e manuais recentes.
- Adicionados avisos na barra de status sobre a idade dos backups, resultados e falhas de agendamento ou retenção.

### Alterado

- Reforçada a verificação dos backups, com alertas e novas tentativas em caso de arquivos inválidos ou inacessíveis.
- Aprimorada a segurança da restauração, com validação dos dados e referências antes de alterar o banco atual.
- Reforçada a proteção contra operações simultâneas durante a preparação e execução de restaurações.
- Aprimorado o tratamento de falhas na restauração, com orientações para preservar o banco de dados e os arquivos necessários à recuperação.
- Ajustado o controle de retenção para evitar exclusões indevidas quando forem identificadas datas futuras nos backups.

### Corrigido

- Corrigidas falhas de concorrência durante a restauração do banco de dados.
- Corrigida a possibilidade de sobrescrita de arquivos durante a criação simultânea de backups.
- Corrigida a retomada do agendamento de backups automáticos após fechamentos interrompidos.
- Corrigida a identificação de backups manuais criados no mesmo segundo, evitando nomes duplicados.

## [0.10.2] - 2026-11-07

### Alterado

- Aprimorado o instalador autocontido, que agora utiliza uma pasta temporária removida após a execução, sem apagar arquivos do usuário.
- Adicionado um atalho complementar na pasta do sistema durante a instalação pelo instalador.

### Corrigido

- Corrigida a limpeza de arquivos de desenvolvimento após a instalação pelo ZIP de código, preservando checkouts Git e dados existentes.

## [0.10.1] - 2026-11-07

### Corrigido

- Corrigida a identificação visual do aplicativo nos atalhos, permitindo ao Windows associar corretamente o ícone à janela e à barra de tarefas.

## [0.10.0] - 2026-11-07

### Adicionado

- Adotado o versionamento semântico estável no formato MAJOR.MINOR.PATCH.
- Adicionada a assinatura digital dos pacotes de atualização com Ed25519.
- Adicionada a validação de assinatura, hash SHA256 e versão dos pacotes antes da instalação de atualizações online.
- Adicionados ambientes Python isolados por versão para preservar a possibilidade de rollback.

### Alterado

- Aprimorado o processo de geração de releases, com validação do formato de versão e da tag correspondente.
- Aprimorado o instalador para verificar a versão ativa antes de confirmar a conclusão da instalação.
- Restringidos os arquivos incluídos nos pacotes de distribuição.

### Corrigido

- Corrigido o funcionamento dos backups manuais com SQLite, garantindo snapshots consistentes mesmo com WAL ativo.
- Corrigido o processo de restauração, que agora valida os dados e prepara um snapshot anterior antes de aplicar alterações.
- Corrigidos detalhes de apresentação e dimensionamento das tabelas dos relatórios.

## [0.10] - 2026-11-07

### Adicionado

- Implementado o launcher com consulta automática de atualizações públicas no GitHub Releases.
- Adicionada a possibilidade de utilizar URLs personalizadas e desativar a busca por atualizações.
- Publicados o manifesto e os pacotes de versão no GitHub para distribuição e atualização online.

## [0.09] - 2026-11-07

### Adicionado

- Implementada a distribuição e atualização online por meio de releases públicas do GitHub.

### Alterado

- Configurados o launcher e o instalador para utilizar o repositório público como origem padrão das atualizações, preservando as opções de personalização e desativação.

## [0.08] - 2026-11-07

### Adicionado

- Adicionadas migrações versionadas para atualização do esquema do banco de dados.
- Adicionado backup automático antes das alterações no esquema do banco.

### Alterado

- Padronizados os cálculos e a persistência de valores monetários em centavos para vendas, parcelas, recebimentos, produtos, pedidos e condicionais.
- Ajustado o pagamento parcial do saldo final para gerar automaticamente uma parcela com o valor restante.

### Corrigido

- Corrigidos problemas de exibição e entrada de valores nas vendas.
- Corrigida a consistência dos valores monetários entre as telas e o banco de dados, preservando a compatibilidade com a interface existente.

## [0.07]

### Adicionado

- Primeira versão distribuída por instalador, com releases versionadas, atualização local e rollback automático.

---

**Observações:** as versões 0.10.6 e 0.10.8 não constam no histórico fornecido. Seus registros devem ser recuperados do histórico de desenvolvimento, caso tenham sido publicadas.
