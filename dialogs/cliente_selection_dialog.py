# dialogs/cliente_selection_dialog.py - VERSÃO MELHORADA COM DIMENSIONAMENTO INTELIGENTE
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLineEdit,
                             QLabel, QDialogButtonBox, QFrame, QMessageBox)
from PyQt6.QtGui import QIcon, QKeyEvent
from PyQt6.QtCore import Qt
from models.cliente import Cliente
from views.cliente_view import ClienteDialog
from utils.helpers import aplicar_maiuscula_formulario
from mixins.table_scroll_mixin import TableScrollNavigationMixin

# ✅ IMPORTAR O MIXIN DE DIMENSIONAMENTO
from mixins.dialog_size_mixin import DialogSizeMixin


# ✅ ADICIONAR MIXIN COMO PRIMEIRA CLASSE BASE
class ClienteSelectionDialog(DialogSizeMixin, TableScrollNavigationMixin, QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cliente_selecionado = None
        self.init_ui()
        aplicar_maiuscula_formulario(self)
        self.carregar_clientes()
        
        # ✅ CONFIGURAR TAMANHO INTELIGENTE
        # Para diálogos com tabela, use "large"
        self.setup_dialog_size_large()

    def init_ui(self):
        self.setWindowTitle("Selecionar Cliente")
        self.setWindowIcon(QIcon("icon.ico"))

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Selecionar Cliente")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        ajuda_label = QLabel("Pressione F1 para cadastrar novo cliente")
        ajuda_label.setStyleSheet("color: #666666; font-style: italic;")
        header_layout.addWidget(ajuda_label)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        search_frame = QFrame()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("Digite nome, CPF/CNPJ, telefone ou email...")
        self.busca_edit.textChanged.connect(self.filtrar_clientes)
        search_layout.addWidget(self.busca_edit)

        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

        # Configurar tabela
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["ID", "Nome", "CPF/CNPJ", "Telefone"])

        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tabela.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        self.tabela.setColumnWidth(0, 50)
        self.tabela.setColumnWidth(2, 130)
        self.tabela.setColumnWidth(3, 110)
        
        # ========== CONFIGURAÇÃO DE ALTURA ==========
        # Configurar VERTICAL HEADER para altura fixa
        vheader = self.tabela.verticalHeader()
        altura_desejada = 22
        
        vheader.setDefaultSectionSize(altura_desejada)
        vheader.setMinimumSectionSize(altura_desejada)
        vheader.setMaximumSectionSize(altura_desejada)
        vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vheader.setCascadingSectionResizes(False)
        vheader.setStretchLastSection(False)
        vheader.setVisible(False)
        
        # Função para aplicar altura quando dados forem carregados
        def aplicar_altura_quando_necessario():
            try:
                if hasattr(self, 'tabela') and self.tabela:
                    for row in range(self.tabela.rowCount()):
                        self.tabela.setRowHeight(row, altura_desejada)
            except:
                pass
        
        # Conectar ao sinal de dados alterados (quando a tabela for populada)
        try:
            if hasattr(self.tabela, 'model'):
                model = self.tabela.model()
                model.rowsInserted.connect(
                    lambda parent, first, last: aplicar_altura_quando_necessario()
                )
        except:
            pass
        # ========== FIM DA CONFIGURAÇÃO ==========

        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)

        self.tabela.doubleClicked.connect(self.selecionar_cliente)

        layout.addWidget(self.tabela)

        # ✅ ATIVAR O SCROLL NAVIGATION MIXIN
        self.setup_scroll_navigation(
            tabela=self.tabela,
            scroll_sensibilidade=1,
            auto_select_first=True
        )

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                  QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(buttons)

        buttons_frame.setLayout(buttons_layout)
        layout.addWidget(buttons_frame)

        self.setLayout(layout)

    def keyPressEvent(self, event: QKeyEvent):
        """Captura o evento de tecla pressionada"""
        if event.key() == Qt.Key.Key_F1:
            self.cadastrar_novo_cliente()
        else:
            super().keyPressEvent(event)

    def cadastrar_novo_cliente(self):
        """Abre a dialog de cadastro de novo cliente"""
        dialog = ClienteDialog()
        if dialog.exec():
            try:
                cliente = dialog.get_data()
                cliente.salvar()
                QMessageBox.information(self, "Sucesso", "Cliente cadastrado com sucesso!")
                self.carregar_clientes()
                self.selecionar_novo_cliente(cliente.id)
            except ValueError as e:
                QMessageBox.warning(self, "Erro", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar cliente: {str(e)}")

    def selecionar_novo_cliente(self, cliente_id):
        """Seleciona o cliente recém-cadastrado na tabela"""
        for row in range(self.tabela.rowCount()):
            if int(self.tabela.item(row, 0).text()) == cliente_id:
                self.tabela.selectRow(row)
                self.tabela.setFocus()
                break

    def carregar_clientes(self):
        self.clientes = Cliente.buscar_todos(apenas_ativos=True)
        self.filtrar_clientes()

    def filtrar_clientes(self):
        texto_busca = self.busca_edit.text().lower().strip()

        if texto_busca:
            clientes_filtrados = [
                c for c in self.clientes
                if (texto_busca in (c.nome or "").lower()) or
                   (texto_busca in (c.cpf_cnpj or "").lower()) or
                   (texto_busca in (c.telefone or "").lower()) or
                   (texto_busca in (c.email or "").lower())
            ]
        else:
            clientes_filtrados = self.clientes

        self.tabela.setRowCount(len(clientes_filtrados))

        for row, cliente in enumerate(clientes_filtrados):
            id_item = QTableWidgetItem(str(cliente.id))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela.setItem(row, 0, id_item)

            nome_item = QTableWidgetItem(cliente.nome or "")
            self.tabela.setItem(row, 1, nome_item)

            cpf_item = QTableWidgetItem(cliente.cpf_cnpj or "")
            self.tabela.setItem(row, 2, cpf_item)

            telefone_item = QTableWidgetItem(cliente.telefone or "")
            self.tabela.setItem(row, 3, telefone_item)
        
        # Aplicar altura após carregar os dados
        self._aplicar_altura_apos_filtro()

    def _aplicar_altura_apos_filtro(self):
        """Aplica altura fixa após filtrar os clientes"""
        try:
            if hasattr(self, 'tabela') and self.tabela:
                for row in range(self.tabela.rowCount()):
                    self.tabela.setRowHeight(row, 21)
        except:
            pass

    def selecionar_cliente(self, index):
        row = index.row()
        if row >= 0 and row < self.tabela.rowCount():
            cliente_id = int(self.tabela.item(row, 0).text())
            self.cliente_selecionado = next((c for c in self.clientes if c.id == cliente_id), None)
            self.accept()

    def accept_selection(self):
        row = self.tabela.currentRow()
        if row != -1 and row < self.tabela.rowCount():
            cliente_id = int(self.tabela.item(row, 0).text())
            self.cliente_selecionado = next((c for c in self.clientes if c.id == cliente_id), None)
        self.accept()

    def get_cliente_selecionado(self):
        return self.cliente_selecionado