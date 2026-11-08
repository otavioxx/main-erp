# \erp\views\config_selection_dialog.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from mainerp.core.config import obter_config
from mainerp.data.models.empresa import Empresa
from mainerp.domain.utils.helpers import aplicar_maiuscula_formulario
from mainerp.ui.styles import cores_ativas


class ConfigSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.configuracao_selecionada = None
        self.init_ui()
        aplicar_maiuscula_formulario(self)
        self.carregar_configuracoes()

    def init_ui(self):
        self.setWindowTitle("Selecionar Configuração")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        self.setWindowIcon(QIcon("icon.ico"))

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Configurações do Sistema")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        filter_frame = QFrame()
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)

        filter_layout.addWidget(QLabel("Filtrar por:"))

        self.filtro_combo = QComboBox()
        self.filtro_combo.addItems(["Todas", "Empresa", "Sistema", "Backup"])
        self.filtro_combo.currentTextChanged.connect(self.filtrar_configuracoes)
        filter_layout.addWidget(self.filtro_combo)

        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("Digite para buscar...")
        self.busca_edit.textChanged.connect(self.filtrar_configuracoes)
        filter_layout.addWidget(self.busca_edit)

        filter_layout.addStretch()
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(3)
        self.tabela.setHorizontalHeaderLabels(["Chave", "Valor", "Categoria"])

        header = self.tabela.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.tabela.setColumnWidth(2, 100)

        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)

        self.tabela.doubleClicked.connect(self.selecionar_configuracao)

        vertical_header = self.tabela.verticalHeader()
        assert vertical_header is not None
        vertical_header.setVisible(False)

        layout.addWidget(self.tabela)

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(buttons)

        buttons_frame.setLayout(buttons_layout)
        layout.addWidget(buttons_frame)

        self.setLayout(layout)

    def carregar_configuracoes(self):
        self.configuracoes = [
            {
                "chave": "empresa.nome",
                "valor": "Nome da Empresa",
                "categoria": "Empresa",
            },
            {
                "chave": "empresa.cnpj",
                "valor": "CNPJ da Empresa",
                "categoria": "Empresa",
            },
            {
                "chave": "empresa.endereco",
                "valor": "Endereço Completo",
                "categoria": "Empresa",
            },
            {
                "chave": "empresa.telefone",
                "valor": "(00) 00000-0000",
                "categoria": "Empresa",
            },
            {
                "chave": "empresa.email",
                "valor": "contato@empresa.com",
                "categoria": "Empresa",
            },
            {"chave": "sistema.tema",
             "valor": "Claro" if obter_config().obter_tema() == "light" else "Escuro",
             "categoria": "Sistema"},
            {"chave": "sistema.idioma", "valor": "Português", "categoria": "Sistema"},
            {"chave": "sistema.moeda", "valor": "R$", "categoria": "Sistema"},
            {"chave": "backup.automatico", "valor": "Ativado", "categoria": "Backup"},
            {"chave": "backup.frequencia", "valor": "Diário", "categoria": "Backup"},
            {"chave": "backup.ultimo", "valor": "2024-01-01", "categoria": "Backup"},
        ]

        empresa = Empresa.buscar()
        if empresa:
            self.configuracoes[0]["valor"] = empresa.nome or "Não configurado"
            self.configuracoes[1]["valor"] = empresa.cnpj or "Não configurado"
            self.configuracoes[2]["valor"] = empresa.endereco or "Não configurado"
            self.configuracoes[3]["valor"] = empresa.telefone or "Não configurado"
            self.configuracoes[4]["valor"] = empresa.email or "Não configurado"

        self.filtrar_configuracoes()

    def filtrar_configuracoes(self):
        categoria_filtro = self.filtro_combo.currentText()
        texto_busca = self.busca_edit.text().lower().strip()

        if categoria_filtro == "Todas":
            configs_filtradas = self.configuracoes
        else:
            configs_filtradas = [
                c for c in self.configuracoes if c["categoria"] == categoria_filtro
            ]

        if texto_busca:
            configs_filtradas = [
                c
                for c in configs_filtradas
                if texto_busca in c["chave"].lower()
                or texto_busca in str(c["valor"]).lower()
                or texto_busca in c["categoria"].lower()
            ]

        self.tabela.setRowCount(len(configs_filtradas))

        for row, configuracao in enumerate(configs_filtradas):
            chave_item = QTableWidgetItem(configuracao["chave"])
            self.tabela.setItem(row, 0, chave_item)

            valor_item = QTableWidgetItem(str(configuracao["valor"]))
            if "Não configurado" in str(configuracao["valor"]):
                valor_item.setForeground(QColor(cores_ativas().danger_text))
            self.tabela.setItem(row, 1, valor_item)

            categoria_item = QTableWidgetItem(configuracao["categoria"])
            categoria_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela.setItem(row, 2, categoria_item)

    def selecionar_configuracao(self, index):
        row = index.row()
        if row >= 0 and row < self.tabela.rowCount():
            item = self.tabela.item(row, 0)
            if item is None:
                return
            chave = item.text()
            self.configuracao_selecionada = next(
                (c for c in self.configuracoes if c["chave"] == chave), None
            )
            self.accept()

    def accept_selection(self):
        row = self.tabela.currentRow()
        if row != -1 and row < self.tabela.rowCount():
            item = self.tabela.item(row, 0)
            if item is None:
                return
            chave = item.text()
            self.configuracao_selecionada = next(
                (c for c in self.configuracoes if c["chave"] == chave), None
            )
        self.accept()

    def get_configuracao_selecionada(self):
        return self.configuracao_selecionada
