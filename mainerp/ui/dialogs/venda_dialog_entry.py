"""Componentes de ProdutoVendaDialog."""

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMessageBox,
    QPushButton,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.produto import Produto
from mainerp.data.money import de_centavos, para_centavos_localizado
from mainerp.ui.mixins.component_mixin import ComponentMixin

__all__ = ["_VendaDialogQuickEntry"]


class _VendaDialogQuickEntry(ComponentMixin):
    def _configurar_atalhos(self):
        """Configura atalhos de teclado"""
        self.shortcut_f2 = QShortcut("F2", self)
        self.shortcut_f2.activated.connect(self._selecionar_cliente)

        self.shortcut_f3 = QShortcut("F3", self)
        self.shortcut_f3.activated.connect(self._selecionar_produto)

        self.shortcut_f4 = QShortcut("F4", self)
        self.shortcut_f4.activated.connect(self._abrir_observacao)

        self.shortcut_f5 = QShortcut("F5", self)
        self.shortcut_f5.activated.connect(self._finalizar_venda)

        self.shortcut_f10 = QShortcut("F10", self)
        self.shortcut_f10.activated.connect(self._aplicar_desconto)

        self.shortcut_delete = QShortcut(
            QKeySequence(QKeySequence.StandardKey.Delete), self
        )
        self.shortcut_delete.activated.connect(self._remover_produto)

    def _configurar_comportamento_enter(self):
        """Configura comportamento da tecla Enter para não interceptar o fluxo"""
        # Garantir que nenhum botão seja padrão
        for botao in self.findChildren(QPushButton):
            botao.setAutoDefault(False)
            botao.setDefault(False)

        # Definir foco inicial no campo código
        self.entry_codigo.setFocus()

    def _processar_enter_codigo(self):
        """Enter no campo código - busca produto e vai para quantidade"""
        codigo_texto = self.entry_codigo.text().strip()
        if not codigo_texto:
            return

        # Buscar produto
        produto_encontrado = self._buscar_e_validar_produto(codigo_texto)

        if produto_encontrado:
            # Ir para o próximo campo
            self.entry_quantidade.setFocus()
            self.entry_quantidade.selectAll()
        else:
            # Manter foco no código se produto não foi encontrado
            self.entry_codigo.selectAll()

    def _processar_enter_quantidade(self):
        """Enter no campo quantidade - vai para valor"""
        quantidade_texto = self.entry_quantidade.text().strip()

        # Validar quantidade
        if not quantidade_texto:
            self.entry_quantidade.setText("1")

        try:
            quantidade = int(quantidade_texto or "1")
            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Quantidade deve ser um número inteiro.")
            self.entry_quantidade.setFocus()
            self.entry_quantidade.selectAll()
            return

        # Ir para campo valor
        self.entry_valor.setFocus()
        self.entry_valor.selectAll()

    def _processar_enter_valor(self):
        """Enter no campo valor - adiciona produto e volta para código"""
        self._adicionar_produto_entrada_rapida()

    def _buscar_e_validar_produto(self, codigo_texto):
        """Busca e valida produto pelo código"""
        try:
            produto_id = int(codigo_texto)
            produto = Produto.buscar_por_id(produto_id)

            if produto:
                self._exibir_produto_encontrado(produto)
                return True
            else:
                self.label_produto_encontrado.setText("❌ Produto não encontrado")
                self.entry_valor.clear()
                return False

        except ValueError:
            self.label_produto_encontrado.setText("❌ Código inválido")
            self.entry_valor.clear()
            return False

    def _buscar_produto_por_codigo(self):
        """Busca produto pelo código digitado (chamado no textChanged)"""
        codigo_texto = self.entry_codigo.text().strip()

        if not codigo_texto:
            self._limpar_info_produto()
            return

        # Só buscar se for um número válido
        try:
            produto_id = int(codigo_texto)
            encontrou_produto = self._buscar_e_validar_produto(codigo_texto)

            # Se encontrou produto válido, atualizar valor automaticamente
            if encontrou_produto:
                self._atualizar_valor_automatico(produto_id)

        except ValueError:
            if len(codigo_texto) > 0:  # Só mostrar erro se há texto
                self.label_produto_encontrado.setText("❌ Digite apenas números")
                self.entry_valor.clear()  # Limpar valor se código inválido

    def _atualizar_valor_automatico(self, produto_id):
        """Atualiza valor automaticamente sempre que um produto válido for encontrado"""
        try:
            produto = Produto.buscar_por_id(produto_id)

            if produto and produto.preco_venda > 0:
                # Sempre atualizar o valor com o preço do produto atual
                valor_formatado = f"{produto.preco_venda:.2f}".replace(".", ",")
                self.entry_valor.setText(valor_formatado)
            else:
                # Se produto não tem preço válido, limpar campo
                self.entry_valor.clear()
        except Exception:
            # Em caso de erro, limpar campo
            registrar_excecao(
                __name__,
                "Exception handled in ProdutoVendaDialog._atualizar_valor_automatico in dialogs/venda_dialog.py",
            )
            self.entry_valor.clear()

    def _limpar_info_produto(self):
        """Limpa informações do produto"""
        self.label_produto_encontrado.clear()
        self.entry_valor.clear()

    def _exibir_produto_encontrado(self, produto):
        """Exibe informações do produto encontrado"""
        if produto.preco_venda <= 0:
            self.label_produto_encontrado.setText(
                f"⚠️ {produto.nome} - Produto sem preço de venda!"
            )
            return

        if produto.estoque <= 0:
            self.label_produto_encontrado.setText(f"⚠️ {produto.nome} - Sem estoque!")
            return

        # Produto válido
        info_produto = f"✅ {produto.nome}"
        if produto.cor:
            info_produto += f" - {produto.cor}"
        if produto.tamanho:
            info_produto += f" - {produto.tamanho}"
        info_produto += f" (Estoque: {produto.estoque})"

        self.label_produto_encontrado.setText(info_produto)

    def _adicionar_produto_entrada_rapida(self):
        """Adiciona produto usando entrada rápida"""
        codigo_texto = self.entry_codigo.text().strip()
        quantidade_texto = self.entry_quantidade.text().strip()
        valor_texto = self.entry_valor.text().strip()

        # Validações
        if not codigo_texto:
            QMessageBox.warning(self, "Aviso", "Digite o código do produto.")
            self.entry_codigo.setFocus()
            return

        if not quantidade_texto:
            quantidade_texto = "1"
            self.entry_quantidade.setText("1")

        if not valor_texto:
            QMessageBox.warning(self, "Aviso", "Digite o valor de venda.")
            self.entry_valor.setFocus()
            return

        try:
            produto_id = int(codigo_texto)
            quantidade = int(quantidade_texto)

            # Converter valor (aceita vírgula ou ponto)
            valor_venda = float(de_centavos(para_centavos_localizado(valor_texto)))

            if quantidade <= 0:
                QMessageBox.warning(
                    self, "Aviso", "A quantidade deve ser maior que zero."
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            if valor_venda <= 0:
                QMessageBox.warning(
                    self, "Aviso", "O valor de venda deve ser maior que zero."
                )
                self.entry_valor.setFocus()
                self.entry_valor.selectAll()
                return

            produto = Produto.buscar_por_id(produto_id)

            if not produto:
                QMessageBox.warning(self, "Aviso", "Produto não encontrado.")
                self.entry_codigo.setFocus()
                self.entry_codigo.selectAll()
                return

            # Validações de estoque
            if produto.estoque <= 0:
                QMessageBox.warning(
                    self,
                    "Produto sem estoque",
                    f"O produto '{produto.nome}' está sem estoque e não pode ser vendido.",
                )
                return

            if quantidade > produto.estoque:
                QMessageBox.warning(
                    self,
                    "Estoque insuficiente",
                    f"Quantidade solicitada ({quantidade}) maior que o estoque disponível ({produto.estoque}).",
                )
                self.entry_quantidade.setFocus()
                self.entry_quantidade.selectAll()
                return

            # Criar uma cópia do produto com o novo preço para esta venda
            produto_venda = Produto(
                id=produto.id,
                nome=produto.nome,
                preco_custo=produto.preco_custo,
                preco_venda=valor_venda,  # Usar o valor digitado
                estoque=produto.estoque,
                fornecedor_id=produto.fornecedor_id,
                ativo=produto.ativo,
                tamanho=produto.tamanho,
                cor=produto.cor,
                ea=produto.ea,
                referencia=produto.referencia,
            )

            self._adicionar_produto(produto_venda, quantidade)
            self._limpar_entrada_rapida()

        except ValueError as e:
            QMessageBox.warning(self, "Aviso", f"Valores inválidos: {e!s}")
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in ProdutoVendaDialog._adicionar_produto_entrada_rapida in dialogs/venda_dialog.py",
            )
            QMessageBox.warning(self, "Erro", f"Erro ao adicionar produto: {e!s}")

    def _limpar_entrada_rapida(self):
        """Limpa campos de entrada rápida e volta foco para código"""
        self.entry_codigo.clear()
        self.entry_quantidade.setText("1")
        self.entry_valor.clear()
        self.label_produto_encontrado.clear()

        # Voltar foco para o campo código para continuar fluxo
        self.entry_codigo.setFocus()
