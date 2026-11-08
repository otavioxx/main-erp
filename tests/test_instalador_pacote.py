import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_pacote_instalador_contem_codigo_e_componentes(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "distribuicao"))
    from distribuicao import criar_instalador, criar_release

    pacote = criar_instalador.construir_instalador(tmp_path)
    with zipfile.ZipFile(pacote) as arquivo:
        nomes = set(arquivo.namelist())
        assert arquivo.testzip() is None
        assert {
            "__main__.py",
            "main.py",
            "icon.ico",
            "requirements.txt",
            "distribuicao/instalar.py",
            "distribuicao/launcher.pyw",
            "distribuicao/criar_release.py",
            "distribuicao/criar_atalhos.ps1",
            "mainerp/ui/theme_tokens.py",
            "mainerp/ui/icones.py",
            "mainerp/ui/icons/shopping-cart.svg",
            "mainerp/ui/listagem_modelo.py",
            "mainerp/ui/icons/plus.svg",
            "mainerp/ui/icons/pencil.svg",
            "mainerp/ui/icons/trash-2.svg",
            "mainerp/ui/icons/search.svg",
            "mainerp/ui/icons/printer.svg",
            "mainerp/ui/icons/rotate-ccw.svg",
            "mainerp/ui/icons/circle-minus.svg",
            "mainerp/ui/icons/circle-x.svg",
            "mainerp/ui/icons/arrow-right-left.svg",
            "mainerp/ui/icons/check.svg",
            "mainerp/ui/icons/package-check.svg",
            "mainerp/ui/icons/hand-coins.svg",
            "mainerp/ui/icons/LICENSE-LUCIDE.txt",
            "mainerp/ui/icons/LICENSE-FEATHER.txt",
        } <= nomes
        assert {
            caminho.relative_to(ROOT).as_posix()
            for caminho in criar_release.arquivos_do_release()
        } <= nomes
        assert not any(nome.startswith(("tests/", ".git/", "dados/")) for nome in nomes)


@pytest.mark.parametrize("tipo", ["release", "instalador"])
def test_icones_funcionam_no_pacote_extraido(tmp_path, monkeypatch, tipo):
    monkeypatch.syspath_prepend(str(ROOT / "distribuicao"))
    from distribuicao import criar_instalador, criar_release

    pacote = (
        criar_release.construir_zip(tmp_path)
        if tipo == "release"
        else criar_instalador.construir_instalador(tmp_path)
    )
    destino = tmp_path / "extraido"
    with zipfile.ZipFile(pacote) as arquivo:
        arquivo.extractall(destino)
    script = """
import sys
sys.path.insert(0, sys.argv[1])
from PyQt6.QtWidgets import QApplication
from mainerp.ui.icones import icone
from mainerp.ui.styles import aplicar_tema
app = QApplication([])
aplicar_tema(app, "dark")
assert not icone("shopping-cart", "#ffffff").pixmap(24, 24).isNull()
for nome in ("plus", "pencil", "trash-2", "search", "printer", "rotate-ccw", "circle-minus", "circle-x", "arrow-right-left", "check", "package-check", "hand-coins"):
    assert not icone(nome, "#ffffff").pixmap(24, 24).isNull(), nome
"""
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path / "dados"),
        "QT_QPA_PLATFORM": "offscreen",
    }
    resultado = subprocess.run(
        [sys.executable, "-I", "-c", script, str(destino)],
        env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


@pytest.mark.parametrize("codigo", [0, 7])
def test_bootstrap_remove_somente_seus_temporarios(tmp_path, codigo):
    temporarios = tmp_path / "temporarios"
    temporarios.mkdir()
    externo = temporarios / "nao-remover.txt"
    externo.write_text("preservado", encoding="utf-8")
    marcador = tmp_path / "resultado.txt"
    pacote = tmp_path / "instalador.pyz"
    with zipfile.ZipFile(pacote, "w") as arquivo:
        arquivo.write(ROOT / "distribuicao" / "instalador_bootstrap.py", "__main__.py")
        arquivo.writestr(
            "distribuicao/instalar.py",
            "import pathlib, sys\n"
            "pathlib.Path(sys.argv[1]).write_text(__file__, encoding='utf-8')\n"
            f"sys.exit({codigo})\n",
        )
    env = {
        **os.environ,
        "TEMP": str(temporarios),
        "TMP": str(temporarios),
        "TMPDIR": str(temporarios),
    }
    resultado = subprocess.run(
        [sys.executable, str(pacote), str(marcador)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == codigo, resultado.stderr
    assert not Path(marcador.read_text(encoding="utf-8")).exists()
    assert list(temporarios.iterdir()) == [externo]
    assert externo.read_text(encoding="utf-8") == "preservado"
    assert pacote.is_file()


def test_bootstrap_recusa_caminhos_externos(tmp_path):
    pacote = tmp_path / "instalador.pyz"
    with zipfile.ZipFile(pacote, "w") as arquivo:
        arquivo.write(ROOT / "distribuicao" / "instalador_bootstrap.py", "__main__.py")
        arquivo.writestr("../fora.txt", "não deve ser criado")
    resultado = subprocess.run(
        [sys.executable, str(pacote)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode != 0
    assert "Caminho inválido" in resultado.stderr
    assert not (tmp_path / "fora.txt").exists()
