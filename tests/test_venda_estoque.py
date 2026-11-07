from mainerp.data.database_utils import DatabaseUtils
from mainerp.domain.utils.venda_utils import VendaEstoqueManager


def test_atualizar_estoque_venda_subtrai_quantidade_de_cada_produto(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        DatabaseUtils, "executar_query", lambda query, params: chamadas.append(params)
    )

    resultado = VendaEstoqueManager.atualizar_estoque_venda(
        [{"id": 3, "quantidade": 2}, {"id": 8, "quantidade": 1}]
    )

    assert resultado is True
    assert chamadas == [(2, 3), (1, 8)]


def test_devolver_estoque_soma_quantidades_dos_itens_da_venda(monkeypatch):
    chamadas = []

    def executar_query(query, params):
        if query.startswith("SELECT"):
            return [(3, 2), (8, 1)]
        chamadas.append(params)

    monkeypatch.setattr(DatabaseUtils, "executar_query", executar_query)

    resultado = VendaEstoqueManager.devolver_estoque_venda(venda_id=14)

    assert resultado is True
    assert chamadas == [(2, 3), (1, 8)]


def test_verificar_disponibilidade_confirma_estoque_suficiente(monkeypatch):
    monkeypatch.setattr(
        DatabaseUtils,
        "executar_query",
        lambda _query, params: [(5 if params == (3,) else 2,)],
    )

    resultado = VendaEstoqueManager.verificar_disponibilidade_produtos(
        [{"id": 3, "quantidade": 2}, {"id": 8, "quantidade": 2}]
    )

    assert resultado == (True, "")


def test_verificar_disponibilidade_rejeita_produto_sem_estoque_suficiente(
    monkeypatch,
):
    monkeypatch.setattr(
        DatabaseUtils, "executar_query", lambda _query, _params: [(1,)]
    )

    resultado = VendaEstoqueManager.verificar_disponibilidade_produtos(
        [{"id": 3, "quantidade": 2}]
    )

    assert resultado == (False, "Estoque insuficiente para produto ID 3")


def test_verificar_disponibilidade_rejeita_produto_inexistente(monkeypatch):
    monkeypatch.setattr(
        DatabaseUtils, "executar_query", lambda _query, _params: []
    )

    resultado = VendaEstoqueManager.verificar_disponibilidade_produtos(
        [{"id": 99, "quantidade": 1}]
    )

    assert resultado == (False, "Produto ID 99 não encontrado")
