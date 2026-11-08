"""Componentes de RecebimentoView."""

import logging
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QMessageBox,
    QTableWidgetItem,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.duplicata import Duplicata
from mainerp.domain.utils.helpers import (
    formatar_data,
    formatar_moeda,
    validar_data,
)
from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.styles import cores_ativas
from mainerp.ui.table_items import NumericTableWidgetItem

logger = logging.getLogger(__name__)


__all__ = ["_RecebimentoViewFilters"]


class _RecebimentoViewFilters(ComponentMixin):
    def _carregar_duplicatas(self):
        """Carrega duplicatas do banco - VERSÃO OTIMIZADA"""
        try:
            # Mostrar estado de carregamento
            self.label_info.setText("(Carregando...)")

            self.todas_duplicatas = Duplicata.buscar_para_recebimento()

            # Inicializar cache de parcelas
            self._inicializar_cache_parcelas()

            # Filtrar e exibir
            self._filtrar_duplicatas_otimizado()

        except Exception as e:
            self.label_info.setText("(Erro ao carregar)")
            QMessageBox.critical(None, "Erro", f"Erro ao carregar duplicatas: {e!s}")

    def _inicializar_cache_parcelas(self):
        """Inicializa cache de total de parcelas por venda"""
        self._parcelas_cache = {}

        # Coletar IDs de vendas únicas
        venda_ids = set()
        for dup in self.todas_duplicatas:
            venda_id = dup[2]  # venda_id está na posição 2
            if venda_id:
                venda_ids.add(venda_id)

        if not venda_ids:
            return

        try:
            for venda_id in venda_ids:
                total = Duplicata.contar_parcelas_por_venda(venda_id)
                self._parcelas_cache[venda_id] = total if total > 0 else 1

        except Exception:
            logger.exception("Erro ao inicializar cache de parcelas")
            # Se houver erro, usa fallback
            for venda_id in venda_ids:
                self._parcelas_cache[venda_id] = 1

    def _filtrar_duplicatas_otimizado(self):
        """Filtra duplicatas - VERSÃO OTIMIZADA"""
        if not hasattr(self, "todas_duplicatas") or not self.todas_duplicatas:
            self.tabela_duplicatas.setRowCount(0)
            self.label_info.setText("(0 duplicatas)")
            return

        status_filtro = self._get_status_selecionado()
        data_inicio_str = self.data_inicio.text().strip()
        data_fim_str = self.data_fim.text().strip()
        cliente_nome_busca = self.busca_cliente.text().strip().lower()

        # Validação rápida de datas
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

        # Converter datas uma vez
        data_inicio = None
        data_fim = None
        hoje = datetime.now().date()

        if data_inicio_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
            except (ValueError, TypeError):
                pass

        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()
            except (ValueError, TypeError):
                pass

        duplicatas_filtradas = []

        # Filtro otimizado em uma passada
        for dup in self.todas_duplicatas:
            # Acesso direto por índice
            status = dup[7]  # status
            cliente_nome = dup[8]  # cliente_nome
            data_vencimento = dup[5]  # data_vencimento
            data_pagamento = dup[6]  # data_pagamento

            # 1. Filtro de status (mais rápido primeiro)
            if not self._validar_status_filtro(
                status_filtro, status, data_vencimento, hoje
            ):
                continue

            # 2. Filtro por nome do cliente
            if cliente_nome_busca:
                nome_atual = str(cliente_nome).lower() if cliente_nome else ""
                if cliente_nome_busca not in nome_atual:
                    continue

            # 3. Filtro de data
            if not self._validar_data_filtro(
                status, data_vencimento, data_pagamento, data_inicio, data_fim
            ):
                continue

            duplicatas_filtradas.append(dup)

        self.duplicatas_filtradas = duplicatas_filtradas
        self._exibir_duplicatas_otimizado(duplicatas_filtradas)
        self._atualizar_label_info()

    def _validar_status_filtro(self, status_filtro, status, data_vencimento, hoje):
        """Validação de status otimizada"""
        if status_filtro == "Abertas":
            return status == "aberto"
        elif status_filtro == "Vencidas":
            if status != "aberto":
                return False
            if not data_vencimento:
                return False
            try:
                data_venc = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
                return data_venc < hoje
            except (ValueError, TypeError):
                return False
        elif status_filtro == "Pagas":
            return status == "pago"
        elif status_filtro == "Todas":
            return True
        return False

    def _validar_data_filtro(
        self, status, data_vencimento, data_pagamento, data_inicio, data_fim
    ):
        """Validação de data otimizada"""
        data_referencia = data_vencimento if status == "aberto" else data_pagamento

        if not data_referencia:
            return not data_inicio and not data_fim

        try:
            data_ref = datetime.strptime(data_referencia, "%Y-%m-%d").date()

            if data_inicio and data_ref < data_inicio:
                return False

            return not (data_fim and data_ref > data_fim)
        except (ValueError, TypeError):
            return False

    def _exibir_duplicatas_otimizado(self, duplicatas):
        """Exibe duplicatas na tabela - VERSÃO OTIMIZADA"""
        # Desabilitar ordenação durante preenchimento
        self.tabela_duplicatas.setSortingEnabled(False)
        self.tabela_duplicatas.setRowCount(len(duplicatas))

        for row, dup in enumerate(duplicatas):
            self._preencher_linha_tabela_otimizado(row, dup)

        # Reativar ordenação
        self.tabela_duplicatas.setSortingEnabled(True)

        # Selecionar primeira linha se houver dados
        if duplicatas and self.tabela_duplicatas.rowCount() > 0:
            self.tabela_duplicatas.selectRow(0)

    def _preencher_linha_tabela_otimizado(self, row, dup):
        """Preenche uma linha da tabela - VERSÃO OTIMIZADA"""
        # Extrair dados com índices fixos
        id_dup = dup[0]  # id
        cliente_nome = dup[8]  # cliente_nome
        venda_id = dup[2]  # venda_id
        numero_parcela = dup[3]  # numero_parcela
        valor = dup[4]  # valor
        data_vencimento = dup[5]  # data_vencimento
        data_pagamento = dup[6]  # data_pagamento
        status = dup[7]  # status
        forma_pagamento = dup[11]  # forma_pagamento (apenas para pagas)

        # Obter total de parcelas do cache
        total_parcelas = self._parcelas_cache.get(venda_id, 1)
        parcela_formatada = f"{numero_parcela}/{total_parcelas}"

        # 1. ID - usar NumericTableWidgetItem para ordenação numérica correta
        item_id = NumericTableWidgetItem(str(id_dup))
        item_id.setData(Qt.ItemDataRole.UserRole, id_dup)  # Armazenar valor numérico
        item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabela_duplicatas.setItem(row, 0, item_id)

        # 2. Cliente
        cliente_item = QTableWidgetItem(str(cliente_nome) if cliente_nome else "N/A")
        self.tabela_duplicatas.setItem(row, 1, cliente_item)

        # 3. Venda ID - também usar NumericTableWidgetItem
        venda_item = NumericTableWidgetItem(str(venda_id))
        venda_item.setData(Qt.ItemDataRole.UserRole, venda_id)
        venda_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabela_duplicatas.setItem(row, 3, venda_item)

        # 4. Parcela
        parcela_item = QTableWidgetItem(parcela_formatada)
        parcela_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabela_duplicatas.setItem(row, 4, parcela_item)

        # 5. Valor - usar NumericTableWidgetItem para ordenação numérica
        valor_num = float(valor) if valor else 0
        valor_item = NumericTableWidgetItem(formatar_moeda(valor_num))
        valor_item.setData(Qt.ItemDataRole.UserRole, valor_num)
        valor_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.tabela_duplicatas.setItem(row, 5, valor_item)

        # 6. Status (coluna 2)
        status_text = status.capitalize()
        if status == "pago" and forma_pagamento:
            status_text = f"{status_text} ({forma_pagamento})"

        status_item = QTableWidgetItem(status_text)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if status == "pago":
            status_item.setForeground(QBrush(QColor(cores_ativas().success_text)))
        elif status == "aberto":
            status_item.setForeground(QBrush(QColor(cores_ativas().warning_text)))

        self.tabela_duplicatas.setItem(row, 2, status_item)

        # 7. Vencimento (coluna 6)
        vencimento = (
            formatar_data(data_vencimento, "%Y-%m-%d", "%d/%m/%Y")
            if data_vencimento
            else "N/A"
        )
        venc_item = QTableWidgetItem(vencimento)
        venc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Aplicar cor se vencida
        if status == "aberto" and data_vencimento:
            try:
                data_venc = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
                if data_venc < datetime.now().date():
                    venc_item.setForeground(QBrush(QColor(cores_ativas().danger_text)))
                    font = venc_item.font()
                    font.setBold(True)
                    venc_item.setFont(font)
            except (ValueError, TypeError):
                pass

        self.tabela_duplicatas.setItem(row, 6, venc_item)

        # 8. Pagamento (coluna 7)
        pagamento = (
            formatar_data(data_pagamento, "%Y-%m-%d", "%d/%m/%Y")
            if data_pagamento
            else "N/A"
        )
        pag_item = QTableWidgetItem(pagamento)
        pag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabela_duplicatas.setItem(row, 7, pag_item)

    def _atualizar_label_info(self):
        """Atualiza label informativo"""
        total_duplicatas = len(self.duplicatas_filtradas)
        status = self._get_status_selecionado()
        cliente = self.busca_cliente.text().strip()
        data_inicio = self.data_inicio.text().strip()
        data_fim = self.data_fim.text().strip()

        info_parts = [f"({total_duplicatas} duplicatas"]

        if status != "Todas":
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

    def _get_status_selecionado(self):
        """Retorna status selecionado no ComboBox"""
        return self.combo_status.currentText()

    def _limpar_filtros(self):
        """Limpa todos os filtros"""
        self.combo_status.setCurrentText("Abertas")
        self.data_inicio.clear()
        self.data_fim.clear()
        self.busca_cliente.clear()
        self._limpar_campo_erro(self.data_inicio)
        self._limpar_campo_erro(self.data_fim)
        self.cliente_filtro = None
        self._filtrar_duplicatas_otimizado()

    def _get_duplicata_selecionada(self):
        """Retorna duplicata selecionada"""
        row = self.tabela_duplicatas.currentRow()
        if row == -1:
            return None

        try:
            item = self.tabela_duplicatas.item(row, 0)
            if item is None:
                return None
            duplicata_id = int(item.text())
            for dup in self.duplicatas_filtradas:
                if dup[0] == duplicata_id:
                    return dup
            return None
        except (IndexError, RuntimeError, TypeError, ValueError):
            registrar_excecao(
                __name__,
                "Exception handled in RecebimentoView._get_duplicata_selecionada in views/recebimento_view.py",
            )
            return None
