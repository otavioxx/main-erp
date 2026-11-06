"""
Soluções para os problemas de ordenação e filtro nas tabelas PyQt6
"""

from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from utils.produto_utils import ProdutoUtils
from utils.helpers import formatar_moeda, formatar_data

class NumericTableWidgetItem(QTableWidgetItem):
    """Item de tabela que ordena numericamente ao invés de alfabeticamente"""

    def __init__(self, text=""):
        super().__init__(text)

    def __lt__(self, other):
        """Sobrescreve a comparação para ordenação numérica"""
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            # Se não conseguir converter para número, usa ordenação de string
            return self.text() < other.text()

# ========== CORREÇÃO 1: Para ClienteView ==========

class ClienteViewFixed:
    """Exemplo de correção para ClienteView"""

    def _preencher_tabela_clientes(self, clientes):
        """Versão corrigida que resolve ambos os problemas"""
        # Cores para clientes inativos
        cor_fundo_inativo = QColor("#4a2a2a")
        cor_texto_inativo = QColor("#ff6b6b")

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_clientes.setSortingEnabled(False)

        for row, cliente in enumerate(clientes):
            # CORREÇÃO: ID usando NumericTableWidgetItem
            item_id = NumericTableWidgetItem(str(cliente.id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not cliente.ativo:
                item_id.setBackground(cor_fundo_inativo)
                item_id.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 0, item_id)

            # Nome
            nome = cliente.nome or ""
            item_nome = QTableWidgetItem(nome)
            if not cliente.ativo:
                item_nome.setBackground(cor_fundo_inativo)
                item_nome.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 1, item_nome)

            # CPF/CNPJ
            cpf_cnpj = cliente.cpf_cnpj or ""
            item_cpf = QTableWidgetItem(cpf_cnpj)
            if not cliente.ativo:
                item_cpf.setBackground(cor_fundo_inativo)
                item_cpf.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 2, item_cpf)

            # Endereço
            endereco = cliente.endereco or ""
            item_endereco = QTableWidgetItem(endereco)
            if not cliente.ativo:
                item_endereco.setBackground(cor_fundo_inativo)
                item_endereco.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 3, item_endereco)

            # Telefone
            telefone = cliente.telefone or ""
            item_telefone = QTableWidgetItem(telefone)
            if not cliente.ativo:
                item_telefone.setBackground(cor_fundo_inativo)
                item_telefone.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 4, item_telefone)

            # Email
            email = cliente.email or ""
            item_email = QTableWidgetItem(email)
            if not cliente.ativo:
                item_email.setBackground(cor_fundo_inativo)
                item_email.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 5, item_email)

            # Observação
            obs = cliente.observacao or ""
            item_obs = QTableWidgetItem(obs)
            if obs:
                item_obs.setToolTip(obs)
            if not cliente.ativo:
                item_obs.setBackground(cor_fundo_inativo)
                item_obs.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 6, item_obs)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_clientes.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID decrescente por padrão
        self.tabela_clientes.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _filtrar_clientes(self):
        """Versão corrigida do filtro"""
        texto_busca = self.busca_edit.text().lower().strip()

        # CORREÇÃO: Trabalhar sempre com os dados originais
        if texto_busca:
            dados_filtrados = [
                c for c in self.dados  # Sempre usar self.dados original
                if (texto_busca in c.nome.lower() if c.nome else False) or
                   (texto_busca in (c.cpf_cnpj or "").lower()) or
                   (texto_busca in (c.telefone or "").lower()) or
                   (texto_busca in (c.email or "").lower()) or
                   (texto_busca in (c.endereco or "").lower()) or
                   (texto_busca in (c.observacao or "").lower())
            ]
        else:
            dados_filtrados = self.dados

        self.tabela_clientes.setRowCount(len(dados_filtrados))
        self._preencher_tabela_clientes(dados_filtrados)

# ========== CORREÇÃO 2: Para ProdutoView (valores monetários) ==========

class ProdutoViewFixed:
    """Exemplo de correção para ProdutoView com valores monetários"""

    def _preencher_tabela_produtos(self, produtos):
        """Versão corrigida para produtos"""
        # Desabilitar ordenação durante preenchimento
        self.tabela_produtos.setSortingEnabled(False)

        cor_texto_inativo = QColor("#ff6b6b")
        cor_lucro_positivo = QColor("#51cf66")
        cor_lucro_negativo = QColor("#ff6b6b")

        for row, produto in enumerate(produtos):
            dados, lucro, markup = ProdutoUtils.formatar_item_produto(produto)

            # ID usando NumericTableWidgetItem
            item_id = NumericTableWidgetItem(str(produto.id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_id.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 0, item_id)

            # Nome
            item_nome = QTableWidgetItem(dados['nome'])
            if not produto.ativo:
                item_nome.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 1, item_nome)

            # Cor
            item_cor = QTableWidgetItem(produto.cor or "")
            item_cor.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_cor.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 2, item_cor)

            # Tamanho
            item_tamanho = QTableWidgetItem(produto.tamanho or "")
            item_tamanho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_tamanho.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 3, item_tamanho)

            # Referência
            item_ref = QTableWidgetItem(produto.referencia or "")
            item_ref.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_ref.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 4, item_ref)

            # CORREÇÃO: Preços usando NumericTableWidgetItem com valor numérico
            item_custo = NumericTableWidgetItem(dados['preco_custo'])
            item_custo.setData(Qt.ItemDataRole.UserRole, produto.preco_custo)  # Armazenar valor numérico
            item_custo.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if not produto.ativo:
                item_custo.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 5, item_custo)

            item_venda = NumericTableWidgetItem(dados['preco_venda'])
            item_venda.setData(Qt.ItemDataRole.UserRole, produto.preco_venda)  # Armazenar valor numérico
            item_venda.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if not produto.ativo:
                item_venda.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 6, item_venda)

            # Estoque usando NumericTableWidgetItem
            item_estoque = NumericTableWidgetItem(dados['estoque'])
            item_estoque.setData(Qt.ItemDataRole.UserRole, produto.estoque)
            item_estoque.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not produto.ativo:
                item_estoque.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 7, item_estoque)

            # Lucro % usando NumericTableWidgetItem
            item_lucro = NumericTableWidgetItem(dados['lucro'])
            item_lucro.setData(Qt.ItemDataRole.UserRole, lucro)
            item_lucro.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if produto.ativo:
                if lucro > 25:
                    item_lucro.setForeground(cor_lucro_positivo)
                elif lucro < 25:
                    item_lucro.setForeground(cor_lucro_negativo)
            else:
                item_lucro.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 8, item_lucro)

            # Markup % usando NumericTableWidgetItem
            item_markup = NumericTableWidgetItem(dados['markup'])
            item_markup.setData(Qt.ItemDataRole.UserRole, markup)
            item_markup.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if produto.ativo:
                if markup > 50:
                    item_markup.setForeground(cor_lucro_positivo)
                elif markup < 50:
                    item_markup.setForeground(cor_lucro_negativo)
            else:
                item_markup.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 9, item_markup)

            # Fornecedor
            item_fornecedor = QTableWidgetItem(dados['fornecedor'])
            if not produto.ativo:
                item_fornecedor.setForeground(cor_texto_inativo)
            self.tabela_produtos.setItem(row, 10, item_fornecedor)

        # Reabilitar ordenação
        self.tabela_produtos.setSortingEnabled(True)
        # Ordenar por ID decrescente por padrão
        self.tabela_produtos.sortItems(0, Qt.SortOrder.DescendingOrder)

# ========== CORREÇÃO 3: Para VendaView (valores monetários em vendas) ==========

class VendaViewFixed:
    """Exemplo de correção para VendaView"""

    def _preencher_tabela_vendas(self, vendas):
        """Versão corrigida para vendas"""
        # Desabilitar ordenação durante preenchimento
        self.tabela_vendas.setSortingEnabled(False)

        for row, venda in enumerate(vendas):
            # ID usando NumericTableWidgetItem
            item_id = NumericTableWidgetItem(str(venda[0]))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 0, item_id)

            # Cliente
            cliente_nome = str(venda[8]) if len(venda) > 8 and venda[8] else "Cliente não informado"
            self.tabela_vendas.setItem(row, 1, QTableWidgetItem(cliente_nome))

            # Data
            data_item = QTableWidgetItem(formatar_data(venda[2], '%Y-%m-%d', '%d/%m/%Y'))
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 2, data_item)

            # Pagamento
            pagamento_item = QTableWidgetItem(str(venda[4]))
            pagamento_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 3, pagamento_item)

            # CORREÇÃO: Desconto usando NumericTableWidgetItem
            desconto_valor = float(venda[7]) if venda[7] else 0
            desconto_item = NumericTableWidgetItem(formatar_moeda(desconto_valor))
            desconto_item.setData(Qt.ItemDataRole.UserRole, desconto_valor)  # Valor numérico para ordenação
            desconto_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.tabela_vendas.setItem(row, 4, desconto_item)

            # CORREÇÃO: Total usando NumericTableWidgetItem
            total_valor = float(venda[3]) if venda[3] else 0
            total_item = NumericTableWidgetItem(formatar_moeda(total_valor))
            total_item.setData(Qt.ItemDataRole.UserRole, total_valor)  # Valor numérico para ordenação
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.tabela_vendas.setItem(row, 5, total_item)

        # Reabilitar ordenação
        self.tabela_vendas.setSortingEnabled(True)
        # Ordenar por ID decrescente por padrão
        self.tabela_vendas.sortItems(0, Qt.SortOrder.DescendingOrder)

# ========== CORREÇÃO UNIVERSAL: Função helper ==========

def aplicar_correcoes_tabela(tabela_widget, dados_originais, funcao_preenchimento):
    """
    Função helper universal para aplicar as correções em qualquer tabela

    Args:
        tabela_widget: O widget da tabela (QTableWidget)
        dados_originais: Lista com os dados originais não filtrados
        funcao_preenchimento: Função que preenche a tabela
    """
    # Desabilitar ordenação durante preenchimento
    tabela_widget.setSortingEnabled(False)

    # Preencher tabela
    funcao_preenchimento(dados_originais)

    # Reabilitar ordenação
    tabela_widget.setSortingEnabled(True)

    # Ordenar por ID (coluna 0) em ordem decrescente
    tabela_widget.sortItems(0, Qt.SortOrder.DescendingOrder)
