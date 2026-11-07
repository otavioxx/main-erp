from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def para_centavos(valor) -> int:
    """Converte um valor monetário para centavos com arredondamento comercial."""
    if valor is None:
        return 0

    try:
        quantizado = Decimal(str(valor)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError) as erro:
        raise ValueError(f"Valor monetário inválido: {valor!r}") from erro

    return int(quantizado * 100)


def de_centavos(centavos: int) -> Decimal:
    """Converte centavos inteiros para um valor Decimal em unidade monetária."""
    return (Decimal(centavos) / 100).quantize(Decimal("0.01"))
