"""
Dialog de Condicional - Versão com Frame de Entrada Rápida - LAYOUT AJUSTADO
Com suporte a redimensionamento inteligente via DialogSizeMixin
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.cliente import Cliente
from mainerp.domain.utils.helpers import (
    aplicar_maiuscula_formulario,
)
from mainerp.ui.mixins.dialog_size_mixin import DialogSizeMixin
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin

from .condicional_dialog_entry import _CondicionalDialogQuickEntry
from .condicional_dialog_layout import _CondicionalDialogLayout
from .condicional_dialog_operations import _CondicionalDialogOperations


class CondicionalDialog(
    _CondicionalDialogLayout,
    _CondicionalDialogQuickEntry,
    _CondicionalDialogOperations,
    DialogSizeMixin,
    TableScrollNavigationMixin,
    QDialog,
):
    """Dialog para criação de condicionais com frame de entrada rápida e redimensionamento inteligente"""

    condicional_salva = pyqtSignal()

    def __init__(self, condicional_id=None, parent=None):
        super().__init__(parent)
        self.condicional_id = condicional_id
        self.produtos_selecionados = []
        self.cliente_selecionado: Cliente | None = None
        self.desconto_total = 0.0
        self.observacao = ""
        self._primeira_exibicao = True
        self._modificacoes_nao_salvas = False
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._configurar_tamanho_dialog()
        self._configurar_comportamento_enter()
        self._carregar_dados()

    def showEvent(self, event):
        """Chamado quando a janela é exibida - garante centralização"""
        super().showEvent(event)

        # Na primeira exibição, centralizar a janela
        if self._primeira_exibicao:
            self._primeira_exibicao = False
            # Usar QApplication para forçar processamento de eventos
            QApplication.processEvents()
            # Agora centralizar
            self._center_on_screen()

    def closeEvent(self, event):
        """NOVIDADE: Pergunta se deseja salvar antes de fechar"""
        # Se há modificações não salvas, perguntar ao usuário
        if self._modificacoes_nao_salvas and self._tem_dados_para_salvar():
            reply = QMessageBox.question(
                self,
                "Modificações não salvas",
                "Você tem modificações não salvas. Deseja salvar antes de sair?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                # Tenta salvar
                try:
                    self._salvar_condicional()
                    event.accept()  # Fecha após salvar
                except Exception as e:
                    registrar_excecao(
                        __name__,
                        "Exception handled in CondicionalDialog.closeEvent in dialogs/condicional_dialog.py",
                    )
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {e!s}"
                    )
                    event.ignore()  # Não fecha se houver erro
                    return

            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()  # Descarta modificações e fecha

            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()  # Cancela o fechamento
                return

        super().closeEvent(event)

    def _tem_dados_para_salvar(self):
        """Verifica se há dados que podem ser salvos"""
        return (
            self.cliente_selecionado is not None and len(self.produtos_selecionados) > 0
        )

    def _marcar_como_modificado(self):
        """Marca que houve modificações não salvas"""
        self._modificacoes_nao_salvas = True
        self._atualizar_indicador_modificacoes()

    def _configurar_tamanho_dialog(self):
        """Configura o tamanho inteligente do diálogo usando o mixin"""
        self.setup_dialog_size(
            min_width=700,  # Largura mínima adequada para a tabela
            min_height=500,  # Altura mínima para ter espaço suficiente
            default_width_percent=0.95,  # 85% da tela
            default_height_percent=0.85,  # 90% da tela (aumentado para tabela maior)
            max_width_percent=0.85,  # Máximo 95% da tela
            max_height_percent=0.90,  # Máximo 95% da tela (aumentado)
        )

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método legado - redirecionado para _init_ui"""
        return self._init_ui()

    def selecionar_cliente(self):
        """Método público para compatibilidade"""
        self._selecionar_cliente()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def abrir_observacao(self):
        """Método público para compatibilidade"""
        self._abrir_observacao()

    def processar_produto(self, produto):
        """Método público para compatibilidade"""
        self._processar_produto(produto)

    def adicionar_produto(self, produto, quantidade):
        """Método público para compatibilidade"""
        self._adicionar_produto(produto, quantidade)

    def remover_produto(self):
        """Método público para compatibilidade"""
        self._remover_produto()

    def aplicar_desconto(self):
        """Método público para compatibilidade"""
        self._aplicar_desconto()

    def calcular_total(self):
        """Método público para compatibilidade"""
        self._calcular_total()

    def atualizar_tabela(self):
        """Método público para compatibilidade"""
        self._atualizar_tabela()

    def carregar_dados(self):
        """Método público para compatibilidade"""
        self._carregar_dados()

    def salvar_condicional(self):
        """Método público para compatibilidade"""
        self._salvar_condicional()
