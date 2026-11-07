# \erp\models\pedido.py
import logging
from datetime import datetime

from mainerp.data.database import obter_database
from mainerp.data.money import de_centavos, para_centavos

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class Pedido(BaseModel):
    TABLE_NAME = "pedidos"

    def __init__(
        self,
        id=None,
        fornecedor_id=None,
        data_pedido=None,
        data_recebimento=None,
        valor_total: float = 0.0,
        valor_frete: float = 0.0,
        desconto: float = 0.0,
        observacao=None,
        status="pendente",
    ):
        self.id = id
        self.fornecedor_id = fornecedor_id
        self.data_pedido = data_pedido or datetime.now().date()
        self.data_recebimento = data_recebimento
        self.valor_total = valor_total
        self.valor_frete = valor_frete
        self.desconto = desconto
        self.observacao = observacao
        self.status = status

    def salvar(self):
        database = obter_database()
        total_centavos = para_centavos(self.valor_total)
        frete_centavos = para_centavos(self.valor_frete)
        desconto_centavos = para_centavos(self.desconto)
        self.valor_total = float(de_centavos(total_centavos))
        self.valor_frete = float(de_centavos(frete_centavos))
        self.desconto = float(de_centavos(desconto_centavos))
        with database.transacao() as cursor:
            if self.id:
                query = """
                    UPDATE pedidos
                    SET fornecedor_id=?, data_pedido=?, data_recebimento=?,
                        valor_total=?, valor_frete=?, desconto=?,
                        valor_total_centavos=?, valor_frete_centavos=?,
                        desconto_centavos=?, observacao=?, status=?
                    WHERE id=?
                """
                params = (
                    self.fornecedor_id,
                    self.data_pedido,
                    self.data_recebimento,
                    self.valor_total,
                    self.valor_frete,
                    self.desconto,
                    total_centavos,
                    frete_centavos,
                    desconto_centavos,
                    self.observacao,
                    self.status,
                    self.id,
                )
            else:
                query = """
                    INSERT INTO pedidos
                    (fornecedor_id, data_pedido, data_recebimento, valor_total,
                     valor_frete, desconto, valor_total_centavos,
                     valor_frete_centavos, desconto_centavos, observacao, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    self.fornecedor_id,
                    self.data_pedido,
                    self.data_recebimento,
                    self.valor_total,
                    self.valor_frete,
                    self.desconto,
                    total_centavos,
                    frete_centavos,
                    desconto_centavos,
                    self.observacao,
                    self.status,
                )

            cursor.execute(query, params)
            if not self.id:
                self.id = cursor.lastrowid

            return self.id

    @classmethod
    def buscar_por_id(cls, id):
        """MÉTODO CORRIGIDO: Query explícita para garantir ordem correta dos campos"""
        try:
            # Query explícita com nomes dos campos para evitar problemas de ordem
            query = """
                SELECT
                    id,
                    fornecedor_id,
                    data_pedido,
                    data_recebimento,
                    valor_total_centavos,
                    valor_frete_centavos,
                    COALESCE(desconto_centavos, 0) as desconto_centavos,
                    observacao,
                    status
                FROM pedidos
                WHERE id = ?
            """
            with obter_database().transacao() as cursor:
                cursor.execute(query, (id,))
                result = cursor.fetchone()

            if result:
                # Mapear explicitamente cada campo para evitar confusão
                return cls(
                    id=result[0],  # id
                    fornecedor_id=result[1],  # fornecedor_id
                    data_pedido=result[2],  # data_pedido
                    data_recebimento=result[3],  # data_recebimento
                    valor_total=float(de_centavos(result[4])),
                    valor_frete=float(de_centavos(result[5])),
                    desconto=float(de_centavos(result[6])),
                    observacao=result[7],  # observacao
                    status=result[8],  # status
                )
            return None
        except Exception:
            logger.exception("Erro ao buscar pedido por ID")
            return None

    @classmethod
    def buscar_todos(cls, status=None):
        """MÉTODO CORRIGIDO: Query explícita para garantir ordem correta dos campos"""
        try:
            # Query explícita com nomes dos campos
            query = """
                SELECT
                    id,
                    fornecedor_id,
                    data_pedido,
                    data_recebimento,
                    valor_total_centavos,
                    valor_frete_centavos,
                    COALESCE(desconto_centavos, 0) as desconto_centavos,
                    observacao,
                    status
                FROM pedidos
            """
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY data_pedido DESC"

            with obter_database().transacao() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

            pedidos = []
            for result in results:
                pedido = cls(
                    id=result[0],  # id
                    fornecedor_id=result[1],  # fornecedor_id
                    data_pedido=result[2],  # data_pedido
                    data_recebimento=result[3],  # data_recebimento
                    valor_total=float(de_centavos(result[4])),
                    valor_frete=float(de_centavos(result[5])),
                    desconto=float(de_centavos(result[6])),
                    observacao=result[7],  # observacao
                    status=result[8],  # status
                )
                pedidos.append(pedido)

            return pedidos

        except Exception:
            logger.exception("Erro ao buscar todos os pedidos")
            return []

    @classmethod
    def buscar_para_listagem(
        cls, data_inicio=None, data_fim=None, fornecedor_id=None, status=None
    ):
        """Busca pedidos com fornecedor e filtros usados pela tela de listagem."""
        query = """
            SELECT
                p.id,
                p.fornecedor_id,
                p.data_pedido,
                p.data_recebimento,
                p.valor_total_centavos,
                p.valor_frete_centavos,
                p.observacao,
                p.status,
                COALESCE(p.desconto_centavos, 0) as desconto_centavos,
                f.nome as fornecedor_nome
            FROM pedidos p
            LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
            WHERE 1=1
        """
        params = []

        if data_inicio:
            query += " AND p.data_pedido >= ?"
            params.append(data_inicio)

        if data_fim:
            query += " AND p.data_pedido <= ?"
            params.append(data_fim)

        if fornecedor_id:
            query += " AND p.fornecedor_id = ?"
            params.append(fornecedor_id)

        if status:
            query += " AND p.status = ?"
            params.append(status)

        query += " ORDER BY p.data_pedido DESC, p.id DESC"

        try:
            with obter_database().transacao() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
            return [
                (
                    *result[:4],
                    float(de_centavos(result[4])),
                    float(de_centavos(result[5])),
                    *result[6:8],
                    float(de_centavos(result[8])),
                    *result[9:],
                )
                for result in results
            ]
        except Exception:
            logger.exception("Erro ao buscar pedidos para listagem")
            return []

    def marcar_como_recebido(self):
        self.status = "recebido"
        self.data_recebimento = datetime.now().date()
        self.salvar()

    def cancelar(self):
        self.status = "cancelado"
        self.salvar()

    def obter_fornecedor(self):
        from mainerp.data.models.fornecedor import Fornecedor

        return (
            Fornecedor.buscar_por_id(self.fornecedor_id) if self.fornecedor_id else None
        )

    def obter_itens(self):
        """MÉTODO MODIFICADO para incluir valor de venda"""
        try:
            query = """
                SELECT
                    ip.id,           -- 0
                    ip.pedido_id,    -- 1
                    ip.produto_id,   -- 2
                    ip.quantidade,   -- 3
                    ip.preco_custo_centavos,  -- 4
                    ip.subtotal_centavos,     -- 5
                    p.nome,          -- 6
                    p.estoque,       -- 7
                    COALESCE(
                        ip.preco_venda_centavos,
                        CAST(ROUND(ip.preco_custo_centavos * 1.3) AS INTEGER)
                    ) as preco_venda_centavos   -- 8
                FROM itens_pedido ip
                JOIN produtos p ON ip.produto_id = p.id
                WHERE ip.pedido_id = ?
            """
            with obter_database().transacao() as cursor:
                cursor.execute(query, (self.id,))
                results = cursor.fetchall()
            return [
                (
                    *result[:4],
                    float(de_centavos(result[4])),
                    float(de_centavos(result[5])),
                    *result[6:8],
                    float(de_centavos(result[8])),
                )
                for result in results
            ]
        except Exception:
            logger.exception("Erro ao obter itens do pedido %s", self.id)
            return []

    def calcular_subtotal_produtos(self):
        """Calcula o subtotal apenas dos produtos (sem frete e desconto)"""
        itens = self.obter_itens()
        subtotal_centavos = sum(para_centavos(item[5]) for item in itens)
        return float(de_centavos(subtotal_centavos))

    def calcular_total_com_desconto_frete(self):
        """Calcula o total final: Subtotal - Desconto + Frete"""
        total_centavos = (
            para_centavos(self.calcular_subtotal_produtos())
            - para_centavos(self.desconto)
            + para_centavos(self.valor_frete)
        )
        return float(de_centavos(max(0, total_centavos)))

    def recalcular_total(self):
        """Recalcula o total baseado nos itens + frete - desconto"""
        self.valor_total = self.calcular_total_com_desconto_frete()
        return self.valor_total
