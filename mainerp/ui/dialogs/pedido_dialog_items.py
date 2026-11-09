"""Componentes de PedidoDialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFocusEvent
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)

from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import (
    calcular_subtotal,
    formatar_moeda,
)
from mainerp.ui.dialogs.observacao_dialog import ObservacaoDialog
from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.theme_tokens import DIMENSOES

__all__ = ["_PedidoDialogItems"]


def _ajustar_recuo_dialogo(dialogo: QInputDialog) -> None:
    campo = dialogo.findChild(QAbstractSpinBox)
    editor = campo.findChild(QLineEdit) if campo is not None else None
    if editor is None:
        raise RuntimeError("Campo numérico sem editor de texto.")
    editor.setTextMargins(DIMENSOES.espacamento, 0, DIMENSOES.espacamento, 0)


class _PedidoDialogItems(ComponentMixin):
    def _selecionar_fornecedor(self):
        """F2 - Selecionar fornecedor"""
        from .fornecedor_selection_dialog import FornecedorSelectionDialog

        dialog = FornecedorSelectionDialog(self)
        if dialog.exec():
            fornecedor = dialog.get_fornecedor_selecionado()
            if fornecedor:
                self.fornecedor_selecionado = fornecedor
                self.label_fornecedor.setText(fornecedor.nome)
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                self._verificar_habilitar_finalizacao()

    def _selecionar_produto(self):
        """F3 - Adicionar produto"""
        from .produto_selection_dialog import ProdutoSelectionDialog

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
                self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _processar_produto(self, produto):
        """Processa produto selecionado - ATUALIZADO COM DIÁLOGOS CORRIGIDOS E SELEÇÃO TOTAL"""
        # Validação básica
        if not hasattr(produto, "nome"):
            QMessageBox.warning(
                self, "Produto inválido", "Produto selecionado é inválido."
            )
            return

        # ========== DIÁLOGO DE QUANTIDADE (IGUAL AO MÓDULO VENDAS) ==========
        quantidade_dialog = QInputDialog(self)

        # Configurar propriedades do diálogo
        quantidade_dialog.setWindowTitle("Quantidade")

        # Montar nome do produto com cor e tamanho se disponíveis
        nome_produto = produto.nome
        if hasattr(produto, "cor") and produto.cor:
            nome_produto += f" {produto.cor}"
        if hasattr(produto, "tamanho") and produto.tamanho:
            nome_produto += f" {produto.tamanho}"

        quantidade_dialog.setLabelText(f"{nome_produto}")
        quantidade_dialog.setIntValue(1)
        quantidade_dialog.setIntMinimum(1)
        quantidade_dialog.setIntMaximum(10000)  # Limite razoável para pedidos
        quantidade_dialog.setIntStep(1)
        _ajustar_recuo_dialogo(quantidade_dialog)

        # Configurar flags da janela (idêntico ao módulo vendas)
        quantidade_dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.MSWindowsFixedSizeDialogHint
        )

        # Tamanho fixo (idêntico ao módulo vendas)
        quantidade_dialog.setFixedSize(400, 150)

        # Executar o diálogo e verificar se foi aceito
        if quantidade_dialog.exec() == QDialog.DialogCode.Accepted:
            quantidade = quantidade_dialog.intValue()

            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                return

            # ========== DIÁLOGO DE PREÇO DE CUSTO (CORRIGIDO COM SELEÇÃO TOTAL) ==========
            preco_custo_dialog = QInputDialog(self)

            # Configurar propriedades do diálogo
            preco_custo_dialog.setWindowTitle("Preço de Custo")
            preco_custo_dialog.setLabelText("Digite o preço de custo:")

            # Usar preço de custo existente ou sugerir um valor
            valor_sugerido = getattr(produto, "preco_custo", 0) or 0
            if valor_sugerido <= 0:
                valor_sugerido = 10.0  # Valor padrão sugerido

            # CORREÇÃO: Configurar o valor máximo para um número alto
            VALOR_MAXIMO = 9999999.99

            preco_custo_dialog.setDoubleValue(valor_sugerido)
            preco_custo_dialog.setDoubleMinimum(0.01)
            preco_custo_dialog.setDoubleMaximum(VALOR_MAXIMO)  # <-- CORREÇÃO PRINCIPAL
            preco_custo_dialog.setDoubleDecimals(2)
            _ajustar_recuo_dialogo(preco_custo_dialog)

            # Configurar flags da janela (igual ao módulo vendas)
            preco_custo_dialog.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.MSWindowsFixedSizeDialogHint
            )

            # Aumentar tamanho para acomodar números maiores
            preco_custo_dialog.setFixedSize(450, 220)

            # ===== SOLUÇÃO COMPLETA: Configurar o QDoubleSpinBox interno com seleção total =====
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QDoubleSpinBox

            def configurar_spinbox_custo():
                # Encontrar o QDoubleSpinBox dentro do diálogo
                spinboxes = preco_custo_dialog.findChildren(QDoubleSpinBox)
                for spinbox in spinboxes:
                    spinbox.setRange(0.01, VALOR_MAXIMO)  # Aumentar limite máximo
                    spinbox.setFixedWidth(220)  # Aumentar largura para números grandes
                    spinbox.setGroupSeparatorShown(True)  # Mostra separador de milhar
                    spinbox.setValue(valor_sugerido)

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

            # Configurar após o diálogo ser mostrado
            QTimer.singleShot(50, configurar_spinbox_custo)
            # ===== FIM DA SOLUÇÃO =====

            # Executar e verificar se foi aceito
            if preco_custo_dialog.exec() == QDialog.DialogCode.Accepted:
                preco_custo = preco_custo_dialog.doubleValue()

                if preco_custo <= 0:
                    QMessageBox.warning(
                        self, "Aviso", "O preço de custo deve ser maior que zero."
                    )
                    return

                # ========== DIÁLOGO DE PREÇO DE VENDA (CORRIGIDO COM SELEÇÃO TOTAL) ==========
                preco_venda_dialog = QInputDialog(self)

                # Configurar propriedades do diálogo
                preco_venda_dialog.setWindowTitle("Preço de Venda")
                preco_venda_dialog.setLabelText("Digite o preço de venda:")

                # Calcular sugestão de preço de venda (30% sobre custo)
                sugestao_venda = preco_custo * 1.3

                # Se o produto já tem preço de venda, usar como referência
                if hasattr(produto, "preco_venda") and produto.preco_venda > 0:
                    sugestao_venda = produto.preco_venda

                preco_venda_dialog.setDoubleValue(sugestao_venda)
                preco_venda_dialog.setDoubleMinimum(0.01)
                preco_venda_dialog.setDoubleMaximum(
                    VALOR_MAXIMO
                )  # <-- CORREÇÃO PRINCIPAL
                preco_venda_dialog.setDoubleDecimals(2)
                _ajustar_recuo_dialogo(preco_venda_dialog)

                # Configurar flags da janela (igual ao módulo vendas)
                preco_venda_dialog.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                    | Qt.WindowType.WindowCloseButtonHint
                    | Qt.WindowType.MSWindowsFixedSizeDialogHint
                )

                # Aumentar tamanho para acomodar números maiores
                preco_venda_dialog.setFixedSize(450, 220)

                # ===== SOLUÇÃO COMPLETA: Configurar o QDoubleSpinBox interno com seleção total =====
                def configurar_spinbox_venda():
                    spinboxes = preco_venda_dialog.findChildren(QDoubleSpinBox)
                    for spinbox in spinboxes:
                        spinbox.setRange(0.01, VALOR_MAXIMO)  # Aumentar limite máximo
                        spinbox.setFixedWidth(
                            220
                        )  # Aumentar largura para números grandes
                        spinbox.setGroupSeparatorShown(
                            True
                        )  # Mostra separador de milhar
                        spinbox.setValue(sugestao_venda)

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

                QTimer.singleShot(50, configurar_spinbox_venda)
                # ===== FIM DA SOLUÇÃO =====

                # Executar e verificar se foi aceito
                if preco_venda_dialog.exec() == QDialog.DialogCode.Accepted:
                    preco_venda = preco_venda_dialog.doubleValue()

                    if preco_venda <= 0:
                        QMessageBox.warning(
                            self, "Aviso", "O preço de venda deve ser maior que zero."
                        )
                        return

                    self._adicionar_produto(
                        produto, preco_custo, preco_venda, quantidade
                    )

    def _adicionar_produto(self, produto, preco_custo, preco_venda, quantidade):
        """Adiciona produto ao pedido - MODIFICADO para incluir valor de venda"""
        subtotal = calcular_subtotal(preco_custo, quantidade)

        # Verificar se produto já existe
        for i, prod in enumerate(self.produtos_selecionados):
            if prod["id"] == produto.id:
                nova_quantidade = prod["quantidade"] + quantidade
                self.produtos_selecionados[i]["quantidade"] = nova_quantidade
                self.produtos_selecionados[i]["preco_custo"] = (
                    preco_custo  # Atualizar preço
                )
                self.produtos_selecionados[i]["preco_venda"] = (
                    preco_venda  # Atualizar preço de venda
                )
                self.produtos_selecionados[i]["subtotal"] = calcular_subtotal(
                    preco_custo, nova_quantidade
                )
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
                return

        # Adicionar novo produto
        self.produtos_selecionados.append(
            {
                "id": produto.id,
                "nome": produto.nome,
                "preco_custo": preco_custo,
                "preco_venda": preco_venda,  # NOVO CAMPO
                "quantidade": quantidade,
                "subtotal": subtotal,
            }
        )

        self._atualizar_tabela()
        self._marcar_como_modificado()  # NOVO: Marca como modificado

    def _remover_produto(self):
        """Delete - Remove produto selecionado"""
        current_row = self.tabela_produtos.currentRow()
        if current_row >= 0 and current_row < len(self.produtos_selecionados):
            reply = QMessageBox.question(
                self,
                "Confirmar Remoção",
                f"Remover {self.produtos_selecionados[current_row]['nome']} do pedido?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.produtos_selecionados.pop(current_row)
                self._atualizar_tabela()
                self._marcar_como_modificado()  # NOVO: Marca como modificado
        else:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para remover.")

    def _definir_frete_desconto(self):
        """F10 - Definir frete e desconto - ATUALIZADO PARA DIÁLOGO MAIS CONSISTENTE"""
        if not self.produtos_selecionados:
            QMessageBox.warning(
                self, "Aviso", "Adicione produtos antes de definir frete e desconto."
            )
            return

        subtotal_centavos = sum(
            para_centavos(prod["subtotal"]) for prod in self.produtos_selecionados
        )
        subtotal_produtos = float(de_centavos(subtotal_centavos))

        # Criar um diálogo personalizado mais consistente
        from PyQt6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLineEdit,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Frete e Desconto")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Informações do subtotal
        subtotal_label = QLabel(
            f"Subtotal dos produtos: {formatar_moeda(subtotal_produtos)}"
        )
        subtotal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtotal_label)

        # Formulário
        form_layout = QFormLayout()

        # Campo Frete
        frete_input = QLineEdit()
        frete_input.setText(str(self.valor_frete) if self.valor_frete > 0 else "0.00")
        frete_input.setPlaceholderText("0.00")
        form_layout.addRow("Frete (R$):", frete_input)

        # Campo Desconto
        desconto_input = QLineEdit()
        desconto_input.setText(
            str(self.valor_desconto) if self.valor_desconto > 0 else "0.00"
        )
        desconto_input.setPlaceholderText("0.00")
        form_layout.addRow("Desconto (R$):", desconto_input)

        layout.addLayout(form_layout)

        # Botões
        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(dialog.accept)
        botoes.rejected.connect(dialog.reject)
        layout.addWidget(botoes)

        # Configurar como diálogo modal
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                # Converter valores
                novo_frete = float(frete_input.text().replace(",", ".") or 0)
                novo_desconto = float(desconto_input.text().replace(",", ".") or 0)

                # Validar valores
                if novo_frete < 0:
                    QMessageBox.warning(self, "Aviso", "O frete não pode ser negativo.")
                    return

                if novo_desconto < 0:
                    QMessageBox.warning(
                        self, "Aviso", "O desconto não pode ser negativo."
                    )
                    return

                if novo_desconto > subtotal_produtos:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"Desconto (R$ {novo_desconto:.2f}) não pode ser maior que o subtotal (R$ {subtotal_produtos:.2f}).",
                    )
                    return

                self.valor_frete = novo_frete
                self.valor_desconto = novo_desconto
                self._calcular_total()
                self._marcar_como_modificado()

            except ValueError:
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Digite valores numéricos válidos para frete e desconto.",
                )

    def _calcular_total(self):
        """Calcula total do pedido - ATUALIZADO com desconto"""
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
        # Garantir que o total não seja negativo
        total = max(0, total)

        self.label_subtotal.setText(formatar_moeda(subtotal))
        self.label_desconto.setText(formatar_moeda(self.valor_desconto))
        self.label_frete.setText(formatar_moeda(self.valor_frete))
        self.label_total.setText(formatar_moeda(total))

        # NOVO: Atualiza indicador visual de modificações
        self._atualizar_indicador_modificacoes()

    def _atualizar_indicador_modificacoes(self):
        """Atualiza indicador visual de modificações não salvas"""
        if self._modificacoes_nao_salvas:
            self.label_modificacoes.setText("Modificações não salvas")
            self.label_modificacoes.setVisible(True)
        else:
            self.label_modificacoes.setVisible(False)

    def _atualizar_tabela(self):
        """Atualiza tabela de produtos - MODIFICADO para incluir Cor, Tamanho, Referência e scroll automático"""
        self.tabela_produtos.setRowCount(len(self.produtos_selecionados))

        for row, produto in enumerate(self.produtos_selecionados):
            # Buscar dados completos do produto para cor, tamanho e referência
            from mainerp.data.models.produto import Produto

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

            # Preço Custo
            custo_item = QTableWidgetItem(formatar_moeda(produto["preco_custo"]))
            custo_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 5, custo_item)

            # Preço Venda
            venda_item = QTableWidgetItem(formatar_moeda(produto["preco_venda"]))
            venda_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            self.tabela_produtos.setItem(row, 6, venda_item)

            # Quantidade
            qtde_item = QTableWidgetItem(str(produto["quantidade"]))
            qtde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 7, qtde_item)

            # Subtotal
            subtotal_item = QTableWidgetItem(formatar_moeda(produto["subtotal"]))
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_produtos.setItem(row, 8, subtotal_item)

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
            len(self.produtos_selecionados) > 0
            and self.fornecedor_selecionado is not None
        )
        self.btn_finalizar.setEnabled(pode_finalizar)
