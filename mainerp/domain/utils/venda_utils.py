"""
Utilitários de Venda - Versão Refatorada
Centraliza toda a lógica de negócio relacionada a vendas
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from mainerp.core.app_logging import registrar_excecao
from mainerp.core.exceptions import ErroERP
from mainerp.data.database_utils import DatabaseUtils
from mainerp.data.money import de_centavos, para_centavos
from mainerp.domain.utils.helpers import converter_data_string


class VendaValidator:
    """Validador para regras de negócio de vendas"""

    @staticmethod
    def validar_produto_para_venda(produto) -> tuple[bool, str]:
        """Valida se produto pode ser vendido"""
        if not produto:
            return False, "Produto não encontrado"

        if produto.preco_venda <= 0:
            return False, f"Produto '{produto.nome}' possui preço de venda 0"

        if produto.estoque <= 0:
            return False, f"Produto '{produto.nome}' está sem estoque"

        return True, ""

    @staticmethod
    def validar_quantidade_disponivel(
        quantidade: int, estoque_atual: int, quantidade_ja_selecionada: int = 0
    ) -> tuple[bool, str]:
        """Valida se quantidade solicitada está disponível"""
        quantidade_total = quantidade + quantidade_ja_selecionada

        if quantidade <= 0:
            return False, "Quantidade deve ser maior que zero"

        if quantidade_total > estoque_atual:
            return (
                False,
                f"Quantidade total ({quantidade_total}) excede estoque disponível ({estoque_atual})",
            )

        return True, ""

    @staticmethod
    def validar_venda_para_finalizacao(
        cliente, produtos: list[dict]
    ) -> tuple[bool, str]:
        """Valida se venda pode ser finalizada"""
        if not cliente:
            return False, "Cliente deve ser selecionado"

        if not produtos:
            return False, "Adicione pelo menos um produto à venda"

        # Validar produtos individualmente
        for produto in produtos:
            if produto.get("quantidade", 0) <= 0:
                return (
                    False,
                    f"Produto '{produto.get('nome', 'Desconhecido')}' com quantidade inválida",
                )

            if produto.get("preco", 0) <= 0:
                return (
                    False,
                    f"Produto '{produto.get('nome', 'Desconhecido')}' com preço inválido",
                )

        return True, ""


class VendaCalculator:
    """Calculador para operações financeiras de vendas"""

    @staticmethod
    def calcular_subtotal_produto_centavos(preco: float, quantidade: int) -> int:
        """Calcula subtotal de um produto em centavos."""
        return para_centavos(preco) * int(quantidade)

    @staticmethod
    def calcular_subtotal_produto(preco: float, quantidade: int) -> float:
        """Calcula subtotal em reais, mantendo a interface legada."""
        return float(
            de_centavos(
                VendaCalculator.calcular_subtotal_produto_centavos(preco, quantidade)
            )
        )

    @staticmethod
    def calcular_total_produtos_centavos(produtos: list[dict[str, Any]]) -> int:
        """Soma os subtotais dos produtos em centavos."""
        return sum(para_centavos(produto.get("subtotal", 0)) for produto in produtos)

    @staticmethod
    def calcular_total_produtos(produtos: list[dict[str, Any]]) -> float:
        """Calcula total em reais, mantendo a interface legada."""
        return float(
            de_centavos(VendaCalculator.calcular_total_produtos_centavos(produtos))
        )

    @staticmethod
    def aplicar_desconto_centavos(subtotal: int, desconto: int) -> int:
        """Aplica desconto a valores em centavos, sem permitir total negativo."""
        return max(0, int(subtotal) - int(desconto))

    @staticmethod
    def aplicar_desconto(subtotal: float, desconto: float) -> float:
        """Aplica desconto em reais, mantendo a interface legada."""
        total_centavos = VendaCalculator.aplicar_desconto_centavos(
            para_centavos(subtotal), para_centavos(desconto)
        )
        return float(de_centavos(total_centavos))

    @staticmethod
    def calcular_valor_parcela_centavos(total: int, num_parcelas: int) -> int:
        """Calcula o valor arredondado de uma parcela em centavos."""
        if num_parcelas <= 0:
            return int(total)
        valor = Decimal(int(total)) / Decimal(num_parcelas)
        return int(valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def calcular_valor_parcela(total: float, num_parcelas: int) -> float:
        """Calcula valor da parcela em reais, mantendo a interface legada."""
        if num_parcelas <= 0:
            return total
        valor_centavos = VendaCalculator.calcular_valor_parcela_centavos(
            para_centavos(total), num_parcelas
        )
        return float(de_centavos(valor_centavos))

    @staticmethod
    def distribuir_desconto_proporcional(
        produtos: list[dict[str, Any]], desconto_total: float
    ) -> list[dict[str, Any]]:
        """Distribui desconto proporcionalmente entre produtos"""
        desconto_total_centavos = para_centavos(desconto_total)
        if desconto_total_centavos <= 0:
            return produtos

        total_sem_desconto_centavos = VendaCalculator.calcular_total_produtos_centavos(
            produtos
        )
        if total_sem_desconto_centavos <= 0:
            return produtos

        produtos_com_desconto = []
        desconto_aplicado_centavos = 0

        for i, produto in enumerate(produtos):
            subtotal_centavos = para_centavos(produto["subtotal"])
            if i == len(produtos) - 1:  # Último produto recebe o resto
                desconto_produto_centavos = (
                    desconto_total_centavos - desconto_aplicado_centavos
                )
            else:
                desconto_proporcional = Decimal(
                    desconto_total_centavos * subtotal_centavos
                ) / Decimal(total_sem_desconto_centavos)
                desconto_produto_centavos = int(
                    desconto_proporcional.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                )
                desconto_aplicado_centavos += desconto_produto_centavos

            produto_copy = produto.copy()
            produto_copy["desconto"] = float(de_centavos(desconto_produto_centavos))
            produto_copy["subtotal_com_desconto"] = float(
                de_centavos(subtotal_centavos - desconto_produto_centavos)
            )
            produtos_com_desconto.append(produto_copy)

        return produtos_com_desconto


class VendaRepository:
    """Repositório para operações de banco de dados relacionadas a vendas"""

    @staticmethod
    def buscar_vendas_com_filtros(
        data_inicio: str | None = None,
        data_fim: str | None = None,
        cliente_id: int | None = None,
    ) -> list[tuple]:
        """Busca vendas com filtros aplicados"""
        query = """
            SELECT v.*, c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE 1=1
        """
        params = []

        # Converter datas se necessário
        if data_inicio:
            data_inicio_obj = converter_data_string(data_inicio, "%d/%m/%Y")
            if data_inicio_obj:
                query += " AND v.data_venda >= ?"
                params.append(data_inicio_obj.strftime("%Y-%m-%d"))

        if data_fim:
            data_fim_obj = converter_data_string(data_fim, "%d/%m/%Y")
            if data_fim_obj:
                query += " AND v.data_venda <= ?"
                params.append(data_fim_obj.strftime("%Y-%m-%d"))

        if cliente_id:
            query += " AND v.cliente_id = ?"
            params.append(cliente_id)

        query += " ORDER BY v.data_venda DESC, v.id DESC"

        return DatabaseUtils.executar_query(query, tuple(params))

    @staticmethod
    def salvar_itens_venda(venda_id: int, produtos: list[dict[str, Any]]) -> bool:
        """Salva itens da venda no banco"""
        try:
            for produto in produtos:
                query = """
                    INSERT INTO itens_venda
                    (venda_id, produto_id, quantidade, preco_unitario, desconto)
                    VALUES (?, ?, ?, ?, ?)
                """
                desconto_produto = produto.get("desconto", 0)
                params = (
                    venda_id,
                    produto["id"],
                    produto["quantidade"],
                    produto["preco"],
                    desconto_produto,
                )
                DatabaseUtils.executar_query(query, params)

            return True
        except Exception as e:
            raise ErroERP(f"Erro ao salvar itens da venda: {e!s}") from e

    @staticmethod
    def buscar_itens_venda_detalhados(venda_id: int) -> list[tuple]:
        """Busca itens da venda com informações detalhadas"""
        query = """
            SELECT iv.id, iv.venda_id, iv.produto_id, iv.quantidade,
                   iv.preco_unitario, iv.desconto, p.nome as produto_nome,
                   p.codigo_barras, p.referencia, p.cor, p.tamanho
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = ?
            ORDER BY p.nome
        """
        return DatabaseUtils.executar_query(query, (venda_id,))

    @staticmethod
    def verificar_parcelas_pagas(venda_id: int) -> bool:
        """Verifica se venda possui parcelas pagas"""
        query = "SELECT COUNT(*) FROM duplicatas_pagas WHERE venda_id = ?"
        resultado = DatabaseUtils.executar_query(query, (venda_id,))
        return resultado[0][0] > 0 if resultado else False

    @staticmethod
    def obter_resumo_periodo(data_inicio: str, data_fim: str) -> dict[str, Any]:
        """Obtém resumo de vendas por período"""
        try:
            # Converter datas
            data_inicio_obj = converter_data_string(data_inicio, "%d/%m/%Y")
            data_fim_obj = converter_data_string(data_fim, "%d/%m/%Y")

            if not data_inicio_obj or not data_fim_obj:
                return {}

            data_inicio_db = data_inicio_obj.strftime("%Y-%m-%d")
            data_fim_db = data_fim_obj.strftime("%Y-%m-%d")

            query = """
                SELECT
                    COUNT(*) as total_vendas,
                    COALESCE(SUM(total), 0) as valor_total,
                    COALESCE(SUM(desconto), 0) as total_desconto,
                    COALESCE(SUM(CASE WHEN forma_pagamento = 'Dinheiro' THEN total ELSE 0 END), 0) as total_dinheiro,
                    COALESCE(SUM(CASE WHEN forma_pagamento = 'Cartão' THEN total ELSE 0 END), 0) as total_cartao,
                    COALESCE(SUM(CASE WHEN forma_pagamento = 'Pix' THEN total ELSE 0 END), 0) as total_pix,
                    COALESCE(SUM(CASE WHEN forma_pagamento = 'Crediario' THEN total ELSE 0 END), 0) as total_crediario
                FROM vendas
                WHERE data_venda BETWEEN ? AND ? AND status IN ('concluida', 'parcelada')
            """
            resultado = DatabaseUtils.executar_query(
                query, (data_inicio_db, data_fim_db)
            )

            if resultado:
                dados = resultado[0]
                return {
                    "total_vendas": dados[0],
                    "valor_total": float(dados[1]),
                    "total_desconto": float(dados[2]),
                    "total_dinheiro": float(dados[3]),
                    "total_cartao": float(dados[4]),
                    "total_pix": float(dados[5]),
                    "total_crediario": float(dados[6]),
                }

            return {}

        except Exception as e:
            raise ErroERP(f"Erro ao obter resumo do período: {e!s}") from e


class VendaEstoqueManager:
    """Gerenciador de estoque para operações de venda"""

    @staticmethod
    def atualizar_estoque_venda(produtos: list[dict[str, Any]]) -> bool:
        """Atualiza estoque após venda (diminui)"""
        try:
            for produto in produtos:
                query = "UPDATE produtos SET estoque = estoque - ? WHERE id = ?"
                DatabaseUtils.executar_query(
                    query, (produto["quantidade"], produto["id"])
                )
            return True
        except Exception as e:
            raise ErroERP(f"Erro ao atualizar estoque: {e!s}") from e

    @staticmethod
    def devolver_estoque_venda(venda_id: int) -> bool:
        """Devolve estoque de venda cancelada (aumenta)"""
        try:
            # Buscar itens da venda
            query_itens = (
                "SELECT produto_id, quantidade FROM itens_venda WHERE venda_id = ?"
            )
            itens = DatabaseUtils.executar_query(query_itens, (venda_id,))

            # Devolver cada item
            for item in itens:
                produto_id, quantidade = item
                query_estoque = "UPDATE produtos SET estoque = estoque + ? WHERE id = ?"
                DatabaseUtils.executar_query(query_estoque, (quantidade, produto_id))

            return True
        except Exception as e:
            raise ErroERP(f"Erro ao devolver estoque: {e!s}") from e

    @staticmethod
    def verificar_disponibilidade_produtos(
        produtos: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """Verifica se todos os produtos têm estoque suficiente"""
        try:
            for produto in produtos:
                query = "SELECT estoque FROM produtos WHERE id = ?"
                resultado = DatabaseUtils.executar_query(query, (produto["id"],))

                if not resultado:
                    return False, f"Produto ID {produto['id']} não encontrado"

                estoque_atual = resultado[0][0]
                if produto["quantidade"] > estoque_atual:
                    return (
                        False,
                        f"Estoque insuficiente para produto ID {produto['id']}",
                    )

            return True, ""
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VendaEstoqueManager.verificar_disponibilidade_produtos in utils/venda_utils.py",
            )
            return False, f"Erro ao verificar estoque: {e!s}"


class VendaUtils:
    """Classe principal de utilitários de venda - interface simplificada"""

    # Instâncias dos componentes
    validator = VendaValidator()
    calculator = VendaCalculator()
    repository = VendaRepository()
    estoque_manager = VendaEstoqueManager()

    @classmethod
    def filtrar_vendas(
        cls,
        data_inicio_str: str | None = None,
        data_fim_str: str | None = None,
        cliente_id: int | None = None,
    ) -> list[tuple]:
        """Filtra vendas - método principal para compatibilidade"""
        return cls.repository.buscar_vendas_com_filtros(
            data_inicio_str, data_fim_str, cliente_id
        )

    @classmethod
    def salvar_itens_venda(cls, venda_id: int, produtos: list[dict[str, Any]]) -> bool:
        """Salva itens da venda - método principal para compatibilidade"""
        return cls.repository.salvar_itens_venda(venda_id, produtos)

    @classmethod
    def devolver_estoque(cls, venda_id: int) -> bool:
        """Devolve estoque - método principal para compatibilidade"""
        return cls.estoque_manager.devolver_estoque_venda(venda_id)

    @classmethod
    def calcular_totais_venda(
        cls, produtos: list[dict[str, Any]], desconto: float = 0
    ) -> tuple[float, float]:
        """Calcula totais da venda - método principal para compatibilidade"""
        subtotal = cls.calculator.calcular_total_produtos(produtos)
        total = cls.calculator.aplicar_desconto(subtotal, desconto)
        return subtotal, total

    @classmethod
    def buscar_itens_venda_completo(cls, venda_id: int) -> list[tuple]:
        """Busca itens da venda - método principal para compatibilidade"""
        return cls.repository.buscar_itens_venda_detalhados(venda_id)

    @classmethod
    def obter_resumo_vendas_por_periodo(
        cls, data_inicio: str, data_fim: str
    ) -> dict[str, Any]:
        """Obtém resumo por período - método principal para compatibilidade"""
        return cls.repository.obter_resumo_periodo(data_inicio, data_fim)

    @classmethod
    def obter_produtos_mais_vendidos(cls, limite: int = 10) -> list[tuple]:
        """Obtém produtos mais vendidos"""
        query = """
            SELECT p.id, p.nome, SUM(iv.quantidade) as total_vendido
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            JOIN vendas v ON iv.venda_id = v.id
            WHERE v.status IN ('concluida', 'parcelada')
            GROUP BY p.id, p.nome
            ORDER BY total_vendido DESC
            LIMIT ?
        """
        return DatabaseUtils.executar_query(query, (limite,))

    # ========== MÉTODOS NOVOS DE CONVENIÊNCIA ==========

    @classmethod
    def validar_produto_venda(cls, produto) -> tuple[bool, str]:
        """Valida produto para venda"""
        return cls.validator.validar_produto_para_venda(produto)

    @classmethod
    def validar_quantidade(
        cls, quantidade: int, estoque: int, quantidade_existente: int = 0
    ) -> tuple[bool, str]:
        """Valida quantidade disponível"""
        return cls.validator.validar_quantidade_disponivel(
            quantidade, estoque, quantidade_existente
        )

    @classmethod
    def validar_finalizacao(cls, cliente, produtos: list[dict]) -> tuple[bool, str]:
        """Valida se venda pode ser finalizada"""
        return cls.validator.validar_venda_para_finalizacao(cliente, produtos)

    @classmethod
    def calcular_subtotal_item(cls, preco: float, quantidade: int) -> float:
        """Calcula subtotal de um item"""
        return cls.calculator.calcular_subtotal_produto(preco, quantidade)

    @classmethod
    def aplicar_desconto_total(cls, subtotal: float, desconto: float) -> float:
        """Aplica desconto ao total"""
        return cls.calculator.aplicar_desconto(subtotal, desconto)

    @classmethod
    def verificar_parcelas_pagas(cls, venda_id: int) -> bool:
        """Verifica se tem parcelas pagas"""
        return cls.repository.verificar_parcelas_pagas(venda_id)

    @classmethod
    def atualizar_estoque_produtos(cls, produtos: list[dict[str, Any]]) -> bool:
        """Atualiza estoque dos produtos"""
        return cls.estoque_manager.atualizar_estoque_venda(produtos)

    @classmethod
    def verificar_estoque_disponivel(
        cls, produtos: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        """Verifica estoque disponível"""
        return cls.estoque_manager.verificar_disponibilidade_produtos(produtos)
