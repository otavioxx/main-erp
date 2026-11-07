"""Componentes de ProdutoVendaDialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import (
    QDialog,
    QInputDialog,
    QMessageBox,
    QTableWidgetItem,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.produto import Produto
from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import (
    aplicar_desconto_total,
    calcular_subtotal,
    formatar_moeda,
    validar_quantidade,
)
from mainerp.domain.utils.venda_utils import VendaUtils
from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog
from mainerp.ui.dialogs.observacao_dialog import ObservacaoDialog
from mainerp.ui.dialogs.pagamento_dialog import PagamentoDialog
from mainerp.ui.dialogs.produto_selection_dialog import ProdutoSelectionDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_VendaDialogOperations"]


class _VendaDialogOperations(ComponentMixin):
    def _cancelar_venda(self):
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
                    self._finalizar_venda()
                    # Se salvou com sucesso, fecha a janela
                    self.reject()
                except Exception as e:
                    # Se houver erro ao salvar, não fecha
                    registrar_excecao(
                        __name__,
                        "Exception handled in ProdutoVendaDialog._cancelar_venda in dialogs/venda_dialog.py",
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

    def _selecionar_cliente(self):
        """F2 - Selecionar cliente"""
        dialog = ClienteSelectionDialog(self)
        if dialog.exec():
            cliente = dialog.get_cliente_selecionado()
            if cliente:
                self.cliente_selecionado = cliente
                self.label_cliente.setText(cliente.nome)
                self._marcar_como_modificado()
                self._verificar_habilitar_finalizacao()

    def _selecionar_produto(self):
        """F3 - Adicionar produto"""
        dialog = ProdutoSelectionDialog(self)
        if dialog.exec():
            produto = dialog.get_produto_selecionado()
            if produto:
                self._processar_produto(produto)

    def _abrir_observacao(self):
        """F4 - Abrir dialog de observação"""
        dialog = ObservacaoDialog(self.observacao, self)
        if dialog.exec():
            nova_observacao = dialog.get_observacao()
            if nova_observacao != self.observacao:
                self.observacao = nova_observacao
                self._marcar_como_modificado()

    def _processar_produto(self, produto):
        """Processa produto selecionado com validações"""
        # Validações
        if produto.preco_venda <= 0:
            QMessageBox.warning(
                self,
                "Produto inválido",
                f"O produto '{produto.nome}' possui preço de venda 0 e não pode ser vendido.",
            )
            return

        if produto.estoque <= 0:
            QMessageBox.warning(
                self,
                "Produto sem estoque",
                f"O produto '{produto.nome}' está sem estoque e não pode ser vendido.",
            )
            return

        # Diálogo de quantidade
        quantidade_dialog = QInputDialog(self)

        quantidade_dialog.setWindowTitle("Quantidade")

        nome_completo = produto.nome
        if hasattr(produto, "cor") and produto.cor:
            nome_completo += f" {produto.cor}"
        if hasattr(produto, "tamanho") and produto.tamanho:
            nome_completo += f" {produto.tamanho}"

        quantidade_dialog.setLabelText(nome_completo)
        quantidade_dialog.setIntValue(1)
        quantidade_dialog.setIntMinimum(1)
        quantidade_dialog.setIntMaximum(produto.estoque)
        quantidade_dialog.setIntStep(1)

        quantidade_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        quantidade_dialog.setFixedSize(400, 150)

        if quantidade_dialog.exec() == QDialog.DialogCode.Accepted:
            quantidade = quantidade_dialog.intValue()

            if validar_quantidade(quantidade, produto.estoque):
                # Diálogo de preço - VERSÃO CORRIGIDA COM SELEÇÃO TOTAL
                preco_dialog = QInputDialog(self)

                preco_dialog.setWindowTitle("Preço de Venda")
                preco_dialog.setLabelText("Digite o preço de venda:")

                # CORREÇÃO: Configurar o valor máximo para um número alto
                VALOR_MAXIMO = 9999999.99

                # Configurar o QDoubleSpinBox diretamente
                preco_dialog.setDoubleValue(produto.preco_venda)
                preco_dialog.setDoubleMinimum(0.01)
                preco_dialog.setDoubleMaximum(VALOR_MAXIMO)
                preco_dialog.setDoubleDecimals(2)

                preco_dialog.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                    | Qt.WindowType.WindowCloseButtonHint
                    | Qt.WindowType.MSWindowsFixedSizeDialogHint
                )

                preco_dialog.setFixedSize(450, 220)

                from PyQt6.QtCore import QTimer
                from PyQt6.QtWidgets import QDoubleSpinBox

                def configurar_spinbox():
                    spinboxes = preco_dialog.findChildren(QDoubleSpinBox)
                    for spinbox in spinboxes:
                        spinbox.setRange(0.01, VALOR_MAXIMO)
                        spinbox.setFixedWidth(220)
                        spinbox.setGroupSeparatorShown(True)
                        spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
                        # Garantir que o valor inicial seja mostrado corretamente
                        spinbox.setValue(produto.preco_venda)

                        # CORREÇÃO: Forçar seleção total do texto quando o spinbox receber foco
                        spinbox.selectAll()

                        # Usar um timer para garantir que a seleção ocorra após o diálogo ser totalmente exibido
                        QTimer.singleShot(100, spinbox.selectAll)

                        # Conectar ao sinal de foco para sempre selecionar tudo quando ganhar foco
                        def selecionar_tudo_ao_focar(
                            event: QFocusEvent | None,
                            sb: QDoubleSpinBox = spinbox,
                        ) -> None:
                            QDoubleSpinBox.focusInEvent(sb, event)
                            sb.selectAll()

                        spinbox.focusInEvent = selecionar_tudo_ao_focar

                        break

                QTimer.singleShot(50, configurar_spinbox)

                if preco_dialog.exec() == QDialog.DialogCode.Accepted:
                    preco_venda = preco_dialog.doubleValue()

                    if preco_venda > 0:
                        produto_venda = Produto(
                            id=produto.id,
                            nome=produto.nome,
                            preco_custo=produto.preco_custo,
                            preco_venda=preco_venda,
                            estoque=produto.estoque,
                            fornecedor_id=produto.fornecedor_id,
                            ativo=produto.ativo,
                            tamanho=produto.tamanho,
                            cor=produto.cor,
                            ea=produto.ea,
                            referencia=produto.referencia,
                        )

                        self._adicionar_produto(produto_venda, quantidade)
                    else:
                        QMessageBox.warning(
                            self, "Aviso", "O preço de venda deve ser maior que zero."
                        )

    def _adicionar_produto(self, produto, quantidade):
        """Adiciona produto à venda"""
        # Validações finais
        if produto.preco_venda <= 0 or produto.estoque <= 0:
            return

        if quantidade > produto.estoque:
            QMessageBox.warning(
                self,
                "Estoque insuficiente",
                f"Quantidade solicitada maior que o estoque disponível ({produto.estoque}).",
            )
            return

        subtotal = calcular_subtotal(produto.preco_venda, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod["id"] == produto.id:
                nova_quantidade = prod["quantidade"] + quantidade
                if nova_quantidade > produto.estoque:
                    QMessageBox.warning(
                        self,
                        "Estoque insuficiente",
                        f"Quantidade total ({nova_quantidade}) excede o estoque disponível ({produto.estoque}).",
                    )
                    return
                self.produtos_selecionados[i]["quantidade"] = nova_quantidade
                self.produtos_selecionados[i]["subtotal"] = calcular_subtotal(
                    produto.preco_venda, nova_quantidade
                )
                self._atualizar_tabela()
                self._marcar_como_modificado()
                return

        # Adicionar novo produto
        self.produtos_selecionados.append(
            {
                "id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco_venda,
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

        self._atualizar_tabela()
        self._marcar_como_modificado()

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self,
                "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} da venda?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
                self._marcar_como_modificado()
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _aplicar_desconto(self):
        """F10 - Aplicar desconto"""
        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione produtos antes de aplicar desconto."
            )
            return

        total_sem_desconto_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        total_sem_desconto = float(de_centavos(total_sem_desconto_centavos))

        desconto, ok = QInputDialog.getDouble(
            self,
            "Desconto na Nota",
            f"Valor total: R$ {total_sem_desconto:.2f}\n\nDigite o valor do desconto:",
            value=self.desconto_total,
            min=0.0,
            max=total_sem_desconto,
            decimals=2,
        )

        if ok:
            self.desconto_total = desconto
            self._calcular_total()
            self._marcar_como_modificado()

    def _calcular_total(self):
        """Calcula total da venda com desconto"""
        total_produtos_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        total_produtos = float(de_centavos(total_produtos_centavos))
        total_venda = aplicar_desconto_total(total_produtos, self.desconto_total)

        self.label_subtotal.setText(formatar_moeda(total_produtos))
        self.label_desconto_aplicado.setText(formatar_moeda(self.desconto_total))
        self.label_total_final.setText(formatar_moeda(total_venda))

        self._atualizar_indicador_modificacoes()

    def _atualizar_indicador_modificacoes(self):
        """Atualiza indicador visual de modificações não salvas"""
        if self._modificacoes_nao_salvas:
            self.label_modificacoes.setText("✎ Modificações não salvas")
            self.label_modificacoes.setVisible(True)
        else:
            self.label_modificacoes.setVisible(False)

    def _atualizar_tabela(self):
        """Atualiza tabela de produtos"""
        self.tabela_produtos.setRowCount(len(self.produtos_selecionados))

        for row, produto in enumerate(self.produtos_selecionados):
            # Buscar dados completos do produto para cor, tamanho e referência
            produto_obj = Produto.buscar_por_id(produto["id"])

            # ID
            id_item = QTableWidgetItem(str(produto["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 0, id_item)

            # Nome
            self.tabela_produtos.setItem(row, 1, QTableWidgetItem(produto["nome"]))

            # Cor
            cor_item = QTableWidgetItem(
                produto_obj.cor if produto_obj and produto_obj.cor else ""
            )
            cor_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 2, cor_item)

            # Tamanho
            tamanho_item = QTableWidgetItem(
                produto_obj.tamanho if produto_obj and produto_obj.tamanho else ""
            )
            tamanho_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 3, tamanho_item)

            # Referência
            ref_item = QTableWidgetItem(
                produto_obj.referencia if produto_obj and produto_obj.referencia else ""
            )
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 4, ref_item)

            # Preço
            preco_item = QTableWidgetItem(formatar_moeda(produto["preco"]))
            preco_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 5, preco_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto["quantidade"]))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 6, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto["subtotal"]))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, subtotal_item)

        # Rolar para o final da tabela para mostrar o produto recém-adicionado
        if self.produtos_selecionados:
            self.tabela_produtos.scrollToBottom()
            # Também selecionar a última linha para destacar o produto adicionado
            ultima_linha = len(self.produtos_selecionados) - 1
            self.tabela_produtos.selectRow(ultima_linha)

        self._calcular_total()
        self._verificar_habilitar_finalizacao()

    def _verificar_habilitar_finalizacao(self):
        """Verifica se pode habilitar finalização"""
        pode_finalizar = (
            len(self.produtos_selecionados) > 0 and self.cliente_selecionado is not None
        )
        self.btn_finalizar.setEnabled(pode_finalizar)

    def _finalizar_venda(self):
        """F5 - Finalizar venda"""
        if self.cliente_selecionado is None:
            QMessageBox.warning(self, "Aviso", "Selecione um cliente para a venda.")
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione pelo menos um produto à venda."
            )
            return

        total_produtos_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        total_produtos = float(de_centavos(total_produtos_centavos))
        total_venda = aplicar_desconto_total(total_produtos, self.desconto_total)

        pagamento_dialog = PagamentoDialog(
            total_venda, self.cliente_selecionado.id, self
        )
        if pagamento_dialog.exec():
            dados_pagamento = pagamento_dialog.get_dados()

            forma_pagamento = dados_pagamento["forma_pagamento"]
            parcelas = dados_pagamento["parcelas"]
            data_primeiro_vencimento = dados_pagamento["data_primeiro_vencimento"]
            valor_entrada = dados_pagamento["valor_entrada"]
            valor_financiado = dados_pagamento["valor_financiado"]

            try:
                from mainerp.data.models.duplicata import Duplicata
                from mainerp.data.models.venda import Venda

                observacao = self.observacao

                venda = Venda(
                    cliente_id=self.cliente_selecionado.id,
                    total=total_venda,
                    forma_pagamento=forma_pagamento,
                    status=(
                        "concluida"
                        if forma_pagamento in ["Dinheiro", "Pix", "Cartão"]
                        else "parcelada"
                    ),
                    parcelas=parcelas,
                    desconto=self.desconto_total,
                    observacao=observacao,
                    valor_entrada=valor_entrada,
                    valor_financiado=valor_financiado,
                )
                venda_id = venda.salvar()

                VendaUtils.salvar_itens_venda(venda_id, self.produtos_selecionados)

                # Atualizar estoque
                for produto in self.produtos_selecionados:
                    produto_obj = Produto.buscar_por_id(produto["id"])
                    if produto_obj:
                        produto_obj.estoque -= produto["quantidade"]
                        produto_obj.salvar()

                # Criar parcelas se crediário - usar valor financiado
                if forma_pagamento == "Crediario":
                    Duplicata.criar_parcelas(
                        venda_id,
                        self.cliente_selecionado.id,
                        valor_financiado,
                        parcelas,
                        data_primeiro_vencimento,
                    )
                    self.venda_crediario_realizada.emit(self.cliente_selecionado.id)

                QMessageBox.information(self, "Sucesso", "Venda realizada com sucesso!")
                self.venda_realizada.emit()

                # Limpar flag de modificações após salvar com sucesso
                self._modificacoes_nao_salvas = False
                self._atualizar_indicador_modificacoes()

                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao processar venda: {e!s}")
