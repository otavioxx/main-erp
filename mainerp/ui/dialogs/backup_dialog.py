"""
Diálogo de Backup - Exibido ao fechar o sistema
VERSÃO MODIFICADA: Apenas botão de backup, não permite fechar sem salvar
COM VALIDAÇÃO DE INTEGRIDADE DO BACKUP
"""

import hashlib
import json
import logging
import os
import tempfile
import uuid
import zipfile
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.core.config import obter_config
from mainerp.core.paths import caminho_dados
from mainerp.data.automatic_backup import criar_snapshot_sqlite

logger = logging.getLogger(__name__)


class BackupConfig:
    """Classe para gerenciar configurações de backup"""

    CONFIG_FILE = caminho_dados("backup_settings.json")
    BACKUP_INTERVAL_DAYS = 1  # Fonte única da verdade para o intervalo de backup

    @classmethod
    def get_last_path(cls):
        """Retorna o último caminho salvo ou Desktop por padrão"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_path = data.get("last_backup_path", "")
                    if last_path and os.path.exists(last_path):
                        return last_path
            except (OSError, json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                return os.path.join(os.path.expanduser("~"), "Desktop")
        # Retorna Desktop se não houver configuração válida
        return os.path.join(os.path.expanduser("~"), "Desktop")

    @classmethod
    def save_last_path(cls, path):
        """Salva o último caminho usado"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Configurações de backup inválidas")
            else:
                data = {}
            data["last_backup_path"] = path
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            registrar_excecao(
                __name__,
                "Exception handled in BackupConfig.save_last_path in dialogs/backup_dialog.py",
            )
            return False

    @classmethod
    def get_last_backup_date(cls):
        """Retorna a data do último backup realizado"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_date_str = data.get("last_backup_date", "")
                    if last_date_str:
                        return datetime.fromisoformat(last_date_str)
            except (OSError, ValueError):
                pass
        return None

    @classmethod
    def save_last_backup_date(cls, date=None, backup_path=None):
        """Salva a data do último backup e caminho do backup"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}

            if date is None:
                date = datetime.now()

            data["last_backup_date"] = date.isoformat()
            if backup_path:
                data["last_backup_file"] = backup_path

                # Calcular e salvar hash do arquivo de backup para verificação futura
                if os.path.exists(backup_path):
                    with open(backup_path, "rb") as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        data["last_backup_hash"] = file_hash

            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            logger.exception("Erro ao salvar configurações de backup")
            return False

    @classmethod
    def should_show_backup_dialog(cls, days_threshold=None):
        """
        Verifica se deve mostrar o diálogo de backup.
        Retorna True se o último backup foi há mais de 'days_threshold' dias
        ou se nunca foi feito backup.
        Usa BACKUP_INTERVAL_DAYS como padrão se days_threshold não for informado.
        """
        if days_threshold is None:
            days_threshold = cls.BACKUP_INTERVAL_DAYS

        last_backup_date = cls.get_last_backup_date()

        if last_backup_date is None:
            # Nunca foi feito backup
            return True

        # Calcula a diferença em dias
        days_since_last_backup = (datetime.now() - last_backup_date).days

        return days_since_last_backup >= days_threshold

    @classmethod
    def validate_last_backup(cls):
        """
        Valida se o último backup ainda existe e é íntegro
        Retorna (bool, str) - (válido, mensagem)
        """
        if not os.path.exists(cls.CONFIG_FILE):
            return False, "Nenhum backup encontrado"

        try:
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            backup_file = data.get("last_backup_file", "")
            saved_hash = data.get("last_backup_hash", "")

            if not backup_file or not os.path.exists(backup_file):
                return False, "Arquivo de backup não encontrado"

            # Verificar integridade do arquivo zip
            try:
                with zipfile.ZipFile(backup_file, "r") as zipf:
                    # Testar se o zip é válido
                    if zipf.testzip():
                        return False, "Arquivo de backup corrompido"

                    # Verificar se contém o arquivo do banco
                    db_files = [f for f in zipf.namelist() if f.endswith(".db")]
                    if not db_files:
                        return False, "Backup não contém arquivo do banco de dados"
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in BackupConfig.validate_last_backup in dialogs/backup_dialog.py",
                )
                return False, f"Erro ao ler arquivo de backup: {e!s}"

            # Verificar hash se disponível
            if saved_hash:
                with open(backup_file, "rb") as f:
                    current_hash = hashlib.md5(f.read()).hexdigest()
                    if current_hash != saved_hash:
                        return (
                            False,
                            "Hash do backup não confere - arquivo pode ter sido modificado",
                        )

            return True, "Backup válido"

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in BackupConfig.validate_last_backup in dialogs/backup_dialog.py",
            )
            return False, f"Erro na validação: {e!s}"


class BackupThread(QThread):
    """Thread para executar backup em segundo plano"""

    progress_changed = pyqtSignal(int)
    backup_completed = pyqtSignal(str)
    backup_error = pyqtSignal(str)

    def __init__(self, source_db, destination_path):
        super().__init__()
        self.source_db = source_db
        self.destination_path = destination_path
        self.backup_hash = None

    def run(self):
        temp_zip = None
        try:
            if not os.path.exists(self.source_db):
                self.backup_error.emit(f"Arquivo não encontrado: {self.source_db}")
                return

            # Criar nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_erp_{timestamp}_{uuid.uuid4().hex}.zip"

            # Primeiro, criar em um arquivo temporário na mesma unidade
            # para garantir que há espaço suficiente
            temp_dir = self.destination_path
            temp_zip = os.path.join(temp_dir, f"temp_{backup_filename}")
            full_backup_path = os.path.join(self.destination_path, backup_filename)

            self.progress_changed.emit(5)

            # Verificar espaço em disco
            try:
                import shutil

                db_size = os.path.getsize(self.source_db)
                _total, _used, free = shutil.disk_usage(self.destination_path)
                if (
                    free < db_size * 1.5
                ):  # Precisa de pelo menos 1.5x o tamanho do banco
                    self.backup_error.emit(
                        f"Espaço em disco insuficiente.\n"
                        f"Disponível: {free / (1024 * 1024 * 1024):.2f} GB\n"
                        f"Necessário: {(db_size * 1.5) / (1024 * 1024 * 1024):.2f} GB"
                    )
                    return
            except Exception:
                logger.exception("Erro ao verificar espaço em disco para backup")

            self.progress_changed.emit(10)

            with tempfile.TemporaryDirectory() as pasta_snapshot:
                snapshot = os.path.join(pasta_snapshot, "snapshot.db")
                criar_snapshot_sqlite(self.source_db, snapshot)
                with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(snapshot, os.path.basename(self.source_db))
                    self.progress_changed.emit(50)

                    config_file = "config.ini"
                    if os.path.exists(config_file):
                        zipf.write(config_file, os.path.basename(config_file))

                    self.progress_changed.emit(80)

                    readme_content = f"""Backup do Sistema ERP
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Arquivo do banco: {os.path.basename(self.source_db)}
Tamanho do snapshot: {os.path.getsize(snapshot) / (1024 * 1024):.2f} MB
"""
                    zipf.writestr("README.txt", readme_content)
                    self.progress_changed.emit(90)

            # Verificar se o zip temporário foi criado corretamente
            if not os.path.exists(temp_zip):
                self.backup_error.emit("Erro ao criar arquivo temporário")
                return

            # Testar a integridade do zip
            try:
                with zipfile.ZipFile(temp_zip, "r") as test_zip:
                    if test_zip.testzip():
                        self.backup_error.emit("Arquivo zip criado está corrompido")
                        return
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in BackupThread.run in dialogs/backup_dialog.py",
                )
                self.backup_error.emit(f"Erro ao testar zip: {e!s}")
                return

            # Renomear o arquivo temporário para o nome final
            try:
                os.replace(temp_zip, full_backup_path)
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in BackupThread.run in dialogs/backup_dialog.py",
                )
                self.backup_error.emit(f"Erro ao salvar arquivo final: {e!s}")
                return

            # Verificação final do arquivo salvo
            if not os.path.exists(full_backup_path):
                self.backup_error.emit("Arquivo de backup não foi salvo")
                return

            # Verificar tamanho do arquivo
            if os.path.getsize(full_backup_path) == 0:
                self.backup_error.emit("Arquivo de backup está vazio")
                return

            # Calcular hash do backup para verificação futura
            with open(full_backup_path, "rb") as f:
                self.backup_hash = hashlib.md5(f.read()).hexdigest()

            self.progress_changed.emit(100)
            self.backup_completed.emit(full_backup_path)

        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            registrar_excecao(
                __name__,
                "Exception handled in BackupThread.run in dialogs/backup_dialog.py",
            )
            self.backup_error.emit(f"Erro ao criar backup: {e!s}")
        finally:
            if temp_zip and os.path.exists(temp_zip):
                try:
                    os.remove(temp_zip)
                except OSError:
                    logger.exception("Falha ao remover arquivo temporário de backup")


class BackupDialog(QDialog):
    """Diálogo para realizar backup do sistema ao fechar"""

    BackupConfig = BackupConfig
    backup_realizado = pyqtSignal(str)  # Sinal emitido quando backup é feito

    def __init__(self, parent=None, force_show=False):
        """
        Inicializa o diálogo de backup.

        Args:
            parent: Widget pai
            force_show: Se True, mostra o diálogo independentemente da data do último backup
        """
        super().__init__(parent)
        self.db_path = obter_config().obter_caminho_banco()  # Banco na pasta de dados
        self.backup_thread = None
        self.force_show = force_show  # Flag para forçar exibição
        self.backup_verificado = False  # Flag para controlar se o backup foi verificado

        # Carregar último caminho salvo
        self.destination_folder = BackupConfig.get_last_path()

        # Configurar a janela para não permitir fechar pelo "X"
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint)

        self._init_ui()

    def showEvent(self, event):
        """Centraliza quando o diálogo é exibido"""
        super().showEvent(event)
        # Centraliza depois que a janela já tem seu tamanho calculado
        self._centralizar_janela()

    def resizeEvent(self, event):
        """Recentraliza quando redimensionado (opcional)"""
        super().resizeEvent(event)
        self._centralizar_janela()

    @staticmethod
    def should_show_dialog(force_show=False):
        """
        Verifica se deve mostrar o diálogo de backup.

        Args:
            force_show: Se True, ignora a verificação de data

        Returns:
            True se deve mostrar o diálogo, False caso contrário
        """
        if force_show:
            return True

        return BackupConfig.should_show_backup_dialog()

    def _init_ui(self):
        """Inicializa interface do diálogo"""
        self.setWindowTitle("Backup do Sistema - Obrigatório")
        self.setMinimumSize(500, 400)
        self.setWindowIcon(QIcon("icon.ico") if os.path.exists("icon.ico") else QIcon())

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("BACKUP OBRIGATÓRIO")
        titulo.setProperty("class", "title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1A4968;")
        layout.addWidget(titulo)

        # Informações do arquivo
        info_group = QGroupBox("Informações do Backup")
        info_layout = QVBoxLayout()

        # Caminho do banco
        db_info = QLabel(f"<b>Arquivo do banco:</b> {os.path.abspath(self.db_path)}")
        db_info.setWordWrap(True)
        info_layout.addWidget(db_info)

        # Tamanho do arquivo
        tamanho = "Não encontrado"
        if os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            tamanho = f"{size_mb:.2f} MB"

        tamanho_label = QLabel(f"<b>Tamanho:</b> {tamanho}")
        info_layout.addWidget(tamanho_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Caminho de destino
        destino_group = QGroupBox("Local de Salvamento")
        destino_layout = QVBoxLayout()

        self.caminho_label = QLabel(
            f"<b>Pasta selecionada:</b> {self.destination_folder}"
        )
        self.caminho_label.setWordWrap(True)
        self.caminho_label.setStyleSheet(
            "padding: 8px; background-color: #404040; border-radius: 4px;"
        )
        destino_layout.addWidget(self.caminho_label)

        # Botão para selecionar pasta
        btn_pasta = QPushButton("Selecionar Pasta...")
        btn_pasta.clicked.connect(self._selecionar_pasta)
        destino_layout.addWidget(btn_pasta, alignment=Qt.AlignmentFlag.AlignCenter)

        destino_group.setLayout(destino_layout)
        layout.addWidget(destino_group)

        # Mensagem de status
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Botões - APENAS O BOTÃO DE BACKUP
        button_layout = QHBoxLayout()

        # Botão Realizar Backup (centralizado)
        self.btn_backup = QPushButton("REALIZAR BACKUP E FECHAR")
        self.btn_backup.clicked.connect(self._iniciar_backup)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                padding: 15px 30px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_backup)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        # Força o cálculo do tamanho da janela
        self.adjustSize()

        # QGuiApplication.primaryScreen() pode retornar None em ambientes sem tela
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            screens = QGuiApplication.screens()
            if not screens:
                return
            screen = screens[0]

        screen_geometry = screen.geometry()

        # Calcula a posição central
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        # Move a janela para a posição calculada
        self.move(x, y)

    def _selecionar_pasta(self):
        """Abre diálogo para selecionar pasta de destino"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para Backup",
            self.destination_folder,
            QFileDialog.Option.ShowDirsOnly,
        )

        if folder:
            # Verificar se a pasta tem permissão de escrita
            test_file = os.path.join(folder, "test_write.tmp")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)

                self.destination_folder = folder
                self.caminho_label.setText(
                    f"<b>Pasta selecionada:</b> {self.destination_folder}"
                )
                # Salvar o novo caminho
                if not BackupConfig.save_last_path(folder):
                    QMessageBox.warning(
                        self,
                        "Configuração não salva",
                        "A pasta foi selecionada, mas não foi possível salvar "
                        "essa preferência para a próxima vez.",
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"A pasta selecionada não tem permissão de escrita:\n\n{e!s}",
                )

    def _iniciar_backup(self):
        """Inicia o processo de backup"""
        # Validar se o arquivo do banco existe
        if not os.path.exists(self.db_path):
            QMessageBox.critical(
                self,
                "Erro",
                f"Arquivo do banco de dados não encontrado:\n{self.db_path}\n\n"
                f"O sistema não pode ser fechado sem fazer backup.",
            )
            return

        # Validar pasta de destino
        if not os.path.exists(self.destination_folder):
            try:
                os.makedirs(self.destination_folder)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Não foi possível criar a pasta de destino:\n{e!s}\n\n"
                    f"Por favor, selecione outra pasta.",
                )
                return

        # Verificar permissão de escrita na pasta
        test_file = os.path.join(self.destination_folder, "test_write.tmp")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"A pasta selecionada não tem permissão de escrita:\n\n{e!s}\n\n"
                f"Por favor, selecione outra pasta.",
            )
            return

        # Salvar o caminho atual (caso tenha sido alterado mas não salvo)
        if not BackupConfig.save_last_path(self.destination_folder):
            QMessageBox.warning(
                self,
                "Configuração não salva",
                "O backup continuará, mas não foi possível salvar a pasta escolhida.",
            )

        # Desabilitar botão durante o backup
        self.btn_backup.setEnabled(False)

        # Mostrar status de processamento
        self.status_label.setVisible(True)
        self.status_label.setText("⏳ Criando backup...")
        self.status_label.setStyleSheet(
            "color: #007bff; font-weight: bold; font-size: 14px;"
        )

        # Criar e iniciar thread de backup
        self.backup_thread = BackupThread(self.db_path, self.destination_folder)
        self.backup_thread.backup_completed.connect(self._backup_concluido)
        self.backup_thread.backup_error.connect(self._backup_erro)
        self.backup_thread.start()

    def _backup_concluido(self, backup_path):
        """Chamado quando o backup é concluído com sucesso"""
        # Verificação adicional do arquivo criado
        if not os.path.exists(backup_path):
            self._backup_erro("Arquivo de backup não foi encontrado após a criação")
            return

        if os.path.getsize(backup_path) == 0:
            self._backup_erro("Arquivo de backup está vazio")
            return

        # Tentar abrir o zip para verificar integridade
        try:
            with zipfile.ZipFile(backup_path, "r") as test_zip:
                # Verificar se o zip está corrompido
                corrupt_file = test_zip.testzip()
                if corrupt_file:
                    self._backup_erro(f"Arquivo de backup corrompido: {corrupt_file}")
                    return

                # Verificar se contém o arquivo do banco
                db_files = [f for f in test_zip.namelist() if f.endswith(".db")]
                if not db_files:
                    self._backup_erro("Arquivo de backup não contém o banco de dados")
                    return
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in BackupDialog._backup_concluido in dialogs/backup_dialog.py",
            )
            self._backup_erro(f"Erro ao validar arquivo de backup: {e!s}")
            return

        # Salvar a data do backup com hash para verificação futura
        if not BackupConfig.save_last_backup_date(backup_path=backup_path):
            QMessageBox.warning(
                self,
                "Configuração não salva",
                "O arquivo de backup foi criado, mas não foi possível salvar sua "
                "data e localização. O sistema poderá solicitar outro backup.",
            )

        self.status_label.setText("✅ Backup concluído e verificado com sucesso!")
        self.status_label.setStyleSheet(
            "color: #28a745; font-weight: bold; font-size: 14px;"
        )

        # Marcar que o backup foi verificado
        self.backup_verificado = True

        # Mostrar mensagem de confirmação
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Backup Concluído")
        msg_box.setText(
            f"Backup realizado com sucesso!\n\n"
            f"Arquivo: {os.path.basename(backup_path)}\n"
            f"Local: {os.path.dirname(backup_path)}\n"
            f"Tamanho: {os.path.getsize(backup_path) / (1024 * 1024):.2f} MB\n\n"
        )

        # Botão OK padrão
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        msg_box.exec()

        # Emitir sinal de backup realizado
        self.backup_realizado.emit(backup_path)

        # Fechar o diálogo de backup
        self.accept()

    def _backup_erro(self, mensagem_erro):
        """Chamado quando ocorre erro no backup"""
        # Habilitar botão novamente
        self.btn_backup.setEnabled(True)

        # Esconder status
        self.status_label.setVisible(False)

        # Reset da flag de verificação
        self.backup_verificado = False

        # Mensagem de erro mais detalhada
        QMessageBox.critical(
            self,
            "Erro no Backup",
            f"Ocorreu um erro durante o backup:\n\n{mensagem_erro}\n\n"
            f"O sistema NÃO será fechado.\n\n"
            f"Por favor, verifique:\n"
            f"• Se a unidade de destino tem espaço disponível\n"
            f"• Se a unidade de destino está funcionando corretamente\n"
            f"• Se você tem permissão de escrita na pasta\n\n"
            f"Tente novamente ou selecione outra pasta.",
        )

    def _abrir_pasta(self, backup_path):
        """Abre a pasta onde o backup foi salvo"""
        try:
            if os.name == "nt":  # Windows
                os.startfile(os.path.dirname(backup_path))
            elif os.name == "posix":  # Linux/Mac
                import subprocess

                subprocess.Popen(["xdg-open", os.path.dirname(backup_path)])
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in BackupDialog._abrir_pasta in dialogs/backup_dialog.py",
            )
            QMessageBox.warning(
                self, "Aviso", f"Não foi possível abrir a pasta:\n{e!s}"
            )

    def closeEvent(self, event):
        """Intercepta o fechamento da janela - NÃO PERMITE FECHAR SEM BACKUP"""
        if self.backup_thread and self.backup_thread.isRunning():
            QMessageBox.information(
                self,
                "Backup em Andamento",
                "O backup ainda está em andamento.\n\n"
                "Aguarde a conclusão do backup para fechar o sistema.",
                QMessageBox.StandardButton.Ok,
            )
            event.ignore()

        elif not self.backup_verificado:
            QMessageBox.warning(
                self,
                "Backup Obrigatório",
                "Para fechar o sistema é necessário realizar um backup com sucesso.\n\n"
                "Clique no botão 'REALIZAR BACKUP E FECHAR' para continuar.",
                QMessageBox.StandardButton.Ok,
            )
            event.ignore()

        else:
            event.accept()
