from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
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
from mainerp.data.models.fornecedor import Fornecedor
from mainerp.ui.dialogs.fornecedor_dialog import FornecedorDialog
from mainerp.ui.mixins.table_scroll_mixin import TableScrollNavigationMixin
from mainerp.ui.styles import cores_ativas
from mainerp.ui.tabela import configurar_listagem_padrao
from mainerp.ui.table_items import NumericTableWidgetItem


class FornecedorView(TableScrollNavigationMixin, QWidget):
    """Interface de gestão de fornecedores otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.mostrar_inativos = False
        self.dados = []
        self._init_ui()
        self._carregar_fornecedores()

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

        # Grupo de fornecedores (tabela)
        self._criar_grupo_fornecedores(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gerenciamento de Fornecedores")
        titulo.setProperty("class", "title")
        header_layout.addWidget(titulo)

        # Label para mostrar estado do filtro
        self.label_filtro = QLabel("(Mostrando apenas ativos - F11 para inativos)")
        self.label_filtro.setProperty("class", "muted")
        header_layout.addWidget(self.label_filtro)
        header_layout.addStretch()

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

    def _criar_grupo_filtros(self, layout):
        """Cria o grupo de filtros"""
        grupo_filtros = QGroupBox("Filtros")

        filtro_layout = QHBoxLayout()
        filtro_layout.setContentsMargins(8, 12, 8, 12)
        filtro_layout.setSpacing(10)

        # Campo de busca

        self.busca_edit = QLineEdit()
        self.busca_edit.setPlaceholderText("Nome, CNPJ, telefone ou email...")
        self.busca_edit.setMaximumWidth(300)
        self.busca_edit.textChanged.connect(self._filtrar_fornecedores)
        filtro_layout.addWidget(self.busca_edit)

        filtro_layout.addStretch()

        # Botão limpar
        btn_limpar = QPushButton("Limpar Filtros")
        btn_limpar.setProperty("class", "secondary")
        btn_limpar.clicked.connect(self._limpar_filtros)
        filtro_layout.addWidget(btn_limpar)

        grupo_filtros.setLayout(filtro_layout)
        layout.addWidget(grupo_filtros)

    def _criar_grupo_acoes(self, layout):
        """Cria o grupo de ações com botões semânticos"""
        grupo_acoes = QGroupBox("Ações")

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 12, 8, 12)
        btn_layout.setSpacing(8)

        # Botões com classes semânticas apropriadas
        self.btn_novo = QPushButton("Novo Fornecedor")
        self.btn_novo.setProperty("class", "success")
        self.btn_novo.clicked.connect(self._novo_fornecedor)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setProperty("class", "secondary")
        self.btn_editar.clicked.connect(self._editar_fornecedor)

        self.btn_inativar = QPushButton("Inativar")
        self.btn_inativar.setProperty("class", "danger")
        self.btn_inativar.clicked.connect(self._inativar_fornecedor)

        self.btn_reativar = QPushButton("Reativar")
        self.btn_reativar.setProperty("class", "warning")
        self.btn_reativar.clicked.connect(self._reativar_fornecedor)

        btn_layout.addWidget(self.btn_novo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_inativar)
        btn_layout.addWidget(self.btn_reativar)
        btn_layout.addStretch()

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_fornecedores(self, layout):
        """Cria a tabela de fornecedores com configuração otimizada"""
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

        titulo = QLabel("Fornecedores")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_fornecedores = QTableWidget()
        self._configurar_tabela_fornecedores()
        container_layout.addWidget(self.tabela_fornecedores)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_fornecedores(self):
        """Configura a tabela de fornecedores - VERSÃO SIMPLIFICADA"""
        self.tabela_fornecedores.setColumnCount(6)
        self.tabela_fornecedores.setHorizontalHeaderLabels(
            ["ID", "Nome", "CNPJ", "Telefone", "Email", "Observação"]
        )

        # Configuração das colunas
        header = self.tabela_fornecedores.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # CNPJ
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Telefone
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Email
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Observação

        # Larguras otimizadas
        larguras_colunas = [50, 200, 130, 110, 250, 350]
        for i, largura in enumerate(larguras_colunas):
            if largura > 0:  # Aplica apenas larguras positivas
                self.tabela_fornecedores.setColumnWidth(i, largura)

        configurar_listagem_padrao(self.tabela_fornecedores)

        self.setup_scroll_navigation(
            tabela=self.tabela_fornecedores,
            scroll_sensibilidade=1,
            auto_select_first=True,
        )

    # ========== MÉTODOS DE CARREGAMENTO E FILTROS ==========

    def _carregar_fornecedores(self):
        """Carrega fornecedores na tabela com tratamento de erros"""
        try:
            if self.mostrar_inativos:
                self.dados = Fornecedor.buscar_todos(apenas_ativos=False)
                self.label_filtro.setText(
                    "(Mostrando todos os registros - F11 para apenas ativos)"
                )
            else:
                self.dados = Fornecedor.buscar_todos(apenas_ativos=True)
                self.label_filtro.setText(
                    "(Mostrando apenas ativos - F11 para inativos)"
                )

            self._filtrar_fornecedores()

        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in FornecedorView._carregar_fornecedores in views/fornecedor_view.py",
            )
            self._mostrar_erro("Erro ao carregar fornecedores", str(e))

    def _filtrar_fornecedores(self):
        """CORREÇÃO: Filtra fornecedores por texto de busca - sempre usa dados originais"""
        texto_busca = self.busca_edit.text().lower().strip()

        # CORREÇÃO: Sempre trabalhar com os dados originais
        if texto_busca:
            dados_filtrados = [
                f
                for f in self.dados  # CORREÇÃO: sempre usar self.dados original
                if (texto_busca in f.nome.lower() if f.nome else False)
                or (texto_busca in (f.cnpj or "").lower())
                or (texto_busca in (f.telefone or "").lower())
                or (texto_busca in (f.email or "").lower())
                or (texto_busca in (f.observacao or "").lower())
            ]
        else:
            dados_filtrados = self.dados

        self.tabela_fornecedores.setRowCount(len(dados_filtrados))
        self._preencher_tabela_fornecedores(dados_filtrados)

    def _preencher_tabela_fornecedores(self, fornecedores):
        """CORREÇÃO: Preenche a tabela com ordenação numérica correta"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_fornecedores.setSortingEnabled(False)

        # Cores para fornecedores inativos (mesmas do sistema de estilos)
        cor_fundo_inativo = QColor(cores_ativas().danger_bg)
        cor_texto_inativo = QColor(cores_ativas().danger_text)

        for row, fornecedor in enumerate(fornecedores):
            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(str(fornecedor.id))
            item_id.setData(
                Qt.ItemDataRole.UserRole, fornecedor.id
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not fornecedor.ativo:
                item_id.setBackground(cor_fundo_inativo)
                item_id.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 0, item_id)

            # Nome
            nome = fornecedor.nome or ""
            item_nome = QTableWidgetItem(nome)
            if not fornecedor.ativo:
                item_nome.setBackground(cor_fundo_inativo)
                item_nome.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 1, item_nome)

            # CNPJ
            cnpj = fornecedor.cnpj or ""
            item_cnpj = QTableWidgetItem(cnpj)
            if not fornecedor.ativo:
                item_cnpj.setBackground(cor_fundo_inativo)
                item_cnpj.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 2, item_cnpj)

            # Telefone
            telefone = fornecedor.telefone or ""
            item_telefone = QTableWidgetItem(telefone)
            if not fornecedor.ativo:
                item_telefone.setBackground(cor_fundo_inativo)
                item_telefone.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 3, item_telefone)

            # Email
            email = fornecedor.email or ""
            item_email = QTableWidgetItem(email)
            if not fornecedor.ativo:
                item_email.setBackground(cor_fundo_inativo)
                item_email.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 4, item_email)

            # Observação
            obs = fornecedor.observacao or ""
            item_obs = QTableWidgetItem(obs)
            if not fornecedor.ativo:
                item_obs.setBackground(cor_fundo_inativo)
                item_obs.setForeground(cor_texto_inativo)
            self.tabela_fornecedores.setItem(row, 5, item_obs)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_fornecedores.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_fornecedores.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _limpar_filtros(self):
        """Limpa todos os filtros e recarrega fornecedores"""
        self.busca_edit.clear()
        self._carregar_fornecedores()

    # ========== MÉTODOS DE AÇÕES ==========

    def _novo_fornecedor(self):
        """Abre dialog para novo fornecedor"""
        dialog = FornecedorDialog()
        if dialog.exec():
            self._carregar_fornecedores()
            self._mostrar_sucesso("Fornecedor cadastrado com sucesso!")

    def _get_fornecedor_selecionado(self):
        """Obtém o fornecedor selecionado na tabela"""
        row = self.tabela_fornecedores.currentRow()
        if row == -1:
            return None
        try:
            item = self.tabela_fornecedores.item(row, 0)
            if item is None:
                return None
            fornecedor_id = int(item.text())
            return Fornecedor.buscar_por_id(fornecedor_id)
        except (ValueError, AttributeError):
            return None

    def _editar_fornecedor(self, checked=False):
        """Edita o fornecedor selecionado"""
        fornecedor = self._get_fornecedor_selecionado()
        if not fornecedor:
            self._mostrar_aviso("Selecione um fornecedor para editar")
            return

        dialog = FornecedorDialog(fornecedor, self)
        if dialog.exec():
            self._carregar_fornecedores()
            self._mostrar_sucesso("Fornecedor atualizado com sucesso!")

    def _inativar_fornecedor(self):
        """Inativa o fornecedor selecionado"""
        fornecedor = self._get_fornecedor_selecionado()
        if not fornecedor:
            self._mostrar_aviso("Selecione um fornecedor para inativar")
            return

        if self._confirmar_inativacao(fornecedor):
            try:
                fornecedor.ativo = False
                fornecedor.salvar()
                self._carregar_fornecedores()
                self.tabela_fornecedores.clearSelection()
                self._mostrar_sucesso("Fornecedor inativado com sucesso!")
            except Exception as e:
                registrar_excecao(
                    __name__,
                    "Exception handled in FornecedorView._inativar_fornecedor in views/fornecedor_view.py",
                )
                self._mostrar_erro("Erro ao inativar fornecedor", str(e))

    def _reativar_fornecedor(self):
        """Reativa o fornecedor selecionado"""
        fornecedor = self._get_fornecedor_selecionado()
        if not fornecedor:
            self._mostrar_aviso("Selecione um fornecedor para reativar")
            return

        try:
            fornecedor.ativo = True
            fornecedor.salvar()
            self._carregar_fornecedores()
            self.tabela_fornecedores.clearSelection()
            self._mostrar_sucesso("Fornecedor reativado com sucesso!")
        except Exception as e:
            registrar_excecao(
                __name__,
                "Exception handled in FornecedorView._reativar_fornecedor in views/fornecedor_view.py",
            )
            self._mostrar_erro("Erro ao reativar fornecedor", str(e))

    def _confirmar_inativacao(self, fornecedor):
        """Confirma a inativação do fornecedor"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Inativação",
            f"Tem certeza que deseja inativar o fornecedor:\n"
            f"Nome: {fornecedor.nome}\n"
            f"CNPJ: {fornecedor.cnpj or 'Não informado'}\n\n"
            "O fornecedor ficará inativo mas seus dados serão preservados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return resposta == QMessageBox.StandardButton.Yes

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

    def carregar_dados(self):
        """Método público para compatibilidade com código existente"""
        self._carregar_fornecedores()

    def filtrar_fornecedores(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_fornecedores()

    def novo_registro(self):
        """Método público para compatibilidade com código existente"""
        self._novo_fornecedor()

    def editar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._editar_fornecedor()

    def inativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._inativar_fornecedor()

    def reativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._reativar_fornecedor()

    def toggle_mostrar_inativos(self):
        """Alterna entre mostrar ativos/inativos - compatibilidade com F11"""
        self.mostrar_inativos = not self.mostrar_inativos
        self._carregar_fornecedores()

    def keyPressEvent(self, event):
        """Manipula eventos de teclado"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_mostrar_inativos()
        else:
            super().keyPressEvent(event)
