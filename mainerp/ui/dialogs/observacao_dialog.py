"""
Dialog para inserção de observações na venda
"""

from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from mainerp.domain.utils.helpers import aplicar_maiuscula_formulario


class ObservacaoDialog(QDialog):
    """Dialog para inserir observações na venda"""

    def __init__(self, observacao_atual="", parent=None):
        super().__init__(parent)
        self.observacao = observacao_atual
        self._init_ui()
        aplicar_maiuscula_formulario(self)

    def _init_ui(self):
        """Inicializa interface"""
        self.setWindowTitle("Observação da Venda")
        self.setMinimumSize(400, 250)
        self.resize(500, 300)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Título
        titulo = QLabel("Observação da Venda")
        titulo.setProperty("class", "title")
        layout.addWidget(titulo)

        # Grupo observação
        grupo_obs = QGroupBox("Observação")
        grupo_obs.setProperty("class", "clean-group")

        obs_layout = QVBoxLayout()
        obs_layout.setContentsMargins(8, 12, 8, 12)

        # Campo de texto
        self.text_observacao = QTextEdit()
        self.text_observacao.setPlaceholderText(
            "Digite aqui observações sobre a venda...\n\n"
            "Exemplos:\n"
            "- Desconto especial por fidelidade\n"
            "- Produto com pequeno defeito\n"
            "- Entrega agendada para..."
        )
        self.text_observacao.setText(self.observacao)
        obs_layout.addWidget(self.text_observacao)

        grupo_obs.setLayout(obs_layout)
        layout.addWidget(grupo_obs)

        # Botões
        btn_layout = QHBoxLayout()

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar)
        btn_layout.addWidget(btn_limpar)

        btn_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "secondary")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)

        btn_confirmar = QPushButton("Confirmar")
        btn_confirmar.setProperty("class", "primary")
        btn_confirmar.clicked.connect(self._confirmar)
        btn_confirmar.setDefault(True)
        btn_layout.addWidget(btn_confirmar)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Foco no campo de texto
        self.text_observacao.setFocus()

    def _limpar(self):
        """Limpa o campo de observação"""
        self.text_observacao.clear()

    def _confirmar(self):
        """Confirma e salva observação"""
        self.observacao = self.text_observacao.toPlainText().strip()
        self.accept()

    def get_observacao(self):
        """Retorna a observação inserida"""
        return self.observacao
