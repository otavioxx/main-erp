import pytest

from mainerp.data.database import Database
from mainerp.data.models import pedido as pedido_model


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "pedidos.db"))
    monkeypatch.setattr(pedido_model, "obter_database", lambda: database)

    with database.transacao() as cursor:
        cursor.executemany(
            "INSERT INTO fornecedores (id, nome) VALUES (?, ?)",
            [(1, "Fornecedor A"), (2, "Fornecedor B")],
        )
        cursor.executemany(
            """
            INSERT INTO pedidos
                (id, fornecedor_id, data_pedido, valor_total, status, desconto)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (1, 1, "2026-03-05", 100, "pendente", None),
                (2, 1, "2026-03-20", 200, "pendente", 5),
                (3, 1, "2026-04-02", 300, "pendente", 0),
                (4, 2, "2026-03-15", 400, "pendente", 0),
                (5, 1, "2026-03-18", 500, "recebido", 0),
            ],
        )

    yield database
    database.close_connection()


def test_buscar_para_listagem_aplica_filtros_e_preserva_formato_dos_dados(database):
    pedidos = pedido_model.Pedido.buscar_para_listagem(
        data_inicio="2026-03-01",
        data_fim="2026-03-31",
        fornecedor_id=1,
        status="pendente",
    )

    assert [pedido[0] for pedido in pedidos] == [2, 1]
    assert pedidos[0][8] == 5
    assert pedidos[0][9] == "Fornecedor A"
    assert pedidos[1][8] == 0
    assert pedidos[1][9] == "Fornecedor A"


def test_buscar_para_listagem_omite_filtros_opcionais(database):
    pedidos = pedido_model.Pedido.buscar_para_listagem()

    assert [pedido[0] for pedido in pedidos] == [3, 2, 5, 4, 1]
