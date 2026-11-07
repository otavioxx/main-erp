"""
Dialog de Pedido - Modificado para incluir desconto e campos Cor, Tamanho, Referência - CORRIGIDO
Com suporte a redimensionamento inteligente via DialogSizeMixin
E verificação de modificações não salvas
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFocusEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app_logging import registrar_excecao
from dialogs.observacao_dialog import ObservacaoDialog
from mixins.dialog_size_mixin import DialogSizeMixin
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.pedido import Pedido
from utils.helpers import (
    aplicar_maiuscula_formulario,
    calcular_subtotal,
    formatar_moeda,
)
from utils.pedido_utils import PedidoUtils
from utils.tabela import fixar_altura_linhas


class PedidoDialog(DialogSizeMixin, TableScrollNavigationMixin, QDialog):
    """Dialog para criação/edição de pedidos com redimensionamento inteligente"""

    pedido_realizado = pyqtSignal()

    def __init__(self, parent=None, pedido=None):
        super().__init__(parent)
        self.produtos_selecionados = []
        self.fornecedor_selecionado = None
        self.valor_frete = 0.0
        self.valor_desconto = 0.0
        self.pedido_editando = pedido
        self.observacao = ""
        self._primeira_exibicao = True
        self._modificacoes_nao_salvas = False  # NOVO: controle de modificações
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._configurar_tamanho_dialog()
        self._carregar_dados_existentes()

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
                # Tenta finalizar o pedido
                try:
                    self._finalizar_pedido()
                    event.accept()  # Fecha após salvar
                except Exception as e:
                    registrar_excecao(
                        __name__,
                        "Exception handled in PedidoDialog.closeEvent in dialogs/pedido_dialog.py",
                    )
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {e!s}"
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
            self.fornecedor_selecionado is not None
            and len(self.produtos_selecionados) > 0
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
            default_height_percent=0.80,  # 90% da tela
            max_width_percent=0.85,  # Máximo 95% da tela
            max_height_percent=0.85,  # Máximo 95% da tela
        )

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

    # ========== MÉTODOS DE AÇÃO ==========

    def _cancelar_pedido(self):
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
                    self._finalizar_pedido()
                    # Se salvou com sucesso, fecha a janela
                    self.reject()
                except Exception as e:
                    # Se houver erro ao salvar, não fecha
                    registrar_excecao(
                        __name__,
                        "Exception handled in PedidoDialog._cancelar_pedido in dialogs/pedido_dialog.py",
                    )
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {e!s}"
                    )
                    return

            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()  # Descarta modificações e fecha

            # Se escolheu Cancelar, não faz nada (permanece na tela)
        else:
            self.reject()

    def _selecionar_fornecedor(self):
        """F2 - Selecionar fornecedor"""
        from .fornecedor_selection_dialog import FornecedorSelectionDialog

        dialog = FornecedorSelectionDialog(self)
        if dialog.exec():
            fornecedor = dialog.get_fornecedor_selecionado()
            if fornecedor:
                self.fornecedor_selecionado = fornecedor
                self.label_fornecedor.setText(fornecedor.nome)
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                self._verificar_habilitar_finalizacao()

    def _selecionar_produto(self):
        """F3 - Adicionar produto"""
        from .produto_selection_dialog import ProdutoSelectionDialog

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
                self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _processar_produto(self, produto):
        """Processa produto selecionado - ATUALIZADO COM DIÁLOGOS CORRIGIDOS E SELEÇÃO TOTAL"""
        # Validação básica
        if not hasattr(produto, "nome"):
            QMessageBox.warning(
                self, "Produto inválido", "Produto selecionado é inválido."
            )
            return

        # ========== DIÁLOGO DE QUANTIDADE (IGUAL AO MÓDULO VENDAS) ==========
        quantidade_dialog = QInputDialog(self)

        # Configurar propriedades do diálogo
        quantidade_dialog.setWindowTitle("Quantidade")

        # Montar nome do produto com cor e tamanho se disponíveis
        nome_produto = produto.nome
        if hasattr(produto, "cor") and produto.cor:
            nome_produto += f" {produto.cor}"
        if hasattr(produto, "tamanho") and produto.tamanho:
            nome_produto += f" {produto.tamanho}"

        quantidade_dialog.setLabelText(f"{nome_produto}")
        quantidade_dialog.setIntValue(1)
        quantidade_dialog.setIntMinimum(1)
        quantidade_dialog.setIntMaximum(10000)  # Limite razoável para pedidos
        quantidade_dialog.setIntStep(1)

        # Configurar flags da janela (idêntico ao módulo vendas)
        quantidade_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        # Tamanho fixo (idêntico ao módulo vendas)
        quantidade_dialog.setFixedSize(400, 150)

        # Executar o diálogo e verificar se foi aceito
        if quantidade_dialog.exec() == QDialog.DialogCode.Accepted:
            quantidade = quantidade_dialog.intValue()

            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                return

            # ========== DIÁLOGO DE PREÇO DE CUSTO (CORRIGIDO COM SELEÇÃO TOTAL) ==========
            preco_custo_dialog = QInputDialog(self)

            # Configurar propriedades do diálogo
            preco_custo_dialog.setWindowTitle("Preço de Custo")
            preco_custo_dialog.setLabelText("Digite o preço de custo:")

            # Usar preço de custo existente ou sugerir um valor
            valor_sugerido = getattr(produto, "preco_custo", 0) or 0
            if valor_sugerido <= 0:
                valor_sugerido = 10.0  # Valor padrão sugerido

            # CORREÇÃO: Configurar o valor máximo para um número alto
            VALOR_MAXIMO = 9999999.99

            preco_custo_dialog.setDoubleValue(valor_sugerido)
            preco_custo_dialog.setDoubleMinimum(0.01)
            preco_custo_dialog.setDoubleMaximum(VALOR_MAXIMO)  # <-- CORREÇÃO PRINCIPAL
            preco_custo_dialog.setDoubleDecimals(2)

            # Configurar flags da janela (igual ao módulo vendas)
            preco_custo_dialog.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.MSWindowsFixedSizeDialogHint
            )

            # Aumentar tamanho para acomodar números maiores
            preco_custo_dialog.setFixedSize(450, 220)

            # ===== SOLUÇÃO COMPLETA: Configurar o QDoubleSpinBox interno com seleção total =====
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QDoubleSpinBox

            def configurar_spinbox_custo():
                # Encontrar o QDoubleSpinBox dentro do diálogo
                spinboxes = preco_custo_dialog.findChildren(QDoubleSpinBox)
                for spinbox in spinboxes:
                    spinbox.setRange(0.01, VALOR_MAXIMO)  # Aumentar limite máximo
                    spinbox.setFixedWidth(220)  # Aumentar largura para números grandes
                    spinbox.setGroupSeparatorShown(True)  # Mostra separador de milhar
                    spinbox.setValue(valor_sugerido)

                    # CORREÇÃO: Forçar seleção total do texto quando o spinbox receber foco
                    spinbox.selectAll()

                    # Usar um timer para garantir que a seleção ocorra após o diálogo ser totalmente exibido
                    QTimer.singleShot(100, spinbox.selectAll)

                    # Conectar ao sinal de foco para sempre selecionar tudo quando ganhar foco
                    def selecionar_tudo_ao_focar(
                        event: QFocusEvent | None,
                        sb: QDoubleSpinBox = spinbox,
                    ) -> None:
                        QDoubleSpinBox.focusInEvent(sb, event)
                        sb.selectAll()

                    spinbox.focusInEvent = selecionar_tudo_ao_focar

                    break

            # Configurar após o diálogo ser mostrado
            QTimer.singleShot(50, configurar_spinbox_custo)
            # ===== FIM DA SOLUÇÃO =====

            # Executar e verificar se foi aceito
            if preco_custo_dialog.exec() == QDialog.DialogCode.Accepted:
                preco_custo = preco_custo_dialog.doubleValue()

                if preco_custo <= 0:
                    QMessageBox.warning(
                        self, "Aviso", "O preço de custo deve ser maior que zero."
                    )
                    return

                # ========== DIÁLOGO DE PREÇO DE VENDA (CORRIGIDO COM SELEÇÃO TOTAL) ==========
                preco_venda_dialog = QInputDialog(self)

                # Configurar propriedades do diálogo
                preco_venda_dialog.setWindowTitle("Preço de Venda")
                preco_venda_dialog.setLabelText("Digite o preço de venda:")

                # Calcular sugestão de preço de venda (30% sobre custo)
                sugestao_venda = preco_custo * 1.3

                # Se o produto já tem preço de venda, usar como referência
                if hasattr(produto, "preco_venda") and produto.preco_venda > 0:
                    sugestao_venda = produto.preco_venda

                preco_venda_dialog.setDoubleValue(sugestao_venda)
                preco_venda_dialog.setDoubleMinimum(0.01)
                preco_venda_dialog.setDoubleMaximum(
                    VALOR_MAXIMO
                )  # <-- CORREÇÃO PRINCIPAL
                preco_venda_dialog.setDoubleDecimals(2)

                # Configurar flags da janela (igual ao módulo vendas)
                preco_venda_dialog.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                    | Qt.WindowType.WindowCloseButtonHint
                    | Qt.WindowType.MSWindowsFixedSizeDialogHint
                )

                # Aumentar tamanho para acomodar números maiores
                preco_venda_dialog.setFixedSize(450, 220)

                # ===== SOLUÇÃO COMPLETA: Configurar o QDoubleSpinBox interno com seleção total =====
                def configurar_spinbox_venda():
                    spinboxes = preco_venda_dialog.findChildren(QDoubleSpinBox)
                    for spinbox in spinboxes:
                        spinbox.setRange(0.01, VALOR_MAXIMO)  # Aumentar limite máximo
                        spinbox.setFixedWidth(
                            220
                        )  # Aumentar largura para números grandes
                        spinbox.setGroupSeparatorShown(
                            True
                        )  # Mostra separador de milhar
                        spinbox.setValue(sugestao_venda)

                        # CORREÇÃO: Forçar seleção total do texto quando o spinbox receber foco
                        spinbox.selectAll()

                        # Usar um timer para garantir que a seleção ocorra após o diálogo ser totalmente exibido
                        QTimer.singleShot(100, spinbox.selectAll)

                        # Conectar ao sinal de foco para sempre selecionar tudo quando ganhar foco
                        def selecionar_tudo_ao_focar(
                            event: QFocusEvent | None,
                            sb: QDoubleSpinBox = spinbox,
                        ) -> None:
                            QDoubleSpinBox.focusInEvent(sb, event)
                            sb.selectAll()

                        spinbox.focusInEvent = selecionar_tudo_ao_focar

                        break

                QTimer.singleShot(50, configurar_spinbox_venda)
                # ===== FIM DA SOLUÇÃO =====

                # Executar e verificar se foi aceito
                if preco_venda_dialog.exec() == QDialog.DialogCode.Accepted:
                    preco_venda = preco_venda_dialog.doubleValue()

                    if preco_venda <= 0:
                        QMessageBox.warning(
                            self, "Aviso", "O preço de venda deve ser maior que zero."
                        )
                        return

                    self._adicionar_produto(
                        produto, preco_custo, preco_venda, quantidade
                    )

    def _adicionar_produto(self, produto, preco_custo, preco_venda, quantidade):
        """Adiciona produto ao pedido - MODIFICADO para incluir valor de venda"""
        subtotal = calcular_subtotal(preco_custo, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod["id"] == produto.id:
                nova_quantidade = prod["quantidade"] + quantidade
                self.produtos_selecionados[i]["quantidade"] = nova_quantidade
                self.produtos_selecionados[i]["preco_custo"] = (
                    preco_custo  # Atualizar preço
                )
                self.produtos_selecionados[i]["preco_venda"] = (
                    preco_venda  # Atualizar preço de venda
                )
                self.produtos_selecionados[i]["subtotal"] = calcular_subtotal(
                    preco_custo, nova_quantidade
                )
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                return

        # Adicionar novo produto
        self.produtos_selecionados.append(
            {
                "id": produto.id,
                "nome": produto.nome,
                "preco_custo": preco_custo,
                "preco_venda": preco_venda,  # NOVO CAMPO
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

        self._atualizar_tabela()
        self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self,
                "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} do pedido?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _definir_frete_desconto(self):
        """F10 - Definir frete e desconto - ATUALIZADO PARA DIÁLOGO MAIS CONSISTENTE"""
        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione produtos antes de definir frete e desconto."
            )
            return

        subtotal_produtos = sum(prod["subtotal"] for prod in self.produtos_selecionados)

        # Criar um diálogo personalizado mais consistente
        from PyQt6.QtWidgets import (
            QDialog,
            QFormLayout,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Frete e Desconto")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Informações do subtotal
        subtotal_label = QLabel(
            f"Subtotal dos produtos: {formatar_moeda(subtotal_produtos)}"
        )
        subtotal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtotal_label)

        # Formulário
        form_layout = QFormLayout()

        # Campo Frete
        frete_input = QLineEdit()
        frete_input.setText(str(self.valor_frete) if self.valor_frete > 0 else "0.00")
        frete_input.setPlaceholderText("0.00")
        form_layout.addRow("Frete (R$):", frete_input)

        # Campo Desconto
        desconto_input = QLineEdit()
        desconto_input.setText(
            str(self.valor_desconto) if self.valor_desconto > 0 else "0.00"
        )
        desconto_input.setPlaceholderText("0.00")
        form_layout.addRow("Desconto (R$):", desconto_input)

        layout.addLayout(form_layout)

        # Botões
        button_layout = QHBoxLayout()

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setProperty("class", "success")

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dialog.reject)
        btn_cancel.setProperty("class", "danger")

        button_layout.addWidget(btn_ok)
        button_layout.addWidget(btn_cancel)
        layout.addLayout(button_layout)

        # Configurar como diálogo modal
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Converter valores
                novo_frete = float(frete_input.text().replace(",", ".") or 0)
                novo_desconto = float(desconto_input.text().replace(",", ".") or 0)

                # Validar valores
                if novo_frete < 0:
                    QMessageBox.warning(self, "Aviso", "O frete não pode ser negativo.")
                    return

                if novo_desconto < 0:
                    QMessageBox.warning(
                        self, "Aviso", "O desconto não pode ser negativo."
                    )
                    return

                if novo_desconto > subtotal_produtos:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"Desconto (R$ {novo_desconto:.2f}) não pode ser maior que o subtotal (R$ {subtotal_produtos:.2f}).",
                    )
                    return

                self.valor_frete = novo_frete
                self.valor_desconto = novo_desconto
                self._calcular_total()
                self._marcar_como_modificado()

            except ValueError:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Digite valores numéricos válidos para frete e desconto.",
                )

    def _calcular_total(self):
        """Calcula total do pedido - ATUALIZADO com desconto"""
        subtotal = sum(prod["subtotal"] for prod in self.produtos_selecionados)
        total = subtotal - self.valor_desconto + self.valor_frete
        # Garantir que o total não seja negativo
        total = max(0, total)

        self.label_subtotal.setText(formatar_moeda(subtotal))
        self.label_desconto.setText(formatar_moeda(self.valor_desconto))
        self.label_frete.setText(formatar_moeda(self.valor_frete))
        self.label_total.setText(formatar_moeda(total))

        # NOVO: Atualiza indicador visual de modificações
        self._atualizar_indicador_modificacoes()

    def _atualizar_indicador_modificacoes(self):
        """Atualiza indicador visual de modificações não salvas"""
        if self._modificacoes_nao_salvas:
            self.label_modificacoes.setText("✎ Modificações não salvas")
            self.label_modificacoes.setVisible(True)
        else:
            self.label_modificacoes.setVisible(False)

    def _atualizar_tabela(self):
        """Atualiza tabela de produtos - MODIFICADO para incluir Cor, Tamanho, Referência e scroll automático"""
        self.tabela_produtos.setRowCount(len(self.produtos_selecionados))

        for row, produto in enumerate(self.produtos_selecionados):
            # Buscar dados completos do produto para cor, tamanho e referência
            from models.produto import Produto

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

            # Preço Custo
            custo_item = QTableWidgetItem(formatar_moeda(produto["preco_custo"]))
            custo_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 5, custo_item)

            # Preço Venda
            venda_item = QTableWidgetItem(formatar_moeda(produto["preco_venda"]))
            venda_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 6, venda_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto["quantidade"]))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto["subtotal"]))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 8, subtotal_item)

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
            len(self.produtos_selecionados) > 0
            and self.fornecedor_selecionado is not None
        )
        self.btn_finalizar.setEnabled(pode_finalizar)

    def _finalizar_pedido(self):
        """F5 - Finalizar pedido - ATUALIZADO com desconto"""
        if not self.fornecedor_selecionado:
            QMessageBox.warning(self, "Aviso", "Selecione um fornecedor.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um produto.")
            return

        subtotal = sum(prod["subtotal"] for prod in self.produtos_selecionados)
        total = max(0, subtotal - self.valor_desconto + self.valor_frete)

        if self._confirmar_pedido(subtotal, total):
            try:
                observacao = self.observacao

                if self.pedido_editando:
                    pedido_id = self._atualizar_pedido_existente(total, observacao)
                    mensagem = "Pedido atualizado com sucesso!"
                else:
                    pedido_id = self._criar_novo_pedido(total, observacao)
                    mensagem = "Pedido realizado com sucesso!"

                self._salvar_itens_pedido(pedido_id)

                QMessageBox.information(self, "Sucesso", mensagem)

                # Limpar flag de modificações após salvar com sucesso
                self._modificacoes_nao_salvas = False
                self._atualizar_indicador_modificacoes()

                self.pedido_realizado.emit()
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao processar pedido: {e!s}")

    def _confirmar_pedido(self, subtotal, total):
        """Confirma finalização do pedido - ATUALIZADO com desconto"""
        pedido_editando = self.pedido_editando
        fornecedor = self.fornecedor_selecionado
        if fornecedor is None:
            raise RuntimeError("Não é possível confirmar o pedido sem fornecedor.")

        if pedido_editando is not None:
            titulo = "Confirmar Edição"
            mensagem = f"EDITAR Pedido #{pedido_editando.id}\n\n"
        else:
            titulo = "Confirmar Pedido"
            mensagem = "NOVO Pedido\n\n"

        mensagem += (
            f"Fornecedor: {fornecedor.nome}\nSubtotal: {formatar_moeda(subtotal)}\n"
        )

        # Incluir desconto apenas se houver
        if self.valor_desconto > 0:
            mensagem += f"Desconto: {formatar_moeda(self.valor_desconto)}\n"

        # Incluir frete apenas se houver
        if self.valor_frete > 0:
            mensagem += f"Frete: {formatar_moeda(self.valor_frete)}\n"

        mensagem += (
            f"Total: {formatar_moeda(total)}\n\n"
            f"Confirmar {'edição' if pedido_editando is not None else 'pedido'}?"
        )

        resposta = QMessageBox.question(
            self,
            titulo,
            mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _atualizar_pedido_existente(self, total, observacao):
        """Atualiza pedido existente - ATUALIZADO com desconto"""
        pedido = self.pedido_editando
        fornecedor = self.fornecedor_selecionado
        if pedido is None:
            raise RuntimeError("Não há pedido em edição para atualizar.")
        if fornecedor is None:
            raise RuntimeError("Não é possível atualizar o pedido sem fornecedor.")

        pedido.fornecedor_id = fornecedor.id
        pedido.valor_total = total
        pedido.valor_frete = self.valor_frete
        pedido.desconto = self.valor_desconto
        pedido.observacao = observacao
        return pedido.salvar()

    def _criar_novo_pedido(self, total, observacao):
        """Cria novo pedido - ATUALIZADO com desconto"""
        fornecedor = self.fornecedor_selecionado
        if fornecedor is None:
            raise RuntimeError("Não é possível criar o pedido sem fornecedor.")

        pedido = Pedido(
            fornecedor_id=fornecedor.id,
            valor_total=total,
            valor_frete=self.valor_frete,
            desconto=self.valor_desconto,
            observacao=observacao,
            status="pendente",
        )
        return pedido.salvar()

    def _salvar_itens_pedido(self, pedido_id):
        """Salva itens do pedido"""
        from utils.database_utils import DatabaseUtils

        DatabaseUtils.executar_query(
            "DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,)
        )
        PedidoUtils.salvar_itens_pedido(pedido_id, self.produtos_selecionados)

    def _carregar_dados_existentes(self):
        """Carrega dados do pedido para edição - MODIFICADO para incluir desconto"""
        if not self.pedido_editando:
            return

        self.setWindowTitle(f"Editar Pedido #{self.pedido_editando.id}")

        # Carregar fornecedor
        from models.fornecedor import Fornecedor

        fornecedor = Fornecedor.buscar_por_id(self.pedido_editando.fornecedor_id)
        if fornecedor:
            self.fornecedor_selecionado = fornecedor
            self.label_fornecedor.setText(fornecedor.nome)

        # Carregar dados
        if self.pedido_editando.observacao:
            self.observacao = self.pedido_editando.observacao

        self.valor_frete = self.pedido_editando.valor_frete or 0.0
        self.valor_desconto = self.pedido_editando.desconto or 0.0

        # Carregar produtos
        itens = self.pedido_editando.obter_itens()
        for item in itens:
            self.produtos_selecionados.append(
                {
                    "id": item[2],  # produto_id
                    "nome": item[6],  # produto_nome
                    "preco_custo": item[4],  # preco_custo
                    "preco_venda": (
                        item[8] if len(item) > 8 and item[8] else item[4] * 1.3
                    ),  # preco_venda (com fallback)
                    "quantidade": item[3],  # quantidade
                    "subtotal": item[5],  # subtotal
                }
            )

        self._atualizar_tabela()
        self._verificar_habilitar_finalizacao()

        # Após carregar dados, não há modificações não salvas inicialmente
        self._modificacoes_nao_salvas = False
        self._atualizar_indicador_modificacoes()

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def definir_frete(self):
        """Método público para compatibilidade - MODIFICADO"""
        self._definir_frete_desconto()

    def selecionar_fornecedor(self):
        """Método público para compatibilidade"""
        self._selecionar_fornecedor()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def abrir_observacao(self):
        """Método público para compatibilidade"""
        self._abrir_observacao()

    def processar_produto(self, produto):
        """Método público para compatibilidade"""
        self._processar_produto(produto)

    def adicionar_produto(self, produto, preco_custo, quantidade, preco_venda=None):
        """Método público para compatibilidade - MODIFICADO"""
        if preco_venda is None:
            preco_venda = preco_custo * 1.3  # Margem padrão de 30%
        self._adicionar_produto(produto, preco_custo, preco_venda, quantidade)

    def remover_produto(self):
        """Método público para compatibilidade"""
        self._remover_produto()

    def calcular_total(self):
        """Método público para compatibilidade"""
        self._calcular_total()

    def atualizar_tabela(self):
        """Método público para compatibilidade"""
        self._atualizar_tabela()

    def verificar_habilitar_finalizacao(self):
        """Método público para compatibilidade"""
        self._verificar_habilitar_finalizacao()

    def finalizar_pedido(self):
        """Método público para compatibilidade"""
        self._finalizar_pedido()

    def carregar_dados_existentes(self):
        """Método público para compatibilidade"""
        self._carregar_dados_existentes()
