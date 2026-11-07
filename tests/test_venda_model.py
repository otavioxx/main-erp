import pytest

from mainerp.data.database import Database
from mainerp.data.models.venda import Venda, VendaStatus


@pytest.mark.parametrize(
    ("status", "parcelas_pagas", "esperado"),
    [
        (VendaStatus.CONCLUIDA, False, (True, "")),
        (
            VendaStatus.CONCLUIDA,
            True,
            (False, "Venda possui parcelas pagas e não pode ser excluída"),
        ),
        (
            VendaStatus.CANCELADA,
            False,
            (False, "Venda já está cancelada"),
        ),
    ],
)
def test_pode_ser_excluida_respeita_pagamentos_e_status(
    monkeypatch, status, parcelas_pagas, esperado
):
    venda = Venda(id=1, status=status)
    monkeypatch.setattr(venda, "tem_parcelas_pagas", lambda: parcelas_pagas)

    assert venda.pode_ser_excluida() == esperado


def test_salvar_venda_persiste_valores_em_reais_e_centavos(monkeypatch):
    chamadas = []

    def executar_query(query, params=None):
        chamadas.append((query, params))
        return 12

    monkeypatch.setattr(
        "mainerp.data.models.venda.DatabaseUtils.executar_query", executar_query
    )
    venda = Venda(
        cliente_id=3,
        total=12.34,
        desconto=1.05,
        valor_entrada=2.00,
        valor_financiado=10.34,
    )

    assert venda.salvar() == 12

    query, params = chamadas[0]
    assert "total_centavos" in query
    assert "desconto_centavos" in query
    assert "valor_entrada_centavos" in query
    assert "valor_financiado_centavos" in query
    assert params[-4:] == (1234, 105, 200, 1034)


def test_buscar_por_id_le_os_valores_das_colunas_em_centavos(monkeypatch):
    dados = (12, 3, "2026-11-07", 1234, "Dinheiro", "concluida", 1, 105, "", 200, 1034)
    queries = []

    def executar_query(query, params=None):
        queries.append(query)
        return [dados]

    monkeypatch.setattr(
        "mainerp.data.models.venda.DatabaseUtils.executar_query", executar_query
    )

    venda = Venda.buscar_por_id(12)

    assert venda is not None
    assert venda.total == 12.34
    assert venda.desconto == 1.05
    assert venda.valor_entrada == 2.0
    assert venda.valor_financiado == 10.34
    assert "total_centavos" in queries[0]


def test_venda_salva_e_recarrega_centavos_no_banco(tmp_path, monkeypatch):
    banco = Database(str(tmp_path / "venda_centavos.db"))
    monkeypatch.setattr("mainerp.data.database_utils.obter_database", lambda: banco)

    try:
        venda = Venda(
            total=12.34,
            desconto=1.05,
            valor_entrada=2.00,
            valor_financiado=10.34,
        )
        venda_id = venda.salvar()

        assert banco.get_connection().execute(
            """
            SELECT total_centavos, desconto_centavos,
                   valor_entrada_centavos, valor_financiado_centavos
            FROM vendas WHERE id = ?
            """,
            (venda_id,),
        ).fetchone() == (1234, 105, 200, 1034)

        venda_recarregada = Venda.buscar_por_id(venda_id)

        assert venda_recarregada is not None
        assert venda_recarregada.total == 12.34
        assert venda_recarregada.desconto == 1.05
        assert venda_recarregada.valor_entrada == 2.0
        assert venda_recarregada.valor_financiado == 10.34

        venda_recarregada.total = 20.00
        venda_recarregada.salvar()
        assert banco.get_connection().execute(
            "SELECT total_centavos FROM vendas WHERE id = ?", (venda_id,)
        ).fetchone() == (2000,)
    finally:
        banco.close_connection()
