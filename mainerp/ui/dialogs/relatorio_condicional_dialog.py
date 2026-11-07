from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog


class RelatorioCondicionalDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros do Relatório de Condicionais")
        self.setMinimumWidth(500)
        self.cliente_selecionado = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("Relatório de Condicionais")
        titulo.setProperty("class", "title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #3c3c3c;")
        layout.addWidget(separator)

        # Grupo de datas - Layout horizontal
        grupo_data = QGroupBox("Período")
        grupo_data.setProperty("class", "form-group")
        layout_data = QHBoxLayout()
        layout_data.setSpacing(10)

        # Data inicial
        data_inicio_layout = QVBoxLayout()
        data_inicio_layout.addWidget(QLabel("Data Inicial:"))
        self.data_inicio = QLineEdit()
        self.data_inicio.setPlaceholderText("DD/MM/AAAA")
        self.data_inicio.setMaximumWidth(100)
        # Definir data padrão (30 dias atrás)
        data_inicio_padrao = QDate.currentDate().addDays(-30)
        self.data_inicio.setText(data_inicio_padrao.toString("dd/MM/yyyy"))
        data_inicio_layout.addWidget(self.data_inicio)
        layout_data.addLayout(data_inicio_layout)

        # Data final
        data_fim_layout = QVBoxLayout()
        data_fim_layout.addWidget(QLabel("Data Final:"))
        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        # Definir data padrão (hoje)
        data_fim_padrao = QDate.currentDate()
        self.data_fim.setText(data_fim_padrao.toString("dd/MM/yyyy"))
        data_fim_layout.addWidget(self.data_fim)
        layout_data.addLayout(data_fim_layout)

        # Espaço flexível
        layout_data.addStretch()

        grupo_data.setLayout(layout_data)
        layout.addWidget(grupo_data)

        # Grupo de cliente
        grupo_cliente = QGroupBox("Cliente")
        grupo_cliente.setProperty("class", "form-group")
        layout_cliente = QVBoxLayout()

        cliente_h_layout = QHBoxLayout()
        self.btn_selecionar_cliente = QPushButton("Selecionar Cliente")
        self.btn_selecionar_cliente.setProperty("class", "secondary")
        self.btn_selecionar_cliente.clicked.connect(self._selecionar_cliente)
        self.btn_selecionar_cliente.setMaximumWidth(150)
        cliente_h_layout.addWidget(self.btn_selecionar_cliente)

        self.label_cliente = QLabel("Nenhum cliente selecionado")
        self.label_cliente.setProperty("class", "muted")
        self.label_cliente.setWordWrap(True)
        cliente_h_layout.addWidget(self.label_cliente, 1)

        layout_cliente.addLayout(cliente_h_layout)
        grupo_cliente.setLayout(layout_cliente)
        layout.addWidget(grupo_cliente)

        # Grupo de status (Ativas, Convertidas, Devolvidas)
        grupo_status = QGroupBox("Status da Condicional")
        grupo_status.setProperty("class", "form-group")
        layout_status = QHBoxLayout()

        self.status_group = QButtonGroup(self)

        self.rb_todos = QRadioButton("Todos")
        self.rb_ativas = QRadioButton("Ativas")
        self.rb_convertidas = QRadioButton("Convertidas")
        self.rb_devolvidas = QRadioButton("Devolvidas")

        self.status_group.addButton(self.rb_todos)
        self.status_group.addButton(self.rb_ativas)
        self.status_group.addButton(self.rb_convertidas)
        self.status_group.addButton(self.rb_devolvidas)

        self.rb_todos.setChecked(True)

        for rb in [
            self.rb_todos,
            self.rb_ativas,
            self.rb_convertidas,
            self.rb_devolvidas,
        ]:
            layout_status.addWidget(rb)

        layout_status.addStretch()
        grupo_status.setLayout(layout_status)
        layout.addWidget(grupo_status)

        # Botões
        botoes_layout = QHBoxLayout()
        botoes_layout.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setProperty("class", "secondary")
        self.btn_cancelar.clicked.connect(self.reject)
        botoes_layout.addWidget(self.btn_cancelar)

        self.btn_gerar = QPushButton("Gerar Relatório")
        self.btn_gerar.setProperty("class", "primary")
        self.btn_gerar.clicked.connect(self.accept)
        botoes_layout.addWidget(self.btn_gerar)

        layout.addLayout(botoes_layout)

        self.setLayout(layout)

    def showEvent(self, event):
        """Sobrescreve o showEvent para centralizar a janela na tela"""
        super().showEvent(event)
        self._centralizar_janela()

    def _centralizar_janela(self):
        """Centraliza a janela na tela (não na janela pai)"""
        # Obter a geometria da tela
        screen = QApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("Não foi possível localizar a tela principal.")
        screen_geometry = screen.availableGeometry()

        # Calcular a posição central
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        # Mover a janela para o centro da tela
        self.move(x, y)

    def _selecionar_cliente(self):
        dialog = ClienteSelectionDialog(self)
        if dialog.exec():
            self.cliente_selecionado = dialog.cliente_selecionado
            if self.cliente_selecionado:
                self.label_cliente.setText(self.cliente_selecionado.nome)
                self.label_cliente.setProperty("class", "")
            else:
                self.label_cliente.setText("Nenhum cliente selecionado")
                self.label_cliente.setProperty("class", "muted")
            style = self.label_cliente.style()
            if style is not None:
                style.unpolish(self.label_cliente)
                style.polish(self.label_cliente)

    def _obter_status_selecionado(self):
        """Retorna o status selecionado"""
        if self.rb_todos.isChecked():
            return "todos"
        elif self.rb_ativas.isChecked():
            return "ativas"
        elif self.rb_convertidas.isChecked():
            return "convertidas"
        elif self.rb_devolvidas.isChecked():
            return "devolvidas"
        return "todos"

    def get_filtros(self):
        return {
            "data_inicio": self.data_inicio.text().strip(),
            "data_fim": self.data_fim.text().strip(),
            "cliente_id": self.cliente_selecionado.id
            if self.cliente_selecionado
            else None,
            "cliente_nome": self.cliente_selecionado.nome
            if self.cliente_selecionado
            else None,
            "status": self._obter_status_selecionado(),
        }
