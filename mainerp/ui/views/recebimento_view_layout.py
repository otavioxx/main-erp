"""Componentes de RecebimentoView."""





from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from mainerp.core.app_logging import registrar_excecao
from mainerp.ui.mixins.component_mixin import ComponentMixin
from mainerp.ui.tabela import configurar_interacao_listagem

__all__ = ["_RecebimentoViewLayout"]


class _RecebimentoViewLayout(ComponentMixin):
    def _init_ui(self):
        """Inicializa interface com layout consistente ao CondicionalView"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        self._criar_header(layout)

        # Filtros
        self._criar_grupo_filtros(layout)

        # Ações
        self._criar_grupo_acoes(layout)

        # Tabela
        self._criar_grupo_duplicatas(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria cabeçalho"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestão de Recebimentos")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label informativo
        self.label_info = QLabel("(Carregando...)")
        self.label_info.setProperty("class", "muted")
        header_layout.addWidget(self.label_info)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_grupo_filtros(self, layout):
        """Cria grupo de filtros com layout similar ao CondicionalView"""
        grupo_filtros = QGroupBox("Filtros")
        grupo_filtros.setProperty("class", "clean-group")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Busca por cliente (lado esquerdo)
        self.busca_cliente = QLineEdit()
        self.busca_cliente.setPlaceholderText("Buscar por nome do cliente...")
        self.busca_cliente.setMaximumWidth(300)
        self.busca_cliente.textChanged.connect(self._filtrar_duplicatas_otimizado)
        filtro_layout.addWidget(self.busca_cliente)

        # ComboBox de status (após busca de cliente)
        filtro_layout.addWidget(QLabel("Status:"))

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Abertas", "Vencidas", "Pagas", "Todas"])
        self.combo_status.setCurrentText("Abertas")
        self.combo_status.setMaximumWidth(120)
        self.combo_status.currentTextChanged.connect(self._filtrar_duplicatas_otimizado)
        filtro_layout.addWidget(self.combo_status)

        filtro_layout.addStretch()

        # Filtros de data (centro)
        self._criar_filtros_data(filtro_layout)

        filtro_layout.addStretch()

        # Botão limpar (direita)
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(btn_limpar)

        grupo_filtros.setLayout(filtro_layout)
        layout.addWidget(grupo_filtros)

    def _criar_filtros_data(self, layout):
        """Cria filtros de data centralizados"""
        layout.addWidget(QLabel("Período de:"))

        self.data_inicio = QLineEdit()
        self.data_inicio.setPlaceholderText("DD/MM/AAAA")
        self.data_inicio.setMaximumWidth(100)
        self.data_inicio.textChanged.connect(self._filtrar_duplicatas_otimizado)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.textChanged.connect(self._filtrar_duplicatas_otimizado)
        layout.addWidget(self.data_fim)

    def _criar_grupo_acoes(self, layout):
        """Cria grupo de ações"""
        grupo_acoes = QGroupBox("Ações")
        grupo_acoes.setProperty("class", "clean-group")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        self.btn_receber = QPushButton("Receber Duplicata")
        self.btn_receber.setProperty("class", "success")
        self.btn_receber.clicked.connect(self._receber_duplicata)

        btn_layout.addWidget(self.btn_receber)
        btn_layout.addStretch()

        self.btn_imprimir_relatorio = QPushButton("Imprimir Relatório")
        self.btn_imprimir_relatorio.setProperty("class", "primary")
        self.btn_imprimir_relatorio.clicked.connect(self._imprimir_relatorio)
        btn_layout.addWidget(self.btn_imprimir_relatorio)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_duplicatas(self, layout):
        """Cria grupo da tabela de duplicatas"""
        # Frame container
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        # Layout principal
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Título
        titulo_frame = QFrame()
        titulo_layout = QHBoxLayout()
        titulo_layout.setContentsMargins(8, 4, 8, 4)

        titulo = QLabel("Duplicatas")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self._criar_tabela_duplicatas()
        container_layout.addWidget(self.tabela_duplicatas)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _criar_tabela_duplicatas(self):
        """Configura tabela de duplicatas - VERSÃO COM TIMER SEGURO"""
        self.tabela_duplicatas = QTableWidget()

        # Altura desejada
        altura_desejada = 22

        # 1. Configurar altura primeiro
        vheader = self.tabela_duplicatas.verticalHeader()
        assert vheader is not None
        vheader.setDefaultSectionSize(altura_desejada)
        vheader.setMinimumSectionSize(altura_desejada)
        vheader.setMaximumSectionSize(altura_desejada)
        vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vheader.setCascadingSectionResizes(False)
        vheader.setStretchLastSection(False)
        vheader.setVisible(False)

        # 2. Configuração normal das colunas
        self.tabela_duplicatas.setColumnCount(8)
        self.tabela_duplicatas.setHorizontalHeaderLabels(
            [
                "ID",
                "Cliente",
                "Status",
                "Venda",
                "Parcela",
                "Valor",
                "Vencimento",
                "Pagamento",
            ]
        )

        header = self.tabela_duplicatas.horizontalHeader()
        assert header is not None
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        # Larguras
        larguras = [50, 0, 120, 60, 60, 80, 100, 100]
        for i, largura in enumerate(larguras):
            if largura > 0:
                self.tabela_duplicatas.setColumnWidth(i, largura)

        configurar_interacao_listagem(self.tabela_duplicatas, ordenar=True)

        # 4. Função para forçar altura COM VERIFICAÇÃO DE SEGURANÇA
        def aplicar_altura_fixa_segura():
            """Versão segura que verifica se a tabela ainda existe"""
            try:
                # Verificação robusta da existência da tabela
                if not hasattr(self, "tabela_duplicatas"):
                    return

                # Verificar se o objeto Qt ainda está vivo
                # Tentando acessar uma propriedade simples
                try:
                    self.tabela_duplicatas.objectName()
                except RuntimeError:
                    # Objeto foi deletado, sair silenciosamente
                    return

                # Verificar se a tabela ainda está acessível
                if not self.tabela_duplicatas or not self.tabela_duplicatas.isVisible():
                    return

                # Aplicar altura em cada linha
                for row in range(self.tabela_duplicatas.rowCount()):
                    try:
                        self.tabela_duplicatas.setRowHeight(row, altura_desejada)
                    except RuntimeError:
                        # Se der erro em uma linha, continuar
                        continue

            except RuntimeError:
                # Objeto deletado durante execução
                return
            except Exception:
                # Qualquer outro erro, ignorar silenciosamente
                registrar_excecao(
                    __name__,
                    "Exception handled in RecebimentoView._criar_tabela_duplicatas.aplicar_altura_fixa_segura in views/recebimento_view.py",
                )
                return

        # 5. Timer SEGURO para aplicar após renderização
        from PyQt6.QtCore import QTimer

        # Criar timer como filho da tabela (será destruído automaticamente)
        timer = QTimer(self.tabela_duplicatas)
        timer.setSingleShot(True)
        timer.timeout.connect(aplicar_altura_fixa_segura)
        timer.start(150)  # Executar após 150ms

        # 6. Função segura para conectar aos sinais
        def conectar_sinais_seguro():
            """Conecta sinais de forma segura"""
            try:
                if (
                    hasattr(self, "tabela_duplicatas")
                    and self.tabela_duplicatas
                    and hasattr(self.tabela_duplicatas, "model")
                ):
                    model = self.tabela_duplicatas.model()
                    if model:
                        # Usar weakref ou captura direta
                        model.rowsInserted.connect(
                            lambda parent, first, last: aplicar_altura_fixa_segura()
                        )
                        model.modelReset.connect(lambda: aplicar_altura_fixa_segura())
            except RuntimeError:
                pass

        # Conectar sinais após um pequeno delay
        QTimer.singleShot(50, conectar_sinais_seguro)

        # 7. Navegação
        self.setup_scroll_navigation(
            tabela=self.tabela_duplicatas,
            scroll_sensibilidade=1,
            auto_select_first=True,
        )

        return self.tabela_duplicatas
