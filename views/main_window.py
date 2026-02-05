from PyQt6.QtWidgets import (QMainWindow, QLabel, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QDialog, QApplication, QButtonGroup, QFrame,
                             QStackedWidget, QStatusBar)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import platform
import psutil
from datetime import datetime
import os
from database import Database

from dialogs.backup_dialog import BackupDialog
from views.cliente_view import ClienteView
from views.produto_view import ProdutoView
from views.fornecedor_view import FornecedorView
from views.venda_view import VendaView
from views.recebimento_view import RecebimentoView
from views.condicional_view import CondicionalView
from views.config_view import ConfigView
from dialogs.venda_dialog import ProdutoVendaDialog
from views.pedido_view import PedidoView

from utils.helpers import aplicar_maiuscula_formulario

class StatusBarWidget(QWidget):
    """Widget personalizado para a status bar com múltiplas informações"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Estados anteriores das teclas para detectar mudanças
        self.caps_state_anterior = None
        self.num_state_anterior = None
        self.init_ui()

    def init_ui(self):
        """Inicializa a interface da status bar"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(15)

        # Versão da aplicação
        self.label_version = QLabel("Digital Solutions - MainERP v0.03")
        self.label_version.setProperty("class", "version-label")
        layout.addWidget(self.label_version)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MainERP")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Barra lateral de navegação
        self.nav_bar = self._criar_barra_navegacao()
        main_layout.addWidget(self.nav_bar)

        # Área de conteúdo
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Widget empilhado para as views
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(content_widget, 1)  # 1 = stretch factor

        # Criar todas as views
        self._criar_views()

        # Criar status bar
        self._criar_status_bar()

        self.configurar_maiuscula_global()

        # Selecionar a primeira aba por padrão
        self._selecionar_aba(0)

        self.showMaximized()

    def _criar_status_bar(self):
        """Cria a barra de status personalizada"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Widget personalizado para a status bar
        self.status_widget = StatusBarWidget(self)

        # Adicionar o widget personalizado à status bar
        self.status_bar.addPermanentWidget(self.status_widget, 1)

        # REMOVA O STYLESHEET INLINE - será aplicado pelo tema
        # Apenas defina classes para estilização via CSS
        self.status_bar.setProperty("class", "main-statusbar")
        self.status_widget.setProperty("class", "statusbar-widget")

    def _criar_barra_navegacao(self):
        """Cria a barra de navegação vertical"""
        nav_frame = QFrame()
        nav_frame.setProperty("class", "sidebar")
        nav_frame.setFixedWidth(220)  # Largura fixa para a barra lateral
        
        # REMOVA O STYLESHEET INLINE - será aplicado pelo tema
        # Apenas defina classes para estilização via CSS
        
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setSpacing(5)
        nav_layout.setContentsMargins(5, 15, 5, 15)

        # Título da aplicação
        titulo = QLabel("MainERP")
        titulo.setProperty("class", "sidebar-title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # REMOVA O STYLESHEET INLINE
        nav_layout.addWidget(titulo)

        # Grupo de botões de navegação
        self.nav_button_group = QButtonGroup(self)
        self.nav_buttons = []

        # Ícones e textos para os botões
        nav_items = [
            ("🛒", "VENDAS"),
            ("💫", "CONDICIONAL"),
            ("📝", "PEDIDOS"),
            ("💰", "RECEBIMENTOS"),
            ("👤", "CLIENTES"),
            ("📦", "PRODUTOS"),
            ("🏭", "FORNECEDORES"),
            ("⚙️", "CONFIGURAÇÕES")
        ]

        for icon, text in nav_items:
            btn = QPushButton(f"{icon} {text}")
            btn.setProperty("class", "nav-button")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # REMOVA O STYLESHEET INLINE - será aplicado pelo tema
            self.nav_button_group.addButton(btn)
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)

        # Espaço flexível no final
        nav_layout.addStretch()

        return nav_frame

    def _criar_views(self):
        """Cria e adiciona todas as views ao stacked widget"""
        self.venda_view = VendaView()
        self.condicional_view = CondicionalView()
        self.pedido_view = PedidoView()
        self.recebimento_view = RecebimentoView()
        self.cliente_view = ClienteView()
        self.produto_view = ProdutoView()
        self.fornecedor_view = FornecedorView()
        self.config_view = ConfigView()

        # Adicionar views ao stacked widget
        self.stacked_widget.addWidget(self.venda_view)
        self.stacked_widget.addWidget(self.condicional_view)
        self.stacked_widget.addWidget(self.pedido_view)
        self.stacked_widget.addWidget(self.recebimento_view)
        self.stacked_widget.addWidget(self.cliente_view)
        self.stacked_widget.addWidget(self.produto_view)
        self.stacked_widget.addWidget(self.fornecedor_view)
        self.stacked_widget.addWidget(self.config_view)

        # Conectar botões de navegação
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self._selecionar_aba(idx))

    def _selecionar_aba(self, index):
        """Seleciona a aba pelo índice"""
        # Atualizar botão de navegação
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

        # Atualizar conteúdo
        self.stacked_widget.setCurrentIndex(index)

        # Executar ações específicas da aba
        current_view = self.stacked_widget.currentWidget()

        if current_view == self.recebimento_view:
            self.recebimento_view.carregar_duplicatas()
        elif current_view == self.produto_view:
            self.produto_view.carregar_dados()
        elif current_view == self.venda_view:
            self.venda_view.carregar_vendas()
        elif current_view == self.cliente_view:
            self.cliente_view.carregar_dados()
        elif current_view == self.fornecedor_view:
            self.fornecedor_view.carregar_dados()
        elif current_view == self.pedido_view:
            self.pedido_view.carregar_dados()

    def configurar_maiuscula_global(self):
        """Aplica conversão automática para maiúscula em toda a aplicação"""
        try:
            aplicar_maiuscula_formulario(self)
        except Exception as e:
            print(f"Erro ao configurar maiúscula global: {e}")

    def closeEvent(self, event):
        """Fecha o sistema, mostrando diálogo de backup apenas se necessário"""
        # Limpa timers
        if hasattr(self, 'status_widget'):
            timers_to_stop = [
                'timer_datetime', 'timer_keys', 'timer_system', 'timer_db'
            ]
            for timer_name in timers_to_stop:
                if hasattr(self.status_widget, timer_name):
                    timer = getattr(self.status_widget, timer_name)
                    if timer.isActive():
                        timer.stop()
        
        # Impede fechamento automático
        event.ignore()
        
        # VERIFICAÇÃO DA DATA DO ÚLTIMO BACKUP
        # Se backup foi feito nos últimos 7 dias, fecha direto sem mostrar nada
        if not BackupDialog.should_show_dialog():
            # Último backup foi recente (menos de 7 dias)
            # Fecha a aplicação SILENCIOSAMENTE
            print("✅ Backup recente detectado, fechando sistema...")
            QApplication.instance().quit()
            return
        
        # Se backup antigo (7+ dias) ou nunca feito, mostra diálogo
        self._mostrar_dialogo_backup()

    def _mostrar_dialogo_backup(self):
        """Mostra o diálogo de backup (apenas quando necessário)"""
        try:
            # Criar diálogo de backup
            backup_dialog = BackupDialog(self)
            backup_dialog.setWindowTitle(f"Backup - {self.windowTitle()}")
            
            # Conectar sinais
            backup_dialog.backup_realizado.connect(self._backup_concluido)
            backup_dialog.fechar_sem_backup.connect(self._fechar_sem_backup)
            
            # Mostrar diálogo modalmente
            result = backup_dialog.exec()
            
            # Verificar o resultado
            if result == QDialog.DialogCode.Accepted:
                # Backup foi feito e diálogo fechado automaticamente
                QApplication.instance().quit()
            elif result == QDialog.DialogCode.Rejected:
                # Usuário clicou em "Fechar sem Backup"
                QApplication.instance().quit()
                
        except Exception as e:
            print(f"Erro ao mostrar diálogo de backup: {e}")
            # Fallback: perguntar se quer fechar mesmo assim
            self._perguntar_fechamento_direto()

    def _backup_concluido(self, backup_path):
        """Chamado quando backup é concluído com sucesso"""
        print(f"✅ Backup criado com sucesso: {backup_path}")
        
        # Aqui você pode adicionar log no sistema
        try:
            from datetime import datetime
            log_msg = f"Backup realizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} - {backup_path}"
            
            # Salvar log se tiver um sistema de logs
            if hasattr(self, 'salvar_log'):
                self.salvar_log('backup', log_msg)
                
        except Exception as e:
            print(f"Erro ao registrar backup: {e}")

    def _fechar_sem_backup(self):
        """Chamado quando usuário escolhe fechar sem backup"""
        
        # Aqui você pode adicionar log no sistema
        try:
            from datetime import datetime
            log_msg = f"Sistema fechado sem backup: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            if hasattr(self, 'salvar_log'):
                self.salvar_log('sistema', log_msg)
                
        except Exception as e:
            print(f"Erro ao registrar fechamento: {e}")