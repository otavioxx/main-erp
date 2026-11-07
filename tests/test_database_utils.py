import pytest

from mainerp.data import database_utils
from mainerp.data.database import Database


@pytest.fixture
def shared_database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "database_utils.db"))
    monkeypatch.setattr(database_utils, "obter_database", lambda: database)
    yield database
    database.close_connection()


def test_executar_query_reutiliza_a_conexao_e_respeita_transacao_externa(
    shared_database,
):
    database_utils.DatabaseUtils.executar_query(
        "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
    )

    with (
        pytest.raises(RuntimeError, match="falha simulada"),
        shared_database.transacao(),
    ):
        database_utils.DatabaseUtils.executar_query(
            "INSERT INTO registros (valor) VALUES (?)", ("revertido",)
        )
        raise RuntimeError("falha simulada")

    assert (
        database_utils.DatabaseUtils.executar_query("SELECT valor FROM registros") == []
    )


def test_executar_com_retry_persiste_resultado_no_gerenciador_compartilhado(
    shared_database,
):
    database_utils.DatabaseUtils.executar_query(
        "CREATE TABLE registros (id INTEGER PRIMARY KEY, valor TEXT)"
    )

    registro_id = database_utils.DatabaseUtils.executar_com_retry(
        "INSERT INTO registros (valor) VALUES (?)", ("salvo",)
    )

    assert registro_id == 1
    assert database_utils.DatabaseUtils.executar_query(
        "SELECT valor FROM registros WHERE id = ?", (registro_id,)
    ) == [("salvo",)]
