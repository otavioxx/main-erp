import pytest

from mainerp.domain.utils.venda_utils import VendaCalculator, VendaValidator


@pytest.mark.parametrize(
    ("preco", "quantidade", "esperado"),
    [
        (12.50, 3, 37.50),
        (1.005, 1, 1.0),
        (0, 4, 0.0),
    ],
)
def test_calcular_subtotal_produto(preco, quantidade, esperado):
    assert VendaCalculator.calcular_subtotal_produto(preco, quantidade) == esperado


def test_calcular_total_produtos_arredonda_soma():
    produtos = [{"subtotal": 10.105}, {"subtotal": 2.205}]

    assert VendaCalculator.calcular_total_produtos(produtos) == 12.31


@pytest.mark.parametrize(
    ("subtotal", "desconto", "esperado"),
    [
        (100, 15, 85.0),
        (10, 12, 0.0),
        (10.555, 0.555, 10.0),
    ],
)
def test_aplicar_desconto_limita_total_a_zero(subtotal, desconto, esperado):
    assert VendaCalculator.aplicar_desconto(subtotal, desconto) == esperado


@pytest.mark.parametrize(
    ("total", "parcelas", "esperado"),
    [
        (100, 4, 25.0),
        (10, 3, 3.33),
        (100, 0, 100),
        (100, -1, 100),
    ],
)
def test_calcular_valor_parcela(total, parcelas, esperado):
    assert VendaCalculator.calcular_valor_parcela(total, parcelas) == esperado


def test_distribuir_desconto_proporcional_preserva_itens_de_entrada():
    produtos = [
        {"id": 1, "subtotal": 60},
        {"id": 2, "subtotal": 40},
    ]

    resultado = VendaCalculator.distribuir_desconto_proporcional(produtos, 10)

    assert resultado == [
        {"id": 1, "subtotal": 60, "desconto": 6.0, "subtotal_com_desconto": 54.0},
        {"id": 2, "subtotal": 40, "desconto": 4.0, "subtotal_com_desconto": 36.0},
    ]
    assert produtos == [{"id": 1, "subtotal": 60}, {"id": 2, "subtotal": 40}]


@pytest.mark.parametrize(
    ("quantidade", "estoque", "ja_selecionada", "valido"),
    [
        (2, 5, 1, True),
        (0, 5, 0, False),
        (5, 5, 1, False),
        (-1, 5, 0, False),
    ],
)
def test_validar_quantidade_disponivel(
    quantidade, estoque, ja_selecionada, valido
):
    resultado, mensagem = VendaValidator.validar_quantidade_disponivel(
        quantidade, estoque, ja_selecionada
    )

    assert resultado is valido
    assert (mensagem == "") is valido
