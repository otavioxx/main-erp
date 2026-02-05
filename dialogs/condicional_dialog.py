"""
Dialog de Condicional - Versão com Frame de Entrada Rápida - CORRIGIDO
Com suporte a redimensionamento inteligente via DialogSizeMixin
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel,
                             QMessageBox, QHeaderView, QInputDialog, QFrame,
                             QLineEdit, QGroupBox, QGridLayout, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QShortcut, QKeySequence

from models.cliente import Cliente
from models.condicional import Condicional
from dialogs.cliente_selection_dialog import ClienteSelectionDialog
from dialogs.produto_selection_dialog import ProdutoSelectionDialog
from dialogs.observacao_dialog import ObservacaoDialog
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from mixins.dialog_size_mixin import DialogSizeMixin
from datetime import datetime, timedelta
from utils.helpers import aplicar_maiuscula_formulario, formatar_moeda, aplicar_desconto_total, validar_quantidade, calcular_subtotal


class CondicionalDialog(DialogSizeMixin, TableScrollNavigationMixin, QDialog):
    """Dialog para criação de condicionais com frame de entrada rápida e redimensionamento inteligente"""

    condicional_salva = pyqtSignal()

    def __init__(self, condicional_id=None, parent=None):
        super().__init__(parent)
        self.condicional_id = condicional_id
        self.produtos_selecionados = []
        self.cliente_selecionado = None
        self.desconto_total = 0.0
        self.observacao = ""
        self._primeira_exibicao = True
        self._modificacoes_nao_salvas = False  # NOVO: controle de modificações
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._configurar_tamanho_dialog()
        self._configurar_comportamento_enter()
        self._carregar_dados()
        self.showMaximized()

    def _init_ui(self):
        """Inicializa interface usando classes CSS semânticas"""
        self.setWindowTitle("Editar Condicional" if self.condicional_id else "Nova Condicional")

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        self._criar_header(layout)

        # Informações do cliente e data
        self._criar_secao_cliente_data(layout)

        # Frame de entrada rápida
        self._criar_frame_entrada_rapida(layout)

        # Tabela de produtos
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
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Tenta salvar
                try:
                    self._salvar_condicional()
                    event.accept()  # Fecha após salvar
                except Exception as e:
                    QMessageBox.warning(self, "Erro ao salvar", f"Não foi possível salvar: {str(e)}")
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
        return (self.cliente_selecionado is not None and 
                len(self.produtos_selecionados) > 0)

    def _marcar_como_modificado(self):
        """Marca que houve modificações não salvas"""
        self._modificacoes_nao_salvas = True

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
        """Cria cabeçalho da dialog"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Editar Condicional" if self.condicional_id else "Nova Condicional")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        # NOVO: Indicador de modificações não salvas
        self.label_modificacoes = QLabel("")
        self.label_modificacoes.setProperty("class", "warning")
        self.label_modificacoes.setVisible(False)
        header_layout.addWidget(self.label_modificacoes)

        layout.addWidget(header_frame)

    def _criar_secao_cliente_data(self, layout):
        """Cria seção combinada de cliente e data de devolução"""
        grupo_cliente_data = QGroupBox("Informações da Condicional")
        grupo_cliente_data.setProperty("class", "clean-group")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(8, 12, 8, 12)

        # Seção do cliente (esquerda)
        cliente_layout = QVBoxLayout()

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
        cliente_layout.addWidget(self.label_cliente)

        main_layout.addLayout(cliente_layout)

        # Separador vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setMaximumWidth(1)
        main_layout.addWidget(separator)

        # Adicionar stretch para empurrar a seção de data para a direita
        main_layout.addStretch()

        # Seção da data (direita)
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data prevista para devolução:"))

        self.date_devolucao = QLineEdit()
        data_futura = (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y")
        self.date_devolucao.setText(data_futura)
        self.date_devolucao.setPlaceholderText("DD/MM/AAAA")
        self.date_devolucao.setMaximumWidth(120)
        # NOVO: Conectar alterações
        self.date_devolucao.textChanged.connect(self._marcar_como_modificado)
        data_layout.addWidget(self.date_devolucao)

        main_layout.addLayout(data_layout)

        grupo_cliente_data.setLayout(main_layout)
        layout.addWidget(grupo_cliente_data)

    def _criar_frame_entrada_rapida(self, layout):
        """Cria frame para entrada rápida de produtos"""
        grupo_entrada = QGroupBox("Entrada Rápida de Produto")
        grupo_entrada.setProperty("class", "clean-group")

        entrada_layout = QVBoxLayout()
        entrada_layout.setContentsMargins(8, 12, 8, 12)

        # Header com instrução
        header_entrada = QHBoxLayout()
        header_entrada.addStretch()
        entrada_layout.addLayout(header_entrada)

        # Campos de entrada em linha horizontal
        campos_layout = QHBoxLayout()
        campos_layout.setSpacing(12)

        # Campo Código do Produto
        codigo_layout = QVBoxLayout()
        codigo_layout.addWidget(QLabel("Código:"))
        self.entry_codigo = QLineEdit()
        self.entry_codigo.setPlaceholderText("ID do produto")
        self.entry_codigo.setMaximumWidth(120)
        # Conectar eventos
        self.entry_codigo.returnPressed.connect(self._processar_enter_codigo)
        self.entry_codigo.textChanged.connect(self._buscar_produto_por_codigo)
        codigo_layout.addWidget(self.entry_codigo)
        campos_layout.addLayout(codigo_layout)

        # Campo Quantidade
        qtd_layout = QVBoxLayout()
        qtd_layout.addWidget(QLabel("Quantidade:"))
        self.entry_quantidade = QLineEdit()
        self.entry_quantidade.setPlaceholderText("1")
        self.entry_quantidade.setText("1")
        self.entry_quantidade.setMaximumWidth(100)
        self.entry_quantidade.returnPressed.connect(self._processar_enter_quantidade)
        # NOVO: Conectar alterações
        self.entry_quantidade.textChanged.connect(self._marcar_como_modificado)
        qtd_layout.addWidget(self.entry_quantidade)
        campos_layout.addLayout(qtd_layout)

        # Campo Valor de Venda (editável)
        valor_layout = QVBoxLayout()
        valor_layout.addWidget(QLabel("Valor de Venda:"))
        self.entry_valor = QLineEdit()
        self.entry_valor.setPlaceholderText("R$ 0,00")
        self.entry_valor.setMaximumWidth(120)
        self.entry_valor.returnPressed.connect(self._processar_enter_valor)
        # NOVO: Conectar alterações
        self.entry_valor.textChanged.connect(self._marcar_como_modificado)
        valor_layout.addWidget(self.entry_valor)
        campos_layout.addLayout(valor_layout)

        campos_layout.addStretch()

        entrada_layout.addLayout(campos_layout)

        # Label para mostrar produto encontrado
        self.label_produto_encontrado = QLabel("")
        self.label_produto_encontrado.setProperty("class", "muted")
        entrada_layout.addWidget(self.label_produto_encontrado)

        grupo_entrada.setLayout(entrada_layout)
        layout.addWidget(grupo_entrada)

    def _criar_secao_produtos(self, layout):
        """Cria seção da tabela de produtos"""
        grupo_produtos = QGroupBox("Produtos da Condicional")
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

        # Configurar tabela
        self._criar_tabela_produtos()
        produtos_layout.addWidget(self.tabela_produtos)

        grupo_produtos.setLayout(produtos_layout)
        layout.addWidget(grupo_produtos)

    def _criar_tabela_produtos(self):
        """Configura tabela de produtos - VERSÃO COM ALTURA FIXA"""
        self.tabela_produtos = QTableWidget()
        self.tabela_produtos.setColumnCount(8)
        self.tabela_produtos.setHorizontalHeaderLabels(
            ["ID", "Nome", "Cor", "Tamanho", "Referência", "Preço", "Qtd", "Subtotal"]
        )

        # Configurar colunas
        header = self.tabela_produtos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)   # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)   # Cor
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)   # Tamanho
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)   # Referência
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   # Preço
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)   # Qtd
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)   # Subtotal

        # Larguras das colunas
        self.tabela_produtos.setColumnWidth(0, 50)   # ID
        self.tabela_produtos.setColumnWidth(2, 120)  # Cor
        self.tabela_produtos.setColumnWidth(3, 70)   # Tamanho
        self.tabela_produtos.setColumnWidth(4, 100)  # Referência
        self.tabela_produtos.setColumnWidth(5, 80)   # Preço
        self.tabela_produtos.setColumnWidth(6, 60)   # Qtd
        self.tabela_produtos.setColumnWidth(7, 90)   # Subtotal
        
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

        # Botão salvar
        self.btn_salvar = QPushButton("F5 - Salvar Condicional")
        self.btn_salvar.setProperty("class", "success")
        self.btn_salvar.setEnabled(False)
        self.btn_salvar.clicked.connect(self._salvar_condicional)
        # IMPORTANTE: Não definir como botão padrão para não interceptar Enter
        self.btn_salvar.setAutoDefault(False)
        self.btn_salvar.setDefault(False)
        buttons_layout.addWidget(self.btn_salvar)

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
        btn_cancelar.clicked.connect(self._cancelar_condicional)  # Alterado para método próprio
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
        self.shortcut_f5.activated.connect(self._salvar_condicional)

        self.shortcut_f10 = QShortcut("F10", self)
        self.shortcut_f10.activated.connect(self._aplicar_desconto)

        self.shortcut_delete = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self)
        self.shortcut_delete.activated.connect(self._remover_produto)

    def _configurar_comportamento_enter(self):
        """Configura comportamento da tecla Enter para não interceptar o fluxo"""
        # Garantir que nenhum botão seja padrão
        for botao in self.findChildren(QPushButton):
            botao.setAutoDefault(False)
            botao.setDefault(False)

        # Definir foco inicial no campo código
        self.entry_codigo.setFocus()

    # ========== MÉTODOS DE ENTRADA RÁPIDA - CORRIGIDOS ==========

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
                QMessageBox.warning(self, "Aviso", "A quantidade deve ser maior que zero.")
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Quantidade deve ser um número inteiro.")
            self.entry_quantidade.setFocus()
            self.entry_quantidade.selectAll()
            return

        # Ir para campo valor (valor já foi atualizado automaticamente no textChanged do código)
        self.entry_valor.setFocus()
        self.entry_valor.selectAll()

    def _processar_enter_valor(self):
        """Enter no campo valor - adiciona produto e volta para código"""
        self._adicionar_produto_entrada_rapida()

    def _preencher_valor_automatico(self):
        """Preenche valor de venda automaticamente se não estiver preenchido"""
        if self.entry_valor.text().strip():
            return  # Já tem valor, não alterar

        codigo_texto = self.entry_codigo.text().strip()
        if not codigo_texto:
            return

        try:
            produto_id = int(codigo_texto)
            from models.produto import Produto
            produto = Produto.buscar_por_id(produto_id)

            if produto and produto.preco_venda > 0:
                # Formatar valor sem R$ para facilitar edição
                self.entry_valor.setText(f"{produto.preco_venda:.2f}".replace(".", ","))
        except (ValueError, Exception):
            pass

    def _buscar_e_validar_produto(self, codigo_texto):
        """Busca e valida produto pelo código"""
        try:
            produto_id = int(codigo_texto)
            from models.produto import Produto
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
            from models.produto import Produto
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
        self.entry_valor.clear()  # Agora também limpa o valor quando não há produto

    def _exibir_produto_encontrado(self, produto):
        """Exibe informações do produto encontrado"""
        if produto.preco_venda <= 0:
            self.label_produto_encontrado.setText(f"⚠️ {produto.nome} - Produto sem preço de venda!")
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
                QMessageBox.warning(self, "Aviso", "A quantidade deve ser maior que zero.")
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            if valor_venda <= 0:
                QMessageBox.warning(self, "Aviso", "O valor de venda deve ser maior que zero.")
                self.entry_valor.setFocus()
                self.entry_valor.selectAll()
                return

            from models.produto import Produto
            produto = Produto.buscar_por_id(produto_id)

            if not produto:
                QMessageBox.warning(self, "Aviso", "Produto não encontrado.")
                self.entry_codigo.setFocus()
                self.entry_codigo.selectAll()
                return

            # Validações de estoque
            if produto.estoque <= 0:
                QMessageBox.warning(
                    self, "Produto sem estoque",
                    f"O produto '{produto.nome}' está sem estoque e não pode ser vendido."
                )
                return

            if quantidade > produto.estoque:
                QMessageBox.warning(
                    self, "Estoque insuficiente",
                    f"Quantidade solicitada ({quantidade}) maior que o estoque disponível ({produto.estoque})."
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            # Criar uma cópia do produto com o novo preço para esta condicional
            produto_condicional = Produto(
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
                referencia=produto.referencia
            )

            self._adicionar_produto(produto_condicional, quantidade)
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

    # ========== MÉTODOS DE AÇÃO ==========

    def _cancelar_condicional(self):
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
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Tenta salvar
                try:
                    self._salvar_condicional()
                    # Se salvou com sucesso, fecha a janela
                    self.reject()
                except Exception as e:
                    # Se houver erro ao salvar, não fecha
                    QMessageBox.warning(self, "Erro ao salvar", f"Não foi possível salvar: {str(e)}")
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
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                self._verificar_habilitar_salvamento()

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
                self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _processar_produto(self, produto):
        """Processa produto selecionado com validações"""
        # Validações
        if produto.preco_venda <= 0:
            QMessageBox.warning(
                self, "Produto inválido",
                f"O produto '{produto.nome}' possui preço de venda 0 e não pode ser vendido."
            )
            return

        if produto.estoque <= 0:
            QMessageBox.warning(
                self, "Produto sem estoque",
                f"O produto '{produto.nome}' está sem estoque e não pode ser vendido."
            )
            return

        # Solicitar quantidade
        quantidade, ok = QInputDialog.getInt(
            self, "Quantidade",
            f"Quantidade:",
            value=1, min=1, max=produto.estoque, step=1
        )

        if ok and validar_quantidade(quantidade, produto.estoque):
            # Solicitar preço de venda
            preco_venda, ok_preco = QInputDialog.getDouble(
                self, "Preço de Venda",
                f"Preço de venda:",
                value=produto.preco_venda, min=0.01, decimals=2
            )

            if ok_preco:
                # Criar uma cópia do produto com o novo preço
                from models.produto import Produto
                produto_condicional = Produto(
                    id=produto.id,
                    nome=produto.nome,
                    preco_custo=produto.preco_custo,
                    preco_venda=preco_venda,  # Usar o preço confirmado
                    estoque=produto.estoque,
                    fornecedor_id=produto.fornecedor_id,
                    ativo=produto.ativo,
                    tamanho=produto.tamanho,
                    cor=produto.cor,
                    ea=produto.ea,
                    referencia=produto.referencia
                )

                self._adicionar_produto(produto_condicional, quantidade)

    def _adicionar_produto(self, produto, quantidade):
        """Adiciona produto à condicional"""
        # Validações finais
        if produto.preco_venda <= 0 or produto.estoque <= 0:
            return

        if quantidade > produto.estoque:
            QMessageBox.warning(
                self, "Estoque insuficiente",
                f"Quantidade solicitada maior que o estoque disponível ({produto.estoque})."
            )
            return

        subtotal = calcular_subtotal(produto.preco_venda, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod['id'] == produto.id:
                nova_quantidade = prod['quantidade'] + quantidade
                if nova_quantidade > produto.estoque:
                    QMessageBox.warning(
                        self, "Estoque insuficiente",
                        f"Quantidade total ({nova_quantidade}) excede o estoque disponível ({produto.estoque})."
                    )
                    return
                self.produtos_selecionados[i]['quantidade'] = nova_quantidade
                self.produtos_selecionados[i]['subtotal'] = calcular_subtotal(produto.preco_venda, nova_quantidade)
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                return

        # Adicionar novo produto
        self.produtos_selecionados.append({
            'id': produto.id,
            'nome': produto.nome,
            'preco': produto.preco_venda,
            'quantidade': quantidade,
            'subtotal': subtotal
        })

        self._atualizar_tabela()
        self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self, "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} da condicional?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _aplicar_desconto(self):
        """F10 - Aplicar desconto"""
        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione produtos antes de aplicar desconto.")
            return

        total_sem_desconto = sum(prod['subtotal'] for prod in self.produtos_selecionados)

        desconto, ok = QInputDialog.getDouble(
            self, "Desconto na Condicional",
            f"Valor total: R$ {total_sem_desconto:.2f}\n\nDigite o valor do desconto:",
            value=self.desconto_total, min=0.0, max=total_sem_desconto, decimals=2
        )

        if ok:
            self.desconto_total = desconto
            self._calcular_total()
            self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _calcular_total(self):
        """Calcula total da condicional com desconto"""
        total_produtos = sum(prod['subtotal'] for prod in self.produtos_selecionados)
        total_condicional = aplicar_desconto_total(total_produtos, self.desconto_total)

        self.label_subtotal.setText(formatar_moeda(total_produtos))
        self.label_desconto_aplicado.setText(formatar_moeda(self.desconto_total))
        self.label_total_final.setText(formatar_moeda(total_condicional))
        
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
        """Atualiza tabela de produtos"""
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

            # Preço
            preco_item = QTableWidgetItem(formatar_moeda(produto['preco']))
            preco_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 5, preco_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto['quantidade']))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 6, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto['subtotal']))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, subtotal_item)

        # Rolar para o final da tabela para mostrar o produto recém-adicionado
        if self.produtos_selecionados:
            self.tabela_produtos.scrollToBottom()
            # Também selecionar a última linha para destacar o produto adicionado
            ultima_linha = len(self.produtos_selecionados) - 1
            self.tabela_produtos.selectRow(ultima_linha)

        self._calcular_total()
        self._verificar_habilitar_salvamento()

    def _verificar_habilitar_salvamento(self):
        """Verifica se pode habilitar salvamento"""
        pode_salvar = (len(self.produtos_selecionados) > 0 and
                      self.cliente_selecionado is not None)
        self.btn_salvar.setEnabled(pode_salvar)

    def _carregar_dados(self):
        """Carrega dados da condicional para edição"""
        if self.condicional_id:
            try:
                if hasattr(self.condicional_id, 'id'):
                    condicional_id = self.condicional_id.id
                else:
                    condicional_id = self.condicional_id

                condicional = Condicional.buscar_por_id(condicional_id)
                if condicional:
                    self.cliente_selecionado = Cliente.buscar_por_id(condicional.cliente_id)
                    if self.cliente_selecionado:
                        self.label_cliente.setText(self.cliente_selecionado.nome)

                    if condicional.data_prevista_devolucao:
                        data_str = condicional.data_prevista_devolucao.strftime("%d/%m/%Y")
                        self.date_devolucao.setText(data_str)

                    self.observacao = condicional.observacao or ""
                    self.desconto_total = condicional.desconto or 0.0

                    for item in condicional.itens:
                        self.produtos_selecionados.append({
                            'id': item['produto_id'],
                            'nome': item['produto_nome'],
                            'preco': item['preco_unitario'],
                            'quantidade': item['quantidade'],
                            'subtotal': item['quantidade'] * item['preco_unitario']
                        })

                    self._atualizar_tabela()
                    # Após carregar dados, não há modificações não salvas
                    self._modificacoes_nao_salvas = False
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Erro ao carregar condicional: {str(e)}")

    def _salvar_condicional(self):
        """F5 - Salvar condicional"""
        if self.cliente_selecionado is None:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente para a condicional.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um produto à condicional.")
            return

        try:
            data_texto = self.date_devolucao.text().strip()
            if data_texto:
                try:
                    data_devolucao = datetime.strptime(data_texto, "%d/%m/%Y").date()
                except ValueError:
                    QMessageBox.warning(self, "Data Inválida", "Formato de data deve ser DD/MM/AAAA")
                    return
            else:
                data_devolucao = datetime.now().date() + timedelta(days=3)

            cliente_id = self.cliente_selecionado.id if hasattr(self.cliente_selecionado, 'id') else self.cliente_selecionado

            condicional = Condicional(
                id=self.condicional_id,
                cliente_id=cliente_id,
                data_condicional=datetime.now().date(),
                data_prevista_devolucao=data_devolucao,
                observacao=self.observacao,
                status="ativa",
                desconto=self.desconto_total
            )

            for produto in self.produtos_selecionados:
                condicional.itens.append({
                    'produto_id': produto['id'],
                    'quantidade': produto['quantidade'],
                    'preco_unitario': float(produto['preco'])
                })

            condicional_id = condicional.salvar()

            QMessageBox.information(self, "Sucesso",
                                "Condicional atualizada com sucesso!" if self.condicional_id
                                else "Condicional criada com sucesso!")

            # Atualizar o estado após salvar
            self.condicional_id = condicional_id  # Atualiza ID se for novo
            self._modificacoes_nao_salvas = False  # Limpa flag de modificações
            self._atualizar_indicador_modificacoes()  # Atualiza indicador

            self.condicional_salva.emit()
            # Não fecha automaticamente após salvar, permite continuar editando
            # self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar condicional: {str(e)}")

    def get_dados_condicional(self):
        """Retorna os dados da condicional para conversão em venda"""
        data_texto = self.date_devolucao.text().strip()
        if data_texto:
            try:
                data_devolucao = datetime.strptime(data_texto, "%d/%m/%Y").date()
            except ValueError:
                data_devolucao = datetime.now().date() + timedelta(days=3)
        else:
            data_devolucao = datetime.now().date() + timedelta(days=3)

        return {
            'cliente': self.cliente_selecionado,
            'produtos': self.produtos_selecionados.copy(),
            'data_devolucao': data_devolucao,
            'observacao': self.observacao,
            'desconto': self.desconto_total
        }

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método legado - redirecionado para _init_ui"""
        return self._init_ui()

    def selecionar_cliente(self):
        """Método público para compatibilidade"""
        self._selecionar_cliente()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def abrir_observacao(self):
        """Método público para compatibilidade"""
        self._abrir_observacao()

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

    def carregar_dados(self):
        """Método público para compatibilidade"""
        self._carregar_dados()

    def salvar_condicional(self):
        """Método público para compatibilidade"""
        self._salvar_condicional()