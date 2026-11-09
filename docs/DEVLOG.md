# Histórico de Desenvolvimento

## 2026-11-08

### Pós-0.10.5 — alterações ainda não publicadas

- **Interface:** implementados tokens centralizados para temas claro e escuro, preferência de tema persistida e estilos consolidados. Foram adicionados ícones SVG com licenças, componentes compartilhados para formulários e listagens, navegação mais compacta e ajustes de rolagem e dimensionamento de diálogos.
- **Empacotamento:** o gerador de releases passou a incluir os novos ícones e arquivos de licença; Pillow foi declarado nas dependências.
- **Testes e validação:** ajustes em testes de backup e atualização; validação em diretórios isolados no Windows dos instaladores 0.10.4/0.10.5 e do launcher, cobrindo atualização assinada, abertura da versão nova, preservação de banco fictício, rollback após falha, reparo de `cryptography` e preservação do launcher quando a instalação de dependências falha.

Estas alterações são posteriores à tag `v0.10.5` e ainda não correspondem a uma release publicada. Os detalhes e itens pendentes permanecem no `ROADMAP.md`.
