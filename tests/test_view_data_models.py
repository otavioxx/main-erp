import pytest

from mainerp.data.database import Database
from mainerp.data.models import condicional as condicional_model
from mainerp.data.models import duplicata as duplicata_model


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "view_data.db"))
    monkeypatch.setattr(condicional_model, "obter_database", lambda: database)
    monkeypatch.setattr(duplicata_model, "obter_database", lambda: database)

    with database.transacao() as cursor:
        cursor.execute(
            "INSERT INTO clientes (id, nome, cpf_cnpj, endereco) VALUES (1, 'Cliente', '123', 'Rua A')"
        )
        cursor.execute(
            "INSERT INTO vendas (id, cliente_id, total, data_venda) "
            "VALUES (1, 1, 150, '2026-03-01')"
        )
        cursor.execute(
            """
            INSERT INTO duplicatas
                (id, venda_id, cliente_id, numero_parcela, valor_parcela,
                 data_vencimento, status)
            VALUES (1, 1, 1, 1, 50, '2026-04-01', 'aberto')
            """
        )
        cursor.execute(
            """
            INSERT INTO duplicatas_pagas
                (id, venda_id, cliente_id, numero_parcela, valor_original,
                 valor_recebido, data_vencimento, data_pagamento, forma_pagamento)
            VALUES (1, 1, 1, 2, 50, 50, '2026-05-01', '2026-05-01', 'Dinheiro')
            """
        )
        cursor.execute(
            """
            INSERT INTO produtos (id, nome, preco_custo, preco_venda)
            VALUES (1, 'Produto', 10, 20)
            """
        )
        cursor.execute(
            """
            INSERT INTO condicionais
                (id, cliente_id, data_condicional, status, observacao, desconto)
            VALUES (1, 1, '2026-03-01', 'ativa', '', 0)
            """
        )
        cursor.execute(
            """
            INSERT INTO itens_condicional
                (condicional_id, produto_id, quantidade, preco_unitario)
            VALUES (1, 1, 1, 20)
            """
        )

    yield database
    database.close_connection()


def test_duplicata_fornece_dados_para_listagem_e_recebimento(database):
    duplicatas = duplicata_model.Duplicata.buscar_para_recebimento()

    assert len(duplicatas) == 2
    assert duplicatas[0][7:9] == ("aberto", "Cliente")
    assert duplicatas[1][7:9] == ("pago", "Cliente")
    assert duplicata_model.Duplicata.contar_parcelas_por_venda(1) == 2
    assert duplicata_model.Duplicata.buscar_dados_cliente_venda(1, 1) == (
        "Cliente",
        "123",
        "Rua A",
        150.0,
        "2026-03-01",
    )


def test_condicional_model_fornece_nome_e_exclui_cabecalho_com_itens(database):
    assert condicional_model.Condicional.buscar_nome_cliente(1) == "Cliente"

    condicional_model.Condicional.excluir_por_id(1)

    assert (
        database.get_connection()
        .execute("SELECT COUNT(*) FROM condicionais WHERE id = 1")
        .fetchone()[0]
        == 0
    )
    assert (
        database.get_connection()
        .execute("SELECT COUNT(*) FROM itens_condicional WHERE condicional_id = 1")
        .fetchone()[0]
        == 0
    )
