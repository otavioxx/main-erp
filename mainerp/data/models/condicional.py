# \erp\model\condicional.py
import logging
from datetime import datetime

from mainerp.data.database import obter_database

logger = logging.getLogger(__name__)


class Condicional:
    def __init__(
        self,
        id=None,
        cliente_id=None,
        data_condicional=None,
        data_prevista_devolucao=None,
        status="ativa",
        observacao="",
        desconto=0.0,
    ):
        self.id = id
        self.cliente_id = cliente_id
        self.data_condicional = data_condicional or datetime.now().date()
        self.data_prevista_devolucao = data_prevista_devolucao
        self.status = status
        self.observacao = observacao
        self.desconto = desconto
        self.itens = []

    def salvar(self):
        with obter_database().transacao() as cursor:
            cliente_id = self.cliente_id
            data_condicional = self.data_condicional
            data_prevista_devolucao = self.data_prevista_devolucao
            status = self.status
            observacao = self.observacao
            desconto = self.desconto

            if self.id:
                cursor.execute(
                    """
                    UPDATE condicionais
                    SET cliente_id=?, data_condicional=?, data_prevista_devolucao=?,
                        status=?, observacao=?, desconto=?
                    WHERE id=?
                """,
                    (
                        cliente_id,
                        data_condicional,
                        data_prevista_devolucao,
                        status,
                        observacao,
                        desconto,
                        self.id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO condicionais
                    (cliente_id, data_condicional, data_prevista_devolucao, status, observacao, desconto)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        cliente_id,
                        data_condicional,
                        data_prevista_devolucao,
                        status,
                        observacao,
                        desconto,
                    ),
                )
                self.id = cursor.lastrowid

            self.salvar_itens(cursor)
            return self.id

    def salvar_itens(self, cursor):
        cursor.execute(
            "DELETE FROM itens_condicional WHERE condicional_id = ?", (self.id,)
        )

        for item in self.itens:
            cursor.execute(
                """
                INSERT INTO itens_condicional
                (condicional_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
            """,
                (
                    self.id,
                    item["produto_id"],
                    item["quantidade"],
                    item["preco_unitario"],
                ),
            )

    @staticmethod
    def buscar_por_id(condicional_id):
        if not isinstance(condicional_id, int):
            try:
                condicional_id = int(condicional_id)
            except (ValueError, TypeError):
                return None

        try:
            with obter_database().transacao() as cursor:
                cursor.execute(
                    """
                SELECT c.id, c.cliente_id, c.data_condicional,
                    c.data_prevista_devolucao, c.status, c.observacao, c.desconto,
                    cli.nome as cliente_nome
                FROM condicionais c
                LEFT JOIN clientes cli ON c.cliente_id = cli.id
                WHERE c.id = ?
            """,
                    (condicional_id,),
                )
                condicional_data = cursor.fetchone()

                if not condicional_data:
                    return None

                condicional = Condicional(
                    id=condicional_data[0],
                    cliente_id=condicional_data[1],
                    data_condicional=datetime.strptime(
                        condicional_data[2], "%Y-%m-%d"
                    ).date()
                    if condicional_data[2]
                    else None,
                    data_prevista_devolucao=datetime.strptime(
                        condicional_data[3], "%Y-%m-%d"
                    ).date()
                    if condicional_data[3]
                    else None,
                    status=condicional_data[4],
                    observacao=condicional_data[5],
                    desconto=float(condicional_data[6]) if condicional_data[6] else 0.0,
                )

                cursor.execute(
                    """
                SELECT ic.id, ic.condicional_id, ic.produto_id, ic.quantidade,
                    ic.preco_unitario, p.nome as produto_nome, p.estoque
                FROM itens_condicional ic
                JOIN produtos p ON ic.produto_id = p.id
                WHERE ic.condicional_id = ?
            """,
                    (condicional_id,),
                )

                itens = cursor.fetchall()
            for item in itens:
                condicional.itens.append(
                    {
                        "id": item[0],
                        "produto_id": item[2],
                        "produto_nome": item[5],
                        "quantidade": item[3],
                        "preco_unitario": item[4],
                        "estoque_atual": item[6],
                    }
                )

            return condicional

        except Exception:
            logger.exception("Erro ao buscar condicional")
            return None

    @staticmethod
    def buscar_todas():
        try:
            with obter_database().transacao() as cursor:
                cursor.execute("""
                SELECT c.id, c.cliente_id, c.data_condicional,
                    c.data_prevista_devolucao, c.status, c.observacao, c.desconto,
                    cli.nome as cliente_nome,
                    (SELECT COUNT(*) FROM itens_condicional WHERE condicional_id = c.id) as total_itens
                FROM condicionais c
                LEFT JOIN clientes cli ON c.cliente_id = cli.id
                ORDER BY c.data_condicional DESC
            """)

                condicionais = cursor.fetchall()
            return condicionais

        except Exception:
            logger.exception("Erro ao buscar todas as condicionais")
            return []

    def marcar_como_devolvida(self):
        self.status = "devolvida"
        self.salvar()

    def marcar_como_convertida(self):
        self.status = "convertida"
        self.salvar()

    def esta_vencida(self):
        if not self.data_prevista_devolucao or self.status != "ativa":
            return False
        hoje = datetime.now().date()
        return self.data_prevista_devolucao < hoje

    def calcular_subtotal(self):
        """Calcula o subtotal (sem desconto)"""
        subtotal = 0
        for item in self.itens:
            subtotal += item["quantidade"] * item["preco_unitario"]
        return subtotal

    def calcular_total(self):
        """Calcula o total final (com desconto aplicado)"""
        subtotal = self.calcular_subtotal()
        return max(0, subtotal - self.desconto)

    @staticmethod
    def criar_tabelas():
        """Cria as tabelas necessárias para o sistema de condicionais"""
        try:
            with obter_database().transacao() as cursor:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS condicionais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    data_saida DATE NOT NULL,
                    data_retorno_prevista DATE,
                    observacoes TEXT,
                    status TEXT DEFAULT 'aberto',
                    desconto REAL DEFAULT 0,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            """)

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS itens_condicional (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    condicional_id INTEGER NOT NULL,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco_unitario REAL NOT NULL,
                    devolvido INTEGER DEFAULT 0,
                    FOREIGN KEY (condicional_id) REFERENCES condicionais (id) ON DELETE CASCADE,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            """)

            logger.debug("Tabelas de condicionais criadas/verificadas com sucesso")

        except Exception:
            logger.exception("Erro ao criar tabelas de condicionais")
            raise
