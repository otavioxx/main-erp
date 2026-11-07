# \erp\model\duplicata.py
import logging
from datetime import timedelta

from mainerp.core.exceptions import ErroERP
from mainerp.data.database import obter_database
from mainerp.data.money import de_centavos, para_centavos

logger = logging.getLogger(__name__)


def _converter_valores_duplicatas(linhas, aberta):
    if aberta:
        return [
            (*linha[:4], float(de_centavos(linha[4])), *linha[5:]) for linha in linhas
        ]
    return [
        (
            *linha[:4],
            float(de_centavos(linha[4])),
            float(de_centavos(linha[5])),
            *linha[6:],
        )
        for linha in linhas
    ]


class Duplicata:
    @staticmethod
    def _criar_parcela_pendente(
        cursor, venda_id, cliente_id, numero_parcela, data_vencimento, valor_centavos
    ):
        """Cria a próxima parcela para um saldo que não pôde ser redistribuído."""
        cursor.execute(
            """
            SELECT COALESCE(MAX(numero_parcela), 0) + 1
            FROM (
                SELECT numero_parcela FROM duplicatas WHERE venda_id = ?
                UNION ALL
                SELECT numero_parcela FROM duplicatas_pagas WHERE venda_id = ?
            )
            """,
            (venda_id, venda_id),
        )
        proximo_numero = max(numero_parcela + 1, cursor.fetchone()[0])
        valor_parcela = float(de_centavos(valor_centavos))
        cursor.execute(
            """
            INSERT INTO duplicatas
            (venda_id, cliente_id, numero_parcela, valor_parcela,
             valor_parcela_centavos, data_vencimento, status)
            VALUES (?, ?, ?, ?, ?, date(?, '+30 days'), 'aberto')
            """,
            (
                venda_id,
                cliente_id,
                proximo_numero,
                valor_parcela,
                valor_centavos,
                data_vencimento,
            ),
        )

    def __init__(
        self,
        id=None,
        venda_id=None,
        cliente_id=None,
        numero_parcela=1,
        valor_parcela=0.0,
        data_vencimento=None,
        data_pagamento=None,
        status="aberto",
    ):
        self.id = id
        self.venda_id = venda_id
        self.cliente_id = cliente_id
        self.numero_parcela = numero_parcela
        self.valor_parcela = valor_parcela
        self.data_vencimento = data_vencimento
        self.data_pagamento = data_pagamento
        self.status = status

    def salvar(self):
        with obter_database().transacao() as cursor:
            if self.id:
                cursor.execute(
                    """
                    UPDATE duplicatas SET venda_id=?, cliente_id=?, numero_parcela=?,
                    valor_parcela=?, valor_parcela_centavos=?,
                    data_vencimento=?, data_pagamento=?, status=?
                    WHERE id=?
                """,
                    (
                        self.venda_id,
                        self.cliente_id,
                        self.numero_parcela,
                        self.valor_parcela,
                        para_centavos(self.valor_parcela),
                        self.data_vencimento,
                        self.data_pagamento,
                        self.status,
                        self.id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO duplicatas (venda_id, cliente_id, numero_parcela,
                    valor_parcela, valor_parcela_centavos, data_vencimento,
                    data_pagamento, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        self.venda_id,
                        self.cliente_id,
                        self.numero_parcela,
                        self.valor_parcela,
                        para_centavos(self.valor_parcela),
                        self.data_vencimento,
                        self.data_pagamento,
                        self.status,
                    ),
                )
                self.id = cursor.lastrowid

            return self.id

    @staticmethod
    def criar_parcelas(
        venda_id, cliente_id, valor_financiado, parcelas, data_primeiro_vencimento
    ):
        """Cria parcelas em centavos baseadas no valor financiado."""
        valor_financiado_centavos = para_centavos(valor_financiado)
        valor_base_centavos = valor_financiado_centavos // parcelas
        duplicatas = []

        with obter_database().transacao() as cursor:
            for i in range(parcelas):
                valor_parcela_centavos = (
                    valor_financiado_centavos - valor_base_centavos * (parcelas - 1)
                    if i == parcelas - 1
                    else valor_base_centavos
                )
                valor_parcela = float(de_centavos(valor_parcela_centavos))
                data_vencimento = data_primeiro_vencimento + timedelta(days=30 * i)

                cursor.execute(
                    """
                INSERT INTO duplicatas
                (venda_id, cliente_id, numero_parcela, valor_parcela,
                 valor_parcela_centavos, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, ?, 'aberto')
                """,
                    (
                        venda_id,
                        cliente_id,
                        i + 1,
                        valor_parcela,
                        valor_parcela_centavos,
                        data_vencimento,
                    ),
                )

                duplicata = Duplicata(
                    id=cursor.lastrowid,
                    venda_id=venda_id,
                    cliente_id=cliente_id,
                    numero_parcela=i + 1,
                    valor_parcela=valor_parcela,
                    data_vencimento=data_vencimento,
                    status="aberto",
                )
                duplicatas.append(duplicata)

        return duplicatas

    @staticmethod
    def buscar_por_venda(venda_id):
        with obter_database().transacao() as cursor:
            cursor.execute(
                """
                SELECT id, venda_id, cliente_id, numero_parcela,
                       valor_parcela_centavos, data_vencimento, data_pagamento, status
                FROM duplicatas
                WHERE venda_id = ?
                ORDER BY numero_parcela
                """,
                (venda_id,),
            )
            return [
                (*row[:4], float(de_centavos(row[4])), *row[5:])
                for row in cursor.fetchall()
            ]

    @staticmethod
    def buscar_todas_com_cliente():
        """Busca todas as duplicatas abertas com informações do cliente"""
        with obter_database().transacao() as cursor:
            cursor.execute("""
                SELECT d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                       d.valor_parcela_centavos, d.data_vencimento, d.data_pagamento,
                       d.status, c.nome as cliente_nome
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                WHERE d.status = 'aberto'
                ORDER BY d.data_vencimento
            """)
            return [
                (*row[:4], float(de_centavos(row[4])), *row[5:])
                for row in cursor.fetchall()
            ]

    @staticmethod
    def _registrar_pagamento(
        cursor,
        venda_id,
        cliente_id,
        numero_parcela,
        valor_original_centavos,
        valor_recebido_centavos,
        data_vencimento,
        data_pagamento,
        forma_pagamento,
    ):
        cursor.execute(
            """
            INSERT INTO duplicatas_pagas
            (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido,
             valor_original_centavos, valor_recebido_centavos, data_vencimento,
             data_pagamento, forma_pagamento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                venda_id,
                cliente_id,
                numero_parcela,
                float(de_centavos(valor_original_centavos)),
                float(de_centavos(valor_recebido_centavos)),
                valor_original_centavos,
                valor_recebido_centavos,
                data_vencimento,
                data_pagamento,
                forma_pagamento,
            ),
        )

    @staticmethod
    def buscar_para_recebimento():
        """Busca parcelas abertas e pagas no formato consumido pela tela de recebimentos."""
        query = """
            SELECT
                d.id,
                d.cliente_id,
                d.venda_id,
                d.numero_parcela,
                d.valor_parcela_centavos as valor,
                d.data_vencimento,
                NULL as data_pagamento,
                'aberto' as status,
                c.nome as cliente_nome,
                v.total_centavos as venda_total,
                v.data_venda,
                NULL as forma_pagamento,
                0 as is_paga
            FROM duplicatas d
            LEFT JOIN clientes c ON d.cliente_id = c.id
            LEFT JOIN vendas v ON d.venda_id = v.id
            WHERE d.status = 'aberto'

            UNION ALL

            SELECT
                dp.id,
                dp.cliente_id,
                dp.venda_id,
                dp.numero_parcela,
                dp.valor_original_centavos as valor,
                dp.data_vencimento,
                dp.data_pagamento,
                'pago' as status,
                c.nome as cliente_nome,
                v.total_centavos as venda_total,
                v.data_venda,
                dp.forma_pagamento,
                1 as is_paga
            FROM duplicatas_pagas dp
            LEFT JOIN clientes c ON dp.cliente_id = c.id
            LEFT JOIN vendas v ON dp.venda_id = v.id
            ORDER BY status, data_vencimento
        """
        with obter_database().transacao() as cursor:
            cursor.execute(query)
            return [
                (
                    *dados[:4],
                    float(de_centavos(dados[4])),
                    *dados[5:9],
                    float(de_centavos(dados[9])) if dados[9] is not None else 0.0,
                    *dados[10:],
                )
                for dados in cursor.fetchall()
            ]

    @staticmethod
    def contar_parcelas_por_venda(venda_id):
        with obter_database().transacao() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM duplicatas "
                "WHERE venda_id = ? AND status = 'aberto'",
                (venda_id,),
            )
            abertas = cursor.fetchone()[0] or 0
            cursor.execute(
                "SELECT COUNT(*) FROM duplicatas_pagas WHERE venda_id = ?",
                (venda_id,),
            )
            pagas = cursor.fetchone()[0] or 0
        return abertas + pagas

    @staticmethod
    def buscar_dados_cliente_venda(cliente_id, venda_id):
        with obter_database().transacao() as cursor:
            cursor.execute(
                """
                SELECT c.nome, c.cpf_cnpj, c.endereco, v.total_centavos, v.data_venda
                FROM clientes c
                LEFT JOIN vendas v ON v.cliente_id = c.id
                WHERE c.id = ? AND v.id = ?
                """,
                (cliente_id, venda_id),
            )
            dados = cursor.fetchone()
            if not dados:
                return None
            return (*dados[:3], float(de_centavos(dados[3])), *dados[4:])

    @staticmethod
    def buscar_por_status(status):
        """Busca duplicatas por status"""
        with obter_database().transacao() as cursor:
            if status == "aberto":
                cursor.execute("""
                    SELECT d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                           d.valor_parcela_centavos, d.data_vencimento, d.data_pagamento,
                           d.status, c.nome as cliente_nome
                    FROM duplicatas d
                    LEFT JOIN clientes c ON d.cliente_id = c.id
                    WHERE d.status = 'aberto'
                    ORDER BY d.data_vencimento
                """)
            else:
                cursor.execute("""
                    SELECT dp.id, dp.venda_id, dp.cliente_id, dp.numero_parcela,
                           dp.valor_original_centavos, dp.valor_recebido_centavos,
                           dp.data_vencimento, dp.data_pagamento, dp.forma_pagamento,
                           dp.created_at, c.nome as cliente_nome
                    FROM duplicatas_pagas dp
                    LEFT JOIN clientes c ON dp.cliente_id = c.id
                    ORDER BY dp.data_pagamento DESC
                """)
            return _converter_valores_duplicatas(cursor.fetchall(), status == "aberto")

    @staticmethod
    def buscar_por_cliente(cliente_id):
        """Busca duplicatas por cliente"""
        with obter_database().transacao() as cursor:
            cursor.execute(
                """
                SELECT d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                       d.valor_parcela_centavos, d.data_vencimento, d.data_pagamento,
                       d.status, c.nome as cliente_nome
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                WHERE d.cliente_id = ? AND d.status = 'aberto'
                ORDER BY d.data_vencimento
            """,
                (cliente_id,),
            )

            abertas = cursor.fetchall()

            cursor.execute(
                """
                SELECT dp.id, dp.venda_id, dp.cliente_id, dp.numero_parcela,
                       dp.valor_original_centavos, dp.valor_recebido_centavos,
                       dp.data_vencimento, dp.data_pagamento, dp.forma_pagamento,
                       dp.created_at, c.nome as cliente_nome
                FROM duplicatas_pagas dp
                LEFT JOIN clientes c ON dp.cliente_id = c.id
                WHERE dp.cliente_id = ?
                ORDER BY dp.data_pagamento DESC
            """,
                (cliente_id,),
            )

            pagas = cursor.fetchall()

            return _converter_valores_duplicatas(
                abertas, aberta=True
            ) + _converter_valores_duplicatas(pagas, aberta=False)

    @staticmethod
    def marcar_como_paga(duplicata_id, valor_recebido, data_pagamento, forma_pagamento):
        with obter_database().transacao() as cursor:
            # Buscar duplicata
            cursor.execute(
                """
                SELECT id, venda_id, cliente_id, numero_parcela,
                       valor_parcela_centavos, data_vencimento
                FROM duplicatas WHERE id = ?
                """,
                (duplicata_id,),
            )
            duplicata = cursor.fetchone()
            if not duplicata:
                raise ErroERP("Duplicata não encontrada")

            valor_original_centavos = duplicata[4]
            venda_id = duplicata[1]
            cliente_id = duplicata[2]
            numero_parcela = duplicata[3]
            data_vencimento = duplicata[5]

            # Calcular diferença
            valor_recebido_centavos = para_centavos(valor_recebido)
            diferenca_centavos = valor_recebido_centavos - valor_original_centavos
            diferenca = float(de_centavos(diferenca_centavos))

            # Buscar parcelas restantes
            cursor.execute(
                """
                SELECT id, numero_parcela, valor_parcela_centavos FROM duplicatas
                WHERE venda_id = ? AND id != ? AND status = 'aberto'
                ORDER BY numero_parcela
            """,
                (venda_id, duplicata_id),
            )

            parcelas_restantes = cursor.fetchall()
            qtd_restantes = len(parcelas_restantes)

            if qtd_restantes == 0 and diferenca_centavos < 0:
                Duplicata._criar_parcela_pendente(
                    cursor,
                    venda_id,
                    cliente_id,
                    numero_parcela,
                    data_vencimento,
                    -diferenca_centavos,
                )

            # Se há diferença e parcelas restantes, redistribuir
            if qtd_restantes > 0 and abs(diferenca) > 1e-9:
                ajuste_por_parcela = round(diferenca / qtd_restantes, 2)

                # Verificar se precisa quitar parcelas automaticamente
                if diferenca > 0:  # Pagou a mais
                    # Calcular o total das parcelas restantes
                    total_parcelas_restantes = sum(
                        float(de_centavos(p[2])) for p in parcelas_restantes
                    )

                    if diferenca >= total_parcelas_restantes:
                        # O valor pago é suficiente para quitar todas as parcelas restantes
                        for (
                            parcela_id,
                            num_parcela,
                            valor_parcela,
                        ) in parcelas_restantes:
                            # Inserir na tabela de pagas
                            Duplicata._registrar_pagamento(
                                cursor,
                                venda_id,
                                cliente_id,
                                num_parcela,
                                valor_parcela,
                                valor_parcela,
                                data_vencimento,
                                data_pagamento,
                                forma_pagamento,
                            )

                            # Remover da tabela duplicatas
                            cursor.execute(
                                "DELETE FROM duplicatas WHERE id = ?", (parcela_id,)
                            )
                    else:
                        # Redistribuir a diferença normalmente
                        for (
                            parcela_id,
                            num_parcela,
                            valor_parcela,
                        ) in parcelas_restantes:
                            valor_parcela_reais = float(de_centavos(valor_parcela))
                            novo_valor = valor_parcela_reais - ajuste_por_parcela

                            if novo_valor <= 0:
                                # Parcela quitada automaticamente
                                Duplicata._registrar_pagamento(
                                    cursor,
                                    venda_id,
                                    cliente_id,
                                    num_parcela,
                                    valor_parcela,
                                    valor_parcela,
                                    data_vencimento,
                                    data_pagamento,
                                    forma_pagamento,
                                )

                                cursor.execute(
                                    "DELETE FROM duplicatas WHERE id = ?", (parcela_id,)
                                )
                            else:
                                # Atualizar valor da parcela
                                cursor.execute(
                                    """
                                    UPDATE duplicatas
                                    SET valor_parcela = ?, valor_parcela_centavos = ?
                                    WHERE id = ?
                                    """,
                                    (
                                        novo_valor,
                                        para_centavos(novo_valor),
                                        parcela_id,
                                    ),
                                )
                else:
                    # Pagou a menos - aumentar o valor das parcelas restantes
                    for parcela_id, _num_parcela, valor_parcela in parcelas_restantes:
                        novo_valor = float(de_centavos(valor_parcela)) + abs(
                            ajuste_por_parcela
                        )
                        cursor.execute(
                            """
                            UPDATE duplicatas
                            SET valor_parcela = ?, valor_parcela_centavos = ?
                            WHERE id = ?
                            """,
                            (novo_valor, para_centavos(novo_valor), parcela_id),
                        )

            # Inserir a parcela atual em duplicatas_pagas
            Duplicata._registrar_pagamento(
                cursor,
                venda_id,
                cliente_id,
                numero_parcela,
                valor_original_centavos,
                valor_recebido_centavos,
                data_vencimento,
                data_pagamento,
                forma_pagamento,
            )

            # Remover da tabela duplicatas
            cursor.execute("DELETE FROM duplicatas WHERE id = ?", (duplicata_id,))

            return True

    @staticmethod
    def ajustar_parcelas_restantes(
        venda_id, duplicata_id, valor_pago, valor_original=None
    ):
        try:
            return Duplicata._ajustar_parcelas_restantes(
                venda_id, duplicata_id, valor_pago, valor_original
            )
        except Exception:
            logger.exception("Erro ao redistribuir diferença de pagamento")
            raise

    @staticmethod
    def _ajustar_parcelas_restantes(
        venda_id, duplicata_id, valor_pago, valor_original=None
    ):
        """
        Ajusta as duplicatas restantes redistribuindo a diferença igualmente.
        Se pagar a menos -> aumenta as parcelas.
        Se pagar a mais -> reduz as parcelas (quitando se valor ficar <= 0).
        """
        from datetime import datetime

        with obter_database().transacao() as cursor:
            # Obter dados da duplicata original se necessário.
            if valor_original is None:
                cursor.execute(
                    """
                    SELECT valor_parcela_centavos, cliente_id, numero_parcela,
                           data_vencimento
                    FROM duplicatas WHERE id = ?
                    """,
                    (duplicata_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ErroERP(
                        "Não foi possível obter o valor da duplicata original para ajuste."
                    )
                valor_original_centavos = row[0]
                valor_original = float(de_centavos(valor_original_centavos))
                cliente_id, numero_parcela, data_vencimento = row[1:]
            else:
                cursor.execute(
                    """
                    SELECT cliente_id, numero_parcela, data_vencimento
                    FROM duplicatas WHERE id = ? AND venda_id = ?
                    """,
                    (duplicata_id, venda_id),
                )
                row = cursor.fetchone()
                if row:
                    cliente_id, numero_parcela, data_vencimento = row
                else:
                    cliente_id = numero_parcela = data_vencimento = None
                valor_original_centavos = para_centavos(valor_original)

            diferenca = float(valor_pago) - float(valor_original)
            diferenca_centavos = para_centavos(valor_pago) - para_centavos(
                valor_original
            )
            if diferenca_centavos == 0:
                # Nada a ajustar
                return

            logger.debug("Redistribuindo diferença de pagamento: %.2f", diferenca)

            # Buscar parcelas restantes abertas
            cursor.execute(
                """
                SELECT id, numero_parcela, valor_parcela_centavos,
                       cliente_id, data_vencimento
                FROM duplicatas
                WHERE venda_id = ? AND id != ? AND status = 'aberto'
                ORDER BY numero_parcela
            """,
                (venda_id, duplicata_id),
            )
            parcelas_restantes = cursor.fetchall()

            if not parcelas_restantes:
                if diferenca_centavos < 0 and cliente_id is not None:
                    Duplicata._criar_parcela_pendente(
                        cursor,
                        venda_id,
                        cliente_id,
                        numero_parcela,
                        data_vencimento,
                        -diferenca_centavos,
                    )
                    logger.info(
                        "Criada parcela para saldo pendente de venda %s", venda_id
                    )
                    return

                logger.debug("Nenhuma parcela restante para redistribuir")
                return

            qtd = len(parcelas_restantes)
            ajuste = round(diferenca / qtd, 2)  # diferença distribuída igualmente
            hoje = datetime.now().date()

            for parcela in parcelas_restantes:
                (
                    parcela_id,
                    numero_parcela,
                    valor_parcela_centavos,
                    cliente_id,
                    data_venc,
                ) = parcela
                valor_parcela = float(de_centavos(valor_parcela_centavos))

                novo_valor = (
                    round(valor_parcela - ajuste, 2)
                    if diferenca > 0
                    else round(valor_parcela + abs(ajuste), 2)
                )

                if novo_valor <= 0:
                    # Parcela quitada automaticamente
                    Duplicata._registrar_pagamento(
                        cursor,
                        venda_id,
                        cliente_id,
                        numero_parcela,
                        valor_parcela_centavos,
                        valor_parcela_centavos,
                        data_venc,
                        hoje,
                        None,
                    )
                    cursor.execute("DELETE FROM duplicatas WHERE id = ?", (parcela_id,))
                    logger.debug(
                        "Parcela %s quitada automaticamente (id %s)",
                        numero_parcela,
                        parcela_id,
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE duplicatas
                        SET valor_parcela = ?, valor_parcela_centavos = ?
                        WHERE id = ? AND status = 'aberto'
                    """,
                        (novo_valor, para_centavos(novo_valor), parcela_id),
                    )
                    logger.debug(
                        "Parcela %s ajustada para R$ %.2f",
                        numero_parcela,
                        novo_valor,
                    )

            logger.debug("Redistribuição concluída e commitada")
