"""Componentes de PedidoDialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.tabela import fixar_altura_linhas

__all__ = ["_PedidoDialogLayout"]


class _PedidoDialogLayout(ComponentMixin):
    def _init_ui(self):
        """Inicializa interface otimizada"""
        self.setWindowTitle("Pedido")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        self._criar_header(layout)

        # Fornecedor
        self._criar_secao_fornecedor(layout)

        # Produtos
        self._criar_secao_produtos(layout)

        # Resumo
        self._criar_resumo_financeiro(layout)

        # Botões
        self._criar_botoes(layout)

        self.setLayout(layout)
        self._configurar_atalhos()

    def _criar_header(self, layout):
        """Cria cabeçalho"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Pedido")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        # NOVO: Indicador de modificações não salvas
        self.label_modificacoes = QLabel("")
        self.label_modificacoes.setProperty("class", "warning")
        self.label_modificacoes.setVisible(False)
        header_layout.addWidget(self.label_modificacoes)

        layout.addWidget(header_frame)

    def _criar_secao_fornecedor(self, layout):
        """Cria seção do fornecedor"""
        grupo_fornecedor = QGroupBox("Fornecedor")
        grupo_fornecedor.setProperty("class", "clean-group")

        fornecedor_layout = QVBoxLayout()
        fornecedor_layout.setContentsMargins(8, 12, 8, 12)

        # Header com atalho
        fornecedor_header = QHBoxLayout()
        fornecedor_header.addWidget(QLabel("Fornecedor selecionado:"))

        fornecedor_atalho = QLabel("F2 - Selecionar")
        fornecedor_atalho.setProperty("class", "muted")
        fornecedor_header.addWidget(fornecedor_atalho)
        fornecedor_header.addStretch()
        fornecedor_layout.addLayout(fornecedor_header)

        self.label_fornecedor = QLabel("Não selecionado")
        fornecedor_layout.addWidget(self.label_fornecedor)

        grupo_fornecedor.setLayout(fornecedor_layout)
        layout.addWidget(grupo_fornecedor)

    def _criar_secao_produtos(self, layout):
        """Cria seção dos produtos"""
        grupo_produtos = QGroupBox("Produtos do Pedido")
        grupo_produtos.setProperty("class", "clean-group")

        produtos_layout = QVBoxLayout()
        produtos_layout.setContentsMargins(8, 12, 8, 12)

        # Header com atalhos
        produtos_header = QHBoxLayout()
        produtos_header.addWidget(QLabel("Itens:"))

        produto_atalho = QLabel("F3 - Adicionar | F4 - Observação | Delete - Remover")
        produto_atalho.setProperty("class", "muted")
        produtos_header.addWidget(produto_atalho)
        produtos_header.addStretch()
        produtos_layout.addLayout(produtos_header)

        # Tabela
        self._criar_tabela_produtos()
        produtos_layout.addWidget(self.tabela_produtos)

        grupo_produtos.setLayout(produtos_layout)
        layout.addWidget(grupo_produtos)

    def _criar_tabela_produtos(self):
        """Configura tabela de produtos - VERSÃO COM ALTURA FIXA"""
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(
            9
        )  # Aumentado para incluir Cor, Tamanho, Referência
        self.tabela_produtos.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome",
                "Cor",
                "Tamanho",
                "Referência",
                "Preço Custo",
                "Preço Venda",
                "Qtd",
                "Subtotal",
            ]
        )

        # Configurar colunas
        header = self.tabela_produtos.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Cor
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Tamanho
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Referência
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Preço Custo
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Preço Venda
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Qtd
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Subtotal

        # Definir larguras das colunas
        self.tabela_produtos.setColumnWidth(0, 50)  # ID
        self.tabela_produtos.setColumnWidth(2, 120)  # Cor
        self.tabela_produtos.setColumnWidth(3, 70)  # Tamanho
        self.tabela_produtos.setColumnWidth(4, 100)  # Referência
        self.tabela_produtos.setColumnWidth(5, 80)  # Preço Custo
        self.tabela_produtos.setColumnWidth(6, 80)  # Preço Venda
        self.tabela_produtos.setColumnWidth(7, 60)  # Qtd
        self.tabela_produtos.setColumnWidth(8, 90)  # Subtotal

        # ========== CONFIGURAÇÃO DE ALTURA ==========
        # Configurar VERTICAL HEADER para altura fixa
        fixar_altura_linhas(self.tabela_produtos, 22)
        # ========== FIM DA CONFIGURAÇÃO ==========

        # Configurações gerais
        self.tabela_produtos.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_produtos.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_produtos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_produtos.setAlternatingRowColors(True)
        self.tabela_produtos.setSortingEnabled(False)

        self.setup_scroll_navigation(
            tabela=self.tabela_produtos,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    def _criar_resumo_financeiro(self, layout):
        """Cria resumo financeiro ATUALIZADO com desconto"""
        grupo_resumo = QGroupBox("Resumo Financeiro")
        grupo_resumo.setProperty("class", "clean-group")

        resumo_layout = QHBoxLayout()
        resumo_layout.setContentsMargins(12, 12, 12, 12)
        resumo_layout.setSpacing(20)

        # Subtotal
        subtotal_layout = QVBoxLayout()
        subtotal_label = QLabel("Subtotal:")
        subtotal_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        subtotal_layout.addWidget(subtotal_label)

        self.label_subtotal = QLabel("R$ 0,00")
        self.label_subtotal.setAlignment(Qt.AlignmentFlag.AlignRight)
        subtotal_layout.addWidget(self.label_subtotal)
        resumo_layout.addLayout(subtotal_layout)

        # Desconto - NOVO
        desconto_layout = QVBoxLayout()
        desconto_label = QLabel("Desconto:")
        desconto_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        desconto_layout.addWidget(desconto_label)

        self.label_desconto = QLabel("R$ 0,00")
        self.label_desconto.setProperty("class", "valor-desconto")
        self.label_desconto.setAlignment(Qt.AlignmentFlag.AlignRight)
        desconto_layout.addWidget(self.label_desconto)
        resumo_layout.addLayout(desconto_layout)

        # Frete
        frete_layout = QVBoxLayout()
        frete_label = QLabel("Frete:")
        frete_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        frete_layout.addWidget(frete_label)

        self.label_frete = QLabel("R$ 0,00")
        self.label_frete.setProperty("class", "valor-frete")
        self.label_frete.setAlignment(Qt.AlignmentFlag.AlignRight)
        frete_layout.addWidget(self.label_frete)
        resumo_layout.addLayout(frete_layout)

        # Total
        total_layout = QVBoxLayout()
        total_label = QLabel("Total:")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(total_label)

        self.label_total = QLabel("R$ 0,00")
        self.label_total.setProperty("class", "valor-total")
        self.label_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(self.label_total)
        resumo_layout.addLayout(total_layout)

        resumo_layout.addStretch()

        grupo_resumo.setLayout(resumo_layout)
        layout.addWidget(grupo_resumo)

    def _criar_botoes(self, layout):
        """Cria botões de ação"""
        buttons_layout = QHBoxLayout()

        self.btn_finalizar = QPushButton("F5 - Salvar Pedido")
        self.btn_finalizar.setProperty("class", "success")
        self.btn_finalizar.setEnabled(False)
        self.btn_finalizar.clicked.connect(self._finalizar_pedido)
        # Evitar que Enter acione o botão
        self.btn_finalizar.setAutoDefault(False)
        self.btn_finalizar.setDefault(False)
        buttons_layout.addWidget(self.btn_finalizar)

        self.btn_frete_desconto = QPushButton("F10 - Frete e Desconto")
        self.btn_frete_desconto.setProperty("class", "warning")
        self.btn_frete_desconto.setAutoDefault(False)
        self.btn_frete_desconto.clicked.connect(self._definir_frete_desconto)
        buttons_layout.addWidget(self.btn_frete_desconto)

        buttons_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "danger")
        btn_cancelar.setAutoDefault(False)
        btn_cancelar.clicked.connect(
            self._cancelar_pedido
        )  # Alterado para método próprio
        buttons_layout.addWidget(btn_cancelar)

        layout.addLayout(buttons_layout)

    def _configurar_atalhos(self):
        """Configura atalhos de teclado"""
        self.shortcut_f2 = QShortcut("F2", self)
        self.shortcut_f2.activated.connect(self._selecionar_fornecedor)

        self.shortcut_f3 = QShortcut("F3", self)
        self.shortcut_f3.activated.connect(self._selecionar_produto)

        self.shortcut_f4 = QShortcut("F4", self)
        self.shortcut_f4.activated.connect(self._abrir_observacao)

        self.shortcut_f5 = QShortcut("F5", self)
        self.shortcut_f5.activated.connect(self._finalizar_pedido)

        self.shortcut_f10 = QShortcut("F10", self)
        self.shortcut_f10.activated.connect(self._definir_frete_desconto)

        self.shortcut_delete = QShortcut(
            QKeySequence(QKeySequence.StandardKey.Delete), self
        )
        self.shortcut_delete.activated.connect(self._remover_produto)
