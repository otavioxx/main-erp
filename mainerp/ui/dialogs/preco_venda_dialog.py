"""Diálogo de entrada do preço de venda de um produto."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QLabel,
    QVBoxLayout,
)

from mainerp.domain.utils.helpers import SelectAllDoubleSpinBox


def solicitar_preco_venda(valor_inicial: float, parent=None) -> float | None:
    """Solicita o preço de venda e retorna None quando o usuário cancela."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Preço de Venda")
    dialog.setMinimumWidth(420)

    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Digite o preço de venda:"))

    campo_preco = SelectAllDoubleSpinBox()
    campo_preco.setRange(0.01, 9999999.99)
    campo_preco.setDecimals(2)
    campo_preco.setValue(valor_inicial)
    campo_preco.setAlignment(Qt.AlignmentFlag.AlignRight)
    campo_preco.setGroupSeparatorShown(True)
    campo_preco.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
    campo_preco.setMinimumWidth(260)
    campo_preco.setMinimumHeight(35)
    layout.addWidget(campo_preco)

    botoes = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    botoes.accepted.connect(dialog.accept)
    botoes.rejected.connect(dialog.reject)
    layout.addWidget(botoes)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return campo_preco.value()
