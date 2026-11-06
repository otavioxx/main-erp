# mixins/table_scroll_mixin.py
"""
Mixin para controle de scroll em tabelas - converte scroll em navegação linha por linha
"""

from PyQt6.QtCore import QEvent, QTimer
from PyQt6.QtWidgets import QTableWidget


class TableScrollNavigationMixin:
    """
    Mixin que converte eventos de scroll do mouse em navegação linha por linha.

    Uso:
        class MinhaView(TableScrollNavigationMixin, QWidget):
            def __init__(self):
                super().__init__()
                self.init_ui()
                # Após criar a tabela, ative o mixin:
                self.setup_scroll_navigation(self.minha_tabela)
    """

    def setup_scroll_navigation(self, tabela: QTableWidget,
                                scroll_sensibilidade: int = 1,
                                auto_select_first: bool = True):
        """
        Configura a navegação por scroll na tabela.

        Args:
            tabela: A QTableWidget a ser configurada
            scroll_sensibilidade: Quantas linhas pular por evento de scroll (padrão: 1)
            auto_select_first: Se deve selecionar automaticamente a primeira linha quando não há seleção
        """
        self._scroll_table = tabela
        self._scroll_sensibilidade = scroll_sensibilidade
        self._scroll_auto_select = auto_select_first
        self._scroll_acumulado = 0
        self._scroll_threshold = 120  # Threshold padrão para um "click" de scroll

        # Timer para debounce de scrolls rápidos
        self._scroll_timer = QTimer()
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(50)  # 50ms de debounce

        # Instalar o event filter
        self._scroll_table.viewport().installEventFilter(self)

        # Configurar a tabela para melhor experiência
        self._scroll_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerItem)

    def eventFilter(self, obj, event):
        """
        Filtra eventos para capturar wheel events na tabela.
        """
        # Verificar se é evento de wheel na viewport da nossa tabela
        if (hasattr(self, '_scroll_table') and
            obj == self._scroll_table.viewport() and
            event.type() == QEvent.Type.Wheel):
            return self._handle_wheel_event(event)

        # Passar para o handler padrão
        return super().eventFilter(obj, event) if hasattr(super(), 'eventFilter') else False

    def _handle_wheel_event(self, event):
        """
        Processa o evento de scroll do mouse.

        Args:
            event: QWheelEvent

        Returns:
            bool: True para bloquear o scroll padrão, False para permitir
        """
        # Verificar se a tabela está vazia
        if self._scroll_table.rowCount() == 0:
            return True  # Bloquear scroll em tabela vazia

        # Obter a linha atual
        linha_atual = self._scroll_table.currentRow()

        # Se não há linha selecionada e auto_select está ativo
        if linha_atual == -1 and self._scroll_auto_select:
            self._selecionar_linha(0)
            return True

        # Se não há linha selecionada e auto_select está desativado
        if linha_atual == -1:
            return False  # Permitir scroll normal

        # Obter a direção e magnitude do scroll
        delta = event.angleDelta().y()

        # Acumular o delta para suavizar scrolls rápidos
        self._scroll_acumulado += delta

        # Verificar se atingiu o threshold para mudar de linha
        if abs(self._scroll_acumulado) >= self._scroll_threshold:
            # Calcular quantas linhas mover
            linhas_para_mover = (abs(self._scroll_acumulado) // self._scroll_threshold) * self._scroll_sensibilidade

            if self._scroll_acumulado > 0:
                # Scroll para cima (linha anterior)
                self._navegar_linhas(-linhas_para_mover)
            else:
                # Scroll para baixo (próxima linha)
                self._navegar_linhas(linhas_para_mover)

            # Resetar acumulador
            self._scroll_acumulado = 0

        # Sempre bloquear o scroll padrão
        return True

    def _navegar_linhas(self, delta: int):
        """
        Navega pelo número especificado de linhas, mas só faz o viewport rolar
        quando a seleção estiver no limite visível (primeira/última visível).
        """
        linha_atual = self._scroll_table.currentRow()
        total_linhas = self._scroll_table.rowCount()

        if linha_atual == -1 or total_linhas == 0:
            return

        # determinar linha alvo e direção
        alvo = max(0, min(linha_atual + delta, total_linhas - 1))
        if alvo == linha_atual:
            return

        step = 1 if alvo > linha_atual else -1
        atual = linha_atual

        # mover 1 por 1 para respeitar o comportamento "scroll só quando estiver no limite visível"
        while atual != alvo:
            proxima = atual + step

            # obter limites visíveis
            primeira_visivel = self._scroll_table.rowAt(0)
            ultima_visivel = self._scroll_table.rowAt(self._scroll_table.viewport().height() - 1)

            if primeira_visivel == -1:
                primeira_visivel = 0
            if ultima_visivel == -1:
                ultima_visivel = total_linhas - 1

            # se estamos indo para baixo e a linha atual é a última visível -> rolar (para manter o comportamento desejado)
            if step > 0 and atual >= ultima_visivel:
                item = self._scroll_table.item(proxima, 0)
                if item:
                    self._scroll_table.scrollToItem(item, QTableWidget.ScrollHint.PositionAtBottom)
            # se estamos indo para cima e a linha atual é a primeira visível -> rolar para cima
            elif step < 0 and atual <= primeira_visivel:
                item = self._scroll_table.item(proxima, 0)
                if item:
                    self._scroll_table.scrollToItem(item, QTableWidget.ScrollHint.PositionAtTop)

            # selecionar a próxima linha sem forçar nova lógica de "garantir visibilidade"
            self._selecionar_linha(proxima, garantir_visivel=False)
            atual = proxima

    def _selecionar_linha(self, linha: int, garantir_visivel: bool = True):
        """
        Seleciona uma linha e — opcionalmente — garante visibilidade.
        O parâmetro garantir_visivel permite à navegação controlar quando rolar o viewport.
        """
        if linha < 0 or linha >= self._scroll_table.rowCount():
            return

        self._scroll_table.setCurrentCell(linha, 0)

        if garantir_visivel:
            self._garantir_linha_visivel(linha)

    def _garantir_linha_visivel(self, linha: int):
        """
        Garante que a linha está visível: apenas posiciona no topo ou no fundo
        se a linha estiver fora da área visível. Se já estiver visível, não faz nada.
        """
        item = self._scroll_table.item(linha, 0)
        if not item:
            return

        primeira_visivel = self._scroll_table.rowAt(0)
        ultima_visivel = self._scroll_table.rowAt(self._scroll_table.viewport().height() - 1)

        if primeira_visivel == -1:
            primeira_visivel = 0
        if ultima_visivel == -1:
            ultima_visivel = self._scroll_table.rowCount() - 1

        if linha < primeira_visivel:
            self._scroll_table.scrollToItem(item, QTableWidget.ScrollHint.PositionAtTop)
        elif linha > ultima_visivel:
            self._scroll_table.scrollToItem(item, QTableWidget.ScrollHint.PositionAtBottom)
        # senao: já está visível -> não faz nada

    def set_scroll_sensibilidade(self, sensibilidade: int):
        """
        Ajusta a sensibilidade do scroll (quantas linhas por evento).

        Args:
            sensibilidade: Número de linhas (mínimo: 1)
        """
        self._scroll_sensibilidade = max(1, sensibilidade)

    def set_scroll_auto_select(self, auto_select: bool):
        """
        Define se deve selecionar automaticamente a primeira linha quando não há seleção.

        Args:
            auto_select: True para ativar, False para desativar
        """
        self._scroll_auto_select = auto_select

    def disable_scroll_navigation(self):
        """
        Desativa a navegação por scroll (útil temporariamente).
        """
        if hasattr(self, '_scroll_table'):
            self._scroll_table.viewport().removeEventFilter(self)

    def enable_scroll_navigation(self):
        """
        Reativa a navegação por scroll.
        """
        if hasattr(self, '_scroll_table'):
            self._scroll_table.viewport().installEventFilter(self)
