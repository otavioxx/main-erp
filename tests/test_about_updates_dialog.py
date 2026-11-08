import os
import subprocess
import sys
from pathlib import Path

import pytest

from mainerp.ui.dialogs import sobre_atualizacoes_dialog as novidades_ui
from mainerp.ui.dialogs.sobre_atualizacoes_dialog import (
    format_release_date,
    parse_changelog,
    preparar_novidades,
    registrar_novidades_lidas,
)


def test_parse_changelog_returns_versions_dates_and_details():
    changelog = """# Histórico de versões

## 0.09 - 2026-11-07

- Atualização online pelo GitHub.

## 0.08 - 2026-11-06

- Correções de vendas.

## 0.07

- Primeira versão distribuída.
"""

    assert parse_changelog(changelog) == [
        ("0.09", "2026-11-07", "- Atualização online pelo GitHub."),
        ("0.08", "2026-11-06", "- Correções de vendas."),
        ("0.07", None, "- Primeira versão distribuída."),
    ]


def test_format_release_date_handles_missing_and_invalid_values():
    assert format_release_date("2026-11-07") == "07/11/2026"
    assert format_release_date(None) == "Não informada"
    assert format_release_date("2026-13-40") == "2026-13-40"


@pytest.fixture
def releases(tmp_path):
    base = tmp_path / "releases"
    atual = base / "0.12.0"
    atual.mkdir(parents=True)
    (atual / "main.py").touch()
    (atual / "CHANGELOG.md").write_text(
        "# Histórico\n\n## 0.12.0 - 2026-11-08\n\n- Nova tela\n\n"
        "## 0.11.0\n\n- Nova função\n\n## 0.10.5\n\n- Antiga\n",
        encoding="utf-8",
    )
    return base, atual, tmp_path / "dados"


def _criar_release(base, versao, confirmada=True):
    pasta = base / versao
    pasta.mkdir()
    (pasta / "main.py").touch()
    if confirmada:
        (pasta / ".ok").touch()
    return pasta


def test_novidades_apenas_apos_atualizacao_e_uma_vez(releases):
    base, atual, dados = releases
    ok = str(atual / ".ok")
    assert preparar_novidades("0.12.0", atual, dados, ok) is None
    _criar_release(base, "0.10.5")
    _criar_release(base, "0.11.0", confirmada=False)
    marcador, notas = preparar_novidades("0.12.0", atual, dados, ok)
    assert "Nova tela" in notas and "Nova função" in notas
    assert "Antiga" not in notas
    assert "08/11/2026" in notas
    (atual / ".ok").touch()
    assert preparar_novidades("0.12.0", atual, dados, ok) is not None
    registrar_novidades_lidas(marcador)
    assert preparar_novidades("0.12.0", atual, dados, ok) is None
    assert preparar_novidades("0.12.0", atual, dados, None) is None
    assert preparar_novidades("0.12.0", atual, dados, str(base / ".ok")) is None


def test_rollback_e_versao_nao_confirmada_nao_simulam_atualizacao(releases):
    base, atual, dados = releases
    _criar_release(base, "0.13.0")
    _criar_release(base, "0.11.0", confirmada=False)
    assert preparar_novidades("0.12.0", atual, dados, str(atual / ".ok")) is None
    _criar_release(base, "0.10.5")
    assert preparar_novidades("0.12.0", atual, dados, str(atual / ".ok")) is None


def test_novidades_ausentes_nao_sao_marcadas_como_lidas(releases):
    base, atual, dados = releases
    _criar_release(base, "0.10.5")
    (atual / "CHANGELOG.md").write_text("## 0.11.0\n\n- Antiga", encoding="utf-8")
    with pytest.raises(ValueError, match="Não há novidades"):
        preparar_novidades("0.12.0", atual, dados, str(atual / ".ok"))
    assert not (dados / "novidades" / "0.12.0.lido").exists()


def test_falha_ao_registrar_nao_cria_marcador(releases, monkeypatch):
    _, _, dados = releases
    marcador = dados / "novidades" / "0.12.0.lido"

    def falhar(*args):
        raise OSError("falha simulada")

    monkeypatch.setattr("mainerp.ui.dialogs.sobre_atualizacoes_dialog.os.replace", falhar)
    with pytest.raises(OSError, match="falha simulada"):
        registrar_novidades_lidas(marcador)
    assert not marcador.exists()
    assert list(marcador.parent.iterdir()) == []


def test_falha_persistencia_avisa_e_permite_repeticao(releases, monkeypatch):
    base, atual, dados = releases
    _criar_release(base, "0.10.5")
    monkeypatch.setattr(novidades_ui, "CODE_DIR", atual)
    monkeypatch.setattr(novidades_ui, "DATA_DIR", dados)
    monkeypatch.setenv("MAINERP_OK_FILE", str(atual / ".ok"))
    mensagens = []
    exibidas = []

    class Dialogo:
        def __init__(self, versao, notas, parent):
            exibidas.append(notas)

        def exec(self):
            return 0

    def falhar(_marcador):
        raise OSError("disco inacessível")

    monkeypatch.setattr(novidades_ui, "NovidadesDialog", Dialogo)
    monkeypatch.setattr(novidades_ui, "registrar_novidades_lidas", falhar)
    monkeypatch.setattr(
        novidades_ui.QMessageBox, "warning", lambda *args: mensagens.append(args)
    )
    novidades_ui.mostrar_novidades_apos_atualizacao(None, "0.12.0")
    assert "Nova tela" in exibidas[0]
    assert "poderão aparecer novamente" in mensagens[0][2]
    assert preparar_novidades("0.12.0", atual, dados, str(atual / ".ok")) is not None


def test_historico_indisponivel_avisa_sem_marcar_leitura(releases, monkeypatch):
    base, atual, dados = releases
    _criar_release(base, "0.10.5")
    (atual / "CHANGELOG.md").unlink()
    monkeypatch.setattr(novidades_ui, "CODE_DIR", atual)
    monkeypatch.setattr(novidades_ui, "DATA_DIR", dados)
    monkeypatch.setenv("MAINERP_OK_FILE", str(atual / ".ok"))
    mensagens = []
    monkeypatch.setattr(
        novidades_ui.QMessageBox, "warning", lambda *args: mensagens.append(args)
    )
    novidades_ui.mostrar_novidades_apos_atualizacao(None, "0.12.0")
    assert "Não foi possível carregar as novidades" in mensagens[0][2]
    assert not (dados / "novidades" / "0.12.0.lido").exists()


def test_inicializacao_mostra_novidades_uma_vez(releases):
    base, atual, dados = releases
    _criar_release(base, "0.10.5")
    root = Path(__file__).resolve().parents[1]
    env = {
        **os.environ,
        "MAINERP_DATA": str(dados),
        "MAINERP_OK_FILE": str(atual / ".ok"),
        "QT_QPA_PLATFORM": "offscreen",
        "TESTE_RELEASE": str(atual),
    }
    env.pop("MAINERP_LAUNCHER", None)
    script = """
import os
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
import mainerp.app as app
from mainerp.ui.dialogs import sobre_atualizacoes_dialog as novidades
novidades.CODE_DIR = Path(os.environ["TESTE_RELEASE"])
app.verificar_instancia_unica = lambda nome: True
app.obter_config().APP_VERSION = "0.12.0"
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
QMessageBox.warning = lambda *args: print("AVISO:", args[2], flush=True)
original_dialog = novidades.NovidadesDialog
class Dialogo(original_dialog):
    def exec(self):
        print("NOVIDADES:", self.novidades.toPlainText(), flush=True)
        QTimer.singleShot(0, self.close)
        return super().exec()
novidades.NovidadesDialog = Dialogo
original_exec = QApplication.exec
def executar():
    QTimer.singleShot(1500, lambda: QApplication.exit(0))
    return original_exec()
QApplication.exec = staticmethod(executar)
app.main()
"""
    resultados = []
    for _ in range(2):
        resultado = subprocess.run(
            [sys.executable, "-c", script], cwd=root, env=env, capture_output=True,
            text=True, errors="replace", timeout=45, check=False,
        )
        assert resultado.returncode == 0, resultado.stdout + resultado.stderr
        resultados.append(resultado.stdout)
    assert "NOVIDADES:" in resultados[0] and "Nova tela" in resultados[0]
    assert "NOVIDADES:" not in resultados[1]
    assert (dados / "novidades" / "0.12.0.lido").is_file()


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_dialogo_novidades_exibe_notas_e_fecha_em_ambos_temas(tmp_path, tema):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "MAINERP_DATA": str(tmp_path), "QT_QPA_PLATFORM": "offscreen"}
    script = """
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from mainerp.ui.dialogs.sobre_atualizacoes_dialog import NovidadesDialog
from mainerp.ui.styles import aplicar_tema
app = QApplication([])
aplicar_tema(app, sys.argv[1])
dialog = NovidadesDialog("0.12.0", "## 0.12.0\\n\\n- Nova tela")
QTimer.singleShot(0, dialog.close)
dialog.exec()
assert "Nova tela" in dialog.novidades.toPlainText()
assert not dialog.isVisible()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", script, tema], cwd=root, env=env,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
