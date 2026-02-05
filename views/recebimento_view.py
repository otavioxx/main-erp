"""
View de Recebimentos - Otimizada com layout consistente ao CondicionalView
"""

import os
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


class RecebimentoView(TableScrollNavigationMixin, QWidget):
    """View de gestão de recebimentos otimizada"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cliente_filtro = None
        self.duplicatas_filtradas = []
        self.ultima_duplicata_paga = None
        self.todas_duplicatas = []
        self._init_ui()
        self._carregar_duplicatas()
        criar_pasta_se_nao_existir("relatorios")

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
        self.label_info = QLabel("(Duplicatas abertas)")
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
        self.busca_cliente.textChanged.connect(self._filtrar_duplicatas)
        filtro_layout.addWidget(self.busca_cliente)

        # ComboBox de status (após busca de cliente)
        filtro_layout.addWidget(QLabel("Status:"))

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Abertas", "Vencidas", "Pagas", "Todas"])
        self.combo_status.setCurrentText("Abertas")
        self.combo_status.setMaximumWidth(120)
        self.combo_status.currentTextChanged.connect(self._filtrar_duplicatas)
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
        self.data_inicio.textChanged.connect(self._filtrar_duplicatas)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.textChanged.connect(self._filtrar_duplicatas)
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
        """Configura tabela de duplicatas"""
        self.tabela_duplicatas = QTableWidget()
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
                "Pagamento",  # MUDANÇA: Status movido para posição 2
            ]
        )

        # Configuração das colunas
        header = self.tabela_duplicatas.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cliente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Status - MOVIDO
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Venda
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Parcela
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Valor
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Vencimento
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)  # Pagamento

        # Larguras das colunas - AJUSTADAS
        larguras = [50, 180, 80, 60, 60, 80, 100, 100]  # Status agora na posição 2
        for i, largura in enumerate(larguras):
            self.tabela_duplicatas.setColumnWidth(i, largura)

        # Configurações gerais (sem mudanças)
        self.tabela_duplicatas.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_duplicatas.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_duplicatas.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_duplicatas.setAlternatingRowColors(True)
        self.tabela_duplicatas.verticalHeader().setVisible(False)
        self.tabela_duplicatas.verticalHeader().setDefaultSectionSize(18)
        self.tabela_duplicatas.setSortingEnabled(True)

        self.setup_scroll_navigation(
            tabela=self.tabela_duplicatas,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    def _debug_selecao(self):
        """Método de debug para verificar seleção"""
        row = self.tabela_duplicatas.currentRow()
        selected_items = self.tabela_duplicatas.selectedItems()
        print(f"DEBUG - Linha atual: {row}, Items selecionados: {len(selected_items)}")

    # ========== MÉTODOS DE DADOS ==========

    def _get_status_selecionado(self):
        """Retorna status selecionado no ComboBox"""
        return self.combo_status.currentText()

    def _carregar_duplicatas(self):
        """Carrega duplicatas do banco"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Duplicatas abertas
            query_abertas = """
                SELECT
                    d.id, d.cliente_id, d.venda_id, d.numero_parcela,
                    d.valor_parcela, d.data_vencimento, d.data_pagamento,
                    d.status, c.nome as cliente_nome, v.total as venda_total,
                    v.data_venda
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                LEFT JOIN vendas v ON d.venda_id = v.id
                WHERE d.status = 'aberto'
                ORDER BY d.data_vencimento
            """

            cursor.execute(query_abertas)
            duplicatas_abertas = cursor.fetchall()

            # Duplicatas pagas
            query_pagas = """
                SELECT
                    dp.id, dp.cliente_id, dp.venda_id, dp.numero_parcela,
                    dp.valor_original, dp.valor_recebido, dp.data_vencimento,
                    dp.data_pagamento, dp.forma_pagamento,
                    c.nome as cliente_nome, c.cpf_cnpj, c.endereco,
                    v.total as venda_total, v.data_venda,
                    'pago' AS status
                FROM duplicatas_pagas dp
                LEFT JOIN clientes c ON dp.cliente_id = c.id
                LEFT JOIN vendas v ON dp.venda_id = v.id
                ORDER BY dp.data_pagamento DESC
            """

            cursor.execute(query_pagas)
            duplicatas_pagas = cursor.fetchall()

            self.todas_duplicatas = duplicatas_abertas + duplicatas_pagas
            self._filtrar_duplicatas()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar duplicatas: {str(e)}")
        finally:
            if "conn" in locals():
                conn.close()

    def _filtrar_duplicatas(self):
        """Filtra duplicatas baseado nos critérios - MÉTODO CORRIGIDO"""
        if not hasattr(self, "todas_duplicatas"):
            return

        status_filtro = self._get_status_selecionado()
        data_inicio_str = self.data_inicio.text().strip()
        data_fim_str = self.data_fim.text().strip()
        cliente_nome_busca = self.busca_cliente.text().strip().lower()

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

        # Converter datas
        data_inicio = None
        data_fim = None

        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()

        duplicatas_filtradas = []

        for dup in self.todas_duplicatas:
            # Identificar tipo de duplicata
            is_paga = len(dup) == 15

            if is_paga:
                status = "pago"
                data_vencimento = dup[6]
                data_pagamento = dup[7]
                cliente_id = dup[1]
                cliente_nome = dup[9]  # Índice correto para duplicatas pagas
            else:
                status = dup[7]
                data_vencimento = dup[5]
                data_pagamento = dup[6]
                cliente_id = dup[1]
                cliente_nome = dup[8]  # Índice correto para duplicatas abertas

            # Filtro de status
            status_ok = self._validar_status_filtro(
                status_filtro, status, data_vencimento
            )
            if not status_ok:
                continue

            # Filtro por nome de cliente (CORRIGIDO)
            if cliente_nome_busca:
                nome_cliente_atual = str(cliente_nome).lower() if cliente_nome else ""
                if cliente_nome_busca not in nome_cliente_atual:
                    continue

            # Filtro de data
            if not self._validar_data_filtro(
                status, data_vencimento, data_pagamento, data_inicio, data_fim
            ):
                continue

            duplicatas_filtradas.append(dup)

        # Ordenar
        self._ordenar_duplicatas(duplicatas_filtradas)

        self.duplicatas_filtradas = duplicatas_filtradas
        self._exibir_duplicatas(duplicatas_filtradas)
        self._atualizar_label_info()

    def _atualizar_label_info(self):
        """Atualiza label informativo baseado nos filtros"""
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

    def _validar_status_filtro(self, status_filtro, status, data_vencimento):
        """Valida se duplicata atende filtro de status"""
        if status_filtro == "Abertas" and status == "aberto":
            return True
        elif status_filtro == "Vencidas" and status == "aberto":
            if data_vencimento:
                try:
                    data_venc = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
                    return data_venc < datetime.now().date()
                except (ValueError, TypeError):
                    pass
        elif status_filtro == "Pagas" and status == "pago":
            return True
        elif status_filtro == "Todas":
            return True
        return False

    def _validar_data_filtro(
        self, status, data_vencimento, data_pagamento, data_inicio, data_fim
    ):
        """Valida se duplicata atende filtro de data"""
        data_referencia = data_vencimento if status == "aberto" else data_pagamento

        if data_referencia and isinstance(data_referencia, str):
            try:
                data_ref = datetime.strptime(data_referencia, "%Y-%m-%d").date()

                if data_inicio and data_ref < data_inicio:
                    return False

                if data_fim and data_ref > data_fim:
                    return False

            except (ValueError, TypeError):
                return False

        return True

    def _ordenar_duplicatas(self, duplicatas_filtradas):
        """Ordena duplicatas por data"""
        try:
            duplicatas_filtradas.sort(
                key=lambda d: (
                    datetime.strptime(d[6] if len(d) == 15 else d[5], "%Y-%m-%d").date()
                    if (d[6] if len(d) == 15 else d[5])
                    and isinstance((d[6] if len(d) == 15 else d[5]), str)
                    else datetime.max.date()
                )
            )
        except Exception:
            duplicatas_filtradas.sort(key=lambda d: d[0])

    def _exibir_duplicatas(self, duplicatas):
        """Exibe duplicatas na tabela"""
        self.tabela_duplicatas.setRowCount(len(duplicatas))

        for row, dup in enumerate(duplicatas):
            self._preencher_linha_tabela(row, dup)

    def _preencher_linha_tabela(self, row, dup):
        """Preenche uma linha da tabela - COM FORMATO DE PARCELA CORRIGIDO"""
        is_paga = len(dup) == 15

        if is_paga:
            (
                id_dup,
                cliente_id,
                venda_id,
            ) = (
                dup[0],
                dup[1],
                dup[2],
            )
            cliente_nome, numero_parcela = dup[9], dup[3]
            valor, data_vencimento = dup[4], dup[6]
            data_pagamento, status = dup[7], "pago"
        else:
            id_dup, cliente_id, venda_id = dup[0], dup[1], dup[2]
            cliente_nome, numero_parcela = dup[8], dup[3]
            valor, data_vencimento = dup[4], dup[5]
            data_pagamento, status = dup[6], dup[7]

        # NOVO: Buscar total de parcelas da venda para exibir formato "1/3"
        total_parcelas = self._get_total_parcelas_venda(venda_id)
        parcela_formatada = (
            f"{numero_parcela}/{total_parcelas}"
            if total_parcelas
            else str(numero_parcela)
        )

        # Preencher células - ÍNDICES AJUSTADOS
        items = [
            (0, str(id_dup), Qt.AlignmentFlag.AlignCenter),
            (1, str(cliente_nome) if cliente_nome else "N/A", None),
            # Status agora na posição 2 - será preenchido separadamente
            (3, str(venda_id), Qt.AlignmentFlag.AlignCenter),
            (
                4,
                parcela_formatada,
                Qt.AlignmentFlag.AlignCenter,
            ),  # MUDANÇA: usar parcela_formatada
            (
                5,
                formatar_moeda(float(valor)) if valor else "0.00",
                (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
            ),
        ]

        for col, text, align in items:
            item = QTableWidgetItem(text)
            if align:
                item.setTextAlignment(align)
            self.tabela_duplicatas.setItem(row, col, item)

        # Status na posição 2 - NOVO
        self._preencher_status(row, status)

        # Vencimento com cor especial - MUDANÇA: de posição 5 para 6
        self._preencher_vencimento(row, data_vencimento, status)

        # Pagamento - MUDANÇA: de posição 6 para 7
        pagamento = (
            formatar_data(data_pagamento, "%Y-%m-%d", "%d/%m/%Y")
            if data_pagamento
            else "N/A"
        )
        pag_item = QTableWidgetItem(pagamento)
        pag_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabela_duplicatas.setItem(row, 7, pag_item)

    def _get_total_parcelas_venda(self, venda_id):
        """Obtém o total de parcelas de uma venda - MÉTODO NOVO"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Buscar nas duplicatas abertas
            cursor.execute(
                """
                SELECT COUNT(*) FROM duplicatas WHERE venda_id = ?
            """,
                (venda_id,),
            )

            count_abertas = cursor.fetchone()[0]

            # Buscar nas duplicatas pagas
            cursor.execute(
                """
                SELECT COUNT(*) FROM duplicatas_pagas WHERE venda_id = ?
            """,
                (venda_id,),
            )

            count_pagas = cursor.fetchone()[0]

            conn.close()

            total = count_abertas + count_pagas
            return total if total > 0 else 1  # Fallback para 1 se não encontrar

        except Exception as e:
            print(f"Erro ao buscar total de parcelas: {e}")
            return 1  # Fallback para 1 em caso de erro

    def _preencher_vencimento(self, row, data_vencimento, status):
        """Preenche coluna de vencimento com cores - APENAS a coluna quando vencida"""
        vencimento = (
            formatar_data(data_vencimento, "%Y-%m-%d", "%d/%m/%Y")
            if data_vencimento
            else "N/A"
        )
        venc_item = QTableWidgetItem(vencimento)
        venc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Aplicar cor vermelha APENAS na coluna de vencimento para duplicatas vencidas
        if status == "aberto" and data_vencimento:
            try:
                data_venc = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
                if data_venc < datetime.now().date():
                    # Cor vermelha apenas para esta célula
                    venc_item.setForeground(
                        QBrush(QColor(140, 47, 47))
                    )  # Vermelho mais forte
                    # Opcional: deixar em negrito para maior destaque
                    font = venc_item.font()
                    font.setBold(True)
                    venc_item.setFont(font)
            except (ValueError, TypeError):
                pass

        self.tabela_duplicatas.setItem(row, 6, venc_item)

    def _preencher_status(self, row, status):
        """Preenche coluna de status com cores"""
        status_item = QTableWidgetItem(status.capitalize())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if status == "pago":
            status_item.setForeground(QBrush(QColor(0, 150, 0)))  # Verde mais escuro
        elif status == "aberto":
            status_item.setForeground(
                QBrush(QColor(237, 145, 33))
            )  # Amarelo mais escuro

        self.tabela_duplicatas.setItem(row, 2, status_item)

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
        self._filtrar_duplicatas()

    def _get_duplicata_selecionada(self):
        """Retorna duplicata selecionada"""
        row = self.tabela_duplicatas.currentRow()
        if row == -1:
            return None

        try:
            duplicata_id = int(self.tabela_duplicatas.item(row, 0).text())
            for dup in self.duplicatas_filtradas:
                if dup[0] == duplicata_id:
                    return dup
            return None
        except Exception:
            return None

    def _receber_duplicata(self):
        """Processa recebimento de duplicata - VERSÃO CORRIGIDA"""
        duplicata = self._get_duplicata_selecionada()
        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para receber")
            return

        # Verificar se é duplicata paga (não pode receber novamente)
        is_paga = len(duplicata) == 15
        if is_paga or (len(duplicata) > 7 and duplicata[7] == "pago"):
            QMessageBox.warning(self, "Aviso", "Esta duplicata já está paga")
            return

        dialog = RecebimentoDialog(duplicata, self)
        if dialog.exec():
            valor_recebido, data_recebimento, forma_pagamento = dialog.get_dados()
            try:
                # Processar recebimento e obter dados da duplicata paga
                dados_duplicata_paga = self._processar_recebimento_com_retorno(
                    duplicata, valor_recebido, data_recebimento, forma_pagamento
                )

                QMessageBox.information(
                    self, "Sucesso", "Recebimento processado com sucesso!"
                )

                # Perguntar sobre impressão
                if self._confirmar_impressao():
                    self._imprimir_comprovante_direto(dados_duplicata_paga)

                self._carregar_duplicatas()

            except Exception as e:
                QMessageBox.critical(
                    self, "Erro", f"Erro ao processar recebimento: {str(e)}"
                )

    def _processar_recebimento_com_retorno(
        self, duplicata, valor_recebido, data_recebimento, forma_pagamento
    ):
        """Processa recebimento e retorna dados da duplicata paga"""
        try:
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
                raise Exception("Falha ao processar recebimento")

            # Buscar dados do cliente para o comprovante
            try:
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
                    raise Exception("Dados do cliente/venda não encontrados")

                # Montar dados completos para o comprovante
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

            except Exception as e:
                raise Exception(f"Erro ao buscar dados complementares: {str(e)}")

        except Exception as e:
            raise e

    def _imprimir_comprovante_direto(self, dados_duplicata):
        """Imprime comprovante usando dados diretos da duplicata"""
        try:
            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados_duplicata, "relatorios"
            )
            if filename:
                try:
                    if ExportUtils.abrir_arquivo(filename):
                        print(f"Comprovante gerado e aberto: {filename}")
                    else:
                        QMessageBox.information(
                            self,
                            "Sucesso",
                            f"Comprovante salvo em:\n{filename}\n\nNão foi possível abrir automaticamente.",
                        )
                except Exception as e:
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
            QMessageBox.critical(self, "Erro", f"Erro ao gerar comprovante: {str(e)}")

    def _confirmar_impressao(self):
        """Confirma se usuário quer imprimir comprovante"""
        resposta = QMessageBox.question(
            self,
            "Imprimir Comprovante",
            "Deseja imprimir o comprovante de pagamento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _imprimir_comprovante_recebimento(self, duplicata):
        """Imprime comprovante de recebimento"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    dp.id, dp.venda_id, dp.cliente_id, dp.numero_parcela,
                    dp.valor_original, dp.valor_recebido, dp.data_vencimento,
                    dp.data_pagamento, dp.forma_pagamento,
                    c.nome as cliente_nome, c.cpf_cnpj, c.endereco,
                    v.total as venda_total, v.data_venda
                FROM duplicatas_pagas dp
                LEFT JOIN clientes c ON dp.cliente_id = c.id
                LEFT JOIN vendas v ON dp.venda_id = v.id
                WHERE dp.venda_id = ? AND dp.numero_parcela = ?
            """,
                (duplicata[2], duplicata[3]),
            )

            duplicata_paga = cursor.fetchone()
            conn.close()

            if duplicata_paga:
                self._imprimir_comprovante(duplicata_paga)
            else:
                QMessageBox.warning(
                    self, "Aviso", "Duplicata paga não encontrada para impressão."
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Erro", f"Erro ao buscar duplicata paga: {str(e)}"
            )

    def _imprimir_comprovante(self, duplicata=None):
        """Imprime comprovante da duplicata - VERSÃO MELHORADA"""
        if duplicata is None:
            duplicata = self._get_duplicata_selecionada()

        if not duplicata:
            QMessageBox.warning(self, "Aviso", "Selecione uma duplicata para imprimir")
            return

        try:
            # Extrair venda_id e numero_parcela corretamente
            venda_id = duplicata[2]
            numero_parcela = duplicata[3]

            # Buscar com retry para garantir que a transação foi commitada
            dados_comprovante = None
            max_tentativas = 3

            for tentativa in range(max_tentativas):
                try:
                    conn = Database().get_connection()
                    cursor = conn.cursor()

                    # Buscar primeiro na tabela de duplicatas pagas
                    cursor.execute(
                        """
                        SELECT
                            dp.id, dp.venda_id, dp.cliente_id, dp.numero_parcela,
                            dp.valor_original, dp.valor_recebido, dp.data_vencimento,
                            dp.data_pagamento, dp.forma_pagamento,
                            c.nome as cliente_nome, c.cpf_cnpj, c.endereco,
                            v.total as venda_total, v.data_venda
                        FROM duplicatas_pagas dp
                        LEFT JOIN clientes c ON dp.cliente_id = c.id
                        LEFT JOIN vendas v ON dp.venda_id = v.id
                        WHERE dp.venda_id = ? AND dp.numero_parcela = ?
                    """,
                        (venda_id, numero_parcela),
                    )

                    row = cursor.fetchone()

                    if row:
                        # Dados para duplicata paga
                        dados_comprovante = {
                            "id": row[0],
                            "venda_id": row[1],
                            "cliente_id": row[2],
                            "numero_parcela": row[3],
                            "valor_original": float(row[4]),
                            "valor_recebido": float(row[5]),
                            "data_vencimento": row[6],
                            "data_pagamento": row[7],
                            "forma_pagamento": row[8],
                            "cliente_nome": row[9],
                            "cpf_cnpj": row[10],
                            "endereco": row[11],
                            "venda_total": float(row[12]) if row[12] else 0,
                            "data_venda": row[13],
                        }
                        break
                    else:
                        # Se não encontrou na tabela de pagas, buscar na tabela de abertas
                        cursor.execute(
                            """
                            SELECT
                                d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                                d.valor_parcela, d.data_vencimento, d.data_pagamento,
                                d.status, c.nome as cliente_nome, c.cpf_cnpj, c.endereco,
                                v.total as venda_total, v.data_venda
                            FROM duplicatas d
                            LEFT JOIN clientes c ON d.cliente_id = c.id
                            LEFT JOIN vendas v ON d.venda_id = v.id
                            WHERE d.venda_id = ? AND d.numero_parcela = ?
                        """,
                            (venda_id, numero_parcela),
                        )

                        row = cursor.fetchone()

                        if row:
                            # Dados para duplicata aberta
                            dados_comprovante = {
                                "id": row[0],
                                "venda_id": row[1],
                                "cliente_id": row[2],
                                "numero_parcela": row[3],
                                "valor_original": float(row[4]),
                                "valor_recebido": float(row[4]),
                                "data_vencimento": row[5],
                                "data_pagamento": row[6],
                                "forma_pagamento": "Não informada",
                                "cliente_nome": row[8],
                                "cpf_cnpj": row[9],
                                "endereco": row[10],
                                "venda_total": float(row[11]) if row[11] else 0,
                                "data_venda": row[12],
                            }
                            break

                    conn.close()

                    # Se não encontrou em nenhuma tabela na primeira tentativa, aguardar um pouco
                    if not dados_comprovante and tentativa < max_tentativas - 1:
                        import time

                        time.sleep(0.5)  # Aguardar 500ms

                except Exception as e:
                    if "conn" in locals():
                        conn.close()
                    if tentativa == max_tentativas - 1:  # Última tentativa
                        raise e
                    import time

                    time.sleep(0.5)

            if not dados_comprovante:
                QMessageBox.warning(
                    self, "Aviso", "Duplicata não encontrada para impressão."
                )
                return

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar dados: {str(e)}")
            return

        # Gerar comprovante
        if dados_comprovante:
            filename = PrintComprovanteRecebimento.gerar_comprovante(
                dados_comprovante, "relatorios"
            )
            if filename:
                try:
                    if ExportUtils.abrir_arquivo(filename):
                        print(f"Comprovante gerado: {filename}")
                    else:
                        QMessageBox.information(
                            self,
                            "Sucesso",
                            f"Comprovante salvo em:\n{filename}\n\nNão foi possível abrir automaticamente.",
                        )
                except Exception as e:
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"Comprovante salvo em:\n{filename}\n\nNão foi possível abrir automaticamente.",
                    )
            else:
                QMessageBox.warning(
                    self, "Erro", "Não foi possível gerar o comprovante."
                )

    def _imprimir_relatorio(self):
        """Imprime relatório de recebimentos"""
        try:
            status_filtro = self._get_status_selecionado()
            data_inicio_str = self.data_inicio.text().strip()
            data_fim_str = self.data_fim.text().strip()

            cliente_id = None
            # Se houver busca por nome de cliente, não usamos cliente específico no relatório
            # O relatório vai filtrar por nome internamente

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
                self, "Erro na Exportação", f"Erro ao exportar relatório:\n{str(e)}"
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
        """Método público para compatibilidade - agora deprecated"""
        # Mantido para compatibilidade, mas agora usa busca por nome
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
        self._filtrar_duplicatas()

    def exibir_duplicatas(self, duplicatas):
        """Método público para compatibilidade"""
        self._exibir_duplicatas(duplicatas)

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
        self._processar_recebimento(
            duplicata, valor_recebido, data_recebimento, forma_pagamento
        )

    def imprimir_comprovante(self, duplicata=None):
        """Método público para compatibilidade"""
        self._imprimir_comprovante(duplicata)

    def imprimir_relatorio(self):
        """Método público para compatibilidade"""
        self._imprimir_relatorio()

    def atualizar_apos_venda(self, cliente_id):
        """Atualiza após venda no crediário"""
        self._carregar_duplicatas()

    def atualizar_tabela_apos_recebimento(self, duplicata_id):
        """Atualiza tabela após recebimento"""
        self._carregar_duplicatas()
