import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableWidget

from mainerp.ui.table_items import NumericTableWidgetItem
from mainerp.ui.views.cliente_view import ClienteView
from mainerp.ui.views.fornecedor_view import FornecedorView

CASES = [
    (
        ClienteView,
        "_carregar_clientes",
        "tabela_clientes",
        ["ID", "Nome", "CPF/CNPJ", "Endereço", "Telefone", "Email", "Observação"],
        [50, 200, 130, 250, 110, 200, 200],
    ),
    (
        FornecedorView,
        "_carregar_fornecedores",
        "tabela_fornecedores",
        ["ID", "Nome", "CNPJ", "Telefone", "Email", "Observação"],
        [50, None, 130, 110, 250, 350],
    ),
]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(params=CASES, ids=["clientes", "fornecedores"])
def listagem(request, monkeypatch, app):
    view_class, load_method, table_name, headers, widths = request.param
    monkeypatch.setattr(view_class, load_method, lambda self: None)
    view = view_class()
    view.show()
    app.processEvents()
    yield view, getattr(view, table_name), headers, widths
    view.close()
    view.deleteLater()
    app.processEvents()


def test_listagem_mantem_configuracao_de_colunas_e_aparencia(listagem):
    view, table, labels, widths = listagem
    assert table.columnCount() == len(labels)
    header = table.horizontalHeader()
    vertical = table.verticalHeader()
    assert header is not None
    assert vertical is not None
    for column, (label, width) in enumerate(zip(labels, widths, strict=True)):
        item = table.horizontalHeaderItem(column)
        assert item is not None
        assert item.text() == label
        if width is None:
            expected_mode = QHeaderView.ResizeMode.Stretch
        elif isinstance(view, ClienteView) and column == 1:
            expected_mode = QHeaderView.ResizeMode.Interactive
        else:
            expected_mode = QHeaderView.ResizeMode.Fixed
        assert header.sectionResizeMode(column) == expected_mode
        if width is not None:
            assert table.columnWidth(column) == width
    assert not vertical.isVisible()
    assert vertical.defaultSectionSize() == 22
    assert vertical.minimumSectionSize() == 22
    assert vertical.maximumSectionSize() == 22
    assert vertical.sectionResizeMode(0) == QHeaderView.ResizeMode.Fixed
    assert table.alternatingRowColors()
    assert table.styleSheet() == ""
    assert table.selectionBehavior() == QTableWidget.SelectionBehavior.SelectRows
    assert table.selectionMode() == QTableWidget.SelectionMode.SingleSelection
    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert table.isSortingEnabled()
    assert table.verticalScrollMode() == QTableWidget.ScrollMode.ScrollPerItem


def test_listagem_ordena_seleciona_e_navega_pelo_scroll(listagem, app):
    _, table, _, _ = listagem
    table.setSortingEnabled(False)
    table.setRowCount(3)
    for row, number in enumerate([10, 2, 1]):
        table.setItem(row, 0, NumericTableWidgetItem(str(number)))
    assert [table.rowHeight(i) for i in range(3)] == [22, 22, 22]
    table.setSortingEnabled(True)
    table.sortItems(0, Qt.SortOrder.AscendingOrder)
    values = []
    for row in range(3):
        item = table.item(row, 0)
        assert item is not None
        values.append(item.text())
    assert values == ["1", "2", "10"]

    changes = []
    table.currentCellChanged.connect(lambda *args: changes.append(args))
    table.setCurrentCell(0, 0)
    viewport = table.viewport()
    assert viewport is not None
    event = QWheelEvent(
        QPointF(5, 5),
        QPointF(5, 5),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(viewport, event)
    app.processEvents()
    assert table.currentRow() == 1
    assert changes[-1][:2] == (1, 0)
    assert len(table.selectionModel().selectedRows()) == 1
