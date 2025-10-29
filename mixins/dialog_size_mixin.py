"""
Mixin para dimensionamento inteligente de diálogos
Adaptado automaticamente ao tamanho da tela e conteúdo
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


class DialogSizeMixin:
    """
    Mixin para gerenciar tamanho e posição de diálogos de forma inteligente.
    
    Características:
    - Redimensionamento responsivo baseado no tamanho da tela
    - Centralização automática na tela
    - Suporte a múltiplos monitores
    - Tamanho máximo/mínimo inteligente
    - Posicionamento relativo à janela pai
    
    Uso:
        class MinhaDialog(DialogSizeMixin, QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                # ... sua inicialização
                self.setup_dialog_size(
                    min_width=400,
                    min_height=300,
                    default_width_percent=0.5,  # 50% da tela
                    default_height_percent=0.6  # 60% da tela
                )
    """

    def setup_dialog_size(
        self,
        min_width=300,
        min_height=200,
        default_width_percent=0.6,
        default_height_percent=0.7,
        max_width_percent=0.95,
        max_height_percent=0.95,
    ):
        """
        Configura o tamanho inteligente do diálogo
        
        Args:
            min_width: Largura mínima em pixels
            min_height: Altura mínima em pixels
            default_width_percent: Percentual da tela para largura padrão (0.0-1.0)
            default_height_percent: Percentual da tela para altura padrão (0.0-1.0)
            max_width_percent: Percentual máximo da tela para largura
            max_height_percent: Percentual máximo da tela para altura
        """
        # Obter dimensões da tela
        screen = self._get_screen_geometry()

        # Calcular tamanho padrão baseado no percentual
        default_width = max(
            min_width, int(screen.width() * default_width_percent)
        )
        default_height = max(
            min_height, int(screen.height() * default_height_percent)
        )

        # Calcular tamanho máximo
        max_width = int(screen.width() * max_width_percent)
        max_height = int(screen.height() * max_height_percent)

        # Aplicar limites
        default_width = min(default_width, max_width)
        default_height = min(default_height, max_height)

        # Configurar tamanho mínimo
        self.setMinimumSize(min_width, min_height)

        # Configurar tamanho padrão
        self.resize(default_width, default_height)

        # Centralizar na tela
        self._center_on_screen()

    def setup_dialog_size_fixed(self, width, height):
        """
        Configura tamanho fixo com segurança (não ultrapassa tela)
        
        Args:
            width: Largura desejada
            height: Altura desejada
        """
        screen = self._get_screen_geometry()

        # Limitar ao tamanho da tela
        safe_width = min(width, int(screen.width() * 0.95))
        safe_height = min(height, int(screen.height() * 0.95))

        self.setFixedSize(safe_width, safe_height)
        self._center_on_screen()

    def setup_dialog_size_compact(self):
        """Configura tamanho compacto (bom para diálogos pequenos)"""
        self.setup_dialog_size(
            min_width=300,
            min_height=150,
            default_width_percent=0.35,
            default_height_percent=0.4,
        )

    def setup_dialog_size_medium(self):
        """Configura tamanho médio (padrão para maioria dos diálogos)"""
        self.setup_dialog_size(
            min_width=400,
            min_height=300,
            default_width_percent=0.5,
            default_height_percent=0.6,
        )

    def setup_dialog_size_large(self):
        """Configura tamanho grande (para diálogos com muitas informações)"""
        self.setup_dialog_size(
            min_width=600,
            min_height=400,
            default_width_percent=0.75,
            default_height_percent=0.8,
        )

    def setup_dialog_size_fullscreen(self):
        """Configura tamanho próximo ao fullscreen"""
        self.setup_dialog_size(
            min_width=800,
            min_height=600,
            default_width_percent=0.9,
            default_height_percent=0.9,
        )

    def _get_screen_geometry(self):
        """Obtém a geometria da tela (considera múltiplos monitores)"""
        if self.parent():
            # Se tem parent, usa a tela onde o parent está
            screen = self.parent().screen()
            if screen:
                return screen.geometry()
        
        # Usa a tela primária
        app = QApplication.instance()
        if app and app.primaryScreen():
            return app.primaryScreen().geometry()
        
        # Fallback: retorna um tamanho padrão
        return Qt.rect(0, 0, 1920, 1080)

    def _center_on_screen(self):
        """Centraliza o diálogo na tela (ou na janela pai se existir)"""
        screen = self._get_screen_geometry()

        # Calcular posição central
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2

        self.move(x, y)

    def position_near_parent(self, offset_x=20, offset_y=20):
        """
        Posiciona o diálogo próximo à janela pai (sem sobrepor completamente)
        
        Args:
            offset_x: Deslocamento horizontal
            offset_y: Deslocamento vertical
        """
        if not self.parent():
            self._center_on_screen()
            return

        parent = self.parent()
        parent_geometry = parent.geometry()

        # Posicionar ao lado do pai
        x = parent_geometry.x() + parent_geometry.width() + offset_x
        y = parent_geometry.y() + offset_y

        # Ajustar se sair da tela
        screen = self._get_screen_geometry()
        if x + self.width() > screen.x() + screen.width():
            x = parent_geometry.x() - self.width() - offset_x

        if y + self.height() > screen.y() + screen.height():
            y = screen.y() + screen.height() - self.height() - 20

        self.move(x, y)

    def make_resizable(self):
        """Permite redimensionar o diálogo (não ativa por padrão)"""
        # Remove qualquer flag que impeça redimensionamento
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), 
                          self.sizePolicy().verticalPolicy())

    def ensure_visible(self):
        """Garante que o diálogo está totalmente visível na tela"""
        screen = self._get_screen_geometry()
        geometry = self.geometry()

        # Verificar se está fora dos limites
        if geometry.right() > screen.right():
            self.move(screen.right() - geometry.width(), geometry.y())

        if geometry.bottom() > screen.bottom():
            self.move(geometry.x(), screen.bottom() - geometry.height())

        if geometry.x() < screen.x():
            self.move(screen.x(), geometry.y())

        if geometry.y() < screen.y():
            self.move(geometry.x(), screen.y())