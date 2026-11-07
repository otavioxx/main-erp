import sqlite3

from database import Database


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

        colunas_condicionais = banco._colunas(
            conn.cursor(), "condicionais"
        )
        colunas_pedidos = banco._colunas(conn.cursor(), "pedidos")
        assert "desconto" in colunas_condicionais
        assert "desconto" in colunas_pedidos
    finally:
        banco.close_connection()

    assert list((tmp_path / "backups").glob("pre_migracao_*.db"))
