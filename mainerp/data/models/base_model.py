# \erp\models\base_model.py
from mainerp.data.database import obter_database


class BaseModel:
    """Classe base para todos os modelos"""

    TABLE_NAME = None
    id: int | None

    @classmethod
    def get_connection(cls):
        return obter_database().get_connection()

    @classmethod
    def executar_query(cls, query, params=None):
        """Executa query e retorna resultados"""
        database = obter_database()
        with database.transacao() as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return cursor.lastrowid

    @classmethod
    def buscar_por_id(cls, id):
        """Busca registro por ID"""
        if not cls.TABLE_NAME:
            raise ValueError("TABLE_NAME deve ser definido")

        query = f"SELECT * FROM {cls.TABLE_NAME} WHERE id = ?"
        result = cls.executar_query(query, (id,))
        if not isinstance(result, list):
            raise TypeError("A consulta por ID não retornou uma lista de registros.")
        return cls(*result[0]) if result else None

    def salvar(self):
        """Salva o objeto no banco (deve ser implementado nas classes filhas)"""
        raise NotImplementedError("Método salvar deve ser implementado")

    def excluir(self):
        """Exclui o registro do banco"""
        if not self.id:
            raise ValueError("Não é possível excluir objeto sem ID")
        if not self.TABLE_NAME:
            raise ValueError("TABLE_NAME deve ser definido")

        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = ?"
        self.executar_query(query, (self.id,))
