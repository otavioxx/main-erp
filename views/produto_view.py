"""
View de Produtos - Padronizada com sistema de estilos e correções de ordenação
"""

import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dialogs.relatorio_produto_dialog import RelatorioProdutoDialog
from imprecoes.print_produto import PrintProduto
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.produto import Produto
from utils.produto_utils import ProdutoUtils
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


class ProdutoView(TableScrollNavigationMixin, QWidget):
    """Interface de gestão de produtos otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.mostrar_inativos = False
        self.dados = []
        self._init_ui()
        self._carregar_produtos()

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

        # Grupo de produtos (tabela)
        self._criar_grupo_produtos(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gerenciamento de Produtos")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label para mostrar estado do filtro
        self.label_filtro = QLabel("(Mostrando apenas ativos - F11 para inativos)")
        self.label_filtro.setProperty("class", "muted")
        header_layout.addWidget(self.label_filtro)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_grupo_filtros(self, layout):
        """Cria o grupo de filtros"""
        grupo_filtros = QGroupBox("Filtros")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Campo de busca
        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText(
            "Nome, preço, fornecedor, cor, tamanho, referência ou estoque..."
        )
        self.busca_edit.setMaximumWidth(300)
        self.busca_edit.textChanged.connect(self._filtrar_produtos)
        filtro_layout.addWidget(self.busca_edit)

        filtro_layout.addStretch()

        # Botão limpar
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(btn_limpar)

        grupo_filtros.setLayout(filtro_layout)
        layout.addWidget(grupo_filtros)

    def _criar_grupo_acoes(self, layout):
        """Cria o grupo de ações com botões semânticos"""
        grupo_acoes = QGroupBox("Ações")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões com classes semânticas apropriadas
        self.btn_novo = QPushButton("Novo Produto")
        self.btn_novo.setProperty("class", "success")
        self.btn_novo.clicked.connect(self._novo_produto)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setProperty("class", "secondary")
        self.btn_editar.clicked.connect(self._editar_produto)

        self.btn_inativar = QPushButton("Inativar")
        self.btn_inativar.setProperty("class", "danger")
        self.btn_inativar.clicked.connect(self._inativar_produto)

        self.btn_reativar = QPushButton("Reativar")
        self.btn_reativar.setProperty("class", "warning")
        self.btn_reativar.clicked.connect(self._reativar_produto)

        self.btn_exportar = QPushButton("Imprimir Relatório")
        self.btn_exportar.setProperty("class", "primary")
        self.btn_exportar.clicked.connect(self._exportar_produtos)

        # Adicionar botões da esquerda
        btn_layout.addWidget(self.btn_novo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_inativar)
        btn_layout.addWidget(self.btn_reativar)

        # Espaço flexível para empurrar o botão de relatório para a direita
        btn_layout.addStretch()

        # Botão de relatório alinhado à direita
        btn_layout.addWidget(self.btn_exportar)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_produtos(self, layout):
        """Cria a tabela de produtos com configuração otimizada"""
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

        titulo = QLabel("Produtos")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_produtos = QTableWidget()
        self._configurar_tabela_produtos()
        container_layout.addWidget(self.tabela_produtos)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_produtos(self):
        """Configura a tabela de produtos de forma otimizada"""
        self.tabela_produtos.setColumnCount(11)  # Aumentado de 8 para 11
        self.tabela_produtos.setHorizontalHeaderLabels(
            [
                "ID",
                "Nome",
                "Cor",
                "Tamanho",
                "Referência",
                "Preço Custo",
                "Preço Venda",
                "Estoque",
                "Lucro %",
                "Markup %",
                "Fornecedor",
            ]
        )

        # Configuração das colunas
        header = self.tabela_produtos.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome

        for i in range(2, 11):  # Outras colunas fixas
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        # Larguras otimizadas com as novas colunas
        larguras_colunas = [50, 200, 120, 70, 100, 100, 100, 80, 80, 80, 200]
        for i, largura in enumerate(larguras_colunas):
            self.tabela_produtos.setColumnWidth(i, largura)

        # Configurações gerais da tabela
        self.tabela_produtos.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_produtos.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_produtos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_produtos.setAlternatingRowColors(True)
        self.tabela_produtos.verticalHeader().setVisible(False)
        self.tabela_produtos.setSortingEnabled(True)

        # Menu contextual
        self.tabela_produtos.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tabela_produtos.customContextMenuRequested.connect(
            self._mostrar_menu_contexto
        )

        self.setup_scroll_navigation(
            tabela=self.tabela_produtos,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    # ========== MÉTODOS DE CARREGAMENTO E FILTROS ==========

    def _carregar_produtos(self):
        """Carrega produtos na tabela com tratamento de erros"""
        try:
            if self.mostrar_inativos:
                self.dados = Produto.buscar_todos(apenas_ativos=False)
                self.label_filtro.setText(
                    "(Mostrando todos os registros - F11 para apenas ativos)"
                )
            else:
                self.dados = Produto.buscar_todos(apenas_ativos=True)
                self.label_filtro.setText(
                    "(Mostrando apenas ativos - F11 para inativos)"
                )

            self._filtrar_produtos()

        except Exception as e:
            self._mostrar_erro("Erro ao carregar produtos", str(e))

    def _filtrar_produtos(self):
        """CORREÇÃO: Filtra produtos por texto de busca - sempre usa dados originais"""
        texto_busca = self.busca_edit.text().lower().strip()

        # CORREÇÃO: Sempre trabalhar com os dados originais
        if texto_busca:
            dados_filtrados = [
                p
                for p in self.dados  # CORREÇÃO: sempre usar self.dados original
                if self._produto_corresponde_busca(p, texto_busca)
            ]
        else:
            dados_filtrados = self.dados

        self.tabela_produtos.setRowCount(len(dados_filtrados))
        self._preencher_tabela_produtos(dados_filtrados)

    def _produto_corresponde_busca(self, produto, texto_busca):
        """Verifica se produto corresponde à busca"""
        campos = [
            produto.nome or "",
            str(produto.id),
            str(produto.preco_custo),
            str(produto.preco_venda),
            str(produto.estoque),
            produto.fornecedor_nome or "",
            produto.cor or "",
            produto.tamanho or "",
            produto.referencia or "",
        ]
        return any(texto_busca in str(campo).lower() for campo in campos)

    def _preencher_tabela_produtos(self, produtos):
        """CORREÇÃO: Preenche a tabela com ordenação numérica correta"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_produtos.setSortingEnabled(False)

        # Cores para produtos inativos
        cor_fundo_inativo = QColor("#4a2a2a")
        cor_texto_inativo = QColor("#ff6b6b")
        cor_lucro_positivo = QColor("#51cf66")
        cor_lucro_negativo = QColor("#ff6b6b")

        for row, produto in enumerate(produtos):
            dados, lucro, markup = ProdutoUtils.formatar_item_produto(produto)

            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(dados["id"])
            item_id.setData(
                Qt.ItemDataRole.UserRole, produto.id
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_id.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 0, item_id)

            # Nome
            item_nome = QTableWidgetItem(dados["nome"])
            if not produto.ativo:
                item_nome.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 1, item_nome)

            # Cor
            item_cor = QTableWidgetItem(produto.cor or "")
            item_cor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_cor.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 2, item_cor)

            # Tamanho
            item_tamanho = QTableWidgetItem(produto.tamanho or "")
            item_tamanho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_tamanho.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 3, item_tamanho)

            # Referência
            item_ref = QTableWidgetItem(produto.referencia or "")
            item_ref.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_ref.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 4, item_ref)

            # CORREÇÃO: Preço Custo usando NumericTableWidgetItem
            item_custo = NumericTableWidgetItem(dados["preco_custo"])
            item_custo.setData(
                Qt.ItemDataRole.UserRole, produto.preco_custo
            )  # Valor numérico
            item_custo.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            if not produto.ativo:
                item_custo.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 5, item_custo)

            # CORREÇÃO: Preço Venda usando NumericTableWidgetItem
            item_venda = NumericTableWidgetItem(dados["preco_venda"])
            item_venda.setData(
                Qt.ItemDataRole.UserRole, produto.preco_venda
            )  # Valor numérico
            item_venda.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            if not produto.ativo:
                item_venda.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 6, item_venda)

            # CORREÇÃO: Estoque usando NumericTableWidgetItem
            item_estoque = NumericTableWidgetItem(dados["estoque"])
            item_estoque.setData(
                Qt.ItemDataRole.UserRole, produto.estoque
            )  # Valor numérico
            item_estoque.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_estoque.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 7, item_estoque)

            # CORREÇÃO: Lucro % usando NumericTableWidgetItem
            item_lucro = NumericTableWidgetItem(dados["lucro"])
            item_lucro.setData(Qt.ItemDataRole.UserRole, lucro)  # Valor numérico
            item_lucro.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if produto.ativo:
                if lucro > 25:
                    item_lucro.setForeground(cor_lucro_positivo)
                elif lucro < 25:
                    item_lucro.setForeground(cor_lucro_negativo)
            else:
                item_lucro.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 8, item_lucro)

            # CORREÇÃO: Markup % usando NumericTableWidgetItem
            item_markup = NumericTableWidgetItem(dados["markup"])
            item_markup.setData(Qt.ItemDataRole.UserRole, markup)  # Valor numérico
            item_markup.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if produto.ativo:
                if markup > 50:
                    item_markup.setForeground(cor_lucro_positivo)
                elif markup < 50:
                    item_markup.setForeground(cor_lucro_negativo)
            else:
                item_markup.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 9, item_markup)

            # Fornecedor
            item_fornecedor = QTableWidgetItem(dados["fornecedor"])
            if not produto.ativo:
                item_fornecedor.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 10, item_fornecedor)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_produtos.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_produtos.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _limpar_filtros(self):
        """Limpa todos os filtros e recarrega produtos"""
        self.busca_edit.clear()
        self._carregar_produtos()

    # ========== MÉTODOS DE AÇÕES ==========

    def _novo_produto(self):
        """Abre dialog para novo produto"""
        dialog = ProdutoDialog()
        if dialog.exec():
            self._carregar_produtos()
            self._mostrar_sucesso("Produto cadastrado com sucesso!")

    def _get_produto_selecionado(self):
        """Obtém o produto selecionado na tabela"""
        row = self.tabela_produtos.currentRow()
        if row == -1:
            return None
        try:
            produto_id = int(self.tabela_produtos.item(row, 0).text())
            return Produto.buscar_por_id(produto_id)
        except (ValueError, AttributeError):
            return None

    def _editar_produto(self):
        """Edita o produto selecionado"""
        produto = self._get_produto_selecionado()
        if not produto:
            self._mostrar_aviso("Selecione um produto para editar")
            return

        dialog = ProdutoDialog(produto)
        if dialog.exec():
            self._carregar_produtos()
            self._mostrar_sucesso("Produto atualizado com sucesso!")

    def _inativar_produto(self):
        """Inativa o produto selecionado com validações de negócio"""
        produto = self._get_produto_selecionado()
        if not produto:
            self._mostrar_aviso("Selecione um produto para inativar")
            return

        # Verifica se o produto pode ser inativado
        verificacao = produto.pode_ser_inativado()

        if not verificacao["pode"]:
            # Mostra os motivos pelos quais não pode ser inativado
            motivos_texto = "\n• ".join(verificacao["motivos"])
            self._mostrar_aviso(
                f"O produto '{produto.nome}' não pode ser inativado pelos seguintes motivos:\n\n"
                f"• {motivos_texto}\n\n"
                "Para inativar este produto, você deve:\n"
                "• Zerar o estoque (se houver)\n"
                "• Finalizar ou cancelar pedidos que o contenham\n"
                "• Finalizar ou cancelar condicionais que o contenham"
            )
            return

        # Se chegou até aqui, pode ser inativado
        if self._confirmar_inativacao(produto):
            try:
                produto.inativar()
                self._carregar_produtos()
                self.tabela_produtos.clearSelection()
                self._mostrar_sucesso("Produto inativado com sucesso!")
            except Exception as e:
                self._mostrar_erro("Erro ao inativar produto", str(e))

    def _reativar_produto(self):
        """Reativa o produto selecionado"""
        produto = self._get_produto_selecionado()
        if not produto:
            self._mostrar_aviso("Selecione um produto para reativar")
            return

        try:
            produto.ativo = True
            produto.salvar()
            self._carregar_produtos()
            self.tabela_produtos.clearSelection()
            self._mostrar_sucesso("Produto reativado com sucesso!")
        except Exception as e:
            self._mostrar_erro("Erro ao reativar produto", str(e))

    def _confirmar_inativacao(self, produto):
        """Confirma a inativação do produto com informações detalhadas"""
        from PyQt6.QtWidgets import QMessageBox

        # Verifica novamente para mostrar informações na confirmação
        verificacao = produto.pode_ser_inativado()

        if verificacao["pode"]:
            mensagem = (
                f"Tem certeza que deseja inativar o produto:\n\n"
                f"Nome: {produto.nome}\n"
                f"Estoque: {produto.estoque}\n"
                f"Preço de Venda: R$ {produto.preco_venda:.2f}\n\n"
                "O produto ficará inativo mas seus dados serão preservados."
            )
        else:
            # Isso não deveria acontecer, mas é uma segurança extra
            motivos_texto = "\n• ".join(verificacao["motivos"])
            mensagem = (
                f"ATENÇÃO: Este produto não pode ser inativado!\n\n"
                f"Motivos:\n• {motivos_texto}\n\n"
                "Deseja continuar mesmo assim? (NÃO RECOMENDADO)"
            )

        resposta = QMessageBox.question(
            self,
            "Confirmar Inativação",
            mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _exportar_produtos(self):
        """Abre diálogo para selecionar filtros e exporta relatório"""
        dialog = RelatorioProdutoDialog(self)
        if dialog.exec():
            filtros = dialog.get_filtros()
            self._gerar_relatorio_com_filtros(filtros)

    def _gerar_relatorio_com_filtros(self, filtros):
        """Gera relatório com base nos filtros selecionados"""
        try:
            filename = PrintProduto.gerar_relatorio_com_filtros(
                filtros=filtros, pasta_destino="relatorios"
            )

            if filename:
                self._abrir_arquivo(filename)
                self._mostrar_sucesso("Relatório gerado com sucesso!")
            else:
                self._mostrar_aviso("Não foi possível gerar o relatório")

        except Exception as e:
            self._mostrar_erro(
                "Erro na Exportação", f"Erro ao exportar produtos:\n{str(e)}"
            )

    def _abrir_arquivo(self, filename):
        """Abre arquivo gerado"""
        try:
            if os.name == "nt":
                os.startfile(filename)
            elif os.name == "posix":
                subprocess.run(
                    ["open" if sys.platform == "darwin" else "xdg-open", filename]
                )
        except Exception as e:
            self._mostrar_aviso(f"Não foi possível abrir automaticamente:\n{e}")

    def _mostrar_menu_contexto(self, pos):
        """Menu contextual"""
        menu = QMenu()

        editar_action = QAction("Editar", self)
        exportar_action = QAction("Exportar Lista", self)

        editar_action.triggered.connect(self._editar_produto)
        exportar_action.triggered.connect(self._exportar_produtos)

        menu.addAction(editar_action)
        menu.addAction(exportar_action)

        produto = self._get_produto_selecionado()
        if produto:
            if produto.ativo:
                inativar_action = QAction("Inativar", self)
                inativar_action.triggered.connect(self._inativar_produto)
                menu.addAction(inativar_action)
            else:
                reativar_action = QAction("Reativar", self)
                reativar_action.triggered.connect(self._reativar_produto)
                menu.addAction(reativar_action)

        menu.exec(self.tabela_produtos.mapToGlobal(pos))

    # ========== MÉTODOS DE INTERFACE ==========

    def _mostrar_erro(self, titulo, mensagem):
        """Mostra mensagem de erro"""
        QMessageBox.critical(self, titulo, mensagem)

    def _mostrar_aviso(self, mensagem):
        """Mostra mensagem de aviso"""
        QMessageBox.warning(self, "Aviso", mensagem)

    def _mostrar_sucesso(self, mensagem):
        """Mostra mensagem de sucesso"""
        QMessageBox.information(self, "Sucesso", mensagem)

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def carregar_dados(self):
        """Método público para compatibilidade com código existente"""
        self._carregar_produtos()

    def filtrar_produtos(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_produtos()

    def novo_registro(self):
        """Método público para compatibilidade com código existente"""
        self._novo_produto()

    def editar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._editar_produto()

    def inativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._inativar_produto()

    def reativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._reativar_produto()

    def exportar_produtos(self):
        """Método público para compatibilidade com código existente"""
        self._exportar_produtos()

    def toggle_mostrar_inativos(self):
        """Alterna entre mostrar ativos/inativos - compatibilidade com F11"""
        self.mostrar_inativos = not self.mostrar_inativos
        self._carregar_produtos()

    def keyPressEvent(self, event):
        """Manipula eventos de teclado"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_mostrar_inativos()
        else:
            super().keyPressEvent(event)
