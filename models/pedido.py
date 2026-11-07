# \erp\models\pedido.py
import sqlite3
from datetime import datetime

from database import Database

from .base_model import BaseModel


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
        conn = Database().get_connection()
        cursor = conn.cursor()

        try:
            if self.id:
                query = """
                    UPDATE pedidos
                    SET fornecedor_id=?, data_pedido=?, data_recebimento=?,
                        valor_total=?, valor_frete=?, desconto=?, observacao=?, status=?
                    WHERE id=?
                """
                params = (
                    self.fornecedor_id,
                    self.data_pedido,
                    self.data_recebimento,
                    self.valor_total,
                    self.valor_frete,
                    self.desconto,
                    self.observacao,
                    self.status,
                    self.id,
                )
            else:
                query = """
                    INSERT INTO pedidos
                    (fornecedor_id, data_pedido, data_recebimento, valor_total,
                     valor_frete, desconto, observacao, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    self.fornecedor_id,
                    self.data_pedido,
                    self.data_recebimento,
                    self.valor_total,
                    self.valor_frete,
                    self.desconto,
                    self.observacao,
                    self.status,
                )

            cursor.execute(query, params)
            conn.commit()

            if not self.id:
                self.id = cursor.lastrowid

            return self.id
        except Exception:
            conn.rollback()
            raise

    @classmethod
    def buscar_por_id(cls, id):
        """MÉTODO CORRIGIDO: Query explícita para garantir ordem correta dos campos"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Query explícita com nomes dos campos para evitar problemas de ordem
            query = """
                SELECT
                    id,
                    fornecedor_id,
                    data_pedido,
                    data_recebimento,
                    valor_total,
                    valor_frete,
                    COALESCE(desconto, 0) as desconto,
                    observacao,
                    status
                FROM pedidos
                WHERE id = ?
            """
            cursor.execute(query, (id,))
            result = cursor.fetchone()

            if result:
                # Mapear explicitamente cada campo para evitar confusão
                return cls(
                    id=result[0],  # id
                    fornecedor_id=result[1],  # fornecedor_id
                    data_pedido=result[2],  # data_pedido
                    data_recebimento=result[3],  # data_recebimento
                    valor_total=result[4],  # valor_total
                    valor_frete=result[5],  # valor_frete
                    desconto=result[6],  # desconto
                    observacao=result[7],  # observacao
                    status=result[8],  # status
                )
            return None
        except Exception as e:
            print(f"Erro ao buscar pedido por ID: {e}")
            return None
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    @classmethod
    def buscar_todos(cls, status=None):
        """MÉTODO CORRIGIDO: Query explícita para garantir ordem correta dos campos"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Query explícita com nomes dos campos
            query = """
                SELECT
                    id,
                    fornecedor_id,
                    data_pedido,
                    data_recebimento,
                    valor_total,
                    valor_frete,
                    COALESCE(desconto, 0) as desconto,
                    observacao,
                    status
                FROM pedidos
            """
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY data_pedido DESC"

            cursor.execute(query, params)
            results = cursor.fetchall()

            pedidos = []
            for result in results:
                pedido = cls(
                    id=result[0],  # id
                    fornecedor_id=result[1],  # fornecedor_id
                    data_pedido=result[2],  # data_pedido
                    data_recebimento=result[3],  # data_recebimento
                    valor_total=result[4],  # valor_total
                    valor_frete=result[5],  # valor_frete
                    desconto=result[6],  # desconto
                    observacao=result[7],  # observacao
                    status=result[8],  # status
                )
                pedidos.append(pedido)

            return pedidos

        except Exception as e:
            print(f"Erro ao buscar todos os pedidos: {e}")
            return []
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    def marcar_como_recebido(self):
        self.status = "recebido"
        self.data_recebimento = datetime.now().date()
        self.salvar()

    def cancelar(self):
        self.status = "cancelado"
        self.salvar()

    def obter_fornecedor(self):
        from models.fornecedor import Fornecedor

        return (
            Fornecedor.buscar_por_id(self.fornecedor_id) if self.fornecedor_id else None
        )

    def obter_itens(self):
        """MÉTODO MODIFICADO para incluir valor de venda"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    ip.id,           -- 0
                    ip.pedido_id,    -- 1
                    ip.produto_id,   -- 2
                    ip.quantidade,   -- 3
                    ip.preco_custo,  -- 4
                    ip.subtotal,     -- 5
                    p.nome,          -- 6
                    p.estoque,       -- 7
                    COALESCE(ip.preco_venda, ip.preco_custo * 1.3) as preco_venda   -- 8
                FROM itens_pedido ip
                JOIN produtos p ON ip.produto_id = p.id
                WHERE ip.pedido_id = ?
            """
            cursor.execute(query, (self.id,))
            results = cursor.fetchall()
            return results if results else []
        except Exception as e:
            print(f"Erro ao obter itens do pedido: {e}")
            return []
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    def calcular_subtotal_produtos(self):
        """Calcula o subtotal apenas dos produtos (sem frete e desconto)"""
        itens = self.obter_itens()
        return sum(item[5] for item in itens)  # item[5] é o subtotal

    def calcular_total_com_desconto_frete(self):
        """Calcula o total final: Subtotal - Desconto + Frete"""
        subtotal = self.calcular_subtotal_produtos()
        return max(0, subtotal - self.desconto + self.valor_frete)

    def recalcular_total(self):
        """Recalcula o total baseado nos itens + frete - desconto"""
        self.valor_total = self.calcular_total_com_desconto_frete()
        return self.valor_total
