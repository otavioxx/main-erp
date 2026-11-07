import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_pacote_instalador_contem_codigo_e_componentes(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "distribuicao"))
    import criar_instalador
    import criar_release

    pacote = criar_instalador.construir_instalador(tmp_path)
    with zipfile.ZipFile(pacote) as arquivo:
        nomes = set(arquivo.namelist())
        assert arquivo.testzip() is None
        assert {
            "__main__.py", "main.py", "icon.ico", "requirements.txt",
            "distribuicao/instalar.py", "distribuicao/launcher.pyw",
            "distribuicao/criar_release.py", "distribuicao/criar_atalhos.ps1",
        } <= nomes
        assert {
            caminho.relative_to(ROOT).as_posix()
            for caminho in criar_release.arquivos_do_release()
        } <= nomes
        assert not any(nome.startswith(("tests/", ".git/", "dados/")) for nome in nomes)


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
    env = {**os.environ, "TEMP": str(temporarios), "TMP": str(temporarios),
           "TMPDIR": str(temporarios)}
    resultado = subprocess.run(
        [sys.executable, str(pacote), str(marcador)], env=env, check=False,
        capture_output=True, text=True,
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
        [sys.executable, str(pacote)], check=False, capture_output=True, text=True,
    )
    assert resultado.returncode != 0
    assert "Caminho inválido" in resultado.stderr
    assert not (tmp_path / "fora.txt").exists()
