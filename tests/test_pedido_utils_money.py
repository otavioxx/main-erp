import pytest

from mainerp.data import database_utils
from mainerp.data.database import Database
from mainerp.domain.utils.pedido_utils import PedidoUtils


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "pedido-utils.db"))
    monkeypatch.setattr(database_utils, "obter_database", lambda: database)
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO fornecedores (id, nome) VALUES (1, 'Fornecedor')")
        cursor.execute(
            "INSERT INTO pedidos (id, fornecedor_id, data_pedido) "
            "VALUES (1, 1, '2026-03-01')"
        )
        cursor.execute(
            "INSERT INTO produtos (id, nome, preco_custo, preco_venda) "
            "VALUES (1, 'Produto', 1, 2)"
        )
    yield database
    database.close_connection()


def test_salvar_itens_e_calcular_totais_usa_centavos(database):
    itens = [
        {
            "id": 1,
            "quantidade": 2,
            "preco_custo": 3.335,
            "preco_venda": 5.005,
            "subtotal": 6.67,
        },
        {
            "id": 1,
            "quantidade": 1,
            "preco_custo": 1.01,
            "preco_venda": 2.03,
            "subtotal": 1.01,
        },
    ]

    assert PedidoUtils.calcular_totais_pedido(itens, frete=0.1) == (7.68, 7.78)
    assert PedidoUtils.salvar_itens_pedido(1, itens)

    linhas = (
        database.get_connection()
        .execute(
            """
        SELECT preco_custo_centavos, preco_venda_centavos, subtotal_centavos
        FROM itens_pedido ORDER BY id
        """
        )
        .fetchall()
    )
    assert linhas == [(334, 501, 667), (101, 203, 101)]


def test_recebimento_atualiza_produtos_com_precos_em_centavos(database):
    with database.transacao() as cursor:
        cursor.execute(
            """
            INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_custo, preco_venda, subtotal)
            VALUES (1, 1, 2, 10.02, 15.03, 20.04)
            """
        )

    resumo = PedidoUtils.obter_resumo_recebimento(1)
    assert resumo["total_investimento"] == 20.04
    assert resumo["produtos"][0]["novo_custo"] == 10.02
    assert PedidoUtils.receber_pedido(1)

    cursor = database.get_connection().cursor()
    cursor.execute(
        "SELECT preco_custo_centavos, preco_venda_centavos, estoque "
        "FROM produtos WHERE id = 1"
    )
    assert cursor.fetchone() == (1002, 1503, 2)
