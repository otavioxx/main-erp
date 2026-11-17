import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QMessageBox,
    QStyle,
    QStyleOptionSpinBox,
)

from mainerp.data.database import Database
from mainerp.data.models.cliente import Cliente
from mainerp.data.models.produto import Produto
from mainerp.ui.dialogs.pagamento_dialog import PagamentoDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_entrada_no_crediario_e_troca_de_forma(app):
    dialogo = PagamentoDialog(100.01, 1)
    dialogo.show()
    app.processEvents()
    assert dialogo.entrada_group.isHidden()

    dialogo.rb_crediario.setChecked(True)
    assert dialogo.get_dados()["valor_entrada"] == 0
    assert dialogo.get_dados()["valor_financiado"] == 100.01
    dialogo.entrada_input.setValue(25)
    dialogo.parcelas_spinner.setValue(3)
    assert not dialogo.entrada_group.isHidden()
    assert "75,01" in dialogo.label_financiado.text()
    assert "25,00" in dialogo.label_valor_parcela.text()
    assert "25,01" in dialogo.label_valor_parcela.text()
    dialogo._validar_e_aceitar()
    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.get_dados()["valor_entrada"] == 25
    assert dialogo.get_dados()["valor_financiado"] == 75.01

    dialogo.rb_pix.setChecked(True)
    assert dialogo.entrada_group.isHidden()
    assert dialogo.get_dados()["valor_entrada"] == 0
    assert dialogo.get_dados()["valor_financiado"] == 100.01
    dialogo.rb_crediario.setChecked(True)
    assert dialogo.get_dados()["valor_entrada"] == 25


def test_clicar_na_entrada_seleciona_valor_para_substituicao(app):
    dialogo = PagamentoDialog(100, 1)
    dialogo.show()
    dialogo.rb_crediario.setChecked(True)
    app.processEvents()
    campo = dialogo.entrada_input
    editor = campo.findChild(QLineEdit)
    assert editor is not None
    dialogo.parcelas_spinner.setFocus()

    # Os stubs do PyQt declaram os métodos estáticos de QTest como métodos de instância.
    QTest.mouseClick(editor, Qt.MouseButton.LeftButton)  # type: ignore[reportCallIssue]
    assert editor.selectedText() == campo.cleanText()
    QTest.keyClicks(editor, "25")  # type: ignore[reportCallIssue]
    assert campo.value() == 25

    QTest.mouseClick(editor, Qt.MouseButton.LeftButton)  # type: ignore[reportCallIssue]
    assert editor.selectedText() == campo.cleanText()
    QTest.keyClicks(editor, "12")  # type: ignore[reportCallIssue]
    assert campo.value() == 12
    assert dialogo.get_dados()["valor_financiado"] == 88

    dialogo.parcelas_spinner.setFocus()
    campo.setFocus(Qt.FocusReason.TabFocusReason)
    assert editor.selectedText().endswith(campo.cleanText())
    QTest.keyClicks(editor, "12")  # type: ignore[reportCallIssue]
    assert campo.value() == 12
    opcoes = QStyleOptionSpinBox()
    campo.initStyleOption(opcoes)
    estilo = campo.style()
    assert estilo is not None
    seta = estilo.subControlRect(
        QStyle.ComplexControl.CC_SpinBox,
        opcoes,
        QStyle.SubControl.SC_SpinBoxUp,
        campo,
    )
    QTest.mouseClick(campo, Qt.MouseButton.LeftButton, pos=seta.center())  # type: ignore[reportCallIssue]
    assert campo.value() == 13


@pytest.mark.usefixtures("app")
def test_entrada_igual_ao_total_e_parcelas_zero_sao_rejeitadas(monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args[2]))
    dialogo = PagamentoDialog(1, 1)
    dialogo.rb_crediario.setChecked(True)
    dialogo.entrada_input.setValue(1)
    dialogo._validar_e_aceitar()
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert "menor que o total" in avisos[-1]

    dialogo.entrada_input.setValue(0.99)
    dialogo.parcelas_spinner.setValue(2)
    dialogo._validar_e_aceitar()
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert "parcelas de pelo menos" in avisos[-1]


@pytest.mark.usefixtures("app")
def test_venda_crediario_com_entrada_persiste_parcelas_sem_recebimento(
    tmp_path, monkeypatch
):
    banco = Database(str(tmp_path / "venda.db"))
    for modulo in (
        "mainerp.data.database_utils",
        "mainerp.data.models.base_model",
        "mainerp.data.models.duplicata",
    ):
        monkeypatch.setattr(f"{modulo}.obter_database", lambda: banco)

    try:
        with banco.transacao() as cursor:
            cursor.execute("INSERT INTO clientes (id, nome) VALUES (1, 'Cliente')")
        produto = Produto(nome="Produto", preco_custo=10, preco_venda=100.01, estoque=2)
        produto.salvar()

        def executar_pagamento(dialogo):
            dialogo.rb_crediario.setChecked(True)
            dialogo.entrada_input.setValue(25)
            dialogo.parcelas_spinner.setValue(3)
            dialogo._validar_e_aceitar()
            return dialogo.result()

        erros = []
        monkeypatch.setattr(PagamentoDialog, "exec", executar_pagamento)
        monkeypatch.setattr(QMessageBox, "information", lambda *_args: None)
        monkeypatch.setattr(
            QMessageBox, "critical", lambda *args: erros.append(args[2])
        )
        venda = ProdutoVendaDialog()
        venda.cliente_selecionado = Cliente(id=1, nome="Cliente")
        venda.produtos_selecionados = [
            {"id": produto.id, "quantidade": 1, "preco": 100.01, "subtotal": 100.01}
        ]
        venda._finalizar_venda()

        assert not erros
        assert venda.result() == QDialog.DialogCode.Accepted
        conexao = banco.get_connection()
        assert conexao.execute(
            "SELECT total_centavos, valor_entrada_centavos, valor_financiado_centavos FROM vendas"
        ).fetchone() == (10001, 2500, 7501)
        parcelas = conexao.execute(
            "SELECT valor_parcela_centavos FROM duplicatas ORDER BY numero_parcela"
        ).fetchall()
        assert parcelas == [(2500,), (2500,), (2501,)]
        assert 2500 + sum(parcela[0] for parcela in parcelas) == 10001
        assert conexao.execute("SELECT COUNT(*) FROM duplicatas_pagas").fetchone() == (
            0,
        )
        assert conexao.execute("SELECT estoque FROM produtos").fetchone() == (1,)
    finally:
        banco.close_connection()
