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


def test_salvar_e_carregar_pedido_usa_valores_em_centavos(database):
    pedido = pedido_model.Pedido(
        fornecedor_id=1,
        valor_total=10.015,
        valor_frete=1.025,
        desconto=0.335,
    )

    pedido.salvar()
    carregado = pedido_model.Pedido.buscar_por_id(pedido.id)

    assert carregado.valor_total == 10.02
    assert carregado.valor_frete == 1.03
    assert carregado.desconto == 0.34
    with database.transacao() as cursor:
        cursor.execute(
            """
            SELECT valor_total_centavos, valor_frete_centavos, desconto_centavos
            FROM pedidos WHERE id = ?
            """,
            (pedido.id,),
        )
        assert cursor.fetchone() == (1002, 103, 34)


def test_obter_itens_e_calcular_totais_usa_centavos(database):
    with database.transacao() as cursor:
        cursor.execute(
            "INSERT INTO produtos (id, nome, preco_custo, preco_venda) VALUES (10, 'Produto', 1, 2)"
        )
        cursor.execute(
            """
            INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_custo, preco_venda, subtotal)
            VALUES (1, 10, 3, 0.10, 0.20, 0.30)
            """
        )

    pedido = pedido_model.Pedido(id=1, valor_frete=0.1, desconto=0.05)

    assert pedido.obter_itens()[0][5] == 0.3
    assert pedido.calcular_subtotal_produtos() == 0.3
    assert pedido.calcular_total_com_desconto_frete() == 0.35
