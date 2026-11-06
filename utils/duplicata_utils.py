from typing import List, Tuple
from utils.database_utils import DatabaseUtils
from datetime import datetime

class DuplicataUtils:
    @staticmethod
    def buscar_duplicatas_filtradas(status: str = None, cliente_id: int = None,
                                  data_inicio: str = None, data_fim: str = None) -> List[Tuple]:
        """Busca duplicatas com filtros complexos"""
        query = """
            SELECT
                d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                d.valor_parcela, d.data_vencimento, d.data_pagamento,
                d.status, c.nome as cliente_nome, v.total as venda_total,
                v.data_venda
            FROM duplicatas d
            LEFT JOIN clientes c ON d.cliente_id = c.id
            LEFT JOIN vendas v ON d.venda_id = v.id
            WHERE 1=1
        """
        params = []

        if status == "Abertas":
            query += " AND d.status = 'aberto'"
        elif status == "Vencidas":
            query += " AND d.status = 'aberto' AND d.data_vencimento < ?"
            params.append(datetime.now().strftime("%Y-%m-%d"))
        elif status == "Pagas":
            query += " AND d.status = 'pago'"

        if cliente_id:
            query += " AND d.cliente_id = ?"
            params.append(cliente_id)

        if data_inicio:
            query += " AND d.data_vencimento >= ?"
            params.append(data_inicio.strftime("%Y-%m-%d") if hasattr(data_inicio, 'strftime') else data_inicio)

        if data_fim:
            query += " AND d.data_vencimento <= ?"
            params.append(data_fim.strftime("%Y-%m-%d") if hasattr(data_fim, 'strftime') else data_fim)

        query += " ORDER BY d.data_vencimento, d.venda_id, d.numero_parcela"

        return DatabaseUtils.executar_query(query, params)

    @staticmethod
    def ajustar_parcelas_restantes(venda_id: int, numero_parcela_atual: int,
                                  diferenca: float) -> bool:
        """Ajusta as parcelas restantes de forma otimizada"""
        try:
            # Buscar parcelas restantes
            query_parcelas = '''
                SELECT id, numero_parcela, valor_parcela
                FROM duplicatas
                WHERE venda_id = ?
                AND numero_parcela > ?
                AND status = 'aberto'
                ORDER BY numero_parcela
            '''
            parcelas_restantes = DatabaseUtils.executar_query(
                query_parcelas, (venda_id, numero_parcela_atual)
            )

            if not parcelas_restantes:
                return True

            total_restante = sum(float(parcela[2]) for parcela in parcelas_restantes)

            if abs(diferenca) < 0.01:
                return True

            for parcela in parcelas_restantes:
                valor_atual = float(parcela[2])
                proporcao = valor_atual / total_restante if total_restante > 0 else 1.0 / len(parcelas_restantes)
                ajuste = diferenca * proporcao
                novo_valor = max(0.01, valor_atual - ajuste)

                query_update = '''
                    UPDATE duplicatas
                    SET valor_parcela = ?
                    WHERE id = ? AND status = 'aberto'
                '''
                DatabaseUtils.executar_query(query_update, (novo_valor, parcela[0]))

            return True

        except Exception as e:
            raise e
