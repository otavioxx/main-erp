from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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
from dialogs.condicional_dialog import CondicionalDialog
from dialogs.relatorio_condicional_dialog import RelatorioCondicionalDialog
from dialogs.venda_dialog import ProdutoVendaDialog
from imprecoes.print_condicional import PrintCondicional
from imprecoes.print_relat_condicional import PrintRelatCondicional
from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.condicional import Condicional
from utils.export_utils import ExportUtils
from utils.helpers import (
    criar_pasta_se_nao_existir,
    formatar_moeda,
    validar_data,
)


# ========== CORREÇÃO: Classe para ordenação numérica ==========
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


class CondicionalView(TableScrollNavigationMixin, QWidget):
    """Interface de gestão de condicionais otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.cliente_filtro = None
        self.dados = []
        self._init_ui()
        self._carregar_condicionais()
        criar_pasta_se_nao_existir("relatorios")

    def _init_ui(self):
        """Inicializa a interface com classes CSS semânticas"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header com título
        self._criar_header(layout)

        # Grupo de filtros
        self._criar_grupo_filtros(layout)

        # Grupo de ações
        self._criar_grupo_acoes(layout)

        # Grupo de condicionais (tabela)
        self._criar_grupo_condicionais(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestão de Condicionais")
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
        """Cria o grupo de filtros com layout similar ao VendaView"""
        grupo_filtros = QGroupBox("Filtros")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Busca por cliente (lado esquerdo)
        self.busca_cliente = QLineEdit()
        self.busca_cliente.setPlaceholderText("Buscar por Nome do cliente...")
        self.busca_cliente.setMaximumWidth(300)
        self.busca_cliente.textChanged.connect(self._filtrar_condicionais)
        filtro_layout.addWidget(self.busca_cliente)

        # ComboBox de status (após busca de cliente)
        filtro_layout.addWidget(QLabel("Status:"))

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Todos", "Ativas", "Convertidas", "Devolvidas"])
        self.combo_status.setCurrentText("Ativas")
        self.combo_status.setMaximumWidth(120)
        self.combo_status.currentTextChanged.connect(self._filtrar_condicionais)
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
        self.data_inicio.textChanged.connect(self._filtrar_condicionais)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.data_fim.textChanged.connect(self._filtrar_condicionais)
        layout.addWidget(self.data_fim)

    def _criar_grupo_acoes(self, layout):
        """Cria o grupo de ações com botões semânticos"""
        grupo_acoes = QGroupBox("Ações")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões principais (esquerda)
        self.btn_nova_condicional = QPushButton("Nova Condicional")
        self.btn_nova_condicional.setProperty("class", "success")
        self.btn_nova_condicional.clicked.connect(self._abrir_nova_condicional)

        self.btn_editar_condicional = QPushButton("Editar")
        self.btn_editar_condicional.setProperty("class", "secondary")
        self.btn_editar_condicional.clicked.connect(self._editar_condicional)

        self.btn_converter_venda = QPushButton("Converter em Venda")
        self.btn_converter_venda.setProperty("class", "primary")
        self.btn_converter_venda.clicked.connect(self._converter_em_venda)

        self.btn_marcar_devolvida = QPushButton("Marcar Devolvida")
        self.btn_marcar_devolvida.setProperty("class", "warning")
        self.btn_marcar_devolvida.clicked.connect(self._marcar_como_devolvida)

        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setProperty("class", "danger")
        self.btn_excluir.clicked.connect(self._excluir_condicional)

        btn_layout.addWidget(self.btn_nova_condicional)
        btn_layout.addWidget(self.btn_editar_condicional)
        btn_layout.addWidget(self.btn_converter_venda)
        btn_layout.addWidget(self.btn_marcar_devolvida)
        btn_layout.addWidget(self.btn_excluir)
        btn_layout.addStretch()

        # Botões de relatório (direita)
        self.btn_imprimir = QPushButton("Imprimir Condicional")
        self.btn_imprimir.setProperty("class", "warning")
        self.btn_imprimir.clicked.connect(self._imprimir_condicional)

        self.btn_exportar = QPushButton("Imprimir Relatório")
        self.btn_exportar.setProperty("class", "primary")
        self.btn_exportar.clicked.connect(self._exportar_condicionais)

        btn_layout.addWidget(self.btn_imprimir)
        btn_layout.addWidget(self.btn_exportar)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_condicionais(self, layout):
        """Cria a tabela de condicionais com configuração otimizada"""
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

        titulo = QLabel("Condicionais")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_condicionais = QTableWidget()
        self._configurar_tabela_condicionais()
        container_layout.addWidget(self.tabela_condicionais)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_condicionais(self):
        """Configura a tabela de condicionais - VERSÃO COM ALTURA FIXA"""
        self.tabela_condicionais.setColumnCount(7)  # Aumentei para 7 colunas
        self.tabela_condicionais.setHorizontalHeaderLabels(
            [
                "ID",
                "Cliente",
                "Data",
                "Prev. Devolução",
                "Itens",
                "Desconto",
                "Valor Total",
            ]
        )

        # Configuração das colunas
        header = self.tabela_condicionais.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cliente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Data
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Prev. Devolução
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Itens
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Desconto
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Total

        # Larguras otimizadas
        larguras_colunas = [50, 100, 200, 120, 60, 80, 100]
        for i, largura in enumerate(larguras_colunas):
            if largura > 0:  # Aplica apenas larguras positivas
                self.tabela_condicionais.setColumnWidth(i, largura)

        # ========== CONFIGURAÇÃO DE ALTURA ==========
        # Configurar VERTICAL HEADER para altura fixa
        vheader = self.tabela_condicionais.verticalHeader()
        altura_desejada = 22

        vheader.setDefaultSectionSize(altura_desejada)
        vheader.setMinimumSectionSize(altura_desejada)
        vheader.setMaximumSectionSize(altura_desejada)
        vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vheader.setCascadingSectionResizes(False)
        vheader.setStretchLastSection(False)
        vheader.setVisible(False)

        # Função para aplicar altura quando dados forem carregados
        def aplicar_altura_quando_necessario():
            try:
                if hasattr(self, "tabela_condicionais") and self.tabela_condicionais:
                    for row in range(self.tabela_condicionais.rowCount()):
                        self.tabela_condicionais.setRowHeight(row, altura_desejada)
            except:
                pass

        # Conectar ao sinal de dados alterados (quando a tabela for populada)
        try:
            if hasattr(self.tabela_condicionais, "model"):
                model = self.tabela_condicionais.model()
                model.rowsInserted.connect(
                    lambda parent, first, last: aplicar_altura_quando_necessario()
                )
        except:
            pass
        # ========== FIM DA CONFIGURAÇÃO ==========

        # Configurações gerais da tabela
        self.tabela_condicionais.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_condicionais.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_condicionais.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabela_condicionais.setAlternatingRowColors(True)
        self.tabela_condicionais.setSortingEnabled(True)

        self.setup_scroll_navigation(
            tabela=self.tabela_condicionais,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    # ========== MÉTODOS DE CARREGAMENTO E FILTROS ==========

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
                    if self._parse_data(c[2])
                    and data_ini <= self._parse_data(c[2]) <= data_fim
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
            cor_laranja = QColor(237, 145, 33)  # Laranja
            for col in range(self.tabela_condicionais.columnCount()):
                item = self.tabela_condicionais.item(row, col)
                if item:
                    item.setForeground(cor_laranja)

        # Para condicionais convertidas - linha toda verde
        elif condicional.status == "convertida":
            cor_verde = QColor(0, 128, 0)  # Verde
            for col in range(self.tabela_condicionais.columnCount()):
                item = self.tabela_condicionais.item(row, col)
                if item:
                    item.setForeground(cor_verde)

        # Para condicionais ativas e vencidas - APENAS a coluna de data prevista em vermelho
        elif condicional.status == "ativa" and condicional.esta_vencida():
            cor_vermelha = QColor(140, 47, 47)  # Vermelho

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
        except:
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

    # ========== MÉTODOS DE AÇÕES ==========

    def _selecionar_cliente(self):
        """Abre dialog para seleção de cliente para filtro"""
        try:
            dialog = ClienteSelectionDialog(self)
            if dialog.exec():
                cliente_selecionado = dialog.get_cliente_selecionado()
                if cliente_selecionado:
                    self.cliente_filtro = cliente_selecionado
                    self.busca_cliente.setText(cliente_selecionado.nome)
                    self._filtrar_condicionais()
                else:
                    self.cliente_filtro = None
                    self.busca_cliente.clear()
                    self._filtrar_condicionais()
        except Exception as e:
            self._mostrar_erro("Erro ao selecionar cliente", str(e))

    def _abrir_nova_condicional(self):
        """Abre dialog para nova condicional"""
        dialog = CondicionalDialog(None, self)
        dialog.condicional_salva.connect(self._carregar_condicionais)
        dialog.exec()

    def _get_condicional_selecionada(self):
        """Obtém a condicional selecionada na tabela"""
        row = self.tabela_condicionais.currentRow()
        if row == -1:
            return None

        try:
            condicional_id_item = self.tabela_condicionais.item(row, 0)
            if condicional_id_item is None:
                return None

            condicional_id = int(condicional_id_item.text())
            return Condicional.buscar_por_id(condicional_id)
        except (ValueError, AttributeError):
            return None

    def _editar_condicional(self):
        """Edita a condicional selecionada - apenas condicionais ativas podem ser editadas"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para editar")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                f"Só é possível editar condicionais com status 'Ativa'.\n"
                f"Status atual: {condicional.status.capitalize()}"
            )
            return

        try:
            dialog = CondicionalDialog(condicional.id, self)
            dialog.condicional_salva.connect(self._carregar_condicionais)
            dialog.exec()
        except Exception as e:
            self._mostrar_erro("Erro ao abrir edição de condicional", str(e))

    def _converter_em_venda(self):
        """Converte a condicional selecionada em uma venda"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para converter em venda")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                "Apenas condicionais ativas podem ser convertidas em venda"
            )
            return

        if not condicional.itens:
            self._mostrar_aviso("A condicional não possui itens para venda")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Conversão",
            f"Converter condicional #{condicional.id} em venda?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}\n"
            f"Total: {formatar_moeda(condicional.calcular_total())}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                dialog = ProdutoVendaDialog(self)

                # Configurar cliente na venda
                from models.cliente import Cliente

                cliente = Cliente.buscar_por_id(condicional.cliente_id)
                if cliente:
                    dialog.cliente_selecionado = cliente
                    dialog.label_cliente.setText(cliente.nome)

                # Adicionar produtos da condicional
                from models.produto import Produto

                for item in condicional.itens:
                    produto = Produto.buscar_por_id(item["produto_id"])
                    if produto:
                        dialog.adicionar_produto(produto, item["quantidade"])

                if dialog.exec():
                    condicional.marcar_como_convertida()
                    self._carregar_condicionais()
                    self._mostrar_sucesso(
                        "Condicional convertida em venda com sucesso!"
                    )

            except Exception as e:
                self._mostrar_erro("Erro ao converter condicional", str(e))

    def _marcar_como_devolvida(self):
        """Marca a condicional selecionada como devolvida"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para marcar como devolvida")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                "Apenas condicionais ativas podem ser marcadas como devolvidas"
            )
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Devolução",
            f"Marcar condicional #{condicional.id} como devolvida?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                condicional.marcar_como_devolvida()
                self._carregar_condicionais()
                self._mostrar_sucesso("Condicional marcada como devolvida!")
            except Exception as e:
                self._mostrar_erro("Erro ao marcar condicional", str(e))

    def _excluir_condicional(self):
        """Exclui a condicional selecionada - apenas condicionais em aberto podem ser excluídas"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para excluir")
            return

        if condicional.status != "ativa":
            self._mostrar_aviso(
                f"Apenas condicionais em aberto podem ser excluídas.\n"
                f"Esta condicional está com status: {condicional.status.capitalize()}"
            )
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Excluir condicional #{condicional.id}?\n"
            f"Cliente: {self._get_nome_cliente(condicional.cliente_id)}\n"
            f"Itens: {len(condicional.itens)}\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            try:
                conn = Database().get_connection()
                cursor = conn.cursor()

                # Excluir itens da condicional
                cursor.execute(
                    "DELETE FROM itens_condicional WHERE condicional_id = ?",
                    (condicional.id,),
                )

                # Excluir a condicional
                cursor.execute(
                    "DELETE FROM condicionais WHERE id = ?", (condicional.id,)
                )

                conn.commit()
                conn.close()

                self._carregar_condicionais()
                self.tabela_condicionais.clearSelection()
                self._mostrar_sucesso("Condicional excluída com sucesso!")

            except Exception as e:
                self._mostrar_erro("Erro ao excluir condicional", str(e))

    def _exportar_condicionais(self):
        """Abre diálogo para selecionar filtros e exporta relatório"""
        dialog = RelatorioCondicionalDialog(self)
        if dialog.exec():
            filtros = dialog.get_filtros()
            self._gerar_relatorio_com_filtros(filtros)

    def _gerar_relatorio_com_filtros(self, filtros):
        """Gera relatório com base nos filtros selecionados"""
        try:
            data_inicio = filtros["data_inicio"]
            data_fim = filtros["data_fim"]
            cliente_id = filtros["cliente_id"]
            status = filtros["status"]

            # Validar datas
            if not self._validar_data(data_inicio) or not self._validar_data(data_fim):
                self._mostrar_aviso("Datas inválidas. Use o formato DD/MM/AAAA")
                return

            # CORREÇÃO: Usar a versão corrigida do PrintRelatCondicional
            filename = PrintRelatCondicional.gerar_relatorio_por_periodo(
                data_inicio, data_fim, status, cliente_id, "relatorios"
            )

            self._tratar_arquivo_gerado(filename, "Relatório exportado")

        except Exception as e:
            self._mostrar_erro(
                "Erro na Exportação",
                f"Ocorreu um erro ao exportar as condicionais:\n{e!s}",
            )

    def _validar_data(self, data_str):
        """Valida formato de data DD/MM/YYYY"""
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def _imprimir_condicional(self):
        """Imprime comprovante da condicional selecionada"""
        condicional = self._get_condicional_selecionada()
        if not condicional:
            self._mostrar_aviso("Selecione uma condicional para imprimir")
            return

        try:
            filename = PrintCondicional.gerar_comprovante(condicional.id, "relatorios")
            self._tratar_arquivo_gerado(filename, "Comprovante gerado")

        except Exception as e:
            self._mostrar_erro(
                "Erro na Impressão",
                f"Ocorreu um erro ao gerar o comprovante:\n{e!s}",
            )

    def _tratar_arquivo_gerado(self, filename, mensagem_sucesso):
        """Trata arquivo gerado (relatório ou comprovante)"""
        if filename and ExportUtils.abrir_arquivo(filename):
            self._mostrar_sucesso(f"{mensagem_sucesso}:\n{filename}")
        else:
            self._mostrar_aviso(
                f"Arquivo salvo em: {filename}\nNão foi possível abrir automaticamente."
            )

    def _get_nome_cliente(self, cliente_id):
        """Obtém o nome do cliente pelo ID"""
        if not cliente_id:
            return "Cliente não informado"

        conn = Database().get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
            result = cursor.fetchone()
            return result[0] if result else "Cliente não encontrado"
        finally:
            conn.close()

    # ========== MÉTODOS DE INTERFACE ==========

    def _mostrar_erro(self, titulo, mensagem):
        """Mostra mensagem de erro"""
        QMessageBox.critical(self, titulo, mensagem)

    def _mostrar_aviso(self, mensagem):
        """Mostra mensagem de aviso"""
        QMessageBox.warning(self, "Aviso", mensagem)

    def _mostrar_sucesso(self, mensagem):
        """Mostra mensagem de sucesso"""
        QMessageBox.information(self, "Sucesso", mensagem)

    # ========== MÉTODOS PÚBLICOS PARA COMPATIBILIDADE ==========

    def carregar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._carregar_condicionais()

    def filtrar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_condicionais()

    def limpar_filtros(self):
        """Método público para compatibilidade com código existente"""
        self._limpar_filtros()

    def selecionar_cliente(self):
        """Método público para compatibilidade com código existente"""
        self._selecionar_cliente()

    def abrir_nova_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._abrir_nova_condicional()

    def get_condicional_selecionada(self):
        """Método público para compatibilidade com código existente"""
        return self._get_condicional_selecionada()

    def editar_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._editar_condicional()

    def converter_em_venda(self):
        """Método público para compatibilidade com código existente"""
        self._converter_em_venda()

    def marcar_como_devolvida(self):
        """Método público para compatibilidade com código existente"""
        self._marcar_como_devolvida()

    def excluir_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._excluir_condicional()

    def exportar_condicionais(self):
        """Método público para compatibilidade com código existente"""
        self._exportar_condicionais()

    def imprimir_condicional(self):
        """Método público para compatibilidade com código existente"""
        self._imprimir_condicional()

    def atualizar_tabela(self):
        """Método público para atualizar a tabela de condicionais"""
        self._carregar_condicionais()

    def get_condicional_by_row(self, row):
        """Obtém a condicional pelo índice da linha na tabela"""
        try:
            condicional_id_item = self.tabela_condicionais.item(row, 0)
            if condicional_id_item is None:
                return None

            condicional_id = int(condicional_id_item.text())
            return Condicional.buscar_por_id(condicional_id)
        except (ValueError, AttributeError):
            return None

    # ========== MÉTODOS UTILITÁRIOS LEGADOS ==========

    def validar_data(self, data_str):
        """Método de compatibilidade - usa a função utilitária"""
        return validar_data(data_str)

    def converter_data(self, data_str):
        """Método de compatibilidade"""
        return self._converter_data(data_str)

    def aplicar_estilo_linha(self, row, condicional):
        """Método de compatibilidade"""
        self._aplicar_estilo_linha(row, condicional)

    def get_nome_cliente(self, cliente_id):
        """Método público para compatibilidade"""
        return self._get_nome_cliente(cliente_id)

    def criar_pasta_relatorios(self):
        """Método de compatibilidade - usa helper"""
        criar_pasta_se_nao_existir("relatorios")

    def limpar_pasta_relatorios(self):
        """Limpa todos os arquivos da pasta de relatórios"""
        try:
            import os

            if os.path.exists("relatorios"):
                for arquivo in os.listdir("relatorios"):
                    caminho_arquivo = os.path.join("relatorios", arquivo)
                    try:
                        if os.path.isfile(caminho_arquivo):
                            os.unlink(caminho_arquivo)
                        print(f"Arquivo removido: {caminho_arquivo}")
                    except Exception as e:
                        print(f"Erro ao deletar {caminho_arquivo}: {e}")
        except Exception as e:
            print(f"Erro ao limpar pasta de relatórios: {e}")

    # ========== PROPRIEDADES PARA COMPATIBILIDADE ==========

    @property
    def init_ui(self):
        """Método legado - redirecionado para _init_ui"""
        return self._init_ui
