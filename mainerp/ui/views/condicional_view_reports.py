"""Componentes de CondicionalView."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QMessageBox,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.database import Database
from mainerp.domain.utils.export_utils import ExportUtils
from mainerp.reports.print_condicional import PrintCondicional
from mainerp.reports.print_relat_condicional import PrintRelatCondicional
from mainerp.ui.dialogs.relatorio_condicional_dialog import RelatorioCondicionalDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_CondicionalViewReports"]


class _CondicionalViewReports(ComponentMixin):
    def _exportar_condicionais(self):
        """Abre diálogo para selecionar filtros e exporta relatório"""
        dialog = RelatorioCondicionalDialog(self)
        if dialog.exec():
            filtros = dialog.get_filtros()
            self._gerar_relatorio_com_filtros(filtros)

    def _gerar_relatorio_com_filtros(self, filtros):
        """Gera relatório com base nos filtros selecionados"""
        try:
            data_inicio = filtros["data_inicio"]
            data_fim = filtros["data_fim"]
            cliente_id = filtros["cliente_id"]
            status = filtros["status"]

            # Validar datas
            if not self._validar_data(data_inicio) or not self._validar_data(data_fim):
                self._mostrar_aviso("Datas inválidas. Use o formato DD/MM/AAAA")
                return

            # CORREÇÃO: Usar a versão corrigida do PrintRelatCondicional
            filename = PrintRelatCondicional.gerar_relatorio_por_periodo(
                data_inicio, data_fim, status, cliente_id, "relatorios"
            )

            self._tratar_arquivo_gerado(filename, "Relatório exportado")

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in CondicionalView._gerar_relatorio_com_filtros in views/condicional_view.py",
            )
            self._mostrar_erro(
                "Erro na Exportação",
                f"Ocorreu um erro ao exportar as condicionais:\n{e!s}",
            )

    def _validar_data(self, data_str):
        """Valida formato de data DD/MM/YYYY"""
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def _imprimir_condicional(self):
        """Imprime comprovante da condicional selecionada"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para imprimir")
            return

        try:
            filename = PrintCondicional.gerar_comprovante(condicional.id, "relatorios")
            self._tratar_arquivo_gerado(filename, "Comprovante gerado")

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in CondicionalView._imprimir_condicional in views/condicional_view.py",
            )
            self._mostrar_erro(
                "Erro na Impressão",
                f"Ocorreu um erro ao gerar o comprovante:\n{e!s}",
            )

    def _tratar_arquivo_gerado(self, filename, mensagem_sucesso):
        """Trata arquivo gerado (relatório ou comprovante)"""
        if filename and ExportUtils.abrir_arquivo(filename):
            self._mostrar_sucesso(f"{mensagem_sucesso}:\n{filename}")
        else:
            self._mostrar_aviso(
                f"Arquivo salvo em: {filename}\nNão foi possível abrir automaticamente."
            )

    def _get_nome_cliente(self, cliente_id):
        """Obtém o nome do cliente pelo ID"""
        if not cliente_id:
            return "Cliente não informado"

        conn = Database().get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
            result = cursor.fetchone()
            return result[0] if result else "Cliente não encontrado"
        finally:
            conn.close()

    def _mostrar_erro(self, titulo, mensagem):
        """Mostra mensagem de erro"""
        QMessageBox.critical(self, titulo, mensagem)

    def _mostrar_aviso(self, mensagem):
        """Mostra mensagem de aviso"""
        QMessageBox.warning(self, "Aviso", mensagem)

    def _mostrar_sucesso(self, mensagem):
        """Mostra mensagem de sucesso"""
        QMessageBox.information(self, "Sucesso", mensagem)
