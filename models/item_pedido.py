# \erp\models\item_pedido.py
from database import Database

class ItemPedido:
    TABLE_NAME = 'itens_pedido'

    @classmethod
    def salvar_itens(cls, pedido_id, itens):
        conn = Database().get_connection()
        cursor = conn.cursor()

        try:
            # Remover itens existentes
            cursor.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))

            # Inserir novos itens
            for item in itens:
                query = '''
                    INSERT INTO itens_pedido
                    (pedido_id, produto_id, quantidade, preco_custo, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                '''
                params = (pedido_id, item['id'], item['quantidade'],
                         item['preco_custo'], item['subtotal'])
                cursor.execute(query, params)

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e

    @classmethod
    def buscar_por_pedido(cls, pedido_id):
        query = "SELECT * FROM itens_pedido WHERE pedido_id = ?"
        conn = Database().get_connection()
        cursor = conn.cursor()
        cursor.execute(query, (pedido_id,))
        return cursor.fetchall()
