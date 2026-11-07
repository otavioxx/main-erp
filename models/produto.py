import sqlite3

from app_logging import registrar_excecao

# \erp\model\produto.py
from models.base_model import BaseModel


class Produto(BaseModel):
    TABLE_NAME = "produtos"

    def __init__(
        self,
        id=None,
        nome="",
        preco_custo=0.0,
        preco_venda=0.0,
        estoque=0,
        fornecedor_id=None,
        ativo=True,
        tamanho="",
        cor="",
        ea="",
        referencia="",
        fornecedor_nome="Nenhum",
    ):
        self.id = id
        self.nome = nome
        self.preco_custo = preco_custo
        self.preco_venda = preco_venda
        self.estoque = estoque
        self.fornecedor_id = fornecedor_id
        self.ativo = ativo
        self.tamanho = tamanho
        self.cor = cor
        self.ea = ea
        self.referencia = referencia
        self.fornecedor_nome = fornecedor_nome

    def salvar(self):
        from utils.produto_utils import ProdutoUtils

        erros = ProdutoUtils.validar_produto(
            self.nome, self.preco_custo, self.preco_venda
        )
        if erros:
            raise ValueError("\n".join(erros))

        if self.id:
            query = """
                UPDATE produtos SET nome=?, preco_custo=?, preco_venda=?, estoque=?,
                fornecedor_id=?, ativo=?, tamanho=?, cor=?, ea=?, referencia=?
                WHERE id=?
            """
            params = (
                self.nome,
                self.preco_custo,
                self.preco_venda,
                self.estoque,
                self.fornecedor_id,
                self.ativo,
                self.tamanho,
                self.cor,
                self.ea,
                self.referencia,
                self.id,
            )
        else:
            query = """
                INSERT INTO produtos (nome, preco_custo, preco_venda, estoque, fornecedor_id,
                ativo, tamanho, cor, ea, referencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.nome,
                self.preco_custo,
                self.preco_venda,
                self.estoque,
                self.fornecedor_id,
                self.ativo,
                self.tamanho,
                self.cor,
                self.ea,
                self.referencia,
            )

        result = self.executar_query(query, params)
        if not self.id:
            if not isinstance(result, int):
                raise RuntimeError("A inserção do produto não retornou um ID.")
            self.id = result
        return self.id

    def atualizar_estoque(self, nova_quantidade):
        self.estoque = nova_quantidade
        self.salvar()

    def pode_ser_inativado(self):
        """
        Verifica se o produto pode ser inativado.
        Retorna um dicionário com 'pode' (bool) e 'motivos' (lista de strings)
        """
        motivos = []

        # Verifica se tem estoque
        if self.estoque > 0:
            motivos.append(f"Produto possui estoque: {self.estoque} unidades")

        # Verifica se está em pedidos ativos
        pedidos_count = self._contar_pedidos_ativos()
        if pedidos_count > 0:
            motivos.append(f"Produto está em {pedidos_count} pedido(s) ativo(s)")

        # Verifica se está em condicionais ativas
        condicionais_count = self._contar_condicionais_ativas()
        if condicionais_count > 0:
            motivos.append(
                f"Produto está em {condicionais_count} condicional(ais) ativa(s)"
            )

        return {"pode": len(motivos) == 0, "motivos": motivos}

    def _contar_pedidos_ativos(self):
        """Conta quantos pedidos ativos contêm este produto"""
        try:
            query = """
                SELECT COUNT(DISTINCT p.id)
                FROM pedidos p
                INNER JOIN itens_pedido ip ON p.id = ip.pedido_id
                WHERE ip.produto_id = ? AND p.status IN ('aberto', 'pendente', 'processando')
            """
            result = self.executar_query(query, (self.id,))
            if not isinstance(result, list):
                raise TypeError("A consulta de pedidos ativos não retornou uma lista.")
            return result[0][0] if result else 0
        except sqlite3.Error:
            # Se a tabela não existir ou houver erro, considera 0
            registrar_excecao(
                __name__,
                "Exception handled in Produto._contar_pedidos_ativos in models/produto.py",
            )
            return 0

    def _contar_condicionais_ativas(self):
        """Conta quantas condicionais ativas contêm este produto"""
        try:
            query = """
                SELECT COUNT(DISTINCT c.id)
                FROM condicionais c
                INNER JOIN itens_condicional ic ON c.id = ic.condicional_id
                WHERE ic.produto_id = ? AND c.status = 'ativa'
            """
            result = self.executar_query(query, (self.id,))
            if not isinstance(result, list):
                raise TypeError(
                    "A consulta de condicionais ativas não retornou uma lista."
                )
            return result[0][0] if result else 0
        except sqlite3.Error:
            # Se a tabela não existir ou houver erro, considera 0
            registrar_excecao(
                __name__,
                "Exception handled in Produto._contar_condicionais_ativas in models/produto.py",
            )
            return 0

    def inativar(self):
        """Inativa o produto após verificar se é possível"""
        verificacao = self.pode_ser_inativado()
        if not verificacao["pode"]:
            raise ValueError(
                "Produto não pode ser inativado:\n" + "\n".join(verificacao["motivos"])
            )

        self.ativo = False
        self.salvar()

    def reativar(self):
        self.ativo = True
        self.salvar()

    @staticmethod
    def buscar_todos(apenas_ativos=True):
        if apenas_ativos:
            query = """
                SELECT p.*, f.nome as fornecedor_nome
                FROM produtos p
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                WHERE p.ativo = 1
                ORDER BY p.nome
            """
        else:
            query = """
                SELECT p.*, f.nome as fornecedor_nome
                FROM produtos p
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                ORDER BY p.nome
            """

        resultados = Produto.executar_query(query)
        if not isinstance(resultados, list):
            raise TypeError("A consulta de produtos não retornou uma lista.")
        produtos = []
        for row in resultados:
            # Trata campos que podem não existir em DBs antigos
            produto = Produto(
                id=row[0],
                nome=row[1],
                preco_custo=row[2],
                preco_venda=row[3],
                estoque=row[4],
                fornecedor_id=row[5],
                ativo=row[6],
                tamanho=row[7] if len(row) > 7 else "",
                cor=row[8] if len(row) > 8 else "",
                ea=row[9] if len(row) > 9 else "",
                referencia=row[10] if len(row) > 10 else "",
                fornecedor_nome=row[11] if len(row) > 11 and row[11] else "Nenhum",
            )
            produtos.append(produto)

        return produtos

    @staticmethod
    def buscar_por_id(produto_id):
        query = """
            SELECT p.*, f.nome as fornecedor_nome
            FROM produtos p
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
            WHERE p.id = ?
        """

        resultados = Produto.executar_query(query, (produto_id,))
        if not isinstance(resultados, list):
            raise TypeError("A consulta por produto não retornou uma lista.")
        if resultados:
            row = resultados[0]
            produto = Produto(
                id=row[0],
                nome=row[1],
                preco_custo=row[2],
                preco_venda=row[3],
                estoque=row[4],
                fornecedor_id=row[5],
                ativo=row[6],
                tamanho=row[7] if len(row) > 7 else "",
                cor=row[8] if len(row) > 8 else "",
                ea=row[9] if len(row) > 9 else "",
                referencia=row[10] if len(row) > 10 else "",
                fornecedor_nome=row[11] if len(row) > 11 and row[11] else "Nenhum",
            )
            return produto
        return None
