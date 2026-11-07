import sqlite3
from datetime import date, timedelta

import pytest

from mainerp.data.database import Database
from mainerp.data.models import duplicata as duplicata_model


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "duplicatas.db"))
    monkeypatch.setattr(duplicata_model, "obter_database", lambda: database)
    yield database
    database.close_connection()


def test_criar_parcelas_divide_valor_e_incrementa_vencimentos(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, ?)", ("Cliente",))
        cursor.execute("INSERT INTO vendas (id, cliente_id) VALUES (42, 7)")
    primeiro_vencimento = date(2026, 1, 15)

    parcelas = duplicata_model.Duplicata.criar_parcelas(
        venda_id=42,
        cliente_id=7,
        valor_financiado=100,
        parcelas=3,
        data_primeiro_vencimento=primeiro_vencimento,
    )

    assert [parcela.id for parcela in parcelas] == [1, 2, 3]
    assert [parcela.numero_parcela for parcela in parcelas] == [1, 2, 3]
    assert [parcela.valor_parcela for parcela in parcelas] == [33.33, 33.33, 33.34]
    assert [parcela.data_vencimento for parcela in parcelas] == [
        primeiro_vencimento + timedelta(days=30 * indice) for indice in range(3)
    ]
    assert all(parcela.status == "aberto" for parcela in parcelas)
    assert database.get_connection().execute(
        """
            SELECT venda_id, cliente_id, numero_parcela, valor_parcela,
                   valor_parcela_centavos
            FROM duplicatas ORDER BY numero_parcela
            """
    ).fetchall() == [
        (42, 7, 1, 33.33, 3333),
        (42, 7, 2, 33.33, 3333),
        (42, 7, 3, 33.34, 3334),
    ]


def test_criar_parcelas_reverte_todos_os_inserts_se_algum_falhar(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (nome) VALUES (?)", ("Cliente",))
        cursor.execute("INSERT INTO vendas (cliente_id) VALUES (1)")
        cursor.execute("""
            CREATE TRIGGER falhar_segunda_parcela
            BEFORE INSERT ON duplicatas
            WHEN NEW.numero_parcela = 2
            BEGIN
                SELECT RAISE(ABORT, 'falha simulada');
            END
        """)

    with pytest.raises(sqlite3.IntegrityError, match="falha simulada"):
        duplicata_model.Duplicata.criar_parcelas(
            venda_id=1,
            cliente_id=1,
            valor_financiado=100,
            parcelas=3,
            data_primeiro_vencimento=date(2026, 1, 15),
        )

    assert (
        database.get_connection()
        .execute("SELECT COUNT(*) FROM duplicatas")
        .fetchone()[0]
        == 0
    )


def test_pagamento_parcial_da_ultima_parcela_cria_nova_parcela_com_saldo(database):
    vencimento = date(2026, 1, 15)
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, 'Cliente')")
        cursor.execute("INSERT INTO vendas (id, cliente_id) VALUES (42, 7)")
        cursor.execute(
            """
            INSERT INTO duplicatas
            (id, venda_id, cliente_id, numero_parcela, valor_parcela,
             valor_parcela_centavos, data_vencimento, status)
            VALUES (5, 42, 7, 3, 100, 10000, ?, 'aberto')
            """,
            (vencimento,),
        )

    assert duplicata_model.Duplicata.marcar_como_paga(
        5, 80, date(2026, 1, 15), "Dinheiro"
    )

    parcelas = (
        database.get_connection()
        .execute(
            """
        SELECT numero_parcela, valor_parcela, valor_parcela_centavos,
               data_vencimento, status
        FROM duplicatas WHERE venda_id = 42
        """
        )
        .fetchall()
    )
    assert parcelas == [(4, 20.0, 2000, "2026-02-14", "aberto")]

    parcela_paga = (
        database.get_connection()
        .execute(
            """
        SELECT numero_parcela, valor_original_centavos, valor_recebido_centavos
        FROM duplicatas_pagas WHERE venda_id = 42
        """
        )
        .fetchone()
    )
    assert parcela_paga == (3, 10000, 8000)


def test_ajuste_de_ultima_parcela_cria_parcela_para_o_saldo(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, 'Cliente')")
        cursor.execute("INSERT INTO vendas (id, cliente_id) VALUES (42, 7)")
        cursor.execute(
            """
            INSERT INTO duplicatas
            (id, venda_id, cliente_id, numero_parcela, valor_parcela,
             valor_parcela_centavos, data_vencimento, status)
            VALUES (5, 42, 7, 2, 50, 5000, '2026-03-01', 'aberto')
            """
        )

    duplicata_model.Duplicata.ajustar_parcelas_restantes(42, 5, 30)

    parcela = (
        database.get_connection()
        .execute(
            """
        SELECT numero_parcela, valor_parcela_centavos, data_vencimento
        FROM duplicatas WHERE id != 5
        """
        )
        .fetchone()
    )
    assert parcela == (3, 2000, "2026-03-31")
