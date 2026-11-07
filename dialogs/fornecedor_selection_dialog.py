"""
Dialog de Seleção de Fornecedores - Padronizado com sistema de estilos
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from dialogs.fornecedor_dialog import FornecedorDialog
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.fornecedor import Fornecedor
from utils.helpers import aplicar_maiuscula_formulario


class FornecedorSelectionDialog(TableScrollNavigationMixin, QDialog):
    """Dialog para seleção de fornecedores com F1 para novo cadastro"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fornecedor_selecionado = None
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._carregar_fornecedores()

    def _init_ui(self):
        """Inicializa interface otimizada"""
        self.setWindowTitle("Selecionar Fornecedor")
        self.setMinimumSize(750, 500)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        self._criar_header(layout)

        # Busca
        self._criar_busca(layout)

        # Tabela
        self._criar_tabela(layout)

        # Botões
        self._criar_botoes(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria cabeçalho com ajuda F1"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Selecionar Fornecedor")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        ajuda_label = QLabel("F1 - Novo fornecedor")
        ajuda_label.setProperty("class", "muted")
        header_layout.addWidget(ajuda_label)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_busca(self, layout):
        """Cria campo de busca"""
        search_frame = QFrame()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("Nome, CNPJ, telefone ou email...")
        self.busca_edit.textChanged.connect(self._filtrar_fornecedores)
        search_layout.addWidget(self.busca_edit)

        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

    def _criar_tabela(self, layout):
        """Cria tabela de fornecedores"""
        self.tabela_fornecedores = QTableWidget()
        self.tabela_fornecedores.setColumnCount(4)
        self.tabela_fornecedores.setHorizontalHeaderLabels(
            ["ID", "Nome", "CNPJ", "Telefone"]
        )

        # Configurar colunas
        header = self.tabela_fornecedores.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        larguras = [50, None, 130, 110]
        for i, largura in enumerate(larguras):
            if largura:
                self.tabela_fornecedores.setColumnWidth(i, largura)

        # Configurações gerais
        self.tabela_fornecedores.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_fornecedores.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_fornecedores.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabela_fornecedores.setAlternatingRowColors(True)
        vertical_header = self.tabela_fornecedores.verticalHeader()
        assert vertical_header is not None
        vertical_header.setVisible(False)

        self.tabela_fornecedores.doubleClicked.connect(self._selecionar_e_fechar)

        self.setup_scroll_navigation(
            tabela=self.tabela_fornecedores,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

        layout.addWidget(self.tabela_fornecedores)

    def _criar_botoes(self, layout):
        """Cria botões do dialog"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._selecionar_fornecedor)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def keyPressEvent(self, event: QKeyEvent):
        """Captura F1 para novo fornecedor"""
        if event.key() == Qt.Key.Key_F1:
            self._cadastrar_novo_fornecedor()
        else:
            super().keyPressEvent(event)

    def _cadastrar_novo_fornecedor(self):
        """Abre dialog para novo fornecedor"""
        dialog = FornecedorDialog()
        if dialog.exec():
            try:
                fornecedor = dialog.get_data()
                fornecedor.salvar()
                QMessageBox.information(self, "Sucesso", "Fornecedor cadastrado!")
                self._carregar_fornecedores()
                self._selecionar_novo_fornecedor(fornecedor.id)
            except ValueError as e:
                QMessageBox.warning(self, "Erro", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar: {e!s}")

    def _selecionar_novo_fornecedor(self, fornecedor_id):
        """Seleciona fornecedor recém-cadastrado"""
        for row in range(self.tabela_fornecedores.rowCount()):
            item = self.tabela_fornecedores.item(row, 0)
            if item is not None and int(item.text()) == fornecedor_id:
                self.tabela_fornecedores.selectRow(row)
                self.tabela_fornecedores.setFocus()
                break

    def _carregar_fornecedores(self):
        """Carrega fornecedores ativos"""
        self.fornecedores = Fornecedor.buscar_todos(apenas_ativos=True)
        self._mostrar_fornecedores(self.fornecedores)

    def _mostrar_fornecedores(self, fornecedores):
        """Exibe fornecedores na tabela"""
        self.tabela_fornecedores.setRowCount(len(fornecedores))

        for row, fornecedor in enumerate(fornecedores):
            # ID
            item_id = QTableWidgetItem(str(fornecedor.id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_fornecedores.setItem(row, 0, item_id)

            # Nome
            self.tabela_fornecedores.setItem(
                row, 1, QTableWidgetItem(fornecedor.nome or "")
            )

            # CNPJ
            self.tabela_fornecedores.setItem(
                row, 2, QTableWidgetItem(fornecedor.cnpj or "")
            )

            # Telefone
            self.tabela_fornecedores.setItem(
                row, 3, QTableWidgetItem(fornecedor.telefone or "")
            )

    def _filtrar_fornecedores(self):
        """Filtra fornecedores por busca"""
        texto_busca = self.busca_edit.text().lower().strip()

        if not texto_busca:
            self._mostrar_fornecedores(self.fornecedores)
            return

        fornecedores_filtrados = [
            f
            for f in self.fornecedores
            if self._fornecedor_corresponde_busca(f, texto_busca)
        ]

        self._mostrar_fornecedores(fornecedores_filtrados)

    def _fornecedor_corresponde_busca(self, fornecedor, texto_busca):
        """Verifica se fornecedor corresponde à busca"""
        campos = [
            fornecedor.nome.lower() if fornecedor.nome else "",
            str(fornecedor.id),
            fornecedor.cnpj.lower() if fornecedor.cnpj else "",
            fornecedor.telefone.lower() if fornecedor.telefone else "",
            fornecedor.email.lower() if fornecedor.email else "",
        ]
        return any(texto_busca in campo for campo in campos)

    def _selecionar_fornecedor(self):
        """Seleciona fornecedor atual"""
        row = self.tabela_fornecedores.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Seleção", "Selecione um fornecedor")
            return

        item = self.tabela_fornecedores.item(row, 0)
        if item is None:
            QMessageBox.warning(
                self, "Seleção", "Não foi possível identificar o fornecedor."
            )
            return
        fornecedor_id = int(item.text())
        self.fornecedor_selecionado = next(
            (f for f in self.fornecedores if f.id == fornecedor_id), None
        )

        if self.fornecedor_selecionado:
            self.accept()

    def _selecionar_e_fechar(self, index):
        """Seleciona ao duplo clique"""
        row = index.row()
        item = self.tabela_fornecedores.item(row, 0)
        if item is None:
            return
        fornecedor_id = int(item.text())
        self.fornecedor_selecionado = next(
            (f for f in self.fornecedores if f.id == fornecedor_id), None
        )

        if self.fornecedor_selecionado:
            self.accept()

    def get_fornecedor_selecionado(self):
        """Retorna fornecedor selecionado"""
        return self.fornecedor_selecionado

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def cadastrar_novo_fornecedor(self):
        """Método público para compatibilidade"""
        self._cadastrar_novo_fornecedor()

    def selecionar_novo_fornecedor(self, fornecedor_id):
        """Método público para compatibilidade"""
        self._selecionar_novo_fornecedor(fornecedor_id)

    def carregar_fornecedores(self):
        """Método público para compatibilidade"""
        self._carregar_fornecedores()

    def mostrar_fornecedores(self, fornecedores):
        """Método público para compatibilidade"""
        self._mostrar_fornecedores(fornecedores)

    def filtrar_fornecedores(self):
        """Método público para compatibilidade"""
        self._filtrar_fornecedores()

    def selecionar_fornecedor(self):
        """Método público para compatibilidade"""
        self._selecionar_fornecedor()

    def selecionar_e_fechar(self, index):
        """Método público para compatibilidade"""
        self._selecionar_e_fechar(index)
