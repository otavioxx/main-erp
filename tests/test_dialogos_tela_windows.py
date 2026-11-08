import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Requer backend Windows do Qt")
@pytest.mark.parametrize("escala", ["1.25", "1.5"])
def test_dialogos_e_botoes_na_area_util(tmp_path, escala):
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "windows",
        "QT_SCALE_FACTOR": escala,
        "PYTHONPATH": str(root),
    }
    script = r"""
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication, QPushButton, QScrollArea, QWidget
from mainerp.core.paths import preparar_ambiente
from mainerp.ui.dialogs.fornecedor_dialog import FornecedorDialog
from mainerp.ui.dialogs.restore_backup_dialog import RestoreBackupDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog
from mainerp.ui.dialogs.pedido_dialog import PedidoDialog
from mainerp.ui.views.cliente_view import ClienteDialog, ClienteView
from mainerp.ui.styles import aplicar_tema

preparar_ambiente()
app = QApplication([])
ClienteView._carregar_clientes = lambda self: None
view = ClienteView()
view.resize(1000, 600)
view.show()
app.processEvents()
assert view.tabela_clientes.columnWidth(1) == 200
assert view.tabela_clientes.horizontalScrollBar().maximum() > 0
view.resize(1200, 600)
app.processEvents()
assert view.tabela_clientes.columnWidth(1) == 200
view.close()
view.deleteLater()
app.processEvents()
for tema in ("light", "dark"):
    aplicar_tema(app, tema)
    pai = QWidget()
    pai.showMaximized()
    app.processEvents()
    for classe in (ClienteDialog, FornecedorDialog, RestoreBackupDialog, ProdutoVendaDialog, PedidoDialog):
        dialogo = classe(parent=pai)
        dialogo.show()
        app.processEvents()
        area = dialogo.screen().availableGeometry()
        assert area.contains(dialogo.frameGeometry()), (tema, classe.__name__, area, dialogo.frameGeometry())
        for botao in dialogo.findChildren(QPushButton):
            if botao.isVisible() and botao.text():
                ret = QRect(botao.mapToGlobal(botao.rect().topLeft()), botao.size())
                assert area.contains(ret), (tema, classe.__name__, botao.text(), ret)
        if isinstance(dialogo, (ClienteDialog, FornecedorDialog)):
            scroll = dialogo.findChild(QScrollArea)
            assert scroll is not None
            scroll.ensureWidgetVisible(dialogo.observacao_edit)
            app.processEvents()
            assert scroll.viewport().rect().contains(
                QRect(dialogo.observacao_edit.mapTo(scroll.viewport(), dialogo.observacao_edit.rect().topLeft()),
                      dialogo.observacao_edit.size())
            )
        dialogo.hide()
        dialogo.deleteLater()
        app.processEvents()
    pai.close()
    pai.deleteLater()
    app.processEvents()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
