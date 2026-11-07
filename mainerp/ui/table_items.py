from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidgetItem


class NumericTableWidgetItem(QTableWidgetItem):
    """Item de tabela que ordena numericamente ao invés de alfabeticamente."""

    def __init__(self, text: str = "") -> None:
        super().__init__(text)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            self_value = self.data(Qt.ItemDataRole.UserRole)
            other_value = other.data(Qt.ItemDataRole.UserRole)

            if self_value is not None and other_value is not None:
                return float(self_value) < float(other_value)

            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            return self.text() < other.text()
