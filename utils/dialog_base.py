"""
Classe base para diálogos centralizados
"""

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QDialog


class DialogBase(QDialog):
    """Classe base para diálogos que se centralizam automaticamente"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._centered = False

    def showEvent(self, event):
        """Centraliza o diálogo quando é mostrado"""
        super().showEvent(event)
        if not self._centered:
            self._centralizar_janela()
            self._centered = True

    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        # Se tiver um parent, centraliza em relação ao parent
        if self.parent():
            parent_geometry = self.parent().frameGeometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Se não tiver parent, centraliza na tela principal
            screen = QGuiApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def resizeEvent(self, event):
        """Recentraliza quando redimensionado"""
        super().resizeEvent(event)
        if self.isVisible():
            self._centralizar_janela()
