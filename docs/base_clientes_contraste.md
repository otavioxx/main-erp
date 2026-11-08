# Linha de base de Clientes e contraste da paleta

Registro anterior à implementação da Fase 4.3. As capturas mostram o **tema escuro
anterior**, enquanto as medições abaixo usam os valores **propostos originalmente**.
Os temas agora implementados ajustam alguns valores; consulte
[identidade visual](identidade_visual.md) para a paleta atual. As tabelas abaixo
permanecem como registro histórico e não são uma medição da implementação.

## Capturas da interface atual

Produzidas em Windows, com PyQt 6.12.0 e Qt 6.12.0, backend `windows`, tela de
1920 × 1080, DPI lógico 96 e fator de escala Qt 1 (DPR 1). O tema aplicado foi o
mesmo `aplicar_tema_dark` usado na inicialização; a fonte configurada na aplicação
é Segoe UI 12 pt, embora existam tamanhos em pixels no QSS.

As imagens foram obtidas com `QWidget.grab()`, sem moldura da janela ou barra lateral.
Foram instanciados diretamente a listagem e o diálogo, com busca de clientes
substituída por três registros fictícios em memória; não foi usado banco de produção.
O diálogo de aviso usa o fluxo de aviso da própria tela. Os nomes, documentos, telefones
e endereços nas imagens são exemplos fictícios.

| Captura | Área em pixels | Cenário |
|---|---:|---|
| [Listagem e seleção](base-clientes/clientes-selecao.png) | 1180 × 720 | Filtro de ativos, linha selecionada e foco na tabela |
| [Inativo e foco](base-clientes/clientes-inativos-foco.png) | 1180 × 720 | Filtro de todos, registro inativo e foco na busca |
| [Diálogo de cliente](base-clientes/cliente-dialogo.png) | 500 × 650 | Cliente ativo preenchido e foco no nome |
| [Botão desabilitado](base-clientes/clientes-botao-desabilitado.png) | 1180 × 720 | `Editar` desabilitado artificialmente para observar o estilo |
| [Aviso](base-clientes/clientes-aviso.png) | 237 × 103 | Aviso “Selecione um cliente para editar” |

Na captura do botão desabilitado, o estado foi forçado para teste; não é uma regra
atual de habilitação da tela. O PNG é idêntico ao da captura imediatamente anterior,
com o botão habilitado: investigar as regras QSS e conferir a diferenciação ao implantar
o novo tema, sem presumir que a captura por si só explica a causa. Na listagem atual,
o inativo recebe cores específicas no item; verificar seleção e hover também ao migrar.

**Limites:** essas capturas são de componentes isolados, sem navegação principal, e
não comprovam comportamento, atalhos, acessibilidade ou impressão. Foram obtidas
apenas em 100%: repetir a comparação visual em 125% e 150% no Windows, inclusive com
textos longos, janela redimensionada e interações reais. Não são uma validação dos
temas propostos nem substituem testes funcionais.

### Comportamentos a preservar no protótipo

- Busca por nome, CPF/CNPJ, telefone, email, endereço e observação; limpeza do filtro.
- Alternância F11 entre clientes ativos e todos, com indicação do filtro; destaque de
  registros inativos, sem depender somente da cor na solução futura.
- Tabela com seleção de linha única, ordenação, navegação pelo scroll e altura padrão
  de 22 unidades Qt; manter as colunas, dados e indicação de observações.
- Ações de criar, editar, inativar e reativar, confirmação de inativação e avisos;
  no diálogo, dados pessoais, contato, observações, estado ativo e confirmação/cancelamento.

## Medição da paleta proposta

Valores calculados a partir dos hexadecimais documentados, usando luminância relativa
sRGB e razão `(Lmais_clara + 0,05) / (Lmais_escura + 0,05)`. Os valores são exibidos
com duas casas; a comparação com o limite usa a razão sem arredondar. Para texto normal,
a meta adotada é **4,5:1**. Para indicadores visuais necessários ao uso, examina-se
**3:1** contra as cores adjacentes; uma borda decorativa não é automaticamente um
indicador necessário. Texto de controles inativos é dispensado do critério WCAG de
contraste de texto, mas continua relevante para a legibilidade prevista no projeto.

As combinações são candidatas para projeto, não pares já exibidos pelo aplicativo.
Alguns usos, como texto branco em botão de acento, são hipóteses para medição; o projeto
ainda precisa especificar os tokens de texto e os estados reais de cada componente.

### Textos sobre superfícies

Cada célula contém contraste do tema **claro / escuro**. Valores abaixo de 4,5:1
estão em negrito.

| Texto | `background_window` | `surface` | `surface_alt` | `table_header` | `hover_bg` |
|---|---:|---:|---:|---:|---:|
| `text_primary` | 13,02 / 13,19 | 14,76 / 11,68 | 13,75 / 10,46 | 11,85 / 9,47 | 12,82 / 9,76 |
| `text_secondary` | 6,24 / 8,23 | 7,07 / 7,29 | 6,59 / 6,53 | 5,68 / 5,91 | 6,15 / 6,09 |
| `text_muted` | 5,02 / 5,41 | 5,69 / 4,79 | 5,30 / **4,29** | 4,57 / **3,89** | 4,94 / **4,00** |

`text_muted` escuro não deve ser usado como texto normal sobre os três fundos destacados
sem ajuste. A combinação clara com `table_header` passa por pequena margem (4,5683:1);
rever também se cores, opacidade ou renderização forem alteradas.

### Navegação, seleção, mensagens e botões

| Texto / fundo | Claro | Escuro |
|---|---:|---:|
| `nav_text` / `nav_bg` | 11,51 | 11,56 |
| `nav_text` / `nav_hover` | 8,36 | 9,60 |
| `selection_text` / `selection_bg` | 11,06 | 8,66 |
| `success_text` / `success_bg` | 5,74 | 6,46 |
| `warning_text` / `warning_bg` | 5,74 | 6,69 |
| `danger_text` / `danger_bg` | 6,15 | 6,03 |
| `info_text` / `info_bg` | 6,89 | 6,03 |
| `button_semantic_text` / `button_success_bg` | 5,33 | 5,33 |
| `button_semantic_text` / `button_danger_bg` | 6,54 | 6,54 |
| Branco `#FFFFFF` / `accent` | 6,07 | 5,42 |
| Branco `#FFFFFF` / `accent_hover` | 7,98 | 4,56 |
| `accent` / `surface`, como texto ou link | 6,07 | **2,71** |
| `accent` / `background_window`, como texto ou link | 5,36 | **3,06** |

Os botões semânticos usam as mesmas cores nos dois temas. O branco sobre
`accent_hover` escuro passa por pequena margem (4,5607:1). No tema escuro, `accent`
não atende a 4,5:1 como texto normal sobre os dois fundos medidos; é necessário definir
uma cor de link adequada ou restringir esse uso antes da implementação.

### Indicadores e bordas

| Primeiro plano / fundo adjacente | Claro | Escuro |
|---|---:|---:|
| `border_input` / `surface` | 3,06 | 3,22 |
| `border_input` / `background_window` | **2,70** | 3,63 |
| `accent` / `surface`, como indicador de foco | 6,07 | **2,71** |
| `accent` / `background_window`, como indicador de foco | 5,36 | 3,06 |
| `success_border` / `success_bg` | 1,65 | 1,95 |
| `warning_border` / `warning_bg` | 1,50 | 2,10 |
| `danger_border` / `danger_bg` | 1,79 | 1,87 |
| `info_border` / `info_bg` | 1,55 | 1,98 |

Onde o contorno for necessário para identificar campo, foco ou estado, as combinações
abaixo de 3:1 exigem revisão ou outro indicador suficiente. As bordas semânticas
podem ser decorativas se texto e demais elementos transmitirem claramente o estado;
não usar os valores medidos como prova de conformidade dos componentes.

## Pendências antes da adoção

1. Definir os pares efetivos por componente e estado, inclusive foco, hover, seleção,
   links, ícones e controles desabilitados. A paleta ainda não especifica todos os
   fundos e textos desses estados; não é possível declarar contraste integral.
2. Corrigir ou restringir os pares que falham e medir também o contraste dos
   indicadores necessários contra **cada** superfície adjacente. Não alterar a
   paleta apenas com base em uma combinação que talvez não seja usada.
3. Implementar o protótipo isolado e repetir as medições e capturas com o QSS e
   `QPalette` efetivamente aplicados, incluindo alterações produzidas pelo Qt, seleção
   e opacidade. Validar visualmente em 100%, 125% e 150% no Windows.
