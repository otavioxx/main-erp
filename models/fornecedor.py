# \erp\model\fornecedor.py
import sqlite3

from models.base_model import BaseModel


class Fornecedor(BaseModel):
    TABLE_NAME = "fornecedores"

    def __init__(
        self,
        id=None,
        nome="",
        cnpj="",
        endereco="",
        telefone="",
        email="",
        observacao="",
        ativo=True,
    ):
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.endereco = endereco
        self.telefone = telefone
        self.email = email
        self.observacao = observacao
        self.ativo = ativo

    def salvar(self):
        cnpj = self.cnpj if self.cnpj and self.cnpj.strip() else None

        try:
            if self.id:
                query = """
                    UPDATE fornecedores SET nome=?, cnpj=?, endereco=?, telefone=?, email=?, observacao=?, ativo=?
                    WHERE id=?
                """
                params = (
                    self.nome,
                    cnpj,
                    self.endereco,
                    self.telefone,
                    self.email,
                    self.observacao,
                    self.ativo,
                    self.id,
                )
            else:
                query = """
                    INSERT INTO fornecedores (nome, cnpj, endereco, telefone, email, observacao, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    self.nome,
                    cnpj,
                    self.endereco,
                    self.telefone,
                    self.email,
                    self.observacao,
                    self.ativo,
                )

            result = self.executar_query(query, params)
            if not self.id:
                self.id = result

        except sqlite3.IntegrityError as e:
            raise ValueError("Já existe um fornecedor cadastrado com este CNPJ") from e

    def inativar(self):
        self.ativo = False
        self.salvar()

    def reativar(self):
        self.ativo = True
        self.salvar()

    @classmethod
    def buscar_todos(cls, apenas_ativos=True):
        if apenas_ativos:
            query = "SELECT * FROM fornecedores WHERE ativo = 1 ORDER BY nome"
        else:
            query = "SELECT * FROM fornecedores ORDER BY nome"

        resultados = cls.executar_query(query)
        fornecedores = []
        for row in resultados:
            cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[7]) if len(row) > 7 else True
            fornecedor = Fornecedor(
                row[0], row[1], cnpj, row[3], row[4], row[5], row[6], ativo
            )
            fornecedores.append(fornecedor)

        return fornecedores

    @classmethod
    def buscar_por_id(cls, fornecedor_id):
        query = "SELECT * FROM fornecedores WHERE id = ?"
        resultado = cls.executar_query(query, (fornecedor_id,))

        if resultado:
            row = resultado[0]
            cnpj = row[2] if row[2] is not None else ""
            ativo = bool(row[7]) if len(row) > 7 else True
            return Fornecedor(
                row[0], row[1], cnpj, row[3], row[4], row[5], row[6], ativo
            )
        return None

    @classmethod
    def buscar_inativos(cls):
        query = "SELECT * FROM fornecedores WHERE ativo = 0 ORDER BY nome"
        resultados = cls.executar_query(query)
        fornecedores = []
        for row in resultados:
            cnpj = row[2] if row[2] is not None else ""
            fornecedor = Fornecedor(
                row[0], row[1], cnpj, row[3], row[4], row[5], row[6], False
            )
            fornecedores.append(fornecedor)

        return fornecedores

    @classmethod
    def buscar_por_cnpj(cls, cnpj):
        query = "SELECT * FROM fornecedores WHERE cnpj = ?"
        resultado = cls.executar_query(query, (cnpj,))

        if resultado:
            row = resultado[0]
            cnpj_val = row[2] if row[2] is not None else ""
            ativo = bool(row[7]) if len(row) > 7 else True
            return Fornecedor(
                row[0], row[1], cnpj_val, row[3], row[4], row[5], row[6], ativo
            )
        return None
