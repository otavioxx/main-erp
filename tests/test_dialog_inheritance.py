import pytest
from PyQt6.QtWidgets import QDialog

from mainerp.ui.dialogs.condicional_dialog import CondicionalDialog
from mainerp.ui.dialogs.pedido_dialog import PedidoDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog


@pytest.mark.parametrize(
    "dialog_class", [ProdutoVendaDialog, CondicionalDialog, PedidoDialog]
)
def test_dialogs_expoem_exec_modal(dialog_class):
    assert issubclass(dialog_class, QDialog)
    assert callable(dialog_class.exec)
