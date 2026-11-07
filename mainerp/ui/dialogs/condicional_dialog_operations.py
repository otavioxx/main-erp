"""Componentes de CondicionalDialog."""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QInputDialog,
    QMessageBox,
    QTableWidgetItem,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.cliente import Cliente
from mainerp.data.models.condicional import Condicional
from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import (
    aplicar_desconto_total,
    calcular_subtotal,
    formatar_moeda,
)
from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog
from mainerp.ui.dialogs.observacao_dialog import ObservacaoDialog
from mainerp.ui.dialogs.preco_venda_dialog import solicitar_preco_venda
from mainerp.ui.dialogs.produto_selection_dialog import ProdutoSelectionDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_CondicionalDialogOperations"]


class _CondicionalDialogOperations(ComponentMixin):
    def _cancelar_condicional(self):
        """Método próprio para cancelar - verifica modificações"""
        if not self._modificacoes_nao_salvas:
            self.reject()
            return

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
                try:
                    self._salvar_condicional()
                    self.reject()
                except Exception as e:
                    registrar_excecao(
                        __name__,
                        "Exception handled in CondicionalDialog._cancelar_condicional in dialogs/condicional_dialog.py",
                    )
                    QMessageBox.warning(
                        self, "Erro ao salvar", f"Não foi possível salvar: {e!s}"
                    )
                    return
            elif reply == QMessageBox.StandardButton.Discard:
                self.reject()
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
                self._verificar_habilitar_salvamento()

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

        quantidade_dialog = QInputDialog(self)
        quantidade_dialog.setWindowTitle("Quantidade")

        nome_produto = produto.nome
        if produto.cor:
            nome_produto += f" {produto.cor}"
        if produto.tamanho:
            nome_produto += f" {produto.tamanho}"

        quantidade_dialog.setLabelText(f"{nome_produto}")
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

            if quantidade <= 0 or quantidade > produto.estoque:
                QMessageBox.warning(
                    self,
                    "Quantidade inválida",
                    f"Quantidade deve estar entre 1 e {produto.estoque}.",
                )
                return

            preco_venda = solicitar_preco_venda(produto.preco_venda, self)
            if preco_venda is not None:
                from mainerp.data.models.produto import Produto

                produto_condicional = Produto(
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

                self._adicionar_produto(produto_condicional, quantidade)

    def _adicionar_produto(self, produto, quantidade):
        """Adiciona produto à condicional"""
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
                f"Remover {self.produtos_selecionados[current_row]['nome']} da condicional?",
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

        desconto_dialog = QInputDialog(self)
        desconto_dialog.setWindowTitle("Desconto na Condicional")
        desconto_dialog.setLabelText(
            f"Valor total: R$ {total_sem_desconto:.2f}\n\nDigite o valor do desconto:"
        )
        desconto_dialog.setDoubleValue(self.desconto_total)
        desconto_dialog.setDoubleMinimum(0.0)
        desconto_dialog.setDoubleMaximum(total_sem_desconto)
        desconto_dialog.setDoubleDecimals(2)

        desconto_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        desconto_dialog.setFixedSize(450, 200)

        if desconto_dialog.exec() == QDialog.DialogCode.Accepted:
            desconto = desconto_dialog.doubleValue()
            self.desconto_total = desconto
            self._calcular_total()
            self._marcar_como_modificado()

    def _calcular_total(self):
        """Calcula total da condicional com desconto"""
        total_produtos_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        total_produtos = float(de_centavos(total_produtos_centavos))
        total_condicional = aplicar_desconto_total(total_produtos, self.desconto_total)

        self.label_subtotal.setText(formatar_moeda(total_produtos))
        self.label_desconto_aplicado.setText(formatar_moeda(self.desconto_total))
        self.label_total_final.setText(formatar_moeda(total_condicional))

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
            from mainerp.data.models.produto import Produto

            produto_obj = Produto.buscar_por_id(produto["id"])

            id_item = QTableWidgetItem(str(produto["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 0, id_item)

            self.tabela_produtos.setItem(row, 1, QTableWidgetItem(produto["nome"]))

            cor_item = QTableWidgetItem(
                produto_obj.cor if produto_obj and produto_obj.cor else ""
            )
            cor_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 2, cor_item)

            tamanho_item = QTableWidgetItem(
                produto_obj.tamanho if produto_obj and produto_obj.tamanho else ""
            )
            tamanho_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 3, tamanho_item)

            ref_item = QTableWidgetItem(
                produto_obj.referencia if produto_obj and produto_obj.referencia else ""
            )
            ref_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 4, ref_item)

            preco_item = QTableWidgetItem(formatar_moeda(produto["preco"]))
            preco_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 5, preco_item)

            qtde_item = QTableWidgetItem(str(produto["quantidade"]))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 6, qtde_item)

            subtotal_item = QTableWidgetItem(formatar_moeda(produto["subtotal"]))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, subtotal_item)

        if self.produtos_selecionados:
            self.tabela_produtos.scrollToBottom()
            ultima_linha = len(self.produtos_selecionados) - 1
            self.tabela_produtos.selectRow(ultima_linha)

        self._calcular_total()
        self._verificar_habilitar_salvamento()

    def _verificar_habilitar_salvamento(self):
        """Verifica se pode habilitar salvamento"""
        pode_salvar = (
            len(self.produtos_selecionados) > 0 and self.cliente_selecionado is not None
        )
        self.btn_salvar.setEnabled(pode_salvar)

    def _carregar_dados(self):
        """Carrega dados da condicional para edição"""
        if self.condicional_id:
            try:
                condicional_id = getattr(self.condicional_id, "id", self.condicional_id)

                condicional = Condicional.buscar_por_id(condicional_id)
                if condicional:
                    self.cliente_selecionado = Cliente.buscar_por_id(
                        condicional.cliente_id
                    )
                    if self.cliente_selecionado:
                        self.label_cliente.setText(self.cliente_selecionado.nome)

                    if condicional.data_prevista_devolucao:
                        data_str = condicional.data_prevista_devolucao.strftime(
                            "%d/%m/%Y"
                        )
                        self.date_devolucao.setText(data_str)

                    self.observacao = condicional.observacao or ""
                    self.desconto_total = condicional.desconto or 0.0

                    for item in condicional.itens:
                        self.produtos_selecionados.append(
                            {
                                "id": item["produto_id"],
                                "nome": item["produto_nome"],
                                "preco": item["preco_unitario"],
                                "quantidade": item["quantidade"],
                                "subtotal": item["quantidade"] * item["preco_unitario"],
                            }
                        )

                    self._atualizar_tabela()
                    self._modificacoes_nao_salvas = False
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in CondicionalDialog._carregar_dados in dialogs/condicional_dialog.py",
                )
                QMessageBox.warning(
                    self, "Erro", f"Erro ao carregar condicional: {e!s}"
                )

    def _salvar_condicional(self):
        """F5 - Salvar condicional"""
        if self.cliente_selecionado is None:
            QMessageBox.warning(
                self, "Aviso", "Selecione um cliente para a condicional."
            )
            return

        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione pelo menos um produto à condicional."
            )
            return

        try:
            data_texto = self.date_devolucao.text().strip()
            if data_texto:
                try:
                    data_devolucao = datetime.strptime(data_texto, "%d/%m/%Y").date()
                except ValueError:
                    QMessageBox.warning(
                        self, "Data Inválida", "Formato de data deve ser DD/MM/AAAA"
                    )
                    return
            else:
                data_devolucao = datetime.now().date() + timedelta(days=3)

            cliente_id = (
                self.cliente_selecionado.id
                if hasattr(self.cliente_selecionado, "id")
                else self.cliente_selecionado
            )

            condicional = Condicional(
                id=self.condicional_id,
                cliente_id=cliente_id,
                data_condicional=datetime.now().date(),
                data_prevista_devolucao=data_devolucao,
                observacao=self.observacao,
                status="ativa",
                desconto=self.desconto_total,
            )

            for produto in self.produtos_selecionados:
                condicional.itens.append(
                    {
                        "produto_id": produto["id"],
                        "quantidade": produto["quantidade"],
                        "preco_unitario": float(produto["preco"]),
                    }
                )

            condicional_id = condicional.salvar()

            QMessageBox.information(
                self,
                "Sucesso",
                (
                    "Condicional atualizada com sucesso!"
                    if self.condicional_id
                    else "Condicional criada com sucesso!"
                ),
            )

            self.condicional_id = condicional_id
            self._modificacoes_nao_salvas = False
            self._atualizar_indicador_modificacoes()
            self.condicional_salva.emit()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar condicional: {e!s}")

    def get_dados_condicional(self):
        """Retorna os dados da condicional para conversão em venda"""
        data_texto = self.date_devolucao.text().strip()
        if data_texto:
            try:
                data_devolucao = datetime.strptime(data_texto, "%d/%m/%Y").date()
            except ValueError:
                data_devolucao = datetime.now().date() + timedelta(days=3)
        else:
            data_devolucao = datetime.now().date() + timedelta(days=3)

        return {
            "cliente": self.cliente_selecionado,
            "produtos": self.produtos_selecionados.copy(),
            "data_devolucao": data_devolucao,
            "observacao": self.observacao,
            "desconto": self.desconto_total,
        }
