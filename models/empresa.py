# \erp\model\empresa.py
from database import Database


class Empresa:
    def __init__(
        self, id=None, nome="", cnpj="", endereco="", telefone="", email="", logo=None
    ):
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.endereco = endereco
        self.telefone = telefone
        self.email = email
        self.logo = logo

    @classmethod
    def buscar(cls):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM empresa LIMIT 1")
        row = cursor.fetchone()

        conn.close()

        if row:
            return cls(*row)
        else:
            return cls()

    def salvar(self):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        if self.id:
            cursor.execute(
                """
                UPDATE empresa SET nome=?, cnpj=?, endereco=?, telefone=?, email=?, logo=?
                WHERE id=?
            """,
                (
                    self.nome,
                    self.cnpj,
                    self.endereco,
                    self.telefone,
                    self.email,
                    self.logo,
                    self.id,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO empresa (nome, cnpj, endereco, telefone, email, logo)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.nome,
                    self.cnpj,
                    self.endereco,
                    self.telefone,
                    self.email,
                    self.logo,
                ),
            )
            self.id = cursor.lastrowid

        conn.commit()
        conn.close()
