# \erp\model\cliente.py
import sqlite3
from datetime import datetime

from database import Database


class Cliente:
    def __init__(
        self,
        id=None,
        nome="",
        cpf_cnpj="",
        endereco="",
        telefone="",
        email="",
        observacao="",
        data_cadastro=None,
        ativo=True,
    ):
        self.id = id
        self.nome = nome
        self.cpf_cnpj = cpf_cnpj
        self.endereco = endereco
        self.telefone = telefone
        self.email = email
        self.observacao = observacao
        self.data_cadastro = data_cadastro or datetime.now().date()
        self.ativo = ativo

    def salvar(self):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cpf_cnpj = self.cpf_cnpj if self.cpf_cnpj and self.cpf_cnpj.strip() else None

        try:
            if self.id:
                cursor.execute(
                    """
                    UPDATE clientes SET nome=?, cpf_cnpj=?, endereco=?, telefone=?, email=?, observacao=?, ativo=?
                    WHERE id=?
                """,
                    (
                        self.nome,
                        cpf_cnpj,
                        self.endereco,
                        self.telefone,
                        self.email,
                        self.observacao,
                        self.ativo,
                        self.id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO clientes (nome, cpf_cnpj, endereco, telefone, email, observacao, data_cadastro, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.nome,
                        cpf_cnpj,
                        self.endereco,
                        self.telefone,
                        self.email,
                        self.observacao,
                        self.data_cadastro,
                        self.ativo,
                    ),
                )
                self.id = cursor.lastrowid

            conn.commit()

        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError("Já existe um cliente cadastrado com este CPF/CNPJ")

        finally:
            conn.close()

    def inativar(self):
        """Marca o cliente como inativo"""
        self.ativo = False
        self.salvar()

    def reativar(self):
        """Reativa o cliente"""
        self.ativo = True
        self.salvar()

    @staticmethod
    def buscar_todos(apenas_ativos=True):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        if apenas_ativos:
            cursor.execute("SELECT * FROM clientes WHERE ativo = 1 ORDER BY nome")
        else:
            cursor.execute("SELECT * FROM clientes ORDER BY nome")

        clientes = []
        for row in cursor.fetchall():
            cpf_cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[8]) if len(row) > 8 else True
            cliente = Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], ativo
            )
            clientes.append(cliente)

        conn.close()
        return clientes

    @staticmethod
    def buscar_por_id(cliente_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            cpf_cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[8]) if len(row) > 8 else True
            return Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], ativo
            )
        return None

    @staticmethod
    def buscar_inativos():
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clientes WHERE ativo = 0 ORDER BY nome")
        clientes = []
        for row in cursor.fetchall():
            cpf_cnpj = row[2] if row[2] is not None else ""
            cliente = Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], False
            )
            clientes.append(cliente)

        conn.close()
        return clientes
