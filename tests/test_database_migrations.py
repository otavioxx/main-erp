import sqlite3

from mainerp.data.database import Database


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
            "SELECT preco_venda FROM itens_pedido WHERE id = 1"
        ).fetchone() == (13.0,)
        assert conn.execute(
            "SELECT valor_financiado FROM vendas WHERE id = 1"
        ).fetchone() == (80.0,)

        colunas_condicionais = banco._colunas(conn.cursor(), "condicionais")
        colunas_pedidos = banco._colunas(conn.cursor(), "pedidos")
        assert "desconto" in colunas_condicionais
        assert "desconto" in colunas_pedidos
    finally:
        banco.close_connection()

    assert list((tmp_path / "backups").glob("pre_migracao_*.db"))
