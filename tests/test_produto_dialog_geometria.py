import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_editores_numericos_tem_espaco_para_os_valores(tmp_path, tema):
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": "1",
        "PYTHONPATH": str(ROOT),
    }
    script = r"""
import sys
from PyQt6.QtWidgets import QApplication, QLineEdit
from mainerp.data.models.produto import Produto
from mainerp.ui.dialogs.produto_dialog import ProdutoDialog
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.theme_tokens import DIMENSOES

app = QApplication([])
aplicar_tema(app, sys.argv[1])
for produto in (
    Produto(preco_custo=12.34, preco_venda=567.89),
    Produto(id=1, preco_custo=12.34, preco_venda=567.89, estoque=123),
):
    dialogo = ProdutoDialog(produto)
    dialogo.show()
    app.processEvents()
    campos = [dialogo.preco_custo_spin, dialogo.preco_venda_spin]
    if produto.id is not None:
        campos.append(dialogo.estoque_spin)
    for campo in campos:
        editor = campo.findChild(QLineEdit)
        assert editor is not None
        assert campo.width() >= 200
        assert editor.width() >= campo.width() - 10, (campo.width(), editor.width())
        assert editor.width() > editor.fontMetrics().horizontalAdvance(editor.text()) + 20
        margens = editor.textMargins()
        assert margens.left() == DIMENSOES.espacamento
        assert margens.right() == DIMENSOES.espacamento
    dialogo.hide()
    dialogo.deleteLater()
    app.processEvents()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", script, tema],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
