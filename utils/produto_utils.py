# \erp\utils\produto_utils.py
from PyQt6.QtGui import QBrush, QColor

from utils.helpers import formatar_moeda


class ProdutoUtils:
    @staticmethod
    def calcular_lucro_percentual(preco_custo, preco_venda):
        """Calcula o percentual de lucro sobre o preço de venda"""
        if preco_venda == 0:
            return 0
        return ((preco_venda - preco_custo) / preco_venda) * 100

    @staticmethod
    def calcular_markup_percentual(preco_custo, preco_venda):
        """Calcula o percentual de markup sobre o preço de custo"""
        if preco_custo == 0:
            return 0
        return ((preco_venda - preco_custo) / preco_custo) * 100

    @staticmethod
    def aplicar_cores_lucro(item, valor):
        """Aplica cores baseadas no valor de lucro/markup"""
        if valor > 0:
            item.setForeground(QBrush(QColor(0, 128, 0)))
        elif valor < 0:
            item.setForeground(QBrush(QColor(200, 50, 50)))

    @staticmethod
    def formatar_item_produto(produto, incluir_fornecedor=True):
        """Formata os dados do produto para exibição"""
        lucro = ProdutoUtils.calcular_lucro_percentual(
            produto.preco_custo, produto.preco_venda
        )
        markup = ProdutoUtils.calcular_markup_percentual(
            produto.preco_custo, produto.preco_venda
        )

        dados = {
            "id": str(produto.id),
            "nome": produto.nome or "",
            "preco_custo": formatar_moeda(produto.preco_custo),
            "preco_venda": formatar_moeda(produto.preco_venda),
            "estoque": str(produto.estoque),
            "lucro": f"{lucro:.1f}%",
            "markup": f"{markup:.1f}%",
            "fornecedor": getattr(produto, "fornecedor_nome", "Nenhum")
            if incluir_fornecedor
            else "",
        }

        return dados, lucro, markup

    def validar_produto(nome, preco_custo, preco_venda):
        erros = []
        if not nome.strip():
            erros.append("O nome do produto é obrigatório")
        if preco_custo < 0:
            erros.append("Preço de custo não pode ser negativo")
        if preco_venda < 0:
            erros.append("Preço de venda não pode ser negativo")

        # Comentado ou removido para permitir venda zero
        # if preco_venda < preco_custo:
        #     erros.append("Preço de venda não pode ser menor que preço de custo")

        return erros
