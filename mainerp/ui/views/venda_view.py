"""
Sistema de Vendas - Versão Corrigida com Ordenação e Filtro Fixos
"""

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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

from mainerp.core.app_logging import registrar_excecao
from mainerp.data.models.venda import Venda
from mainerp.domain.utils.export_utils import ExportUtils
from mainerp.domain.utils.helpers import (
    criar_pasta_se_nao_existir,
    formatar_data,
    formatar_moeda,
    validar_data,
)
from mainerp.domain.utils.venda_utils import VendaUtils
from mainerp.reports.print_relat_venda import PrintRelatVenda
from mainerp.reports.print_venda import PrintVenda
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin
from mainerp.ui.tabela import configurar_interacao_listagem
from mainerp.ui.table_items import NumericTableWidgetItem


class VendaView(TableScrollNavigationMixin, QWidget):
    """Interface de gestão de vendas otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.cliente_filtro = None
        self.dados = []
        self._init_ui()
        self._carregar_vendas()
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

        # Grupo de vendas (tabela)
        self._criar_grupo_vendas(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gestão de Vendas")
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
        """Cria o grupo de filtros com layout similar ao FornecedorView"""
        grupo_filtros = QGroupBox("Filtros")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Busca por cliente (lado esquerdo)

        self.busca_cliente = QLineEdit()
        self.busca_cliente.setPlaceholderText("Buscar por Nome do cliente...")
        self.busca_cliente.setMaximumWidth(300)
        self.busca_cliente.textChanged.connect(self._filtrar_vendas)
        filtro_layout.addWidget(self.busca_cliente)

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
        self.data_inicio.textChanged.connect(self._filtrar_vendas)
        layout.addWidget(self.data_inicio)

        layout.addWidget(QLabel("até:"))

        self.data_fim = QLineEdit()
        self.data_fim.setPlaceholderText("DD/MM/AAAA")
        self.data_fim.setMaximumWidth(100)
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.data_fim.textChanged.connect(self._filtrar_vendas)
        layout.addWidget(self.data_fim)

    def _criar_grupo_acoes(self, layout):
        """Cria o grupo de ações com botões semânticos"""
        grupo_acoes = QGroupBox("Ações")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões principais (esquerda)
        self.btn_nova_venda = QPushButton("Nova Venda")
        self.btn_nova_venda.setProperty("class", "success")
        self.btn_nova_venda.clicked.connect(self._abrir_nova_venda)

        self.btn_excluir = QPushButton("Excluir")
        self.btn_excluir.setProperty("class", "danger")
        self.btn_excluir.clicked.connect(self._excluir_venda)

        btn_layout.addWidget(self.btn_nova_venda)
        btn_layout.addWidget(self.btn_excluir)
        btn_layout.addStretch()

        # Botões de relatório (direita)
        self.btn_imprimir = QPushButton("Imprimir Venda")
        self.btn_imprimir.setProperty("class", "warning")
        self.btn_imprimir.clicked.connect(self._imprimir_venda)

        self.btn_exportar = QPushButton("Imprimir Relatório")
        self.btn_exportar.setProperty("class", "primary")
        self.btn_exportar.clicked.connect(self._exportar_vendas)

        btn_layout.addWidget(self.btn_imprimir)
        btn_layout.addWidget(self.btn_exportar)

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_vendas(self, layout):
        """Cria a tabela de vendas com configuração otimizada"""
        # Frame container
        container = QFrame()
        container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)

        # Layout principal
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Título (opcional, se quiser manter estilo similar)
        titulo_frame = QFrame()
        titulo_layout = QHBoxLayout()
        titulo_layout.setContentsMargins(8, 4, 8, 4)

        titulo = QLabel("Vendas")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_vendas = QTableWidget()
        self._configurar_tabela_vendas()
        container_layout.addWidget(self.tabela_vendas)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_vendas(self):
        """Configura a tabela de vendas - VERSÃO FINAL COM STRETCH"""

        # Configuração básica das colunas
        self.tabela_vendas.setColumnCount(6)
        self.tabela_vendas.setHorizontalHeaderLabels(
            ["ID", "Cliente", "Data", "Pagamento", "Desconto", "Total"]
        )

        # Configuração das colunas (com Stretch na coluna Cliente)
        header = self.tabela_vendas.horizontalHeader()

        if header is not None:
            # Modo Interactive para permitir redimensionamento manual
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

            # Configurações específicas por coluna
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cliente
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Data
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Pagamento
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Desconto
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Total

        # Larguras para colunas fixas (a coluna Cliente será stretch)
        larguras_fixas = [50, 0, 100, 120, 80, 100]  # 0 para Cliente pois será stretch
        for i, largura in enumerate(larguras_fixas):
            if largura > 0:  # Aplica apenas larguras positivas
                self.tabela_vendas.setColumnWidth(i, largura)

        # ========== CONFIGURAÇÃO DE ALTURA ==========
        self.tabela_vendas.setProperty("linhaCompacta", True)

        # 2. Configurar VERTICAL HEADER
        vheader = self.tabela_vendas.verticalHeader()

        # ALTURA DESEJADA (use o mesmo valor da tabela de produtos)
        altura_desejada = 22

        if vheader is not None:
            vheader.setMinimumSectionSize(altura_desejada)
            vheader.setMaximumSectionSize(altura_desejada)
            vheader.setDefaultSectionSize(altura_desejada)
            vheader.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            vheader.setCascadingSectionResizes(False)
            vheader.setStretchLastSection(False)
            vheader.setVisible(False)  # Opcional: esconder números

        # 4. Timer para garantir após renderização
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(
            100, lambda: self._forcar_altura_vendas_final(altura_desejada)
        )

        # ========== FIM DA CONFIGURAÇÃO ==========

        configurar_interacao_listagem(self.tabela_vendas, ordenar=False)

        # Navegação
        self.setup_scroll_navigation(
            tabela=self.tabela_vendas, scroll_sensibilidade=1, auto_select_first=True
        )

    def _forcar_altura_vendas_final(self, altura_desejada):
        """Força a altura após renderização - para tabela de vendas"""
        if not hasattr(self, "tabela_vendas"):
            return

        vheader = self.tabela_vendas.verticalHeader()
        if vheader is None:
            return

        # Forçar linha por linha (só se necessário)
        for row in range(self.tabela_vendas.rowCount()):
            if vheader.sectionSize(row) != altura_desejada:
                vheader.resizeSection(row, altura_desejada)

    # ========== MÉTODOS DE CARREGAMENTO E FILTROS ==========

    def _carregar_vendas(
        self, data_inicio_str=None, data_fim_str=None, cliente_nome=None
    ):
        """Carrega vendas na tabela com tratamento de erros"""
        try:
            # Se não foram passados parâmetros, usa os valores dos filtros
            if data_inicio_str is None:
                data_inicio_str = self.data_inicio.text().strip()
            if data_fim_str is None:
                data_fim_str = self.data_fim.text().strip()
            if cliente_nome is None:
                cliente_nome = self.busca_cliente.text().strip()

            # Buscar vendas com filtro de data
            self.dados = VendaUtils.filtrar_vendas(data_inicio_str, data_fim_str, None)
            self.dados.sort(
                key=lambda venda: venda[0], reverse=True
            )  # Ordem decrescente por ID

            self._filtrar_vendas()
            self._atualizar_label_info()

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VendaView._carregar_vendas in views/venda_view.py",
            )
            self._mostrar_erro("Erro ao carregar vendas", str(e))

    def _filtrar_vendas(self):
        """CORREÇÃO: Filtra vendas - recarrega do banco apenas quando necessário"""
        data_inicio_str = self.data_inicio.text().strip()
        data_fim_str = self.data_fim.text().strip()
        cliente_nome = self.busca_cliente.text().strip()

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

        datas_mudaram = (
            not hasattr(self, "_ultima_data_inicio")
            or not hasattr(self, "_ultima_data_fim")
            or self._ultima_data_inicio != data_inicio_str
            or self._ultima_data_fim != data_fim_str
        )

        # Se as datas mudaram, recarregar do banco
        if datas_mudaram:
            self.dados = VendaUtils.filtrar_vendas(data_inicio_str, data_fim_str, None)
            self.dados.sort(key=lambda venda: venda[0], reverse=True)
            self._ultima_data_inicio = data_inicio_str
            self._ultima_data_fim = data_fim_str

        # Filtro por nome do cliente na busca local
        dados_filtrados = self.dados
        if cliente_nome:
            dados_filtrados = [
                v
                for v in self.dados
                if cliente_nome.lower()
                in (str(v[-1]) if len(v) > 0 and v[-1] else "").lower()
            ]

        self.tabela_vendas.setRowCount(len(dados_filtrados))
        self._preencher_tabela_vendas(dados_filtrados)
        self._atualizar_label_info()

    def _preencher_tabela_vendas(self, vendas):
        """CORREÇÃO: Preenche a tabela com ordenação numérica correta"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_vendas.setSortingEnabled(False)

        for row, venda in enumerate(vendas):
            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(str(venda[0]))
            item_id.setData(
                Qt.ItemDataRole.UserRole, venda[0]
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 0, item_id)

            # CORREÇÃO: Cliente - usar o último índice que contém o nome do cliente
            # A query retorna v.* seguido de c.nome as cliente_nome
            cliente_nome = (
                str(venda[-1])
                if len(venda) > 0 and venda[-1]
                else "Cliente não informado"
            )
            self.tabela_vendas.setItem(row, 1, QTableWidgetItem(cliente_nome))

            # Data
            data_item = QTableWidgetItem(
                formatar_data(venda[2], "%Y-%m-%d", "%d/%m/%Y")
            )
            data_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 2, data_item)

            # Pagamento
            pagamento_item = QTableWidgetItem(str(venda[4]))
            pagamento_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_vendas.setItem(row, 3, pagamento_item)

            # CORREÇÃO: Desconto usando NumericTableWidgetItem com valor numérico
            desconto_valor = float(venda[7]) if venda[7] else 0
            desconto_item = NumericTableWidgetItem(formatar_moeda(desconto_valor))
            desconto_item.setData(
                Qt.ItemDataRole.UserRole, desconto_valor
            )  # Valor numérico para ordenação
            desconto_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_vendas.setItem(row, 4, desconto_item)

            # CORREÇÃO: Total usando NumericTableWidgetItem com valor numérico
            total_valor = float(venda[3]) if venda[3] else 0
            total_item = NumericTableWidgetItem(formatar_moeda(total_valor))
            total_item.setData(
                Qt.ItemDataRole.UserRole, total_valor
            )  # Valor numérico para ordenação
            total_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.tabela_vendas.setItem(row, 5, total_item)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_vendas.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_vendas.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _atualizar_label_info(self):
        """Atualiza o label informativo baseado nos filtros"""
        total_vendas = self.tabela_vendas.rowCount()
        data_inicio = self.data_inicio.text().strip()
        data_fim = self.data_fim.text().strip()
        cliente = self.busca_cliente.text().strip()

        info_parts = [f"({total_vendas} vendas"]

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
        """Limpa todos os filtros e recarrega vendas"""
        self.data_inicio.setText(
            (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        )
        self.data_fim.setText(datetime.now().strftime("%d/%m/%Y"))
        self.busca_cliente.clear()
        self._limpar_campo_erro(self.data_inicio)
        self._limpar_campo_erro(self.data_fim)
        self._carregar_vendas()

    # ========== MÉTODOS DE AÇÕES ==========

    def _abrir_nova_venda(self):
        """Abre dialog para nova venda"""
        dialog = ProdutoVendaDialog(self)
        dialog.venda_realizada.connect(self._carregar_vendas)
        dialog.exec()

    def _get_venda_selecionada(self):
        """Obtém a venda selecionada na tabela"""
        row = self.tabela_vendas.currentRow()
        if row == -1:
            return None
        try:
            item = self.tabela_vendas.item(row, 0)
            if item is None:
                return None
            venda_id = int(item.text())
            return Venda.buscar_por_id(venda_id)
        except (ValueError, AttributeError):
            return None

    def _excluir_venda(self):
        """Exclui a venda selecionada com validações"""
        venda = self._get_venda_selecionada()
        if not venda:
            self._mostrar_aviso("Selecione uma venda para excluir")
            return

        venda_id = venda.id
        if venda_id is None:
            self._mostrar_erro("Erro ao excluir venda", "ID da venda não encontrado")
            return

        # Verificar parcelas pagas
        if self._tem_parcelas_pagas(venda_id):
            self._mostrar_aviso(
                f"Não é possível excluir a venda #{venda_id}.\n"
                "Existem parcelas pagas associadas a esta venda."
            )
            return

        # Confirmar exclusão
        if self._confirmar_exclusao(venda):
            try:
                VendaUtils.devolver_estoque(venda_id)
                venda.excluir()
                self._carregar_vendas()
                self.tabela_vendas.clearSelection()
                self._mostrar_sucesso("Venda excluída com sucesso!")
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in VendaView._excluir_venda in views/venda_view.py",
                )
                self._mostrar_erro("Erro ao excluir venda", str(e))

    def _tem_parcelas_pagas(self, venda_id):
        """Verifica se a venda tem parcelas pagas"""
        try:
            return VendaUtils.verificar_parcelas_pagas(venda_id)
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VendaView._tem_parcelas_pagas in views/venda_view.py",
            )
            self._mostrar_erro("Erro ao verificar parcelas pagas", str(e))
            return True  # Em caso de erro, assume que tem parcelas para segurança

    def _confirmar_exclusao(self, venda):
        """Confirma a exclusão da venda"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a venda #{venda.id}?\n"
            f"Data: {formatar_data(venda.data_venda)}\n"
            f"Total: {formatar_moeda(venda.total)}\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

    def _exportar_vendas(self):
        """Abre diálogo para selecionar filtros e exporta relatório"""
        from mainerp.ui.dialogs.relatorio_venda_dialog import RelatorioVendaDialog

        dialog = RelatorioVendaDialog(self)
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
            forma_pagamento = filtros["forma_pagamento"]

            # Validar datas
            if not self._validar_data(data_inicio) or not self._validar_data(data_fim):
                self._mostrar_aviso("Datas inválidas. Use o formato DD/MM/AAAA")
                return

            filename = PrintRelatVenda.gerar_relatorio_por_periodo(
                data_inicio, data_fim, cliente_id, status, forma_pagamento, "relatorios"
            )

            self._tratar_arquivo_gerado(filename, "Relatório exportado")

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VendaView._gerar_relatorio_com_filtros in views/venda_view.py",
            )
            self._mostrar_erro(
                "Erro na Exportação",
                f"Ocorreu um erro ao exportar as vendas:\n{e!s}",
            )

    def _validar_data(self, data_str):
        """Valida formato de data DD/MM/YYYY"""
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def _imprimir_venda(self):
        """Imprime comprovante da venda selecionada"""
        venda = self._get_venda_selecionada()
        if not venda:
            self._mostrar_aviso("Selecione uma venda para imprimir")
            return

        try:
            filename = PrintVenda.gerar_comprovante(venda.id, "relatorios")
            self._tratar_arquivo_gerado(filename, "Comprovante gerado")

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in VendaView._imprimir_venda in views/venda_view.py",
            )
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

    def carregar_vendas(self, data_inicio_str=None, data_fim_str=None, cliente_id=None):
        """Método público para compatibilidade com código existente"""
        self._carregar_vendas(data_inicio_str, data_fim_str, cliente_id)

    def filtrar_vendas(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_vendas()

    def limpar_filtros(self):
        """Método público para compatibilidade com código existente"""
        self._limpar_filtros()

    def abrir_nova_venda(self):
        """Método público para compatibilidade com código existente"""
        self._abrir_nova_venda()

    def get_venda_selecionada(self):
        """Método público para compatibilidade com código existente"""
        return self._get_venda_selecionada()

    def excluir_venda(self):
        """Método público para compatibilidade com código existente"""
        self._excluir_venda()

    def exportar_vendas(self):
        """Método público para compatibilidade com código existente"""
        self._exportar_vendas()

    def imprimir_venda(self):
        """Método público para compatibilidade com código existente"""
        self._imprimir_venda()

    def atualizar_tabela(self):
        """Método público para compatibilidade com código existente"""
        self._carregar_vendas()
