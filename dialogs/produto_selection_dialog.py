"""
Dialog de Seleção de Produtos - Otimizado com correções de ordenação e filtro
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

from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.produto import Produto
from utils.helpers import aplicar_maiuscula_formulario
from utils.produto_utils import ProdutoUtils
from utils.tabela import fixar_altura_linhas
from views.produto_dialog import ProdutoDialog


# ========== CORREÇÃO: Classe para ordenação numérica ==========
class NumericTableWidgetItem(QTableWidgetItem):
    """Item de tabela que ordena numericamente ao invés de alfabeticamente"""

    def __init__(self, text=""):
        super().__init__(text)

    def __lt__(self, other):
        """Sobrescreve a comparação para ordenação numérica"""
        try:
            # Tenta extrair valor numérico do UserRole primeiro
            self_value = self.data(Qt.ItemDataRole.UserRole)
            other_value = other.data(Qt.ItemDataRole.UserRole)

            if self_value is not None and other_value is not None:
                return float(self_value) < float(other_value)

            # Se não tem UserRole, tenta converter o texto
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            # Se não conseguir converter para número, usa ordenação de string
            return self.text() < other.text()


class ProdutoSelectionDialog(TableScrollNavigationMixin, QDialog):
    """Dialog para seleção de produtos com F1 para novo cadastro"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.produto_selecionado = None
        self.produtos_atualmente_exibidos = []  # NOVO: guarda produtos exibidos atualmente
        self._init_ui()

        aplicar_maiuscula_formulario(self)
        self._carregar_produtos()

    def _init_ui(self):
        """Inicializa interface otimizada"""
        self.setWindowTitle("Selecionar Produto")
        self.setMinimumSize(1000, 750)

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

        titulo = QLabel("Selecionar Produto")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        ajuda_label = QLabel("F1 - Novo produto")
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
        self.busca_edit.setPlaceholderText(
            "Digite para buscar produtos (nome, cor, tamanho, referência, fornecedor)..."
        )
        self.busca_edit.textChanged.connect(self._filtrar_produtos)
        search_layout.addWidget(self.busca_edit)

        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

    def _criar_tabela(self, layout):
        """Cria tabela de produtos - VERSÃO COM ALTURA FIXA"""
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(8)  # Aumentado de 5 para 8
        self.tabela_produtos.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome",
                "Cor",
                "Tamanho",
                "Referência",
                "Preço Venda",
                "Estoque",
                "Fornecedor",
            ]
        )

        # Configurar colunas
        header = self.tabela_produtos.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome

        # Outras colunas com largura fixa
        for i in range(2, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        larguras = [
            50,
            None,
            120,
            70,
            100,
            100,
            80,
            180,
        ]  # None para Nome que é Stretch
        for i, largura in enumerate(larguras):
            if largura:
                self.tabela_produtos.setColumnWidth(i, largura)

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
        self.tabela_produtos.setSortingEnabled(True)

        self.tabela_produtos.doubleClicked.connect(self._selecionar_e_fechar)

        self.setup_scroll_navigation(
            tabela=self.tabela_produtos,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

        layout.addWidget(self.tabela_produtos)

    def _criar_botoes(self, layout):
        """Cria botões do dialog"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._selecionar_produto)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def keyPressEvent(self, event: QKeyEvent):
        """Captura F1 para novo produto"""
        if event.key() == Qt.Key.Key_F1:
            self._cadastrar_novo_produto()
        else:
            super().keyPressEvent(event)

    def _cadastrar_novo_produto(self):
        """Abre dialog para novo produto"""
        dialog = ProdutoDialog()
        if dialog.exec():
            try:
                produto = dialog.get_data()
                produto.salvar()
                QMessageBox.information(self, "Sucesso", "Produto cadastrado!")
                self._carregar_produtos()
                self._selecionar_novo_produto(produto.id)
            except ValueError as e:
                QMessageBox.warning(self, "Erro", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar: {e!s}")

    def _selecionar_novo_produto(self, produto_id):
        """Seleciona produto recém-cadastrado"""
        for row in range(self.tabela_produtos.rowCount()):
            if int(self.tabela_produtos.item(row, 0).text()) == produto_id:
                self.tabela_produtos.selectRow(row)
                self.tabela_produtos.setFocus()
                break

    def _carregar_produtos(self):
        """Carrega produtos ativos"""
        self.produtos = Produto.buscar_todos(apenas_ativos=True)
        self._mostrar_produtos(self.produtos)

    def _mostrar_produtos(self, produtos):
        """CORREÇÃO: Exibe produtos na tabela com ordenação numérica correta"""

        # CORREÇÃO: Guarda os produtos atualmente exibidos
        self.produtos_atualmente_exibidos = produtos

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_produtos.setSortingEnabled(False)

        self.tabela_produtos.setRowCount(len(produtos))

        for row, produto in enumerate(produtos):
            dados, _, _ = ProdutoUtils.formatar_item_produto(
                produto, incluir_fornecedor=True
            )

            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(dados["id"])
            item_id.setData(
                Qt.ItemDataRole.UserRole, produto.id
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 0, item_id)

            # Nome
            item_nome = QTableWidgetItem(dados["nome"])
            self.tabela_produtos.setItem(row, 1, item_nome)

            # Cor
            item_cor = QTableWidgetItem(produto.cor or "")
            item_cor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 2, item_cor)

            # Tamanho
            item_tamanho = QTableWidgetItem(produto.tamanho or "")
            item_tamanho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 3, item_tamanho)

            # Referência
            item_ref = QTableWidgetItem(produto.referencia or "")
            item_ref.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 4, item_ref)

            # CORREÇÃO: Preço Venda usando NumericTableWidgetItem para ordenação por valor
            item_preco = NumericTableWidgetItem(dados["preco_venda"])
            item_preco.setData(
                Qt.ItemDataRole.UserRole, produto.preco_venda
            )  # Valor numérico
            item_preco.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 5, item_preco)

            # CORREÇÃO: Estoque usando NumericTableWidgetItem para ordenação numérica
            item_estoque = NumericTableWidgetItem(dados["estoque"])
            item_estoque.setData(
                Qt.ItemDataRole.UserRole, produto.estoque
            )  # Valor numérico
            item_estoque.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 6, item_estoque)

            # Fornecedor
            item_fornecedor = QTableWidgetItem(dados["fornecedor"])
            self.tabela_produtos.setItem(row, 7, item_fornecedor)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_produtos.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_produtos.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _filtrar_produtos(self):
        """CORREÇÃO: Filtra produtos por busca - sempre usa dados originais"""
        texto_busca = self.busca_edit.text().lower().strip()

        if not texto_busca:
            # CORREÇÃO: Sempre usar self.produtos originais
            self._mostrar_produtos(self.produtos)
            return

        # CORREÇÃO: Filtrar sempre a partir dos dados originais
        produtos_filtrados = [
            p
            for p in self.produtos  # CORREÇÃO: sempre usar self.produtos original
            if self._produto_corresponde_busca(p, texto_busca)
        ]

        self._mostrar_produtos(produtos_filtrados)

    def _produto_corresponde_busca(self, produto, texto_busca):
        """Verifica se produto corresponde à busca"""
        campos = [
            produto.nome.lower(),
            str(produto.id),
            produto.fornecedor_nome.lower() if produto.fornecedor_nome else "",
            produto.cor.lower() if produto.cor else "",
            produto.tamanho.lower() if produto.tamanho else "",
            produto.referencia.lower() if produto.referencia else "",
        ]
        return any(texto_busca in campo for campo in campos)

    def _selecionar_produto(self):
        """CORREÇÃO: Seleciona produto atual usando produtos_atualmente_exibidos"""
        row = self.tabela_produtos.currentRow()
        if row == -1:
            QMessageBox.warning(self, "Seleção", "Selecione um produto")
            return

        # CORREÇÃO: Verifica se a linha existe na tabela
        if row >= self.tabela_produtos.rowCount():
            QMessageBox.warning(self, "Erro", "Linha selecionada não é mais válida")
            return

        # CORREÇÃO: Agora pega o ID da célula na linha atual
        item_id = self.tabela_produtos.item(row, 0)
        if not item_id:
            QMessageBox.warning(self, "Erro", "Não foi possível obter o ID do produto")
            return

        try:
            produto_id = int(item_id.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "ID do produto inválido")
            return

        # CORREÇÃO: Procura nos produtos atualmente exibidos, não na lista original
        # Isso garante que o produto correto seja encontrado mesmo após filtro/ordenação
        self.produto_selecionado = next(
            (p for p in self.produtos_atualmente_exibidos if p.id == produto_id), None
        )

        if not self.produto_selecionado:
            # Fallback: tenta encontrar na lista original
            self.produto_selecionado = next(
                (p for p in self.produtos if p.id == produto_id), None
            )

        if self.produto_selecionado:
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", f"Produto ID {produto_id} não encontrado")

    def _selecionar_e_fechar(self, index):
        """CORREÇÃO: Seleciona ao duplo clique usando produtos_atualmente_exibidos"""
        row = index.row()

        # CORREÇÃO: Verifica se a linha é válida
        if row >= self.tabela_produtos.rowCount():
            return

        item_id = self.tabela_produtos.item(row, 0)
        if not item_id:
            return

        try:
            produto_id = int(item_id.text())
        except ValueError:
            return

        # CORREÇÃO: Procura nos produtos atualmente exibidos
        self.produto_selecionado = next(
            (p for p in self.produtos_atualmente_exibidos if p.id == produto_id), None
        )

        if not self.produto_selecionado:
            # Fallback
            self.produto_selecionado = next(
                (p for p in self.produtos if p.id == produto_id), None
            )

        if self.produto_selecionado:
            self.accept()

    def get_produto_selecionado(self):
        """Retorna produto selecionado"""
        return self.produto_selecionado

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def cadastrar_novo_produto(self):
        """Método público para compatibilidade"""
        self._cadastrar_novo_produto()

    def selecionar_novo_produto(self, produto_id):
        """Método público para compatibilidade"""
        self._selecionar_novo_produto(produto_id)

    def carregar_produtos(self):
        """Método público para compatibilidade"""
        self._carregar_produtos()

    def mostrar_produtos(self, produtos):
        """Método público para compatibilidade"""
        self._mostrar_produtos(produtos)

    def filtrar_produtos(self):
        """Método público para compatibilidade"""
        self._filtrar_produtos()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def selecionar_e_fechar(self, index):
        """Método público para compatibilidade"""
        self._selecionar_e_fechar(index)
