#\erp\utils\produto_validation.py
"""
Utilitários para validação de produtos
"""
from database import Database

class ProdutoValidationUtils:
    """Classe com métodos estáticos para validação de produtos"""

    @staticmethod
    def verificar_produto_em_uso(produto_id):
        """
        Verifica se um produto está sendo usado em pedidos ou condicionais ativos
        Retorna um dicionário com informações detalhadas sobre o uso
        """
        resultado = {
            'em_uso': False,
            'estoque': 0,
            'pedidos_ativos': 0,
            'condicionais_ativas': 0,
            'detalhes_pedidos': [],
            'detalhes_condicionais': [],
            'motivos_bloqueio': []
        }

        try:
            # Busca informações do produto
            produto_info = ProdutoValidationUtils._buscar_info_produto(produto_id)
            if not produto_info:
                return resultado

            resultado['estoque'] = produto_info['estoque']

            # Verifica estoque
            if produto_info['estoque'] > 0:
                resultado['em_uso'] = True
                resultado['motivos_bloqueio'].append(f"Produto possui estoque: {produto_info['estoque']} unidades")

            # Verifica pedidos ativos
            pedidos_info = ProdutoValidationUtils._buscar_pedidos_ativos(produto_id)
            resultado['pedidos_ativos'] = len(pedidos_info)
            resultado['detalhes_pedidos'] = pedidos_info

            if pedidos_info:
                resultado['em_uso'] = True
                resultado['motivos_bloqueio'].append(f"Produto está em {len(pedidos_info)} pedido(s) ativo(s)")

            # Verifica condicionais ativas
            condicionais_info = ProdutoValidationUtils._buscar_condicionais_ativas(produto_id)
            resultado['condicionais_ativas'] = len(condicionais_info)
            resultado['detalhes_condicionais'] = condicionais_info

            if condicionais_info:
                resultado['em_uso'] = True
                resultado['motivos_bloqueio'].append(f"Produto está em {len(condicionais_info)} condicional(ais) ativa(s)")

        except Exception as e:
            print(f"Erro ao verificar produto em uso: {e}")

        return resultado

    @staticmethod
    def _buscar_info_produto(produto_id):
        """Busca informações básicas do produto"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, nome, estoque, ativo FROM produtos WHERE id = ?", (produto_id,))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'nome': row[1],
                    'estoque': row[2],
                    'ativo': row[3]
                }
            return None
        except Exception:
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def _buscar_pedidos_ativos(produto_id):
        """Busca pedidos ativos que contêm o produto"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            query = '''
                SELECT DISTINCT p.id, p.data_pedido, p.status, c.nome as cliente_nome,
                       ip.quantidade, ip.preco_custo
                FROM pedidos p
                INNER JOIN itens_pedido ip ON p.id = ip.pedido_id
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE ip.produto_id = ? AND p.status IN ('aberto', 'pendente', 'processando')
                ORDER BY p.data_pedido DESC
            '''

            cursor.execute(query, (produto_id,))
            rows = cursor.fetchall()

            pedidos = []
            for row in rows:
                pedidos.append({
                    'pedido_id': row[0],
                    'data_pedido': row[1],
                    'status': row[2],
                    'cliente_nome': row[3] or 'Cliente não informado',
                    'quantidade': row[4],
                    'preco_custo': row[5]
                })

            return pedidos
        except Exception:
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def _buscar_condicionais_ativas(produto_id):
        """Busca condicionais ativas que contêm o produto"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            query = '''
                SELECT DISTINCT c.id, c.data_condicional, c.data_prevista_devolucao,
                       cl.nome as cliente_nome, ic.quantidade, ic.preco_unitario
                FROM condicionais c
                INNER JOIN itens_condicional ic ON c.id = ic.condicional_id
                LEFT JOIN clientes cl ON c.cliente_id = cl.id
                WHERE ic.produto_id = ? AND c.status = 'ativa'
                ORDER BY c.data_condicional DESC
            '''

            cursor.execute(query, (produto_id,))
            rows = cursor.fetchall()

            condicionais = []
            for row in rows:
                condicionais.append({
                    'condicional_id': row[0],
                    'data_condicional': row[1],
                    'data_prevista_devolucao': row[2],
                    'cliente_nome': row[3] or 'Cliente não informado',
                    'quantidade': row[4],
                    'preco_unitario': row[5]
                })

            return condicionais
        except Exception:
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    @staticmethod
    def gerar_relatorio_bloqueios(produto_id):
        """Gera um relatório detalhado dos motivos de bloqueio"""
        info = ProdutoValidationUtils.verificar_produto_em_uso(produto_id)

        if not info['em_uso']:
            return "Produto pode ser inativado sem restrições."

        relatorio = ["PRODUTO NÃO PODE SER INATIVADO", "=" * 40, ""]

        # Motivos gerais
        relatorio.extend(["MOTIVOS:", ""])
        for motivo in info['motivos_bloqueio']:
            relatorio.append(f"• {motivo}")
        relatorio.append("")

        # Detalhes dos pedidos
        if info['detalhes_pedidos']:
            relatorio.extend(["PEDIDOS ATIVOS:", ""])
            for pedido in info['detalhes_pedidos']:
                relatorio.append(f"• Pedido #{pedido['pedido_id']} - {pedido['cliente_nome']}")
                relatorio.append(f"  Data: {pedido['data_pedido']} | Status: {pedido['status']}")
                relatorio.append(f"  Quantidade: {pedido['quantidade']} | Preço: R$ {pedido['preco_custo']:.2f}")
                relatorio.append("")

        # Detalhes das condicionais
        if info['detalhes_condicionais']:
            relatorio.extend(["CONDICIONAIS ATIVAS:", ""])
            for condicional in info['detalhes_condicionais']:
                relatorio.append(f"• Condicional #{condicional['condicional_id']} - {condicional['cliente_nome']}")
                relatorio.append(f"  Data: {condicional['data_condicional']} | Previsão: {condicional['data_prevista_devolucao']}")
                relatorio.append(f"  Quantidade: {condicional['quantidade']} | Preço: R$ {condicional['preco_unitario']:.2f}")
                relatorio.append("")

        relatorio.extend([
            "AÇÕES NECESSÁRIAS:",
            "• Zerar o estoque (se houver)",
            "• Finalizar ou cancelar pedidos ativos",
            "• Finalizar ou cancelar condicionais ativas"
        ])

        return "\n".join(relatorio)

    @staticmethod
    def produtos_que_nao_podem_ser_inativados():
        """Retorna lista de todos os produtos que não podem ser inativados"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Produtos com estoque
            cursor.execute("SELECT id, nome, estoque FROM produtos WHERE estoque > 0 AND ativo = 1")
            produtos_com_estoque = cursor.fetchall()

            # Produtos em pedidos ativos
            cursor.execute('''
                SELECT DISTINCT p.id, p.nome, COUNT(ped.id) as total_pedidos
                FROM produtos p
                INNER JOIN itens_pedido ip ON p.id = ip.produto_id
                INNER JOIN pedidos ped ON ip.pedido_id = ped.id
                WHERE ped.status IN ('aberto', 'pendente', 'processando') AND p.ativo = 1
                GROUP BY p.id, p.nome
            ''')
            produtos_em_pedidos = cursor.fetchall()

            # Produtos em condicionais ativas
            cursor.execute('''
                SELECT DISTINCT p.id, p.nome, COUNT(c.id) as total_condicionais
                FROM produtos p
                INNER JOIN itens_condicional ic ON p.id = ic.produto_id
                INNER JOIN condicionais c ON ic.condicional_id = c.id
                WHERE c.status = 'ativa' AND p.ativo = 1
                GROUP BY p.id, p.nome
            ''')
            produtos_em_condicionais = cursor.fetchall()

            # Consolida resultados
            produtos_bloqueados = {}

            for produto in produtos_com_estoque:
                produtos_bloqueados[produto[0]] = {
                    'id': produto[0],
                    'nome': produto[1],
                    'estoque': produto[2],
                    'pedidos_ativos': 0,
                    'condicionais_ativas': 0
                }

            for produto in produtos_em_pedidos:
                if produto[0] not in produtos_bloqueados:
                    produtos_bloqueados[produto[0]] = {
                        'id': produto[0],
                        'nome': produto[1],
                        'estoque': 0,
                        'pedidos_ativos': produto[2],
                        'condicionais_ativas': 0
                    }
                else:
                    produtos_bloqueados[produto[0]]['pedidos_ativos'] = produto[2]

            for produto in produtos_em_condicionais:
                if produto[0] not in produtos_bloqueados:
                    produtos_bloqueados[produto[0]] = {
                        'id': produto[0],
                        'nome': produto[1],
                        'estoque': 0,
                        'pedidos_ativos': 0,
                        'condicionais_ativas': produto[2]
                    }
                else:
                    produtos_bloqueados[produto[0]]['condicionais_ativas'] = produto[2]

            return list(produtos_bloqueados.values())

        except Exception as e:
            print(f"Erro ao buscar produtos bloqueados: {e}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()
