# Identidade Visual — MainERP

## 1. Direção visual

O MainERP adota uma identidade visual inspirada em sistemas ERP corporativos, priorizando sobriedade, legibilidade, consistência e densidade de informação.
Esta é a direção da Fase 4.3; a implementação e a validação visual são incrementais.
As referências são de padrão de uso: não copiar logotipos, ícones, textos ou outros
ativos de terceiros.

Princípios:

- **Estrutura plana:** cantos com raio zero e bordas visíveis de 1 px; sem sombras
  nem gradientes decorativos. Um componente pode não ter borda quando sua separação
  permanecer clara.
- **Hierarquia:** azul-marinho na navegação, cinzas neutros nas superfícies e um azul
  de acento para ação primária, foco e links; não usar cor apenas como decoração.
- **Significado:** sucesso, atenção, perigo e informação representam estados ou ações
  reais. Não depender apenas de cor: combinar com texto ou outro indicador reconhecível.
- **Densidade com legibilidade:** controles, linhas e espaçamentos compactos, sem cortar
  textos ou dificultar a leitura, a seleção e o uso por teclado. As dimensões finais
  dependem da validação visual na escala atualmente priorizada de 100%.
- **Ícones e texto:** ícones monocromáticos de conjunto com licença verificada; textos
  curtos e sóbrios, mantendo nomes de ações claros e avisos compreensíveis.
- **Acessibilidade:** contraste mínimo de 4,5:1 para texto normal; foco visível, estados
  distinguíveis e navegação por teclado. Avaliar também textos desabilitados, bordas,
  ícones e seleção, sem supor que uma cor isolada garante contraste em todo contexto.
- **Temas:** claro como padrão para configurações novas e escuro como opção.

### Navegação e densidade

A navegação lateral usa itens compactos com ícone e texto, faixa reta no item ativo
e contorno visível para foco de teclado. A largura permanece em 220 unidades Qt para
acomodar os rótulos; a altura dos itens medida no Windows a 100% foi de 32 unidades.
O preenchimento vertical de botões, campos e listas suspensas foi reduzido. A fonte
base permanece Segoe UI 12 pt e as linhas das sete listagens permanecem em 22 unidades:
os estilos de tabela usam tamanhos em pixels, distintos dos pontos da fonte base.
Testes também verificam as métricas para fontes base de 12 e 14 pt. O trabalho visual
atual prioriza exclusivamente 100%; os registros anteriores de outras escalas são
históricos, não critérios para a etapa atual.

### Tela-modelo de listagem

Cada listagem mantém título, painel de filtros, barra de ações e grade com cabeçalho
destacado e linhas alternadas. A barra usa ícones Lucide monocromáticos e texto; as
operações e seus nomes continuam próprios de cada domínio. Pesquisar leva o foco ao
campo de filtro, que continua aplicando a busca como antes. O rodapé mostra a quantidade
de registros exibidos após os filtros, não uma soma financeira.

Os atalhos locais são Ctrl+F para pesquisa, Ctrl+N para inclusão, Ctrl+E para edição
e Ctrl+P para impressão do documento ou relatório principal, quando disponíveis.
Eles atuam somente na listagem ativa; F11 e os atalhos de busca específicos de Produtos
permanecem disponíveis. A barra de status mostra empresa, versão e situação do backup;
o nome da empresa é atualizado ao salvar as configurações.

Nos formulários de Cliente, Fornecedor, Produto, Recebimento, Venda, Pedido e
Condicional, confirmar ou salvar é primário e cancelar é secundário. Ações destrutivas
continuam identificadas como perigo. Grupos usam o tema central de bordas retas.
Capturas do conteúdo dessas sete telas e formulários foram inspecionadas nos dois
temas em Windows a 100%, com banco isolado e linhas ilustrativas. Isso não substitui
uma revisão detalhada de interações e dados representativos.

## 2. Paleta oficial de cores

### Superfícies e estrutura

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `background_window` | `#EEF1F5` | `#1B1F24` | Fundo da janela |
| `surface` | `#FFFFFF` | `#232930` | Grades, formulários e campos |
| `surface_alt` | `#F5F7FA` | `#2A313A` | Linhas zebradas |
| `table_header` | `#E1E7EE` | `#2F3842` | Cabeçalhos de grades |
| `border` | `#C3CCD7` | `#3A444F` | Divisores e linhas |
| `border_input` | `#8795A3` | `#6B7785` | Contorno dos campos |

### Textos

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `text_primary` | `#1F2933` | `#E1E6EB` | Texto principal |
| `text_secondary` | `#4B5A6A` | `#AEB8C2` | Rótulos e textos auxiliares |
| `text_muted` | `#5C6875` | `#A0AFBE` | Dicas e metadados |
| `text_disabled` | `#5C6875` | `#A0AFBE` | Texto de botão desabilitado |
| `surface_disabled` | `#E1E7EE` | `#2A313A` | Fundo de botão desabilitado |

### Navegação institucional

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `nav_bg` | `#0B2A4A` | `#121A23` | Barra lateral |
| `nav_hover` | `#14406E` | `#1C2A3A` | Item ativo ou sob o mouse |
| `nav_text` | `#DCE6F0` | `#C9D3DD` | Texto da navegação |

### Cor de acento

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `accent` | `#1565A8` | `#2B6CB0` | Botões primários |
| `accent_hover` | `#0F5290` | `#2F78C4` | Hover de ações primárias |
| `accent_text` | `#1565A8` | `#87BDF5` | Texto destacado e links |
| `focus` | `#1565A8` | `#87BDF5` | Borda de foco |

### Seleção e interação

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `selection_bg` | `#CFE3F6` | `#1F4E79` | Fundo da linha selecionada |
| `selection_text` | `#0B2A4A` | `#FFFFFF` | Texto da linha selecionada |
| `hover_bg` | `#E8F0F8` | `#2D3640` | Linha sob o mouse |

### Estados semânticos

Cada estado possui três cores: texto, fundo e borda.

| Estado | Token | Claro | Escuro |
|---|---|---|---|
| Sucesso | `success_text` | `#1E6B30` | `#6FCF86` |
| Sucesso | `success_bg` | `#E3F4E7` | `#1F3A28` |
| Sucesso | `success_border` | `#8CCB9A` | `#2F6B43` |
| Atenção | `warning_text` | `#8A5300` | `#E8B04A` |
| Atenção | `warning_bg` | `#FFF3D6` | `#3B2F17` |
| Atenção | `warning_border` | `#F0C36D` | `#7A5C1F` |
| Perigo | `danger_text` | `#A82019` | `#F28B85` |
| Perigo | `danger_bg` | `#FDE7E5` | `#3F2220` |
| Perigo | `danger_border` | `#E8A09B` | `#8A3A36` |
| Informação | `info_text` | `#0F5290` | `#6DB6F2` |
| Informação | `info_bg` | `#E3F0FA` | `#1B3248` |
| Informação | `info_border` | `#9CC6EA` | `#2F5F8F` |

### Botões de ação semântica

Botões sólidos de confirmação e ações destrutivas possuem cores próprias:

| Token | Cor | Aplicação |
|---|---|---|
| `button_success_bg` | `#1E7B34` | Confirmar e concluir ações |
| `button_danger_bg` | `#B3261E` | Excluir e executar ações destrutivas |
| `button_semantic_text` | `#FFFFFF` | Texto dos botões |

Essas cores são específicas para botões sólidos e não substituem os tokens semânticos de texto, fundo e borda.

### Referências

As imagens são referências visuais, não capturas da aplicação implementada:
[tema claro](tema-claro.png) e [tema escuro](tema-escuro.png).
Para capturas do tema anterior e medições da proposta original, consulte a
[linha de base de Clientes e contraste](base_clientes_contraste.md).

## 3. Regras de utilização

1. Não utilizar cores hexadecimais diretamente nos componentes da interface.
2. Toda cor deve ser referenciada por um token de `CoresPaleta`.
3. O azul de acento não deve ser utilizado indiscriminadamente como decoração.
4. Cores semânticas devem representar estados reais do sistema.
5. Botões de exclusão devem utilizar o padrão de perigo.
6. Botões de confirmação devem utilizar o padrão de sucesso quando a ação justificar destaque semântico.
7. Estados desabilitados devem preservar legibilidade e contraste.
8. A linha selecionada deve manter contraste adequado entre fundo e texto.
9. O tema claro deve ser utilizado por padrão em novas instalações.
10. A preferência de tema deve ser persistida nas configurações.

## 4. Implementação e evolução

`mainerp/ui/theme_tokens.py` define cores e dimensões dos dois temas;
`CoresPaleta` adapta esses tokens aos seletores existentes em `styles.py`, e
`ConstrutorEstilos` gera o QSS. A inicialização aplica o tema à paleta Qt e ao QSS.
As cores de estados usadas pelas listagens e diálogos são obtidas do tema ativo.
O QSS é centralizado em `styles.py`: propriedades dos widgets identificam os
estilos e os estados dinâmicos são reaplicados quando mudam. As tabelas de vendas
e produtos usam o seletor de linhas compactas; a altura das seções continua
configurada pelas próprias listagens.

O Qt Fusion é usado como estilo-base dos widgets, com raio zero no QSS para os
controles da aplicação. As bordas externas e a barra de título de janelas nativas,
assim como diálogos nativos do Windows para arquivos, continuam sob controle do
sistema operacional e podem manter cantos arredondados. O Fusion reduz diferenças
entre estilos nativos, mas não garante aparência idêntica entre versões e escalas
do Windows; elas ainda exigem inspeção visual.

Os ícones de navegação e ações são SVGs locais do Lucide 0.468.0, renderizados com
tokens do tema e variantes para seleção e desativação. O conjunto usa licença ISC;
alguns ícones derivam do Feather, sob licença MIT. Os textos integrais das licenças
acompanham os SVGs em `mainerp/ui/icons/` e são incluídos nas releases e no instalador.
Mensagens de estado usam texto explícito e os avisos nativos, sem depender de emoji.

O splash de inicialização usa as cores do tema ativo, superfícies planas e bordas
retas. Ele mantém as mensagens das etapas reais, sem apresentar progresso simulado.
Seu tamanho lógico é preservado e a imagem é desenhada na escala da tela principal.

Em **Configurações > Aparência**, selecione Claro ou Escuro e clique em **Salvar tema**;
a escolha entra em vigor na próxima abertura. Sem arquivo de configuração, o padrão é
claro; arquivos existentes sem preferência ou com preferência inválida usam escuro.
Um valor inválido gera aviso no log e não é sobrescrito automaticamente. Se o arquivo
de configuração não puder ser lido ou a gravação falhar, a alteração é recusada e
uma mensagem é exibida. A preferência antiga explícita `dark` permanece escura, mas
usa a nova paleta, não a aparência antiga.

A fonte continua com base Segoe UI 12 pt; `appearance.font_size` não é usada para
defini-la. Há tamanhos em pixels no QSS. Os testes de contraste cobrem combinações
previstas; não substituem a avaliação dos widgets, de todos os estados ou das escalas
do Windows.

### Caminho incremental

Cada etapa deve ser pequena e preservar o funcionamento anterior até ser validada:

1. **Linha de base:** registrar capturas da listagem e do diálogo de Clientes, com dados
   fictícios e estados de foco, seleção, desativação e aviso; anotar resolução e escala.
   Inventariar os estilos locais e regras funcionais dessas telas antes de alterá-las.
2. **Contraste:** medir os pares texto/fundo realmente usados nos dois temas, incluindo
   estados de interação e seleção; revisar valores que não atendam à meta antes de
   adotar a paleta. Uma amostra de pares não valida a paleta inteira.
3. **Fundação e preferência:** tokens, aplicação e persistência foram implementados;
   ampliar a validação visual, em especial nas telas e nos estados menos frequentes.
   Preservar as classes semânticas e a compatibilidade dos chamadores.
5. **Protótipo limitado:** aplicar o padrão a Clientes e seu diálogo e comparar com a
   linha de base. Preservar filtros, ordenação, seleção, atalhos, cadastro e validações.
   Depois de validado, expandir em lotes pequenos para outras telas e navegação.
6. **Consolidação:** migrar estilos locais gradualmente, inclusive backup e restauração.
   Introduzir verificações automatizadas por componentes já migrados; uma proibição
   global de cores ou raios antes da migração faria o projeto atual falhar.
7. **Ícones e relatórios:** escolher ícones e conferir licença e inclusão na release.
   O gerador atual inclui arquivos Python dos pacotes autorizados, não SVGs
   automaticamente. Alinhar PDFs após a escolha dos componentes da Fase 4.2.

Antes de mudar dimensões, conferir `mainerp/ui/tabela.py`: a listagem padrão fixa linhas
em 22 unidades Qt. Validar o resultado com fonte e escala reais no Windows em vez de
assumir equivalência entre pixels do QSS, pontos da fonte e pixels físicos. Avaliar
`Fusion` em protótipo, pois uma mudança global de estilo pode afetar telas não migradas.

## 5. Validação

Em cada lote, usar uma instalação ou dados de teste isolados e:

- Medir contraste de combinações efetivamente exibidas e conferir foco, estados ativos,
  desabilitados, seleção, mensagens e legibilidade sem depender apenas de cor.
- Conferir os temas em 100%, 125% e 150% no Windows, incluindo textos longos,
  redimensionamento, cortes e acesso aos controles. Capturas offscreen ajudam na
  regressão, mas não substituem a conferência visual nessas escalas.
- Comparar as telas migradas com a linha de base e verificar navegação por teclado,
  filtros, ordenação, seleção, ações e comportamento dos diálogos.
- Executar testes Qt relevantes para os dois temas e os fluxos afetados; ao alterar
  empacotamento, conferir o conteúdo da release e uma instalação isolada.
- Impedir novos estilos fora do padrão nos componentes já migrados e ampliar a
  verificação conforme os demais forem convertidos.

## 6. Relação com os relatórios

Os relatórios PDF devem seguir a mesma identidade visual do aplicativo.

Os relatórios atuais usam ReportLab. A Fase 4.2 ainda avaliará o motor e os componentes
compartilhados; não há decisão de usar template HTML. Após essa escolha, adaptar a
identidade aos documentos e validar contraste e impressão, sem pressupor que o tema
escuro da interface seja apropriado para papel.
