"""Componentes de CondicionalView."""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QTableWidgetItem,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.condicional import Condicional
from mainerp.domain.utils.helpers import (
    formatar_moeda,
    validar_data,
)
from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.styles import cores_ativas
from mainerp.ui.table_items import NumericTableWidgetItem

__all__ = ["_CondicionalViewFilters"]


class _CondicionalViewFilters(ComponentMixin):
    def _carregar_condicionais(self):
        """Carrega condicionais na tabela com tratamento de erros"""
        try:
            # Buscar todas as condicionais
            self.dados = Condicional.buscar_todas()
            self.dados.sort(
                key=lambda condicional: condicional[0], reverse=True
            )  # Ordem decrescente por ID

            self._filtrar_condicionais()
            self._atualizar_label_info()

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in CondicionalView._carregar_condicionais in views/condicional_view.py",
            )
            self._mostrar_erro("Erro ao carregar condicionais", str(e))

    def _filtrar_condicionais(self):
        """CORREÇÃO: Filtra condicionais por data, status e cliente - sempre usa dados originais"""
        data_inicio_str = self.data_inicio.text().strip()
        data_fim_str = self.data_fim.text().strip()
        cliente_nome = self.busca_cliente.text().strip()
        status_selecionado = self.combo_status.currentText()

        # Validação visual das datas
        if data_inicio_str and not validar_data(data_inicio_str):
            self._marcar_campo_erro(self.data_inicio)
            return
        else:
            self._limpar_campo_erro(self.data_inicio)

        if data_fim_str and not validar_data(data_fim_str):
            self._marcar_campo_erro(self.data_fim)
            return
        else:
            self._limpar_campo_erro(self.data_fim)

        # CORREÇÃO: Aplicar filtros sempre nos dados originais
        dados_filtrados = self.dados.copy()  # Partir sempre dos dados originais

        # Filtro por status
        if status_selecionado != "Todos":
            status_map = {
                "Ativas": "ativa",
                "Convertidas": "convertida",
                "Devolvidas": "devolvida",
            }
            status_filtro = status_map.get(status_selecionado, "")
            dados_filtrados = [
                c for c in dados_filtrados if str(c[4]).lower() == status_filtro
            ]

        # Filtro por data
        if data_inicio_str and data_fim_str:
            try:
                data_ini = self._converter_data(data_inicio_str)
                data_fim = self._converter_data(data_fim_str)

                dados_filtrados = [
                    c
                    for c in dados_filtrados
                    if (data_condicional := self._parse_data(c[2])) is not None
                    and data_ini is not None
                    and data_fim is not None
                    and data_ini <= data_condicional <= data_fim
                ]
            except ValueError:
                pass

        # Filtro por nome do cliente na busca local - CORREÇÃO AQUI
        if cliente_nome:
            dados_filtrados = [
                c
                for c in dados_filtrados
                if cliente_nome.lower()
                in (
                    str(c[7]) if len(c) > 7 and c[7] else ""
                ).lower()  # ✅ Índice correto [7]
            ]

        self.tabela_condicionais.setRowCount(len(dados_filtrados))
        self._preencher_tabela_condicionais(dados_filtrados)
        self._atualizar_label_info()

    def _preencher_tabela_condicionais(self, condicionais):
        """CORREÇÃO: Preenche a tabela com ordenação numérica correta"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_condicionais.setSortingEnabled(False)

        for row, condicional in enumerate(condicionais):
            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(str(condicional[0]))
            item_id.setData(
                Qt.ItemDataRole.UserRole, condicional[0]
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_condicionais.setItem(row, 0, item_id)

            # Cliente
            cliente_nome = (
                str(condicional[7])
                if len(condicional) > 7 and condicional[7]
                else "Cliente não informado"
            )
            self.tabela_condicionais.setItem(row, 1, QTableWidgetItem(cliente_nome))

            # Data
            data = condicional[2]
            if hasattr(data, "strftime"):
                data_str = data.strftime("%d/%m/%Y")
            else:
                try:
                    data_obj = datetime.strptime(str(data), "%Y-%m-%d")
                    data_str = data_obj.strftime("%d/%m/%Y")
                except ValueError:
                    data_str = str(data)
            data_item = QTableWidgetItem(data_str)
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_condicionais.setItem(row, 2, data_item)

            # Data prevista devolução
            data_prevista = condicional[3]
            if data_prevista:
                if hasattr(data_prevista, "strftime"):
                    data_prevista_str = data_prevista.strftime("%d/%m/%Y")
                else:
                    try:
                        data_obj = datetime.strptime(str(data_prevista), "%Y-%m-%d")
                        data_prevista_str = data_obj.strftime("%d/%m/%Y")
                    except ValueError:
                        data_prevista_str = str(data_prevista)
            else:
                data_prevista_str = "Não definida"
            dp_item = QTableWidgetItem(data_prevista_str)
            dp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_condicionais.setItem(row, 3, dp_item)

            # CORREÇÃO: Quantidade de itens usando NumericTableWidgetItem
            itens_count = condicional[8] if len(condicional) > 8 else 0
            itens_item = NumericTableWidgetItem(str(itens_count))
            itens_item.setData(Qt.ItemDataRole.UserRole, itens_count)  # Valor numérico
            itens_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_condicionais.setItem(row, 4, itens_item)

            # CORREÇÃO: Desconto usando NumericTableWidgetItem com valor numérico
            desconto_valor = (
                float(condicional[6]) if len(condicional) > 6 and condicional[6] else 0
            )
            desconto_item = NumericTableWidgetItem(formatar_moeda(desconto_valor))
            desconto_item.setData(
                Qt.ItemDataRole.UserRole, desconto_valor
            )  # Valor numérico para ordenação
            desconto_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_condicionais.setItem(row, 5, desconto_item)

            # CORREÇÃO: Valor total usando NumericTableWidgetItem com valor numérico
            condicional_obj = Condicional.buscar_por_id(condicional[0])
            if condicional_obj:
                total = condicional_obj.calcular_total()  # Já aplica o desconto
                total_item = NumericTableWidgetItem(formatar_moeda(total))
                total_item.setData(
                    Qt.ItemDataRole.UserRole, total
                )  # Valor numérico para ordenação
            else:
                total_item = NumericTableWidgetItem(formatar_moeda(0))
                total_item.setData(Qt.ItemDataRole.UserRole, 0)
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_condicionais.setItem(row, 6, total_item)

            # Aplicar cores baseadas no status
            self._aplicar_estilo_linha(row, condicional_obj)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_condicionais.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_condicionais.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _aplicar_estilo_linha(self, row, condicional):
        """Aplica cores específicas baseadas no status da condicional"""
        if not condicional:
            return

        # Para condicionais devolvidas - linha toda laranja
        if condicional.status == "devolvida":
            cor_laranja = QColor(cores_ativas().warning_text)  # Laranja
            for col in range(self.tabela_condicionais.columnCount()):
                item = self.tabela_condicionais.item(row, col)
                if item:
                    item.setForeground(cor_laranja)

        # Para condicionais convertidas - linha toda verde
        elif condicional.status == "convertida":
            cor_verde = QColor(cores_ativas().success_text)  # Verde
            for col in range(self.tabela_condicionais.columnCount()):
                item = self.tabela_condicionais.item(row, col)
                if item:
                    item.setForeground(cor_verde)

        # Para condicionais ativas e vencidas - APENAS a coluna de data prevista em vermelho
        elif condicional.status == "ativa" and condicional.esta_vencida():
            cor_vermelha = QColor(cores_ativas().danger_text)  # Vermelho

            # Aplicar vermelho apenas na coluna 3 (Prev. Devolução)
            item_data_prevista = self.tabela_condicionais.item(row, 3)
            if item_data_prevista:
                item_data_prevista.setForeground(cor_vermelha)
                # Opcional: deixar o texto em negrito para maior destaque
                font = item_data_prevista.font()
                font.setBold(True)
                item_data_prevista.setFont(font)

    def _atualizar_label_info(self):
        """Atualiza o label informativo baseado nos filtros"""
        total_condicionais = self.tabela_condicionais.rowCount()
        data_inicio = self.data_inicio.text().strip()
        data_fim = self.data_fim.text().strip()
        cliente = self.busca_cliente.text().strip()
        status = self.combo_status.currentText()

        info_parts = [f"({total_condicionais} condicionais"]

        if status != "Todos":
            info_parts.append(f"status: {status.lower()}")

        if data_inicio or data_fim:
            if data_inicio and data_fim:
                info_parts.append(f"período: {data_inicio} a {data_fim}")
            elif data_inicio:
                info_parts.append(f"a partir de {data_inicio}")
            elif data_fim:
                info_parts.append(f"até {data_fim}")

        if cliente:
            info_parts.append(f"cliente: {cliente}")

        self.label_info.setText(" - ".join(info_parts) + ")")

    def _converter_data(self, data_str):
        """Converte string DD/MM/AAAA para objeto date"""
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            return None

    def _parse_data(self, val):
        """Parse de data genérico para diferentes formatos"""
        if hasattr(val, "strftime"):
            return val.date() if hasattr(val, "date") else val
        try:
            return datetime.strptime(str(val), "%Y-%m-%d").date()
        except ValueError:
            return None

    def _marcar_campo_erro(self, campo):
        """Marca campo com erro visual"""
        campo.setProperty("class", "error")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_campo_erro(self, campo):
        """Remove marcação de erro do campo"""
        campo.setProperty("class", "")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_filtros(self):
        """Limpa todos os filtros e recarrega condicionais"""
        self.data_inicio.setText(
            (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        )
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.busca_cliente.clear()
        self.combo_status.setCurrentText("Todos")
        self._limpar_campo_erro(self.data_inicio)
        self._limpar_campo_erro(self.data_fim)
        self._carregar_condicionais()
