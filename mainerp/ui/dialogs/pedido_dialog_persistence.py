"""Componentes de PedidoDialog."""

from PyQt6.QtWidgets import (
    QMessageBox,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.pedido import Pedido
from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import (
    formatar_moeda,
)
from mainerp.domain.utils.pedido_utils import PedidoUtils
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_PedidoDialogPersistence"]


class _PedidoDialogPersistence(ComponentMixin):
    def _cancelar_pedido(self):
        """Método próprio para cancelar - verifica modificações"""
        # Se não há modificações, apenas fecha
        if not self._modificacoes_nao_salvas:
            self.reject()
            return

        # Se há modificações, pergunta ao usuário
        if self._tem_dados_para_salvar():
            reply = QMessageBox.question(
                self,
                "Modificações não salvas",
                "Você tem modificações não salvas. Deseja salvar antes de cancelar?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )

            if reply == QMessageBox.StandardButton.Save:
                # Tenta finalizar
                try:
                    self._finalizar_pedido()
                    # Se salvou com sucesso, fecha a janela
                    self.reject()
                except Exception as e:
                    # Se houver erro ao salvar, não fecha
                    registrar_excecao(
                        __name__,
                        "Exception handled in PedidoDialog._cancelar_pedido in dialogs/pedido_dialog.py",
                    )
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {e!s}"
                    )
                    return

            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()  # Descarta modificações e fecha

            # Se escolheu Cancelar, não faz nada (permanece na tela)
        else:
            self.reject()

    def _finalizar_pedido(self):
        """F5 - Finalizar pedido - ATUALIZADO com desconto"""
        if not self.fornecedor_selecionado:
            QMessageBox.warning(self, "Aviso", "Selecione um fornecedor.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos um produto.")
            return

        subtotal_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        total_centavos = max(
            0,
            subtotal_centavos
            - para_centavos(self.valor_desconto)
            + para_centavos(self.valor_frete),
        )
        subtotal = float(de_centavos(subtotal_centavos))
        total = float(de_centavos(total_centavos))

        if self._confirmar_pedido(subtotal, total):
            try:
                observacao = self.observacao

                if self.pedido_editando:
                    pedido_id = self._atualizar_pedido_existente(total, observacao)
                    mensagem = "Pedido atualizado com sucesso!"
                else:
                    pedido_id = self._criar_novo_pedido(total, observacao)
                    mensagem = "Pedido realizado com sucesso!"

                self._salvar_itens_pedido(pedido_id)

                QMessageBox.information(self, "Sucesso", mensagem)

                # Limpar flag de modificações após salvar com sucesso
                self._modificacoes_nao_salvas = False
                self._atualizar_indicador_modificacoes()

                self.pedido_realizado.emit()
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao processar pedido: {e!s}")

    def _confirmar_pedido(self, subtotal, total):
        """Confirma finalização do pedido - ATUALIZADO com desconto"""
        pedido_editando = self.pedido_editando
        fornecedor = self.fornecedor_selecionado
        if fornecedor is None:
            raise RuntimeError("Não é possível confirmar o pedido sem fornecedor.")

        if pedido_editando is not None:
            titulo = "Confirmar Edição"
            mensagem = f"EDITAR Pedido #{pedido_editando.id}\n\n"
        else:
            titulo = "Confirmar Pedido"
            mensagem = "NOVO Pedido\n\n"

        mensagem += (
            f"Fornecedor: {fornecedor.nome}\nSubtotal: {formatar_moeda(subtotal)}\n"
        )

        # Incluir desconto apenas se houver
        if self.valor_desconto > 0:
            mensagem += f"Desconto: {formatar_moeda(self.valor_desconto)}\n"

        # Incluir frete apenas se houver
        if self.valor_frete > 0:
            mensagem += f"Frete: {formatar_moeda(self.valor_frete)}\n"

        mensagem += (
            f"Total: {formatar_moeda(total)}\n\n"
            f"Confirmar {'edição' if pedido_editando is not None else 'pedido'}?"
        )

        resposta = QMessageBox.question(
            self,
            titulo,
            mensagem,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _atualizar_pedido_existente(self, total, observacao):
        """Atualiza pedido existente - ATUALIZADO com desconto"""
        pedido = self.pedido_editando
        fornecedor = self.fornecedor_selecionado
        if pedido is None:
            raise RuntimeError("Não há pedido em edição para atualizar.")
        if fornecedor is None:
            raise RuntimeError("Não é possível atualizar o pedido sem fornecedor.")

        pedido.fornecedor_id = fornecedor.id
        pedido.valor_total = total
        pedido.valor_frete = self.valor_frete
        pedido.desconto = self.valor_desconto
        pedido.observacao = observacao
        return pedido.salvar()

    def _criar_novo_pedido(self, total, observacao):
        """Cria novo pedido - ATUALIZADO com desconto"""
        fornecedor = self.fornecedor_selecionado
        if fornecedor is None:
            raise RuntimeError("Não é possível criar o pedido sem fornecedor.")

        pedido = Pedido(
            fornecedor_id=fornecedor.id,
            valor_total=total,
            valor_frete=self.valor_frete,
            desconto=self.valor_desconto,
            observacao=observacao,
            status="pendente",
        )
        return pedido.salvar()

    def _salvar_itens_pedido(self, pedido_id):
        """Salva itens do pedido"""
        from mainerp.data.database_utils import DatabaseUtils

        DatabaseUtils.executar_query(
            "DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,)
        )
        PedidoUtils.salvar_itens_pedido(pedido_id, self.produtos_selecionados)

    def _carregar_dados_existentes(self):
        """Carrega dados do pedido para edição - MODIFICADO para incluir desconto"""
        if not self.pedido_editando:
            return

        self.setWindowTitle(f"Editar Pedido #{self.pedido_editando.id}")

        # Carregar fornecedor
        from mainerp.data.models.fornecedor import Fornecedor

        fornecedor = Fornecedor.buscar_por_id(self.pedido_editando.fornecedor_id)
        if fornecedor:
            self.fornecedor_selecionado = fornecedor
            self.label_fornecedor.setText(fornecedor.nome)

        # Carregar dados
        if self.pedido_editando.observacao:
            self.observacao = self.pedido_editando.observacao

        self.valor_frete = self.pedido_editando.valor_frete or 0.0
        self.valor_desconto = self.pedido_editando.desconto or 0.0

        # Carregar produtos
        itens = self.pedido_editando.obter_itens()
        for item in itens:
            self.produtos_selecionados.append(
                {
                    "id": item[2],  # produto_id
                    "nome": item[6],  # produto_nome
                    "preco_custo": item[4],  # preco_custo
                    "preco_venda": (
                        item[8] if len(item) > 8 and item[8] else item[4] * 1.3
                    ),  # preco_venda (com fallback)
                    "quantidade": item[3],  # quantidade
                    "subtotal": item[5],  # subtotal
                }
            )

        self._atualizar_tabela()
        self._verificar_habilitar_finalizacao()

        # Após carregar dados, não há modificações não salvas inicialmente
        self._modificacoes_nao_salvas = False
        self._atualizar_indicador_modificacoes()
