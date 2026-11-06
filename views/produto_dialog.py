"""
Dialog de Produto - Otimizado para novo sistema de estilos com Cadastro em Lote
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QDialogButtonBox, QDoubleSpinBox,
                             QSpinBox, QCheckBox, QGroupBox, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from models.produto import Produto
from models.fornecedor import Fornecedor
from dialogs.fornecedor_selection_dialog import FornecedorSelectionDialog
from utils.helpers import SelectAllLineEdit, SelectAllDoubleSpinBox, SelectAllSpinBox
from utils.helpers import aplicar_maiuscula_formulario

class ProdutoDialog(QDialog):
    """Dialog para cadastro/edição de produtos"""

    def __init__(self, produto=None, parent=None):
        super().__init__(parent)
        self.produto = produto or Produto()
        self.fornecedor_nome = ""
        self.produto_original = None  # Para armazenar dados do produto original
        self.ultimo_produto_salvo_id = None  # Para armazenar ID do último produto salvo no lote
        self.campos_navegacao = []  # Lista de campos para navegação com Tab/Enter
        self._init_ui()

        aplicar_maiuscula_formulario(self)
        self._configurar_navegacao()

    def _init_ui(self):
        """Inicializa interface otimizada"""
        self.setWindowTitle("Cadastro de Produto")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Informações básicas
        self._criar_grupo_info(layout)

        # Valores e estoque
        self._criar_grupo_valores(layout)

        # Fornecedor
        self._criar_grupo_fornecedor(layout)

        # Status e opções
        self._criar_status_e_opcoes(layout)

        # Botões
        self._criar_botoes(layout)

        self.setLayout(layout)

    def _criar_grupo_info(self, layout):
        """Cria grupo de informações básicas"""
        grupo_info = QGroupBox("Informações do Produto")
        grupo_info.setProperty("class", "clean-group")

        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        # Nome
        info_layout.addWidget(QLabel("Nome*:"))
        self.nome_edit = SelectAllLineEdit(self.produto.nome)
        self.nome_edit.setPlaceholderText("Nome completo do produto")
        self.nome_edit.setMinimumHeight(35)
        self.campos_navegacao.append(self.nome_edit)
        info_layout.addWidget(self.nome_edit)

        # Layout horizontal para campos menores
        row1_layout = QHBoxLayout()

        # Tamanho
        tamanho_layout = QVBoxLayout()
        tamanho_layout.addWidget(QLabel("Tamanho*:"))
        self.tamanho_edit = SelectAllLineEdit(self.produto.tamanho or "")
        self.tamanho_edit.setPlaceholderText("P, M, G, Unico, etc.")
        self.tamanho_edit.setMinimumHeight(35)
        self.campos_navegacao.append(self.tamanho_edit)
        tamanho_layout.addWidget(self.tamanho_edit)

        # Cor
        cor_layout = QVBoxLayout()
        cor_layout.addWidget(QLabel("Cor*:"))
        self.cor_edit = SelectAllLineEdit(self.produto.cor or "")
        self.cor_edit.setPlaceholderText("Azul, Verde, etc.")
        self.cor_edit.setMinimumHeight(35)
        self.campos_navegacao.append(self.cor_edit)
        cor_layout.addWidget(self.cor_edit)

        row1_layout.addLayout(tamanho_layout)
        row1_layout.addLayout(cor_layout)
        info_layout.addLayout(row1_layout)

        # Layout horizontal para segunda linha
        row2_layout = QHBoxLayout()

        # EA
        ea_layout = QVBoxLayout()
        ea_layout.addWidget(QLabel("EAN:"))
        self.ea_edit = SelectAllLineEdit(self.produto.ea or "")
        self.ea_edit.setPlaceholderText("Código EAN de 13 dígitos")
        self.ea_edit.setMinimumHeight(35)
        self.campos_navegacao.append(self.ea_edit)
        ea_layout.addWidget(self.ea_edit)

        # Referência
        ref_layout = QVBoxLayout()
        ref_layout.addWidget(QLabel("Referência:"))
        self.referencia_edit = SelectAllLineEdit(self.produto.referencia or "")
        self.referencia_edit.setPlaceholderText("Código do fornecedor")
        self.referencia_edit.setMinimumHeight(35)
        self.campos_navegacao.append(self.referencia_edit)
        ref_layout.addWidget(self.referencia_edit)

        row2_layout.addLayout(ea_layout)
        row2_layout.addLayout(ref_layout)
        info_layout.addLayout(row2_layout)

        grupo_info.setLayout(info_layout)
        layout.addWidget(grupo_info)

    def _criar_grupo_valores(self, layout):
        """Cria grupo de valores e estoque"""
        grupo_valores = QGroupBox("Valores e Estoque")
        grupo_valores.setProperty("class", "clean-group")

        valores_layout = QVBoxLayout()
        valores_layout.setSpacing(6)

        # Preço custo
        valores_layout.addWidget(QLabel("Preço de Custo:"))
        self.preco_custo_spin = SelectAllDoubleSpinBox()
        self.preco_custo_spin.setMaximum(999999.99)
        self.preco_custo_spin.setValue(self.produto.preco_custo)
        self.preco_custo_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.preco_custo_spin.setMinimumHeight(35)
        self.campos_navegacao.append(self.preco_custo_spin)
        valores_layout.addWidget(self.preco_custo_spin)

        # Preço venda
        valores_layout.addWidget(QLabel("Preço de Venda:"))
        self.preco_venda_spin = SelectAllDoubleSpinBox()
        self.preco_venda_spin.setMaximum(999999.99)
        self.preco_venda_spin.setValue(self.produto.preco_venda)
        self.preco_venda_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.preco_venda_spin.setMinimumHeight(35)
        self.campos_navegacao.append(self.preco_venda_spin)
        valores_layout.addWidget(self.preco_venda_spin)

        # Estoque (apenas para edição)
        if self.produto.id is not None:
            valores_layout.addWidget(QLabel("Estoque:"))
            self.estoque_spin = SelectAllSpinBox()
            self.estoque_spin.setMaximum(999999)
            self.estoque_spin.setValue(self.produto.estoque)
            self.estoque_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            self.estoque_spin.setMinimumHeight(35)
            self.campos_navegacao.append(self.estoque_spin)
            valores_layout.addWidget(self.estoque_spin)

        grupo_valores.setLayout(valores_layout)
        layout.addWidget(grupo_valores)

    def _criar_grupo_fornecedor(self, layout):
        """Cria grupo de fornecedor"""
        grupo_fornecedor = QGroupBox("Fornecedor")
        grupo_fornecedor.setProperty("class", "clean-group")

        fornecedor_layout = QVBoxLayout()
        fornecedor_layout.setSpacing(6)

        fornecedor_inner_layout = QHBoxLayout()

        self.fornecedor_label = QLabel("Nenhum fornecedor selecionado")
        self.fornecedor_label.setFixedWidth(200)
        self.fornecedor_label.setWordWrap(False)
        self.fornecedor_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # Carregar fornecedor atual se existir
        if self.produto.fornecedor_id:
            fornecedor = Fornecedor.buscar_por_id(self.produto.fornecedor_id)
            if fornecedor:
                self.fornecedor_nome = fornecedor.nome
                self.fornecedor_label.setText(fornecedor.nome)

        self.btn_selecionar_fornecedor = QPushButton("Selecionar")
        self.btn_selecionar_fornecedor.setProperty("class", "secondary")
        self.btn_selecionar_fornecedor.clicked.connect(self._selecionar_fornecedor)

        fornecedor_inner_layout.addWidget(self.fornecedor_label)
        fornecedor_inner_layout.addStretch()
        fornecedor_inner_layout.addWidget(self.btn_selecionar_fornecedor)

        fornecedor_layout.addLayout(fornecedor_inner_layout)
        grupo_fornecedor.setLayout(fornecedor_layout)
        layout.addWidget(grupo_fornecedor)

    def _criar_status_e_opcoes(self, layout):
        """Cria checkboxes de status e opções"""
        opcoes_frame = QFrame()
        opcoes_layout = QVBoxLayout()
        opcoes_layout.setContentsMargins(0, 0, 0, 0)
        opcoes_layout.setSpacing(8)

        # Linha 1: Produto Ativo
        linha1_layout = QHBoxLayout()
        self.ativo_checkbox = QCheckBox("Produto Ativo")
        self.ativo_checkbox.setChecked(self.produto.ativo)
        linha1_layout.addWidget(self.ativo_checkbox)
        linha1_layout.addStretch()
        opcoes_layout.addLayout(linha1_layout)

        # Linha 2: Cadastro em Lote (apenas para novos produtos)
        if self.produto.id is None:
            linha2_layout = QHBoxLayout()
            self.cadastro_lote_checkbox = QCheckBox("Cadastro em lote")
            self.cadastro_lote_checkbox.setChecked(False)
            self.cadastro_lote_checkbox.setToolTip("Manter janela aberta após cadastrar, preservando todos os dados para facilitar cadastro de produtos similares")
            linha2_layout.addWidget(self.cadastro_lote_checkbox)
            linha2_layout.addStretch()
            opcoes_layout.addLayout(linha2_layout)

        opcoes_frame.setLayout(opcoes_layout)
        layout.addWidget(opcoes_frame)

    def _criar_botoes(self, layout):
        """Cria botões do dialog"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Salvar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._salvar_produto)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _configurar_navegacao(self):
        """Configura navegação entre campos com Enter"""
        # Conecta o evento returnPressed para cada campo
        for i, campo in enumerate(self.campos_navegacao):
            if isinstance(campo, QLineEdit):
                # Remove conexões existentes de returnPressed
                try:
                    campo.returnPressed.disconnect()
                except:
                    pass
                # Conecta para navegar para próximo campo
                campo.returnPressed.connect(lambda idx=i: self._navegar_para_proximo(idx))
            elif isinstance(campo, (QDoubleSpinBox, QSpinBox)):
                # Para spinboxes, precisamos sobrescrever keyPressEvent
                campo.keyPressEvent = self._criar_key_press_event_spinbox(campo, i)

    def _navegar_para_proximo(self, indice_atual):
        """Navega para o próximo campo na lista"""
        proximo_indice = indice_atual + 1
        
        if proximo_indice < len(self.campos_navegacao):
            proximo_campo = self.campos_navegacao[proximo_indice]
            proximo_campo.setFocus()
            if isinstance(proximo_campo, QLineEdit):
                proximo_campo.selectAll()
        else:
            # Se for o último campo, vai para o botão "Selecionar Fornecedor"
            self.btn_selecionar_fornecedor.setFocus()

    def _criar_key_press_event_spinbox(self, spinbox, indice):
        """Cria um keyPressEvent personalizado para spinboxes"""
        def keyPressEvent(event):
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self._navegar_para_proximo(indice)
                event.accept()
            else:
                # Chama o comportamento padrão
                super(type(spinbox), spinbox).keyPressEvent(event)
        
        return keyPressEvent

    def keyPressEvent(self, event):
        """Override do keyPressEvent para desabilitar Enter global"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Verifica se o foco está em algum widget que não seja os botões
            widget_focado = self.focusWidget()
            
            # Se o foco estiver nos botões do QDialogButtonBox, permite o Enter
            if isinstance(widget_focado, QPushButton):
                # Permite o comportamento padrão (acionar o botão)
                super().keyPressEvent(event)
            else:
                # Para outros widgets, apenas ignora o Enter
                # A navegação já é tratada nos próprios widgets
                event.ignore()
        else:
            super().keyPressEvent(event)

    def _selecionar_fornecedor(self):
        """Abre dialog para selecionar fornecedor"""
        dialog = FornecedorSelectionDialog(self)
        if dialog.exec():
            fornecedor = dialog.get_fornecedor_selecionado()
            if fornecedor:
                self.produto.fornecedor_id = fornecedor.id
                self.fornecedor_nome = fornecedor.nome
                self.fornecedor_label.setText(fornecedor.nome)

    def get_data(self):
        """Retorna dados do produto preenchidos"""
        self.produto.nome = self.nome_edit.text()
        self.produto.preco_custo = self.preco_custo_spin.value()
        self.produto.preco_venda = self.preco_venda_spin.value()
        self.produto.tamanho = self.tamanho_edit.text()
        self.produto.cor = self.cor_edit.text()
        self.produto.ea = self.ea_edit.text()
        self.produto.referencia = self.referencia_edit.text()

        # Estoque apenas em edição
        if hasattr(self, "estoque_spin"):
            self.produto.estoque = self.estoque_spin.value()

        self.produto.ativo = self.ativo_checkbox.isChecked()
        return self.produto

    def _preparar_proximo_produto(self):
        """Prepara os dados para o próximo produto no cadastro em lote"""
        try:
            # Busca o último produto salvo do banco de dados
            if self.ultimo_produto_salvo_id:
                produto_template = Produto.buscar_por_id(self.ultimo_produto_salvo_id)

                if produto_template:
                    # Cria um novo produto copiando TODOS os dados do último produto salvo
                    self.produto = Produto()
                    self.produto.nome = produto_template.nome
                    self.produto.preco_custo = produto_template.preco_custo
                    self.produto.preco_venda = produto_template.preco_venda
                    self.produto.tamanho = produto_template.tamanho
                    self.produto.cor = produto_template.cor
                    self.produto.ea = produto_template.ea
                    self.produto.referencia = produto_template.referencia
                    self.produto.fornecedor_id = produto_template.fornecedor_id
                    self.produto.ativo = produto_template.ativo
                    # Não copia o ID (para criar um novo produto) nem o estoque

                    # Atualiza todos os campos da interface com os dados do produto template
                    self.nome_edit.setText(produto_template.nome)
                    self.preco_custo_spin.setValue(produto_template.preco_custo)
                    self.preco_venda_spin.setValue(produto_template.preco_venda)
                    self.tamanho_edit.setText(produto_template.tamanho or "")
                    self.cor_edit.setText(produto_template.cor or "")
                    self.ea_edit.setText(produto_template.ea or "")
                    self.referencia_edit.setText(produto_template.referencia or "")
                    self.ativo_checkbox.setChecked(produto_template.ativo)

                    # Atualiza o fornecedor na interface
                    if produto_template.fornecedor_id:
                        fornecedor = Fornecedor.buscar_por_id(produto_template.fornecedor_id)
                        if fornecedor:
                            self.fornecedor_nome = fornecedor.nome
                            self.fornecedor_label.setText(fornecedor.nome)
                        else:
                            self.fornecedor_label.setText("Nenhum fornecedor selecionado")
                    else:
                        self.fornecedor_label.setText("Nenhum fornecedor selecionado")

                    # Coloca foco no nome e seleciona todo o texto para facilitar edição
                    self.nome_edit.setFocus()
                    self.nome_edit.selectAll()

                    return

            # Fallback: se não conseguiu buscar o produto, mantém os dados atuais
            self.nome_edit.setFocus()
            self.nome_edit.selectAll()

        except Exception as e:
            print(f"Erro ao preparar próximo produto: {e}")
            # Em caso de erro, apenas coloca foco no nome
            self.nome_edit.setFocus()
            self.nome_edit.selectAll()

    def _salvar_produto(self):
        """Salva o produto - chamado apenas pelo botão Salvar"""
        try:
            # Valida se o nome foi preenchido
            if not self.nome_edit.text().strip():
                QMessageBox.warning(self, "Erro", "O nome do produto é obrigatório!")
                self.nome_edit.setFocus()
                return
            
            # Valida se a cor foi preenchida
            if not self.cor_edit.text().strip():
                QMessageBox.warning(self, "Erro", "A cor do produto é obrigatória!")
                self.cor_edit.setFocus()
                return
            
            # Valida se o tamanho foi preenchido
            if not self.tamanho_edit.text().strip():
                QMessageBox.warning(self, "Erro", "O tamanho do produto é obrigatório!")
                self.tamanho_edit.setFocus()
                return

            # Obtém os dados do formulário
            produto_atualizado = self.get_data()

            # Salva no banco de dados
            produto_atualizado.salvar()

            # Verifica se é cadastro em lote E é um produto novo
            eh_novo_produto = self.produto.id is None or (hasattr(self, 'produto_original') and self.produto_original is None)
            eh_cadastro_lote = hasattr(self, 'cadastro_lote_checkbox') and self.cadastro_lote_checkbox.isChecked()

            if eh_novo_produto and eh_cadastro_lote:
                # Armazena o ID do produto recém-salvo para usar como template
                self.ultimo_produto_salvo_id = produto_atualizado.id

                # Mostra confirmação
                QMessageBox.information(
                    self,
                    "Produto Cadastrado",
                    f"Produto '{produto_atualizado.nome}' cadastrado com sucesso!\n\n"
                    "A janela permanecerá aberta com todos os dados mantidos para cadastrar o próximo produto."
                )

                # Prepara para o próximo produto
                self._preparar_proximo_produto()

                # Não fecha a janela - apenas retorna
                return
            else:
                # Comportamento normal - fecha a janela
                super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Erro ao salvar produto:\n{str(e)}")

    def reject(self):
        """Override do método reject para confirmar cancelamento se houver alterações"""
        # Verifica se está em modo de cadastro em lote e há dados preenchidos
        eh_cadastro_lote = hasattr(self, 'cadastro_lote_checkbox') and self.cadastro_lote_checkbox.isChecked()
        tem_dados = (self.nome_edit.text().strip() or
                    self.preco_custo_spin.value() > 0 or
                    self.preco_venda_spin.value() > 0)

        if eh_cadastro_lote and tem_dados:
            resposta = QMessageBox.question(
                self,
                "Confirmar Cancelamento",
                "Você está no modo de cadastro em lote e há dados preenchidos.\n"
                "Deseja realmente cancelar e fechar a janela?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if resposta == QMessageBox.StandardButton.No:
                return

        super().reject()

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def selecionar_fornecedor(self):
        """Método público para compatibilidade"""
        self._selecionar_fornecedor()