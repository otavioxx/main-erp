import sqlite3
import time
from collections.abc import Sequence
from typing import Any

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.database import obter_database


class DatabaseUtils:
    @staticmethod
    def executar_query(query: str, params: Sequence[Any] | None = None) -> Any:
        """Executa query genérica"""
        with obter_database().transacao() as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return cursor.lastrowid

    @staticmethod
    def buscar_por_tabela(tabela: str, id: int) -> tuple | None:
        """Busca registro por ID em qualquer tabela"""
        query = f"SELECT * FROM {tabela} WHERE id = ?"
        resultado = DatabaseUtils.executar_query(query, (id,))
        return resultado[0] if resultado else None

    @staticmethod
    def buscar_todos(tabela: str, ordenar_por: str | None = None) -> list[tuple]:
        """Busca todos os registros de uma tabela"""
        query = f"SELECT * FROM {tabela}"
        if ordenar_por:
            query += f" ORDER BY {ordenar_por}"
        return DatabaseUtils.executar_query(query)

    @staticmethod
    def executar_com_retry(
        query: str,
        params: Sequence[Any] | None = None,
        max_tentativas: int = 3,
    ) -> Any:
        """Executa uma query com retry em caso de database locked"""
        tentativa = 0
        while tentativa < max_tentativas:
            try:
                with obter_database().transacao() as cursor:
                    cursor.execute(query, params or ())
                    if query.strip().upper().startswith("SELECT"):
                        return cursor.fetchall()
                    return cursor.lastrowid

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and tentativa < max_tentativas - 1:
                    tentativa += 1
                    time.sleep(0.1 * tentativa)
                    continue
                else:
                    raise

    @staticmethod
    def buscar_com_filtros(
        tabela: str,
        filtros: dict[str, Any] | None = None,
        ordenar_por: str | None = None,
    ) -> list[tuple]:
        """Busca registros com filtros dinâmicos"""
        query = f"SELECT * FROM {tabela}"
        params = []

        if filtros:
            conditions = []
            for campo, valor in filtros.items():
                conditions.append(f"{campo} = ?")
                params.append(valor)
            query += " WHERE " + " AND ".join(conditions)

        if ordenar_por:
            query += f" ORDER BY {ordenar_por}"

        return DatabaseUtils.executar_query(query, params)

    @staticmethod
    def buscar_paginado(
        tabela: str,
        pagina: int = 1,
        itens_por_pagina: int = 50,
        ordenar_por: str = "id",
    ) -> list[tuple]:
        """Busca registros com paginação"""
        offset = (pagina - 1) * itens_por_pagina
        query = f"SELECT * FROM {tabela} ORDER BY {ordenar_por} LIMIT ? OFFSET ?"
        return DatabaseUtils.executar_query(query, (itens_por_pagina, offset))

    @staticmethod
    def excluir_por_id(tabela: str, id: int) -> bool:
        """Exclui registro por ID"""
        query = f"DELETE FROM {tabela} WHERE id = ?"
        try:
            DatabaseUtils.executar_query(query, (id,))
            return True
        except sqlite3.Error:
            registrar_excecao(
                __name__,
                "Exception handled in DatabaseUtils.excluir_por_id in utils/database_utils.py",
            )
            return False

    @staticmethod
    def buscar_itens_pedido(pedido_id):
        """
        Busca todos os itens de um pedido específico
        """
        query = """
            SELECT pi.id, pi.produto_id, p.nome as produto_nome, pi.quantidade,
                   pi.preco_custo as preco_unitario, pi.subtotal
            FROM itens_pedido pi
            INNER JOIN produtos p ON pi.produto_id = p.id
            WHERE pi.pedido_id = ?
            ORDER BY p.nome
        """
        with obter_database().transacao() as cursor:
            cursor.execute(query, (pedido_id,))
            return cursor.fetchall()
