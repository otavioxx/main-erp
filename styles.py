"""
Sistema de Estilos Modular para PyQt6 - VERSÃO SIMPLIFICADA
Tema Dark Clean único com suporte a customização e status bar escura
"""

from dataclasses import dataclass
from typing import Optional

from PyQt6.QtGui import QColor, QFont, QPalette


@dataclass
class CoresPaleta:
    """Classe para organizar as cores do tema dark"""
    
    # Cores primárias - mais escuras
    background_primary: str = "#1a1a1a"  # Mais escuro
    background_secondary: str = "#202020"  # Mais escuro
    background_tertiary: str = "#252525"  # Mais escuro
    
    # Cores de texto
    text_primary: str = "#b9b9b9"  # Ligeiramente mais claro
    text_secondary: str = "#a09f9f"  # Mais claro
    text_muted: str = "#707070"
    text_disabled: str = "#2E2D2D"  # Mais escuro
    
    # Cores de acento
    accent_primary: str = "#1A4968"
    accent_hover: str = "#0c5991"
    accent_pressed: str = "#024f83"
    
    # Cores de borda - mais escuras
    border_primary: str = "#333333"  # Mais escuro
    border_secondary: str = "#404040"  # Mais escuro
    border_focus: str = "#025a94"
    
    # Cores semânticas
    success: str = "#2d5a2d"
    success_border: str = "#3d6b3d"
    warning: str = "#5a4d2d"
    warning_border: str = "#6b5d3d"
    danger: str = "#5a2d2d"
    danger_border: str = "#6b3d3d"
    
    # Cores de seleção
    selection_bg: str = "#025a94"
    selection_text: str = "#ffffff"
    hover_bg: str = "#2a2a2a"  # Mais escuro


class ConfiguracaoFonte:
    """Configurações de fonte"""
    
    def __init__(self, familia: str = "Segoe UI", tamanho_base: int = 12):
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
        """
    
    def _estilo_botoes(self) -> str:
        """Estilos para botões"""
        return f"""
        QPushButton {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: 1px solid {self.cores.border_secondary};
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 400;
            font-size: {self.fonte.tamanho_pequeno}px;
            min-width: 70px;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
        }}
        
        QPushButton:pressed {{
            background-color: {self.cores.background_secondary};
        }}
        
        QPushButton:disabled {{
            background-color: {self.cores.background_secondary};
            color: {self.cores.text_disabled};
            border-color: {self.cores.border_primary};
        }}
        
        QPushButton[class="success"] {{
            background-color: {self.cores.success};
            border-color: {self.cores.success_border};
        }}
        
        QPushButton[class="danger"] {{
            background-color: {self.cores.danger};
            border-color: {self.cores.danger_border};
        }}
        
        QPushButton[class="warning"] {{
            background-color: {self.cores.warning};
            border-color: {self.cores.warning_border};
            color: {self.cores.text_primary};
        }}
        
        QPushButton[class="primary"] {{
            background-color: {self.cores.accent_primary};
            border-color: {self.cores.accent_hover};
            color: {self.cores.selection_text};
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {self.cores.accent_hover};
        }}
        
        QPushButton[class="secondary"] {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
            color: {self.cores.text_primary};
        }}
        """
    
    def _estilo_combobox(self) -> str:
        """Estilos para ComboBox estilo Windows 11"""
        return f"""
        QComboBox {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: 1px solid {self.cores.border_secondary};
            border-radius: 4px;
            padding: 5px 8px;
            font-size: {self.fonte.tamanho_pequeno}px;
            min-height: 20px;
            selection-background-color: {self.cores.selection_bg};
        }}
        
        QComboBox:hover {{
            background-color: {self.cores.hover_bg};
            border-color: {self.cores.border_primary};
        }}
        
        QComboBox:focus {{
            border: 1px solid {self.cores.border_focus};
            background-color: {self.cores.hover_bg};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid {self.cores.border_secondary};
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            background-color: transparent;
        }}
        
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {self.cores.text_secondary};
            margin: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {self.cores.background_tertiary};
            border: 1px solid {self.cores.border_secondary};
            border-radius: 4px;
            padding: 2px;
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            height: 28px;
            padding: 4px 8px;
            border-radius: 2px;
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
            background-color: {self.cores.background_secondary};
            border: 1px solid {self.cores.border_primary};
            border-radius: 2px;
            gridline-color: {self.cores.border_primary};
            alternate-background-color: {self.cores.background_tertiary};
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            font-size: {self.fonte.tamanho_pequeno}px;
            outline: 0;
        }}
        
        QTableWidget::item {{
            padding: 4px 6px;
            border-bottom: 1px solid {self.cores.border_primary};
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
            background-color: #2f2f2f;
        }}
        
        /* Quando a linha está selecionada E tem hover */
        QTableWidget::item:selected:hover {{
            background-color: {self.cores.accent_hover};
        }}
        
        /* Estilo específico para células inativas com hover */
        QTableWidget::item[class="inativo"]:hover {{
            background-color: #3a2525;
        }}
        
        QHeaderView::section {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_secondary};
            padding: 6px 8px;
            border: none;
            border-right: 1px solid {self.cores.border_primary};
            border-bottom: 1px solid {self.cores.border_secondary};
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
            border-radius: 6px;
        }}
        
        QTableWidget QScrollBar::handle:vertical {{
            background-color: {self.cores.border_secondary};
            border-radius: 6px;
            min-height: 20px;
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
            border: 1px solid {self.cores.border_secondary};
            border-radius: 3px;
            padding: 5px 8px;
            font-size: {self.fonte.tamanho_pequeno}px;
            selection-background-color: {self.cores.selection_bg};
            selection-color: {self.cores.selection_text};
            min-height: 20px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {self.cores.border_focus};
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
            border: 1px solid {self.cores.border_primary};
            border-radius: 6px;
            background-color: {self.cores.background_secondary};
            margin: 4px;
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {self.cores.text_secondary};
            padding: 8px 16px;
            margin-right: 2px;
            border: none;
            border-bottom: 2px solid transparent;
            font-weight: 400;
            font-size: {self.fonte.tamanho_base}px;
        }}
        
        QTabBar::tab:selected {{
            color: {self.cores.accent_primary};
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
            border: 1px solid {self.cores.border_primary};
            background-color: transparent;
        }}
        
        QCheckBox::indicator {{
            border-radius: 3px;
        }}
        
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {self.cores.accent_primary};
            border: 1px solid {self.cores.accent_primary};
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
            border-radius: 4px;
        }}
        
        /* Barras verticais */
        QScrollBar:vertical {{
            width: 8px;
            border-radius: 4px;
        }}
        
        /* Handle (a parte que arrastamos) */
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {{
            background-color: {self.cores.border_primary};
            border-radius: 4px;
            min-height: 20px;
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
            border-top: 1px solid {self.cores.border_primary};
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
            border-radius: 12px;
            min-width: 25px;
            text-align: center;
        }}
        
        QLabel[class="key-indicator-active"] {{
            color: #ffffff;
            font-weight: bold;
            border: 2px solid;
            padding: 3px 6px;
            border-radius: 12px;
            min-width: 25px;
            text-align: center;
        }}
        
        QLabel[class="key-indicator-inactive"] {{
            color: {self.cores.text_disabled};
            background: {self.cores.background_tertiary};
            border: 1px solid {self.cores.border_secondary};
            padding: 3px 6px;
            border-radius: 12px;
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
            background-color: {self.cores.background_secondary};
            border-right: 1px solid {self.cores.border_primary};
        }}
        
        /* Título da sidebar */
        QLabel[class="sidebar-title"] {{
            font-size: 34px;
            font-weight: bold;
            color: {self.cores.accent_primary};
            padding: 10px;
            border-bottom: 2px solid {self.cores.border_primary};
            margin-bottom: 15px;
            background-color: transparent;
        }}
        
        /* Botões de navegação na sidebar */
        QPushButton[class="nav-button"] {{
            background-color: transparent;
            color: {self.cores.text_secondary};
            border: none;
            padding: 12px 15px;
            text-align: left;
            font-size: 14px;
            font-weight: 500;
            border-radius: 6px;
            margin: 2px 5px;
        }}
        
        QPushButton[class="nav-button"]:hover {{
            background-color: {self.cores.hover_bg};
            color: {self.cores.text_primary};
        }}
        
        QPushButton[class="nav-button"]:checked {{
            background-color: {self.cores.accent_primary};
            color: {self.cores.selection_text};
            font-weight: 600;
        }}
        
        QPushButton[class="nav-button"]:pressed {{
            background-color: {self.cores.accent_pressed};
        }}
        
        /* Status bar */
        QStatusBar[class="main-statusbar"] {{
            background-color: {self.cores.background_primary};
            border-top: 1px solid {self.cores.border_primary};
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
            border: 1px solid {self.cores.border_primary};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 5px;
            background-color: {self.cores.background_secondary};
            padding-bottom: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 1px 2px;
            color: {self.cores.selection_text};
            border-radius: 1px;
            margin-left: 5px;
            font-weight: 500;
        }}
        
        QMenu {{
            background-color: {self.cores.background_tertiary};
            border: 1px solid {self.cores.border_secondary};
            border-radius: 4px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 16px;
            border-radius: 2px;
            font-size: {self.fonte.tamanho_pequeno}px;
        }}
        
        QMenu::item:selected {{
            background-color: {self.cores.accent_primary};
        }}
        
        QToolTip {{
            background-color: {self.cores.background_tertiary};
            color: {self.cores.text_primary};
            border: 1px solid {self.cores.border_secondary};
            border-radius: 3px;
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
            color: {self.cores.accent_primary};
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
            background-color: #4a2a2a;
            color: #ff6b6b;
        }}
        
        QTableWidgetItem[class="pendente"] {{
            background-color: #4a3a2a;
            color: #ff8c42;
        }}
        
        QTableWidgetItem[class="concluido"] {{
            background-color: #2a4a2a;
            color: #51cf66;
        }}
        
        QTableWidgetItem[class="novo"] {{
            background-color: #4a2a4a;
            color: #ff6b9d;
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


def aplicar_tema_dark(app, fonte_customizada: Optional[ConfiguracaoFonte] = None):
    """
    Aplica o tema dark à aplicação PyQt6
    
    Args:
        app: Instância da aplicação PyQt6
        fonte_customizada: Configuração personalizada de fonte
    """
    # Configuração da fonte
    if fonte_customizada is None:
        fonte_customizada = ConfiguracaoFonte()
    
    fonte = QFont(fonte_customizada.familia, fonte_customizada.tamanho_base)
    app.setFont(fonte)
    
    # Usar cores padrão do tema dark
    cores = CoresPaleta()
    
    # Configurar paleta nativa
    configurar_paleta_qt(app, cores)
    
    # Construir e aplicar stylesheet
    construtor = ConstrutorEstilos(cores, fonte_customizada)
    stylesheet = construtor.construir_stylesheet()
    app.setStyleSheet(stylesheet)


def aplicar_estilos(app, fonte_customizada: Optional[ConfiguracaoFonte] = None):
    """
    Função principal para aplicar estilos (mantida para compatibilidade)
    """
    aplicar_tema_dark(app, fonte_customizada)