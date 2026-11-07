from mainerp.data.database import Database
from mainerp.data.models import condicional as condicional_model


def test_condicional_persiste_e_le_valores_em_centavos(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "condicional_centavos.db"))
    monkeypatch.setattr(condicional_model, "obter_database", lambda: database)

    try:
        with database.transacao() as cursor:
            cursor.execute("INSERT INTO clientes (id, nome) VALUES (1, 'Cliente')")
            cursor.execute(
                """
                INSERT INTO produtos (id, nome, preco_custo, preco_venda)
                VALUES (1, 'Produto', 1, 2)
                """
            )

        condicional = condicional_model.Condicional(cliente_id=1, desconto=0.01)
        condicional.itens = [
            {"produto_id": 1, "quantidade": 2, "preco_unitario": 1.005}
        ]
        condicional_id = condicional.salvar()

        assert database.get_connection().execute(
            """
            SELECT desconto_centavos FROM condicionais WHERE id = ?
            """,
            (condicional_id,),
        ).fetchone() == (1,)
        assert database.get_connection().execute(
            """
            SELECT preco_unitario_centavos
            FROM itens_condicional WHERE condicional_id = ?
            """,
            (condicional_id,),
        ).fetchone() == (101,)
        assert condicional.calcular_subtotal_centavos() == 202
        assert condicional.calcular_subtotal() == 2.02
        assert condicional.calcular_total() == 2.01

        with database.transacao() as cursor:
            cursor.execute(
                "UPDATE condicionais SET desconto = 9 WHERE id = ?",
                (condicional_id,),
            )
            cursor.execute(
                "UPDATE condicionais SET desconto_centavos = 50 WHERE id = ?",
                (condicional_id,),
            )
            cursor.execute(
                """
                UPDATE itens_condicional
                SET preco_unitario = 9
                WHERE condicional_id = ?
                """,
                (condicional_id,),
            )
            cursor.execute(
                """
                UPDATE itens_condicional SET preco_unitario_centavos = 250
                WHERE condicional_id = ?
                """,
                (condicional_id,),
            )

        recarregada = condicional_model.Condicional.buscar_por_id(condicional_id)
        assert recarregada is not None
        assert recarregada.desconto == 0.5
        assert recarregada.itens[0]["preco_unitario"] == 2.5
        assert recarregada.calcular_total() == 4.5
        assert condicional_model.Condicional.buscar_todas()[0][6] == 0.5
    finally:
        database.close_connection()
