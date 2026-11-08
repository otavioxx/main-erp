import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableWidget

from mainerp.ui.table_items import NumericTableWidgetItem
from mainerp.ui.views import (
    condicional_view,
    pedido_view,
    produto_view,
    recebimento_view,
    venda_view,
)

CASES = [
    (
        pedido_view,
        "PedidoView",
        "_carregar_dados",
        "tabela_pedidos",
        [
            "ID",
            "Fornecedor",
            "Data Pedido",
            "Status",
            "Recebimento",
            "Desconto",
            "Frete",
            "Total",
        ],
        [50, None, 100, 90, 100, 80, 70, 80],
        True,
        False,
    ),
    (
        condicional_view,
        "CondicionalView",
        "_carregar_condicionais",
        "tabela_condicionais",
        [
            "ID",
            "Cliente",
            "Data",
            "Prev. Devolução",
            "Itens",
            "Desconto",
            "Valor Total",
        ],
        [50, None, 200, 120, 60, 80, 100],
        True,
        False,
    ),
    (
        venda_view,
        "VendaView",
        "_carregar_vendas",
        "tabela_vendas",
        ["ID", "Cliente", "Data", "Pagamento", "Desconto", "Total"],
        [50, None, 100, 120, 80, 100],
        False,
        True,
    ),
    (
        produto_view,
        "ProdutoView",
        "_carregar_produtos",
        "tabela_produtos",
        [
            "ID",
            "Nome",
            "Cor",
            "Tamanho",
            "Referência",
            "Preço Custo",
            "Preço Venda",
            "Estoque",
            "Lucro %",
            "Markup %",
            "Fornecedor",
        ],
        [50, None, 120, 70, 100, 100, 100, 80, 80, 80, 180],
        True,
        True,
    ),
    (
        recebimento_view,
        "RecebimentoView",
        "_carregar_duplicatas",
        "tabela_duplicatas",
        [
            "ID",
            "Cliente",
            "Status",
            "Venda",
            "Parcela",
            "Valor",
            "Vencimento",
            "Pagamento",
        ],
        [50, None, 120, 60, 60, 80, 100, 100],
        True,
        False,
    ),
]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(
    params=CASES, ids=["pedidos", "condicionais", "vendas", "produtos", "recebimentos"]
)
def listagem(request, monkeypatch, app):
    module, name, load_method, table_name, labels, widths, sorting, has_css = (
        request.param
    )
    view_class = getattr(module, name)
    monkeypatch.setattr(view_class, load_method, lambda self: None)
    if hasattr(module, "criar_pasta_se_nao_existir"):
        monkeypatch.setattr(module, "criar_pasta_se_nao_existir", lambda path: None)
    view = view_class()
    view.show()
    app.processEvents()
    yield view, getattr(view, table_name), labels, widths, sorting, has_css
    view.close()
    view.deleteLater()
    app.processEvents()


def test_configuracao_individual(listagem):
    _, table, labels, widths, sorting, has_css = listagem
    assert table.columnCount() == len(labels)
    header = table.horizontalHeader()
    vertical = table.verticalHeader()
    assert header is not None and vertical is not None
    for column, (label, width) in enumerate(zip(labels, widths, strict=True)):
        item = table.horizontalHeaderItem(column)
        assert item is not None
        assert item.text() == label
        assert header.sectionResizeMode(column) == (
            QHeaderView.ResizeMode.Stretch
            if width is None
            else QHeaderView.ResizeMode.Fixed
        )
        if width is not None:
            assert table.columnWidth(column) == width
    assert not vertical.isVisible()
    assert vertical.defaultSectionSize() == 22
    assert vertical.minimumSectionSize() == 22
    assert vertical.maximumSectionSize() == 22
    assert vertical.sectionResizeMode(0) == QHeaderView.ResizeMode.Fixed
    assert table.selectionBehavior() == QTableWidget.SelectionBehavior.SelectRows
    assert table.selectionMode() == QTableWidget.SelectionMode.SingleSelection
    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert table.alternatingRowColors()
    assert table.isSortingEnabled() is sorting
    assert not table.styleSheet()
    assert bool(table.property("linhaCompacta")) is has_css
    assert table.verticalScrollMode() == QTableWidget.ScrollMode.ScrollPerItem


def test_ordenacao_selecao_altura_e_navegacao(listagem, app):
    _, table, _, _, _, _ = listagem
    table.setSortingEnabled(False)
    table.setRowCount(3)
    for row, number in enumerate([10, 2, 1]):
        table.setItem(row, 0, NumericTableWidgetItem(str(number)))
    assert [table.rowHeight(row) for row in range(3)] == [22, 22, 22]
    table.setSortingEnabled(True)
    table.sortItems(0, Qt.SortOrder.AscendingOrder)
    items = [table.item(row, 0) for row in range(3)]
    assert all(item is not None for item in items)
    assert [item.text() for item in items if item is not None] == ["1", "2", "10"]
    table.setCurrentCell(0, 0)
    changes = []
    table.currentCellChanged.connect(lambda *args: changes.append(args))
    viewport = table.viewport()
    assert viewport is not None
    event = QWheelEvent(
        QPointF(5, 5),
        QPointF(5, 5),
        QPoint(),
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
    selection = table.selectionModel()
    assert selection is not None
    assert len(selection.selectedRows()) == 1


@pytest.mark.parametrize("listagem", [CASES[3]], indirect=True, ids=["produtos"])
def test_produtos_preserva_sinal_de_ordenacao_e_menu(listagem):
    view, table, _, _, _, _ = listagem
    assert isinstance(view, produto_view.ProdutoView)
    assert table.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu
    header = table.horizontalHeader()
    assert header is not None
    header.setSortIndicator(2, Qt.SortOrder.AscendingOrder)
    header.sectionClicked.emit(2)
    assert view.ultima_ordenacao_coluna == 2
    assert view.ultima_ordenacao_ordem == Qt.SortOrder.AscendingOrder
    table.sortItems(0, Qt.SortOrder.DescendingOrder)
    view._restaurar_estado_tabela()
    assert header.sortIndicatorSection() == 2
    assert header.sortIndicatorOrder() == Qt.SortOrder.AscendingOrder
