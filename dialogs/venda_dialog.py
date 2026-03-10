"""
Dialog de Venda - Versão Final com Frame de Entrada Rápida - LAYOUT AJUSTADO
Com suporte a redimensionamento inteligente via DialogSizeMixin
E verificação de modificações não salvas
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QGridLayout,  # NOVO: Importado para layout em grid
)

from dialogs.cliente_selection_dialog import ClienteSelectionDialog
from dialogs.observacao_dialog import ObservacaoDialog
from dialogs.pagamento_dialog import PagamentoDialog
from dialogs.produto_selection_dialog import ProdutoSelectionDialog
from mixins.dialog_size_mixin import DialogSizeMixin
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.produto import Produto
from utils.helpers import (
    aplicar_desconto_total,
    calcular_subtotal,
    formatar_moeda,
    validar_quantidade,
)
from utils.venda_utils import VendaUtils


class ProdutoVendaDialog(DialogSizeMixin, TableScrollNavigationMixin, QDialog):
    """Dialog para criação de vendas com frame de entrada rápida e redimensionamento inteligente"""

    venda_realizada = pyqtSignal()
    venda_crediario_realizada = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.produtos_selecionados = []
        self.cliente_selecionado = None
        self.desconto_total = 0.0
        self.observacao = ""
        self._primeira_exibicao = True
        self._modificacoes_nao_salvas = False
        self._init_ui()
        self._configurar_comportamento_enter()
        self._configurar_tamanho_dialog()

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

    def showEvent(self, event):
        """Chamado quando a janela é exibida - garante centralização"""
        super().showEvent(event)

        # Na primeira exibição, centralizar a janela
        if self._primeira_exibicao:
            self._primeira_exibicao = False
            # Usar QApplication para forçar processamento de eventos
            QApplication.processEvents()
            # Agora centralizar
            self._center_on_screen()

    def closeEvent(self, event):
        """NOVIDADE: Pergunta se deseja salvar antes de fechar"""
        # Se há modificações não salvas, perguntar ao usuário
        if self._modificacoes_nao_salvas and self._tem_dados_para_salvar():
            reply = QMessageBox.question(
                self,
                "Modificações não salvas",
                "Você tem modificações não salvas. Deseja salvar antes de sair?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                # Tenta finalizar a venda
                try:
                    self._finalizar_venda()
                    event.accept()  # Fecha após salvar
                except Exception as e:
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {str(e)}"
                    )
                    event.ignore()  # Não fecha se houver erro
                    return

            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()  # Descarta modificações e fecha

            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()  # Cancela o fechamento
                return

        super().closeEvent(event)

    def _tem_dados_para_salvar(self):
        """Verifica se há dados que podem ser salvos"""
        return (
            self.cliente_selecionado is not None and len(self.produtos_selecionados) > 0
        )

    def _marcar_como_modificado(self):
        """Marca que houve modificações não salvas"""
        self._modificacoes_nao_salvas = True
        self._atualizar_indicador_modificacoes()

    def _configurar_tamanho_dialog(self):
        """Configura o tamanho inteligente do diálogo usando o mixin"""
        self.setup_dialog_size(
            min_width=700,  # Largura mínima adequada para a tabela
            min_height=500,  # Altura mínima para ter espaço suficiente
            default_width_percent=0.95,  # 85% da tela
            default_height_percent=0.85,  # 90% da tela (aumentado para tabela maior)
            max_width_percent=0.85,  # Máximo 95% da tela
            max_height_percent=0.90,  # Máximo 95% da tela (aumentado)
        )

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

    # ========== MÉTODO MODIFICADO: Agora recebe layout pai e percentual ==========
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

    # ========== MÉTODO MODIFICADO: Aumentado para ocupar mais espaço vertical ==========
    def _criar_secao_produtos(self, layout):
        """Cria seção da tabela de produtos - AGORA COM MAIS ESPAÇO"""
        from PyQt6.QtWidgets import QSizePolicy  # IMPORT ADICIONADO AQUI
        
        grupo_produtos = QGroupBox("Produtos da Venda")
        grupo_produtos.setProperty("class", "clean-group")
        
        # Fazer este grupo ocupar mais espaço vertical
        grupo_produtos.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Horizontal
            QSizePolicy.Policy.Expanding   # Vertical
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
        vheader = self.tabela_produtos.verticalHeader()
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
                if hasattr(self, "tabela_produtos") and self.tabela_produtos:
                    for row in range(self.tabela_produtos.rowCount()):
                        self.tabela_produtos.setRowHeight(row, altura_desejada)
            except Exception:
                pass

        # Conectar ao sinal de dados alterados
        try:
            if hasattr(self.tabela_produtos, "model"):
                model = self.tabela_produtos.model()
                model.rowsInserted.connect(
                    lambda parent, first, last: aplicar_altura_quando_necessario()
                )
        except Exception:
            pass

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
        self.btn_finalizar.setProperty("class", "success")
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
        btn_cancelar.setProperty("class", "danger")
        btn_cancelar.setAutoDefault(False)
        btn_cancelar.clicked.connect(self._cancelar_venda)
        buttons_layout.addWidget(btn_cancelar)

        layout.addLayout(buttons_layout)

    def _configurar_atalhos(self):
        """Configura atalhos de teclado"""
        self.shortcut_f2 = QShortcut("F2", self)
        self.shortcut_f2.activated.connect(self._selecionar_cliente)

        self.shortcut_f3 = QShortcut("F3", self)
        self.shortcut_f3.activated.connect(self._selecionar_produto)

        self.shortcut_f4 = QShortcut("F4", self)
        self.shortcut_f4.activated.connect(self._abrir_observacao)

        self.shortcut_f5 = QShortcut("F5", self)
        self.shortcut_f5.activated.connect(self._finalizar_venda)

        self.shortcut_f10 = QShortcut("F10", self)
        self.shortcut_f10.activated.connect(self._aplicar_desconto)

        self.shortcut_delete = QShortcut(
            QKeySequence(QKeySequence.StandardKey.Delete), self
        )
        self.shortcut_delete.activated.connect(self._remover_produto)

    def _configurar_comportamento_enter(self):
        """Configura comportamento da tecla Enter para não interceptar o fluxo"""
        # Garantir que nenhum botão seja padrão
        for botao in self.findChildren(QPushButton):
            botao.setAutoDefault(False)
            botao.setDefault(False)

        # Definir foco inicial no campo código
        self.entry_codigo.setFocus()

    # ========== MÉTODOS DE ENTRADA RÁPIDA (mantidos iguais) ==========

    def _processar_enter_codigo(self):
        """Enter no campo código - busca produto e vai para quantidade"""
        codigo_texto = self.entry_codigo.text().strip()
        if not codigo_texto:
            return

        # Buscar produto
        produto_encontrado = self._buscar_e_validar_produto(codigo_texto)

        if produto_encontrado:
            # Ir para o próximo campo
            self.entry_quantidade.setFocus()
            self.entry_quantidade.selectAll()
        else:
            # Manter foco no código se produto não foi encontrado
            self.entry_codigo.selectAll()

    def _processar_enter_quantidade(self):
        """Enter no campo quantidade - vai para valor"""
        quantidade_texto = self.entry_quantidade.text().strip()

        # Validar quantidade
        if not quantidade_texto:
            self.entry_quantidade.setText("1")

        try:
            quantidade = int(quantidade_texto or "1")
            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Quantidade deve ser um número inteiro.")
            self.entry_quantidade.setFocus()
            self.entry_quantidade.selectAll()
            return

        # Ir para campo valor
        self.entry_valor.setFocus()
        self.entry_valor.selectAll()

    def _processar_enter_valor(self):
        """Enter no campo valor - adiciona produto e volta para código"""
        self._adicionar_produto_entrada_rapida()

    def _buscar_e_validar_produto(self, codigo_texto):
        """Busca e valida produto pelo código"""
        try:
            produto_id = int(codigo_texto)
            produto = Produto.buscar_por_id(produto_id)

            if produto:
                self._exibir_produto_encontrado(produto)
                return True
            else:
                self.label_produto_encontrado.setText("❌ Produto não encontrado")
                self.entry_valor.clear()
                return False

        except ValueError:
            self.label_produto_encontrado.setText("❌ Código inválido")
            self.entry_valor.clear()
            return False

    def _buscar_produto_por_codigo(self):
        """Busca produto pelo código digitado (chamado no textChanged)"""
        codigo_texto = self.entry_codigo.text().strip()

        if not codigo_texto:
            self._limpar_info_produto()
            return

        # Só buscar se for um número válido
        try:
            produto_id = int(codigo_texto)
            encontrou_produto = self._buscar_e_validar_produto(codigo_texto)

            # Se encontrou produto válido, atualizar valor automaticamente
            if encontrou_produto:
                self._atualizar_valor_automatico(produto_id)

        except ValueError:
            if len(codigo_texto) > 0:  # Só mostrar erro se há texto
                self.label_produto_encontrado.setText("❌ Digite apenas números")
                self.entry_valor.clear()  # Limpar valor se código inválido

    def _atualizar_valor_automatico(self, produto_id):
        """Atualiza valor automaticamente sempre que um produto válido for encontrado"""
        try:
            produto = Produto.buscar_por_id(produto_id)

            if produto and produto.preco_venda > 0:
                # Sempre atualizar o valor com o preço do produto atual
                valor_formatado = f"{produto.preco_venda:.2f}".replace(".", ",")
                self.entry_valor.setText(valor_formatado)
            else:
                # Se produto não tem preço válido, limpar campo
                self.entry_valor.clear()
        except Exception:
            # Em caso de erro, limpar campo
            self.entry_valor.clear()

    def _limpar_info_produto(self):
        """Limpa informações do produto"""
        self.label_produto_encontrado.clear()
        self.entry_valor.clear()

    def _exibir_produto_encontrado(self, produto):
        """Exibe informações do produto encontrado"""
        if produto.preco_venda <= 0:
            self.label_produto_encontrado.setText(
                f"⚠️ {produto.nome} - Produto sem preço de venda!"
            )
            return

        if produto.estoque <= 0:
            self.label_produto_encontrado.setText(f"⚠️ {produto.nome} - Sem estoque!")
            return

        # Produto válido
        info_produto = f"✅ {produto.nome}"
        if produto.cor:
            info_produto += f" - {produto.cor}"
        if produto.tamanho:
            info_produto += f" - {produto.tamanho}"
        info_produto += f" (Estoque: {produto.estoque})"

        self.label_produto_encontrado.setText(info_produto)

    def _adicionar_produto_entrada_rapida(self):
        """Adiciona produto usando entrada rápida"""
        codigo_texto = self.entry_codigo.text().strip()
        quantidade_texto = self.entry_quantidade.text().strip()
        valor_texto = self.entry_valor.text().strip()

        # Validações
        if not codigo_texto:
            QMessageBox.warning(self, "Aviso", "Digite o código do produto.")
            self.entry_codigo.setFocus()
            return

        if not quantidade_texto:
            quantidade_texto = "1"
            self.entry_quantidade.setText("1")

        if not valor_texto:
            QMessageBox.warning(self, "Aviso", "Digite o valor de venda.")
            self.entry_valor.setFocus()
            return

        try:
            produto_id = int(codigo_texto)
            quantidade = int(quantidade_texto)

            # Converter valor (aceita vírgula ou ponto)
            valor_venda = float(valor_texto.replace(",", "."))

            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            if valor_venda <= 0:
                QMessageBox.warning(
                    self, "Aviso", "O valor de venda deve ser maior que zero."
                )
                self.entry_valor.setFocus()
                self.entry_valor.selectAll()
                return

            produto = Produto.buscar_por_id(produto_id)

            if not produto:
                QMessageBox.warning(self, "Aviso", "Produto não encontrado.")
                self.entry_codigo.setFocus()
                self.entry_codigo.selectAll()
                return

            # Validações de estoque
            if produto.estoque <= 0:
                QMessageBox.warning(
                    self,
                    "Produto sem estoque",
                    f"O produto '{produto.nome}' está sem estoque e não pode ser vendido.",
                )
                return

            if quantidade > produto.estoque:
                QMessageBox.warning(
                    self,
                    "Estoque insuficiente",
                    f"Quantidade solicitada ({quantidade}) maior que o estoque disponível ({produto.estoque}).",
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            # Criar uma cópia do produto com o novo preço para esta venda
            produto_venda = Produto(
                id=produto.id,
                nome=produto.nome,
                preco_custo=produto.preco_custo,
                preco_venda=valor_venda,  # Usar o valor digitado
                estoque=produto.estoque,
                fornecedor_id=produto.fornecedor_id,
                ativo=produto.ativo,
                tamanho=produto.tamanho,
                cor=produto.cor,
                ea=produto.ea,
                referencia=produto.referencia,
            )

            self._adicionar_produto(produto_venda, quantidade)
            self._limpar_entrada_rapida()

        except ValueError as e:
            QMessageBox.warning(self, "Aviso", f"Valores inválidos: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao adicionar produto: {str(e)}")

    def _limpar_entrada_rapida(self):
        """Limpa campos de entrada rápida e volta foco para código"""
        self.entry_codigo.clear()
        self.entry_quantidade.setText("1")
        self.entry_valor.clear()
        self.label_produto_encontrado.clear()

        # Voltar foco para o campo código para continuar fluxo
        self.entry_codigo.setFocus()

    # ========== MÉTODOS DE AÇÃO (mantidos iguais) ==========

    def _cancelar_venda(self):
        """Método próprio para cancelar - verifica modificações"""
        # Se não há modificações, apenas fecha
        if not self._modificacoes_nao_salvas:
            self.reject()
            return

        # Se há modificações, pergunta ao usuário
        if self._tem_dados_para_salvar():
            reply = QMessageBox.question(
                self,
                "Modificações não salvas",
                "Você tem modificações não salvas. Deseja salvar antes de cancelar?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                # Tenta finalizar
                try:
                    self._finalizar_venda()
                    # Se salvou com sucesso, fecha a janela
                    self.reject()
                except Exception as e:
                    # Se houver erro ao salvar, não fecha
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {str(e)}"
                    )
                    return

            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()  # Descarta modificações e fecha

            # Se escolheu Cancelar, não faz nada (permanece na tela)
        else:
            self.reject()

    def _selecionar_cliente(self):
        """F2 - Selecionar cliente"""
        dialog = ClienteSelectionDialog(self)
        if dialog.exec():
            cliente = dialog.get_cliente_selecionado()
            if cliente:
                self.cliente_selecionado = cliente
                self.label_cliente.setText(cliente.nome)
                self._marcar_como_modificado()
                self._verificar_habilitar_finalizacao()

    def _selecionar_produto(self):
        """F3 - Adicionar produto"""
        dialog = ProdutoSelectionDialog(self)
        if dialog.exec():
            produto = dialog.get_produto_selecionado()
            if produto:
                self._processar_produto(produto)

    def _abrir_observacao(self):
        """F4 - Abrir dialog de observação"""
        dialog = ObservacaoDialog(self.observacao, self)
        if dialog.exec():
            nova_observacao = dialog.get_observacao()
            if nova_observacao != self.observacao:
                self.observacao = nova_observacao
                self._marcar_como_modificado()

    def _processar_produto(self, produto):
        """Processa produto selecionado com validações"""
        # Validações
        if produto.preco_venda <= 0:
            QMessageBox.warning(
                self,
                "Produto inválido",
                f"O produto '{produto.nome}' possui preço de venda 0 e não pode ser vendido.",
            )
            return

        if produto.estoque <= 0:
            QMessageBox.warning(
                self,
                "Produto sem estoque",
                f"O produto '{produto.nome}' está sem estoque e não pode ser vendido.",
            )
            return

        # Diálogo de quantidade
        quantidade_dialog = QInputDialog(self)

        quantidade_dialog.setWindowTitle("Quantidade")
        
        nome_completo = produto.nome
        if hasattr(produto, 'cor') and produto.cor:
            nome_completo += f" {produto.cor}"
        if hasattr(produto, 'tamanho') and produto.tamanho:
            nome_completo += f" {produto.tamanho}"
        
        quantidade_dialog.setLabelText(nome_completo)
        quantidade_dialog.setIntValue(1)
        quantidade_dialog.setIntMinimum(1)
        quantidade_dialog.setIntMaximum(produto.estoque)
        quantidade_dialog.setIntStep(1)

        quantidade_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        quantidade_dialog.setFixedSize(400, 150)

        if quantidade_dialog.exec() == QDialog.DialogCode.Accepted:
            quantidade = quantidade_dialog.intValue()

            if validar_quantidade(quantidade, produto.estoque):
                # Diálogo de preço
                preco_dialog = QInputDialog(self)

                preco_dialog.setWindowTitle("Preço de Venda")
                preco_dialog.setLabelText("Digite o preço de venda:")
                preco_dialog.setDoubleValue(produto.preco_venda)
                preco_dialog.setDoubleMinimum(0.01)
                preco_dialog.setDoubleDecimals(2)

                preco_dialog.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                    | Qt.WindowType.WindowCloseButtonHint
                    | Qt.WindowType.MSWindowsFixedSizeDialogHint
                )

                preco_dialog.setFixedSize(450, 220)

                from PyQt6.QtCore import QTimer
                from PyQt6.QtWidgets import QDoubleSpinBox
                
                def configurar_spinbox():
                    spinboxes = preco_dialog.findChildren(QDoubleSpinBox)
                    for spinbox in spinboxes:
                        spinbox.setRange(0.01, 9999999.99)
                        spinbox.setFixedWidth(220)
                        spinbox.setGroupSeparatorShown(True)
                        spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
                        break
                
                QTimer.singleShot(50, configurar_spinbox)

                if preco_dialog.exec() == QDialog.DialogCode.Accepted:
                    preco_venda = preco_dialog.doubleValue()

                    if preco_venda > 0:
                        produto_venda = Produto(
                            id=produto.id,
                            nome=produto.nome,
                            preco_custo=produto.preco_custo,
                            preco_venda=preco_venda,
                            estoque=produto.estoque,
                            fornecedor_id=produto.fornecedor_id,
                            ativo=produto.ativo,
                            tamanho=produto.tamanho,
                            cor=produto.cor,
                            ea=produto.ea,
                            referencia=produto.referencia,
                        )

                        self._adicionar_produto(produto_venda, quantidade)
                    else:
                        QMessageBox.warning(
                            self, 
                            "Aviso", 
                            "O preço de venda deve ser maior que zero."
                        )

    def _adicionar_produto(self, produto, quantidade):
        """Adiciona produto à venda"""
        # Validações finais
        if produto.preco_venda <= 0 or produto.estoque <= 0:
            return

        if quantidade > produto.estoque:
            QMessageBox.warning(
                self,
                "Estoque insuficiente",
                f"Quantidade solicitada maior que o estoque disponível ({produto.estoque}).",
            )
            return

        subtotal = calcular_subtotal(produto.preco_venda, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod["id"] == produto.id:
                nova_quantidade = prod["quantidade"] + quantidade
                if nova_quantidade > produto.estoque:
                    QMessageBox.warning(
                        self,
                        "Estoque insuficiente",
                        f"Quantidade total ({nova_quantidade}) excede o estoque disponível ({produto.estoque}).",
                    )
                    return
                self.produtos_selecionados[i]["quantidade"] = nova_quantidade
                self.produtos_selecionados[i]["subtotal"] = calcular_subtotal(
                    produto.preco_venda, nova_quantidade
                )
                self._atualizar_tabela()
                self._marcar_como_modificado()
                return

        # Adicionar novo produto
        self.produtos_selecionados.append(
            {
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco_venda,
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

        self._atualizar_tabela()
        self._marcar_como_modificado()

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self,
                "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} da venda?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
                self._marcar_como_modificado()
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _aplicar_desconto(self):
        """F10 - Aplicar desconto"""
        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione produtos antes de aplicar desconto."
            )
            return

        total_sem_desconto = sum(
            prod["subtotal"] for prod in self.produtos_selecionados
        )

        desconto, ok = QInputDialog.getDouble(
            self,
            "Desconto na Nota",
            f"Valor total: R$ {total_sem_desconto:.2f}\n\nDigite o valor do desconto:",
            value=self.desconto_total,
            min=0.0,
            max=total_sem_desconto,
            decimals=2,
        )

        if ok:
            self.desconto_total = desconto
            self._calcular_total()
            self._marcar_como_modificado()

    def _calcular_total(self):
        """Calcula total da venda com desconto"""
        total_produtos = sum(prod["subtotal"] for prod in self.produtos_selecionados)
        total_venda = aplicar_desconto_total(total_produtos, self.desconto_total)

        self.label_subtotal.setText(formatar_moeda(total_produtos))
        self.label_desconto_aplicado.setText(formatar_moeda(self.desconto_total))
        self.label_total_final.setText(formatar_moeda(total_venda))

        self._atualizar_indicador_modificacoes()

    def _atualizar_indicador_modificacoes(self):
        """Atualiza indicador visual de modificações não salvas"""
        if self._modificacoes_nao_salvas:
            self.label_modificacoes.setText("✎ Modificações não salvas")
            self.label_modificacoes.setVisible(True)
        else:
            self.label_modificacoes.setVisible(False)

    def _atualizar_tabela(self):
        """Atualiza tabela de produtos"""
        self.tabela_produtos.setRowCount(len(self.produtos_selecionados))

        for row, produto in enumerate(self.produtos_selecionados):
            # Buscar dados completos do produto para cor, tamanho e referência
            produto_obj = Produto.buscar_por_id(produto["id"])

            # ID
            id_item = QTableWidgetItem(str(produto["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 0, id_item)

            # Nome
            self.tabela_produtos.setItem(row, 1, QTableWidgetItem(produto["nome"]))

            # Cor
            cor_item = QTableWidgetItem(
                produto_obj.cor if produto_obj and produto_obj.cor else ""
            )
            cor_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 2, cor_item)

            # Tamanho
            tamanho_item = QTableWidgetItem(
                produto_obj.tamanho if produto_obj and produto_obj.tamanho else ""
            )
            tamanho_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 3, tamanho_item)

            # Referência
            ref_item = QTableWidgetItem(
                produto_obj.referencia if produto_obj and produto_obj.referencia else ""
            )
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 4, ref_item)

            # Preço
            preco_item = QTableWidgetItem(formatar_moeda(produto["preco"]))
            preco_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 5, preco_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto["quantidade"]))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 6, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto["subtotal"]))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, subtotal_item)

        # Rolar para o final da tabela para mostrar o produto recém-adicionado
        if self.produtos_selecionados:
            self.tabela_produtos.scrollToBottom()
            # Também selecionar a última linha para destacar o produto adicionado
            ultima_linha = len(self.produtos_selecionados) - 1
            self.tabela_produtos.selectRow(ultima_linha)

        self._calcular_total()
        self._verificar_habilitar_finalizacao()

    def _verificar_habilitar_finalizacao(self):
        """Verifica se pode habilitar finalização"""
        pode_finalizar = (
            len(self.produtos_selecionados) > 0 and self.cliente_selecionado is not None
        )
        self.btn_finalizar.setEnabled(pode_finalizar)

    def _finalizar_venda(self):
        """F5 - Finalizar venda"""
        if self.cliente_selecionado is None:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente para a venda.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione pelo menos um produto à venda."
            )
            return

        total_produtos = sum(prod["subtotal"] for prod in self.produtos_selecionados)
        total_venda = aplicar_desconto_total(total_produtos, self.desconto_total)

        pagamento_dialog = PagamentoDialog(
            total_venda, self.cliente_selecionado.id, self
        )
        if pagamento_dialog.exec():
            dados_pagamento = pagamento_dialog.get_dados()

            forma_pagamento = dados_pagamento["forma_pagamento"]
            parcelas = dados_pagamento["parcelas"]
            data_primeiro_vencimento = dados_pagamento["data_primeiro_vencimento"]
            valor_entrada = dados_pagamento["valor_entrada"]
            valor_financiado = dados_pagamento["valor_financiado"]

            try:
                from models.duplicata import Duplicata
                from models.venda import Venda

                observacao = self.observacao

                venda = Venda(
                    cliente_id=self.cliente_selecionado.id,
                    total=total_venda,
                    forma_pagamento=forma_pagamento,
                    status=(
                        "concluida"
                        if forma_pagamento in ["Dinheiro", "Pix", "Cartão"]
                        else "parcelada"
                    ),
                    parcelas=parcelas,
                    desconto=self.desconto_total,
                    observacao=observacao,
                    valor_entrada=valor_entrada,
                    valor_financiado=valor_financiado,
                )
                venda_id = venda.salvar()

                VendaUtils.salvar_itens_venda(venda_id, self.produtos_selecionados)

                # Atualizar estoque
                for produto in self.produtos_selecionados:
                    produto_obj = Produto.buscar_por_id(produto["id"])
                    if produto_obj:
                        produto_obj.estoque -= produto["quantidade"]
                        produto_obj.salvar()

                # Criar parcelas se crediário - usar valor financiado
                if forma_pagamento == "Crediario":
                    Duplicata.criar_parcelas(
                        venda_id,
                        self.cliente_selecionado.id,
                        valor_financiado,
                        parcelas,
                        data_primeiro_vencimento,
                    )
                    self.venda_crediario_realizada.emit(self.cliente_selecionado.id)

                QMessageBox.information(self, "Sucesso", "Venda realizada com sucesso!")
                self.venda_realizada.emit()
                
                # Limpar flag de modificações após salvar com sucesso
                self._modificacoes_nao_salvas = False
                self._atualizar_indicador_modificacoes()
                
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao processar venda: {str(e)}")

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def selecionar_cliente(self):
        """Método público para compatibilidade"""
        self._selecionar_cliente()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def processar_produto(self, produto):
        """Método público para compatibilidade"""
        self._processar_produto(produto)

    def adicionar_produto(self, produto, quantidade):
        """Método público para compatibilidade"""
        self._adicionar_produto(produto, quantidade)

    def remover_produto(self):
        """Método público para compatibilidade"""
        self._remover_produto()

    def aplicar_desconto(self):
        """Método público para compatibilidade"""
        self._aplicar_desconto()

    def calcular_total(self):
        """Método público para compatibilidade"""
        self._calcular_total()

    def atualizar_tabela(self):
        """Método público para compatibilidade"""
        self._atualizar_tabela()

    def verificar_habilitar_finalizacao(self):
        """Método público para compatibilidade"""
        self._verificar_habilitar_finalizacao()

    def finalizar_venda(self):
        """Método público para compatibilidade"""
        self._finalizar_venda()