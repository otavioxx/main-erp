from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from mainerp.ui.styles import cores_ativas


class RelatorioProdutoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filtros do Relatório de Produtos")
        self.setMinimumWidth(550)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("Relatório de Produtos")
        titulo.setProperty("class", "title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"color: {cores_ativas().border};")
        layout.addWidget(separator)

        # Grupo de filtro por estoque
        grupo_estoque = QGroupBox("Filtro por Estoque")
        grupo_estoque.setProperty("class", "form-group")
        layout_estoque = QHBoxLayout()

        self.estoque_group = QButtonGroup(self)

        self.rb_com_estoque = QRadioButton("Com Estoque")
        self.rb_sem_estoque = QRadioButton("Sem Estoque")
        self.rb_ambos_estoque = QRadioButton("Ambos")

        self.estoque_group.addButton(self.rb_com_estoque)
        self.estoque_group.addButton(self.rb_sem_estoque)
        self.estoque_group.addButton(self.rb_ambos_estoque)

        self.rb_ambos_estoque.setChecked(True)

        for rb in [self.rb_com_estoque, self.rb_sem_estoque, self.rb_ambos_estoque]:
            layout_estoque.addWidget(rb)

        layout_estoque.addStretch()
        grupo_estoque.setLayout(layout_estoque)
        layout.addWidget(grupo_estoque)

        # Grupo de filtro por status
        grupo_status = QGroupBox("Filtro por Status")
        grupo_status.setProperty("class", "form-group")
        layout_status = QHBoxLayout()

        self.status_group = QButtonGroup(self)

        self.rb_ativos = QRadioButton("Ativos")
        self.rb_inativos = QRadioButton("Inativos")
        self.rb_ambos_status = QRadioButton("Ambos")

        self.status_group.addButton(self.rb_ativos)
        self.status_group.addButton(self.rb_inativos)
        self.status_group.addButton(self.rb_ambos_status)

        self.rb_ativos.setChecked(True)

        for rb in [self.rb_ativos, self.rb_inativos, self.rb_ambos_status]:
            layout_status.addWidget(rb)

        layout_status.addStretch()
        grupo_status.setLayout(layout_status)
        layout.addWidget(grupo_status)

        # Grupo de ordenação
        grupo_ordenacao = QGroupBox("Ordenação")
        grupo_ordenacao.setProperty("class", "form-group")
        layout_ordenacao = QVBoxLayout()

        # Primeira linha: ordenar por
        ordenar_layout = QHBoxLayout()
        ordenar_layout.addWidget(QLabel("Ordenar por:"))

        self.combo_ordenar = QComboBox()
        self.combo_ordenar.addItems(
            ["ID", "Nome", "Estoque", "Preço de Venda", "Preço de Custo"]
        )
        self.combo_ordenar.setCurrentText("ID")
        self.combo_ordenar.setMaximumWidth(150)
        ordenar_layout.addWidget(self.combo_ordenar)

        ordenar_layout.addStretch()
        layout_ordenacao.addLayout(ordenar_layout)

        # Segunda linha: direção da ordenação
        direcao_layout = QHBoxLayout()

        self.direcao_group = QButtonGroup(self)

        self.rb_crescente = QRadioButton("Crescente")
        self.rb_decrescente = QRadioButton("Decrescente")

        self.direcao_group.addButton(self.rb_crescente)
        self.direcao_group.addButton(self.rb_decrescente)

        self.rb_decrescente.setChecked(
            True
        )  # Padrão decrescente (ID mais recente primeiro)

        direcao_layout.addWidget(self.rb_crescente)
        direcao_layout.addWidget(self.rb_decrescente)
        direcao_layout.addStretch()

        layout_ordenacao.addLayout(direcao_layout)
        grupo_ordenacao.setLayout(layout_ordenacao)
        layout.addWidget(grupo_ordenacao)

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

    def _obter_filtro_estoque(self):
        """Retorna o filtro de estoque selecionado"""
        if self.rb_com_estoque.isChecked():
            return "com_estoque"
        elif self.rb_sem_estoque.isChecked():
            return "sem_estoque"
        else:
            return "ambos"

    def _obter_filtro_status(self):
        """Retorna o filtro de status selecionado"""
        if self.rb_ativos.isChecked():
            return "ativos"
        elif self.rb_inativos.isChecked():
            return "inativos"
        else:
            return "ambos"

    def _obter_ordenacao(self):
        """Retorna a ordenação selecionada"""
        campo_map = {
            "ID": "id",
            "Nome": "nome",
            "Estoque": "estoque",
            "Preço de Venda": "preco_venda",
            "Preço de Custo": "preco_custo",
        }

        campo = campo_map.get(self.combo_ordenar.currentText(), "id")
        direcao = "desc" if self.rb_decrescente.isChecked() else "asc"

        return campo, direcao

    def get_filtros(self):
        """Retorna todos os filtros selecionados"""
        campo_ordenacao, direcao_ordenacao = self._obter_ordenacao()

        return {
            "filtro_estoque": self._obter_filtro_estoque(),
            "filtro_status": self._obter_filtro_status(),
            "ordenar_por": campo_ordenacao,
            "direcao": direcao_ordenacao,
        }
