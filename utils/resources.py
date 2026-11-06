import os

from PyQt6.QtGui import QIcon

from paths import CODE_DIR


def resource_path(relative_path: str) -> str:
    """Caminho de um recurso (ex.: icon.ico) dentro da pasta do código."""
    return os.path.join(str(CODE_DIR), relative_path)


def app_icon() -> QIcon:
    return QIcon(resource_path("icon.ico"))
