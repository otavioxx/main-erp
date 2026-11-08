import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_modelo_listagens_e_status_em_processo_isolado(tmp_path, tema):
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": "1",
        "PYTHONPATH": str(ROOT),
    }
    script = r"""
import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QMessageBox, QPushButton
from mainerp.data.automatic_backup import BackupAutomatico
from mainerp.data.models.cliente import Cliente
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.theme_tokens import cores_do_tema
from mainerp.ui.views.main_window import MainWindow
from mainerp.ui.views.cliente_view import ClienteDialog
from mainerp.ui.dialogs.fornecedor_dialog import FornecedorDialog
from mainerp.ui.dialogs.produto_dialog import ProdutoDialog
from mainerp.ui.dialogs.recebimento_dialog import RecebimentoDialog
from mainerp.ui.dialogs.condicional_dialog import CondicionalDialog
from mainerp.ui.dialogs.pedido_dialog import PedidoDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog

app = QApplication([])
BackupAutomatico.iniciar = lambda self: None
aplicar_tema(app, sys.argv[1])
janela = MainWindow()
app.processEvents()
views = (
    (janela.venda_view, "tabela_vendas", "busca_cliente", "btn_nova_venda"),
    (janela.condicional_view, "tabela_condicionais", "busca_cliente", "btn_nova_condicional"),
    (janela.pedido_view, "tabela_pedidos", "busca_fornecedor", "btn_novo_pedido"),
    (janela.recebimento_view, "tabela_duplicatas", "busca_cliente", None),
    (janela.cliente_view, "tabela_clientes", "busca_edit", "btn_novo"),
    (janela.produto_view, "tabela_produtos", "busca_edit", "btn_novo"),
    (janela.fornecedor_view, "tabela_fornecedores", "busca_edit", "btn_novo"),
)
for indice, (view, tabela_nome, busca_nome, novo_nome) in enumerate(views):
    janela._selecionar_aba(indice)
    janela.activateWindow()
    app.processEvents()
    tabela = getattr(view, tabela_nome)
    rodape = view.findChild(QLabel, "total_registros")
    assert rodape is not None
    for quantidade in (3, 1, 0):
        tabela.setRowCount(quantidade)
        assert rodape.text() == f"Registros exibidos: {quantidade}"
    busca = getattr(view, busca_nome)
    assert not busca.findChild(QAction, "icone_pesquisa_listagem").icon().isNull()
    tabela.setFocus()
    QTest.keyClick(tabela, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert busca.hasFocus(), tabela_nome
    pesquisar = next(b for b in view.findChildren(QPushButton) if b.text() == "Pesquisar")
    tabela.setFocus()
    pesquisar.click()
    assert busca.hasFocus(), tabela_nome
    if novo_nome:
        botao = getattr(view, novo_nome)
        assert not botao.icon().isNull()
        acionado = []
        botao.clicked.disconnect()
        botao.clicked.connect(lambda: acionado.append(True))
        QTest.keyClick(busca, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
        assert acionado == [True], tabela_nome
        dialogo = QDialog(janela)
        dialogo.setModal(True)
        dialogo.show()
        app.processEvents()
        QTest.keyClick(dialogo, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
        assert acionado == [True], tabela_nome
        dialogo.close()
        app.processEvents()
clientes = janela.cliente_view
clientes.dados = [Cliente(id=1, nome="ALFA"), Cliente(id=2, nome="BETA")]
clientes.busca_edit.clear()
clientes._filtrar_clientes()
rodape_clientes = clientes.findChild(QLabel, "total_registros")
assert rodape_clientes.text() == "Registros exibidos: 2"
clientes.busca_edit.setText("ALFA")
assert rodape_clientes.text() == "Registros exibidos: 1"
clientes.busca_edit.setText("INEXISTENTE")
assert rodape_clientes.text() == "Registros exibidos: 0"
assert janela.status_widget.label_empresa.text() == janela.config_view.empresa.nome
janela.config_view.nome_edit.setText("Empresa de teste")
QMessageBox.information = lambda *args: QMessageBox.StandardButton.Ok
janela.config_view.salvar_configuracoes()
assert janela.status_widget.label_empresa.text() == janela.config_view.empresa.nome
assert janela.status_widget.label_empresa.text() == "EMPRESA DE TESTE"
assert janela.status_widget.label_version.text()
assert janela.status_widget.label_backup.text()
novo_tema = "dark" if sys.argv[1] == "light" else "light"
aplicar_tema(app, novo_tema)
for view, _, busca_nome, _ in views:
    for botao in view.findChildren(QPushButton):
        if botao.property("icone_listagem"):
            assert not botao.icon().isNull()
    assert not getattr(view, busca_nome).findChild(QAction, "icone_pesquisa_listagem").icon().isNull()
pesquisar = next(b for b in janela.cliente_view.findChildren(QPushButton) if b.text() == "Pesquisar")
imagem = pesquisar.icon().pixmap(QSize(24, 24)).toImage()
cores = [imagem.pixelColor(x, y) for x in range(imagem.width()) for y in range(imagem.height()) if imagem.pixelColor(x, y).alpha() == 255]
assert cores and all(cor == QColor(cores_do_tema(novo_tema).text_primary) for cor in cores)
for dialogo in (ClienteDialog(), FornecedorDialog(), ProdutoDialog(), RecebimentoDialog((1, 1, 1, 1, 100, '2026-01-01'))):
    caixa = dialogo.findChild(QDialogButtonBox)
    assert caixa.button(QDialogButtonBox.StandardButton.Ok).property("class") == "primary"
    assert caixa.button(QDialogButtonBox.StandardButton.Cancel).property("class") == "secondary"
for dialogo, principal in ((CondicionalDialog(), "btn_salvar"), (PedidoDialog(), "btn_finalizar"), (ProdutoVendaDialog(), "btn_finalizar")):
    assert getattr(dialogo, principal).property("class") == "primary"
    cancelar = next(b for b in dialogo.findChildren(QPushButton) if b.text() == "Cancelar")
    assert cancelar.property("class") == "secondary"
janela.hide()
janela.deleteLater()
app.processEvents()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, tema],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
