# \erp\views\config_view.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mainerp.data.models.empresa import Empresa
from mainerp.ui.dialogs.backup_dialog import BackupDialog
from mainerp.ui.dialogs.config_selection_dialog import ConfigSelectionDialog
from mainerp.ui.dialogs.restore_backup_dialog import RestoreBackupDialog


class ConfigView(QWidget):
    def __init__(self):
        super().__init__()
        self.empresa = Empresa.buscar()
        self.logo_path = None
        self.edit_mode = False
        self.initUI()
        self.carregar_configuracoes()
        self.toggle_edit_mode(False)

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(15)

        self.header_logo = QLabel()
        self.header_logo.setFixedSize(40, 40)
        self.header_logo.setProperty("class", "configuracao-header-logo")
        self.atualizar_header_logo()

        titulo = QLabel("Configurações da Empresa")
        titulo.setProperty("class", "configuracao-title")

        header_layout.addWidget(self.header_logo)
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setProperty("class", "primary")
        self.btn_editar.setFixedWidth(100)
        self.btn_editar.clicked.connect(self.toggle_edit)
        header_layout.addWidget(self.btn_editar)

        btn_avancadas = QPushButton("⚙️")
        btn_avancadas.setProperty("class", "secondary")
        btn_avancadas.setFixedWidth(120)
        btn_avancadas.clicked.connect(self.mostrar_configuracoes_avancadas)
        header_layout.addWidget(btn_avancadas)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setProperty("class", "separator")
        layout.addWidget(separator)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setProperty("class", "clean-scroll")

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(5, 5, 5, 5)

        self.tab_widget = QTabWidget()
        self.tab_widget.setProperty("class", "clean-tabs")

        aba_empresa = QWidget()
        empresa_layout = QVBoxLayout()
        empresa_layout.setSpacing(12)
        empresa_layout.setContentsMargins(10, 10, 10, 10)

        grupo_basico = QGroupBox("Informações Básicas")
        grupo_basico.setProperty("class", "clean-group")
        form_basico = QFormLayout()
        form_basico.setSpacing(10)
        form_basico.setContentsMargins(15, 20, 15, 15)

        self.nome_edit = QLineEdit()
        self.nome_edit.setPlaceholderText("Nome completo da empresa")
        self.nome_edit.setMinimumHeight(35)

        self.cnpj_edit = QLineEdit()
        self.cnpj_edit.setPlaceholderText("00.000.000/0000-00")
        self.cnpj_edit.setMinimumHeight(35)

        form_basico.addRow(QLabel("Nome da Empresa:"), self.nome_edit)
        form_basico.addRow(QLabel("CNPJ:"), self.cnpj_edit)

        grupo_basico.setLayout(form_basico)
        empresa_layout.addWidget(grupo_basico)

        grupo_contato = QGroupBox("Contato")
        grupo_contato.setProperty("class", "clean-group")
        form_contato = QFormLayout()
        form_contato.setSpacing(10)
        form_contato.setContentsMargins(15, 20, 15, 15)

        self.telefone_edit = QLineEdit()
        self.telefone_edit.setPlaceholderText("(00) 00000-0000")
        self.telefone_edit.setMinimumHeight(35)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Ex: contato@empresa.com")
        self.email_edit.setMinimumHeight(35)

        form_contato.addRow(QLabel("Telefone:"), self.telefone_edit)
        form_contato.addRow(QLabel("Email:"), self.email_edit)

        grupo_contato.setLayout(form_contato)
        empresa_layout.addWidget(grupo_contato)

        grupo_endereco = QGroupBox("Endereço")
        grupo_endereco.setProperty("class", "clean-group")
        endereco_layout = QVBoxLayout()
        endereco_layout.setContentsMargins(15, 20, 15, 15)

        self.endereco_edit = QTextEdit()
        self.endereco_edit.setPlaceholderText("Digite o endereço completo da empresa")
        self.endereco_edit.setMaximumHeight(100)
        self.endereco_edit.setMinimumHeight(80)

        endereco_layout.addWidget(self.endereco_edit)
        grupo_endereco.setLayout(endereco_layout)
        empresa_layout.addWidget(grupo_endereco)

        grupo_logo = QGroupBox("Logo da Empresa")
        grupo_logo.setProperty("class", "clean-group")
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(15, 20, 15, 15)

        logo_container = QWidget()
        logo_container_layout = QHBoxLayout()
        logo_container_layout.setContentsMargins(0, 0, 0, 0)

        logo_area = QFrame()
        logo_area_layout = QVBoxLayout()
        logo_area_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.setProperty("class", "configuracao-logo-label")
        self.atualizar_logo()

        self.logo_label.mousePressEvent = self.selecionar_logo
        self.logo_label.setCursor(Qt.CursorShape.PointingHandCursor)

        logo_area_layout.addWidget(self.logo_label)
        logo_area.setLayout(logo_area_layout)

        logo_buttons = QWidget()
        logo_buttons_layout = QVBoxLayout()
        logo_buttons_layout.setSpacing(8)
        logo_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_selecionar_logo = QPushButton("Selecionar")
        self.btn_selecionar_logo.setProperty("class", "secondary")
        self.btn_selecionar_logo.setFixedWidth(120)
        self.btn_selecionar_logo.clicked.connect(self.selecionar_logo)

        self.btn_remover_logo = QPushButton("Remover")
        self.btn_remover_logo.setProperty("class", "danger")
        self.btn_remover_logo.setFixedWidth(120)
        self.btn_remover_logo.clicked.connect(self.remover_logo)

        logo_buttons_layout.addWidget(self.btn_selecionar_logo)
        logo_buttons_layout.addWidget(self.btn_remover_logo)
        logo_buttons_layout.addStretch()

        logo_buttons.setLayout(logo_buttons_layout)

        logo_container_layout.addWidget(logo_area)
        logo_container_layout.addSpacing(20)
        logo_container_layout.addWidget(logo_buttons)
        logo_container_layout.addStretch()

        logo_container.setLayout(logo_container_layout)
        logo_layout.addWidget(logo_container)
        grupo_logo.setLayout(logo_layout)
        empresa_layout.addWidget(grupo_logo)

        empresa_layout.addStretch()
        aba_empresa.setLayout(empresa_layout)

        self.tab_widget.addTab(aba_empresa, "Dados da Empresa")

        content_layout.addWidget(self.tab_widget)
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        layout.addWidget(scroll_area)

        self.action_frame = QFrame()
        self.action_frame.setVisible(False)
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 10, 0, 0)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("class", "danger")
        btn_cancelar.setFixedWidth(120)
        btn_cancelar.clicked.connect(self.cancelar_edicao)

        btn_salvar = QPushButton("Salvar")
        btn_salvar.setProperty("class", "success")
        btn_salvar.setFixedWidth(120)
        btn_salvar.clicked.connect(self.salvar_configuracoes)

        action_layout.addStretch()
        action_layout.addWidget(btn_cancelar)
        action_layout.addSpacing(10)
        action_layout.addWidget(btn_salvar)

        self.action_frame.setLayout(action_layout)
        layout.addWidget(self.action_frame)

        # Grupo de Backup/Restauração (sempre visível)
        backup_group = QGroupBox("Backup e Restauração")
        backup_group.setProperty("class", "clean-group")
        backup_layout = QVBoxLayout()
        backup_layout.setContentsMargins(15, 20, 15, 15)

        # Botões em linha
        btn_layout = QHBoxLayout()

        # Botão Criar Backup
        btn_backup = QPushButton("💾 Criar Backup")
        btn_backup.setProperty("class", "primary")
        btn_backup.setFixedWidth(150)
        btn_backup.clicked.connect(self._criar_backup)

        # Botão Restaurar Backup
        btn_restore = QPushButton("📁 Restaurar Backup")
        btn_restore.setProperty("class", "warning")
        btn_restore.setFixedWidth(150)
        btn_restore.clicked.connect(self._restaurar_backup)

        btn_layout.addWidget(btn_backup)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(btn_restore)
        btn_layout.addStretch()

        backup_layout.addLayout(btn_layout)
        backup_group.setLayout(backup_layout)

        layout.addWidget(backup_group)

        self.setLayout(layout)

    def atualizar_logo(self):
        if self.empresa.logo:
            pixmap = QPixmap()
            pixmap.loadFromData(self.empresa.logo)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.logo_label.setPixmap(pixmap)
                self.logo_label.setText("")
            else:
                self.logo_label.setText("Logo inválido\nClique para selecionar")
        else:
            self.logo_label.setText("Sem logo\nClique para selecionar")

    def atualizar_header_logo(self):
        if self.empresa.logo:
            pixmap = QPixmap()
            pixmap.loadFromData(self.empresa.logo)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    40,
                    40,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.header_logo.setPixmap(pixmap)
                self.header_logo.setText("")
            else:
                self.header_logo.setText("")
        else:
            self.header_logo.setText("🏢")

    def toggle_edit_mode(self, edit_mode):
        self.edit_mode = edit_mode

        campos = [
            self.nome_edit,
            self.cnpj_edit,
            self.telefone_edit,
            self.email_edit,
            self.endereco_edit,
        ]

        for campo in campos:
            campo.setReadOnly(not edit_mode)
            campo.setProperty("class", "editable" if edit_mode else "readonly")

        self.action_frame.setVisible(edit_mode)
        self.btn_editar.setVisible(not edit_mode)

        self.btn_selecionar_logo.setEnabled(edit_mode)
        self.btn_remover_logo.setEnabled(edit_mode)
        self.logo_label.setEnabled(edit_mode)

        if edit_mode:
            self.btn_editar.setText("Editando...")
        else:
            self.btn_editar.setText("Editar")

    def toggle_edit(self):
        self.toggle_edit_mode(True)

    def cancelar_edicao(self):
        self.carregar_configuracoes()
        self.toggle_edit_mode(False)
        QMessageBox.information(
            self, "Edição Cancelada", "As alterações foram descartadas."
        )

    def carregar_configuracoes(self):
        """Carrega as configurações nos campos"""
        self.nome_edit.setText(self.empresa.nome or "")
        self.cnpj_edit.setText(self.empresa.cnpj or "")
        self.telefone_edit.setText(self.empresa.telefone or "")
        self.email_edit.setText(self.empresa.email or "")
        self.endereco_edit.setPlainText(self.empresa.endereco or "")
        self.atualizar_logo()
        self.atualizar_header_logo()

    def selecionar_logo(self, event=None):
        if not self.edit_mode:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Logo",
            "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;Todos os arquivos (*)",
        )

        if file_path:
            self.logo_path = file_path
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.logo_label.setPixmap(pixmap)
                self.logo_label.setText("")

    def remover_logo(self):
        if not self.edit_mode:
            return

        resposta = QMessageBox.question(
            self,
            "Remover Logo",
            "Tem certeza que deseja remover o logo da empresa?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.logo_path = None
            self.empresa.logo = None
            self.logo_label.clear()
            self.logo_label.setText("Sem logo\nClique para selecionar")

    def salvar_configuracoes(self):
        try:
            if not self.nome_edit.text().strip():
                QMessageBox.warning(self, "Aviso", "O nome da empresa é obrigatório!")
                return

            self.empresa.nome = self.nome_edit.text().strip()
            self.empresa.cnpj = self.cnpj_edit.text().strip()
            self.empresa.telefone = self.telefone_edit.text().strip()
            self.empresa.email = self.email_edit.text().strip()
            self.empresa.endereco = self.endereco_edit.toPlainText().strip()

            if self.logo_path:
                with open(self.logo_path, "rb") as f:
                    self.empresa.logo = f.read()

            self.empresa.salvar()

            self.atualizar_header_logo()
            self.toggle_edit_mode(False)

            QMessageBox.information(
                self, "Sucesso", "Configurações salvas com sucesso!"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {e!s}")

    def mostrar_configuracoes_avancadas(self):
        dialog = ConfigSelectionDialog(self)
        dialog.exec()

    # ========== MÉTODOS DE BACKUP/RESTAURAÇÃO ==========

    def _criar_backup(self):
        """Abre diálogo para criar backup manual"""
        try:
            dialog = BackupDialog(self)
            dialog.setWindowTitle("Criar Backup Manual")
            dialog.backup_realizado.connect(self._backup_concluido)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao abrir diálogo de backup: {e!s}"
            )

    def _restaurar_backup(self):
        """Abre diálogo para restaurar backup"""
        try:
            dialog = RestoreBackupDialog(self)
            dialog.setWindowTitle("Restaurar Backup")
            dialog.restore_completed.connect(self._restauracao_concluida)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao abrir diálogo de restauração: {e!s}"
            )

    def _backup_concluido(self, backup_path):
        """Chamado quando backup é criado com sucesso"""
        if backup_path:  # Pode ser string vazia
            QMessageBox.information(
                self, "✅ Backup Criado", f"Backup criado com sucesso:\n\n{backup_path}"
            )

    def _restauracao_concluida(self):
        """Fecha o sistema para aplicar a restauração na próxima inicialização."""
        self._reiniciar_sistema()

    def _reiniciar_sistema(self):
        """Reinicia o sistema após restauração"""
        # Emite código especial para reinício (100)
        from PyQt6.QtWidgets import QApplication

        QApplication.exit(100)
