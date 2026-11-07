# \erp\model\cliente.py
import sqlite3
from datetime import datetime

from mainerp.data.database import obter_database


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
        db = obter_database()
        cpf_cnpj = self.cpf_cnpj if self.cpf_cnpj and self.cpf_cnpj.strip() else None

        try:
            with db.transacao() as cursor:
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
        except sqlite3.IntegrityError as e:
            raise ValueError("Já existe um cliente cadastrado com este CPF/CNPJ") from e

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
        db = obter_database()
        query = (
            "SELECT * FROM clientes WHERE ativo = 1 ORDER BY nome"
            if apenas_ativos
            else "SELECT * FROM clientes ORDER BY nome"
        )
        with db.transacao() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        clientes = []
        for row in rows:
            cpf_cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[8]) if len(row) > 8 else True
            cliente = Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], ativo
            )
            clientes.append(cliente)
        return clientes

    @staticmethod
    def buscar_por_id(cliente_id):
        db = obter_database()
        with db.transacao() as cursor:
            cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
            row = cursor.fetchone()

        if row:
            cpf_cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[8]) if len(row) > 8 else True
            return Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], ativo
            )
        return None

    @staticmethod
    def buscar_inativos():
        db = obter_database()
        with db.transacao() as cursor:
            cursor.execute("SELECT * FROM clientes WHERE ativo = 0 ORDER BY nome")
            rows = cursor.fetchall()
        clientes = []
        for row in rows:
            cpf_cnpj = row[2] if row[2] is not None else ""
            cliente = Cliente(
                row[0], row[1], cpf_cnpj, row[3], row[4], row[5], row[6], row[7], False
            )
            clientes.append(cliente)

        return clientes
