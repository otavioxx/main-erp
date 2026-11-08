"""Tema central da interface Qt."""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from mainerp.ui.theme_tokens import CLARO, DIMENSOES, ESCURO, CoresTema


class CoresPaleta:
    """Adapta os tokens aos seletores existentes durante a migração."""

    def __init__(self, tokens: CoresTema = CLARO):
        self.tokens = tokens
        self.background_primary = tokens.background_window
        self.background_secondary = tokens.surface
        self.background_tertiary = tokens.surface_alt
        self.text_primary = tokens.text_primary
        self.text_secondary = tokens.text_secondary
        self.text_muted = tokens.text_muted
        self.text_disabled = tokens.text_disabled
        self.accent_primary = tokens.accent
        self.accent_hover = tokens.accent_hover
        self.accent_pressed = tokens.accent_hover
        self.border_primary = tokens.border
        self.border_secondary = tokens.border_input
        self.border_focus = tokens.focus
        self.success = tokens.button_success_bg
        self.success_border = tokens.button_success_bg
        self.warning = tokens.warning_bg
        self.warning_border = tokens.warning_border
        self.danger = tokens.button_danger_bg
        self.danger_border = tokens.button_danger_bg
        self.selection_bg = tokens.selection_bg
        self.selection_text = tokens.selection_text
        self.hover_bg = tokens.hover_bg


class ConfiguracaoFonte:
    """Configurações de fonte"""

    def __init__(
        self, familia: str = DIMENSOES.fonte_familia,
        tamanho_base: int = DIMENSOES.fonte_tamanho_pt,
    ):
        self.familia = familia
        self.tamanho_base = tamanho_base
        self.tamanho_pequeno = tamanho_base - 1
        self.tamanho_medio = tamanho_base + 2
        self.tamanho_grande = tamanho_base + 7
        self.tamanho_titulo = tamanho_base + 11


class ConstrutorEstilos:
    """Construtor de estilos CSS baseado em template"""

    def __init__(self, cores: CoresPaleta, fonte: ConfiguracaoFonte):
        self.cores = cores
        self.fonte = fonte
        self.dimensoes = DIMENSOES

    def _estilo_widget_base(self) -> str:
        """Estilo base para todos os widgets"""
        return f"""
        QWidget {{
            background-color: {self.cores.background_primary};
            color: {self.cores.text_primary};
            font-family: '{self.fonte.familia}', -apple-system, BlinkMacSystemFont, sans-serif;
            border: none;
            outline: none;
        }}
        QDialog {{
            border-radius: {self.dimensoes.raio}px;
        }}
        """

    def _estilo_botoes(self) -> str:
        """Estilos para botões"""
        return f"""
        QPushButton {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            padding: 6px 12px;
            border-radius: {self.dimensoes.raio}px;
            font-weight: 400;
            font-size: {self.fonte.tamanho_pequeno}px;
            min-width: 70px;
            min-height: {self.dimensoes.altura_controle_minima}px;
        }}
        
        QPushButton:hover {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
        }}
        
        QPushButton:pressed {{
            background-color: {self.cores.background_secondary};
        }}
        
        QPushButton:disabled {{
            background-color: {self.cores.tokens.surface_disabled};
            color: {self.cores.text_disabled};
            border-color: {self.cores.border_primary};
        }}
        
        QPushButton[class="success"] {{
            background-color: {self.cores.success};
            border-color: {self.cores.success_border};
            color: {self.cores.tokens.button_semantic_text};
        }}
        
        QPushButton[class="danger"] {{
            background-color: {self.cores.danger};
            border-color: {self.cores.danger_border};
            color: {self.cores.tokens.button_semantic_text};
        }}

        QPushButton[class="success"]:hover, QPushButton[class="success"]:pressed {{
            background-color: {self.cores.success};
        }}
        QPushButton[class="danger"]:hover, QPushButton[class="danger"]:pressed {{
            background-color: {self.cores.danger};
        }}
        QPushButton[class="warning"]:hover, QPushButton[class="warning"]:pressed {{
            background-color: {self.cores.warning};
        }}
        
        QPushButton[class="warning"] {{
            background-color: {self.cores.warning};
            border-color: {self.cores.warning_border};
            color: {self.cores.tokens.warning_text};
        }}
        
        QPushButton[class="primary"] {{
            background-color: {self.cores.accent_primary};
            border-color: {self.cores.accent_hover};
            color: {self.cores.tokens.button_semantic_text};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {self.cores.accent_hover};
        }}
        
        QPushButton[class="secondary"] {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
            color: {self.cores.text_primary};
        }}

        QPushButton:disabled,
        QPushButton[class="success"]:disabled, QPushButton[class="danger"]:disabled,
        QPushButton[class="warning"]:disabled, QPushButton[class="primary"]:disabled,
        QPushButton[class="secondary"]:disabled, QPushButton[class="nav-button"]:disabled {{
            background-color: {self.cores.tokens.surface_disabled};
            color: {self.cores.text_disabled};
            border: {self.dimensoes.borda}px solid {self.cores.border_primary};
        }}
        """

    def _estilo_combobox(self) -> str:
        """Estilos para listas suspensas."""
        return f"""
        QComboBox {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            padding: 5px {self.dimensoes.espacamento}px;
            font-size: {self.fonte.tamanho_pequeno}px;
            min-height: {self.dimensoes.altura_controle_minima}px;
            selection-background-color: {self.cores.selection_bg};
        }}
        
        QComboBox:hover {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
        }}
        
        QComboBox:focus {{
            border: {self.dimensoes.borda}px solid {self.cores.border_focus};
            background-color: {self.cores.hover_bg};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {self.cores.background_tertiary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            padding: 2px;
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            height: 28px;
            padding: 4px 8px;
            border-radius: {self.dimensoes.raio}px;
            margin: 1px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {self.cores.hover_bg};
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {self.cores.selection_bg};
            color: {self.cores.selection_text};
        }}
        """

    def _estilo_tabelas(self) -> str:
        """Estilos para tabelas com hover melhorado"""
        return f"""
        QTableWidget {{
            background-color: {self.cores.tokens.surface};
            border: {self.dimensoes.borda}px solid {self.cores.border_primary};
            border-radius: {self.dimensoes.raio}px;
            gridline-color: {self.cores.border_primary};
            alternate-background-color: {self.cores.tokens.surface_alt};
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            font-size: {self.fonte.tamanho_pequeno}px;
            outline: 0;
        }}
        
        QTableWidget::item {{
            padding: 4px 6px;
            border-bottom: {self.dimensoes.borda}px solid {self.cores.border_primary};
            border-right: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {self.cores.selection_bg};
            color: {self.cores.selection_text};
        }}
        
        /* HOVER: Destaca toda a linha quando o mouse passa sobre qualquer célula */
        QTableWidget::item:hover {{
            background-color: {self.cores.hover_bg};
        }}
        
        /* Hover mais suave para linhas alternadas */
        QTableWidget::item:alternate:hover {{
            background-color: {self.cores.hover_bg};
        }}
        
        /* Quando a linha está selecionada E tem hover */
        QTableWidget::item:selected:hover {{
            background-color: {self.cores.selection_bg};
        }}
        
        /* Estilo específico para células inativas com hover */
        QTableWidget::item[class="inativo"]:hover {{
            background-color: {self.cores.tokens.danger_bg};
        }}
        
        QHeaderView::section {{
            background-color: {self.cores.tokens.table_header};
            color: {self.cores.text_secondary};
            padding: 6px 8px;
            border: none;
            border-right: {self.dimensoes.borda}px solid {self.cores.border_primary};
            border-bottom: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            font-weight: 500;
            font-size: {self.fonte.tamanho_pequeno}px;
        }}
        
        QHeaderView::section:hover {{
            background-color: {self.cores.hover_bg};
        }}
        
        /* Melhorar a visualização da barra de scroll da tabela */
        QTableWidget QScrollBar:vertical {{
            background-color: {self.cores.background_primary};
            border: none;
            width: 12px;
            border-radius: {self.dimensoes.raio}px;
        }}
        
        QTableWidget QScrollBar::handle:vertical {{
            background-color: {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            min-height: {self.dimensoes.altura_controle_minima}px;
        }}
        
        QTableWidget QScrollBar::handle:vertical:hover {{
            background-color: {self.cores.text_disabled};
        }}
        """

    def _estilo_inputs(self) -> str:
        """Estilos para campos de entrada"""
        return f"""
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            padding: 5px 8px;
            font-size: {self.fonte.tamanho_pequeno}px;
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            min-height: {self.dimensoes.altura_controle_minima}px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: {self.dimensoes.borda}px solid {self.cores.border_focus};
            background-color: {self.cores.hover_bg};
        }}
        
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            width: 0px;
            border: none;
        }}
        """

    def _estilo_tabs(self) -> str:
        """Estilos para abas"""
        return f"""
        QTabWidget::pane {{
            border: {self.dimensoes.borda}px solid {self.cores.border_primary};
            border-radius: {self.dimensoes.raio}px;
            background-color: {self.cores.background_secondary};
            margin: 4px;
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {self.cores.text_secondary};
            padding: 8px 16px;
            margin-right: 2px;
            border: none;
            border-radius: {self.dimensoes.raio}px;
            border-bottom: 2px solid transparent;
            font-weight: 400;
            font-size: {self.fonte.tamanho_base}px;
        }}
        
        QTabBar::tab:selected {{
            color: {self.cores.tokens.accent_text};
            border-bottom: 2px solid {self.cores.accent_primary};
            font-weight: 500;
        }}
        
        QTabBar::tab:hover {{
            color: {self.cores.text_primary};
            background-color: {self.cores.background_tertiary};
        }}
        """

    def _estilo_controles(self) -> str:
        """Estilos para checkboxes, radiobuttons, etc."""
        return f"""
        QCheckBox, QRadioButton {{
            spacing: 6px;
            color: {self.cores.text_secondary};
            font-size: {self.fonte.tamanho_pequeno}px;
            background-color: transparent;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: {self.dimensoes.borda}px solid {self.cores.border_primary};
            background-color: transparent;
        }}
        
        QCheckBox::indicator {{
            border-radius: {self.dimensoes.raio}px;
        }}
        
        QRadioButton::indicator {{
            border-radius: {self.dimensoes.raio}px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {self.cores.accent_primary};
            border: {self.dimensoes.borda}px solid {self.cores.accent_primary};
        }}
        """

    def _estilo_scrollbars(self) -> str:
        """Estilos para barras de rolagem - versão melhorada"""
        return f"""
        /* Estilo geral para todas as barras de rolagem */
        QScrollBar {{
            background-color: {self.cores.background_secondary};
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        
        /* Barras horizontais */
        QScrollBar:horizontal {{
            height: 8px;
            border-radius: {self.dimensoes.raio}px;
        }}
        
        /* Barras verticais */
        QScrollBar:vertical {{
            width: 8px;
            border-radius: {self.dimensoes.raio}px;
        }}
        
        /* Handle (a parte que arrastamos) */
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {{
            background-color: {self.cores.border_primary};
            border-radius: {self.dimensoes.raio}px;
            min-height: {self.dimensoes.altura_controle_minima}px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {{
            background-color: {self.cores.text_disabled};
        }}
        
        QScrollBar::handle:horizontal:pressed, QScrollBar::handle:vertical:pressed {{
            background-color: {self.cores.accent_primary};
        }}
        
        /* Botões de seta (normalmente escondidos em designs modernos) */
        QScrollBar::add-line, QScrollBar::sub-line {{
            background: none;
            border: none;
            height: 0px;
            width: 0px;
        }}
        
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}
        
        /* Estilo específico para áreas de texto */
        QTextEdit QScrollBar:vertical, QTextEdit QScrollBar:horizontal,
        QPlainTextEdit QScrollBar:vertical, QPlainTextEdit QScrollBar:horizontal {{
            background-color: {self.cores.background_primary};
        }}
        
        /* Estilo para tabelas */
        QTableWidget QScrollBar:vertical, QTableWidget QScrollBar:horizontal {{
            background-color: {self.cores.background_secondary};
        }}
        
        /* Estilo para listas */
        QListWidget QScrollBar:vertical, QListWidget QScrollBar:horizontal {{
            background-color: {self.cores.background_secondary};
        }}
        
        /* Estilo para tree views */
        QTreeWidget QScrollBar:vertical, QTreeWidget QScrollBar:horizontal {{
            background-color: {self.cores.background_secondary};
        }}
        """

    def _estilo_status_bar(self) -> str:
        """Estilos específicos para status bar"""
        return f"""
        QStatusBar {{
            background-color: {self.cores.background_primary};
            border-top: {self.dimensoes.borda}px solid {self.cores.border_primary};
            font-size: {self.fonte.tamanho_pequeno}px;
            color: {self.cores.text_secondary};
            padding: 2px 5px;
        }}
        
        QStatusBar::item {{
            border: none;
        }}
        
        /* Estilos para indicadores de teclas na status bar */
        QLabel[class="key-indicator"] {{
            font-size: 10px;
            font-weight: bold;
            padding: 3px 6px;
            border-radius: {self.dimensoes.raio}px;
            min-width: 25px;
            text-align: center;
        }}
        
        QLabel[class="key-indicator-active"] {{
            color: {self.cores.tokens.button_semantic_text};
            font-weight: bold;
            border: 2px solid;
            padding: 3px 6px;
            border-radius: {self.dimensoes.raio}px;
            min-width: 25px;
            text-align: center;
        }}
        
        QLabel[class="key-indicator-inactive"] {{
            color: {self.cores.text_disabled};
            background: {self.cores.background_tertiary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            padding: 3px 6px;
            border-radius: {self.dimensoes.raio}px;
            min-width: 25px;
            text-align: center;
        }}
        """

    def _estilo_sidebar(self) -> str:
        """Estilos específicos para barra lateral (sidebar)"""
        return f"""
        /* Estilos para a barra lateral principal */
        QFrame[class="sidebar"], 
        QWidget[class="sidebar"] {{
            background-color: {self.cores.tokens.nav_bg};
            border-right: {self.dimensoes.borda}px solid {self.cores.border_primary};
        }}
        
        /* Título da sidebar */
        QLabel[class="sidebar-title"] {{
            font-size: 34px;
            font-weight: bold;
            color: {self.cores.tokens.nav_text};
            padding: 10px;
            border-bottom: 2px solid {self.cores.border_primary};
            margin-bottom: 15px;
            background-color: transparent;
        }}
        
        /* Botões de navegação na sidebar */
        QPushButton[class="nav-button"] {{
            background-color: transparent;
            color: {self.cores.tokens.nav_text};
            border: none;
            padding: 12px 15px;
            text-align: left;
            font-size: 14px;
            font-weight: 500;
            border-radius: {self.dimensoes.raio}px;
            margin: 2px 5px;
        }}
        
        QPushButton[class="nav-button"]:hover {{
            background-color: {self.cores.tokens.nav_hover};
            color: {self.cores.tokens.nav_text};
        }}
        
        QPushButton[class="nav-button"]:checked {{
            background-color: {self.cores.accent_primary};
            color: {self.cores.tokens.button_semantic_text};
            font-weight: 600;
        }}
        
        QPushButton[class="nav-button"]:pressed {{
            background-color: {self.cores.accent_pressed};
        }}
        
        /* Status bar */
        QStatusBar[class="main-statusbar"] {{
            background-color: {self.cores.background_primary};
            border-top: {self.dimensoes.borda}px solid {self.cores.border_primary};
            font-size: 11px;
            color: {self.cores.text_secondary};
            padding: 2px 5px;
        }}
        
        /* Widget da status bar */
        QWidget[class="statusbar-widget"] {{
            background-color: transparent;
        }}
        
        QLabel[class="version-label"] {{
            color: {self.cores.text_muted};
            font-size: 11px;
            background-color: transparent;
        }}
        """

    def _estilo_extras(self) -> str:
        """Estilos extras (tooltips, menus, etc.)"""
        return f"""
        QGroupBox {{
            font-weight: 500;
            font-size: {self.fonte.tamanho_base}px;
            color: {self.cores.text_secondary};
            border: {self.dimensoes.borda}px solid {self.cores.border_primary};
            border-radius: {self.dimensoes.raio}px;
            margin-top: 12px;
            padding-top: 5px;
            background-color: {self.cores.background_secondary};
            padding-bottom: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 1px 2px;
            color: {self.cores.text_primary};
            border-radius: {self.dimensoes.raio}px;
            margin-left: 5px;
            font-weight: 500;
        }}
        
        QMenu {{
            background-color: {self.cores.background_tertiary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 16px;
            border-radius: {self.dimensoes.raio}px;
            font-size: {self.fonte.tamanho_pequeno}px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.cores.accent_primary};
            color: {self.cores.tokens.button_semantic_text};
        }}
        
        QToolTip {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: {self.dimensoes.borda}px solid {self.cores.border_secondary};
            border-radius: {self.dimensoes.raio}px;
            padding: 6px;
            font-size: {self.fonte.tamanho_pequeno}px;
        }}
        
        QLabel {{
            font-size: {self.fonte.tamanho_pequeno}px;
            color: {self.cores.text_secondary};
            font-weight: 400;
            background-color: transparent;
        }}
        
        QLabel[class="title"] {{
            font-size: {self.fonte.tamanho_titulo}px;
            font-weight: 500;
            color: {self.cores.text_primary};
            padding: 2px 0px;
        }}
        
        QLabel[class="highlight"] {{
            font-weight: bold;
            color: {self.cores.tokens.accent_text};
        }}
        
        QLabel[class="muted"] {{
            font-size: {self.fonte.tamanho_pequeno}px;
            color: {self.cores.text_muted};
            font-style: italic;
            font-weight: 400;
            background-color: transparent;
        }}
        
        /* Estilos para status de cadastros */
        QTableWidgetItem[class="inativo"] {{
            background-color: {self.cores.tokens.danger_bg};
            color: {self.cores.tokens.danger_text};
        }}
        
        QTableWidgetItem[class="pendente"] {{
            background-color: {self.cores.tokens.warning_bg};
            color: {self.cores.tokens.warning_text};
        }}
        
        QTableWidgetItem[class="concluido"] {{
            background-color: {self.cores.tokens.success_bg};
            color: {self.cores.tokens.success_text};
        }}
        
        QTableWidgetItem[class="novo"] {{
            background-color: {self.cores.tokens.info_bg};
            color: {self.cores.tokens.info_text};
        }}
        """

    def construir_stylesheet(self) -> str:
        """Constrói o stylesheet completo"""
        return "".join(
            [
                self._estilo_widget_base(),
                self._estilo_sidebar(),  # INCLUA O ESTILO DA SIDEBAR
                self._estilo_botoes(),
                self._estilo_tabelas(),
                self._estilo_inputs(),
                self._estilo_combobox(),
                self._estilo_tabs(),
                self._estilo_controles(),
                self._estilo_scrollbars(),
                self._estilo_status_bar(),
                self._estilo_extras(),
            ]
        )


def configurar_paleta_qt(app, cores: CoresPaleta):
    """Configura a paleta nativa do Qt"""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(cores.background_primary))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(cores.text_primary))
    palette.setColor(QPalette.ColorRole.Base, QColor(cores.background_tertiary))
    palette.setColor(
        QPalette.ColorRole.AlternateBase, QColor(cores.background_secondary)
    )
    palette.setColor(QPalette.ColorRole.Text, QColor(cores.text_primary))
    palette.setColor(QPalette.ColorRole.Button, QColor(cores.background_tertiary))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(cores.text_primary))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(cores.selection_bg))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cores.selection_text))
    app.setPalette(palette)


def aplicar_tema(app, tema: str, fonte_customizada: ConfiguracaoFonte | None = None):
    """Aplica o tema selecionado à paleta e ao stylesheet da aplicação."""
    if tema not in ("light", "dark"):
        raise ValueError(f"Tema desconhecido: {tema!r}")
    if app.setStyle("Fusion") is None:
        raise RuntimeError("Não foi possível aplicar o estilo Qt Fusion.")
    # Configuração da fonte - CORRIGIR VALIDAÇÃO
    if fonte_customizada is None:
        fonte_customizada = ConfiguracaoFonte()

    # VALIDAR tamanho da fonte
    if fonte_customizada.tamanho_base <= 0:
        fonte_customizada.tamanho_base = 12  # Valor padrão seguro
        fonte_customizada.tamanho_pequeno = 11
        fonte_customizada.tamanho_medio = 14
        fonte_customizada.tamanho_grande = 19
        fonte_customizada.tamanho_titulo = 23

    fonte = QFont(fonte_customizada.familia, fonte_customizada.tamanho_base)

    # VALIDAR tamanho da fonte Qt
    if fonte.pointSize() <= 0:
        fonte.setPointSize(12)  # Tamanho seguro

    app.setFont(fonte)

    cores = CoresPaleta(CLARO if tema == "light" else ESCURO)

    # Configurar paleta nativa
    configurar_paleta_qt(app, cores)

    # Construir e aplicar stylesheet
    construtor = ConstrutorEstilos(cores, fonte_customizada)
    stylesheet = construtor.construir_stylesheet()
    app.setStyleSheet(stylesheet)
    app.setProperty("mainerp_tema", tema)


def aplicar_tema_dark(app, fonte_customizada: ConfiguracaoFonte | None = None):
    """Compatibilidade para chamadores que solicitam explicitamente o tema escuro."""
    aplicar_tema(app, "dark", fonte_customizada)


def cores_ativas() -> CoresTema:
    app = QApplication.instance()
    return ESCURO if app is not None and app.property("mainerp_tema") == "dark" else CLARO


def aplicar_estilos(app, fonte_customizada: ConfiguracaoFonte | None = None):
    """
    Função principal para aplicar estilos (mantida para compatibilidade)
    """
    aplicar_tema_dark(app, fonte_customizada)
