import pytest

from models.produto import Produto
from utils.produto_utils import ProdutoUtils


@pytest.mark.parametrize(
    ("nome", "preco_custo", "preco_venda", "erros_esperados"),
    [
        ("Camisa", 10, 15, []),
        (" ", 10, 15, ["O nome do produto é obrigatório"]),
        ("Camisa", -1, 15, ["Preço de custo não pode ser negativo"]),
        ("Camisa", 10, -1, ["Preço de venda não pode ser negativo"]),
    ],
)
def test_validar_produto(nome, preco_custo, preco_venda, erros_esperados):
    assert ProdutoUtils.validar_produto(nome, preco_custo, preco_venda) == erros_esperados


@pytest.mark.parametrize(
    ("estoque", "pedidos_ativos", "condicionais_ativas", "pode"),
    [
        (0, 0, 0, True),
        (2, 0, 0, False),
        (0, 1, 0, False),
        (0, 0, 1, False),
    ],
)
def test_pode_ser_inativado_considera_estoque_e_vinculos(
    monkeypatch, estoque, pedidos_ativos, condicionais_ativas, pode
):
    produto = Produto(estoque=estoque)
    monkeypatch.setattr(
        produto, "_contar_pedidos_ativos", lambda: pedidos_ativos
    )
    monkeypatch.setattr(
        produto, "_contar_condicionais_ativas", lambda: condicionais_ativas
    )

    resultado = produto.pode_ser_inativado()

    assert resultado["pode"] is pode
    assert bool(resultado["motivos"]) is (not pode)


def test_inativar_salva_produto_quando_regras_permitem(monkeypatch):
    produto = Produto(estoque=0)
    monkeypatch.setattr(produto, "_contar_pedidos_ativos", lambda: 0)
    monkeypatch.setattr(produto, "_contar_condicionais_ativas", lambda: 0)
    salvamentos = []
    monkeypatch.setattr(produto, "salvar", lambda: salvamentos.append(produto.ativo))

    produto.inativar()

    assert produto.ativo is False
    assert salvamentos == [False]


def test_inativar_rejeita_produto_com_estoque(monkeypatch):
    produto = Produto(estoque=1)
    monkeypatch.setattr(produto, "_contar_pedidos_ativos", lambda: 0)
    monkeypatch.setattr(produto, "_contar_condicionais_ativas", lambda: 0)
    monkeypatch.setattr(produto, "salvar", lambda: pytest.fail("não deve salvar"))

    with pytest.raises(ValueError, match="Produto possui estoque: 1 unidades"):
        produto.inativar()

    assert produto.ativo is True
