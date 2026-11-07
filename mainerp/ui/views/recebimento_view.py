"""
View de Recebimentos - Otimizada para performance
"""

import logging

from PyQt6.QtWidgets import (
    QMessageBox,
    QWidget,
)

from mainerp.domain.utils.export_utils import ExportUtils
from mainerp.domain.utils.helpers import (
    criar_pasta_se_nao_existir,
)
from mainerp.reports.print_comprovante_recebimento import PrintComprovanteRecebimento
from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin

from .recebimento_view_actions import _RecebimentoViewActions
from .recebimento_view_filters import _RecebimentoViewFilters
from .recebimento_view_layout import _RecebimentoViewLayout

logger = logging.getLogger(__name__)


class RecebimentoView(
    _RecebimentoViewLayout,
    _RecebimentoViewFilters,
    _RecebimentoViewActions,
    TableScrollNavigationMixin,
    QWidget,
):
    """View de gestão de recebimentos otimizada para performance"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cliente_filtro = None
        self.duplicatas_filtradas = []
        self.ultima_duplicata_paga = None
        self.todas_duplicatas = []
        self._parcelas_cache = {}  # Cache para total de parcelas
        self._loaded = False  # Flag para carregamento lazy
        self._init_ui()
        criar_pasta_se_nao_existir("relatorios")

    def showEvent(self, event):
        """Carrega dados apenas quando a view é exibida (lazy loading)"""
        if not self._loaded:
            self._carregar_duplicatas()
            self._loaded = True
        super().showEvent(event)

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def get_status_selecionado(self):
        """Método público para compatibilidade"""
        return self._get_status_selecionado()

    def selecionar_cliente(self):
        """Método público para compatibilidade"""
        dialog = ClienteSelectionDialog(self)
        if dialog.exec():
            cliente_selecionado = dialog.get_cliente_selecionado()
            if cliente_selecionado:
                self.busca_cliente.setText(cliente_selecionado.nome)

    def carregar_duplicatas(self):
        """Método público para compatibilidade"""
        self._carregar_duplicatas()

    def filtrar_duplicatas(self):
        """Método público para compatibilidade"""
        self._filtrar_duplicatas_otimizado()

    def exibir_duplicatas(self, duplicatas):
        """Método público para compatibilidade"""
        self._exibir_duplicatas_otimizado(duplicatas)

    def limpar_filtros(self):
        """Método público para compatibilidade"""
        self._limpar_filtros()

    def get_duplicata_selecionada(self):
        """Método público para compatibilidade"""
        return self._get_duplicata_selecionada()

    def receber_duplicata(self):
        """Método público para compatibilidade"""
        self._receber_duplicata()

    def processar_recebimento(
        self, duplicata, valor_recebido, data_recebimento, forma_pagamento
    ):
        """Método público para compatibilidade"""
        self._processar_recebimento_com_retorno(
            duplicata, valor_recebido, data_recebimento, forma_pagamento
        )

    def imprimir_comprovante(self, duplicata=None):
        """Método público para compatibilidade"""
        # Método simplificado para compatibilidade
        if duplicata is None:
            duplicata = self._get_duplicata_selecionada()

        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para imprimir")
            return

        # Lógica básica de impressão
        try:
            dados = {
                "id": duplicata[0],
                "venda_id": duplicata[2],
                "cliente_id": duplicata[1],
                "numero_parcela": duplicata[3],
                "valor_original": float(duplicata[4]),
                "valor_recebido": float(duplicata[4]),
                "data_vencimento": duplicata[5],
                "data_pagamento": duplicata[6] if len(duplicata) > 6 else None,
                "forma_pagamento": (
                    duplicata[11] if len(duplicata) > 11 else "Não informada"
                ),
                "cliente_nome": duplicata[8],
                "cpf_cnpj": "",
                "endereco": "",
                "venda_total": float(duplicata[9]) if len(duplicata) > 9 else 0,
                "data_venda": duplicata[10] if len(duplicata) > 10 else None,
            }

            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados, "relatorios"
            )
            if filename:
                ExportUtils.abrir_arquivo(filename)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao imprimir: {e!s}")

    def imprimir_relatorio(self):
        """Método público para compatibilidade"""
        self._imprimir_relatorio()

    def atualizar_apos_venda(self, cliente_id):
        """Atualiza após venda no crediário"""
        self._carregar_duplicatas()

    def atualizar_tabela_apos_recebimento(self, duplicata_id):
        """Atualiza tabela após recebimento"""
        self._carregar_duplicatas()

    def atualizar_tabela(self):
        """Método público para atualizar a tabela"""
        self._carregar_duplicatas()
