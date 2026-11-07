from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

    class ComponentMixin(QWidget):
        def __getattr__(self, name: str) -> Any:
            return getattr(super(), name)
else:

    class ComponentMixin:
        def __getattr__(self, name: str) -> Any:
            return getattr(super(), name)
