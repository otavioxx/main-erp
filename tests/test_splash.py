import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("tema", ["light", "dark"])
@pytest.mark.parametrize("escala", ["1", "1.25", "1.5"])
def test_splash_usa_tema_e_atualiza_progresso(tmp_path, tema, escala):
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": escala,
        "PYTHONPATH": str(root),
    }
    script = """
import sys
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QWidget
from mainerp.app import show_splash
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.theme_tokens import CLARO, ESCURO

app = QApplication([])
aplicar_tema(app, sys.argv[1])
cores = CLARO if sys.argv[1] == "light" else ESCURO
splash = show_splash("MainERP")
app.processEvents()
pixmap = splash.pixmap()
escala = pixmap.devicePixelRatio()
assert escala == float(sys.argv[2])
assert pixmap.width() == round(450 * escala)
assert pixmap.height() == round(300 * escala)
assert splash.width() == 450 and splash.height() == 300
imagem = pixmap.toImage()
assert imagem.pixelColor(round(10 * escala), round(10 * escala)) == QColor(cores.nav_bg)
assert imagem.pixelColor(round(10 * escala), round(100 * escala)) == QColor(cores.surface)
assert imagem.pixelColor(0, 0) == QColor(cores.border)
assert imagem.pixelColor(0, round(100 * escala)) == QColor(cores.border)
for x, y in ((0, 0), (imagem.width() - 1, 0),
             (0, imagem.height() - 1), (imagem.width() - 1, imagem.height() - 1)):
    assert imagem.pixelColor(x, y).alpha() == 255
splash.update_message("Verificando banco de dados e migrações...")
app.processEvents()
assert splash.pixmap().toImage() != imagem
imagem = splash.pixmap().toImage()
assert imagem.pixelColor(round(29 * escala), round(200 * escala)) == QColor(cores.accent)
splash.update_message("Preparando interface...")
app.processEvents()
assert splash.pixmap().toImage() != imagem
window = QWidget()
window.show()
splash.finish(window)
assert not splash.isVisible()
window.close()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", script, tema, escala],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
