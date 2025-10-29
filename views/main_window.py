from PyQt6.QtWidgets import (QMainWindow, QLabel, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QButtonGroup, QFrame,
                             QStackedWidget, QStatusBar)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
import platform
import psutil
from datetime import datetime
import os
from database import Database

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
        self.label_version = QLabel("Digital Solutios - MainERP v0.03")
        self.label_version.setStyleSheet("color: #999; font-size: 11px;")
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

        # Estilo da status bar - adaptado ao tema claro
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #d0d0d0;
                font-size: 12px;
                color: #333;
            }
            QStatusBar::item {
                border: none;
            }
        """)

    def _criar_barra_navegacao(self):
        """Cria a barra de navegação vertical"""
        nav_frame = QFrame()
        nav_frame.setProperty("class", "nav-bar")
        nav_frame.setFixedWidth(200)  # Largura fixa para a barra lateral
        nav_frame.setStyleSheet("""
            QFrame.nav-bar {
                background-color: #f9f9f9;
                border-right: 1px solid #e0e0e0;
            }
        """)

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setSpacing(5)
        nav_layout.setContentsMargins(5, 15, 5, 15)

        # Título da aplicação
        titulo = QLabel("MainERP")
        titulo.setProperty("class", "nav-title")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            QLabel.nav-title {
                font-size: 40px;
                font-weight: bold;
                color: #1A4968;
                padding: 10px;
                border-bottom: 2px solid #e0e0e0;
                margin-bottom: 10px;
            }
        """)
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
            btn.setStyleSheet("""
                QPushButton.nav-button {
                    background-color: transparent;
                    color: #666;
                    border: none;
                    padding: 12px 8px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 4px;
                }
                QPushButton.nav-button:hover {
                    background-color: #eeeeee;
                    color: #1a1a1a;
                }
                QPushButton.nav-button:checked {
                    background-color: #1A4968;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton.nav-button:pressed {
                    background-color: #0c5991;
                }
            """)
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
            print("Conversão para maiúscula ativada globalmente!")
        except Exception as e:
            print(f"Erro ao configurar maiúscula global: {e}")

    def closeEvent(self, event):
        """Limpa timers ao fechar a aplicação"""
        if hasattr(self, 'status_widget'):
            timers_to_stop = [
                'timer_datetime', 'timer_keys', 'timer_system', 'timer_db'
            ]
            for timer_name in timers_to_stop:
                if hasattr(self.status_widget, timer_name):
                    timer = getattr(self.status_widget, timer_name)
                    if timer.isActive():
                        timer.stop()

        event.accept()