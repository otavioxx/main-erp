#\erp\database.py
import sqlite3
from datetime import datetime
from config import config, get_config

class Database:
    def __init__(self, db_name=None):
        self.db_name = db_name or get_config('database.name', 'erp.db')
        self.connection = None
        self.init_database()
        self._adicionar_campo_desconto_condicionais()
        self.adicionar_novos_campos_produtos()
        self._adicionar_campo_preco_venda_itens_pedido()
        self._adicionar_campo_observacao_vendas()
        self._adicionar_campos_entrada_vendas()
        self._adicionar_campo_desconto_pedidos()  # NOVO

    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.execute("PRAGMA foreign_keys = ON")
            timezone = get_config('database.timezone', '-03:00')
            self.connection.execute(f"PRAGMA timezone = '{timezone}'")
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                email TEXT,
                logo BLOB
            )
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj_unique
            ON clientes(cpf_cnpj)
            WHERE cpf_cnpj IS NOT NULL AND cpf_cnpj != ''
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fornecedores_cnpj_unique
            ON fornecedores(cnpj)
            WHERE cnpj IS NOT NULL AND cnpj != ''
        ''')

        # Tabela produtos com todos os campos (novos e antigos)
        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens_condicional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condicional_id INTEGER NOT NULL,
                produto_id INTEGER NOT NULL,
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL,
                FOREIGN KEY (condicional_id) REFERENCES condicionais (id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
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
        ''')

        conn.commit()

    def _adicionar_campo_desconto_pedidos(self):
        """Adiciona o campo desconto à tabela pedidos se ainda não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(pedidos)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

            if 'desconto' not in colunas_existentes:
                cursor.execute("ALTER TABLE pedidos ADD COLUMN desconto REAL DEFAULT 0")
                conn.commit()
                print("Campo 'desconto' adicionado à tabela pedidos")
        except Exception as e:
            print(f"Erro ao adicionar campo desconto aos pedidos: {e}")

    def _adicionar_campo_desconto_condicionais(self):
        """Adiciona o campo desconto à tabela condicionais se ainda não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(condicionais)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

            if 'desconto' not in colunas_existentes:
                cursor.execute("ALTER TABLE condicionais ADD COLUMN desconto REAL DEFAULT 0")
                conn.commit()
                print("Campo 'desconto' adicionado à tabela condicionais")
        except Exception as e:
            print(f"Erro ao adicionar campo desconto: {e}")

    def _adicionar_campo_observacao_vendas(self):
        """Adiciona o campo observacao à tabela vendas se ainda não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(vendas)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

            if 'observacao' not in colunas_existentes:
                cursor.execute("ALTER TABLE vendas ADD COLUMN observacao TEXT DEFAULT ''")
                conn.commit()
                print("Campo 'observacao' adicionado à tabela vendas")
        except Exception as e:
            print(f"Erro ao adicionar campo observacao: {e}")

    def _adicionar_campo_preco_venda_itens_pedido(self):
        """Adiciona o campo preco_venda à tabela itens_pedido se ainda não existir"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(itens_pedido)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

            if 'preco_venda' not in colunas_existentes:
                cursor.execute("ALTER TABLE itens_pedido ADD COLUMN preco_venda REAL DEFAULT 0")
                conn.commit()
                print("Campo 'preco_venda' adicionado à tabela itens_pedido")

                cursor.execute("""
                    UPDATE itens_pedido
                    SET preco_venda = preco_custo * 1.3
                    WHERE preco_venda = 0 OR preco_venda IS NULL
                """)
                conn.commit()
                print("Registros existentes atualizados com preço de venda padrão (custo * 1.3)")

        except Exception as e:
            print(f"Erro ao adicionar campo preco_venda: {e}")

    def _adicionar_campos_entrada_vendas(self):
        """Adiciona os campos valor_entrada e valor_financiado à tabela vendas se ainda não existirem"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA table_info(vendas)")
            colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

            if 'valor_entrada' not in colunas_existentes:
                cursor.execute("ALTER TABLE vendas ADD COLUMN valor_entrada REAL DEFAULT 0")
                conn.commit()
                print("Campo 'valor_entrada' adicionado à tabela vendas")

            if 'valor_financiado' not in colunas_existentes:
                cursor.execute("ALTER TABLE vendas ADD COLUMN valor_financiado REAL DEFAULT 0")
                conn.commit()
                print("Campo 'valor_financiado' adicionado à tabela vendas")

                cursor.execute("""
                    UPDATE vendas
                    SET valor_financiado = total
                    WHERE valor_financiado = 0 OR valor_financiado IS NULL
                """)
                conn.commit()
                print("Registros existentes atualizados com valor_financiado = total")

        except Exception as e:
            print(f"Erro ao adicionar campos de entrada: {e}")

    def adicionar_novos_campos_produtos(self):
        """Adiciona os novos campos à tabela produtos se ainda não existirem"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(produtos)")
        colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]

        novos_campos = [
            ('tamanho', 'TEXT'),
            ('cor', 'TEXT'),
            ('ea', 'TEXT'),
            ('referencia', 'TEXT')
        ]

        for campo, tipo in novos_campos:
            if campo not in colunas_existentes:
                try:
                    cursor.execute(f"ALTER TABLE produtos ADD COLUMN {campo} {tipo}")
                    conn.commit()
                    print(f"Campo {campo} adicionado com sucesso")
                except Exception as e:
                    print(f"Erro ao adicionar campo {campo}: {e}")