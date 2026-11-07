import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem

from mainerp.ui.dialogs import produto_selection_dialog
from mainerp.ui.table_items import NumericTableWidgetItem
from mainerp.ui.views import (
    cliente_view,
    condicional_view_filters,
    fornecedor_view,
    pedido_view,
    produto_view,
    recebimento_view_filters,
    venda_view,
)

ITEM_CLASSES = [
    NumericTableWidgetItem,
    cliente_view.NumericTableWidgetItem,
    fornecedor_view.NumericTableWidgetItem,
    pedido_view.NumericTableWidgetItem,
    produto_view.NumericTableWidgetItem,
    venda_view.NumericTableWidgetItem,
    produto_selection_dialog.NumericTableWidgetItem,
    condicional_view_filters.NumericTableWidgetItem,
    recebimento_view_filters.NumericTableWidgetItem,
]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def table_texts(table):
    texts = []
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        assert item is not None
        texts.append(item.text())
    return texts


@pytest.mark.parametrize("item_class", ITEM_CLASSES)
def test_numeric_item_preserves_comparison_contract(item_class):
    def item(text, value=None):
        result = item_class(text)
        if value is not None:
            result.setData(Qt.ItemDataRole.UserRole, value)
        return result

    assert item("2") < item("10")
    assert item("-3.5") < item("0")
    assert item("R$ 9,00", 9) < item("R$ 10,00", 10)
    assert item("", 0) < item("R$ 1,00", 1)
    assert item("") < item("2")
    assert item("R$ 10,00") < item("R$ 9,00")
    assert item("2", 100) < item("10")
    assert item("a", "inválido") < item("b", 1)
    assert item("2") < QTableWidgetItem("10")


@pytest.mark.parametrize("item_class", ITEM_CLASSES)
@pytest.mark.usefixtures("app")
def test_qt_sorts_currency_and_numbers_in_both_directions(item_class):
    table = QTableWidget(3, 1)
    for row, (text, value) in enumerate(
        [("R$ 10,00", 10), ("R$ 1.000,00", 1000), ("R$ 2,00", 2)]
    ):
        item = item_class(text)
        item.setData(Qt.ItemDataRole.UserRole, value)
        table.setItem(row, 0, item)

    table.sortItems(0, Qt.SortOrder.AscendingOrder)
    assert table_texts(table) == [
        "R$ 2,00",
        "R$ 10,00",
        "R$ 1.000,00",
    ]
    table.sortItems(0, Qt.SortOrder.DescendingOrder)
    assert table_texts(table) == [
        "R$ 1.000,00",
        "R$ 10,00",
        "R$ 2,00",
    ]


@pytest.mark.usefixtures("app")
def test_qt_sorts_numeric_text_and_empty_values():
    table = QTableWidget(4, 1)
    for row, text in enumerate(["10", "", "2", "-1"]):
        table.setItem(row, 0, NumericTableWidgetItem(text))

    table.sortItems(0, Qt.SortOrder.AscendingOrder)
    assert table_texts(table) == ["", "-1", "2", "10"]
    table.sortItems(0, Qt.SortOrder.DescendingOrder)
    assert table_texts(table) == ["10", "2", "-1", ""]


def test_all_views_use_shared_numeric_item():
    assert all(item_class is NumericTableWidgetItem for item_class in ITEM_CLASSES)
