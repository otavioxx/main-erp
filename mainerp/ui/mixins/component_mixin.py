from typing import Any

from PyQt6.QtWidgets import QWidget


class ComponentMixin(QWidget):
    def __getattr__(self, name: str) -> Any:
        return getattr(super(), name)
