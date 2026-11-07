"""
Modelo de Venda - Versão Refatorada
Simplificado e integrado com VendaUtils refatorado
"""

from datetime import datetime
from typing import Any, Optional

from mainerp.core.exceptions import ErroERP
from mainerp.data.database_utils import DatabaseUtils
from mainerp.data.models.base_model import BaseModel
from mainerp.data.money import de_centavos, para_centavos


class VendaStatus:
    """Enum para status de venda"""

    PENDENTE = "pendente"
    CONCLUIDA = "concluida"
    PARCELADA = "parcelada"
    CANCELADA = "cancelada"


class FormaPagamento:
    """Enum para formas de pagamento"""

    DINHEIRO = "Dinheiro"
    CARTAO = "Cartão"
    PIX = "Pix"
    CREDIARIO = "Crediario"


class Venda(BaseModel):
    """Modelo de Venda com lógica simplificada"""

    TABLE_NAME = "vendas"

    def __init__(
        self,
        id=None,
        cliente_id=None,
        data_venda=None,
        total=0.0,
        forma_pagamento="",
        status=VendaStatus.PENDENTE,
        parcelas=1,
        desconto=0.0,
        observacao="",
        valor_entrada=0.0,
        valor_financiado=None,
    ):
        self.id = id
        self.cliente_id = cliente_id
        self.data_venda = data_venda or datetime.now().date()
        self.total = float(total) if total else 0.0
        self.forma_pagamento = forma_pagamento
        self.status = status
        self.parcelas = int(parcelas) if parcelas else 1
        self.desconto = float(desconto) if desconto else 0.0
        self.observacao = observacao or ""
        self.valor_entrada = float(valor_entrada) if valor_entrada else 0.0
        self.valor_financiado = (
            float(valor_financiado) if valor_financiado is not None else self.total
        )

    def salvar(self) -> int:
        """Salva venda no banco de dados"""
        try:
            if self.id:
                return self._atualizar()
            else:
                return self._inserir()
        except Exception as e:
            raise ErroERP(f"Erro ao salvar venda: {e!s}") from e

    def _inserir(self) -> int:
        """Insere nova venda"""
        query = """
            INSERT INTO vendas
            (cliente_id, data_venda, total, forma_pagamento, status, parcelas,
             desconto, observacao, valor_entrada, valor_financiado, total_centavos,
             desconto_centavos, valor_entrada_centavos, valor_financiado_centavos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            self.cliente_id,
            self.data_venda,
            self.total,
            self.forma_pagamento,
            self.status,
            self.parcelas,
            self.desconto,
            self.observacao,
            self.valor_entrada,
            self.valor_financiado,
            para_centavos(self.total),
            para_centavos(self.desconto),
            para_centavos(self.valor_entrada),
            para_centavos(self.valor_financiado),
        )

        venda_id = DatabaseUtils.executar_query(query, params)
        if not isinstance(venda_id, int):
            raise RuntimeError("A inserção da venda não retornou um ID.")
        self.id = venda_id
        return venda_id

    def _atualizar(self) -> int:
        """Atualiza venda existente"""
        venda_id = self._obter_id()
        query = """
            UPDATE vendas
            SET cliente_id=?, data_venda=?, total=?, forma_pagamento=?,
                status=?, parcelas=?, desconto=?, observacao=?, valor_entrada=?,
                valor_financiado=?, total_centavos=?, desconto_centavos=?,
                valor_entrada_centavos=?, valor_financiado_centavos=?
            WHERE id=?
        """
        params = (
            self.cliente_id,
            self.data_venda,
            self.total,
            self.forma_pagamento,
            self.status,
            self.parcelas,
            self.desconto,
            self.observacao,
            self.valor_entrada,
            self.valor_financiado,
            para_centavos(self.total),
            para_centavos(self.desconto),
            para_centavos(self.valor_entrada),
            para_centavos(self.valor_financiado),
            venda_id,
        )

        DatabaseUtils.executar_query(query, params)
        return venda_id

    def _obter_id(self) -> int:
        if self.id is None:
            raise ValueError("A venda ainda não possui ID.")
        return self.id

    def excluir(self) -> bool:
        """Exclui venda e relacionamentos"""
        if not self.id:
            raise ValueError("Não é possível excluir venda sem ID")

        try:
            # Excluir itens da venda
            DatabaseUtils.executar_query(
                "DELETE FROM itens_venda WHERE venda_id = ?", (self.id,)
            )

            # Excluir duplicatas
            DatabaseUtils.executar_query(
                "DELETE FROM duplicatas WHERE venda_id = ?", (self.id,)
            )

            # Excluir duplicatas pagas
            DatabaseUtils.executar_query(
                "DELETE FROM duplicatas_pagas WHERE venda_id = ?", (self.id,)
            )

            # Excluir a venda
            DatabaseUtils.executar_query("DELETE FROM vendas WHERE id = ?", (self.id,))

            return True

        except Exception as e:
            raise ErroERP(f"Erro ao excluir venda: {e!s}") from e

    def cancelar(self) -> bool:
        """Cancela venda e devolve estoque"""
        try:
            # Importar aqui para evitar import circular
            from mainerp.domain.utils.venda_utils import VendaUtils

            # Devolver estoque
            VendaUtils.devolver_estoque(self._obter_id())

            # Atualizar status
            self.status = VendaStatus.CANCELADA
            self.salvar()

            return True

        except Exception as e:
            raise ErroERP(f"Erro ao cancelar venda: {e!s}") from e

    # ========== MÉTODOS DE CONSULTA ==========

    def get_itens(self) -> list[tuple]:
        """Obtém itens da venda"""
        from mainerp.domain.utils.venda_utils import VendaUtils

        return VendaUtils.buscar_itens_venda_completo(self._obter_id())

    def get_parcelas(self) -> list[tuple]:
        """Obtém parcelas da venda"""
        query = """
            SELECT id, venda_id, cliente_id, numero_parcela,
                   valor_parcela_centavos, data_vencimento, data_pagamento, status
            FROM duplicatas
            WHERE venda_id = ?
            ORDER BY numero_parcela
        """
        return [
            (*parcela[:4], float(de_centavos(parcela[4])), *parcela[5:])
            for parcela in DatabaseUtils.executar_query(query, (self._obter_id(),))
        ]

    def get_cliente(self):
        """Obtém cliente da venda"""
        if not self.cliente_id:
            return None

        try:
            from mainerp.data.models.cliente import Cliente

            return Cliente.buscar_por_id(self.cliente_id)
        except ImportError:
            # Fallback se modelo Cliente não estiver disponível
            query = "SELECT * FROM clientes WHERE id = ?"
            resultado = DatabaseUtils.executar_query(query, (self.cliente_id,))
            return resultado[0] if resultado else None

    def tem_parcelas_pagas(self) -> bool:
        """Verifica se tem parcelas pagas"""
        from mainerp.domain.utils.venda_utils import VendaUtils

        return VendaUtils.verificar_parcelas_pagas(self._obter_id())

    def pode_ser_excluida(self) -> tuple[bool, str]:
        """Verifica se venda pode ser excluída"""
        if self.tem_parcelas_pagas():
            return False, "Venda possui parcelas pagas e não pode ser excluída"

        if self.status == VendaStatus.CANCELADA:
            return False, "Venda já está cancelada"

        return True, ""

    def calcular_total_com_desconto(self) -> float:
        """Calcula total considerando desconto"""
        from mainerp.domain.utils.venda_utils import VendaUtils

        return VendaUtils.aplicar_desconto_total(
            self.total + self.desconto, self.desconto
        )

    # ========== MÉTODOS DE CLASSE ==========

    @classmethod
    def buscar_por_id(cls, venda_id: int) -> Optional["Venda"]:
        """Busca venda por ID"""
        if not venda_id:
            return None

        query = f"{cls._SELECT_CAMPOS} WHERE id = ?"
        resultado = DatabaseUtils.executar_query(query, (venda_id,))

        if resultado:
            return cls._from_row(resultado[0])

        return None

    @classmethod
    def buscar_todas(
        cls, limite: int | None = None, apenas_ativas: bool = True
    ) -> list["Venda"]:
        """Busca todas as vendas"""
        query = cls._SELECT_CAMPOS
        params = []

        if apenas_ativas:
            query += " WHERE status != ?"
            params.append(VendaStatus.CANCELADA)

        query += " ORDER BY data_venda DESC, id DESC"

        if limite:
            query += " LIMIT ?"
            params.append(limite)

        resultados = DatabaseUtils.executar_query(query, params)

        vendas = []
        for dados in resultados:
            vendas.append(cls._from_row(dados))

        return vendas

    @classmethod
    def buscar_por_cliente(cls, cliente_id: int) -> list["Venda"]:
        """Busca vendas por cliente"""
        query = """
            {campos}
            WHERE cliente_id = ? AND status != ?
            ORDER BY data_venda DESC
        """.format(campos=cls._SELECT_CAMPOS)
        resultados = DatabaseUtils.executar_query(
            query, (cliente_id, VendaStatus.CANCELADA)
        )

        vendas = []
        for dados in resultados:
            vendas.append(cls._from_row(dados))

        return vendas

    _SELECT_CAMPOS = """
        SELECT id, cliente_id, data_venda, total_centavos, forma_pagamento,
               status, parcelas, desconto_centavos, observacao,
               valor_entrada_centavos, valor_financiado_centavos
        FROM vendas
    """

    @classmethod
    def _from_row(cls, dados) -> "Venda":
        return cls(
            id=dados[0],
            cliente_id=dados[1],
            data_venda=dados[2],
            total=float(de_centavos(dados[3])),
            forma_pagamento=dados[4],
            status=dados[5],
            parcelas=dados[6],
            desconto=float(de_centavos(dados[7])),
            observacao=dados[8],
            valor_entrada=float(de_centavos(dados[9])),
            valor_financiado=float(de_centavos(dados[10])),
        )

    @classmethod
    def buscar_por_periodo(
        cls, data_inicio: str, data_fim: str, cliente_id: int | None = None
    ) -> list[tuple]:
        """Busca vendas por período (retorna tuplas para compatibilidade)"""
        from mainerp.domain.utils.venda_utils import VendaUtils

        return VendaUtils.filtrar_vendas(data_inicio, data_fim, cliente_id)

    @classmethod
    def obter_estatisticas_periodo(
        cls, data_inicio: str, data_fim: str
    ) -> dict[str, Any]:
        """Obtém estatísticas de vendas por período"""
        from mainerp.domain.utils.venda_utils import VendaUtils

        return VendaUtils.obter_resumo_vendas_por_periodo(data_inicio, data_fim)

    @classmethod
    def criar_venda_completa(
        cls,
        cliente_id: int,
        produtos: list[dict[str, Any]],
        forma_pagamento: str,
        parcelas: int = 1,
        desconto: float = 0.0,
        observacao: str = "",
    ) -> "Venda":
        """Cria venda completa com validações e salvamento de itens"""
        try:
            # Importar aqui para evitar import circular
            from mainerp.domain.utils.venda_utils import VendaUtils

            # Validar dados
            valido, erro = VendaUtils.validar_finalizacao(
                {"id": cliente_id} if cliente_id else None, produtos
            )
            if not valido:
                raise ValueError(erro)

            # Verificar estoque
            estoque_ok, erro_estoque = VendaUtils.verificar_estoque_disponivel(produtos)
            if not estoque_ok:
                raise ValueError(erro_estoque)

            # Calcular totais
            _subtotal, total = VendaUtils.calcular_totais_venda(produtos, desconto)

            # Determinar status
            status = VendaStatus.CONCLUIDA
            if forma_pagamento == FormaPagamento.CREDIARIO:
                status = VendaStatus.PARCELADA

            # Criar venda
            venda = cls(
                cliente_id=cliente_id,
                total=total,
                forma_pagamento=forma_pagamento,
                status=status,
                parcelas=parcelas,
                desconto=desconto,
                observacao=observacao,
            )

            # Salvar venda
            venda_id = venda.salvar()

            # Salvar itens
            VendaUtils.salvar_itens_venda(venda_id, produtos)

            # Atualizar estoque
            VendaUtils.atualizar_estoque_produtos(produtos)

            return venda

        except Exception as e:
            raise ErroERP(f"Erro ao criar venda: {e!s}") from e

    # ========== MÉTODOS AUXILIARES ==========

    def to_dict(self) -> dict[str, Any]:
        """Converte venda para dicionário"""
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "data_venda": self.data_venda.isoformat()
            if hasattr(self.data_venda, "isoformat")
            else str(self.data_venda),
            "total": self.total,
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "parcelas": self.parcelas,
            "desconto": self.desconto,
            "observacao": self.observacao,
        }

    def __str__(self) -> str:
        return f"Venda {self.id} - Cliente {self.cliente_id} - R$ {self.total:.2f}"

    def __repr__(self) -> str:
        return f"Venda(id={self.id}, cliente_id={self.cliente_id}, total={self.total}, status='{self.status}')"
