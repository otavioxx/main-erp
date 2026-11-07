# \erp\database.py
import sqlite3
from datetime import datetime
from pathlib import Path

from config import config, get_config


class MigracaoError(RuntimeError):
    """Falha ao atualizar o esquema do banco de dados."""


class Database:
    """Acesso ao SQLite com migrações numeradas.

    O esquema é controlado por ``PRAGMA user_version``. Cada migração roda uma
    única vez, dentro de uma transação, e antes de qualquer migração pendente
    é feito um backup automático do banco em ``<dados>/backups``.

    COMO ADICIONAR UMA ALTERAÇÃO DE ESQUEMA
    1. escreva um método ``_migracao_NNN_descricao(self)``;
    2. registre-o em ``MIGRACOES`` com o próximo número;
    3. mantenha migrações ADITIVAS (novas tabelas/colunas), assim uma versão
       anterior do sistema continua funcionando com o banco já migrado.
    """

    # (versão, nome do método). Nunca renumere nem apague entradas antigas.
    MIGRACOES = [
        (1, "_migracao_001_esquema_base"),
        # (2, "_migracao_002_exemplo"),
    ]

    MANTER_BACKUPS_MIGRACAO = 10

    def __init__(self, db_name=None):
        self.db_name = db_name or config.obter_caminho_banco()
        self.connection = None
        self.migrar()

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.execute("PRAGMA foreign_keys = ON")
            timezone = get_config("database.timezone", "-03:00")
            self.connection.execute(f"PRAGMA timezone = '{timezone}'")
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    # ------------------------------------------------------------------
    # Motor de migrações
    # ------------------------------------------------------------------

    def versao_esquema(self) -> int:
        return self.get_connection().execute("PRAGMA user_version").fetchone()[0]

    def migrar(self):
        """Aplica, em ordem, as migrações que ainda não rodaram neste banco."""
        conn = self.get_connection()
        atual = self.versao_esquema()
        pendentes = [(v, nome) for v, nome in self.MIGRACOES if v > atual]
        if not pendentes:
            return

        destino = pendentes[-1][0]
        backup = self._backup_pre_migracao(atual, destino)

        for versao, nome in pendentes:
            try:
                conn.execute("BEGIN")
                getattr(self, nome)()
                conn.execute(f"PRAGMA user_version = {versao}")
                conn.commit()
            except Exception as e:
                conn.rollback()
                dica = f"\nBackup anterior à migração: {backup}" if backup else ""
                raise MigracaoError(
                    f"Falha ao atualizar o banco de dados para a versão {versao} "
                    f"({nome}): {e}{dica}"
                ) from e

    def _backup_pre_migracao(self, de: int, para: int):
        """Copia o banco atual antes de migrar. Retorna o caminho ou None."""
        conn = self.get_connection()
        tabelas = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'table'"
        ).fetchone()[0]
        if tabelas == 0:
            return None  # banco novo e vazio: nada a proteger

        pasta = Path(self.db_name).resolve().parent / "backups"
        pasta.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = pasta / f"pre_migracao_v{de}_para_v{para}_{carimbo}.db"

        copia = sqlite3.connect(str(destino))
        try:
            conn.backup(copia)
        finally:
            copia.close()

        antigos = sorted(pasta.glob("pre_migracao_*.db"))
        for velho in antigos[: -self.MANTER_BACKUPS_MIGRACAO]:
            try:
                velho.unlink()
            except OSError:
                pass
        return str(destino)

    @staticmethod
    def _colunas(cursor, tabela):
        cursor.execute(f"PRAGMA table_info({tabela})")
        return [coluna[1] for coluna in cursor.fetchall()]

    def _garantir_coluna(self, cursor, tabela, coluna, definicao):
        """ADD COLUMN se ainda não existir. Retorna True quando adicionou."""
        if coluna in self._colunas(cursor, tabela):
            return False
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
        return True

    # ------------------------------------------------------------------
    # Migração 1: esquema base
    # Reúne tudo o que antes rodava a cada abertura do sistema. É idempotente,
    # então serve para bancos novos, antigos e backups restaurados.
    # ------------------------------------------------------------------

    def _migracao_001_esquema_base(self):
        self.init_database()
        cursor = self.get_connection().cursor()

        self._garantir_coluna(cursor, "condicionais", "desconto", "REAL DEFAULT 0")

        for campo, tipo in (
            ("tamanho", "TEXT"),
            ("cor", "TEXT"),
            ("ea", "TEXT"),
            ("referencia", "TEXT"),
        ):
            self._garantir_coluna(cursor, "produtos", campo, tipo)

        if self._garantir_coluna(
            cursor, "itens_pedido", "preco_venda", "REAL DEFAULT 0"
        ):
            cursor.execute("""
                UPDATE itens_pedido
                SET preco_venda = preco_custo * 1.3
                WHERE preco_venda = 0 OR preco_venda IS NULL
            """)

        self._garantir_coluna(cursor, "vendas", "observacao", "TEXT DEFAULT ''")
        self._garantir_coluna(cursor, "vendas", "valor_entrada", "REAL DEFAULT 0")
        if self._garantir_coluna(
            cursor, "vendas", "valor_financiado", "REAL DEFAULT 0"
        ):
            cursor.execute("""
                UPDATE vendas
                SET valor_financiado = total
                WHERE valor_financiado = 0 OR valor_financiado IS NULL
            """)

        self._garantir_coluna(cursor, "pedidos", "desconto", "REAL DEFAULT 0")

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                email TEXT,
                logo BLOB
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf_cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                email TEXT,
                observacao TEXT,
                data_cadastro DATE,
                ativo BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj_unique
            ON clientes(cpf_cnpj)
            WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                email TEXT,
                observacao TEXT,
                ativo BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fornecedores_cnpj_unique
            ON fornecedores(cnpj)
            WHERE cnpj IS NOT NULL AND cnpj != ''
        """)

        # Tabela produtos com todos os campos (novos e antigos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco_custo REAL NOT NULL,
                preco_venda REAL NOT NULL,
                estoque INTEGER DEFAULT 0,
                fornecedor_id INTEGER,
                ativo BOOLEAN DEFAULT 1,
                tamanho TEXT,
                cor TEXT,
                ea TEXT,
                referencia TEXT,
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                data_venda DATE,
                total REAL,
                forma_pagamento TEXT,
                status TEXT DEFAULT 'pendente',
                parcelas INTEGER DEFAULT 1,
                desconto REAL DEFAULT 0,
                valor_entrada REAL DEFAULT 0,
                valor_financiado REAL DEFAULT 0,
                observacao TEXT DEFAULT '',
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_venda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                preco_unitario REAL,
                desconto REAL DEFAULT 0,
                FOREIGN KEY (venda_id) REFERENCES vendas (id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duplicatas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                cliente_id INTEGER,
                numero_parcela INTEGER,
                valor_parcela REAL,
                data_vencimento DATE,
                data_pagamento DATE,
                status TEXT DEFAULT 'aberto',
                FOREIGN KEY (venda_id) REFERENCES vendas (id),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duplicatas_pagas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                cliente_id INTEGER,
                numero_parcela INTEGER,
                valor_original REAL,
                valor_recebido REAL,
                data_vencimento DATE,
                data_pagamento DATE,
                forma_pagamento TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venda_id) REFERENCES vendas (id),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS condicionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                data_condicional DATE NOT NULL,
                data_prevista_devolucao DATE,
                status TEXT DEFAULT 'ativa',
                observacao TEXT,
                desconto REAL DEFAULT 0,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_condicional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condicional_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                FOREIGN KEY (condicional_id) REFERENCES condicionais (id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fornecedor_id INTEGER NOT NULL,
                data_pedido DATE NOT NULL,
                data_recebimento DATE,
                valor_total REAL DEFAULT 0,
                valor_frete REAL DEFAULT 0,
                desconto REAL DEFAULT 0,
                observacao TEXT,
                status TEXT DEFAULT 'pendente', -- pendente, recebido, cancelado
                FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_custo REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        """)
