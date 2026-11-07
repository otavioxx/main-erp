import sqlite3

import pytest

from mainerp.data.database import Database
from mainerp.data.models import base_model
from mainerp.data.models import cliente as cliente_model
from mainerp.data.models import condicional as condicional_model
from mainerp.data.models import empresa as empresa_model
from mainerp.data.models import pedido as pedido_model


def test_transacao_confirma_alteracoes(tmp_path):
    database = Database(str(tmp_path / "transactions.db"))
    try:
        with database.transacao() as cursor:
            cursor.execute(
                "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
            )
            cursor.execute("INSERT INTO registros (valor) VALUES (?)", ("salvo",))

        assert database.get_connection().execute(
            "SELECT valor FROM registros"
        ).fetchone() == ("salvo",)
    finally:
        database.close_connection()


def test_transacao_reverte_todas_as_alteracoes_ao_ocorrer_erro(tmp_path):
    database = Database(str(tmp_path / "transactions.db"))
    try:
        database.get_connection().execute(
            "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
        )

        with (
            pytest.raises(RuntimeError, match="falha simulada"),
            database.transacao() as cursor,
        ):
            cursor.execute("INSERT INTO registros (valor) VALUES (?)", ("perdido",))
            raise RuntimeError("falha simulada")

        assert (
            database.get_connection()
            .execute("SELECT COUNT(*) FROM registros")
            .fetchone()[0]
            == 0
        )
    finally:
        database.close_connection()


def test_transacoes_aninhadas_revertem_savepoint_sem_afetar_transacao_externa(
    tmp_path,
):
    database = Database(str(tmp_path / "transactions.db"))
    try:
        database.get_connection().execute(
            "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
        )

        with database.transacao() as cursor:
            cursor.execute("INSERT INTO registros (valor) VALUES (?)", ("mantido",))
            with (
                pytest.raises(RuntimeError, match="falha interna"),
                database.transacao() as nested_cursor,
            ):
                nested_cursor.execute(
                    "INSERT INTO registros (valor) VALUES (?)", ("revertido",)
                )
                raise RuntimeError("falha interna")
            cursor.execute(
                "INSERT INTO registros (valor) VALUES (?)", ("tambem mantido",)
            )

        assert database.get_connection().execute(
            "SELECT valor FROM registros ORDER BY id"
        ).fetchall() == [("mantido",), ("tambem mantido",)]
    finally:
        database.close_connection()


def test_base_model_usa_o_gerenciador_de_transacoes(monkeypatch, tmp_path):
    database = Database(str(tmp_path / "base_model.db"))
    monkeypatch.setattr(base_model, "obter_database", lambda: database)

    class Registro(base_model.BaseModel):
        TABLE_NAME = "registros"

        def __init__(self, id, valor):
            self.id = id
            self.valor = valor

    try:
        database.get_connection().execute(
            "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
        )

        row_id = Registro.executar_query(
            "INSERT INTO registros (valor) VALUES (?)", ("teste",)
        )
        registro = Registro.buscar_por_id(row_id)

        assert registro is not None
        assert registro.valor == "teste"
    finally:
        database.close_connection()


def test_cliente_e_empresa_usam_o_gerenciador_compartilhado(monkeypatch, tmp_path):
    database = Database(str(tmp_path / "models.db"))
    monkeypatch.setattr(cliente_model, "obter_database", lambda: database)
    monkeypatch.setattr(empresa_model, "obter_database", lambda: database)
    try:
        cliente = cliente_model.Cliente(nome="Cliente de teste")
        cliente.salvar()
        cliente_encontrado = cliente_model.Cliente.buscar_por_id(cliente.id)
        assert cliente_encontrado is not None
        assert cliente_encontrado.nome == "Cliente de teste"
        assert len(cliente_model.Cliente.buscar_todos()) == 1

        empresa = empresa_model.Empresa(nome="Empresa de teste")
        empresa.salvar()
        assert empresa_model.Empresa.buscar().nome == "Empresa de teste"
    finally:
        database.close_connection()


def test_pedido_e_condicional_usam_transacoes_compartilhadas(monkeypatch, tmp_path):
    database = Database(str(tmp_path / "pedido_condicional.db"))
    monkeypatch.setattr(pedido_model, "obter_database", lambda: database)
    monkeypatch.setattr(condicional_model, "obter_database", lambda: database)
    try:
        with database.transacao() as cursor:
            cursor.execute(
                "INSERT INTO fornecedores (nome) VALUES (?)", ("Fornecedor",)
            )
            cursor.execute("INSERT INTO clientes (nome) VALUES (?)", ("Cliente",))
            cursor.execute(
                "INSERT INTO produtos (nome, preco_custo, preco_venda) "
                "VALUES (?, ?, ?)",
                ("Produto", 10, 20),
            )

        pedido = pedido_model.Pedido(fornecedor_id=1, valor_total=10)
        assert pedido.salvar() == pedido.id
        pedido_encontrado = pedido_model.Pedido.buscar_por_id(pedido.id)
        assert pedido_encontrado is not None
        assert pedido_encontrado.fornecedor_id == 1

        condicional = condicional_model.Condicional(cliente_id=1)
        condicional.itens = [{"produto_id": 1, "quantidade": 2, "preco_unitario": 20}]
        assert condicional.salvar() == condicional.id
        carregada = condicional_model.Condicional.buscar_por_id(condicional.id)
        assert carregada is not None
        assert carregada.cliente_id == 1
        assert carregada.itens[0]["produto_id"] == 1
        assert len(condicional_model.Condicional.buscar_todas()) == 1
    finally:
        database.close_connection()


def test_salvar_condicional_reverte_cabecalho_se_item_falhar(monkeypatch, tmp_path):
    database = Database(str(tmp_path / "condicional_rollback.db"))
    monkeypatch.setattr(condicional_model, "obter_database", lambda: database)
    try:
        with database.transacao() as cursor:
            cursor.execute("INSERT INTO clientes (nome) VALUES (?)", ("Cliente",))

        condicional = condicional_model.Condicional(cliente_id=1)
        condicional.itens = [{"produto_id": 999, "quantidade": 1, "preco_unitario": 20}]

        with pytest.raises(sqlite3.IntegrityError):
            condicional.salvar()

        assert (
            database.get_connection()
            .execute("SELECT COUNT(*) FROM condicionais")
            .fetchone()[0]
            == 0
        )
    finally:
        database.close_connection()


def test_obter_database_reutiliza_gerenciador_na_thread(monkeypatch):
    import mainerp.data.database as database_module

    instancias = []

    class FakeDatabase:
        def __init__(self):
            instancias.append(self)

    monkeypatch.setattr(database_module, "Database", FakeDatabase)
    monkeypatch.delattr(database_module._database_por_thread, "database", raising=False)

    assert database_module.obter_database() is database_module.obter_database()
    assert len(instancias) == 1
