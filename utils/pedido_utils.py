# \erp\utils\pedido_utils.py
import logging
from typing import Any

from utils.database_utils import DatabaseUtils
from utils.helpers import converter_data_string

logger = logging.getLogger(__name__)


class PedidoUtils:
    @staticmethod
    def salvar_itens_pedido(pedido_id: int, itens: list[dict[str, Any]]) -> bool:
        """Salva os itens do pedido no banco - MODIFICADO para incluir valor de venda"""
        for item in itens:
            query = """
                INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_custo, preco_venda, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (
                pedido_id,
                item["id"],
                item["quantidade"],
                item["preco_custo"],
                item["preco_venda"],
                item["subtotal"],
            )
            DatabaseUtils.executar_query(query, params)

        return True

    @staticmethod
    def filtrar_pedidos(
        data_inicio_str: str | None = None,
        data_fim_str: str | None = None,
        fornecedor_id: int | None = None,
        status: str | None = None,
    ) -> list[tuple]:
        """Filtra pedidos com os parâmetros fornecidos"""
        query = """
            SELECT p.*, f.nome as fornecedor_nome
            FROM pedidos p
            JOIN fornecedores f ON p.fornecedor_id = f.id
            WHERE 1=1
        """
        params = []

        # Converter datas
        data_inicio = (
            converter_data_string(data_inicio_str, "%d/%m/%Y")
            if data_inicio_str
            else None
        )
        data_fim = (
            converter_data_string(data_fim_str, "%d/%m/%Y") if data_fim_str else None
        )

        if data_inicio:
            query += " AND p.data_pedido >= ?"
            params.append(data_inicio.strftime("%Y-%m-%d"))

        if data_fim:
            query += " AND p.data_pedido <= ?"
            params.append(data_fim.strftime("%Y-%m-%d"))

        if fornecedor_id:
            query += " AND p.fornecedor_id = ?"
            params.append(fornecedor_id)

        if status:
            query += " AND p.status = ?"
            params.append(status)

        query += " ORDER BY p.data_pedido DESC"

        return DatabaseUtils.executar_query(query, tuple(params))

    @staticmethod
    def receber_pedido(pedido_id: int) -> bool:
        """
        Marca pedido como recebido e atualiza estoque, preço de custo E preço de venda
        MODIFICADO: Agora atualiza tanto preço de custo quanto preço de venda no produto
        """
        try:
            # Buscar itens do pedido - INCLUINDO PRECO_VENDA
            query_itens = """
                SELECT produto_id, quantidade, preco_custo, preco_venda
                FROM itens_pedido
                WHERE pedido_id = ?
            """
            itens = DatabaseUtils.executar_query(query_itens, (pedido_id,))

            if not itens:
                logger.warning("Nenhum item encontrado para o pedido %s", pedido_id)
                return False

            # Atualizar cada produto individualmente
            produtos_atualizados = 0
            for produto_id, quantidade, preco_custo, preco_venda in itens:
                # Verificar se preco_venda existe, senão usar fallback
                if preco_venda is None or preco_venda <= 0:
                    preco_venda = preco_custo * 1.3  # Margem padrão de 30%
                    logger.debug(
                        "Produto %s: usando preço de venda calculado (R$ %.2f)",
                        produto_id,
                        preco_venda,
                    )

                # Atualizar produto: preço de custo, preço de venda e estoque
                query_update = """
                    UPDATE produtos
                    SET preco_custo = ?, preco_venda = ?, estoque = estoque + ?
                    WHERE id = ?
                """
                DatabaseUtils.executar_query(
                    query_update, (preco_custo, preco_venda, quantidade, produto_id)
                )

                produtos_atualizados += 1
                logger.debug(
                    "Produto %s atualizado: custo=R$%.2f, venda=R$%.2f, +%s estoque",
                    produto_id,
                    preco_custo,
                    preco_venda,
                    quantidade,
                )

            # Marcar pedido como recebido
            query_pedido = """
                UPDATE pedidos
                SET status = 'recebido', data_recebimento = date('now')
                WHERE id = ?
            """
            DatabaseUtils.executar_query(query_pedido, (pedido_id,))

            logger.info(
                "Pedido %s marcado como recebido; %s produtos atualizados",
                pedido_id,
                produtos_atualizados,
            )
            return True

        except Exception:
            logger.exception("Erro ao receber pedido %s", pedido_id)
            raise

    @staticmethod
    def cancelar_pedido(pedido_id: int) -> bool:
        """Cancela o pedido"""
        query = "UPDATE pedidos SET status = 'cancelado' WHERE id = ?"
        DatabaseUtils.executar_query(query, (pedido_id,))
        return True

    @staticmethod
    def calcular_totais_pedido(
        itens: list[dict[str, Any]], frete: float = 0
    ) -> tuple[float, float]:
        """Calcula totais do pedido"""
        subtotal = sum(item["subtotal"] for item in itens)
        total = subtotal + frete
        return subtotal, total

    @staticmethod
    def atualizar_pedido(
        pedido_id: int,
        fornecedor_id: int,
        itens: list[dict[str, Any]],
        valor_frete: float,
        observacao: str | None = None,
    ) -> bool:
        """Atualiza um pedido existente - MODIFICADO para incluir valor de venda"""
        # Calcular total
        subtotal = sum(item["subtotal"] for item in itens)
        total = subtotal + valor_frete

        # Atualizar pedido
        query_pedido = """
            UPDATE pedidos
            SET fornecedor_id = ?, valor_total = ?, valor_frete = ?, observacao = ?
            WHERE id = ?
        """
        DatabaseUtils.executar_query(
            query_pedido, (fornecedor_id, total, valor_frete, observacao, pedido_id)
        )

        # Remover itens antigos e adicionar novos
        DatabaseUtils.executar_query(
            "DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,)
        )

        for item in itens:
            query_item = """
                INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_custo, preco_venda, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            DatabaseUtils.executar_query(
                query_item,
                (
                    pedido_id,
                    item["id"],
                    item["quantidade"],
                    item["preco_custo"],
                    item["preco_venda"],
                    item["subtotal"],
                ),
            )

        return True

    @staticmethod
    def obter_resumo_recebimento(pedido_id: int) -> dict[str, Any]:
        """
        Obtém resumo do que será atualizado ao receber o pedido
        Útil para confirmação antes do recebimento
        """
        try:
            query = """
                SELECT
                    ip.produto_id,
                    p.nome as produto_nome,
                    p.preco_custo as custo_atual,
                    p.preco_venda as venda_atual,
                    p.estoque as estoque_atual,
                    ip.preco_custo as novo_custo,
                    ip.preco_venda as nova_venda,
                    ip.quantidade
                FROM itens_pedido ip
                JOIN produtos p ON ip.produto_id = p.id
                WHERE ip.pedido_id = ?
            """
            itens = DatabaseUtils.executar_query(query, (pedido_id,))

            resumo = {
                "total_produtos": len(itens),
                "produtos": [],
                "total_investimento": 0,
            }

            for item in itens:
                produto_info = {
                    "id": item[0],
                    "nome": item[1],
                    "custo_atual": item[2],
                    "venda_atual": item[3],
                    "estoque_atual": item[4],
                    "novo_custo": item[5],
                    "nova_venda": item[6] or item[5] * 1.3,  # fallback se null
                    "quantidade": item[7],
                    "investimento": item[5] * item[7],
                }
                resumo["produtos"].append(produto_info)
                resumo["total_investimento"] += produto_info["investimento"]

            return resumo

        except Exception as e:
            logger.exception("Erro ao obter resumo do pedido")
            return {"error": str(e)}
