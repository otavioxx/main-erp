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


def test_consultas_de_duplicatas_preservam_tuplas_legadas_em_reais(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, 'Cliente')")
        cursor.execute("INSERT INTO vendas (id, cliente_id) VALUES (42, 7)")
        cursor.execute(
            """
            INSERT INTO duplicatas
                (id, venda_id, cliente_id, numero_parcela, valor_parcela,
                 data_vencimento, status)
            VALUES (1, 42, 7, 1, 12.34, '2026-04-01', 'aberto')
            """
        )
        cursor.execute(
            """
            INSERT INTO duplicatas_pagas
                (id, venda_id, cliente_id, numero_parcela, valor_original,
                 valor_recebido, data_vencimento, data_pagamento, forma_pagamento)
            VALUES (2, 42, 7, 2, 12.34, 12.35, '2026-04-01', '2026-04-02', 'Pix')
            """
        )

    abertas = duplicata_model.Duplicata.buscar_por_venda(42)
    abertas_cliente = duplicata_model.Duplicata.buscar_por_status("aberto")
    pagas_cliente = duplicata_model.Duplicata.buscar_por_status("pago")
    por_cliente = duplicata_model.Duplicata.buscar_por_cliente(7)

    assert len(abertas[0]) == 8
    assert abertas[0][4] == 12.34
    assert abertas_cliente[0][8] == "Cliente"
    assert abertas_cliente[0][4] == 12.34
    assert len(pagas_cliente[0]) == 11
    assert pagas_cliente[0][4:6] == (12.34, 12.35)
    assert len(por_cliente) == 2
    assert por_cliente[1][4:6] == (12.34, 12.35)


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


def test_buscar_para_recebimento_le_valores_em_centavos(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, 'Cliente')")
        cursor.execute("INSERT INTO vendas (id, cliente_id, total) VALUES (42, 7, 25)")
        cursor.execute(
            """
            INSERT INTO duplicatas
            (id, venda_id, cliente_id, numero_parcela, valor_parcela, data_vencimento)
            VALUES (5, 42, 7, 1, 10, '2026-01-15')
            """
        )
        cursor.execute(
            """
            INSERT INTO duplicatas_pagas
            (id, venda_id, cliente_id, numero_parcela, valor_original,
             valor_recebido, data_vencimento, data_pagamento, forma_pagamento)
            VALUES (6, 42, 7, 2, 8, 7, '2026-02-15', '2026-02-15', 'Dinheiro')
            """
        )
        cursor.execute("UPDATE vendas SET total_centavos = 2600 WHERE id = 42")
        cursor.execute(
            "UPDATE duplicatas SET valor_parcela_centavos = 1100 WHERE id = 5"
        )
        cursor.execute(
            """
            UPDATE duplicatas_pagas
            SET valor_original_centavos = 900, valor_recebido_centavos = 800
            WHERE id = 6
            """
        )

    registros = duplicata_model.Duplicata.buscar_para_recebimento()

    aberta = next(registro for registro in registros if registro[7] == "aberto")
    paga = next(registro for registro in registros if registro[7] == "pago")
    assert (aberta[4], aberta[9]) == (11.0, 26.0)
    assert (paga[4], paga[9]) == (9.0, 26.0)


def test_ajustar_parcelas_persiste_novo_valor_em_centavos(database):
    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (7, 'Cliente')")
        cursor.execute("INSERT INTO vendas (id, cliente_id) VALUES (42, 7)")
        cursor.execute(
            """
            INSERT INTO duplicatas
            (id, venda_id, cliente_id, numero_parcela, valor_parcela,
             valor_parcela_centavos, data_vencimento, status)
            VALUES
                (5, 42, 7, 1, 100, 10000, '2026-03-01', 'aberto'),
                (6, 42, 7, 2, 100, 10000, '2026-03-31', 'aberto')
            """
        )

    duplicata_model.Duplicata.ajustar_parcelas_restantes(42, 5, 80)

    assert database.get_connection().execute(
        "SELECT valor_parcela_centavos FROM duplicatas WHERE id = 6"
    ).fetchone() == (12000,)
