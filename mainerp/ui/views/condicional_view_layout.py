"""Componentes de CondicionalView."""

from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.tabela import configurar_listagem_padrao

__all__ = ["_CondicionalViewLayout"]


class _CondicionalViewLayout(ComponentMixin):
    def _init_ui(self):
        """Inicializa a interface com classes CSS semânticas"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header com título
        self._criar_header(layout)

        # Grupo de filtros
        self._criar_grupo_filtros(layout)

        # Grupo de ações
        self._criar_grupo_acoes(layout)

        # Grupo de condicionais (tabela)
        self._criar_grupo_condicionais(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestão de Condicionais")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label informativo sobre filtros
        self.label_info = QLabel("(Últimos 30 dias)")
        self.label_info.setProperty("class", "muted")
        header_layout.addWidget(self.label_info)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_grupo_filtros(self, layout):
        """Cria o grupo de filtros com layout similar ao VendaView"""
        grupo_filtros = QGroupBox("Filtros")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Busca por cliente (lado esquerdo)
        self.busca_cliente = QLineEdit()
        self.busca_cliente.setPlaceholderText("Buscar por Nome do cliente...")
        self.busca_cliente.setMaximumWidth(300)
        self.busca_cliente.textChanged.connect(self._filtrar_condicionais)
        filtro_layout.addWidget(self.busca_cliente)

        # ComboBox de status (após busca de cliente)
        filtro_layout.addWidget(QLabel("Status:"))

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "Ativas", "Convertidas", "Devolvidas"])
        self.combo_status.setCurrentText("Ativas")
        self.combo_status.setMaximumWidth(120)
        self.combo_status.currentTextChanged.connect(self._filtrar_condicionais)
        filtro_layout.addWidget(self.combo_status)

        filtro_layout.addStretch()

        # Filtros de data (centro)
        self._criar_filtros_data_centralizados(filtro_layout)

        filtro_layout.addStretch()

        # Botão limpar (direita)
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(btn_limpar)

        grupo_filtros.setLayout(filtro_layout)
        layout.addWidget(grupo_filtros)

    def _criar_filtros_data_centralizados(self, layout):
        """Cria os campos de filtro por data centralizados"""
        layout.addWidget(QLabel("Período de:"))

        self.data_inicio = QLineEdit()
        self.data_inicio.setPlaceholderText("DD/MM/AAAA")
        self.data_inicio.setMaximumWidth(100)
        self.data_inicio.setText(
            (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        )
        self.data_inicio.textChanged.connect(self._filtrar_condicionais)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.data_fim.textChanged.connect(self._filtrar_condicionais)
        layout.addWidget(self.data_fim)

    def _criar_grupo_acoes(self, layout):
        """Cria o grupo de ações com botões semânticos"""
        grupo_acoes = QGroupBox("Ações")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões principais (esquerda)
        self.btn_nova_condicional = QPushButton("Nova Condicional")
        self.btn_nova_condicional.setProperty("class", "success")
        self.btn_nova_condicional.clicked.connect(self._abrir_nova_condicional)

        self.btn_editar_condicional = QPushButton("Editar")
        self.btn_editar_condicional.setProperty("class", "secondary")
        self.btn_editar_condicional.clicked.connect(self._editar_condicional)

        self.btn_converter_venda = QPushButton("Converter em Venda")
        self.btn_converter_venda.setProperty("class", "primary")
        self.btn_converter_venda.clicked.connect(self._converter_em_venda)

        self.btn_marcar_devolvida = QPushButton("Marcar Devolvida")
        self.btn_marcar_devolvida.setProperty("class", "warning")
        self.btn_marcar_devolvida.clicked.connect(self._marcar_como_devolvida)

        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setProperty("class", "danger")
        self.btn_excluir.clicked.connect(self._excluir_condicional)

        btn_layout.addWidget(self.btn_nova_condicional)
        btn_layout.addWidget(self.btn_editar_condicional)
        btn_layout.addWidget(self.btn_converter_venda)
        btn_layout.addWidget(self.btn_marcar_devolvida)
        btn_layout.addWidget(self.btn_excluir)
        btn_layout.addStretch()

        # Botões de relatório (direita)
        self.btn_imprimir = QPushButton("Imprimir Condicional")
        self.btn_imprimir.setProperty("class", "warning")
        self.btn_imprimir.clicked.connect(self._imprimir_condicional)

        self.btn_exportar = QPushButton("Imprimir Relatório")
        self.btn_exportar.setProperty("class", "primary")
        self.btn_exportar.clicked.connect(self._exportar_condicionais)

        btn_layout.addWidget(self.btn_imprimir)
        btn_layout.addWidget(self.btn_exportar)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_condicionais(self, layout):
        """Cria a tabela de condicionais com configuração otimizada"""
        # Frame container
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        # Layout principal
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Título
        titulo_frame = QFrame()
        titulo_layout = QHBoxLayout()
        titulo_layout.setContentsMargins(8, 4, 8, 4)

        titulo = QLabel("Condicionais")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_condicionais = QTableWidget()
        self._configurar_tabela_condicionais()
        container_layout.addWidget(self.tabela_condicionais)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_condicionais(self):
        """Configura a tabela de condicionais - VERSÃO COM ALTURA FIXA"""
        self.tabela_condicionais.setColumnCount(7)  # Aumentei para 7 colunas
        self.tabela_condicionais.setHorizontalHeaderLabels(
            [
                "ID",
                "Cliente",
                "Data",
                "Prev. Devolução",
                "Itens",
                "Desconto",
                "Valor Total",
            ]
        )

        # Configuração das colunas
        header = self.tabela_condicionais.horizontalHeader()
        if header is None:
            raise RuntimeError(
                "Não foi possível obter o cabeçalho horizontal da tabela"
            )

        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cliente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Data
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Prev. Devolução
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Itens
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Desconto
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Total

        # Larguras otimizadas
        larguras_colunas = [50, 100, 200, 120, 60, 80, 100]
        for i, largura in enumerate(larguras_colunas):
            if largura > 0:  # Aplica apenas larguras positivas
                self.tabela_condicionais.setColumnWidth(i, largura)

        configurar_listagem_padrao(self.tabela_condicionais)

        self.setup_scroll_navigation(
            tabela=self.tabela_condicionais,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )
