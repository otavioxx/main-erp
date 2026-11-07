"""Componentes de CondicionalView."""

from PyQt6.QtWidgets import (
    QMessageBox,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.condicional import Condicional
from mainerp.domain.utils.helpers import (
    formatar_moeda,
)
from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog
from mainerp.ui.dialogs.condicional_dialog import CondicionalDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_CondicionalViewActions"]


class _CondicionalViewActions(ComponentMixin):
    def _selecionar_cliente(self):
        """Abre dialog para seleção de cliente para filtro"""
        try:
            dialog = ClienteSelectionDialog(self)
            if dialog.exec():
                cliente_selecionado = dialog.get_cliente_selecionado()
                if cliente_selecionado:
                    self.cliente_filtro = cliente_selecionado
                    self.busca_cliente.setText(cliente_selecionado.nome)
                    self._filtrar_condicionais()
                else:
                    self.cliente_filtro = None
                    self.busca_cliente.clear()
                    self._filtrar_condicionais()
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in CondicionalView._selecionar_cliente in views/condicional_view.py",
            )
            self._mostrar_erro("Erro ao selecionar cliente", str(e))

    def _abrir_nova_condicional(self):
        """Abre dialog para nova condicional"""
        dialog = CondicionalDialog(None, self)
        dialog.condicional_salva.connect(self._carregar_condicionais)
        dialog.exec()

    def _get_condicional_selecionada(self):
        """Obtém a condicional selecionada na tabela"""
        row = self.tabela_condicionais.currentRow()
        if row == -1:
            return None

        try:
            condicional_id_item = self.tabela_condicionais.item(row, 0)
            if condicional_id_item is None:
                return None

            condicional_id = int(condicional_id_item.text())
            return Condicional.buscar_por_id(condicional_id)
        except (ValueError, AttributeError):
            return None

    def _editar_condicional(self):
        """Edita a condicional selecionada - apenas condicionais ativas podem ser editadas"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para editar")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                f"Só é possível editar condicionais com status 'Ativa'.\n"
                f"Status atual: {condicional.status.capitalize()}"
            )
            return

        try:
            dialog = CondicionalDialog(condicional.id, self)
            dialog.condicional_salva.connect(self._carregar_condicionais)
            dialog.exec()
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in CondicionalView._editar_condicional in views/condicional_view.py",
            )
            self._mostrar_erro("Erro ao abrir edição de condicional", str(e))

    def _converter_em_venda(self):
        """Converte a condicional selecionada em uma venda"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para converter em venda")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                "Apenas condicionais ativas podem ser convertidas em venda"
            )
            return

        if not condicional.itens:
            self._mostrar_aviso("A condicional não possui itens para venda")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Conversão",
            f"Converter condicional #{condicional.id} em venda?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}\n"
            f"Total: {formatar_moeda(condicional.calcular_total())}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                dialog = ProdutoVendaDialog(self)

                # Configurar cliente na venda
                from mainerp.data.models.cliente import Cliente

                cliente = Cliente.buscar_por_id(condicional.cliente_id)
                if cliente:
                    dialog.cliente_selecionado = cliente
                    dialog.label_cliente.setText(cliente.nome)

                # Adicionar produtos da condicional
                from mainerp.data.models.produto import Produto

                for item in condicional.itens:
                    produto = Produto.buscar_por_id(item["produto_id"])
                    if produto:
                        dialog.adicionar_produto(produto, item["quantidade"])

                if dialog.exec():
                    condicional.marcar_como_convertida()
                    self._carregar_condicionais()
                    self._mostrar_sucesso(
                        "Condicional convertida em venda com sucesso!"
                    )

            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in CondicionalView._converter_em_venda in views/condicional_view.py",
                )
                self._mostrar_erro("Erro ao converter condicional", str(e))

    def _marcar_como_devolvida(self):
        """Marca a condicional selecionada como devolvida"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para marcar como devolvida")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                "Apenas condicionais ativas podem ser marcadas como devolvidas"
            )
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Devolução",
            f"Marcar condicional #{condicional.id} como devolvida?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                condicional.marcar_como_devolvida()
                self._carregar_condicionais()
                self._mostrar_sucesso("Condicional marcada como devolvida!")
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in CondicionalView._marcar_como_devolvida in views/condicional_view.py",
                )
                self._mostrar_erro("Erro ao marcar condicional", str(e))

    def _excluir_condicional(self):
        """Exclui a condicional selecionada - apenas condicionais em aberto podem ser excluídas"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para excluir")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                f"Apenas condicionais em aberto podem ser excluídas.\n"
                f"Esta condicional está com status: {condicional.status.capitalize()}"
            )
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Excluir condicional #{condicional.id}?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                Condicional.excluir_por_id(condicional.id)

                self._carregar_condicionais()
                self.tabela_condicionais.clearSelection()
                self._mostrar_sucesso("Condicional excluída com sucesso!")

            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in CondicionalView._excluir_condicional in views/condicional_view.py",
                )
                self._mostrar_erro("Erro ao excluir condicional", str(e))
