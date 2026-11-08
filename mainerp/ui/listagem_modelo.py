"""Elementos comuns das listagens de gestão."""

from PyQt6.QtCore import QSize, Qt, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from mainerp.ui.icones import icone
from mainerp.ui.styles import cores_ativas


class TotalRegistros(QLabel):
    def __init__(self, tabela: QTableWidget, parent: QWidget):
        super().__init__(parent)
        self.tabela = tabela
        self.setObjectName("total_registros")
        self.setProperty("class", "muted")
        modelo = tabela.model()
        if modelo is None:
            raise RuntimeError("Tabela sem modelo de dados.")
        modelo.rowsInserted.connect(self.atualizar)
        modelo.rowsRemoved.connect(self.atualizar)
        modelo.modelReset.connect(self.atualizar)
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("Aplicação Qt não inicializada.")
        app.aboutToQuit.connect(self.desconectar)
        self.atualizar()

    @pyqtSlot()
    def atualizar(self) -> None:
        self.setText(f"Registros exibidos: {self.tabela.rowCount()}")

    @pyqtSlot()
    def desconectar(self) -> None:
        modelo = self.tabela.model()
        if modelo is not None:
            modelo.rowsInserted.disconnect(self.atualizar)
            modelo.rowsRemoved.disconnect(self.atualizar)
            modelo.modelReset.disconnect(self.atualizar)


def _atualizar_icone_botao(widget: QPushButton, nome: str) -> None:
    cores = cores_ativas()
    cor = {
        "success": cores.button_semantic_text,
        "danger": cores.button_semantic_text,
        "primary": cores.button_semantic_text,
        "warning": cores.warning_text,
    }.get(widget.property("class"), cores.text_primary)
    widget.setIcon(icone(nome, cor))


def atualizar_icones_listagens() -> None:
    cores = cores_ativas()
    for widget in QApplication.allWidgets():
        if isinstance(widget, QLineEdit):
            pesquisa = widget.findChild(QAction, "icone_pesquisa_listagem")
            if pesquisa is not None:
                pesquisa.setIcon(icone("search", cores.text_primary))
        nome = widget.property("icone_listagem")
        if not isinstance(widget, QPushButton) or not isinstance(nome, str):
            continue
        _atualizar_icone_botao(widget, nome)


def configurar_modelo(
    view: QWidget,
    tabela: QTableWidget,
    busca: QLineEdit,
    acoes: list[tuple[QPushButton, str, str | None]],
) -> None:
    """Padroniza ícones, atalhos locais e contagem da tabela filtrada."""
    grupo_acoes = next(
        (grupo for grupo in view.findChildren(QGroupBox) if grupo.title() == "Ações"),
        None,
    )
    if grupo_acoes is None:
        raise RuntimeError("Listagem sem barra de ações.")
    layout_acoes = grupo_acoes.layout()
    if not isinstance(layout_acoes, QHBoxLayout):
        raise RuntimeError("Listagem sem barra de ações.")
    botao_busca = QPushButton("Pesquisar", grupo_acoes)
    botao_busca.setProperty("class", "secondary")
    botao_busca.clicked.connect(busca.setFocus)
    botao_busca.setToolTip("Pesquisar (Ctrl+F)")
    posicao = next(
        (
            i
            for i in range(layout_acoes.count())
            if (item := layout_acoes.itemAt(i)) is not None
            and item.spacerItem() is not None
        ),
        layout_acoes.count(),
    )
    layout_acoes.insertWidget(posicao, botao_busca)
    acoes = [*acoes, (botao_busca, "search", None)]
    for botao, nome, atalho in acoes:
        botao.setProperty("icone_listagem", nome)
        _atualizar_icone_botao(botao, nome)
        botao.setIconSize(QSize(16, 16))
        if atalho:
            shortcut = QShortcut(QKeySequence(atalho), view)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(botao.click)
            botao.setToolTip(f"{botao.text()} ({atalho})")

    shortcut_busca = QShortcut(QKeySequence("Ctrl+F"), view)
    shortcut_busca.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
    shortcut_busca.activated.connect(busca.setFocus)
    busca.setToolTip("Pesquisar (Ctrl+F)")
    acao_busca = busca.addAction(
        icone("search", cores_ativas().text_primary),
        QLineEdit.ActionPosition.LeadingPosition,
    )
    if acao_busca is None:
        raise RuntimeError("Não foi possível criar o ícone de pesquisa.")
    acao_busca.setObjectName("icone_pesquisa_listagem")

    rodape = TotalRegistros(tabela, view)
    layout = view.layout()
    if not isinstance(layout, QVBoxLayout):
        raise RuntimeError("Listagem sem layout vertical.")
    layout.addWidget(rodape)
