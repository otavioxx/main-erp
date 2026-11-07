"""Utilitários para tabelas Qt."""

from PyQt6.QtWidgets import QHeaderView, QTableWidget


def configurar_listagem_padrao(tabela: QTableWidget) -> None:
    """Configura a apresentação comum das listagens de clientes e fornecedores."""
    fixar_altura_linhas(tabela, 22)
    tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabela.setAlternatingRowColors(True)
    tabela.setSortingEnabled(True)


def fixar_altura_linhas(tabela: QTableWidget, altura: int = 22) -> None:
    """Fixa a altura das linhas e a reaplica sempre que entram linhas novas.

    Substitui o bloco de ~30 linhas que estava copiado em várias telas.
    """
    vheader = tabela.verticalHeader()
    assert vheader is not None
    vheader.setDefaultSectionSize(altura)
    vheader.setMinimumSectionSize(altura)
    vheader.setMaximumSectionSize(altura)
    vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    vheader.setCascadingSectionResizes(False)
    vheader.setStretchLastSection(False)
    vheader.setVisible(False)

    def aplicar() -> None:
        try:
            for row in range(tabela.rowCount()):
                tabela.setRowHeight(row, altura)
        except RuntimeError:  # o widget Qt já foi destruído
            pass

    model = tabela.model()
    if model is not None:
        model.rowsInserted.connect(lambda *_: aplicar())
