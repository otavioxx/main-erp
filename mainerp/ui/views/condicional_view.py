import logging

from PyQt6.QtWidgets import (
    QWidget,
)

from mainerp.data.models.condicional import Condicional
from mainerp.domain.utils.helpers import (
    criar_pasta_se_nao_existir,
    validar_data,
)
from mainerp.ui.listagem_modelo import configurar_modelo
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin

from .condicional_view_actions import _CondicionalViewActions
from .condicional_view_filters import _CondicionalViewFilters
from .condicional_view_layout import _CondicionalViewLayout
from .condicional_view_reports import _CondicionalViewReports

logger = logging.getLogger(__name__)


class CondicionalView(
    _CondicionalViewLayout,
    _CondicionalViewFilters,
    _CondicionalViewActions,
    _CondicionalViewReports,
    TableScrollNavigationMixin,
    QWidget,
):
    """Interface de gestão de condicionais otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.cliente_filtro = None
        self.dados = []
        self._init_ui()
        configurar_modelo(
            self,
            self.tabela_condicionais,
            self.busca_cliente,
            [
                (self.btn_nova_condicional, "plus", "Ctrl+N"),
                (self.btn_editar_condicional, "pencil", "Ctrl+E"),
                (self.btn_converter_venda, "arrow-right-left", None),
                (self.btn_marcar_devolvida, "check", None),
                (self.btn_excluir, "trash-2", None),
                (self.btn_imprimir, "printer", "Ctrl+P"),
                (self.btn_exportar, "printer", None),
            ],
        )
        self._carregar_condicionais()
        criar_pasta_se_nao_existir("relatorios")

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def carregar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._carregar_condicionais()

    def filtrar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_condicionais()

    def limpar_filtros(self):
        """Método público para compatibilidade com código existente"""
        self._limpar_filtros()

    def selecionar_cliente(self):
        """Método público para compatibilidade com código existente"""
        self._selecionar_cliente()

    def abrir_nova_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._abrir_nova_condicional()

    def get_condicional_selecionada(self):
        """Método público para compatibilidade com código existente"""
        return self._get_condicional_selecionada()

    def editar_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._editar_condicional()

    def converter_em_venda(self):
        """Método público para compatibilidade com código existente"""
        self._converter_em_venda()

    def marcar_como_devolvida(self):
        """Método público para compatibilidade com código existente"""
        self._marcar_como_devolvida()

    def excluir_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._excluir_condicional()

    def exportar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._exportar_condicionais()

    def imprimir_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._imprimir_condicional()

    def atualizar_tabela(self):
        """Método público para atualizar a tabela de condicionais"""
        self._carregar_condicionais()

    def get_condicional_by_row(self, row):
        """Obtém a condicional pelo índice da linha na tabela"""
        try:
            condicional_id_item = self.tabela_condicionais.item(row, 0)
            if condicional_id_item is None:
                return None

            condicional_id = int(condicional_id_item.text())
            return Condicional.buscar_por_id(condicional_id)
        except (ValueError, AttributeError):
            return None

    # ========== MÉTODOS UTILITÁRIOS LEGADOS ==========

    def validar_data(self, data_str):
        """Método de compatibilidade - usa a função utilitária"""
        return validar_data(data_str)

    def converter_data(self, data_str):
        """Método de compatibilidade"""
        return self._converter_data(data_str)

    def aplicar_estilo_linha(self, row, condicional):
        """Método de compatibilidade"""
        self._aplicar_estilo_linha(row, condicional)

    def get_nome_cliente(self, cliente_id):
        """Método público para compatibilidade"""
        return self._get_nome_cliente(cliente_id)

    def criar_pasta_relatorios(self):
        """Método de compatibilidade - usa helper"""
        criar_pasta_se_nao_existir("relatorios")

    def limpar_pasta_relatorios(self):
        """Limpa todos os arquivos da pasta de relatórios"""
        try:
            import os

            if os.path.exists("relatorios"):
                for arquivo in os.listdir("relatorios"):
                    caminho_arquivo = os.path.join("relatorios", arquivo)
                    try:
                        if os.path.isfile(caminho_arquivo):
                            os.unlink(caminho_arquivo)
                        logger.debug(
                            "Arquivo de relatório removido: %s", caminho_arquivo
                        )
                    except Exception:
                        logger.exception(
                            "Erro ao remover arquivo de relatório %s", caminho_arquivo
                        )
        except Exception:
            logger.exception("Erro ao limpar pasta de relatórios")

    # ========== PROPRIEDADES PARA COMPATIBILIDADE ==========

    @property
    def init_ui(self):
        """Método legado - redirecionado para _init_ui"""
        return self._init_ui
