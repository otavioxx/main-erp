import pytest

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
