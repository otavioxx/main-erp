from pathlib import Path

import pytest

from mainerp.data.database import Database
from mainerp.data.models import empresa as empresa_model
from mainerp.reports import (
    print_condicional,
    print_pedido,
    print_relat_condicional,
    print_relat_pedido,
    print_relat_recebimento,
    print_relat_venda,
    print_venda,
)


@pytest.fixture
def database(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "money-reports.db"))
    for module in (
        print_condicional,
        print_pedido,
        print_relat_condicional,
        print_relat_pedido,
        print_relat_recebimento,
        print_relat_venda,
        print_venda,
    ):
        monkeypatch.setattr(module, "obter_database", lambda: database)
    monkeypatch.setattr(empresa_model, "obter_database", lambda: database)

    with database.transacao() as cursor:
        cursor.execute("INSERT INTO clientes (id, nome) VALUES (1, 'Cliente')")
        cursor.execute("INSERT INTO fornecedores (id, nome) VALUES (1, 'Fornecedor')")
        cursor.execute(
            """
            INSERT INTO produtos
                (id, nome, preco_custo, preco_venda, cor, tamanho, referencia)
            VALUES (1, 'Produto', 3.21, 4.32, 'Azul', 'M', 'REF-1')
            """
        )
        cursor.execute(
            """
            INSERT INTO vendas
                (id, cliente_id, data_venda, total, desconto, forma_pagamento, status)
            VALUES (1, 1, '2026-03-01', 10.02, 0.34, 'Pix', 'concluida')
            """
        )
        cursor.execute(
            """
            INSERT INTO itens_venda
                (venda_id, produto_id, quantidade, preco_unitario, desconto)
            VALUES (1, 1, 2, 5.01, 0)
            """
        )
        cursor.execute(
            """
            INSERT INTO duplicatas
                (venda_id, cliente_id, numero_parcela, valor_parcela, data_vencimento)
            VALUES (1, 1, 1, 5.01, '2026-04-01')
            """
        )
        cursor.execute(
            """
            INSERT INTO duplicatas_pagas
                (venda_id, cliente_id, numero_parcela, valor_original,
                 valor_recebido, data_vencimento, data_pagamento, forma_pagamento)
            VALUES (1, 1, 2, 5.01, 5.02, '2026-04-01', '2026-04-02', 'Pix')
            """
        )
        cursor.execute(
            """
            INSERT INTO pedidos
                (id, fornecedor_id, data_pedido, valor_total, valor_frete, desconto)
            VALUES (1, 1, '2026-03-01', 8.64, 1.23, 0.45)
            """
        )
        cursor.execute(
            """
            INSERT INTO itens_pedido
                (pedido_id, produto_id, quantidade, preco_custo, preco_venda, subtotal)
            VALUES (1, 1, 2, 3.21, 4.32, 6.42)
            """
        )
        cursor.execute(
            """
            INSERT INTO condicionais
                (id, cliente_id, data_condicional, desconto)
            VALUES (1, 1, '2026-03-01', 0.12)
            """
        )
        cursor.execute(
            """
            INSERT INTO itens_condicional
                (condicional_id, produto_id, quantidade, preco_unitario)
            VALUES (1, 1, 3, 2.14)
            """
        )

    yield database
    database.close_connection()


def test_relatorios_leem_centavos_e_preservam_valores_em_reais(database, tmp_path):
    item_pedido = print_pedido.PrintPedido.buscar_itens_pedido(1)[0]
    item_venda = print_venda.PrintVenda.buscar_itens_venda_detalhados(1)[0]
    parcelas = print_venda.PrintVenda.buscar_parcelas_venda(1)
    pedido = print_relat_pedido.PrintRelatPedido._buscar_pedidos_completos()[0]
    venda = print_relat_venda.PrintRelatVenda._buscar_vendas_com_cliente()[0]
    condicional = print_relat_condicional.PrintRelatCondicional
    dados_condicional = condicional._buscar_condicionais_com_cliente()[0]
    item_condicional = (
        print_condicional.PrintCondicional.buscar_itens_condicional_detalhados(1)[0]
    )

    assert item_pedido[7:10] == (3.21, 4.32, 6.42)
    assert item_venda[6] == 5.01
    assert [parcela[1] for parcela in parcelas] == [5.01, 5.02]
    assert pedido[4:6] == (8.64, 1.23)
    assert pedido[8] == 0.45
    assert venda[3] == 10.02
    assert venda[7] == 0.34
    assert dados_condicional[6] == 0.12
    assert condicional._calcular_total_condicional(1) == 6.42
    assert item_condicional[6] == 2.14

    arquivo = print_relat_recebimento.PrintRelatRecebimento.gerar_relatorio(
        None, None, "Todas", pasta_destino=str(tmp_path)
    )
    assert Path(arquivo).exists()
