# Histórico de Desenvolvimento

## 2026-11-09

### Interface — ajustes em diálogos

- **Recuo de campos numéricos:** aplicado `setTextMargins` (`DIMENSOES.espacamento`) no editor interno dos spinboxes em venda, condicional (desconto, quantidade e preço), recebimento, parcelas do pagamento e diálogos de quantidade/preço de custo/preço de venda do pedido; `solicitar_preco_venda` ganhou o parâmetro `ajustar_recuo_campo`.
- **Tamanho de janelas:** `FornecedorSelectionDialog` (médio) e `ProdutoSelectionDialog` (grande) passaram a usar `DialogSizeMixin`.
- **Pagamento:** removido o frame "Valor de Entrada"; `valor_entrada` permanece 0.0 em `get_dados()` por compatibilidade com a venda.
- **Ícone:** removido `setWindowIcon` relativo de `ClienteSelectionDialog`, que anulava o ícone da aplicação na barra de título.
- **Pedido:** botões do diálogo "Frete e Desconto" trocados por `QDialogButtonBox`, igual aos demais diálogos.
- **Teste Windows:** a asserção de largura da coluna Nome agora verifica a regra de dimensionamento responsivo, em vez de exigir largura fixa.
- **ROADMAP:** Fase D ajustada com validação de estados visíveis de contraste e conferência de navegação por teclado.

### Release 0.10.7

- Inclui as melhorias de interface, os ajustes em diálogos, a inclusão de recursos visuais no pacote e a validação isolada dos instaladores e do launcher registrados abaixo.
- A tag `v0.10.6` não publicou a release porque dois testes de diálogo falharam no runner Linux ao acessar `QLineEdit.cursorRect()`. O teste agora verifica as margens públicas do editor; a tag não foi reutilizada.
- Validação local em Windows: Ruff passou; pytest aprovou 353 testes (1 ignorado).

## 2026-11-08

### Alterações após 0.10.5

- **Interface:** implementados tokens centralizados para temas claro e escuro, preferência de tema persistida e estilos consolidados. Foram adicionados ícones SVG com licenças, componentes compartilhados para formulários e listagens, navegação mais compacta e ajustes de rolagem e dimensionamento de diálogos.
- **Empacotamento:** o gerador de releases passou a incluir os novos ícones e arquivos de licença; Pillow foi declarado nas dependências.
- **Testes e validação:** ajustes em testes de backup e atualização; validação em diretórios isolados no Windows dos instaladores 0.10.4/0.10.5 e do launcher, cobrindo atualização assinada, abertura da versão nova, preservação de banco fictício, rollback após falha, reparo de `cryptography` e preservação do launcher quando a instalação de dependências falha.

As alterações foram consolidadas na release 0.10.7. Os itens ainda pendentes permanecem no `ROADMAP.md`.
