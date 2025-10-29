# \erp\dialogs\frete_desconto_dialog.py - VERSÃO MELHORADA
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from utils.helpers import SelectAllDoubleSpinBox, formatar_moeda

# ✅ IMPORTAR MIXIN DE DIMENSIONAMENTO
from mixins.dialog_size_mixin import DialogSizeMixin


class FreteDescontoDialog(DialogSizeMixin, QDialog):
    """Dialog para definir frete e desconto do pedido"""

    def __init__(self, frete_atual=0.0, desconto_atual=0.0, subtotal_produtos=0.0, parent=None):
        super().__init__(parent)
        self.frete_atual = frete_atual
        self.desconto_atual = desconto_atual
        self.subtotal_produtos = subtotal_produtos
        self._init_ui()
        
        # ✅ CONFIGURAR TAMANHO COMPACTO (é um diálogo pequeno)
        self.setup_dialog_size_compact()
        
        self._conectar_sinais()
        self._configurar_atalhos()
        self._calcular_total()

    def _init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Frete e Desconto")
        self.setModal(True)
        # ❌ REMOVER setFixedSize - deixar o mixin controlar

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Grupo de informações
        self._criar_grupo_info(layout)

        # Grupo de valores
        self._criar_grupo_valores(layout)

        # Grupo do total
        self._criar_grupo_total(layout)

        # Botões
        self._criar_botoes(layout)

        self.setLayout(layout)

        # Focar no campo frete
        self.spin_frete.setFocus()
        self.spin_frete.selectAll()

    def _criar_grupo_info(self, layout):
        """Cria grupo com informações"""
        grupo_info = QGroupBox("Informações do Pedido")
        form_layout = QFormLayout()

        # Subtotal dos produtos
        self.label_subtotal = QLabel(formatar_moeda(self.subtotal_produtos))
        self.label_subtotal.setProperty("class", "valor-destaque")
        form_layout.addRow("Subtotal dos Produtos:", self.label_subtotal)

        grupo_info.setLayout(form_layout)
        layout.addWidget(grupo_info)

    def _criar_grupo_valores(self, layout):
        """Cria grupo para inserção de valores"""
        grupo_valores = QGroupBox("Frete e Desconto")
        form_layout = QFormLayout()

        # Frete
        self.spin_frete = SelectAllDoubleSpinBox()
        self.spin_frete.setDecimals(2)
        self.spin_frete.setMinimum(0.0)
        self.spin_frete.setMaximum(999999.99)
        self.spin_frete.setValue(self.frete_atual)
        self.spin_frete.setToolTip("Digite o valor do frete (F1)")
        form_layout.addRow("Frete:", self.spin_frete)

        # Desconto
        self.spin_desconto = SelectAllDoubleSpinBox()
        self.spin_desconto.setDecimals(2)
        self.spin_desconto.setMinimum(0.0)
        self.spin_desconto.setMaximum(999999.99)
        self.spin_desconto.setValue(self.desconto_atual)
        self.spin_desconto.setToolTip("Digite o valor do desconto (F2)")
        form_layout.addRow("Desconto:", self.spin_desconto)

        grupo_valores.setLayout(form_layout)
        layout.addWidget(grupo_valores)

    def _criar_grupo_total(self, layout):
        """Cria grupo do total"""
        grupo_total = QGroupBox("Total do Pedido")
        form_layout = QFormLayout()

        # Fórmula
        formula_label = QLabel("Subtotal - Desconto + Frete")
        formula_label.setProperty("class", "muted")
        form_layout.addRow("Cálculo:", formula_label)

        # Total final
        self.label_total_final = QLabel("R$ 0,00")
        self.label_total_final.setProperty("class", "valor-total")
        form_layout.addRow("Total Final:", self.label_total_final)

        grupo_total.setLayout(form_layout)
        layout.addWidget(grupo_total)

    def _criar_botoes(self, layout):
        """Cria botões de ação"""
        buttons_layout = QHBoxLayout()

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.setProperty("class", "success")
        btn_confirmar.clicked.connect(self.accept)
        btn_confirmar.setDefault(True)
        buttons_layout.addWidget(btn_confirmar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "danger")
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setAutoDefault(False)
        buttons_layout.addWidget(btn_cancelar)

        layout.addLayout(buttons_layout)

    def _conectar_sinais(self):
        """Conecta sinais para atualização automática"""
        self.spin_frete.valueChanged.connect(self._calcular_total)
        self.spin_desconto.valueChanged.connect(self._calcular_total)

    def _configurar_atalhos(self):
        """Configura atalhos de teclado"""
        # F1 - Focar no frete
        shortcut_f1 = QShortcut(QKeySequence("F1"), self)
        shortcut_f1.activated.connect(lambda: self._focar_campo(self.spin_frete))

        # F2 - Focar no desconto
        shortcut_f2 = QShortcut(QKeySequence("F2"), self)
        shortcut_f2.activated.connect(lambda: self._focar_campo(self.spin_desconto))

        # Enter - Confirmar
        shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut_enter.activated.connect(self.accept)

        # Escape - Cancelar
        shortcut_escape = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut_escape.activated.connect(self.reject)

    def _focar_campo(self, campo):
        """Foca em um campo específico"""
        campo.setFocus()
        campo.selectAll()

    def _calcular_total(self):
        """Calcula e exibe o total final"""
        frete = self.spin_frete.value()
        desconto = self.spin_desconto.value()

        # Fórmula: Subtotal - Desconto + Frete
        total_final = self.subtotal_produtos - desconto + frete

        # Garantir que o total não seja negativo
        total_final = max(0, total_final)

        self.label_total_final.setText(formatar_moeda(total_final))

    def get_frete(self):
        """Retorna o valor do frete"""
        return self.spin_frete.value()

    def get_desconto(self):
        """Retorna o valor do desconto"""
        return self.spin_desconto.value()

    def get_total_final(self):
        """Retorna o total final calculado"""
        frete = self.get_frete()
        desconto = self.get_desconto()
        total = self.subtotal_produtos - desconto + frete
        return max(0, total)