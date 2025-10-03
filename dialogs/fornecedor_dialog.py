#\erp\views\fornecedor_view.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QLabel, QDialogButtonBox, QFrame, QTextEdit, QCheckBox, QGroupBox)
from PyQt6.QtGui import QIcon
from models.fornecedor import Fornecedor
from utils.helpers import SelectAllLineEdit
from utils.helpers import aplicar_maiuscula_formulario

class FornecedorDialog(QDialog):
    def __init__(self, fornecedor=None, parent=None):
        super().__init__(parent)
        self.fornecedor = fornecedor or Fornecedor()
        self.init_ui()
        aplicar_maiuscula_formulario(self)

    def init_ui(self):
        self.setWindowTitle("Cadastro de Fornecedor")
        self.setMinimumWidth(500)
        self.setMinimumHeight(750)
        self.setWindowIcon(QIcon("icon.ico"))

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        self.criar_grupo_dados(layout)
        self.criar_grupo_contato(layout)
        self.criar_grupo_observacoes(layout)
        self.criar_status(layout)
        self.criar_botoes(layout)

        self.setLayout(layout)
        self.nome_edit.setFocus()

    def criar_grupo_dados(self, layout):
        grupo_dados = QGroupBox("Dados do Fornecedor")
        grupo_dados.setProperty("class", "clean-group")
        dados_layout = QVBoxLayout()
        dados_layout.setSpacing(8)

        dados_layout.addWidget(QLabel("Nome/Razão Social:*"))
        self.nome_edit = SelectAllLineEdit(self.fornecedor.nome)
        self.nome_edit.setPlaceholderText("Ex: Comércio de Materiais de Construção Ltda")
        dados_layout.addWidget(self.nome_edit)

        dados_layout.addWidget(QLabel("CNPJ:"))
        self.cnpj_edit = SelectAllLineEdit(self.fornecedor.cnpj)
        self.cnpj_edit.setPlaceholderText("Ex: 12.345.678/0001-90")
        dados_layout.addWidget(self.cnpj_edit)

        grupo_dados.setLayout(dados_layout)
        layout.addWidget(grupo_dados)

    def criar_grupo_contato(self, layout):
        grupo_contato = QGroupBox("Informações de Contato")
        grupo_contato.setProperty("class", "clean-group")
        contato_layout = QVBoxLayout()
        contato_layout.setSpacing(8)

        contato_layout.addWidget(QLabel("Endereço completo:"))
        self.endereco_edit = SelectAllLineEdit(self.fornecedor.endereco)
        self.endereco_edit.setPlaceholderText("Ex: Av. Industrial, 1000 - Galpão 5 - São Paulo/SP")
        contato_layout.addWidget(self.endereco_edit)

        contato_layout.addWidget(QLabel("Telefone para contato:"))
        self.telefone_edit = SelectAllLineEdit(self.fornecedor.telefone)
        self.telefone_edit.setPlaceholderText("Ex: (11) 3333-3333")
        contato_layout.addWidget(self.telefone_edit)

        contato_layout.addWidget(QLabel("Email comercial:"))
        self.email_edit = SelectAllLineEdit(self.fornecedor.email)
        self.email_edit.setPlaceholderText("Ex: vendas@fornecedor.com.br")
        contato_layout.addWidget(self.email_edit)

        grupo_contato.setLayout(contato_layout)
        layout.addWidget(grupo_contato)

    def criar_grupo_observacoes(self, layout):
        grupo_obs = QGroupBox("Observações e Informações Adicionais")
        grupo_obs.setProperty("class", "clean-group")
        obs_layout = QVBoxLayout()
        obs_layout.setSpacing(6)

        obs_layout.addWidget(QLabel("Condições comerciais, prazos, observações:"))
        self.observacao_edit = QTextEdit(self.fornecedor.observacao)
        self.observacao_edit.setPlaceholderText("Ex: Prazo de entrega 15 dias, pagamento 30/60/90, \ncontato: Sr. Carlos - (11) 99999-9999")
        self.observacao_edit.setMaximumHeight(100)
        obs_layout.addWidget(self.observacao_edit)

        grupo_obs.setLayout(obs_layout)
        layout.addWidget(grupo_obs)

    def criar_status(self, layout):
        status_frame = QFrame()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        status_info = QLabel("Status do fornecedor:")
        status_info.setStyleSheet("font-weight: bold; color: #cccccc;")

        self.ativo_checkbox = QCheckBox("Fornecedor ativo no sistema")
        self.ativo_checkbox.setChecked(self.fornecedor.ativo)
        self.ativo_checkbox.setToolTip("Desmarque para inativar o fornecedor (não aparecerá nas listas normais)")

        status_layout.addWidget(status_info)
        status_layout.addWidget(self.ativo_checkbox)
        status_layout.addStretch()

        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)

    def criar_botoes(self, layout):
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                  QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        buttons.button(QDialogButtonBox.StandardButton.Ok).setToolTip("Salvar as informações do fornecedor")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancelar e fechar sem salvar")

        buttons_layout.addStretch()
        buttons_layout.addWidget(buttons)

        buttons_frame.setLayout(buttons_layout)
        layout.addWidget(buttons_frame)

    def get_data(self):
        nome = self.nome_edit.text().strip()
        if not nome:
            raise ValueError("O nome do fornecedor é obrigatório!")

        self.fornecedor.nome = nome
        self.fornecedor.cnpj = self.cnpj_edit.text().strip()
        self.fornecedor.endereco = self.endereco_edit.text().strip()
        self.fornecedor.telefone = self.telefone_edit.text().strip()
        self.fornecedor.email = self.email_edit.text().strip()
        self.fornecedor.observacao = self.observacao_edit.toPlainText().strip()
        self.fornecedor.ativo = self.ativo_checkbox.isChecked()
        return self.fornecedor

    def accept(self):
        """Sobrescrita do accept para salvar dados antes de fechar"""
        try:
            # Coleta os dados do formulário
            self.get_data()

            # Salva no banco de dados
            self.fornecedor.salvar()

            # Fecha o dialog com sucesso
            super().accept()

        except ValueError as e:
            # Mostra erro de validação
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro de Validação", str(e))

        except Exception as e:
            # Mostra erro de salvamento
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o fornecedor:\n{str(e)}")
