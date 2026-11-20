import sqlite3

import pytest

from mainerp.data.database import Database, MigracaoError
from mainerp.data.models import base_model
from mainerp.data.models.produto import Produto


class DatabaseEsquema3(Database):
    MIGRACOES = Database.MIGRACOES[:3]


COLUNAS_REAIS = {
    "produtos": ("preco_custo", "preco_venda"),
    "vendas": ("total", "desconto", "valor_entrada", "valor_financiado"),
    "itens_venda": ("preco_unitario", "desconto"),
    "duplicatas": ("valor_parcela",),
    "duplicatas_pagas": ("valor_original", "valor_recebido"),
    "condicionais": ("desconto",),
    "itens_condicional": ("preco_unitario",),
    "pedidos": ("valor_total", "valor_frete", "desconto"),
    "itens_pedido": ("preco_custo", "preco_venda", "subtotal"),
}


def remover_colunas_reais_em_memoria(origem: sqlite3.Connection) -> sqlite3.Connection:
    """Ensaio de migração: executa DDL somente em uma nova conexão em memória."""
    copia = sqlite3.connect(":memory:")
    try:
        origem.backup(copia)
        if copia.execute("PRAGMA user_version").fetchone() != (3,):
            raise ValueError("O ensaio requer uma cópia no esquema 3.")
        copia.execute("PRAGMA foreign_keys = ON")
        copia.execute("BEGIN")
        for tabela, campos in COLUNAS_REAIS.items():
            copia.execute(f'DROP TRIGGER "trg_{tabela}_centavos_insert"')
            copia.execute(f'DROP TRIGGER "trg_{tabela}_centavos_update"')
            for campo in campos:
                copia.execute(f'ALTER TABLE "{tabela}" DROP COLUMN "{campo}"')
        if (
            copia.execute("PRAGMA integrity_check").fetchall() != [("ok",)]
            or copia.execute("PRAGMA foreign_key_check").fetchone() is not None
        ):
            raise sqlite3.DatabaseError("A cópia migrada falhou na validação.")
        copia.execute("PRAGMA user_version = 4")
        copia.commit()
        return copia
    except BaseException:
        copia.close()
        raise


def test_migracao_4_preserva_centavos_sem_recalcular(tmp_path, monkeypatch):
    caminho = tmp_path / "schema3.db"
    banco = DatabaseEsquema3(str(caminho))
    try:
        origem = banco.get_connection()
        with banco.transacao() as cursor:
            cursor.execute(
                "INSERT INTO produtos (nome, preco_custo, preco_venda) "
                "VALUES ('Teste', 1.25, 2.50)"
            )
            cursor.execute(
                "INSERT INTO duplicatas (valor_parcela) VALUES (?)", (1.004999999999,)
            )
            cursor.execute("UPDATE duplicatas SET valor_parcela_centavos = 100")
        assert banco.versao_esquema() == 3
        assert origem.execute(
            "SELECT valor_parcela, valor_parcela_centavos FROM duplicatas"
        ).fetchone() == (1.004999999999, 100)
    finally:
        banco.close_connection()
    banco = Database(str(caminho))
    try:
        conn = banco.get_connection()
        assert banco.versao_esquema() == 4
        assert conn.execute(
            "SELECT valor_parcela_centavos FROM duplicatas"
        ).fetchone() == (100,)
        assert conn.execute(
            "SELECT preco_custo_centavos, preco_venda_centavos FROM produtos"
        ).fetchone() == (125, 250)
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        for tabela, campos in COLUNAS_REAIS.items():
            colunas = {
                coluna[1] for coluna in conn.execute(f'PRAGMA table_info("{tabela}")')
            }
            assert not set(campos) & colunas
            assert {f"{campo}_centavos" for campo in campos} <= colunas
        assert conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type = 'trigger' "
            "AND name LIKE 'trg_%_centavos_%'"
        ).fetchone() == (0,)
        monkeypatch.setattr(base_model, "obter_database", lambda: banco)
        produto = Produto.buscar_por_id(1)
        assert produto is not None
        assert (produto.preco_custo, produto.preco_venda) == (1.25, 2.50)
        assert Produto(nome="Novo", preco_custo=3.01, preco_venda=5.02).salvar()
        assert conn.execute(
            "SELECT preco_custo_centavos, preco_venda_centavos FROM produtos WHERE nome = 'Novo'"
        ).fetchone() == (301, 502)
    finally:
        banco.close_connection()
    (backup,) = (tmp_path / "backups").glob("pre_migracao_v3_para_v4_*.db")
    with sqlite3.connect(backup) as anterior:
        assert anterior.execute("PRAGMA user_version").fetchone() == (3,)
        assert anterior.execute(
            "SELECT valor_parcela, valor_parcela_centavos FROM duplicatas"
        ).fetchone() == (1.004999999999, 100)


def test_migracao_4_reverte_ddl_e_preserva_backup_se_falhar(tmp_path):
    caminho = tmp_path / "schema3.db"
    banco = DatabaseEsquema3(str(caminho))
    conn = banco.get_connection()
    conn.execute(
        "INSERT INTO produtos (nome, preco_custo, preco_venda) VALUES ('Teste', 1, 2)"
    )
    conn.execute('DROP TRIGGER "trg_itens_venda_centavos_update"')
    conn.commit()
    esquema = conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
    ).fetchall()
    banco.close_connection()

    with pytest.raises(MigracaoError, match="versão 4"):
        Database(str(caminho))

    with sqlite3.connect(caminho) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (3,)
        assert (
            conn.execute(
                "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"
            ).fetchall()
            == esquema
        )
        assert conn.execute(
            "SELECT preco_custo_centavos, preco_venda_centavos FROM produtos"
        ).fetchone() == (100, 200)
    (backup,) = (tmp_path / "backups").glob("pre_migracao_v3_para_v4_*.db")
    with sqlite3.connect(backup) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (3,)


def test_migracao_4_recusa_centavos_invalidos_sem_remover_dados(tmp_path):
    caminho = tmp_path / "schema3.db"
    banco = DatabaseEsquema3(str(caminho))
    conn = banco.get_connection()
    conn.execute(
        "INSERT INTO produtos (nome, preco_custo, preco_venda) VALUES ('Teste', 1, 2)"
    )
    conn.execute("UPDATE produtos SET preco_custo_centavos = 1.5")
    conn.commit()
    banco.close_connection()

    with pytest.raises(MigracaoError, match="produtos.preco_custo_centavos"):
        Database(str(caminho))

    with sqlite3.connect(caminho) as conn:
        assert conn.execute("PRAGMA user_version").fetchone() == (3,)
        assert conn.execute(
            "SELECT preco_custo, preco_custo_centavos FROM produtos"
        ).fetchone() == (1, 1.5)
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    assert list((tmp_path / "backups").glob("pre_migracao_v3_para_v4_*.db"))


def test_migracao_inicial_cria_esquema_base_e_aplica_apenas_uma_vez(tmp_path):
    caminho_banco = tmp_path / "novo.db"

    banco = Database(str(caminho_banco))
    try:
        conn = banco.get_connection()
        tabelas = {
            linha[0]
            for linha in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

        assert banco.versao_esquema() == Database.MIGRACOES[-1][0]
        assert {"produtos", "vendas", "duplicatas", "pedidos"} <= tabelas

        banco.migrar()

        assert banco.versao_esquema() == Database.MIGRACOES[-1][0]
    finally:
        banco.close_connection()


def test_migracao_cria_indices_de_consulta_e_e_idempotente(tmp_path):
    banco = Database(str(tmp_path / "indices.db"))
    try:
        conn = banco.get_connection()
        indices = {
            linha[0]
            for linha in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        esperados = {
            "idx_vendas_status_data",
            "idx_vendas_cliente_status_data",
            "idx_pedidos_status_data",
            "idx_pedidos_fornecedor_status_data",
            "idx_condicionais_status_data",
            "idx_condicionais_cliente_status_data",
            "idx_duplicatas_status_vencimento",
            "idx_duplicatas_cliente_status_vencimento",
            "idx_duplicatas_venda_status",
            "idx_duplicatas_pagas_cliente_data",
            "idx_duplicatas_pagas_venda",
            "idx_itens_venda_venda",
            "idx_itens_condicional_condicional",
            "idx_itens_pedido_pedido",
        }
        assert esperados <= indices

        conn.executemany(
            "INSERT INTO vendas (status, data_venda) VALUES (?, ?)",
            [
                (
                    "concluida" if indice % 5 == 0 else "pendente",
                    f"2024-01-{indice % 28 + 1:02d}",
                )
                for indice in range(500)
            ],
        )
        plano = conn.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT id FROM vendas
            WHERE status = ? AND data_venda BETWEEN ? AND ?
            """,
            ("concluida", "2024-01-03", "2024-01-05"),
        ).fetchall()
        assert any("idx_vendas_status_data" in linha[3] for linha in plano)

        banco.migrar()
        indices_apos_segunda_execucao = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type = 'index' AND name LIKE 'idx_%'"
        ).fetchone()[0]
        assert indices_apos_segunda_execucao == len(esperados) + 2
    finally:
        banco.close_connection()


def test_migracao_monetaria_cria_centavos_preserva_valores_e_sincroniza_escritas(
    tmp_path,
):
    caminho_banco = tmp_path / "centavos.db"
    banco = DatabaseEsquema3(str(caminho_banco))
    try:
        conn = banco.get_connection()
        conn.execute("INSERT INTO clientes (id, nome) VALUES (1, 'Cliente de teste')")
        conn.execute(
            "INSERT INTO vendas (id, cliente_id, total, desconto) "
            "VALUES (1, 1, 0.1 + 0.2, 1.005)"
        )
        conn.commit()

        assert conn.execute(
            "SELECT total, total_centavos, desconto_centavos FROM vendas WHERE id = 1"
        ).fetchone() == (0.30000000000000004, 30, 101)

        conn.execute(
            "UPDATE vendas SET total = ?, desconto = ? WHERE id = 1",
            (12.345, -1.005),
        )
        conn.commit()
        assert conn.execute(
            "SELECT total_centavos, desconto_centavos FROM vendas WHERE id = 1"
        ).fetchone() == (1235, -101)

        conn.execute(
            "INSERT INTO produtos (nome, preco_custo, preco_venda) VALUES (?, ?, ?)",
            ("Produto de teste", 3.99, 5.5),
        )
        conn.commit()
        assert conn.execute(
            "SELECT preco_custo_centavos, preco_venda_centavos FROM produtos"
        ).fetchone() == (399, 550)

        banco.migrar()
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master "
                "WHERE type = 'trigger' AND name LIKE 'trg_%_centavos_%'"
            ).fetchone()[0]
            == 18
        )
    finally:
        banco.close_connection()

    conexao_legada = sqlite3.connect(caminho_banco)
    try:
        conexao_legada.execute("UPDATE vendas SET total = 7.25 WHERE id = 1")
        conexao_legada.commit()
        assert conexao_legada.execute(
            "SELECT total_centavos FROM vendas WHERE id = 1"
        ).fetchone() == (725,)
    finally:
        conexao_legada.close()


def test_migracao_monetaria_cria_centavos_para_todos_os_campos_do_esquema(tmp_path):
    banco = Database(str(tmp_path / "todos_centavos.db"))
    campos_monetarios = {
        "produtos": {"preco_custo", "preco_venda"},
        "vendas": {"total", "desconto", "valor_entrada", "valor_financiado"},
        "itens_venda": {"preco_unitario", "desconto"},
        "duplicatas": {"valor_parcela"},
        "duplicatas_pagas": {"valor_original", "valor_recebido"},
        "condicionais": {"desconto"},
        "itens_condicional": {"preco_unitario"},
        "pedidos": {"valor_total", "valor_frete", "desconto"},
        "itens_pedido": {"preco_custo", "preco_venda", "subtotal"},
    }

    try:
        conn = banco.get_connection()
        assert sum(map(len, campos_monetarios.values())) == 19
        for tabela, campos in campos_monetarios.items():
            colunas = set(banco._colunas(conn.cursor(), tabela))
            assert {f"{campo}_centavos" for campo in campos} <= colunas
    finally:
        banco.close_connection()


def test_migracao_adiciona_colunas_ausentes_e_preserva_dados_anteriores(tmp_path):
    caminho_banco = tmp_path / "legado.db"
    conn = sqlite3.connect(caminho_banco)
    conn.executescript("""
        CREATE TABLE condicionais (id INTEGER PRIMARY KEY);
        CREATE TABLE produtos (id INTEGER PRIMARY KEY, preco_custo REAL);
        CREATE TABLE itens_pedido (
            id INTEGER PRIMARY KEY,
            preco_custo REAL
        );
        CREATE TABLE vendas (id INTEGER PRIMARY KEY, total REAL);
        CREATE TABLE pedidos (id INTEGER PRIMARY KEY);
        INSERT INTO produtos (id, preco_custo) VALUES (1, 10);
        INSERT INTO itens_pedido (id, preco_custo) VALUES (1, 10);
        INSERT INTO vendas (id, total) VALUES (1, 80);
    """)
    conn.commit()
    conn.close()

    banco = Database(str(caminho_banco))
    try:
        conn = banco.get_connection()

        assert banco.versao_esquema() == Database.MIGRACOES[-1][0]
        assert conn.execute(
            "SELECT preco_venda_centavos FROM itens_pedido WHERE id = 1"
        ).fetchone() == (1300,)
        assert conn.execute(
            "SELECT valor_financiado_centavos FROM vendas WHERE id = 1"
        ).fetchone() == (8000,)

        colunas_condicionais = banco._colunas(conn.cursor(), "condicionais")
        colunas_pedidos = banco._colunas(conn.cursor(), "pedidos")
        assert "desconto_centavos" in colunas_condicionais
        assert "desconto_centavos" in colunas_pedidos
    finally:
        banco.close_connection()

    assert list((tmp_path / "backups").glob("pre_migracao_*.db"))
