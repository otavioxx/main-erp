"""Diálogo para seleção da forma de pagamento."""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import SelectAllDoubleSpinBox, formatar_moeda
from mainerp.domain.utils.venda_utils import VendaCalculator
from mainerp.ui.theme_tokens import DIMENSOES


class _EntradaManual(SelectAllDoubleSpinBox):
    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        return QAbstractSpinBox.StepEnabledFlag.StepNone


class _EditorEntrada(QLineEdit):
    def __init__(self, campo: SelectAllDoubleSpinBox):
        super().__init__(campo)
        self._campo = campo

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        super().mousePressEvent(event)
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self._campo.selectAll()


class PagamentoDialog(QDialog):
    """Dialog para seleção de forma de pagamento."""

    def __init__(self, valor_total, cliente_id, parent=None):
        super().__init__(parent)
        self.valor_total = float(de_centavos(para_centavos(valor_total)))
        self.cliente_id = cliente_id
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

        self.entrada_group = QGroupBox("Valor de Entrada")
        entrada_layout = QVBoxLayout(self.entrada_group)
        self.entrada_input = _EntradaManual()
        editor_entrada = _EditorEntrada(self.entrada_input)
        self.entrada_input.setLineEdit(editor_entrada)
        self.entrada_input.setDecimals(2)
        self.entrada_input.setRange(0, max(0, self.valor_total))
        self.entrada_input.setPrefix("R$ ")
        editor_entrada.setTextMargins(
            DIMENSOES.espacamento, 0, DIMENSOES.espacamento, 0
        )
        entrada_layout.addWidget(self.entrada_input)
        self.label_financiado = QLabel()
        entrada_layout.addWidget(self.label_financiado)
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
        editor = self.parcelas_spinner.findChild(QLineEdit)
        if editor is None:
            raise RuntimeError("Campo numérico de parcelas sem editor de texto.")
        editor.setTextMargins(DIMENSOES.espacamento, 0, DIMENSOES.espacamento, 0)
        parcelas_h_layout.addWidget(self.parcelas_spinner)
        parcelas_h_layout.addStretch()

        parcelas_layout.addLayout(parcelas_h_layout)

        self.label_valor_parcela = QLabel("Valor da parcela: R$ 0,00")
        self.label_valor_parcela.setProperty("estadoVisual", "acento")
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

        self.parcelas_spinner.valueChanged.connect(self._calcular_parcela)
        self.entrada_input.valueChanged.connect(self._calcular_parcela)

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

        self.entrada_group.setVisible(is_crediario)
        # Verificar se os grupos existem antes de tentar modificá-los
        if hasattr(self, "parcelas_group"):
            self.parcelas_group.setVisible(is_crediario)
        if hasattr(self, "vencimento_group"):
            self.vencimento_group.setVisible(is_crediario)

        # Redimensionar a janela automaticamente após mostrar/ocultar campos
        self.adjustSize()

        # Recentralizar a janela após redimensionar
        self._centralizar_janela()

        self._calcular_parcela()

    def _calcular_parcela(self):
        """Calcula valor da parcela"""
        if not hasattr(self, "label_valor_parcela") or not hasattr(
            self, "rb_crediario"
        ):
            return

        if self.rb_crediario.isChecked():
            valor_financiado_centavos = para_centavos(self.valor_total) - para_centavos(
                self.entrada_input.value()
            )
            self.label_financiado.setText(
                f"Valor financiado: {formatar_moeda(float(de_centavos(valor_financiado_centavos)))}"
            )
            if (
                valor_financiado_centavos > 0
                and hasattr(self, "parcelas_spinner")
                and self.parcelas_spinner.value() > 0
            ):
                parcelas = self.parcelas_spinner.value()
                valor_parcela_centavos = valor_financiado_centavos // parcelas
                valor_parcela = float(de_centavos(valor_parcela_centavos))
                texto = f"Valor da parcela: {formatar_moeda(valor_parcela)}"
                ultima = valor_financiado_centavos - valor_parcela_centavos * (
                    parcelas - 1
                )
                if ultima != valor_parcela_centavos:
                    texto += f" (última: {formatar_moeda(float(de_centavos(ultima)))})"
                self.label_valor_parcela.setText(texto)
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
            try:
                financiado = VendaCalculator.calcular_financiado_centavos(
                    para_centavos(self.valor_total),
                    para_centavos(self.entrada_input.value()),
                )
            except ValueError as erro:
                QMessageBox.warning(self, "Erro", str(erro))
                return

            if (
                self.entrada_input.value() > 0
                and financiado < self.parcelas_spinner.value()
            ):
                QMessageBox.warning(
                    self,
                    "Erro",
                    "O valor financiado deve permitir parcelas de pelo menos R$ 0,01.",
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

        entrada_centavos = (
            para_centavos(self.entrada_input.value())
            if self.rb_crediario.isChecked()
            else 0
        )
        valor_financiado = (
            float(
                de_centavos(
                    VendaCalculator.calcular_financiado_centavos(
                        para_centavos(self.valor_total), entrada_centavos
                    )
                )
            )
            if self.rb_crediario.isChecked()
            else self.valor_total
        )

        # Retorna no formato esperado pelo código original
        return {
            "forma_pagamento": forma,
            "parcelas": parcelas,
            "data_primeiro_vencimento": data_vencimento,
            "valor_entrada": float(de_centavos(entrada_centavos)),
            "valor_financiado": valor_financiado,
        }
