from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QLabel, QMenu, QFrame)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QTimer, QEvent

class BaseTableView(QWidget):
    TABLE_NAME = None
    MODEL_CLASS = None
    DIALOG_CLASS = None
    COLUMNS = []
    COLUMN_WIDTHS = []

    def __init__(self):
        super().__init__()
        self.mostrar_inativos = False
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.processar_scroll)
        self.scroll_direcao = 0
        self.init_ui()
        self.carregar_dados()
        self.configurar_atalhos()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        self.criar_cabecalho(layout)
        self.criar_botoes(layout)
        self.criar_tabela(layout)

        self.setLayout(layout)

    def configurar_atalhos(self):
        """Configura atalhos de teclado incluindo navegação"""
        # Atalho existente
        self.atalho_f11 = QShortcut(QKeySequence("F11"), self)
        self.atalho_f11.activated.connect(self.toggle_filtro_inativos)

        # Navegação por linhas
        self.atalho_seta_baixo = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        self.atalho_seta_cima = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        self.atalho_page_down = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        self.atalho_page_up = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        self.atalho_home = QShortcut(QKeySequence(Qt.Key.Key_Home), self)
        self.atalho_end = QShortcut(QKeySequence(Qt.Key.Key_End), self)

        # Conectar navegação
        self.atalho_seta_baixo.activated.connect(self.navegar_proxima_linha)
        self.atalho_seta_cima.activated.connect(self.navegar_linha_anterior)
        self.atalho_page_down.activated.connect(self.navegar_pagina_baixo)
        self.atalho_page_up.activated.connect(self.navegar_pagina_cima)
        self.atalho_home.activated.connect(self.navegar_primeira_linha)
        self.atalho_end.activated.connect(self.navegar_ultima_linha)

        # Atalhos para ações
        self.atalho_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        self.atalho_enter.activated.connect(self.editar_registro)

        self.atalho_delete = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.atalho_delete.activated.connect(self.inativar_registro)

        self.atalho_insert = QShortcut(QKeySequence(Qt.Key.Key_Insert), self)
        self.atalho_insert.activated.connect(self.novo_registro)

    def criar_cabecalho(self, layout):
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel(self.get_titulo())
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label para mostrar estado do filtro e atalhos
        filtro_texto = "(Mostrando apenas ativos - F11 para inativos)"
        atalhos_texto = "Navegação: ↑↓ Home End PgUp PgDn | Enter=Editar Del=Inativar Ins=Novo"

        self.label_filtro = QLabel(filtro_texto)
        self.label_filtro.setProperty("class", "muted")
        header_layout.addWidget(self.label_filtro)

        self.label_atalhos = QLabel(atalhos_texto)
        self.label_atalhos.setProperty("class", "muted")
        header_layout.addWidget(self.label_atalhos)

        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def criar_botoes(self, layout):
        btn_frame = QFrame()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_novo = QPushButton(self.get_texto_botao_novo())
        self.btn_editar = QPushButton("Editar")
        self.btn_excluir = QPushButton("Inativar")
        self.btn_reativar = QPushButton("Reativar")

        # Aplicar classes CSS do sistema de estilos
        self.btn_novo.setProperty("class", "success")
        self.btn_editar.setProperty("class", "secondary")
        self.btn_excluir.setProperty("class", "danger")
        self.btn_reativar.setProperty("class", "warning")

        self.btn_novo.clicked.connect(self.novo_registro)
        self.btn_editar.clicked.connect(self.editar_registro)
        self.btn_excluir.clicked.connect(self.inativar_registro)
        self.btn_reativar.clicked.connect(self.reativar_registro)

        btn_layout.addWidget(self.btn_novo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_excluir)
        btn_layout.addWidget(self.btn_reativar)
        btn_layout.addStretch()

        btn_frame.setLayout(btn_layout)
        layout.addWidget(btn_frame)

    def criar_tabela(self, layout):
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(self.COLUMNS))
        self.tabela.setHorizontalHeaderLabels(self.COLUMNS)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        header.setSectionsClickable(False)

        for i, width in enumerate(self.COLUMN_WIDTHS):
            if width is not None:
                self.tabela.setColumnWidth(i, width)
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Configurações de altura das linhas
        self.tabela.verticalHeader().setDefaultSectionSize(32)
        self.tabela.verticalHeader().setMinimumSectionSize(32)
        self.tabela.verticalHeader().setMaximumSectionSize(32)
        self.tabela.verticalHeader().setVisible(False)

        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)

        # Configurar para capturar eventos de mouse
        self.tabela.setMouseTracking(True)

        # CORREÇÃO: Instalar filtro de eventos para capturar wheel
        self.tabela.installEventFilter(self)

        self.tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabela.customContextMenuRequested.connect(self.mostrar_menu_contexto)

        # Conectar duplo clique para editar
        self.tabela.itemDoubleClicked.connect(self.editar_registro)

        layout.addWidget(self.tabela)

    def eventFilter(self, obj, event):
        """Filtro de eventos para capturar wheel events na tabela"""
        if obj == self.tabela and event.type() == QEvent.Type.Wheel:
            return self.processar_wheel_event(event)
        return super().eventFilter(obj, event)

    def processar_wheel_event(self, event):
        """Processa o evento de scroll do mouse"""
        if self.tabela.rowCount() == 0:
            return False

        linha_atual = self.tabela.currentRow()
        delta = event.angleDelta().y()

        # Se não há linha selecionada, selecionar a primeira
        if linha_atual == -1:
            self.tabela.setCurrentCell(0, 0)
            return True  # Bloquear o scroll padrão

        # Determinar nova linha
        if delta > 0:  # Scroll para cima
            nova_linha = max(0, linha_atual - 1)
        else:  # Scroll para baixo
            nova_linha = min(self.tabela.rowCount() - 1, linha_atual + 1)

        # Mover seleção apenas se for uma linha diferente
        if nova_linha != linha_atual:
            self.tabela.setCurrentCell(nova_linha, 0)
            # Garantir que a linha seja visível
            self.tabela.scrollToItem(
                self.tabela.item(nova_linha, 0),
                QTableWidget.ScrollHint.EnsureVisible
            )

        return True  # Bloquear o scroll padrão da tabela

    def wheel_event_customizado(self, event):
        """Método removido - agora usando eventFilter"""
        pass

    def navegar_proxima_linha(self):
        """Move para a próxima linha"""
        linha_atual = self.tabela.currentRow()
        total_linhas = self.tabela.rowCount()

        if total_linhas == 0:
            return

        if linha_atual == -1:  # Nenhuma linha selecionada
            linha_atual = -1

        nova_linha = min(linha_atual + 1, total_linhas - 1)
        self.tabela.setCurrentCell(nova_linha, 0)
        self.tabela.scrollToItem(self.tabela.item(nova_linha, 0))

    def navegar_linha_anterior(self):
        """Move para a linha anterior"""
        linha_atual = self.tabela.currentRow()
        total_linhas = self.tabela.rowCount()

        if total_linhas == 0:
            return

        if linha_atual == -1:  # Nenhuma linha selecionada
            linha_atual = total_linhas

        nova_linha = max(linha_atual - 1, 0)
        self.tabela.setCurrentCell(nova_linha, 0)
        self.tabela.scrollToItem(self.tabela.item(nova_linha, 0))

    def navegar_pagina_baixo(self):
        """Move uma página para baixo"""
        linha_atual = self.tabela.currentRow()
        total_linhas = self.tabela.rowCount()

        if total_linhas == 0:
            return

        # Calcular quantas linhas são visíveis
        altura_tabela = self.tabela.viewport().height()
        altura_linha = 32  # Altura definida acima
        linhas_visiveis = max(1, altura_tabela // altura_linha)

        if linha_atual == -1:
            nova_linha = 0
        else:
            nova_linha = min(linha_atual + linhas_visiveis, total_linhas - 1)

        self.tabela.setCurrentCell(nova_linha, 0)
        self.tabela.scrollToItem(self.tabela.item(nova_linha, 0))

    def navegar_pagina_cima(self):
        """Move uma página para cima"""
        linha_atual = self.tabela.currentRow()
        total_linhas = self.tabela.rowCount()

        if total_linhas == 0:
            return

        # Calcular quantas linhas são visíveis
        altura_tabela = self.tabela.viewport().height()
        altura_linha = 32
        linhas_visiveis = max(1, altura_tabela // altura_linha)

        if linha_atual == -1:
            nova_linha = total_linhas - 1
        else:
            nova_linha = max(linha_atual - linhas_visiveis, 0)

        self.tabela.setCurrentCell(nova_linha, 0)
        self.tabela.scrollToItem(self.tabela.item(nova_linha, 0))

    def navegar_primeira_linha(self):
        """Move para a primeira linha"""
        if self.tabela.rowCount() > 0:
            self.tabela.setCurrentCell(0, 0)
            self.tabela.scrollToItem(self.tabela.item(0, 0))

    def navegar_ultima_linha(self):
        """Move para a última linha"""
        total_linhas = self.tabela.rowCount()
        if total_linhas > 0:
            self.tabela.setCurrentCell(total_linhas - 1, 0)
            self.tabela.scrollToItem(self.tabela.item(total_linhas - 1, 0))

    def processar_scroll(self):
        """Processa o scroll acumulado"""
        if self.scroll_direcao > 0:
            self.navegar_linha_anterior()
        elif self.scroll_direcao < 0:
            self.navegar_proxima_linha()
        self.scroll_direcao = 0

    def toggle_filtro_inativos(self):
        """Alterna entre mostrar apenas ativos e mostrar todos"""
        self.mostrar_inativos = not self.mostrar_inativos

        if self.mostrar_inativos:
            self.label_filtro.setText("(Mostrando todos - F11 para apenas ativos)")
        else:
            self.label_filtro.setText("(Mostrando apenas ativos - F11 para inativos)")

        # Salvar linha atual
        linha_anterior = self.tabela.currentRow()
        registro_id = None
        if linha_anterior >= 0:
            try:
                registro_id = int(self.tabela.item(linha_anterior, 0).text())
            except (ValueError, AttributeError):
                pass

        self.carregar_dados()

        # Tentar restaurar seleção
        if registro_id is not None:
            self.selecionar_registro_por_id(registro_id)
        elif self.tabela.rowCount() > 0:
            # Se não conseguir encontrar o registro, selecionar primeira linha
            self.tabela.setCurrentCell(0, 0)

    def selecionar_registro_por_id(self, registro_id):
        """Seleciona um registro específico por ID"""
        for row in range(self.tabela.rowCount()):
            try:
                if int(self.tabela.item(row, 0).text()) == registro_id:
                    self.tabela.setCurrentCell(row, 0)
                    self.tabela.scrollToItem(self.tabela.item(row, 0))
                    return True
            except (ValueError, AttributeError):
                continue
        return False

    def carregar_dados(self):
        if self.mostrar_inativos:
            dados = self.MODEL_CLASS.buscar_todos(apenas_ativos=False)
        else:
            dados = self.MODEL_CLASS.buscar_todos(apenas_ativos=True)

        self.tabela.setRowCount(len(dados))

        for row, item in enumerate(dados):
            self.preencher_linha_tabela(row, item)

        # Selecionar primeira linha se houver dados
        if len(dados) > 0:
            self.tabela.setCurrentCell(0, 0)

    def preencher_linha_tabela(self, row, item):
        valores = self.obter_valores_linha(item)
        for col, valor in enumerate(valores):
            item_tabela = QTableWidgetItem(str(valor))

            # Centraliza a primeira coluna
            if col == 0:
                item_tabela.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Aplicar classe CSS para inativos
            if not item.ativo:
                item_tabela.setProperty("class", "inativo")

            self.tabela.setItem(row, col, item_tabela)

    def obter_valores_linha(self, item):
        return [item.id, item.nome, item.cnpj, item.telefone, item.email, item.observacao]

    def mostrar_menu_contexto(self, pos):
        menu = QMenu()

        editar_action = QAction("Editar (Enter)", self)
        inativar_action = QAction("Inativar (Del)", self)
        reativar_action = QAction("Reativar", self)

        editar_action.triggered.connect(self.editar_registro)
        inativar_action.triggered.connect(self.inativar_registro)
        reativar_action.triggered.connect(self.reativar_registro)

        menu.addAction(editar_action)

        registro = self.get_registro_selecionado()
        if registro and registro.ativo:
            menu.addAction(inativar_action)
        elif registro and not registro.ativo:
            menu.addAction(reativar_action)

        menu.exec(self.tabela.mapToGlobal(pos))

    def get_registro_selecionado(self):
        row = self.tabela.currentRow()
        if row == -1:
            return None
        try:
            registro_id = int(self.tabela.item(row, 0).text())
            return self.MODEL_CLASS.buscar_por_id(registro_id)
        except (ValueError, AttributeError):
            return None

    def novo_registro(self):
        dialog = self.DIALOG_CLASS()
        if dialog.exec():
            try:
                registro = dialog.get_data()
                registro.salvar()
                self.carregar_dados()

                # Tentar selecionar o novo registro
                self.selecionar_registro_por_id(registro.id)

                QMessageBox.information(self, "Sucesso", "Registro cadastrado com sucesso!")
            except ValueError as e:
                QMessageBox.warning(self, "Aviso", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cadastrar registro: {str(e)}")

    def editar_registro(self):
        registro = self.get_registro_selecionado()
        if not registro:
            QMessageBox.warning(self, "Aviso", "Selecione um registro para editar")
            return

        dialog = self.DIALOG_CLASS(registro)
        if dialog.exec():
            try:
                registro = dialog.get_data()
                registro.salvar()
                self.carregar_dados()

                # Tentar manter o registro selecionado
                self.selecionar_registro_por_id(registro.id)

                QMessageBox.information(self, "Sucesso", "Registro atualizado com sucesso!")
            except ValueError as e:
                QMessageBox.warning(self, "Aviso", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar registro: {str(e)}")

    def inativar_registro(self):
        registro = self.get_registro_selecionado()
        if not registro:
            QMessageBox.warning(self, "Aviso", "Selecione um registro para inativar")
            return

        if not registro.ativo:
            QMessageBox.warning(self, "Aviso", "Este registro já está inativo")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Inativação",
            f"Tem certeza que deseja inativar o registro '{registro.nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                linha_atual = self.tabela.currentRow()
                registro.inativar()
                self.carregar_dados()

                # Tentar manter posição na tabela
                if self.tabela.rowCount() > 0:
                    nova_linha = min(linha_atual, self.tabela.rowCount() - 1)
                    self.tabela.setCurrentCell(nova_linha, 0)

                QMessageBox.information(self, "Sucesso", "Registro inativado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao inativar registro: {str(e)}")

    def reativar_registro(self):
        registro = self.get_registro_selecionado()
        if not registro:
            QMessageBox.warning(self, "Aviso", "Selecione um registro para reativar")
            return

        if registro.ativo:
            QMessageBox.warning(self, "Aviso", "Este registro já está ativo")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Reativação",
            f"Tem certeza que deseja reativar o registro '{registro.nome}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                registro.reativar()
                self.carregar_dados()

                # Tentar selecionar o registro reativado
                self.selecionar_registro_por_id(registro.id)

                QMessageBox.information(self, "Sucesso", "Registro reativado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao reativar registro: {str(e)}")

    # MÉTODOS ABSTRATOS - devem ser implementados pelas subclasses
    def get_titulo(self):
        raise NotImplementedError("Subclasses devem implementar get_titulo()")

    def get_texto_botao_novo(self):
        raise NotImplementedError("Subclasses devem implementar get_texto_botao_novo()")
