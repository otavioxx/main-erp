"""
Dialog de Pedido - Modificado para incluir desconto e campos Cor, Tamanho, Referência - CORRIGIDO
Com suporte a redimensionamento inteligente via DialogSizeMixin
E verificação de modificações não salvas
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMessageBox,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.domain.utils.helpers import (
    aplicar_maiuscula_formulario,
)
from mainerp.ui.mixins.dialog_size_mixin import DialogSizeMixin
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin

from .pedido_dialog_items import _PedidoDialogItems
from .pedido_dialog_layout import _PedidoDialogLayout
from .pedido_dialog_persistence import _PedidoDialogPersistence


class PedidoDialog(
    _PedidoDialogLayout,
    _PedidoDialogItems,
    _PedidoDialogPersistence,
    DialogSizeMixin,
    TableScrollNavigationMixin,
    QDialog,
):
    """Dialog para criação/edição de pedidos com redimensionamento inteligente"""

    pedido_realizado = pyqtSignal()

    def __init__(self, parent=None, pedido=None):
        super().__init__(parent)
        self.produtos_selecionados = []
        self.fornecedor_selecionado = None
        self.valor_frete = 0.0
        self.valor_desconto = 0.0
        self.pedido_editando = pedido
        self.observacao = ""
        self._primeira_exibicao = True
        self._modificacoes_nao_salvas = False  # NOVO: controle de modificações
        self._init_ui()
        aplicar_maiuscula_formulario(self)
        self._configurar_tamanho_dialog()
        self._carregar_dados_existentes()

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
                # Tenta finalizar o pedido
                try:
                    self._finalizar_pedido()
                    event.accept()  # Fecha após salvar
                except Exception as e:
                    registrar_excecao(
                        __name__,
                        "Exception handled in PedidoDialog.closeEvent in dialogs/pedido_dialog.py",
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
            self.fornecedor_selecionado is not None
            and len(self.produtos_selecionados) > 0
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
            default_height_percent=0.80,  # 90% da tela
            max_width_percent=0.85,  # Máximo 95% da tela
            max_height_percent=0.85,  # Máximo 95% da tela
        )

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def init_ui(self):
        """Método público para compatibilidade"""
        self._init_ui()

    def definir_frete(self):
        """Método público para compatibilidade - MODIFICADO"""
        self._definir_frete_desconto()

    def selecionar_fornecedor(self):
        """Método público para compatibilidade"""
        self._selecionar_fornecedor()

    def selecionar_produto(self):
        """Método público para compatibilidade"""
        self._selecionar_produto()

    def abrir_observacao(self):
        """Método público para compatibilidade"""
        self._abrir_observacao()

    def processar_produto(self, produto):
        """Método público para compatibilidade"""
        self._processar_produto(produto)

    def adicionar_produto(self, produto, preco_custo, quantidade, preco_venda=None):
        """Método público para compatibilidade - MODIFICADO"""
        if preco_venda is None:
            preco_venda = preco_custo * 1.3  # Margem padrão de 30%
        self._adicionar_produto(produto, preco_custo, preco_venda, quantidade)

    def remover_produto(self):
        """Método público para compatibilidade"""
        self._remover_produto()

    def calcular_total(self):
        """Método público para compatibilidade"""
        self._calcular_total()

    def atualizar_tabela(self):
        """Método público para compatibilidade"""
        self._atualizar_tabela()

    def verificar_habilitar_finalizacao(self):
        """Método público para compatibilidade"""
        self._verificar_habilitar_finalizacao()

    def finalizar_pedido(self):
        """Método público para compatibilidade"""
        self._finalizar_pedido()

    def carregar_dados_existentes(self):
        """Método público para compatibilidade"""
        self._carregar_dados_existentes()
