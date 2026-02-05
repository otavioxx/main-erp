from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from mixins.table_scroll_mixin import TableScrollNavigationMixin
from models.cliente import Cliente
from utils.helpers import aplicar_maiuscula_formulario


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


class ClienteDialog(QDialog):
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente or Cliente()
        self._init_ui()
        aplicar_maiuscula_formulario(self)

    def _init_ui(self):
        self.setWindowTitle("Cadastro de Cliente")
        self.setMinimumSize(500, 650)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Dados Pessoais
        grupo_dados = QGroupBox("Dados Pessoais")
        dados_layout = QVBoxLayout()
        dados_layout.setSpacing(8)

        dados_layout.addWidget(QLabel("Nome completo:"))
        self.nome_edit = QLineEdit(self.cliente.nome or "")
        self.nome_edit.setPlaceholderText("Ex: João da Silva Santos")
        dados_layout.addWidget(self.nome_edit)

        dados_layout.addWidget(QLabel("CPF/CNPJ:"))
        self.cpf_cnpj_edit = QLineEdit(self.cliente.cpf_cnpj or "")
        self.cpf_cnpj_edit.setPlaceholderText(
            "Ex: 123.456.789-00 ou 12.345.678/0001-90"
        )
        dados_layout.addWidget(self.cpf_cnpj_edit)

        grupo_dados.setLayout(dados_layout)
        layout.addWidget(grupo_dados)

        # Contato
        grupo_contato = QGroupBox("Informações de Contato")
        contato_layout = QVBoxLayout()
        contato_layout.setSpacing(8)

        contato_layout.addWidget(QLabel("Endereço:"))
        self.endereco_edit = QLineEdit(self.cliente.endereco or "")
        self.endereco_edit.setPlaceholderText(
            "Rua das Flores, 123 - Centro - São Paulo/SP"
        )
        contato_layout.addWidget(self.endereco_edit)

        contato_layout.addWidget(QLabel("Telefone:"))
        self.telefone_edit = QLineEdit(self.cliente.telefone or "")
        self.telefone_edit.setPlaceholderText("(11) 99999-9999")
        contato_layout.addWidget(self.telefone_edit)

        contato_layout.addWidget(QLabel("Email:"))
        self.email_edit = QLineEdit(self.cliente.email or "")
        self.email_edit.setPlaceholderText("joao.silva@email.com")
        contato_layout.addWidget(self.email_edit)

        grupo_contato.setLayout(contato_layout)
        layout.addWidget(grupo_contato)

        # Observações
        grupo_obs = QGroupBox("Observações")
        obs_layout = QVBoxLayout()

        self.observacao_edit = QTextEdit(self.cliente.observacao or "")
        self.observacao_edit.setPlaceholderText(
            "Informações adicionais sobre o cliente..."
        )
        self.observacao_edit.setMaximumHeight(80)
        obs_layout.addWidget(self.observacao_edit)

        grupo_obs.setLayout(obs_layout)
        layout.addWidget(grupo_obs)

        # Status
        status_layout = QHBoxLayout()
        self.ativo_checkbox = QCheckBox("Cliente ativo")
        self.ativo_checkbox.setChecked(self.cliente.ativo)
        status_layout.addWidget(self.ativo_checkbox)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.nome_edit.setFocus()

    def get_data(self):
        self.cliente.nome = self.nome_edit.text().strip()
        self.cliente.cpf_cnpj = self.cpf_cnpj_edit.text().strip()
        self.cliente.endereco = self.endereco_edit.text().strip()
        self.cliente.telefone = self.telefone_edit.text().strip()
        self.cliente.email = self.email_edit.text().strip()
        self.cliente.observacao = self.observacao_edit.toPlainText().strip()
        self.cliente.ativo = self.ativo_checkbox.isChecked()
        return self.cliente


class ClienteView(TableScrollNavigationMixin, QWidget):
    """Interface de gestão de clientes otimizada para o novo sistema de estilos"""

    def __init__(self):
        super().__init__()
        self.mostrar_inativos = False
        self.dados = []
        self._init_ui()
        self._carregar_clientes()

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

        # Grupo de clientes (tabela)
        self._criar_grupo_clientes(layout)

        self.setLayout(layout)

    def _criar_header(self, layout):
        """Cria o cabeçalho da tela"""
        header_frame = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("Gerenciamento de Clientes")
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
        self.busca_edit.setPlaceholderText("Nome, CPF/CNPJ, telefone ou email...")
        self.busca_edit.setMaximumWidth(300)
        self.busca_edit.textChanged.connect(self._filtrar_clientes)
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
        self.btn_novo = QPushButton("Novo Cliente")
        self.btn_novo.setProperty("class", "success")
        self.btn_novo.clicked.connect(self._novo_cliente)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setProperty("class", "secondary")
        self.btn_editar.clicked.connect(self._editar_cliente)

        self.btn_inativar = QPushButton("Inativar")
        self.btn_inativar.setProperty("class", "danger")
        self.btn_inativar.clicked.connect(self._inativar_cliente)

        self.btn_reativar = QPushButton("Reativar")
        self.btn_reativar.setProperty("class", "warning")
        self.btn_reativar.clicked.connect(self._reativar_cliente)

        btn_layout.addWidget(self.btn_novo)
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_inativar)
        btn_layout.addWidget(self.btn_reativar)
        btn_layout.addStretch()

        grupo_acoes.setLayout(btn_layout)
        layout.addWidget(grupo_acoes)

    def _criar_grupo_clientes(self, layout):
        """Cria a tabela de clientes com configuração otimizada"""
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

        titulo = QLabel("Clientes")
        titulo.setProperty("class", "subtitle")
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()

        titulo_frame.setLayout(titulo_layout)
        container_layout.addWidget(titulo_frame)

        # Tabela
        self.tabela_clientes = QTableWidget()
        self._configurar_tabela_clientes()
        container_layout.addWidget(self.tabela_clientes)

        container.setLayout(container_layout)
        layout.addWidget(container)

    def _configurar_tabela_clientes(self):
        """Configura a tabela de clientes de forma otimizada"""
        self.tabela_clientes.setColumnCount(7)
        self.tabela_clientes.setHorizontalHeaderLabels(
            ["ID", "Nome", "CPF/CNPJ", "Endereço", "Telefone", "Email", "Observação"]
        )

        # Configuração das colunas
        header = self.tabela_clientes.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Nome
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # CPF/CNPJ
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Endereço
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Telefone
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Email
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Observação

        # Larguras otimizadas
        larguras_colunas = [50, 200, 130, 250, 110, 200, 200]
        for i, largura in enumerate(larguras_colunas):
            self.tabela_clientes.setColumnWidth(i, largura)

        # Configurações gerais da tabela
        self.tabela_clientes.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabela_clientes.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabela_clientes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_clientes.setAlternatingRowColors(True)
        self.tabela_clientes.verticalHeader().setVisible(False)
        self.tabela_clientes.setSortingEnabled(True)

        self.setup_scroll_navigation(
            tabela=self.tabela_clientes,
            scroll_sensibilidade=1,  # 1 linha por scroll (padrão)
            auto_select_first=True,  # Seleciona primeira linha automaticamente
        )

    # ========== MÉTODOS DE CARREGAMENTO E FILTROS ==========

    def _carregar_clientes(self):
        """Carrega clientes na tabela com tratamento de erros"""
        try:
            if self.mostrar_inativos:
                self.dados = Cliente.buscar_todos(apenas_ativos=False)
                self.label_filtro.setText(
                    "(Mostrando todos os registros - F11 para apenas ativos)"
                )
            else:
                self.dados = Cliente.buscar_todos(apenas_ativos=True)
                self.label_filtro.setText(
                    "(Mostrando apenas ativos - F11 para inativos)"
                )

            self._filtrar_clientes()

        except Exception as e:
            self._mostrar_erro("Erro ao carregar clientes", str(e))

    def _filtrar_clientes(self):
        """CORREÇÃO: Filtra clientes por texto de busca - sempre usa dados originais"""
        texto_busca = self.busca_edit.text().lower().strip()

        # CORREÇÃO: Sempre trabalhar com os dados originais
        if texto_busca:
            dados_filtrados = [
                c
                for c in self.dados  # CORREÇÃO: sempre usar self.dados original
                if (texto_busca in c.nome.lower() if c.nome else False)
                or (texto_busca in (c.cpf_cnpj or "").lower())
                or (texto_busca in (c.telefone or "").lower())
                or (texto_busca in (c.email or "").lower())
                or (texto_busca in (c.endereco or "").lower())
                or (texto_busca in (c.observacao or "").lower())
            ]
        else:
            dados_filtrados = self.dados

        self.tabela_clientes.setRowCount(len(dados_filtrados))
        self._preencher_tabela_clientes(dados_filtrados)

    def _preencher_tabela_clientes(self, clientes):
        """CORREÇÃO: Preenche a tabela com ordenação numérica correta"""

        # CORREÇÃO: Desabilitar ordenação durante preenchimento
        self.tabela_clientes.setSortingEnabled(False)

        # Cores para clientes inativos (mesmas do sistema de estilos)
        cor_fundo_inativo = QColor("#4a2a2a")
        cor_texto_inativo = QColor("#ff6b6b")

        for row, cliente in enumerate(clientes):
            # CORREÇÃO: ID usando NumericTableWidgetItem para ordenação numérica
            item_id = NumericTableWidgetItem(str(cliente.id))
            item_id.setData(
                Qt.ItemDataRole.UserRole, cliente.id
            )  # Armazenar valor numérico
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not cliente.ativo:
                item_id.setBackground(cor_fundo_inativo)
                item_id.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 0, item_id)

            # Nome
            nome = cliente.nome or ""
            item_nome = QTableWidgetItem(nome)
            if not cliente.ativo:
                item_nome.setBackground(cor_fundo_inativo)
                item_nome.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 1, item_nome)

            # CPF/CNPJ
            cpf_cnpj = cliente.cpf_cnpj or ""
            item_cpf = QTableWidgetItem(cpf_cnpj)
            if not cliente.ativo:
                item_cpf.setBackground(cor_fundo_inativo)
                item_cpf.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 2, item_cpf)

            # Endereço
            endereco = cliente.endereco or ""
            item_endereco = QTableWidgetItem(endereco)
            if not cliente.ativo:
                item_endereco.setBackground(cor_fundo_inativo)
                item_endereco.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 3, item_endereco)

            # Telefone
            telefone = cliente.telefone or ""
            item_telefone = QTableWidgetItem(telefone)
            if not cliente.ativo:
                item_telefone.setBackground(cor_fundo_inativo)
                item_telefone.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 4, item_telefone)

            # Email
            email = cliente.email or ""
            item_email = QTableWidgetItem(email)
            if not cliente.ativo:
                item_email.setBackground(cor_fundo_inativo)
                item_email.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 5, item_email)

            # Observação
            obs = cliente.observacao or ""
            item_obs = QTableWidgetItem(obs)
            if obs:
                item_obs.setToolTip(obs)
            if not cliente.ativo:
                item_obs.setBackground(cor_fundo_inativo)
                item_obs.setForeground(cor_texto_inativo)
            self.tabela_clientes.setItem(row, 6, item_obs)

        # CORREÇÃO: Reabilitar ordenação após preenchimento
        self.tabela_clientes.setSortingEnabled(True)

        # CORREÇÃO: Ordenar por ID em ordem decrescente por padrão
        self.tabela_clientes.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _limpar_filtros(self):
        """Limpa todos os filtros e recarrega clientes"""
        self.busca_edit.clear()
        self._carregar_clientes()

    # ========== MÉTODOS DE AÇÕES ==========

    def _novo_cliente(self):
        """Abre dialog para novo cliente"""
        dialog = ClienteDialog()
        if dialog.exec():
            try:
                novo_cliente = dialog.get_data()
                novo_cliente.salvar()
                self._carregar_clientes()
                self._mostrar_sucesso("Cliente cadastrado com sucesso!")
            except Exception as e:
                self._mostrar_erro("Erro ao salvar cliente", str(e))

    def _get_cliente_selecionado(self):
        """Obtém o cliente selecionado na tabela"""
        row = self.tabela_clientes.currentRow()
        if row == -1:
            return None
        try:
            cliente_id = int(self.tabela_clientes.item(row, 0).text())
            return Cliente.buscar_por_id(cliente_id)
        except (ValueError, AttributeError):
            return None

    def _editar_cliente(self):
        """Edita o cliente selecionado"""
        cliente = self._get_cliente_selecionado()
        if not cliente:
            self._mostrar_aviso("Selecione um cliente para editar")
            return

        dialog = ClienteDialog(self, cliente)
        if dialog.exec():
            try:
                cliente_editado = dialog.get_data()
                cliente_editado.salvar()
                self._carregar_clientes()
                self._mostrar_sucesso("Cliente atualizado com sucesso!")
            except Exception as e:
                self._mostrar_erro("Erro ao salvar cliente", str(e))

    def _inativar_cliente(self):
        """Inativa o cliente selecionado"""
        cliente = self._get_cliente_selecionado()
        if not cliente:
            self._mostrar_aviso("Selecione um cliente para inativar")
            return

        if self._confirmar_inativacao(cliente):
            try:
                cliente.ativo = False
                cliente.salvar()
                self._carregar_clientes()
                self.tabela_clientes.clearSelection()
                self._mostrar_sucesso("Cliente inativado com sucesso!")
            except Exception as e:
                self._mostrar_erro("Erro ao inativar cliente", str(e))

    def _reativar_cliente(self):
        """Reativa o cliente selecionado"""
        cliente = self._get_cliente_selecionado()
        if not cliente:
            self._mostrar_aviso("Selecione um cliente para reativar")
            return

        try:
            cliente.ativo = True
            cliente.salvar()
            self._carregar_clientes()
            self.tabela_clientes.clearSelection()
            self._mostrar_sucesso("Cliente reativado com sucesso!")
        except Exception as e:
            self._mostrar_erro("Erro ao reativar cliente", str(e))

    def _confirmar_inativacao(self, cliente):
        """Confirma a inativação do cliente"""
        resposta = QMessageBox.question(
            self,
            "Confirmar Inativação",
            f"Tem certeza que deseja inativar o cliente:\n"
            f"Nome: {cliente.nome}\n"
            f"CPF/CNPJ: {cliente.cpf_cnpj or 'Não informado'}\n\n"
            "O cliente ficará inativo mas seus dados serão preservados.",
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
        self._carregar_clientes()

    def filtrar_clientes(self):
        """Método público para compatibilidade com código existente"""
        self._filtrar_clientes()

    def novo_registro(self):
        """Método público para compatibilidade com código existente"""
        self._novo_cliente()

    def editar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._editar_cliente()

    def inativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._inativar_cliente()

    def reativar_registro(self):
        """Método público para compatibilidade com código existente"""
        self._reativar_cliente()

    def toggle_mostrar_inativos(self):
        """Alterna entre mostrar ativos/inativos - compatibilidade com F11"""
        self.mostrar_inativos = not self.mostrar_inativos
        self._carregar_clientes()

    def keyPressEvent(self, event):
        """Manipula eventos de teclado"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_mostrar_inativos()
        else:
            super().keyPressEvent(event)
