import os
import subprocess
import sys
from pathlib import Path

import pytest


def _executar(script, tmp_path, *argumentos, escala="1"):
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": escala,
        "PYTHONPATH": str(root),
    }
    return subprocess.run(
        [sys.executable, "-c", script, *argumentos],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("tema", ["light", "dark"])
@pytest.mark.parametrize("escala", ["1", "1.25", "1.5"])
def test_splash_usa_tema_e_atualiza_progresso(tmp_path, tema, escala):
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
splash = show_splash()
app.processEvents()
pixmap = splash.pixmap()
escala = pixmap.devicePixelRatio()
assert escala == float(sys.argv[2])
assert pixmap.width() == round(450 * escala)
assert pixmap.height() == round(300 * escala)
assert splash.width() == 450 and splash.height() == 300
imagem = pixmap.toImage()

# Fundo plano (sem faixa de cabeçalho) e borda reta na cor do tema
assert imagem.pixelColor(round(10 * escala), round(10 * escala)) == QColor(cores.surface)
assert imagem.pixelColor(round(10 * escala), round(100 * escala)) == QColor(cores.surface)
assert imagem.pixelColor(0, 0) == QColor(cores.border)
assert imagem.pixelColor(0, round(100 * escala)) == QColor(cores.border)
for x, y in ((0, 0), (imagem.width() - 1, 0),
             (0, imagem.height() - 1), (imagem.width() - 1, imagem.height() - 1)):
    assert imagem.pixelColor(x, y).alpha() == 255

# Barra sem progresso: só o trilho; com 60%, trilho e preenchimento em cores sólidas
y_barra = round(216 * escala)
assert imagem.pixelColor(round(100 * escala), y_barra) == QColor(cores.border)
splash.atualizar("Verificando banco de dados e migrações...", 60)
app.processEvents()
assert splash.pixmap().toImage() != imagem
imagem = splash.pixmap().toImage()
assert imagem.pixelColor(round(100 * escala), y_barra) == QColor(cores.accent_text)
assert imagem.pixelColor(round(300 * escala), y_barra) == QColor(cores.border)

# Sem percentual a barra permanece; ela nunca retrocede
splash.atualizar("Preparando interface...")
splash.atualizar("Etapa anterior", 10)
assert splash.percentual == 60
app.processEvents()
imagem_final = splash.pixmap().toImage()
assert imagem_final.pixelColor(round(100 * escala), y_barra) == QColor(cores.accent_text)
assert imagem_final.pixelColor(round(300 * escala), y_barra) == QColor(cores.border)

window = QWidget()
window.show()
splash.finish(window)
assert not splash.isVisible()
window.close()
"""
    resultado = _executar(script, tmp_path, tema, escala, escala=escala)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_percentual_do_carregamento_das_telas(tmp_path):
    script = """
from mainerp.app import percentual_carregamento_telas as pct

assert pct("Carregando tela 1/8: Vendas...") == 20
assert pct("Carregando tela 5/8: Clientes...") == 60
assert pct("Carregando tela 8/8: Configurações...") == 90
valores = [pct(f"Carregando tela {i}/8: x...") for i in range(1, 9)]
assert valores == sorted(valores) and valores[-1] < 100
# Mensagens sem posição, ou com posição inválida, não alteram o progresso
assert pct("Preparando interface...") is None
assert pct("Carregando tela 0/8: x...") is None
assert pct("Carregando tela 9/8: x...") is None
assert pct("Carregando tela 1/0: x...") is None
"""
    resultado = _executar(script, tmp_path)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
