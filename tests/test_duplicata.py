from datetime import date, timedelta

from models.duplicata import DatabaseUtils, Duplicata


def test_criar_parcelas_divide_valor_e_incrementa_vencimentos(monkeypatch):
    chamadas = []

    def executar_com_retry(query, params):
        chamadas.append((query, params))
        return len(chamadas)

    monkeypatch.setattr(DatabaseUtils, "executar_com_retry", executar_com_retry)
    primeiro_vencimento = date(2026, 1, 15)

    parcelas = Duplicata.criar_parcelas(
        venda_id=42,
        cliente_id=7,
        valor_financiado=100,
        parcelas=3,
        data_primeiro_vencimento=primeiro_vencimento,
    )

    assert [parcela.id for parcela in parcelas] == [1, 2, 3]
    assert [parcela.numero_parcela for parcela in parcelas] == [1, 2, 3]
    assert [parcela.valor_parcela for parcela in parcelas] == [100 / 3] * 3
    assert [parcela.data_vencimento for parcela in parcelas] == [
        primeiro_vencimento + timedelta(days=30 * indice)
        for indice in range(3)
    ]
    assert all(parcela.status == "aberto" for parcela in parcelas)
    assert [chamada[1][0:4] for chamada in chamadas] == [
        (42, 7, 1, 100 / 3),
        (42, 7, 2, 100 / 3),
        (42, 7, 3, 100 / 3),
    ]
