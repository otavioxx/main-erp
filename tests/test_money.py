from decimal import Decimal

import pytest

from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import aplicar_desconto_total, calcular_subtotal


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


def test_helpers_de_itens_calculam_subtotal_e_desconto_em_centavos():
    assert calcular_subtotal(1.005, 2) == 2.02
    assert aplicar_desconto_total(2.02, 0.01) == 2.01
    assert aplicar_desconto_total(2.02, 3) == 0
