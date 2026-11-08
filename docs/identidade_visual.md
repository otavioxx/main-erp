# Identidade Visual — MainERP

## 1. Direção visual

O MainERP adota uma identidade visual inspirada em sistemas ERP corporativos, priorizando sobriedade, legibilidade, consistência e densidade de informação.

Princípios:

- Azul-marinho institucional na navegação.
- Cinzas neutros nas superfícies e áreas de trabalho.
- Um único azul de acento para ações primárias, foco e links.
- Cores vivas exclusivamente para estados semânticos: sucesso, atenção, perigo e informação.
- Bordas retas de 1 px, sem arredondamentos, sombras ou gradientes.
- Ícones monocromáticos.
- Tema claro como padrão e tema escuro como opção.
- Contraste mínimo de 4,5:1 para textos normais.
- Aparência compacta, sem comprometer a legibilidade.

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
| `text_muted` | `#5C6875` | `#8795A3` | Dicas e metadados |

### Navegação institucional

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `nav_bg` | `#0B2A4A` | `#121A23` | Barra lateral e barra de status |
| `nav_hover` | `#14406E` | `#1C2A3A` | Item ativo ou sob o mouse |
| `nav_text` | `#DCE6F0` | `#C9D3DD` | Texto da navegação |

### Cor de acento

| Token | Claro | Escuro | Aplicação |
|---|---|---|---|
| `accent` | `#1565A8` | `#2B6CB0` | Botões primários, foco e links |
| `accent_hover` | `#0F5290` | `#2F78C4` | Hover de ações primárias |

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

Imagens de referencia:
Tema claro: docs\tema-claro.png
Tema escuro: docs\tema-escuro.png
HTML: docs\previa_paleta_erp_claro_escuro.html

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

## 4. Implementação

A implementação deve ser centralizada em `mainerp/ui/styles.py`, utilizando:

- `CoresPaleta`: definição dos tokens e valores por tema.
- `ConstrutorEstilos`: geração dos estilos dos componentes a partir dos tokens.
- Tema claro e tema escuro: seleção dos valores conforme a configuração ativa.

Nenhuma tela ou diálogo deve manter uma paleta própria independente.

## 5. Validação

Antes da aplicação definitiva:

- Validar contraste de textos, controles, estados e seleção.
- Conferir os temas em escalas de 100%, 125% e 150% no Windows.
- Verificar consistência visual entre telas, diálogos, tabelas e relatórios.
- Executar testes automatizados de aplicação dos temas.
- Garantir que novas telas não introduzam cores fixas fora da paleta oficial.

## 6. Relação com os relatórios

Os relatórios PDF devem seguir a mesma identidade visual do aplicativo.

O template compartilhado `mainerp/reports/templates/base.html`, previsto na Fase 4.2, deverá utilizar os mesmos valores da paleta oficial, mantendo consistência entre a interface e os documentos gerados.
