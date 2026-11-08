import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton

from mainerp.core.config import Config
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.theme_tokens import CLARO, ESCURO
from mainerp.ui.views import config_view

ROOT = Path(__file__).resolve().parents[1]


def test_preferencia_nova_antiga_invalida_e_persistencia(tmp_path, caplog):
    caminho = tmp_path / "config.json"
    nova = Config(str(caminho))
    assert nova.obter_tema() == "light"
    assert nova.salvar_tema("dark")
    assert Config(str(caminho)).obter_tema() == "dark"
    caminho.write_text(json.dumps({"company": {"name": "Teste"}}), encoding="utf-8")
    antiga = Config(str(caminho))
    assert antiga.obter_tema() == "dark"
    assert antiga.salvar_tema("light")
    assert Config(str(caminho)).obter_tema() == "light"
    assert json.loads(caminho.read_text(encoding="utf-8"))["company"]["name"] == "Teste"
    caminho.write_text('{"appearance": {"theme": "invalido"}}', encoding="utf-8")
    invalida = Config(str(caminho))
    assert invalida.obter_tema() == "dark"
    assert "Tema inválido" in caplog.text
    assert "invalido" in caminho.read_text(encoding="utf-8")


def test_falha_ao_salvar_preserva_configuracao(tmp_path, monkeypatch):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"appearance": {"theme": "dark"}}', encoding="utf-8")
    config = Config(str(caminho))
    original = caminho.read_bytes()

    def falhar(*args):
        raise OSError("falha simulada")

    monkeypatch.setattr("mainerp.core.config.os.replace", falhar)
    assert not config.salvar_tema("light")
    assert config.obter_tema() == "dark"
    assert caminho.read_bytes() == original
    assert list(tmp_path.iterdir()) == [caminho]


def test_configuracao_corrompida_nao_e_sobrescrita(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("{", encoding="utf-8")
    config = Config(str(caminho))
    assert not config.salvar_tema("light")
    assert caminho.read_text(encoding="utf-8") == "{"


@pytest.mark.parametrize("tema,cores", [("light", CLARO), ("dark", ESCURO)])
def test_tema_aplica_paleta_raio_e_estado_desabilitado(tema, cores):
    app = QApplication.instance() or QApplication([])
    aplicar_tema(app, tema)
    assert app.palette().color(QPalette.ColorRole.Window).name().upper() == cores.background_window
    assert re.findall(r"border(?:-(?:top|bottom)-(?:left|right))?-radius:\s*(\d+)px", app.styleSheet())
    assert all(
        valor == "0"
        for valor in re.findall(
            r"border(?:-(?:top|bottom)-(?:left|right))?-radius:\s*(\d+)px", app.styleSheet()
        )
    )
    button = QPushButton("Editar")
    button.setProperty("class", "secondary")
    button.resize(120, 40)
    button.show()
    app.processEvents()
    habilitado = button.grab().toImage()
    button.setEnabled(False)
    app.processEvents()
    desabilitado = button.grab().toImage()
    assert habilitado != desabilitado
    button.close()


def test_seletor_avisa_e_persiste_ou_mostra_erro(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    config = Config(str(tmp_path / "config.json"))
    monkeypatch.setattr(config_view, "obter_config", lambda: config)
    monkeypatch.setattr(config_view.Empresa, "buscar", lambda: config_view.Empresa())
    mensagens = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: mensagens.append(args))
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: mensagens.append(args))
    view = config_view.ConfigView()
    view.tema_combo.setCurrentIndex(view.tema_combo.findData("dark"))
    view.salvar_tema()
    assert Config(config.config_file).obter_tema() == "dark"
    assert "próxima abertura" in mensagens[-1][2]
    monkeypatch.setattr(config, "salvar_tema", lambda tema: False)
    view.tema_combo.setCurrentIndex(view.tema_combo.findData("light"))
    view.salvar_tema()
    assert "Não foi possível salvar" in mensagens[-1][2]
    assert config.obter_tema() == "dark"
    view.deleteLater()
    app.processEvents()


@pytest.mark.parametrize("tema", ["light", "dark"])
@pytest.mark.parametrize("escala", ["1", "1.25", "1.5"])
def test_controles_retos_e_interacoes_com_fusion(tmp_path, tema, escala):
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_SCALE_FACTOR": escala,
        "PYTHONPATH": str(ROOT),
    }
    script = r"""
import sys
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QLineEdit, QMenu, QPushButton,
    QScrollBar, QStyle, QStyleOptionSlider, QTabWidget, QTableWidget,
    QVBoxLayout, QWidget,
)
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.theme_tokens import CLARO, ESCURO

class App(QApplication):
    estilo_selecionado = None
    def setStyle(self, estilo):
        resultado = super().setStyle(estilo)
        self.estilo_selecionado = resultado.objectName() if resultado else None
        return resultado

app = App([])
aplicar_tema(app, sys.argv[1])
assert app.estilo_selecionado.lower() == "fusion"
cores = CLARO if sys.argv[1] == "light" else ESCURO
janela = QDialog()
layout = QVBoxLayout(janela)
botao = QPushButton("Salvar")
campo = QLineEdit()
combo = QComboBox()
combo.addItems(["Primeiro", "Segundo"])
abas = QTabWidget()
abas.addTab(QWidget(), "Uma")
abas.addTab(QWidget(), "Duas")
tabela = QTableWidget(20, 2)
barra = QScrollBar(Qt.Orientation.Horizontal)
barra.setRange(0, 100)
for widget in (botao, campo, combo, abas, tabela, barra):
    layout.addWidget(widget)
janela.resize(500, 600)
janela.show()
app.processEvents()

for widget, cor in ((botao, cores.border_input), (campo, cores.border_input),
                    (combo, cores.border_input), (tabela, cores.border)):
    imagem = widget.grab().toImage()
    assert imagem.pixelColor(0, 0) == QColor(cor), (type(widget).__name__, imagem.pixelColor(0, 0).name())
    direito = round((widget.width() - 1) * imagem.devicePixelRatio())
    assert imagem.pixelColor(direito, 0) == QColor(cor), type(widget).__name__

campo.setFocus()
QTest.keyClicks(campo, "teste")
assert campo.text() == "teste"
combo.setFocus()
QTest.keyClick(combo, Qt.Key.Key_Down)
assert combo.currentText() == "Segundo"
combo.showPopup()
app.processEvents()
assert combo.view().isVisible()
combo.hidePopup()
abas.setCurrentIndex(1)
assert abas.currentIndex() == 1
QTest.mouseClick(barra, Qt.MouseButton.LeftButton, pos=QPoint(barra.width() - 10, 4))
assert barra.value() > 0
opcao = QStyleOptionSlider()
barra.initStyleOption(opcao)
ret = barra.style().subControlRect(
    QStyle.ComplexControl.CC_ScrollBar, opcao,
    QStyle.SubControl.SC_ScrollBarSlider, barra,
)
imagem = barra.grab().toImage()
dpr = imagem.devicePixelRatio()
for x, y in ((ret.left(), ret.top()), (ret.right(), ret.top())):
    assert imagem.pixelColor(round(x*dpr), round(y*dpr)) == QColor(cores.border)
menu = QMenu(janela)
acionadas = []
acao = menu.addAction("Editar")
acao.triggered.connect(lambda: acionadas.append(True))
menu.popup(janela.mapToGlobal(janela.rect().center()))
app.processEvents()
assert menu.isVisible()
imagem_menu = menu.grab().toImage()
assert imagem_menu.pixelColor(0, 0) == QColor(cores.border_input)
acao.trigger()
assert acionadas == [True]
menu.close()
janela.close()
assert not janela.isVisible()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, tema],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("tema", ["light", "dark"])
def test_telas_e_dialogos_abrem_em_tema_isolado(tmp_path, tema):
    env = {
        **os.environ,
        "MAINERP_DATA": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "PYTHONPATH": str(ROOT),
    }
    script = r"""
import sys
from PyQt6.QtWidgets import QApplication
from mainerp.ui.styles import aplicar_tema
from mainerp.ui.views.cliente_view import ClienteDialog, ClienteView
from mainerp.ui.views.config_view import ConfigView
from mainerp.ui.views.condicional_view import CondicionalView
from mainerp.ui.views.fornecedor_view import FornecedorView
from mainerp.ui.views.pedido_view import PedidoView
from mainerp.ui.views.produto_view import BuscaEspecificaDialog, ProdutoView
from mainerp.ui.views.recebimento_view import RecebimentoView
from mainerp.ui.views.venda_view import VendaView
from mainerp.ui.views.main_window import MainWindow
from mainerp.data.automatic_backup import BackupAutomatico
from mainerp.ui.dialogs.backup_dialog import BackupDialog
from mainerp.ui.dialogs.cliente_selection_dialog import ClienteSelectionDialog
from mainerp.ui.dialogs.condicional_dialog import CondicionalDialog
from mainerp.ui.dialogs.config_selection_dialog import ConfigSelectionDialog
from mainerp.ui.dialogs.fornecedor_dialog import FornecedorDialog
from mainerp.ui.dialogs.fornecedor_selection_dialog import FornecedorSelectionDialog
from mainerp.ui.dialogs.observacao_dialog import ObservacaoDialog
from mainerp.ui.dialogs.pagamento_dialog import PagamentoDialog
from mainerp.ui.dialogs.pedido_dialog import PedidoDialog
from mainerp.ui.dialogs.produto_dialog import ProdutoDialog
from mainerp.ui.dialogs.produto_selection_dialog import ProdutoSelectionDialog
from mainerp.ui.dialogs.recebimento_dialog import RecebimentoDialog
from mainerp.ui.dialogs.relatorio_condicional_dialog import RelatorioCondicionalDialog
from mainerp.ui.dialogs.relatorio_produto_dialog import RelatorioProdutoDialog
from mainerp.ui.dialogs.relatorio_venda_dialog import RelatorioVendaDialog
from mainerp.ui.dialogs.restore_backup_dialog import RestoreBackupDialog
from mainerp.ui.dialogs.sobre_atualizacoes_dialog import SobreAtualizacoesDialog
from mainerp.ui.dialogs.venda_dialog import ProdutoVendaDialog
app = QApplication([])
aplicar_tema(app, sys.argv[1])
BackupAutomatico.iniciar = lambda self: None
constructors = [
    ClienteView, ConfigView, CondicionalView, FornecedorView, PedidoView,
    ProdutoView, RecebimentoView, VendaView, ClienteDialog, BackupDialog,
    ClienteSelectionDialog, CondicionalDialog, ConfigSelectionDialog,
    FornecedorDialog, FornecedorSelectionDialog, ObservacaoDialog,
    lambda: PagamentoDialog(100, 1), PedidoDialog, ProdutoDialog,
    ProdutoSelectionDialog,
    lambda: RecebimentoDialog((1, 1, 1, 1, 100, '2026-01-01')),
    RelatorioCondicionalDialog, RelatorioProdutoDialog, RelatorioVendaDialog,
    RestoreBackupDialog, SobreAtualizacoesDialog, ProdutoVendaDialog,
    lambda: BuscaEspecificaDialog('Busca', 'Digite'), MainWindow,
]
for create in constructors:
    widget = create()
    widget.show()
    app.processEvents()
    print(type(widget).__name__, flush=True)
    widget.hide()
    widget.deleteLater()
    app.processEvents()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, tema],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ClienteView" in result.stdout
    assert "RestoreBackupDialog" in result.stdout
    assert "ProdutoVendaDialog" in result.stdout
    assert "MainWindow" in result.stdout
