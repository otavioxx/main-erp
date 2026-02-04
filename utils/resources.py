import os
import sys
from PyQt6.QtGui import QIcon


def resource_path(relative_path: str) -> str:
    """
    Retorna o caminho correto tanto em dev quanto no PyInstaller
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def app_icon() -> QIcon:
    return QIcon(resource_path("icon.ico"))
