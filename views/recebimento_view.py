"""
View de Recebimentos - Otimizada para performance
"""

import logging
from datetime import datetime

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

from database import Database
from dialogs.cliente_selection_dialog import ClienteSelectionDialog
from dialogs.recebimento_dialog import RecebimentoDialog
from exceptions import ErroERP
from imprecoes.print_comprovante_recebimento import PrintComprovanteRecebimento
from imprecoes.print_relat_recebimento import PrintRelatRecebimento
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.duplicata import Duplicata
from utils.export_utils import ExportUtils
from utils.helpers import (
    criar_pasta_se_nao_existir,
    formatar_data,
    formatar_moeda,
    validar_data,
)

logger = logging.getLogger(__name__)


class NumericTableWidgetItem(QTableWidgetItem):
    """Item de tabela que ordena numericamente ao invés de alfabeticamente"""

    def __init__(self, text=""):
        super().__init__(text)

    def __lt__(self, other):
        """Sobrescreve a comparação para ordenação numérica"""
        try:
            # Tenta extrair valor numérico do UserRole primeiro
            self_value = self.data(Qt.ItemDataRole.UserRole)
            other_value = other.data(Qt.ItemDataRole.UserRole)

            if self_value is not None and other_value is not None:
                return float(self_value) < float(other_value)

            # Se não tem UserRole, tenta converter o texto
            return float(self.text()) < float(other.text())
        except (ValueError, TypeError):
            # Se não conseguir converter para número, usa ordenação de string
            return self.text() < other.text()


class RecebimentoView(TableScrollNavigationMixin, QWidget):
    """View de gestão de recebimentos otimizada para performance"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cliente_filtro = None
        self.duplicatas_filtradas = []
        self.ultima_duplicata_paga = None
        self.todas_duplicatas = []
        self._parcelas_cache = {}  # Cache para total de parcelas
        self._loaded = False  # Flag para carregamento lazy
        self._init_ui()
        criar_pasta_se_nao_existir("relatorios")

    def showEvent(self, event):
        """Carrega dados apenas quando a view é exibida (lazy loading)"""
        if not self._loaded:
            self._carregar_duplicatas()
            self._loaded = True
        super().showEvent(event)

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

        # 3. Configurações gerais (OS ESTILOS SERÃO APLICADOS GLOBALMENTE)
        self.tabela_duplicatas.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_duplicatas.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_duplicatas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_duplicatas.setAlternatingRowColors(True)
        self.tabela_duplicatas.setSortingEnabled(True)

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

    # ========== MÉTODOS DE DADOS OTIMIZADOS ==========

    def _carregar_duplicatas(self):
        """Carrega duplicatas do banco - VERSÃO OTIMIZADA"""
        try:
            # Mostrar estado de carregamento
            self.label_info.setText("(Carregando...)")

            conn = Database().get_connection()
            cursor = conn.cursor()

            # CONSULTA ÚNICA OTIMIZADA com UNION ALL
            query = """
                -- Duplicatas abertas
                SELECT
                    d.id,
                    d.cliente_id,
                    d.venda_id,
                    d.numero_parcela,
                    d.valor_parcela as valor,
                    d.data_vencimento,
                    NULL as data_pagamento,
                    'aberto' as status,
                    c.nome as cliente_nome,
                    v.total as venda_total,
                    v.data_venda,
                    NULL as forma_pagamento,
                    0 as is_paga
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                LEFT JOIN vendas v ON d.venda_id = v.id
                WHERE d.status = 'aberto'

                UNION ALL

                -- Duplicatas pagas
                SELECT
                    dp.id,
                    dp.cliente_id,
                    dp.venda_id,
                    dp.numero_parcela,
                    dp.valor_original as valor,
                    dp.data_vencimento,
                    dp.data_pagamento,
                    'pago' as status,
                    c.nome as cliente_nome,
                    v.total as venda_total,
                    v.data_venda,
                    dp.forma_pagamento,
                    1 as is_paga
                FROM duplicatas_pagas dp
                LEFT JOIN clientes c ON dp.cliente_id = c.id
                LEFT JOIN vendas v ON dp.venda_id = v.id
                ORDER BY status, data_vencimento
            """

            cursor.execute(query)
            self.todas_duplicatas = cursor.fetchall()

            # Inicializar cache de parcelas
            self._inicializar_cache_parcelas()

            # Filtrar e exibir
            self._filtrar_duplicatas_otimizado()

        except Exception as e:
            self.label_info.setText("(Erro ao carregar)")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar duplicatas: {e!s}")
        finally:
            if "conn" in locals():
                conn.close()

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
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Buscar totais para todas as vendas de uma vez
            for venda_id in venda_ids:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM duplicatas WHERE venda_id = ? AND status = 'aberto'
                """,
                    (venda_id,),
                )
                count_abertas = cursor.fetchone()[0] or 0

                cursor.execute(
                    """
                    SELECT COUNT(*) FROM duplicatas_pagas WHERE venda_id = ?
                """,
                    (venda_id,),
                )
                count_pagas = cursor.fetchone()[0] or 0

                total = count_abertas + count_pagas
                self._parcelas_cache[venda_id] = total if total > 0 else 1

            conn.close()

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
            status_item.setForeground(QBrush(QColor(0, 150, 0)))
        elif status == "aberto":
            status_item.setForeground(QBrush(QColor(237, 145, 33)))

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
                    venc_item.setForeground(QBrush(QColor(140, 47, 47)))
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

    # ========== MÉTODOS DE AÇÃO ==========

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
        except Exception:
            return None

    def _receber_duplicata(self):
        """Processa recebimento de duplicata"""
        duplicata = self._get_duplicata_selecionada()
        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para receber")
            return

        # Verificar se já está paga
        if duplicata[7] == "pago":  # status na posição 7
            QMessageBox.warning(self, "Aviso", "Esta duplicata já está paga")
            return

        dialog = RecebimentoDialog(duplicata, self)
        if dialog.exec():
            valor_recebido, data_recebimento, forma_pagamento = dialog.get_dados()
            try:
                # Processar recebimento
                dados_duplicata_paga = self._processar_recebimento_com_retorno(
                    duplicata, valor_recebido, data_recebimento, forma_pagamento
                )

                QMessageBox.information(
                    self, "Sucesso", "Recebimento processado com sucesso!"
                )

                # Perguntar sobre impressão
                if self._confirmar_impressao():
                    self._imprimir_comprovante_direto(dados_duplicata_paga)

                # Recarregar dados
                self._recarregar_dados_apos_recebimento()

            except Exception as e:
                QMessageBox.critical(
                    self, "Erro", f"Erro ao processar recebimento: {e!s}"
                )

    def _processar_recebimento_com_retorno(
        self, duplicata, valor_recebido, data_recebimento, forma_pagamento
    ):
        """Processa recebimento e retorna dados da duplicata paga"""
        duplicata_id = duplicata[0]
        venda_id = duplicata[2]
        cliente_id = duplicata[1]
        numero_parcela = duplicata[3]
        valor_original = duplicata[4]
        data_vencimento = duplicata[5]

        # Processar o recebimento
        success = Duplicata.marcar_como_paga(
            duplicata_id, valor_recebido, data_recebimento, forma_pagamento
        )

        if not success:
            raise ErroERP("Falha ao processar recebimento")

        # Buscar dados para comprovante
        conn = Database().get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.nome, c.cpf_cnpj, c.endereco, v.total, v.data_venda
            FROM clientes c
            LEFT JOIN vendas v ON v.cliente_id = c.id
            WHERE c.id = ? AND v.id = ?
        """,
            (cliente_id, venda_id),
        )

        cliente_venda = cursor.fetchone()
        conn.close()

        if not cliente_venda:
            raise ErroERP("Dados do cliente/venda não encontrados")

        # Montar dados para comprovante
        dados_comprovante = {
            "id": duplicata_id,
            "venda_id": venda_id,
            "cliente_id": cliente_id,
            "numero_parcela": numero_parcela,
            "valor_original": float(valor_original),
            "valor_recebido": float(valor_recebido),
            "data_vencimento": data_vencimento,
            "data_pagamento": data_recebimento,
            "forma_pagamento": forma_pagamento,
            "cliente_nome": cliente_venda[0],
            "cpf_cnpj": cliente_venda[1],
            "endereco": cliente_venda[2],
            "venda_total": float(cliente_venda[3]) if cliente_venda[3] else 0,
            "data_venda": cliente_venda[4],
        }

        return dados_comprovante

    def _recarregar_dados_apos_recebimento(self):
        """Recarrega dados após recebimento - otimizado"""
        # Atualizar cache localmente primeiro
        duplicata_selecionada = self._get_duplicata_selecionada()
        venda_id = (
            duplicata_selecionada[2] if duplicata_selecionada is not None else None
        )

        if venda_id and venda_id in self._parcelas_cache:
            # Atualizar contagem no cache
            self._parcelas_cache[venda_id] += 1

        # Recarregar apenas se necessário
        self._carregar_duplicatas()

    def _imprimir_comprovante_direto(self, dados_duplicata):
        """Imprime comprovante usando dados diretos"""
        try:
            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados_duplicata, "relatorios"
            )
            if filename:
                if ExportUtils.abrir_arquivo(filename):
                    logger.info("Comprovante de recebimento gerado")
                else:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"Comprovante salvo em:\n{filename}\n\nNão foi possível abrir automaticamente.",
                    )
            else:
                QMessageBox.warning(
                    self, "Erro", "Não foi possível gerar o comprovante."
                )

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar comprovante: {e!s}")

    def _confirmar_impressao(self):
        """Confirma se usuário quer imprimir comprovante"""
        resposta = QMessageBox.question(
            self,
            "Imprimir Comprovante",
            "Deseja imprimir o comprovante de pagamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _imprimir_relatorio(self):
        """Imprime relatório de recebimentos"""
        try:
            status_filtro = self._get_status_selecionado()
            data_inicio_str = self.data_inicio.text().strip()
            data_fim_str = self.data_fim.text().strip()

            cliente_id = None

            if data_inicio_str and not validar_data(data_inicio_str):
                QMessageBox.warning(self, "Aviso", "Data inicial inválida")
                return
            if data_fim_str and not validar_data(data_fim_str):
                QMessageBox.warning(self, "Aviso", "Data final inválida")
                return

            filename = PrintRelatRecebimento.gerar_relatorio(
                data_inicio_str, data_fim_str, status_filtro, cliente_id, "relatorios"
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
                self, "Erro na Exportação", f"Erro ao exportar relatório:\n{e!s}"
            )

    # ========== MÉTODOS DE VALIDAÇÃO ==========

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

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def get_status_selecionado(self):
        """Método público para compatibilidade"""
        return self._get_status_selecionado()

    def selecionar_cliente(self):
        """Método público para compatibilidade"""
        dialog = ClienteSelectionDialog(self)
        if dialog.exec():
            cliente_selecionado = dialog.get_cliente_selecionado()
            if cliente_selecionado:
                self.busca_cliente.setText(cliente_selecionado.nome)

    def carregar_duplicatas(self):
        """Método público para compatibilidade"""
        self._carregar_duplicatas()

    def filtrar_duplicatas(self):
        """Método público para compatibilidade"""
        self._filtrar_duplicatas_otimizado()

    def exibir_duplicatas(self, duplicatas):
        """Método público para compatibilidade"""
        self._exibir_duplicatas_otimizado(duplicatas)

    def limpar_filtros(self):
        """Método público para compatibilidade"""
        self._limpar_filtros()

    def get_duplicata_selecionada(self):
        """Método público para compatibilidade"""
        return self._get_duplicata_selecionada()

    def receber_duplicata(self):
        """Método público para compatibilidade"""
        self._receber_duplicata()

    def processar_recebimento(
        self, duplicata, valor_recebido, data_recebimento, forma_pagamento
    ):
        """Método público para compatibilidade"""
        self._processar_recebimento_com_retorno(
            duplicata, valor_recebido, data_recebimento, forma_pagamento
        )

    def imprimir_comprovante(self, duplicata=None):
        """Método público para compatibilidade"""
        # Método simplificado para compatibilidade
        if duplicata is None:
            duplicata = self._get_duplicata_selecionada()

        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para imprimir")
            return

        # Lógica básica de impressão
        try:
            dados = {
                "id": duplicata[0],
                "venda_id": duplicata[2],
                "cliente_id": duplicata[1],
                "numero_parcela": duplicata[3],
                "valor_original": float(duplicata[4]),
                "valor_recebido": float(duplicata[4]),
                "data_vencimento": duplicata[5],
                "data_pagamento": duplicata[6] if len(duplicata) > 6 else None,
                "forma_pagamento": (
                    duplicata[11] if len(duplicata) > 11 else "Não informada"
                ),
                "cliente_nome": duplicata[8],
                "cpf_cnpj": "",
                "endereco": "",
                "venda_total": float(duplicata[9]) if len(duplicata) > 9 else 0,
                "data_venda": duplicata[10] if len(duplicata) > 10 else None,
            }

            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados, "relatorios"
            )
            if filename:
                ExportUtils.abrir_arquivo(filename)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao imprimir: {e!s}")

    def imprimir_relatorio(self):
        """Método público para compatibilidade"""
        self._imprimir_relatorio()

    def atualizar_apos_venda(self, cliente_id):
        """Atualiza após venda no crediário"""
        self._carregar_duplicatas()

    def atualizar_tabela_apos_recebimento(self, duplicata_id):
        """Atualiza tabela após recebimento"""
        self._carregar_duplicatas()

    def atualizar_tabela(self):
        """Método público para atualizar a tabela"""
        self._carregar_duplicatas()
