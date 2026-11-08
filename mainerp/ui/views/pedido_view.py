"""
View de Pedidos - Otimizada com correções de ordenação e layout reorganizado - CORRIGIDO para nova estrutura
"""

import logging
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mainerp.data.models.pedido import Pedido
from mainerp.domain.utils.export_utils import ExportUtils
from mainerp.domain.utils.helpers import (
    criar_pasta_se_nao_existir,
    formatar_data,
    formatar_moeda,
    validar_data,
)
from mainerp.domain.utils.pedido_utils import PedidoUtils
from mainerp.reports.print_pedido import PrintPedido
from mainerp.reports.print_relat_pedido import PrintRelatPedido
from mainerp.ui.dialogs.pedido_dialog import PedidoDialog
from mainerp.ui.listagem_modelo import configurar_modelo
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin
from mainerp.ui.styles import cores_ativas
from mainerp.ui.tabela import configurar_listagem_padrao
from mainerp.ui.table_items import NumericTableWidgetItem

logger = logging.getLogger(__name__)


class PedidoView(TableScrollNavigationMixin, QWidget):
    """View de gestão de pedidos otimizada - CORRIGIDA para nova estrutura"""

    def __init__(self):
        super().__init__()
        self.fornecedor_filtro = None
        self.dados = []
        criar_pasta_se_nao_existir("relatorios")
        self._init_ui()
        configurar_modelo(
            self,
            self.tabela_pedidos,
            self.busca_fornecedor,
            [
                (self.btn_novo_pedido, "plus", "Ctrl+N"),
                (self.btn_receber, "package-check", None),
                (self.btn_editar, "pencil", "Ctrl+E"),
                (self.btn_cancelar, "circle-x", None),
                (self.btn_imprimir, "printer", "Ctrl+P"),
                (self.btn_exportar, "printer", None),
            ],
        )
        self._carregar_dados()

    def _init_ui(self):
        """Inicializa interface otimizada"""
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
        self._criar_grupo_pedidos(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria cabeçalho"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestão de Pedidos")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label informativo sobre filtros
        self.label_info = QLabel("(Últimos 30 dias)")
        self.label_info.setProperty("class", "muted")
        header_layout.addWidget(self.label_info)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_grupo_filtros(self, layout):
        """Cria grupo de filtros similar ao VendaView"""
        grupo_filtros = QGroupBox("Filtros")
        grupo_filtros.setProperty("class", "clean-group")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Busca por fornecedor (lado esquerdo)
        self.busca_fornecedor = QLineEdit()
        self.busca_fornecedor.setPlaceholderText("Buscar por Nome do fornecedor...")
        self.busca_fornecedor.setMaximumWidth(300)
        self.busca_fornecedor.textChanged.connect(self._filtrar_pedidos)
        filtro_layout.addWidget(self.busca_fornecedor)

        # ComboBox de status (após busca de fornecedor)
        filtro_layout.addWidget(QLabel("Status:"))

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "Pendentes", "Recebidos", "Cancelados"])
        self.combo_status.setCurrentText("Todos")
        self.combo_status.setMaximumWidth(120)
        self.combo_status.currentTextChanged.connect(self._filtrar_pedidos)
        filtro_layout.addWidget(self.combo_status)

        filtro_layout.addStretch()

        # Filtros de data (centro)
        self._criar_filtros_data_centralizados(filtro_layout)

        filtro_layout.addStretch()

        # Botão limpar (direita)
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(btn_limpar)

        grupo_filtros.setLayout(filtro_layout)
        layout.addWidget(grupo_filtros)

    def _criar_filtros_data_centralizados(self, layout):
        """Cria os campos de filtro por data centralizados"""
        layout.addWidget(QLabel("Período de:"))

        self.data_inicio = QLineEdit()
        self.data_inicio.setPlaceholderText("DD/MM/AAAA")
        self.data_inicio.setMaximumWidth(100)
        self.data_inicio.setText(
            (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        )
        self.data_inicio.textChanged.connect(self._filtrar_pedidos)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.data_fim.textChanged.connect(self._filtrar_pedidos)
        layout.addWidget(self.data_fim)

    def _criar_grupo_acoes(self, layout):
        """Cria grupo de ações"""
        grupo_acoes = QGroupBox("Ações")
        grupo_acoes.setProperty("class", "clean-group")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões com classes semânticas
        botoes_config = [
            ("btn_novo_pedido", "Novo Pedido", "success", self._abrir_novo_pedido),
            ("btn_receber", "Receber Pedido", "primary", self._receber_pedido),
            ("btn_editar", "Editar Pedido", "secondary", self._editar_pedido),
            ("btn_cancelar", "Cancelar Pedido", "danger", self._cancelar_pedido),
        ]

        for attr_name, texto, classe, callback in botoes_config:
            botao = QPushButton(texto)
            botao.setProperty("class", classe)
            botao.clicked.connect(callback)
            setattr(self, attr_name, botao)
            btn_layout.addWidget(botao)

        btn_layout.addStretch()

        # Botões de relatório
        self.btn_imprimir = QPushButton("Imprimir Pedido")
        self.btn_imprimir.setProperty("class", "warning")
        self.btn_imprimir.clicked.connect(self._imprimir_pedido)

        self.btn_exportar = QPushButton("Imprimir Relatório")
        self.btn_exportar.setProperty("class", "primary")
        self.btn_exportar.clicked.connect(self._exportar_pedidos)

        btn_layout.addWidget(self.btn_imprimir)
        btn_layout.addWidget(self.btn_exportar)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_pedidos(self, layout):
        """Cria grupo da tabela de pedidos"""
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

        titulo = QLabel("Pedidos")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self._criar_tabela_pedidos()  # Este método deve criar self.tabela_pedidos
        container_layout.addWidget(self.tabela_pedidos)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _criar_tabela_pedidos(self):
        """Configura tabela de pedidos - VERSÃO COM ALTURA FIXA"""
        self.tabela_pedidos = QTableWidget()
        self.tabela_pedidos.setColumnCount(8)  # AUMENTADO para incluir desconto
        self.tabela_pedidos.setHorizontalHeaderLabels(
            [
                "ID",
                "Fornecedor",
                "Data Pedido",
                "Status",
                "Recebimento",
                "Desconto",
                "Frete",
                "Total",
            ]
        )

        # Configuração das colunas
        header = self.tabela_pedidos.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Fornecedor
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Data
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Status
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Recebimento
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Desconto
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Frete
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Total

        # LARGURAS AJUSTADAS para incluir desconto
        larguras = [50, 150, 100, 90, 100, 80, 70, 80]
        for i, largura in enumerate(larguras):
            if largura > 0:  # Aplica apenas larguras positivas
                self.tabela_pedidos.setColumnWidth(i, largura)

        configurar_listagem_padrao(self.tabela_pedidos)

        self.setup_scroll_navigation(
            tabela=self.tabela_pedidos,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    # ========== MÉTODOS DE DADOS ==========

    def _get_status_selecionado(self):
        """Retorna status selecionado"""
        status_selecionado = self.combo_status.currentText()
        if status_selecionado == "Todos":
            return None
        elif status_selecionado == "Pendentes":
            return "pendente"
        elif status_selecionado == "Recebidos":
            return "recebido"
        elif status_selecionado == "Cancelados":
            return "cancelado"
        return None

    def _buscar_pedidos_com_estrutura_correta(
        self, data_inicio_str=None, data_fim_str=None, fornecedor_id=None, status=None
    ):
        """Normaliza datas da interface e delega a consulta ao model Pedido."""
        try:
            if data_inicio_str:
                try:
                    data_inicio_str = datetime.strptime(
                        data_inicio_str, "%d/%m/%Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    data_inicio_str = None

            if data_fim_str:
                try:
                    data_fim_str = datetime.strptime(data_fim_str, "%d/%m/%Y").strftime(
                        "%Y-%m-%d"
                    )
                except ValueError:
                    data_fim_str = None

            return Pedido.buscar_para_listagem(
                data_inicio_str, data_fim_str, fornecedor_id, status
            )

        except Exception:
            logger.exception("Erro ao buscar pedidos")
            return []

    def _carregar_dados(
        self, data_inicio_str=None, data_fim_str=None, fornecedor_id=None, status=None
    ):
        """Carrega dados na tabela - MÉTODO ATUALIZADO"""
        if not hasattr(self, "tabela_pedidos"):
            return

        try:
            # Se não foram passados parâmetros, usa os valores dos filtros
            if data_inicio_str is None:
                data_inicio_str = self.data_inicio.text().strip()
            if data_fim_str is None:
                data_fim_str = self.data_fim.text().strip()
            if status is None:
                status = self._get_status_selecionado()

            # CORREÇÃO: Usar novo método que busca com estrutura explícita
            self.dados = self._buscar_pedidos_com_estrutura_correta(
                data_inicio_str, data_fim_str, fornecedor_id, status
            )

            self._filtrar_pedidos()
            self._atualizar_label_info()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar pedidos: {e!s}")

    def _filtrar_pedidos(self):
        """CORREÇÃO: Filtra pedidos com validação - sempre usa dados originais"""
        data_inicio_str = self.data_inicio.text().strip()
        data_fim_str = self.data_fim.text().strip()
        fornecedor_nome = self.busca_fornecedor.text().strip()
        status_selecionado = self.combo_status.currentText()

        # Validação visual
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
                "Pendentes": "pendente",
                "Recebidos": "recebido",
                "Cancelados": "cancelado",
            }
            status_filtro = status_map.get(status_selecionado, "")
            dados_filtrados = [
                p for p in dados_filtrados if str(p[7]).lower() == status_filtro
            ]

        # Filtro por nome do fornecedor na busca local
        # CORREÇÃO: Usar índice 9 para nome do fornecedor
        if fornecedor_nome:
            dados_filtrados = [
                p
                for p in dados_filtrados
                if fornecedor_nome.lower()
                in (str(p[9]) if len(p) > 9 and p[9] else "").lower()
            ]

        self.tabela_pedidos.setRowCount(len(dados_filtrados))
        self._preencher_linha_tabela(dados_filtrados)
        self._atualizar_label_info()

    def _preencher_linha_tabela(self, pedidos):
        """CORREÇÃO: Preenche tabela com NOVA ESTRUTURA incluindo desconto"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_pedidos.setSortingEnabled(False)

        for row, pedido in enumerate(pedidos):
            # ESTRUTURA CORRIGIDA:
            # 0=id, 1=fornecedor_id, 2=data_pedido, 3=data_recebimento, 4=valor_total,
            # 5=valor_frete, 6=observacao, 7=status, 8=desconto, 9=fornecedor_nome

            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(str(pedido[0]))
            item_id.setData(
                Qt.ItemDataRole.UserRole, pedido[0]
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_pedidos.setItem(row, 0, item_id)

            # CORREÇÃO: Fornecedor - agora no índice 9
            fornecedor_nome = (
                str(pedido[9])
                if len(pedido) > 9 and pedido[9]
                else "Fornecedor não informado"
            )
            self.tabela_pedidos.setItem(row, 1, QTableWidgetItem(fornecedor_nome))

            # Data Pedido
            data_pedido = QTableWidgetItem(
                formatar_data(pedido[2], "%Y-%m-%d", "%d/%m/%Y")
            )
            data_pedido.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_pedidos.setItem(row, 2, data_pedido)

            # Status com cores - índice 7
            self._preencher_status(row, pedido[7])

            # Data Recebimento - índice 3
            data_recebimento = (
                formatar_data(pedido[3], "%Y-%m-%d", "%d/%m/%Y") if pedido[3] else "-"
            )
            data_recebimento_item = QTableWidgetItem(data_recebimento)
            data_recebimento_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_pedidos.setItem(row, 4, data_recebimento_item)

            # NOVO: Desconto - índice 8
            desconto_valor = float(pedido[8]) if len(pedido) > 8 and pedido[8] else 0
            desconto_item = NumericTableWidgetItem(
                formatar_moeda(desconto_valor) if desconto_valor > 0 else "-"
            )
            desconto_item.setData(Qt.ItemDataRole.UserRole, desconto_valor)
            desconto_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            # Destacar desconto em vermelho se houver
            if desconto_valor > 0:
                desconto_item.setForeground(QBrush(QColor(cores_ativas().danger_text)))
            self.tabela_pedidos.setItem(row, 5, desconto_item)

            # CORREÇÃO: Frete - índice 5
            frete_valor = float(pedido[5]) if pedido[5] else 0
            frete_item = NumericTableWidgetItem(
                formatar_moeda(frete_valor) if frete_valor > 0 else "-"
            )
            frete_item.setData(
                Qt.ItemDataRole.UserRole, frete_valor
            )  # Valor numérico para ordenação
            frete_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_pedidos.setItem(row, 6, frete_item)

            # CORREÇÃO: Total - índice 4
            total_valor = float(pedido[4]) if pedido[4] else 0
            total_item = NumericTableWidgetItem(formatar_moeda(total_valor))
            total_item.setData(
                Qt.ItemDataRole.UserRole, total_valor
            )  # Valor numérico para ordenação
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_pedidos.setItem(row, 7, total_item)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_pedidos.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_pedidos.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _preencher_status(self, row, status):
        """Preenche status com cores"""
        status_str = (
            str(status) if status is not None else "pendente"
        )  # CORREÇÃO: Garantir que seja string
        status_item = QTableWidgetItem(status_str.capitalize())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cores baseadas no status
        if status_str.lower() == "pendente":
            status_item.setForeground(QBrush(QColor(cores_ativas().warning_text)))
        elif status_str.lower() == "recebido":
            status_item.setForeground(QBrush(QColor(cores_ativas().success_text)))
        elif status_str.lower() == "cancelado":
            status_item.setForeground(QBrush(QColor(cores_ativas().danger_text)))

        self.tabela_pedidos.setItem(row, 3, status_item)

    def _atualizar_label_info(self):
        """Atualiza o label informativo baseado nos filtros"""
        total_pedidos = self.tabela_pedidos.rowCount()
        data_inicio = self.data_inicio.text().strip()
        data_fim = self.data_fim.text().strip()
        fornecedor = self.busca_fornecedor.text().strip()
        status = self.combo_status.currentText()

        info_parts = [f"({total_pedidos} pedidos"]

        if status != "Todos":
            info_parts.append(f"status: {status.lower()}")

        if data_inicio or data_fim:
            if data_inicio and data_fim:
                info_parts.append(f"período: {data_inicio} a {data_fim}")
            elif data_inicio:
                info_parts.append(f"a partir de {data_inicio}")
            elif data_fim:
                info_parts.append(f"até {data_fim}")

        if fornecedor:
            info_parts.append(f"fornecedor: {fornecedor}")

        self.label_info.setText(" - ".join(info_parts) + ")")

    def _marcar_campo_erro(self, campo):
        """Marca campo com erro"""
        campo.setProperty("class", "error")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_campo_erro(self, campo):
        """Remove erro do campo"""
        campo.setProperty("class", "")
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _limpar_filtros(self):
        """Limpa todos os filtros"""
        self.data_inicio.setText(
            (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        )
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.busca_fornecedor.clear()
        self._limpar_campo_erro(self.data_inicio)
        self._limpar_campo_erro(self.data_fim)
        self.fornecedor_filtro = None
        self.combo_status.setCurrentText("Todos")
        self._carregar_dados()

    # ========== MÉTODOS DE AÇÃO ==========

    def _selecionar_fornecedor(self):
        """Abre dialog de seleção de fornecedor"""
        from mainerp.ui.dialogs.fornecedor_selection_dialog import (
            FornecedorSelectionDialog,
        )

        dialog = FornecedorSelectionDialog(self)
        if dialog.exec():
            fornecedor = dialog.get_fornecedor_selecionado()
            if fornecedor:
                self.fornecedor_filtro = fornecedor
                self.busca_fornecedor.setText(fornecedor.nome)
                self._filtrar_pedidos()

    def _get_pedido_selecionado(self):
        """Obtém pedido selecionado"""
        row = self.tabela_pedidos.currentRow()
        if row == -1:
            return None
        try:
            item = self.tabela_pedidos.item(row, 0)
            if item is None:
                return None
            pedido_id = int(item.text())
            from mainerp.data.models.pedido import Pedido

            return Pedido.buscar_por_id(pedido_id)
        except (ValueError, AttributeError):
            return None

    def _abrir_novo_pedido(self):
        """Abre dialog de novo pedido"""
        dialog = PedidoDialog(self)
        dialog.pedido_realizado.connect(self._carregar_dados)
        dialog.exec()

    def _receber_pedido(self):
        """Recebe pedido selecionado"""
        pedido = self._get_pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido para receber")
            return

        if pedido.status == "recebido":
            QMessageBox.warning(self, "Aviso", "Este pedido já foi recebido")
            return

        if pedido.status == "cancelado":
            QMessageBox.warning(
                self, "Aviso", "Não é possível receber um pedido cancelado"
            )
            return

        pedido_id = pedido.id
        if not isinstance(pedido_id, int):
            QMessageBox.warning(self, "Aviso", "ID do pedido inválido")
            return

        if self._confirmar_recebimento(pedido):
            try:
                PedidoUtils.receber_pedido(pedido_id)
                self._carregar_dados()
                QMessageBox.information(self, "Sucesso", "Pedido recebido!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao receber pedido: {e!s}")

    def _confirmar_recebimento(self, pedido):
        """Confirma recebimento do pedido"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Recebimento",
            f"Marcar pedido #{pedido.id} como recebido?\n"
            f"Fornecedor: {pedido.obter_fornecedor().nome if pedido.obter_fornecedor() else 'N/A'}\n"
            f"Total: {formatar_moeda(pedido.valor_total)}\n\n"
            "Esta ação irá atualizar o estoque dos produtos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _editar_pedido(self):
        """Edita pedido selecionado"""
        pedido = self._get_pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido para editar")
            return

        if pedido.status != "pendente":
            QMessageBox.warning(
                self,
                "Aviso",
                f"Só é possível editar pedidos pendentes.\nStatus atual: {pedido.status.capitalize()}",
            )
            return

        dialog = PedidoDialog(self, pedido=pedido)
        dialog.pedido_realizado.connect(self._carregar_dados)
        dialog.exec()

    def _cancelar_pedido(self):
        """Cancela pedido selecionado"""
        pedido = self._get_pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido para cancelar")
            return

        if pedido.status == "recebido":
            QMessageBox.warning(
                self, "Aviso", "Não é possível cancelar um pedido já recebido"
            )
            return

        if pedido.status == "cancelado":
            QMessageBox.warning(self, "Aviso", "Este pedido já está cancelado")
            return

        if self._confirmar_cancelamento(pedido):
            try:
                pedido_id = pedido.id
                if not isinstance(pedido_id, int):
                    QMessageBox.warning(
                        self, "Aviso", "Pedido inválido para cancelamento"
                    )
                    return

                PedidoUtils.cancelar_pedido(pedido_id)
                self._carregar_dados()
                QMessageBox.information(self, "Sucesso", "Pedido cancelado!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao cancelar pedido: {e!s}")

    def _confirmar_cancelamento(self, pedido):
        """Confirma cancelamento do pedido"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Cancelamento",
            f"Cancelar pedido #{pedido.id}?\n"
            f"Fornecedor: {pedido.obter_fornecedor().nome if pedido.obter_fornecedor() else 'N/A'}\n"
            f"Total: {formatar_moeda(pedido.valor_total)}\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _exportar_pedidos(self):
        """Exporta relatório de pedidos"""
        try:
            data_inicio = self.data_inicio.text().strip()
            data_fim = self.data_fim.text().strip()
            fornecedor_id = (
                self.fornecedor_filtro.id if self.fornecedor_filtro else None
            )
            status = self._get_status_selecionado()

            if data_inicio and not validar_data(data_inicio):
                QMessageBox.warning(self, "Aviso", "Data inicial inválida")
                return
            if data_fim and not validar_data(data_fim):
                QMessageBox.warning(self, "Aviso", "Data final inválida")
                return

            filename = PrintRelatPedido.gerar_relatorio_por_periodo(
                data_inicio, data_fim, fornecedor_id, status, "relatorios"
            )

            if filename and ExportUtils.abrir_arquivo(filename):
                QMessageBox.information(
                    self, "Sucesso", f"Relatório exportado:\n{filename}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Arquivo salvo",
                    f"Arquivo salvo em: {filename}\nNão foi possível abrir automaticamente.",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro na Exportação", f"Erro ao exportar pedidos:\n{e!s}"
            )

    def _imprimir_pedido(self):
        """Imprime pedido selecionado"""
        pedido = self._get_pedido_selecionado()
        if not pedido:
            QMessageBox.warning(self, "Aviso", "Selecione um pedido para imprimir")
            return
        try:
            filename = PrintPedido.gerar_comprovante(pedido.id, "relatorios")
            if filename and ExportUtils.abrir_arquivo(filename):
                QMessageBox.information(
                    self, "Sucesso", f"Comprovante gerado:\n{filename}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Arquivo salvo",
                    f"Arquivo salvo em: {filename}\nNão foi possível abrir automaticamente.",
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Erro na Impressão", f"Erro ao gerar comprovante:\n{e!s}"
            )

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def selecionar_fornecedor(self):
        """Método público para compatibilidade"""
        self._selecionar_fornecedor()

    def carregar_dados(
        self, data_inicio_str=None, data_fim_str=None, fornecedor_id=None, status=None
    ):
        """Método público para compatibilidade"""
        self._carregar_dados(data_inicio_str, data_fim_str, fornecedor_id, status)

    def get_status_selecionado(self):
        """Método público para compatibilidade"""
        return self._get_status_selecionado()

    def filtrar_pedidos(self):
        """Método público para compatibilidade"""
        self._filtrar_pedidos()

    def limpar_filtros(self):
        """Método público para compatibilidade"""
        self._limpar_filtros()

    def abrir_novo_pedido(self):
        """Método público para compatibilidade"""
        self._abrir_novo_pedido()

    def get_pedido_selecionado(self):
        """Método público para compatibilidade"""
        return self._get_pedido_selecionado()

    def receber_pedido(self):
        """Método público para compatibilidade"""
        self._receber_pedido()

    def editar_pedido(self):
        """Método público para compatibilidade"""
        self._editar_pedido()

    def cancelar_pedido(self):
        """Método público para compatibilidade"""
        self._cancelar_pedido()

    def exportar_pedidos(self):
        """Método público para compatibilidade"""
        self._exportar_pedidos()

    def imprimir_pedido(self):
        """Método público para compatibilidade"""
        self._imprimir_pedido()

    def atualizar_tabela(self):
        """Método público para compatibilidade"""
        self._carregar_dados()
