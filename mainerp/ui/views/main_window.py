import logging
from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from mainerp.core.config import obter_config
from mainerp.data.automatic_backup import BackupAutomatico
from mainerp.domain.utils.helpers import aplicar_maiuscula_formulario
from mainerp.ui.dialogs.backup_dialog import BackupConfig, BackupDialog
from mainerp.ui.dialogs.sobre_atualizacoes_dialog import SobreAtualizacoesDialog
from mainerp.ui.views.cliente_view import ClienteView
from mainerp.ui.views.condicional_view import CondicionalView
from mainerp.ui.views.config_view import ConfigView
from mainerp.ui.views.fornecedor_view import FornecedorView
from mainerp.ui.views.pedido_view import PedidoView
from mainerp.ui.views.produto_view import ProdutoView
from mainerp.ui.views.recebimento_view import RecebimentoView
from mainerp.ui.views.venda_view import VendaView

logger = logging.getLogger(__name__)


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
        self.label_version = QLabel(
            f"© Digital Solutions - MainERP v{obter_config().APP_VERSION}"
        )
        self.label_version.setProperty("class", "version-label")
        layout.addWidget(self.label_version)


class MainWindow(QMainWindow):
    # Sinal para quando backup é realizado
    backup_realizado = pyqtSignal(str)

    def __init__(
        self, progress_callback: Callable[[str], None] | None = None
    ):
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
        self._criar_views(progress_callback)

        # Criar status bar
        self._criar_status_bar()

        self.configurar_maiuscula_global()

        # Selecionar a primeira aba por padrão
        self._selecionar_aba(0)

        self._aguardando_backup_automatico = False
        self.backup_automatico = BackupAutomatico(
            obter_config().obter_caminho_banco(), self
        )
        self.backup_automatico.backup_concluido.connect(
            self._backup_automatico_concluido
        )
        self.backup_automatico.backup_falhou.connect(self._backup_automatico_falhou)
        self.backup_automatico.operacao_finalizada.connect(
            self._retomar_fechamento_apos_backup
        )
        self.backup_automatico.iniciar()

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
            ("⚙️", "CONFIGURAÇÕES"),
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

        self.about_updates_button = QPushButton("ℹ️ SOBRE / ATUALIZAÇÕES")
        self.about_updates_button.setProperty("class", "nav-button")
        self.about_updates_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.about_updates_button.clicked.connect(self._mostrar_sobre_atualizacoes)
        nav_layout.addWidget(self.about_updates_button)

        return nav_frame

    def _mostrar_sobre_atualizacoes(self):
        dialog = SobreAtualizacoesDialog(self)
        dialog.exec()

    def _criar_views(
        self, progress_callback: Callable[[str], None] | None = None
    ):
        """Cria e adiciona as views, notificando o progresso de cada tela."""
        def informar_progresso(indice: int, nome: str):
            if progress_callback:
                progress_callback(f"Carregando tela {indice}/8: {nome}...")

        informar_progresso(1, "Vendas")
        self.venda_view = VendaView()
        informar_progresso(2, "Condicionais")
        self.condicional_view = CondicionalView()
        informar_progresso(3, "Pedidos")
        self.pedido_view = PedidoView()
        informar_progresso(4, "Recebimentos")
        self.recebimento_view = RecebimentoView()
        informar_progresso(5, "Clientes")
        self.cliente_view = ClienteView()
        informar_progresso(6, "Produtos")
        self.produto_view = ProdutoView()
        informar_progresso(7, "Fornecedores")
        self.fornecedor_view = FornecedorView()
        informar_progresso(8, "Configurações")
        self.config_view = ConfigView()

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
        except Exception:
            logger.exception("Erro ao configurar maiúscula global")

    def closeEvent(self, event):
        """Fecha o sistema, mostrando diálogo de backup apenas se necessário"""
        if self.backup_automatico.em_execucao:
            event.ignore()
            if not self._aguardando_backup_automatico:
                self._aguardando_backup_automatico = True
                self.status_bar.showMessage(
                    "Aguarde a conclusão do backup automático para fechar..."
                )
            return

        self.backup_automatico.parar()

        # Limpa timers
        if hasattr(self, "status_widget"):
            timers_to_stop = [
                "timer_datetime",
                "timer_keys",
                "timer_system",
                "timer_db",
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
            logger.info("Backup recente detectado; fechando sistema")
            app = QApplication.instance()
            if app is not None:
                app.quit()
            return

        # Se backup antigo (7+ dias) ou nunca feito, mostra diálogo
        self._mostrar_dialogo_backup()

    def _backup_automatico_concluido(self, caminho: str):
        self.status_bar.showMessage(
            f"Backup automático salvo: {caminho}", 10000
        )

    def _backup_automatico_falhou(self, erro: str):
        logger.error("Backup automático não foi concluído: %s", erro)
        self.status_bar.showMessage(f"Falha no backup automático: {erro}", 15000)

    def _retomar_fechamento_apos_backup(self):
        if not self._aguardando_backup_automatico:
            return
        self._aguardando_backup_automatico = False
        self.close()

    def _mostrar_dialogo_backup(self):
        """Mostra o diálogo de backup (apenas quando necessário)"""
        try:
            # Criar diálogo de backup
            backup_dialog = BackupDialog(self)
            backup_dialog.setWindowTitle(f"Backup - {self.windowTitle()}")

            # Conectar sinal de backup realizado
            backup_dialog.backup_realizado.connect(self._backup_concluido)

            # Mostrar diálogo modalmente
            result = backup_dialog.exec()

            # VERIFICAÇÃO EXPLÍCITA: Se o diálogo foi aceito, fecha o sistema
            if result == QDialog.DialogCode.Accepted:
                logger.info("Backup concluído; fechando sistema")
                app = QApplication.instance()
                if app is not None:
                    app.quit()

        except Exception:
            logger.exception("Erro ao mostrar diálogo de backup")
            self._perguntar_fechamento_emergencial()

    def _backup_concluido(self, backup_path):
        """Chamado quando o backup é concluído com sucesso"""
        # Salvar a data do backup
        BackupConfig.save_last_backup_date()

        # Não tenta acessar status_label que não existe
        # Opcional: mostrar mensagem na status bar
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage("✅ Backup concluído com sucesso!", 3000)

        # Emitir sinal de backup realizado (se necessário)
        self.backup_realizado.emit(backup_path)

        # O fechamento do sistema será feito no método _mostrar_dialogo_backup
        # após verificar o resultado do diálogo

    def _perguntar_fechamento_emergencial(self):
        """Fallback: pergunta se quer fechar sem backup (apenas em caso de erro no diálogo)"""
        reply = QMessageBox.question(
            self,
            "Erro no Backup",
            "Não foi possível abrir o diálogo de backup.\n\n"
            "Deseja fechar o sistema mesmo assim?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            app = QApplication.instance()
            if app is not None:
                app.quit()
