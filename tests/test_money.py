from decimal import Decimal

import pytest

from mainerp.data.money import de_centavos, para_centavos


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (0, 0),
        (1.25, 125),
        (0.1 + 0.2, 30),
        ("1.005", 101),
        ("-1.005", -101),
        (Decimal("12.34"), 1234),
        (None, 0),
    ],
)
def test_para_centavos_arredonda_e_converte_valores(valor, esperado):
    assert para_centavos(valor) == esperado


def test_de_centavos_retorna_decimal_exato():
    assert de_centavos(1234) == Decimal("12.34")
    assert de_centavos(-101) == Decimal("-1.01")


def test_para_centavos_rejeita_valor_invalido():
    with pytest.raises(ValueError, match="Valor monetário inválido"):
        para_centavos("não é dinheiro")
