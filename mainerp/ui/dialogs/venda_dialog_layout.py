"""Componentes de ProdutoVendaDialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,  # NOVO: Importado para layout em grid
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
from mainerp.ui.tabela import fixar_altura_linhas

__all__ = ["_VendaDialogLayout"]


class _VendaDialogLayout(ComponentMixin):
    def _init_ui(self):
        """Inicializa interface usando classes CSS semânticas"""
        self.setWindowTitle("Nova Venda")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        self._criar_header(layout)

        # ========== LAYOUT MODIFICADO: Cliente + Entrada Rápida lado a lado ==========
        # Criar um layout horizontal para os dois frames
        cliente_entrada_layout = QHBoxLayout()
        cliente_entrada_layout.setSpacing(12)

        # Frame do cliente (lado esquerdo) - OCUPA 40% DO ESPAÇO
        self._criar_secao_cliente(cliente_entrada_layout, 40)

        # Frame de entrada rápida (lado direito) - OCUPA 60% DO ESPAÇO
        self._criar_frame_entrada_rapida(cliente_entrada_layout, 60)

        # Adicionar o layout horizontal ao layout principal
        layout.addLayout(cliente_entrada_layout)
        # ========== FIM DA MODIFICAÇÃO ==========

        # Tabela de produtos (agora com mais espaço vertical)
        self._criar_secao_produtos(layout)

        # Resumo financeiro
        self._criar_resumo_financeiro(layout)

        # Botões de ação
        self._criar_botoes_acao(layout)

        self.setLayout(layout)
        self._configurar_atalhos()

    def _criar_header(self, layout):
        """Cria cabeçalho da dialog"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Nova Venda")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        # NOVO: Indicador de modificações não salvas
        self.label_modificacoes = QLabel("")
        self.label_modificacoes.setProperty("class", "warning")
        self.label_modificacoes.setVisible(False)
        header_layout.addWidget(self.label_modificacoes)

        layout.addWidget(header_frame)

    def _criar_secao_cliente(self, parent_layout, percentual=40):
        """Cria seção de seleção de cliente"""
        grupo_cliente = QGroupBox("Cliente")
        grupo_cliente.setProperty("class", "clean-group")

        # Configurar tamanho mínimo e altura fixa
        grupo_cliente.setMinimumWidth(250)
        grupo_cliente.setFixedHeight(120)  # <-- ALTURA FIXA AQUI

        cliente_layout = QVBoxLayout()
        cliente_layout.setContentsMargins(8, 12, 8, 12)

        # Header do cliente com atalho
        cliente_header = QHBoxLayout()
        cliente_header.addWidget(QLabel("Cliente selecionado:"))

        cliente_atalho = QLabel("F2 - Selecionar")
        cliente_atalho.setProperty("class", "muted")
        cliente_header.addWidget(cliente_atalho)
        cliente_header.addStretch()
        cliente_layout.addLayout(cliente_header)

        # Label do cliente selecionado
        self.label_cliente = QLabel("Não selecionado")
        self.label_cliente.setWordWrap(True)
        cliente_layout.addWidget(self.label_cliente)

        grupo_cliente.setLayout(cliente_layout)
        parent_layout.addWidget(grupo_cliente)

    def _criar_frame_entrada_rapida(self, parent_layout, percentual=60):
        """Cria frame para entrada rápida de produtos"""
        grupo_entrada = QGroupBox("Entrada Rápida de Produto")
        grupo_entrada.setProperty("class", "clean-group")

        # Configurar tamanho mínimo e altura fixa
        grupo_entrada.setMinimumWidth(350)
        grupo_entrada.setFixedHeight(120)  # <-- ALTURA FIXA AQUI (mesma do cliente)

        entrada_layout = QVBoxLayout()
        entrada_layout.setContentsMargins(8, 12, 8, 12)
        entrada_layout.setSpacing(8)

        # Campos de entrada em grid
        campos_grid = QGridLayout()
        campos_grid.setHorizontalSpacing(10)
        campos_grid.setVerticalSpacing(5)

        # Linha 0: Labels
        campos_grid.addWidget(QLabel("Código:"), 0, 0)
        campos_grid.addWidget(QLabel("Quantidade:"), 0, 1)
        campos_grid.addWidget(QLabel("Valor de Venda:"), 0, 2)

        # Linha 1: Campos de entrada
        self.entry_codigo = QLineEdit()
        self.entry_codigo.setPlaceholderText("ID do produto")
        campos_grid.addWidget(self.entry_codigo, 1, 0)

        self.entry_quantidade = QLineEdit()
        self.entry_quantidade.setPlaceholderText("1")
        self.entry_quantidade.setText("1")
        campos_grid.addWidget(self.entry_quantidade, 1, 1)

        self.entry_valor = QLineEdit()
        self.entry_valor.setPlaceholderText("R$ 0,00")
        campos_grid.addWidget(self.entry_valor, 1, 2)

        # Configurar expansão das colunas
        campos_grid.setColumnStretch(0, 1)
        campos_grid.setColumnStretch(1, 1)
        campos_grid.setColumnStretch(2, 2)

        entrada_layout.addLayout(campos_grid)

        # Label para mostrar produto encontrado
        self.label_produto_encontrado = QLabel("")
        self.label_produto_encontrado.setProperty("class", "muted")
        self.label_produto_encontrado.setWordWrap(True)
        entrada_layout.addWidget(self.label_produto_encontrado)

        # Conectar eventos
        self.entry_codigo.returnPressed.connect(self._processar_enter_codigo)
        self.entry_codigo.textChanged.connect(self._buscar_produto_por_codigo)
        self.entry_codigo.textChanged.connect(self._marcar_como_modificado)

        self.entry_quantidade.returnPressed.connect(self._processar_enter_quantidade)
        self.entry_quantidade.textChanged.connect(self._marcar_como_modificado)

        self.entry_valor.returnPressed.connect(self._processar_enter_valor)
        self.entry_valor.textChanged.connect(self._marcar_como_modificado)

        grupo_entrada.setLayout(entrada_layout)
        parent_layout.addWidget(grupo_entrada)

    def _criar_secao_produtos(self, layout):
        """Cria seção da tabela de produtos - AGORA COM MAIS ESPAÇO"""
        from PyQt6.QtWidgets import QSizePolicy  # IMPORT ADICIONADO AQUI

        grupo_produtos = QGroupBox("Produtos da Venda")
        grupo_produtos.setProperty("class", "clean-group")

        # Fazer este grupo ocupar mais espaço vertical
        grupo_produtos.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Horizontal
            QSizePolicy.Policy.Expanding,  # Vertical
        )

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

        # Configurar tabela
        self._criar_tabela_produtos()
        produtos_layout.addWidget(self.tabela_produtos)

        grupo_produtos.setLayout(produtos_layout)
        layout.addWidget(grupo_produtos, 1)  # Stretch=1 para ocupar espaço extra

    def _criar_tabela_produtos(self):
        """Configura tabela de produtos - VERSÃO COM ALTURA FIXA"""
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(8)
        self.tabela_produtos.setHorizontalHeaderLabels(
            ["ID", "Nome", "Cor", "Tamanho", "Referência", "Preço", "Qtd", "Subtotal"]
        )

        # Configurar colunas
        header = self.tabela_produtos.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Cor
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Tamanho
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Referência
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Preço
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Qtd
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Subtotal

        # Larguras das colunas
        self.tabela_produtos.setColumnWidth(0, 50)  # ID
        self.tabela_produtos.setColumnWidth(2, 120)  # Cor
        self.tabela_produtos.setColumnWidth(3, 70)  # Tamanho
        self.tabela_produtos.setColumnWidth(4, 100)  # Referência
        self.tabela_produtos.setColumnWidth(5, 80)  # Preço
        self.tabela_produtos.setColumnWidth(6, 60)  # Qtd
        self.tabela_produtos.setColumnWidth(7, 90)  # Subtotal

        # Configurar VERTICAL HEADER para altura fixa
        fixar_altura_linhas(self.tabela_produtos, 22)

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
            scroll_sensibilidade=1,
            auto_select_first=True,
        )

    def _criar_resumo_financeiro(self, layout):
        """Cria resumo financeiro"""
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

        # Desconto
        desconto_layout = QVBoxLayout()
        desconto_label = QLabel("Desconto Aplicado:")
        desconto_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        desconto_layout.addWidget(desconto_label)

        self.label_desconto_aplicado = QLabel("R$ 0,00")
        self.label_desconto_aplicado.setProperty("class", "valor-desconto")
        self.label_desconto_aplicado.setAlignment(Qt.AlignmentFlag.AlignRight)
        desconto_layout.addWidget(self.label_desconto_aplicado)
        resumo_layout.addLayout(desconto_layout)

        # Total
        total_layout = QVBoxLayout()
        total_label = QLabel("Total Final:")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(total_label)

        self.label_total_final = QLabel("R$ 0,00")
        self.label_total_final.setProperty("class", "valor-total")
        self.label_total_final.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_layout.addWidget(self.label_total_final)
        resumo_layout.addLayout(total_layout)

        resumo_layout.addStretch()

        grupo_resumo.setLayout(resumo_layout)
        layout.addWidget(grupo_resumo)

    def _criar_botoes_acao(self, layout):
        """Cria botões de ação com classes CSS semânticas"""
        buttons_layout = QHBoxLayout()

        # Botão finalizar
        self.btn_finalizar = QPushButton("F5 - Finalizar Venda")
        self.btn_finalizar.setProperty("class", "primary")
        self.btn_finalizar.setEnabled(False)
        self.btn_finalizar.clicked.connect(self._finalizar_venda)
        self.btn_finalizar.setAutoDefault(False)
        self.btn_finalizar.setDefault(False)
        buttons_layout.addWidget(self.btn_finalizar)

        # Botão desconto
        self.btn_desconto = QPushButton("F10 - Aplicar Desconto")
        self.btn_desconto.setProperty("class", "warning")
        self.btn_desconto.setAutoDefault(False)
        self.btn_desconto.clicked.connect(self._aplicar_desconto)
        buttons_layout.addWidget(self.btn_desconto)

        buttons_layout.addStretch()

        # Botão cancelar
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "secondary")
        btn_cancelar.setAutoDefault(False)
        btn_cancelar.clicked.connect(self._cancelar_venda)
        buttons_layout.addWidget(btn_cancelar)

        layout.addLayout(buttons_layout)
