"""Exceções do PLUMA."""


class ErroERP(Exception):
    """Erro de operação/negócio do sistema (mensagem pensada para o usuário).

    Herda de Exception, então todo ``except Exception`` existente continua
    funcionando; o ganho é poder capturar só os erros do sistema quando quiser.
    """
