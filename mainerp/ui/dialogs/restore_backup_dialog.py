"""
Diálogo para Restauração de Backup
"""

import os
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.core.config import obter_config
from mainerp.data.db_utils import DatabaseManager
from mainerp.data.restore import preparar_restauracao
from mainerp.ui.dialog_base import DialogBase
from mainerp.ui.styles import cores_ativas


class VerifyBackupThread(QThread):
    """Thread para verificar backup em segundo plano"""

    verification_complete = pyqtSignal(dict)
    verification_error = pyqtSignal(str)

    def __init__(self, backup_path):
        super().__init__()
        self.backup_path = backup_path

    def run(self):
        try:
            if not os.path.exists(self.backup_path):
                self.verification_error.emit(
                    f"Arquivo não encontrado: {self.backup_path}"
                )
                return

            # Obter informações do backup
            if self.backup_path.lower().endswith(".zip"):
                info = self._get_zip_info()
            else:
                info = self._get_db_info()

            self.verification_complete.emit(info)

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VerifyBackupThread.run in dialogs/restore_backup_dialog.py",
            )
            self.verification_error.emit(f"Erro ao verificar backup: {e!s}")

    def _get_zip_info(self):
        """Obtém informações de arquivo ZIP"""
        import shutil
        import tempfile
        import zipfile

        info = {
            "type": "zip",
            "path": self.backup_path,
            "size_mb": os.path.getsize(self.backup_path) / (1024 * 1024),
            "modified": datetime.fromtimestamp(os.path.getmtime(self.backup_path)),
            "is_valid": False,
            "tables": [],
            "record_counts": {},
            "db_files": [],
        }

        try:
            with zipfile.ZipFile(self.backup_path, "r") as zipf:
                # Listar arquivos
                info["files"] = zipf.namelist()

                # Procurar arquivo .db
                db_files = [
                    item for item in zipf.infolist()
                    if not item.is_dir() and item.filename.lower().endswith(".db")
                ]
                info["db_files"] = [item.filename for item in db_files]

                if len(db_files) == 1:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        db_filename = db_files[0].filename
                        extracted_db = os.path.join(temp_dir, "backup.db")
                        with zipf.open(db_files[0]) as origem, open(extracted_db, "wb") as destino:
                            shutil.copyfileobj(origem, destino)

                        # Verificar o banco extraído
                        db_info = DatabaseManager.get_database_info(extracted_db)
                        if db_info and DatabaseManager._verify_database(extracted_db):
                            info["is_valid"] = True
                            info["tables"] = db_info["tables"]
                            info["record_counts"] = db_info["record_counts"]
                            info["db_name"] = db_filename
                else:
                    info["error"] = "O backup ZIP deve conter exatamente um banco .db"
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VerifyBackupThread._get_zip_info in dialogs/restore_backup_dialog.py",
            )
            info["error"] = str(e)

        return info

    def _get_db_info(self):
        """Obtém informações de arquivo .db"""
        info = DatabaseManager.get_database_info(self.backup_path)
        if info and DatabaseManager._verify_database(self.backup_path):
            info["type"] = "db"
            info["is_valid"] = True
        else:
            info = {
                "type": "db",
                "path": self.backup_path,
                "is_valid": False,
                "error": "Arquivo de banco de dados inválido",
            }

        return info


class RestoreBackupThread(QThread):
    """Prepara o backup; a restauração é feita na próxima inicialização."""

    progress_changed = pyqtSignal(int)
    restore_complete = pyqtSignal(str)
    restore_error = pyqtSignal(str)

    def __init__(self, backup_path, target_db):
        super().__init__()
        self.backup_path = backup_path
        self.target_db = target_db

    def run(self):
        try:
            self.progress_changed.emit(10)

            # Verificar backup
            if not os.path.exists(self.backup_path):
                self.restore_error.emit(f"Arquivo não encontrado: {self.backup_path}")
                return

            self.progress_changed.emit(30)

            preparar_restauracao(self.backup_path, self.target_db)
            self.progress_changed.emit(100)
            self.restore_complete.emit(
                f"Backup preparado: {os.path.basename(self.backup_path)}"
            )

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in RestoreBackupThread.run in dialogs/restore_backup_dialog.py",
            )
            self.restore_error.emit(f"Erro durante a restauração: {e!s}")


class RestoreBackupDialog(DialogBase):
    """Diálogo para restauração de backup"""

    restore_completed = pyqtSignal()  # Sinal emitido quando restauração é concluída

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_db = obter_config().obter_caminho_banco()  # Banco atual
        self.backup_info = None
        self.verify_thread = None
        self.restore_thread = None

        self._init_ui()
        self._carregar_backups_locais()

    def showEvent(self, event):
        """Centraliza quando o diálogo é exibido"""
        super().showEvent(event)
        # Centraliza depois que a janela já tem seu tamanho calculado
        self._centralizar_janela()

    def resizeEvent(self, event):
        """Recentraliza quando redimensionado (opcional)"""
        super().resizeEvent(event)
        self._centralizar_janela()

    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        # Força o cálculo do tamanho da janela
        self.adjustSize()

        # Obtém a geometria da tela
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is None:
            raise RuntimeError("Não foi possível localizar a tela principal.")
        screen = primary_screen.geometry()

        # Calcula a posição central
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2

        # Move a janela para a posição calculada
        self.move(x, y)

    def _init_ui(self):
        """Inicializa interface do diálogo"""
        self.setWindowTitle("Restauração de Backup")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Título
        titulo = QLabel("RESTAURAÇÃO DE BACKUP")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setProperty("class", "title")
        layout.addWidget(titulo)

        # Divisor
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Painel superior: Seleção de arquivo
        top_panel = QGroupBox("Selecionar Backup")
        top_layout = QVBoxLayout()

        # Caminho do arquivo
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Arquivo de backup:"))

        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet(f"padding: 8px; background-color: {cores_ativas().surface_alt}; color: {cores_ativas().text_primary};")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label, 1)

        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self._selecionar_arquivo)
        btn_browse.setProperty("class", "secondary")
        file_layout.addWidget(btn_browse)

        top_layout.addLayout(file_layout)

        # Backups locais
        local_backups_group = QGroupBox("Backups Locais")
        local_layout = QVBoxLayout()

        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(4)
        self.backups_table.setHorizontalHeaderLabels(
            ["Arquivo", "Tamanho", "Data", "Tipo"]
        )
        header = self.backups_table.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.backups_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.backups_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.backups_table.cellDoubleClicked.connect(self._selecionar_backup_tabela)

        local_layout.addWidget(self.backups_table)
        local_backups_group.setLayout(local_layout)
        top_layout.addWidget(local_backups_group)

        top_panel.setLayout(top_layout)
        splitter.addWidget(top_panel)

        # Painel inferior: Informações e ações
        bottom_panel = QGroupBox("Informações do Backup")
        bottom_layout = QVBoxLayout()

        # Área de informações
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        self.info_text.setStyleSheet("font-family: Consolas, monospace; font-size: 10pt;")
        bottom_layout.addWidget(self.info_text)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        bottom_layout.addWidget(self.status_label)

        bottom_panel.setLayout(bottom_layout)
        splitter.addWidget(bottom_panel)

        # Configurar tamanhos do splitter
        splitter.setSizes([300, 200])
        layout.addWidget(splitter, 1)

        # Botões de ação
        button_layout = QHBoxLayout()

        # Botão Verificar
        self.btn_verify = QPushButton("Verificar Backup")
        self.btn_verify.clicked.connect(self._verificar_backup)
        self.btn_verify.setEnabled(False)
        self.btn_verify.setProperty("class", "primary")

        # Botão Restaurar
        self.btn_restore = QPushButton("Restaurar Backup")
        self.btn_restore.clicked.connect(self._iniciar_restauracao)
        self.btn_restore.setEnabled(False)
        self.btn_restore.setProperty("class", "success")

        # Botão Cancelar
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setProperty("class", "secondary")

        button_layout.addWidget(self.btn_verify)
        button_layout.addWidget(self.btn_restore)
        button_layout.addStretch()
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _carregar_backups_locais(self):
        """Carrega lista de backups locais"""
        backups_folder = os.path.join(os.path.dirname(self.current_db), "backups")
        if os.path.exists(backups_folder):
            backups = DatabaseManager.list_backups(backups_folder)

            self.backups_table.setRowCount(len(backups))

            for i, backup in enumerate(backups):
                # Nome do arquivo
                name_item = QTableWidgetItem(backup["name"])
                name_item.setData(Qt.ItemDataRole.UserRole, backup["path"])

                # Tamanho
                size_item = QTableWidgetItem(f"{backup['size_mb']:.2f} MB")

                # Data
                date_item = QTableWidgetItem(
                    backup["modified"].strftime("%d/%m/%Y %H:%M")
                )

                # Tipo
                type_item = QTableWidgetItem("ZIP" if backup["type"] == "zip" else "DB")

                self.backups_table.setItem(i, 0, name_item)
                self.backups_table.setItem(i, 1, size_item)
                self.backups_table.setItem(i, 2, date_item)
                self.backups_table.setItem(i, 3, type_item)

    def _selecionar_arquivo(self):
        """Abre diálogo para selecionar arquivo de backup"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Backup",
            "",
            "Arquivos de Backup (*.db *.zip);;Todos os arquivos (*.*)",
        )

        if file_path:
            self._processar_arquivo_selecionado(file_path)

    def _selecionar_backup_tabela(self, row, column):
        """Seleciona backup da tabela"""
        item = self.backups_table.item(row, 0)
        if item is None:
            return
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self._processar_arquivo_selecionado(file_path)

    def _processar_arquivo_selecionado(self, file_path):
        """Processa arquivo selecionado"""
        self.file_label.setText(file_path)
        self.btn_verify.setEnabled(True)
        self.btn_restore.setEnabled(False)
        self.backup_info = None

        # Limpar informações anteriores
        self.info_text.clear()
        self.info_text.append(f"Arquivo selecionado: {os.path.basename(file_path)}")
        self.info_text.append(f"Caminho: {file_path}")

        if file_path.endswith(".zip"):
            self.info_text.append("Tipo: Arquivo ZIP (compactado)")
        else:
            self.info_text.append("Tipo: Arquivo de banco de dados (.db)")

        self.info_text.append(
            "\nClique em 'Verificar Backup' para analisar o arquivo..."
        )

    def _verificar_backup(self):
        """Verifica o arquivo de backup selecionado"""
        file_path = self.file_label.text()
        if not file_path or file_path == "Nenhum arquivo selecionado":
            QMessageBox.warning(
                self, "Aviso", "Selecione um arquivo de backup primeiro."
            )
            return

        # Desabilitar botões durante verificação
        self.btn_verify.setEnabled(False)
        self.btn_restore.setEnabled(False)

        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Progresso indeterminado

        self.status_label.setVisible(True)
        self.status_label.setText("Verificando arquivo de backup...")
        self.status_label.setStyleSheet(f"color: {cores_ativas().accent_text}; font-weight: bold;")

        # Criar e iniciar thread de verificação
        self.verify_thread = VerifyBackupThread(file_path)
        self.verify_thread.verification_complete.connect(self._verificacao_concluida)
        self.verify_thread.verification_error.connect(self._verificacao_erro)
        self.verify_thread.start()

    def _verificacao_concluida(self, info):
        """Chamado quando a verificação é concluída"""
        self.backup_info = info
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)

        # Atualizar informações
        self.info_text.clear()

        if info.get("is_valid"):
            self.info_text.append("✅ BACKUP VÁLIDO")
            self.info_text.append("=" * 40)

            # Informações básicas
            self.info_text.append(f"Arquivo: {os.path.basename(info['path'])}")
            self.info_text.append(f"Tamanho: {info.get('size_mb', 0):.2f} MB")
            self.info_text.append(
                f"Data: {info.get('modified', '').strftime('%d/%m/%Y %H:%M')}"
            )

            if info["type"] == "zip":
                self.info_text.append(
                    f"Tipo: ZIP (contém: {', '.join(info.get('db_files', []))})"
                )

            self.info_text.append("\n📊 TABELAS ENCONTRADAS:")
            self.info_text.append("-" * 30)

            # Listar tabelas
            for table in info.get("tables", []):
                count = info.get("record_counts", {}).get(table, 0)
                self.info_text.append(f"  • {table}: {count} registros")

            # Contagem total
            total_tables = len(info.get("tables", []))
            total_records = sum(info.get("record_counts", {}).values())
            self.info_text.append(
                f"\n📈 TOTAL: {total_tables} tabelas, {total_records} registros"
            )

            # Habilitar botão de restauração
            self.btn_restore.setEnabled(True)
            self.status_label.setVisible(True)
            self.status_label.setText("✅ Backup verificado e válido para restauração")
            self.status_label.setStyleSheet(f"color: {cores_ativas().success_text}; font-weight: bold;")

        else:
            self.info_text.append("❌ BACKUP INVÁLIDO OU CORROMPIDO")
            self.info_text.append("=" * 40)
            self.info_text.append(f"Erro: {info.get('error', 'Arquivo inválido')}")

            self.status_label.setVisible(True)
            self.status_label.setText("❌ Backup inválido - Não pode ser restaurado")
            self.status_label.setStyleSheet(f"color: {cores_ativas().danger_text}; font-weight: bold;")

        # Reabilitar botão de verificação
        self.btn_verify.setEnabled(True)

    def _verificacao_erro(self, mensagem_erro):
        """Chamado quando ocorre erro na verificação"""
        self.progress_bar.setVisible(False)
        self.btn_verify.setEnabled(True)

        self.status_label.setVisible(True)
        self.status_label.setText("❌ Erro na verificação do backup")
        self.status_label.setStyleSheet(f"color: {cores_ativas().danger_text}; font-weight: bold;")

        QMessageBox.critical(
            self,
            "Erro na Verificação",
            f"Ocorreu um erro ao verificar o backup:\n\n{mensagem_erro}",
        )

    def _iniciar_restauracao(self):
        """Inicia o processo de restauração"""
        if not self.backup_info or not self.backup_info.get("is_valid"):
            QMessageBox.warning(self, "Aviso", "Verifique o backup antes de restaurar.")
            return

        if (
            os.environ.get("MAINERP_LAUNCHER") == "1"
            and os.environ.get("MAINERP_RESTORE_PROTOCOL") != "1"
        ):
            QMessageBox.critical(
                self,
                "Atualização do launcher necessária",
                "Atualize o launcher com o instalador antes de restaurar um backup. "
                "Nenhum dado foi alterado.",
            )
            return

        # Confirmar restauração
        reply = QMessageBox.warning(
            self,
            "⚠️ CONFIRMAR RESTAURAÇÃO",
            "ATENÇÃO: Esta ação irá SUBSTITUIR o banco de dados atual!\n\n"
            "• Todos os dados atuais serão perdidos\n"
            "• O sistema será fechado e a restauração ocorrerá na próxima abertura\n"
            "• Um backup do estado atual será criado antes da restauração\n\n"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Desabilitar botões
        self.btn_verify.setEnabled(False)
        self.btn_restore.setEnabled(False)

        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_label.setVisible(True)
        self.status_label.setText("Iniciando restauração do backup...")
        self.status_label.setStyleSheet(f"color: {cores_ativas().accent_text}; font-weight: bold;")

        # Criar e iniciar thread de restauração
        self.restore_thread = RestoreBackupThread(
            self.backup_info["path"], self.current_db
        )
        self.restore_thread.progress_changed.connect(
            self._atualizar_progresso_restauracao
        )
        self.restore_thread.restore_complete.connect(self._restauracao_concluida)
        self.restore_thread.restore_error.connect(self._restauracao_erro)
        self.restore_thread.start()

    def _atualizar_progresso_restauracao(self, valor):
        """Atualiza a barra de progresso da restauração"""
        self.progress_bar.setValue(valor)

        # Atualizar mensagem de status
        if valor < 30:
            self.status_label.setText("Preparando restauração...")
        elif valor < 60:
            self.status_label.setText("Validando backup...")
        elif valor < 90:
            self.status_label.setText("Preparando restauração...")
        else:
            self.status_label.setText("Finalizando restauração...")

    def _restauracao_concluida(self, mensagem):
        """Chamado quando o backup foi preparado com sucesso."""
        if self.restore_thread is not None:
            self.restore_thread.wait()
        self.progress_bar.setValue(100)

        self.status_label.setText("✅ Restauração preparada!")
        self.status_label.setStyleSheet(f"color: {cores_ativas().success_text}; font-weight: bold;")

        # Mostrar mensagem de sucesso
        QMessageBox.information(
            self,
            "Restauração preparada",
            f"{mensagem}\n\nO sistema será fechado; a restauração será aplicada "
            "antes da próxima abertura.",
        )

        # Emitir sinal de restauração concluída
        self.restore_completed.emit()

        # Fechar o diálogo
        self.accept()

        # O sistema principal deve tratar o reinício

    def _restauracao_erro(self, mensagem_erro):
        """Chamado quando ocorre erro na restauração"""
        self.btn_verify.setEnabled(True)
        self.btn_restore.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.status_label.setVisible(True)
        self.status_label.setText("❌ Erro durante a restauração")
        self.status_label.setStyleSheet(f"color: {cores_ativas().danger_text}; font-weight: bold;")

        QMessageBox.critical(
            self,
            "❌ Erro na Restauração",
            f"Ocorreu um erro durante a restauração:\n\n{mensagem_erro}\n\n"
            "A preparação falhou; nenhum dado atual foi substituído.",
        )

    def _pode_fechar(self):
        if self.restore_thread and self.restore_thread.isRunning():
            QMessageBox.warning(
                self,
                "Restauração em Andamento",
                "Aguarde a conclusão da restauração antes de fechar esta janela.",
            )
            return False

        if self.verify_thread and self.verify_thread.isRunning():
            QMessageBox.warning(
                self,
                "Verificação em Andamento",
                "Aguarde a conclusão da verificação antes de fechar esta janela.",
            )
            return False

        return True

    def reject(self):
        if self._pode_fechar():
            super().reject()

    def closeEvent(self, event):
        """Intercepta o fechamento da janela"""
        if self._pode_fechar():
            event.accept()
        else:
            event.ignore()
