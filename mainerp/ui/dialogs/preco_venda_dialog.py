"""Diálogo para entrada do preço de venda de um produto."""

from PyQt6.QtCore import QLocale, QTimer
from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QInputDialog


def solicitar_preco_venda(
    valor_inicial: float,
    parent=None,
) -> float | None:

    dialog = QInputDialog(parent)

    dialog.setWindowTitle("Preço de Venda")
    dialog.setLabelText("Digite o preço de venda:")

    # Configurar entrada numérica decimal
    dialog.setInputMode(QInputDialog.InputMode.DoubleInput)

    # Configuração regional brasileira
    dialog.setLocale(
        QLocale(
            QLocale.Language.Portuguese,
            QLocale.Country.Brazil,
        )
    )

    # Configurar valores
    dialog.setDoubleMinimum(0.01)
    dialog.setDoubleMaximum(9999999.99)
    dialog.setDoubleDecimals(2)
    dialog.setDoubleStep(0.01)
    dialog.setDoubleValue(float(valor_inicial))

    dialog.setMinimumWidth(420)

    # Selecionar automaticamente todo o valor ao abrir
    spinbox = dialog.findChild(QDoubleSpinBox)

    if spinbox is not None:
        QTimer.singleShot(100, spinbox.selectAll)

    # Executar diálogo
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    return dialog.doubleValue()
