"""
Dialog de Pagamento - Versão Simplificada com Entrada
"""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from mainerp.domain.utils.helpers import SelectAllDoubleSpinBox, formatar_moeda


class PagamentoDialog(QDialog):
    """Dialog para seleção de forma de pagamento com suporte a entrada"""

    def __init__(self, valor_total, cliente_id, parent=None):
        super().__init__(parent)
        self.valor_total = float(valor_total)
        self.cliente_id = cliente_id
        self.valor_entrada = 0.0
        self._init_ui()

    def _init_ui(self):
        """Inicializa interface do dialog"""
        self.setWindowTitle("Forma de Pagamento")
        self.setMinimumSize(400, 200)  # Tamanho inicial menor

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Valor total
        valor_label = QLabel(f"Valor Total: {formatar_moeda(self.valor_total)}")
        valor_label.setProperty("class", "title")
        valor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(valor_label)

        # Forma de pagamento - MUDANÇA AQUI: Layout horizontal
        pagamento_group = QGroupBox("Forma de Pagamento")
        pagamento_layout = QHBoxLayout()  # Mudado de QVBoxLayout para QHBoxLayout

        self.forma_group = QButtonGroup(self)
        self.rb_dinheiro = QRadioButton("Dinheiro")
        self.rb_pix = QRadioButton("Pix")
        self.rb_cartao = QRadioButton("Cartão")
        self.rb_crediario = QRadioButton("Crediário")

        for rb in [self.rb_dinheiro, self.rb_pix, self.rb_cartao, self.rb_crediario]:
            self.forma_group.addButton(rb)
            pagamento_layout.addWidget(rb)

        self.rb_dinheiro.setChecked(True)
        pagamento_group.setLayout(pagamento_layout)
        layout.addWidget(pagamento_group)

        # Valor de entrada (só aparece no crediário)
        self.entrada_group = QGroupBox("Valor de Entrada")
        entrada_layout = QVBoxLayout()

        entrada_layout.addWidget(QLabel("Valor de entrada (opcional):"))

        entrada_h_layout = QHBoxLayout()
        self.entrada_input = SelectAllDoubleSpinBox()
        self.entrada_input.setMaximum(self.valor_total)
        self.entrada_input.setMinimum(0.0)
        self.entrada_input.setValue(0.0)
        self.entrada_input.setDecimals(2)
        entrada_h_layout.addWidget(self.entrada_input)

        # Botões rápidos
        for perc in [20, 30, 50]:
            btn = QPushButton(f"{perc}%")
            btn.clicked.connect(lambda checked, p=perc: self._aplicar_percentual(p))
            entrada_h_layout.addWidget(btn)

        entrada_layout.addLayout(entrada_h_layout)

        self.label_financiado = QLabel("Valor a financiar: R$ 0,00")
        self.label_financiado.setStyleSheet("color: #27ae60; font-weight: bold;")
        entrada_layout.addWidget(self.label_financiado)

        self.entrada_group.setLayout(entrada_layout)
        layout.addWidget(self.entrada_group)

        # Parcelas (só aparece no crediário)
        self.parcelas_group = QGroupBox("Parcelamento")
        parcelas_layout = QVBoxLayout()

        parcelas_h_layout = QHBoxLayout()
        parcelas_h_layout.addWidget(QLabel("Número de parcelas:"))

        self.parcelas_spinner = QSpinBox()
        self.parcelas_spinner.setMinimum(1)
        self.parcelas_spinner.setMaximum(24)
        self.parcelas_spinner.setValue(1)
        self.parcelas_spinner.setMaximumWidth(80)  # Metade do tamanho
        parcelas_h_layout.addWidget(self.parcelas_spinner)
        parcelas_h_layout.addStretch()

        parcelas_layout.addLayout(parcelas_h_layout)

        self.label_valor_parcela = QLabel("Valor da parcela: R$ 0,00")
        self.label_valor_parcela.setStyleSheet("color: #3498db; font-weight: bold;")
        parcelas_layout.addWidget(self.label_valor_parcela)

        self.parcelas_group.setLayout(parcelas_layout)
        layout.addWidget(self.parcelas_group)

        # Data vencimento (só aparece no crediário) - CAMPO NA MESMA LINHA
        self.vencimento_group = QGroupBox("Primeiro Vencimento")
        vencimento_layout = QVBoxLayout()

        # Layout horizontal para colocar label e campo na mesma linha
        vencimento_h_layout = QHBoxLayout()
        vencimento_h_layout.addWidget(QLabel("Data do primeiro vencimento:"))

        self.data_vencimento = QLineEdit()
        self.data_vencimento.setPlaceholderText("DD/MM/AAAA")
        self.data_vencimento.setMaximumWidth(120)  # Metade do tamanho

        # Calcular data padrão (hoje + 30 dias)
        data_padrao = datetime.now() + timedelta(days=30)
        self.data_vencimento.setText(data_padrao.strftime("%d/%m/%Y"))

        vencimento_h_layout.addWidget(self.data_vencimento)
        vencimento_h_layout.addStretch()  # Adiciona espaço à direita
        vencimento_layout.addLayout(vencimento_h_layout)

        self.vencimento_group.setLayout(vencimento_layout)
        layout.addWidget(self.vencimento_group)

        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validar_e_aceitar)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # CONECTAR EVENTOS DEPOIS DE CRIAR TUDO
        for rb in [self.rb_dinheiro, self.rb_pix, self.rb_cartao, self.rb_crediario]:
            rb.toggled.connect(self._atualizar_campos)

        self.entrada_input.valueChanged.connect(self._calcular_financiado)
        self.parcelas_spinner.valueChanged.connect(self._calcular_parcela)

        # AGORA SIM PODE CHAMAR O MÉTODO
        self._atualizar_campos()

        # Centralizar a janela ao abrir
        self._centralizar_janela()

    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        parent = self.parentWidget()
        if parent is not None:
            # Se tem parent, centraliza em relação ao parent
            parent_geometry = parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Se não tem parent, centraliza na tela
            primary_screen = QGuiApplication.primaryScreen()
            if primary_screen is None:
                raise RuntimeError("Não foi possível localizar a tela principal.")
            screen = primary_screen.geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def _atualizar_campos(self):
        """Mostra/oculta campos baseado na forma de pagamento"""
        is_crediario = self.rb_crediario.isChecked()

        # Verificar se os grupos existem antes de tentar modificá-los
        if hasattr(self, "entrada_group"):
            self.entrada_group.setVisible(is_crediario)
        if hasattr(self, "parcelas_group"):
            self.parcelas_group.setVisible(is_crediario)
        if hasattr(self, "vencimento_group"):
            self.vencimento_group.setVisible(is_crediario)

        if not is_crediario:
            self.valor_entrada = 0.0

        # Redimensionar a janela automaticamente após mostrar/ocultar campos
        self.adjustSize()

        # Definir tamanho mínimo baseado no modo
        if is_crediario:
            self.setMinimumSize(400, 500)  # Maior para acomodar todos os campos
        else:
            self.setMinimumSize(400, 200)  # Menor para apenas os campos básicos

        # Recentralizar a janela após redimensionar
        self._centralizar_janela()

        self._calcular_financiado()

    def _aplicar_percentual(self, percentual):
        """Aplica percentual do valor total como entrada"""
        valor = (self.valor_total * percentual) / 100
        self.entrada_input.setValue(valor)

    def _calcular_financiado(self):
        """Calcula valor financiado"""
        if hasattr(self, "entrada_input"):
            self.valor_entrada = self.entrada_input.value()

        valor_financiado = self.valor_total - self.valor_entrada

        if hasattr(self, "label_financiado"):
            self.label_financiado.setText(
                f"Valor a financiar: {formatar_moeda(valor_financiado)}"
            )

        self._calcular_parcela()

    def _calcular_parcela(self):
        """Calcula valor da parcela"""
        if not hasattr(self, "label_valor_parcela") or not hasattr(
            self, "rb_crediario"
        ):
            return

        if self.rb_crediario.isChecked():
            valor_financiado = self.valor_total - self.valor_entrada
            if (
                valor_financiado > 0
                and hasattr(self, "parcelas_spinner")
                and self.parcelas_spinner.value() > 0
            ):
                valor_parcela = valor_financiado / self.parcelas_spinner.value()
                self.label_valor_parcela.setText(
                    f"Valor da parcela: {formatar_moeda(valor_parcela)}"
                )
            else:
                self.label_valor_parcela.setText("Valor da parcela: R$ 0,00")
        else:
            self.label_valor_parcela.setText("Valor da parcela: R$ 0,00")

    def _validar_data(self, data_str):
        """Valida se a data está no formato correto"""
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def _validar_e_aceitar(self):
        """Valida dados antes de aceitar"""
        if self.rb_crediario.isChecked():
            if self.valor_entrada >= self.valor_total:
                QMessageBox.warning(
                    self, "Erro", "Valor de entrada deve ser menor que o total."
                )
                return

            valor_financiado = self.valor_total - self.valor_entrada
            if valor_financiado <= 0:
                QMessageBox.warning(
                    self, "Erro", "Valor financiado deve ser maior que zero."
                )
                return

            # Validar formato da data
            data_texto = self.data_vencimento.text().strip()
            if not self._validar_data(data_texto):
                QMessageBox.warning(
                    self, "Erro", "Data deve estar no formato DD/MM/AAAA."
                )
                return

        self.accept()

    def get_dados(self):
        """Retorna dados do pagamento - COMPATÍVEL COM CÓDIGO ORIGINAL"""
        if self.rb_dinheiro.isChecked():
            forma = "Dinheiro"
        elif self.rb_pix.isChecked():
            forma = "Pix"
        elif self.rb_cartao.isChecked():
            forma = "Cartão"
        else:
            forma = "Crediario"

        parcelas = self.parcelas_spinner.value() if self.rb_crediario.isChecked() else 1

        # MODIFICADO: Converter string de data para objeto date
        data_vencimento = None
        if self.rb_crediario.isChecked():
            data_texto = self.data_vencimento.text().strip()
            try:
                data_vencimento = datetime.strptime(data_texto, "%d/%m/%Y").date()
            except ValueError:
                # Se houver erro na conversão, usar data padrão
                data_vencimento = (datetime.now() + timedelta(days=30)).date()

        valor_financiado = self.valor_total - self.valor_entrada

        # Retorna no formato esperado pelo código original
        return {
            "forma_pagamento": forma,
            "parcelas": parcelas,
            "data_primeiro_vencimento": data_vencimento,
            "valor_entrada": self.valor_entrada,
            "valor_financiado": valor_financiado,
        }
