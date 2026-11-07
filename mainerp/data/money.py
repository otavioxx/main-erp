import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def para_centavos_localizado(valor: str) -> int:
    """Converte texto monetário brasileiro ou internacional para centavos."""
    texto = valor.strip().replace("R$", "").replace(" ", "").replace("\u00a0", "")
    if not texto or not re.fullmatch(r"[+-]?[0-9.,]+", texto):
        raise ValueError(f"Valor monetário inválido: {valor!r}")

    sinal = ""
    if texto[0] in "+-":
        sinal, texto = texto[0], texto[1:]

    tem_ponto = "." in texto
    tem_virgula = "," in texto
    if tem_ponto and tem_virgula:
        separador_decimal = "." if texto.rfind(".") > texto.rfind(",") else ","
        separador_grupo = "," if separador_decimal == "." else "."
        inteiro, fracao = texto.rsplit(separador_decimal, 1)
        grupos = inteiro.split(separador_grupo)
        if (
            not fracao.isdigit()
            or not grupos[0].isdigit()
            or not 1 <= len(grupos[0]) <= 3
            or any(not grupo.isdigit() or len(grupo) != 3 for grupo in grupos[1:])
        ):
            raise ValueError(f"Valor monetário inválido: {valor!r}")
        normalizado = f"{sinal}{''.join(grupos)}.{fracao}"
    elif tem_ponto or tem_virgula:
        separador = "." if tem_ponto else ","
        partes = texto.split(separador)
        if len(partes) == 2:
            inteiro, fracao = partes
            if not inteiro.isdigit() or not fracao.isdigit():
                raise ValueError(f"Valor monetário inválido: {valor!r}")
            normalizado = f"{sinal}{inteiro}.{fracao}"
        elif (
            partes[0].isdigit()
            and 1 <= len(partes[0]) <= 3
            and all(grupo.isdigit() and len(grupo) == 3 for grupo in partes[1:])
        ):
            normalizado = f"{sinal}{''.join(partes)}"
        else:
            raise ValueError(f"Valor monetário inválido: {valor!r}")
    else:
        normalizado = f"{sinal}{texto}"

    try:
        return para_centavos(normalizado)
    except ValueError as erro:
        raise ValueError(f"Valor monetário inválido: {valor!r}") from erro


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
