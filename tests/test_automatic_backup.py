import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import mainerp.data.automatic_backup as automatic_backup
from mainerp.data.automatic_backup import (
    BACKUP_PREFIX,
    BackupAutomatico,
    aplicar_retencao_backups,
    backup_automatico_vencido,
    criar_backup_automatico,
)


def test_criar_backup_automatico_produz_snapshot_sqlite_integro(tmp_path):
    banco = tmp_path / "erp.db"
    conn = sqlite3.connect(banco)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT)")
    conn.execute("INSERT INTO clientes (nome) VALUES ('Teste')")
    conn.commit()
    agora = datetime(2026, 11, 7, 9, 30)

    try:
        backup = criar_backup_automatico(banco, tmp_path / "backups", agora)
    finally:
        conn.close()

    assert backup.name == f"{BACKUP_PREFIX}20261107_093000.db"
    copia = sqlite3.connect(backup)
    try:
        assert copia.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert copia.execute("SELECT nome FROM clientes").fetchone() == ("Teste",)
    finally:
        copia.close()
    assert not list(backup.parent.glob("*.tmp"))


def test_backup_automatico_vencido_usa_idade_do_snapshot_mais_recente(tmp_path):
    pasta = tmp_path / "backups"
    pasta.mkdir()
    agora = datetime(2026, 11, 7, 12)

    assert backup_automatico_vencido(pasta, agora)

    arquivo = pasta / f"{BACKUP_PREFIX}recente.db"
    arquivo.write_bytes(b"snapshot")
    mtime = agora.timestamp() - 23 * 60 * 60
    os.utime(arquivo, (mtime, mtime))
    assert not backup_automatico_vencido(pasta, agora)

    mtime = agora.timestamp() - timedelta(days=1).total_seconds()
    os.utime(arquivo, (mtime, mtime))
    assert backup_automatico_vencido(pasta, agora)


def test_retencao_remove_apenas_backups_automaticos_com_mais_de_30_dias(tmp_path):
    pasta = tmp_path / "backups"
    pasta.mkdir()
    agora = datetime(2026, 11, 7, 12)
    antigo = pasta / f"{BACKUP_PREFIX}antigo.db"
    recente = pasta / f"{BACKUP_PREFIX}recente.db"
    migracao = pasta / "pre_migracao_v0_para_v1.db"
    for arquivo in (antigo, recente, migracao):
        arquivo.write_bytes(b"backup")

    timestamp_antigo = (agora - timedelta(days=31)).timestamp()
    os.utime(antigo, (timestamp_antigo, timestamp_antigo))

    removidos = aplicar_retencao_backups(pasta, agora)

    assert removidos == [antigo]
    assert not antigo.exists()
    assert recente.exists()
    assert migracao.exists()


def test_servico_inicia_backup_vencido_em_thread(tmp_path):
    from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer

    app = QCoreApplication.instance() or QCoreApplication([])
    banco = tmp_path / "erp.db"
    conn = sqlite3.connect(banco)
    conn.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()
    service = BackupAutomatico(banco)
    backups_criados = []
    falhas = []
    service.backup_concluido.connect(backups_criados.append)
    service.backup_falhou.connect(falhas.append)
    loop = QEventLoop()
    service.operacao_finalizada.connect(loop.quit)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    service.iniciar()
    timeout.start(5000)
    loop.exec()
    timeout.stop()
    service.parar()
    app.processEvents()

    assert not falhas
    assert len(backups_criados) == 1
    assert Path(backups_criados[0]).is_file()


def test_agendamento_falha_visivelmente_e_tenta_novamente(tmp_path, monkeypatch):
    from PyQt6.QtCore import QCoreApplication

    app = QCoreApplication.instance() or QCoreApplication([])
    service = BackupAutomatico(tmp_path / "erp.db")
    falhas = []
    service.backup_falhou.connect(falhas.append)
    verificar = automatic_backup.ultimo_backup_automatico

    def falhar(_):
        raise PermissionError("acesso negado")

    monkeypatch.setattr(automatic_backup, "ultimo_backup_automatico", falhar)
    service.iniciar()
    app.processEvents()
    assert falhas and "acesso negado" in falhas[-1]
    assert "Falha ao verificar agendamento" in service.resultado
    assert service._timer.isActive()
    assert not service.em_execucao

    monkeypatch.setattr(automatic_backup, "ultimo_backup_automatico", verificar)
    pasta = tmp_path / "backups"
    pasta.mkdir()
    (pasta / f"{BACKUP_PREFIX}recente.db").write_bytes(b"snapshot")
    service.verificar_e_executar()
    assert service.ultimo_backup is not None
    assert not service.em_execucao
    service.parar()


def test_parar_cancela_verificacao_inicial_ja_agendada(tmp_path):
    from PyQt6.QtCore import QCoreApplication

    app = QCoreApplication.instance() or QCoreApplication([])
    service = BackupAutomatico(tmp_path / "inexistente.db")
    falhas = []
    service.backup_falhou.connect(falhas.append)
    service.iniciar()
    service.parar()
    app.processEvents()
    assert not falhas
    assert not service.em_execucao
    assert service.resultado == "Ainda não verificado"


def test_falha_de_backup_e_nova_tentativa_atualizam_resultado(tmp_path):
    from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer

    app = QCoreApplication.instance() or QCoreApplication([])
    banco = tmp_path / "erp.db"
    service = BackupAutomatico(banco)
    falhas, concluidos = [], []
    service.backup_falhou.connect(falhas.append)
    service.backup_concluido.connect(concluidos.append)

    def aguardar():
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        service.operacao_finalizada.connect(loop.quit)
        timeout.start(5000)
        loop.exec()
        timeout.stop()
        service.operacao_finalizada.disconnect(loop.quit)
        assert not service.em_execucao

    service.iniciar()
    aguardar()
    assert falhas and "não encontrado" in falhas[0]
    assert service.resultado.startswith("Falha:")
    assert service.ultimo_backup is None

    with sqlite3.connect(banco) as conn:
        conn.execute("CREATE TABLE teste (id INTEGER)")
    service.verificar_e_executar()
    aguardar()
    service.parar()
    app.processEvents()
    assert len(concluidos) == 1
    assert service.resultado == "Concluído"
    assert service.ultimo_backup is not None


def test_falha_retencao_nao_oculta_backup_criado(tmp_path, monkeypatch):
    from PyQt6.QtCore import QCoreApplication, QEventLoop, QTimer

    app = QCoreApplication.instance() or QCoreApplication([])
    banco = tmp_path / "erp.db"
    with sqlite3.connect(banco) as conn:
        conn.execute("CREATE TABLE teste (id INTEGER)")
    service = BackupAutomatico(banco)
    concluidos, falhas = [], []
    service.backup_concluido.connect(concluidos.append)
    service.retencao_falhou.connect(falhas.append)

    def falhar(*args):
        raise PermissionError("retenção negada")

    monkeypatch.setattr(automatic_backup, "aplicar_retencao_backups", falhar)
    loop = QEventLoop()
    service.operacao_finalizada.connect(loop.quit)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    service.iniciar()
    timeout.start(5000)
    loop.exec()
    timeout.stop()
    service.parar()
    app.processEvents()

    assert not service.em_execucao
    assert len(concluidos) == 1 and Path(concluidos[0]).is_file()
    assert falhas == ["retenção negada"]
    assert "Concluído; falha na retenção" in service.resultado
    assert service.ultimo_backup is not None


@pytest.mark.parametrize(
    "cenario", [
        "cancelado", "aceito", "erro_recusado", "erro_aceito", "recente",
        "verificacao_falha",
    ]
)
def test_fechamento_reinicia_agendamento_somente_se_interrompido(monkeypatch, cenario):
    from types import SimpleNamespace

    from PyQt6.QtGui import QCloseEvent
    from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

    from mainerp.ui.views.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    operacoes = []
    service = SimpleNamespace(
        em_execucao=False,
        parar=lambda: operacoes.append("parar"),
        iniciar=lambda: operacoes.append("iniciar"),
    )
    janela = SimpleNamespace(
        backup_automatico=service,
        _mostrar_dialogo_backup=lambda: MainWindow._mostrar_dialogo_backup(janela),
        _perguntar_fechamento_emergencial=lambda: (
            MainWindow._perguntar_fechamento_emergencial(janela)
        ),
        windowTitle=lambda: "MainERP",
    )
    monkeypatch.setattr(app, "quit", lambda: operacoes.append("quit"))

    class Dialogo:
        def __init__(self, _parent):
            if cenario.startswith("erro"):
                raise RuntimeError("erro simulado")
            self.backup_realizado = SimpleNamespace(connect=lambda slot: None)

        def setWindowTitle(self, _titulo):
            pass

        def exec(self):
            return (
                QDialog.DialogCode.Accepted if cenario == "aceito"
                else QDialog.DialogCode.Rejected
            )

    janela._backup_concluido = lambda caminho: None
    monkeypatch.setattr("mainerp.ui.views.main_window.BackupDialog", Dialogo)
    def verificar():
        if cenario == "verificacao_falha":
            raise OSError("falha simulada")
        return cenario != "recente"

    Dialogo.should_show_dialog = staticmethod(verificar)
    monkeypatch.setattr(
        QMessageBox, "question",
        lambda *args: (
            QMessageBox.StandardButton.Yes if cenario == "erro_aceito"
            else QMessageBox.StandardButton.No
        ),
    )
    evento = QCloseEvent()
    MainWindow.closeEvent(janela, evento)
    assert not evento.isAccepted()
    assert operacoes == (
        ["parar", "quit"] if cenario in ("aceito", "erro_aceito", "recente")
        else ["parar", "iniciar"]
    )


def test_fechamento_cancelado_reativa_timer_real(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from PyQt6.QtGui import QCloseEvent
    from PyQt6.QtWidgets import QApplication

    from mainerp.ui.views.main_window import BackupDialog, MainWindow

    app = QApplication.instance() or QApplication([])
    service = BackupAutomatico(tmp_path / "erp.db")
    service.iniciar()
    janela = SimpleNamespace(
        backup_automatico=service, _mostrar_dialogo_backup=lambda: False
    )
    monkeypatch.setattr(BackupDialog, "should_show_dialog", lambda: True)
    evento = QCloseEvent()
    MainWindow.closeEvent(janela, evento)
    assert not evento.isAccepted()
    assert service._timer.isActive()
    service.parar()
    app.processEvents()
    assert not service.em_execucao


def test_fechamento_aguarda_worker_e_retoma_uma_vez():
    from types import SimpleNamespace

    from PyQt6.QtGui import QCloseEvent

    from mainerp.ui.views.main_window import MainWindow

    operacoes = []
    janela = SimpleNamespace(
        backup_automatico=SimpleNamespace(em_execucao=True),
        _aguardando_backup_automatico=False,
        status_bar=SimpleNamespace(showMessage=operacoes.append),
        close=lambda: operacoes.append("close"),
    )
    evento = QCloseEvent()
    MainWindow.closeEvent(janela, evento)
    MainWindow.closeEvent(janela, QCloseEvent())
    assert not evento.isAccepted()
    assert len(operacoes) == 1
    MainWindow._retomar_fechamento_apos_backup(janela)
    MainWindow._retomar_fechamento_apos_backup(janela)
    assert operacoes[-1] == "close"
    assert operacoes.count("close") == 1


def test_status_mostra_idade_e_ultima_falha():
    from types import SimpleNamespace

    from PyQt6.QtWidgets import QApplication, QLabel

    from mainerp.ui.views.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    label = QLabel()
    janela = SimpleNamespace(
        backup_automatico=SimpleNamespace(
            ultimo_backup=datetime.now() - timedelta(days=2, hours=3, minutes=4),
            resultado="Concluído; falha na retenção: acesso negado",
        ),
        status_widget=SimpleNamespace(label_backup=label),
    )
    MainWindow._atualizar_status_backup(janela)
    assert "2d 3h 4min" in label.text()
    assert "falha na retenção: acesso negado" in label.text()
    label.close()
    app.processEvents()
