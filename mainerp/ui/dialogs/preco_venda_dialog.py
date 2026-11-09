"""Diálogo para entrada do preço de venda de um produto."""

from PyQt6.QtCore import QLocale, QTimer
from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QInputDialog, QLineEdit

from mainerp.ui.theme_tokens import DIMENSOES


def solicitar_preco_venda(
    valor_inicial: float,
    parent=None,
    ajustar_recuo_campo: bool = False,
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

    spinbox = dialog.findChild(QDoubleSpinBox)
    if ajustar_recuo_campo:
        if spinbox is None:
            raise RuntimeError("Diálogo de preço sem campo numérico.")
        editor = spinbox.findChild(QLineEdit)
        if editor is None:
            raise RuntimeError("Campo numérico de preço sem editor de texto.")
        editor.setTextMargins(
            DIMENSOES.espacamento, 0, DIMENSOES.espacamento, 0
        )

    # Selecionar automaticamente todo o valor ao abrir
    if spinbox is not None:
        QTimer.singleShot(100, spinbox.selectAll)

    # Executar diálogo
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    return dialog.doubleValue()
