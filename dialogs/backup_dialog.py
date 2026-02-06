"""
Diálogo de Backup - Exibido ao fechar o sistema
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QGroupBox,
                             QDialogButtonBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QGuiApplication
import os
import shutil
from datetime import datetime, timedelta
import zipfile
import json


class BackupConfig:
    """Classe para gerenciar configurações de backup"""
    
    CONFIG_FILE = "backup_settings.json"
    
    @classmethod
    def get_last_path(cls):
        """Retorna o último caminho salvo ou Desktop por padrão"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_path = data.get('last_backup_path', '')
                    if last_path and os.path.exists(last_path):
                        return last_path
            except:
                pass
        # Retorna Desktop se não houver configuração válida
        return os.path.join(os.path.expanduser("~"), "Desktop")
    
    @classmethod
    def save_last_path(cls, path):
        """Salva o último caminho usado"""
        try:
            data = {'last_backup_path': path}
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    @classmethod
    def get_last_backup_date(cls):
        """Retorna a data do último backup realizado"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_date_str = data.get('last_backup_date', '')
                    if last_date_str:
                        return datetime.fromisoformat(last_date_str)
            except:
                pass
        return None
    
    @classmethod
    def save_last_backup_date(cls, date=None):
        """Salva a data do último backup"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            if date is None:
                date = datetime.now()
            
            data['last_backup_date'] = date.isoformat()
            
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    @classmethod
    def should_show_backup_dialog(cls, days_threshold=7):
        """
        Verifica se deve mostrar o diálogo de backup.
        Retorna True se o último backup foi há mais de 'days_threshold' dias
        ou se nunca foi feito backup.
        """
        last_backup_date = cls.get_last_backup_date()
        
        if last_backup_date is None:
            # Nunca foi feito backup
            return True
        
        # Calcula a diferença em dias
        days_since_last_backup = (datetime.now() - last_backup_date).days
        
        return days_since_last_backup >= days_threshold


class BackupThread(QThread):
    """Thread para executar backup em segundo plano"""
    progress_changed = pyqtSignal(int)
    backup_completed = pyqtSignal(str)
    backup_error = pyqtSignal(str)
    
    def __init__(self, source_db, destination_path):
        super().__init__()
        self.source_db = source_db
        self.destination_path = destination_path
        
    def run(self):
        try:
            if not os.path.exists(self.source_db):
                self.backup_error.emit(f"Arquivo não encontrado: {self.source_db}")
                return
            
            # Criar nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_erp_{timestamp}.zip"
            full_backup_path = os.path.join(self.destination_path, backup_filename)
            
            self.progress_changed.emit(10)
            
            # Criar arquivo zip
            with zipfile.ZipFile(full_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar arquivo do banco de dados
                zipf.write(self.source_db, os.path.basename(self.source_db))
                self.progress_changed.emit(50)
                
                # Adicionar arquivo de configuração se existir
                config_file = "config.ini"
                if os.path.exists(config_file):
                    zipf.write(config_file, os.path.basename(config_file))
                
                self.progress_changed.emit(80)
                
                # Adicionar README com informações do backup
                readme_content = f"""Backup do Sistema ERP
Data: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Arquivo do banco: {os.path.basename(self.source_db)}
Tamanho: {os.path.getsize(self.source_db) / (1024*1024):.2f} MB
"""
                zipf.writestr("README.txt", readme_content)
                self.progress_changed.emit(90)
            
            self.progress_changed.emit(100)
            self.backup_completed.emit(full_backup_path)
            
        except Exception as e:
            self.backup_error.emit(f"Erro ao criar backup: {str(e)}")


class BackupDialog(QDialog):
    """Diálogo para realizar backup do sistema ao fechar"""
    BackupConfig = BackupConfig 
    backup_realizado = pyqtSignal(str)  # Sinal emitido quando backup é feito
    fechar_sem_backup = pyqtSignal()    # Sinal para fechar sem backup
    
    def __init__(self, parent=None, force_show=False):
        """
        Inicializa o diálogo de backup.
        
        Args:
            parent: Widget pai
            force_show: Se True, mostra o diálogo independentemente da data do último backup
        """
        super().__init__(parent)
        self.db_path = "erp.db"  # Caminho padrão do banco de dados
        self.backup_thread = None
        self.force_show = force_show  # Flag para forçar exibição
        
        # Carregar último caminho salvo
        self.destination_folder = BackupConfig.get_last_path()
        
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
        
        return BackupConfig.should_show_backup_dialog(days_threshold=7)
    
    def _get_days_since_last_backup(self):
        """Retorna quantos dias se passaram desde o último backup"""
        last_backup_date = BackupConfig.get_last_backup_date()
        
        if last_backup_date is None:
            return None  # Nunca foi feito backup
        
        return (datetime.now() - last_backup_date).days
    
    def _init_ui(self):
        """Inicializa interface do diálogo"""
        self.setWindowTitle("Backup do Sistema")
        self.setMinimumSize(500, 500)  # Menor altura sem a barra de progresso
        self.setWindowIcon(QIcon("icon.ico") if os.path.exists("icon.ico") else QIcon())
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        titulo = QLabel("BACKUP")
        titulo.setProperty("class", "title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1A4968;")
        layout.addWidget(titulo)
        
        # Mensagem informativa
        last_backup_info = self._get_last_backup_info()
        mensagem_text = (
            "O sistema será fechado. Deseja realizar backup do banco de dados antes de sair?\n\n"
            "É recomendado fazer backup regularmente para evitar perda de dados."
        )
        
        if last_backup_info:
            mensagem_text += f"\n\n{last_backup_info}"
        
        mensagem = QLabel(mensagem_text)
        mensagem.setWordWrap(True)
        mensagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mensagem)
        
        layout.addSpacing(10)
        
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
        
        self.caminho_label = QLabel(f"<b>Pasta selecionada:</b> {self.destination_folder}")
        self.caminho_label.setWordWrap(True)
        self.caminho_label.setStyleSheet("padding: 8px; background-color: #404040; border-radius: 4px;")
        destino_layout.addWidget(self.caminho_label)
        
        # Botão para selecionar pasta
        btn_pasta = QPushButton("Selecionar Pasta...")
        btn_pasta.clicked.connect(self._selecionar_pasta)
        destino_layout.addWidget(btn_pasta, alignment=Qt.AlignmentFlag.AlignCenter)
        
        destino_group.setLayout(destino_layout)
        layout.addWidget(destino_group)
        
        # Mensagem de status (sem barra de progresso)
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Botões
        button_layout = QHBoxLayout()
        
        # Botão Fechar sem Backup
        self.btn_fechar = QPushButton("Fechar sem Backup")
        self.btn_fechar.clicked.connect(self._fechar_sem_backup)
        self.btn_fechar.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        # Botão Realizar Backup
        self.btn_backup = QPushButton("Realizar Backup")
        self.btn_backup.clicked.connect(self._iniciar_backup)
        self.btn_backup.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        button_layout.addWidget(self.btn_fechar)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_backup)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _get_last_backup_info(self):
        """Retorna informações sobre o último backup"""
        last_backup_date = BackupConfig.get_last_backup_date()
        
        if last_backup_date is None:
            return "⚠️ Nunca foi feito backup do sistema!"
        
        days_since = self._get_days_since_last_backup()
        
        if days_since is not None:
            if days_since == 0:
                return "✅ Backup realizado hoje"
            elif days_since == 1:
                return "✅ Backup realizado ontem"
            elif days_since < 7:
                return f"✅ Backup realizado há {days_since} dias"
            else:
                return f"⚠️ O último backup foi há {days_since} dias (recomenda-se fazer backup a cada 7 dias)"
        
        return ""
    
    def _centralizar_janela(self):
        """Centraliza a janela na tela"""
        # Força o cálculo do tamanho da janela
        self.adjustSize()
        
        # Obtém a geometria da tela
        screen = QGuiApplication.primaryScreen().geometry()
        
        # Calcula a posição central
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        
        # Move a janela para a posição calculada
        self.move(x, y)
    
    def _selecionar_pasta(self):
        """Abre diálogo para selecionar pasta de destino"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para Backup",
            self.destination_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.destination_folder = folder
            self.caminho_label.setText(f"<b>Pasta selecionada:</b> {self.destination_folder}")
            # Salvar o novo caminho
            BackupConfig.save_last_path(folder)
    
    def _fechar_sem_backup(self):
        """Fecha o programa sem fazer backup"""
        days_since = self._get_days_since_last_backup()
        
        warning_msg = "Tem certeza que deseja fechar sem fazer backup?\n\n"
        
        if days_since is None:
            warning_msg += "⚠️ NUNCA foi feito backup do sistema!\nQualquer dado poderá ser perdido permanentemente."
        elif days_since >= 7:
            warning_msg += f"⚠️ O último backup foi há {days_since} dias.\nQualquer dado não salvo poderá ser perdido."
        else:
            warning_msg += "Qualquer dado não salvo poderá ser perdido."
        
        reply = QMessageBox.question(
            self,
            "Confirmar Fechamento",
            warning_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.fechar_sem_backup.emit()
            self.accept()
    
    def _iniciar_backup(self):
        """Inicia o processo de backup"""
        # Validar se o arquivo do banco existe
        if not os.path.exists(self.db_path):
            QMessageBox.critical(
                self,
                "Erro",
                f"Arquivo do banco de dados não encontrado:\n{self.db_path}"
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
                    f"Não foi possível criar a pasta de destino:\n{str(e)}"
                )
                return
        
        # Salvar o caminho atual (caso tenha sido alterado mas não salvo)
        BackupConfig.save_last_path(self.destination_folder)
        
        # Desabilitar botões durante o backup
        self.btn_backup.setEnabled(False)
        self.btn_fechar.setEnabled(False)
        
        # Mostrar status de processamento
        self.status_label.setVisible(True)
        self.status_label.setText("⏳ Criando backup...")
        self.status_label.setStyleSheet("color: #007bff; font-weight: bold; font-size: 14px;")
        
        # Criar e iniciar thread de backup
        self.backup_thread = BackupThread(self.db_path, self.destination_folder)
        self.backup_thread.backup_completed.connect(self._backup_concluido)
        self.backup_thread.backup_error.connect(self._backup_erro)
        self.backup_thread.start()
    
    def _backup_concluido(self, backup_path):
        """Chamado quando o backup é concluído com sucesso"""
        # Salvar a data do backup
        BackupConfig.save_last_backup_date()
        
        self.status_label.setText("✅ Backup concluído com sucesso!")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold; font-size: 14px;")
        
        # Atualizar informações sobre o último backup
        last_backup_info = self._get_last_backup_info()
        
        # Mostrar mensagem de confirmação
        QMessageBox.information(
            self,
            "Backup Concluído",
            f"Backup realizado com sucesso!\n\n"
            f"Arquivo: {os.path.basename(backup_path)}\n"
            f"Local: {os.path.dirname(backup_path)}\n\n"
            f"{last_backup_info}"
        )
        
        # Emitir sinal de backup realizado
        self.backup_realizado.emit(backup_path)
        
        # Fechar diálogo
        self.accept()
    
    def _backup_erro(self, mensagem_erro):
        """Chamado quando ocorre erro no backup"""
        # Habilitar botões novamente
        self.btn_backup.setEnabled(True)
        self.btn_fechar.setEnabled(True)
        
        # Esconder status
        self.status_label.setVisible(False)
        
        QMessageBox.critical(
            self,
            "Erro no Backup",
            f"Ocorreu um erro durante o backup:\n\n{mensagem_erro}"
        )
    
    def _abrir_pasta(self, backup_path):
        """Abre a pasta onde o backup foi salvo"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(os.path.dirname(backup_path))
            elif os.name == 'posix':  # Linux/Mac
                import subprocess
                subprocess.Popen(['xdg-open', os.path.dirname(backup_path)])
        except Exception as e:
            QMessageBox.warning(
                self,
                "Aviso",
                f"Não foi possível abrir a pasta:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """Intercepta o fechamento da janela"""
        if self.backup_thread and self.backup_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Backup em Andamento",
                "O backup ainda está em andamento. Deseja cancelar e fechar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.backup_thread.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()