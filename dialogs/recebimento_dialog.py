"""
Dialog de Recebimento - Otimizado para novo sistema de estilos
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QMessageBox, QGroupBox,
                             QDialogButtonBox,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt
from datetime import datetime

from models.cliente import Cliente
from utils.helpers import SelectAllDoubleSpinBox, SelectAllLineEdit
from utils.helpers import formatar_moeda, formatar_data, validar_data
from utils.helpers import aplicar_maiuscula_formulario

class RecebimentoDialog(QDialog):
    """Dialog para recebimento de duplicatas"""

    def __init__(self, duplicata, parent=None):
        super().__init__(parent)
        self.duplicata = duplicata
        self.valor_original = float(duplicata[4])
        self._init_ui()

        aplicar_maiuscula_formulario(self)

    def _init_ui(self):
        """Inicializa interface com classes CSS"""
        self.setWindowTitle("Receber Duplicata")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Informações da duplicata
        self._criar_info_duplicata(layout)

        # Dados do recebimento
        self._criar_dados_recebimento(layout)

        # Botões
        self._criar_botoes(layout)

        self.setLayout(layout)

    def _criar_info_duplicata(self, layout):
        """Cria seção de informações"""
        info_group = QGroupBox("Informações da Duplicata")
        info_group.setProperty("class", "clean-group")

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(8, 12, 8, 12)

        # Labels de informação
        info_items = [
            f"Cliente: {self._get_nome_cliente()}",
            f"Parcela: {self.duplicata[3]}",
            f"Vencimento: {formatar_data(self.duplicata[5])}",
            f"Valor Original: {formatar_moeda(self.valor_original)}"
        ]

        for item in info_items:
            label = QLabel(item)
            info_layout.addWidget(label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def _criar_dados_recebimento(self, layout):
        """Cria seção de dados do recebimento"""
        valor_group = QGroupBox("Recebimento")
        valor_group.setProperty("class", "clean-group")

        valor_layout = QVBoxLayout()
        valor_layout.setContentsMargins(8, 12, 8, 12)

        # Valor recebido
        valor_layout.addWidget(QLabel("Valor Recebido:"))
        self.valor_recebido_input = SelectAllDoubleSpinBox()
        self.valor_recebido_input.setMaximum(999999.99)
        self.valor_recebido_input.setValue(self.valor_original)
        self.valor_recebido_input.setDecimals(2)
        self.valor_recebido_input.valueChanged.connect(self._verificar_diferenca_valor)
        valor_layout.addWidget(self.valor_recebido_input)

        # Label para mostrar diferença
        self.diferenca_label = QLabel("")
        self.diferenca_label.setProperty("class", "info-label")
        self.diferenca_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.diferenca_label.setVisible(False)
        valor_layout.addWidget(self.diferenca_label)

        # Data recebimento
        valor_layout.addWidget(QLabel("Data do Recebimento:"))
        self.data_recebimento = SelectAllLineEdit()
        self.data_recebimento.setPlaceholderText("DD/MM/AAAA")
        self.data_recebimento.setText(datetime.now().strftime("%d/%m/%Y"))
        self.data_recebimento.textChanged.connect(self._validar_data_input)
        valor_layout.addWidget(self.data_recebimento)

        # Forma de pagamento
        self._criar_forma_pagamento(valor_layout)

        valor_group.setLayout(valor_layout)
        layout.addWidget(valor_group)

    def _verificar_diferenca_valor(self):
        """Verifica e exibe diferença entre valor recebido e original"""
        valor_recebido = self.valor_recebido_input.value()
        diferenca = valor_recebido - self.valor_original
        
        # Limpar label se não houver diferença
        if abs(diferenca) < 0.01:  # Considera diferença menor que 1 centavo
            self.diferenca_label.setVisible(False)
            self.diferenca_label.setText("")
            return
        
        # Mostrar diferença
        self.diferenca_label.setVisible(True)
        
        if diferenca > 0:
            texto = f"Valor maior em: {formatar_moeda(diferenca)}"
            cor = "green"
        else:
            texto = f"Valor menor em: {formatar_moeda(abs(diferenca))}"
            cor = "red"
        
        self.diferenca_label.setText(texto)
        self.diferenca_label.setStyleSheet(f"color: {cor}; font-weight: bold;")

    def _criar_forma_pagamento(self, layout):
        """Cria seção de forma de pagamento"""
        layout.addWidget(QLabel("Forma de Pagamento:"))

        self.forma_pagamento_group = QButtonGroup(self)
        self.rb_dinheiro = QRadioButton("Dinheiro")
        self.rb_pix = QRadioButton("Pix")
        self.rb_cartao = QRadioButton("Cartão")

        # Configurar group
        for rb in [self.rb_dinheiro, self.rb_pix, self.rb_cartao]:
            self.forma_pagamento_group.addButton(rb)

        self.rb_dinheiro.setChecked(True)

        # Layout horizontal
        forma_layout = QHBoxLayout()
        forma_layout.addWidget(self.rb_dinheiro)
        forma_layout.addWidget(self.rb_pix)
        forma_layout.addWidget(self.rb_cartao)
        forma_layout.addStretch()

        layout.addLayout(forma_layout)

    def _criar_botoes(self, layout):
        """Cria botões do dialog"""
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._verificar_e_aceitar)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def _validar_data_input(self):
        """Valida data em tempo real"""
        data_texto = self.data_recebimento.text().strip()
        if data_texto and not validar_data(data_texto):
            self._marcar_campo_erro(self.data_recebimento)
        else:
            self._limpar_campo_erro(self.data_recebimento)

    def _marcar_campo_erro(self, campo):
        """Marca campo com erro"""
        campo.setProperty("class", "error")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_campo_erro(self, campo):
        """Remove erro do campo"""
        campo.setProperty("class", "")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _verificar_e_aceitar(self):
        """Valida dados antes de aceitar"""
        data_texto = self.data_recebimento.text().strip()

        if not data_texto:
            QMessageBox.warning(self, "Aviso", "Informe a data de recebimento.")
            return

        if not validar_data(data_texto):
            QMessageBox.warning(self, "Aviso", "Data inválida. Use DD/MM/AAAA.")
            return

        valor_recebido = self.valor_recebido_input.value()
        
        if valor_recebido <= 0:
            QMessageBox.warning(self, "Aviso", "Valor deve ser maior que zero.")
            return

        # Verificar se há diferença significativa
        diferenca = abs(valor_recebido - self.valor_original)
        
        if diferenca > 0.01:  # Se diferença maior que 1 centavo
            confirmado = self._mostrar_aviso_diferenca(valor_recebido)
            
            if not confirmado:
                return  # Usuário cancelou

        self.accept()

    def _mostrar_aviso_diferenca(self, valor_recebido):
        """Mostra aviso sobre diferença de valor"""
        diferenca = valor_recebido - self.valor_original
        
        # Determinar o tipo de diferença
        if diferenca > 0:
            tipo = "maior"
            acao = "reduzidos"
            simbolo = "+"
        else:
            tipo = "menor"
            acao = "aumentados"
            simbolo = "-"
        
        # Título único
        titulo_janela = "Valor Divergente"
        
        # Mensagem formatada com quebras explícitas
        mensagem = f"""<b>Valor {tipo.capitalize()} que o original</b><br><br>

    <code>Valor original:  {formatar_moeda(self.valor_original)}</code><br>
    <code>Valor recebido: {formatar_moeda(valor_recebido)}</code><br>
    <code>Diferença:      {simbolo}{formatar_moeda(abs(diferenca))}</code><br><br>

    As próximas parcelas terão seus valores {acao}<br>
    proporcionalmente para compensar esta diferença.<br><br>

    Deseja continuar com o recebimento?"""
        
        # Criar message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo_janela)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensagem)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Botões
        btn_confirmar = msg_box.addButton("Confirmar", QMessageBox.ButtonRole.YesRole)
        btn_confirmar.setProperty("class", "primary-button")
        
        btn_corrigir = msg_box.addButton("Corrigir", QMessageBox.ButtonRole.NoRole)
        btn_corrigir.setProperty("class", "secondary-button")
        
        # Definir botão padrão
        msg_box.setDefaultButton(btn_corrigir)
        
        # Executar message box
        msg_box.exec()
        
        # Verificar qual botão foi pressionado
        botao_pressionado = msg_box.clickedButton()
        
        # Retornar True se o usuário clicou em "Confirmar"
        return botao_pressionado == btn_confirmar

    def _get_nome_cliente(self):
        """Obtém nome do cliente - MÉTODO CORRIGIDO"""
        try:
            # Verificar se é duplicata paga (15 campos) ou aberta (9 campos)
            is_paga = len(self.duplicata) == 15

            if is_paga:
                # Para duplicatas pagas, o cliente_id está no índice 1
                # e o nome do cliente já vem no índice 9
                cliente_id = self.duplicata[1]
                cliente_nome = self.duplicata[9]  # Nome já vem da query

                # Se o nome já está disponível, usar diretamente
                if cliente_nome:
                    return cliente_nome
                else:
                    # Fallback: buscar pelo ID
                    cliente = Cliente.buscar_por_id(cliente_id)
                    return cliente.nome if cliente else "Cliente não encontrado"
            else:
                # Para duplicatas abertas, o cliente_id está no índice 1
                # e o nome do cliente vem no índice 8
                cliente_id = self.duplicata[1]

                # Verificar se o nome já vem na estrutura
                if len(self.duplicata) > 8 and self.duplicata[8]:
                    return self.duplicata[8]
                else:
                    # Fallback: buscar pelo ID
                    cliente = Cliente.buscar_por_id(cliente_id)
                    return cliente.nome if cliente else "Cliente não encontrado"

        except Exception as e:
            print(f"Erro ao obter nome do cliente: {e}")
            print(f"Estrutura da duplicata: {self.duplicata}")
            return "Cliente não encontrado"

    def get_dados(self):
        """Retorna dados do recebimento"""
        data_texto = self.data_recebimento.text().strip()
        data_recebimento = datetime.strptime(data_texto, "%d/%m/%Y").date()

        if self.rb_dinheiro.isChecked():
            forma = "Dinheiro"
        elif self.rb_pix.isChecked():
            forma = "Pix"
        else:
            forma = "Cartão"

        return (
            self.valor_recebido_input.value(),
            data_recebimento,
            forma
        )

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def validar_data_input(self):
        """Método público para compatibilidade"""
        self._validar_data_input()

    def verificar_e_aceitar(self):
        """Método público para compatibilidade"""
        self._verificar_e_aceitar()

    def get_nome_cliente(self):
        """Método público para compatibilidade"""
        return self._get_nome_cliente()