"""
Dialog de Pedido - Modificado para incluir desconto e campos Cor, Tamanho, Referência - CORRIGIDO
Com suporte a redimensionamento inteligente via DialogSizeMixin
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel,
                             QMessageBox, QHeaderView, QInputDialog, QFrame,
                             QLineEdit, QGroupBox, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence
from utils.helpers import formatar_moeda, calcular_subtotal
from utils.pedido_utils import PedidoUtils
from models.pedido import Pedido
from dialogs.observacao_dialog import ObservacaoDialog
from dialogs.frete_desconto_dialog import FreteDescontoDialog
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from mixins.dialog_size_mixin import DialogSizeMixin
from utils.helpers import aplicar_maiuscula_formulario


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
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._configurar_tamanho_dialog()
        self._carregar_dados_existentes()
        self.showMaximized()

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

    def _configurar_tamanho_dialog(self):
        """Configura o tamanho inteligente do diálogo usando o mixin"""
        self.setup_dialog_size(
            min_width=700,           # Largura mínima adequada para a tabela
            min_height=500,           # Altura mínima para ter espaço suficiente
            default_width_percent=0.95,  # 85% da tela
            default_height_percent=0.80, # 90% da tela
            max_width_percent=0.85,      # Máximo 95% da tela
            max_height_percent=0.85      # Máximo 95% da tela
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
        self.tabela_produtos.setColumnCount(9)  # Aumentado para incluir Cor, Tamanho, Referência
        self.tabela_produtos.setHorizontalHeaderLabels([
            "ID", "Nome", "Cor", "Tamanho", "Referência", "Preço Custo", "Preço Venda", "Qtd", "Subtotal"
        ])

        # Configurar colunas
        header = self.tabela_produtos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Cor
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)   # Tamanho
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)   # Referência
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Preço Custo
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Preço Venda
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)   # Qtd
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)   # Subtotal

        # Definir larguras das colunas
        self.tabela_produtos.setColumnWidth(0, 50)   # ID
        self.tabela_produtos.setColumnWidth(2, 120)  # Cor
        self.tabela_produtos.setColumnWidth(3, 70)   # Tamanho
        self.tabela_produtos.setColumnWidth(4, 100)  # Referência
        self.tabela_produtos.setColumnWidth(5, 80)   # Preço Custo
        self.tabela_produtos.setColumnWidth(6, 80)   # Preço Venda
        self.tabela_produtos.setColumnWidth(7, 60)   # Qtd
        self.tabela_produtos.setColumnWidth(8, 90)   # Subtotal
        
        # ========== CONFIGURAÇÃO DE ALTURA ==========
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
                if hasattr(self, 'tabela_produtos') and self.tabela_produtos:
                    for row in range(self.tabela_produtos.rowCount()):
                        self.tabela_produtos.setRowHeight(row, altura_desejada)
            except:
                pass
        
        # Conectar ao sinal de dados alterados (quando a tabela for populada)
        try:
            if hasattr(self.tabela_produtos, 'model'):
                model = self.tabela_produtos.model()
                model.rowsInserted.connect(
                    lambda parent, first, last: aplicar_altura_quando_necessario()
                )
        except:
            pass
        # ========== FIM DA CONFIGURAÇÃO ==========

        # Configurações gerais
        self.tabela_produtos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_produtos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela_produtos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_produtos.setAlternatingRowColors(True)
        self.tabela_produtos.setSortingEnabled(False)

        self.setup_scroll_navigation(
            tabela=self.tabela_produtos,
            scroll_sensibilidade=1,      # 1 linha por scroll (padrão)
            auto_select_first=True       # Seleciona primeira linha automaticamente
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

        self.btn_finalizar = QPushButton("F5 - Finalizar Pedido")
        self.btn_finalizar.setProperty("class", "success")
        self.btn_finalizar.setEnabled(False)
        self.btn_finalizar.clicked.connect(self._finalizar_pedido)
        # Evitar que Enter acione o botão
        self.btn_finalizar.setAutoDefault(False)
        self.btn_finalizar.setDefault(False)
        buttons_layout.addWidget(self.btn_finalizar)

        self.btn_frete_desconto = QPushButton("F10 - Frete e Desconto")  # MODIFICADO
        self.btn_frete_desconto.setProperty("class", "warning")
        self.btn_frete_desconto.setAutoDefault(False)
        self.btn_frete_desconto.clicked.connect(self._definir_frete_desconto)  # MODIFICADO
        buttons_layout.addWidget(self.btn_frete_desconto)

        buttons_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "danger")
        btn_cancelar.setAutoDefault(False)
        btn_cancelar.clicked.connect(self.reject)
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
        self.shortcut_f10.activated.connect(self._definir_frete_desconto)  # MODIFICADO

        self.shortcut_delete = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self)
        self.shortcut_delete.activated.connect(self._remover_produto)

    # ========== MÉTODOS DE AÇÃO ==========

    def _selecionar_fornecedor(self):
        """F2 - Selecionar fornecedor"""
        from .fornecedor_selection_dialog import FornecedorSelectionDialog
        dialog = FornecedorSelectionDialog(self)
        if dialog.exec():
            fornecedor = dialog.get_fornecedor_selecionado()
            if fornecedor:
                self.fornecedor_selecionado = fornecedor
                self.label_fornecedor.setText(fornecedor.nome)
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
            self.observacao = dialog.get_observacao()

    def _processar_produto(self, produto):
        """Processa produto selecionado - MODIFICADO para incluir valor de venda"""
        # 1. Pedir quantidade
        quantidade, ok = QInputDialog.getInt(
            self, "Quantidade",
            f"Quantidade:",
            value=1, min=1, max=10000, step=1
        )

        if not ok or quantidade <= 0:
            return

        # 2. Pedir preço de custo
        preco_custo, ok = QInputDialog.getDouble(
            self, "Preço de Custo",
            f"Preço de custo para {produto.nome}:",
            value=produto.preco_custo or 0,
            min=0.01, max=10000, decimals=2
        )

        if not ok or preco_custo <= 0:
            return

        # 3. Pedir valor de venda
        preco_venda, ok = QInputDialog.getDouble(
            self, "Preço de Venda",
            f"Preço de venda para {produto.nome}:",
            value=produto.preco_venda if hasattr(produto, 'preco_venda') and produto.preco_venda else preco_custo * 1.3,  # Sugestão de 30% de margem
            min=0.01, max=10000, decimals=2
        )

        if ok and preco_venda > 0:
            self._adicionar_produto(produto, preco_custo, preco_venda, quantidade)

    def _adicionar_produto(self, produto, preco_custo, preco_venda, quantidade):
        """Adiciona produto ao pedido - MODIFICADO para incluir valor de venda"""
        subtotal = calcular_subtotal(preco_custo, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod['id'] == produto.id:
                nova_quantidade = prod['quantidade'] + quantidade
                self.produtos_selecionados[i]['quantidade'] = nova_quantidade
                self.produtos_selecionados[i]['preco_custo'] = preco_custo  # Atualizar preço
                self.produtos_selecionados[i]['preco_venda'] = preco_venda  # Atualizar preço de venda
                self.produtos_selecionados[i]['subtotal'] = calcular_subtotal(preco_custo, nova_quantidade)
                self._atualizar_tabela()
                return

        # Adicionar novo produto
        self.produtos_selecionados.append({
            'id': produto.id,
            'nome': produto.nome,
            'preco_custo': preco_custo,
            'preco_venda': preco_venda,  # NOVO CAMPO
            'quantidade': quantidade,
            'subtotal': subtotal,
        })

        self._atualizar_tabela()

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self, "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} do pedido?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _definir_frete_desconto(self):
        """F10 - Definir frete e desconto - NOVO MÉTODO"""
        subtotal_produtos = sum(prod['subtotal'] for prod in self.produtos_selecionados)

        dialog = FreteDescontoDialog(
            frete_atual=self.valor_frete,
            desconto_atual=self.valor_desconto,
            subtotal_produtos=subtotal_produtos,
            parent=self
        )

        if dialog.exec():
            self.valor_frete = dialog.get_frete()
            self.valor_desconto = dialog.get_desconto()
            self._calcular_total()

    def _calcular_total(self):
        """Calcula total do pedido - ATUALIZADO com desconto"""
        subtotal = sum(prod['subtotal'] for prod in self.produtos_selecionados)
        total = subtotal - self.valor_desconto + self.valor_frete
        # Garantir que o total não seja negativo
        total = max(0, total)

        self.label_subtotal.setText(formatar_moeda(subtotal))
        self.label_desconto.setText(formatar_moeda(self.valor_desconto))  # NOVO
        self.label_frete.setText(formatar_moeda(self.valor_frete))
        self.label_total.setText(formatar_moeda(total))

    def _atualizar_tabela(self):
        """Atualiza tabela de produtos - MODIFICADO para incluir Cor, Tamanho, Referência e scroll automático"""
        self.tabela_produtos.setRowCount(len(self.produtos_selecionados))

        for row, produto in enumerate(self.produtos_selecionados):
            # Buscar dados completos do produto para cor, tamanho e referência
            from models.produto import Produto
            produto_obj = Produto.buscar_por_id(produto['id'])

            # ID
            id_item = QTableWidgetItem(str(produto['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 0, id_item)

            # Nome
            self.tabela_produtos.setItem(row, 1, QTableWidgetItem(produto['nome']))

            # Cor
            cor_item = QTableWidgetItem(produto_obj.cor if produto_obj and produto_obj.cor else "")
            cor_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 2, cor_item)

            # Tamanho
            tamanho_item = QTableWidgetItem(produto_obj.tamanho if produto_obj and produto_obj.tamanho else "")
            tamanho_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 3, tamanho_item)

            # Referência
            ref_item = QTableWidgetItem(produto_obj.referencia if produto_obj and produto_obj.referencia else "")
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 4, ref_item)

            # Preço Custo
            custo_item = QTableWidgetItem(formatar_moeda(produto['preco_custo']))
            custo_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 5, custo_item)

            # Preço Venda
            venda_item = QTableWidgetItem(formatar_moeda(produto['preco_venda']))
            venda_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 6, venda_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto['quantidade']))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto['subtotal']))
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
        pode_finalizar = (len(self.produtos_selecionados) > 0 and
                         self.fornecedor_selecionado is not None)
        self.btn_finalizar.setEnabled(pode_finalizar)

    def _finalizar_pedido(self):
        """F5 - Finalizar pedido - ATUALIZADO com desconto"""
        if not self.fornecedor_selecionado:
            QMessageBox.warning(self, "Aviso", "Selecione um fornecedor.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um produto.")
            return

        subtotal = sum(prod['subtotal'] for prod in self.produtos_selecionados)
        total = max(0, subtotal - self.valor_desconto + self.valor_frete)  # ATUALIZADO

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
                self.pedido_realizado.emit()
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao processar pedido: {str(e)}")

    def _confirmar_pedido(self, subtotal, total):
        """Confirma finalização do pedido - ATUALIZADO com desconto"""
        if self.pedido_editando:
            titulo = "Confirmar Edição"
            mensagem = f"EDITAR Pedido #{self.pedido_editando.id}\n\n"
        else:
            titulo = "Confirmar Pedido"
            mensagem = "NOVO Pedido\n\n"

        mensagem += (
            f"Fornecedor: {self.fornecedor_selecionado.nome}\n"
            f"Subtotal: {formatar_moeda(subtotal)}\n"
        )

        # Incluir desconto apenas se houver
        if self.valor_desconto > 0:
            mensagem += f"Desconto: {formatar_moeda(self.valor_desconto)}\n"

        # Incluir frete apenas se houver
        if self.valor_frete > 0:
            mensagem += f"Frete: {formatar_moeda(self.valor_frete)}\n"

        mensagem += (
            f"Total: {formatar_moeda(total)}\n\n"
            f"Confirmar {'edição' if self.pedido_editando else 'pedido'}?"
        )

        resposta = QMessageBox.question(
            self, titulo, mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _atualizar_pedido_existente(self, total, observacao):
        """Atualiza pedido existente - ATUALIZADO com desconto"""
        self.pedido_editando.fornecedor_id = self.fornecedor_selecionado.id
        self.pedido_editando.valor_total = total
        self.pedido_editando.valor_frete = self.valor_frete
        self.pedido_editando.desconto = self.valor_desconto  # NOVO CAMPO
        self.pedido_editando.observacao = observacao
        return self.pedido_editando.salvar()

    def _criar_novo_pedido(self, total, observacao):
        """Cria novo pedido - ATUALIZADO com desconto"""
        pedido = Pedido(
            fornecedor_id=self.fornecedor_selecionado.id,
            valor_total=total,
            valor_frete=self.valor_frete,
            desconto=self.valor_desconto,  # NOVO CAMPO
            observacao=observacao,
            status='pendente'
        )
        return pedido.salvar()

    def _salvar_itens_pedido(self, pedido_id):
        """Salva itens do pedido"""
        from utils.database_utils import DatabaseUtils
        DatabaseUtils.executar_query(
            "DELETE FROM itens_pedido WHERE pedido_id = ?",
            (pedido_id,)
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
        self.valor_desconto = self.pedido_editando.desconto or 0.0  # NOVO CAMPO

        # Carregar produtos
        itens = self.pedido_editando.obter_itens()
        for item in itens:
            self.produtos_selecionados.append({
                'id': item[2],          # produto_id
                'nome': item[6],        # produto_nome
                'preco_custo': item[4], # preco_custo
                'preco_venda': item[8] if len(item) > 8 and item[8] else item[4] * 1.3,  # preco_venda (com fallback)
                'quantidade': item[3],  # quantidade
                'subtotal': item[5],    # subtotal
            })

        self._atualizar_tabela()
        self._verificar_habilitar_finalizacao()

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