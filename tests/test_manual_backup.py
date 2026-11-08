import json
import os
import sqlite3
import subprocess
import sys
import threading
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from mainerp.data.automatic_backup import criar_snapshot_sqlite
from mainerp.data.database import Database
from mainerp.data.restore import caminho_restauracao_pendente
from mainerp.ui.dialogs.backup_dialog import BackupConfig, BackupDialog, BackupThread
from mainerp.ui.dialogs.restore_backup_dialog import (
    RestoreBackupThread,
    VerifyBackupThread,
)


def test_backup_manual_inclui_transacoes_do_wal(tmp_path):
    banco = tmp_path / "erp.db"
    conexao = sqlite3.connect(banco)
    conexao.execute("PRAGMA journal_mode = WAL")
    conexao.execute("PRAGMA wal_autocheckpoint = 0")
    conexao.execute("CREATE TABLE clientes (nome TEXT)")
    conexao.execute("INSERT INTO clientes VALUES ('Cliente em WAL')")
    conexao.commit()
    destino = tmp_path / "destino"
    destino.mkdir()
    worker = BackupThread(str(banco), str(destino))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)
    try:
        worker.run()
        assert not erros
        assert len(concluidos) == 1
        with zipfile.ZipFile(concluidos[0]) as arquivo:
            arquivo.extract("erp.db", tmp_path / "restaurado")
        copia = sqlite3.connect(tmp_path / "restaurado" / "erp.db")
        try:
            assert copia.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert copia.execute("SELECT nome FROM clientes").fetchone() == (
                "Cliente em WAL",
            )
        finally:
            copia.close()
        assert not list(destino.glob("temp_*.zip"))
    finally:
        conexao.close()


def test_backup_manual_corrompido_nao_publica_zip(tmp_path):
    banco = tmp_path / "erp.db"
    banco.write_bytes(b"nao e sqlite")
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)

    worker.run()

    assert not concluidos
    assert erros
    assert not list(tmp_path.glob("*.zip"))


@pytest.mark.parametrize(
    "estado", ["valido", "removido", "corrompido", "alterado", "inacessivel"]
)
def test_backup_recente_so_dispensa_dialogo_se_for_validado(
    tmp_path, monkeypatch, estado
):
    from PyQt6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", str(tmp_path / "settings.json"))
    arquivo = tmp_path / "backup.zip"
    banco = tmp_path / "erp.db"
    with sqlite3.connect(banco) as conn:
        conn.execute("CREATE TABLE teste (id INTEGER)")
    with zipfile.ZipFile(arquivo, "w") as zf:
        zf.write(banco, "erp.db")
    assert BackupConfig.save_last_backup_date(datetime.now(), str(arquivo))
    if estado == "removido":
        arquivo.unlink()
    elif estado == "corrompido":
        arquivo.write_bytes(b"arquivo corrompido")
    elif estado == "alterado":
        with zipfile.ZipFile(arquivo, "w") as zf:
            zf.writestr("erp.db", b"banco alterado")
    elif estado == "inacessivel":
        def negar(*args, **kwargs):
            raise PermissionError("destino indisponível")

        monkeypatch.setattr("mainerp.ui.dialogs.backup_dialog.zipfile.ZipFile", negar)

    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args))
    assert BackupDialog.should_show_dialog() is (estado != "valido")
    if estado == "valido":
        assert not avisos
    else:
        assert len(avisos) == 1
        assert "backup" in avisos[0][2].lower()
        assert "novo" in avisos[0][2].lower()
    app.processEvents()


def test_fechamento_nao_dispensa_dialogo_ao_perder_backup_recente(tmp_path, monkeypatch):
    from PyQt6.QtGui import QCloseEvent
    from PyQt6.QtWidgets import QApplication, QMessageBox

    from mainerp.ui.views.main_window import MainWindow

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", str(tmp_path / "settings.json"))
    assert BackupConfig.save_last_backup_date(datetime.now(), str(tmp_path / "ausente.zip"))
    avisos, operacoes = [], []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args))
    monkeypatch.setattr(app, "quit", lambda: operacoes.append("quit"))
    janela = SimpleNamespace(
        backup_automatico=SimpleNamespace(
            em_execucao=False,
            parar=lambda: operacoes.append("parar"),
            iniciar=lambda: operacoes.append("iniciar"),
        ),
        _mostrar_dialogo_backup=lambda: operacoes.append("dialogo") or False,
    )
    evento = QCloseEvent()
    MainWindow.closeEvent(janela, evento)
    assert not evento.isAccepted()
    assert operacoes == ["parar", "dialogo", "iniciar"]
    assert len(avisos) == 1
    app.processEvents()


def test_backup_legado_sem_hash_ainda_verifica_conteudo_zip(tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", str(tmp_path / "settings.json"))
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zf:
        zf.writestr("erp.db", b"banco legado")
    Path(BackupConfig.CONFIG_FILE).write_text(
        json.dumps({"last_backup_date": datetime.now().isoformat(),
                    "last_backup_file": str(arquivo)}),
        encoding="utf-8",
    )
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args))
    assert not BackupDialog.should_show_dialog()
    arquivo.write_bytes(b"corrompido")
    assert BackupDialog.should_show_dialog()
    assert len(avisos) == 1
    app.processEvents()


def test_backup_vencido_solicita_dialogo_sem_validar_arquivo(tmp_path, monkeypatch):
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", str(tmp_path / "settings.json"))
    assert BackupConfig.save_last_backup_date(datetime.now() - timedelta(days=2))

    def nao_validar():
        raise AssertionError("backup vencido não precisa ser validado")

    monkeypatch.setattr(BackupConfig, "validate_last_backup", nao_validar)
    assert BackupDialog.should_show_dialog()


def test_falha_ao_criar_snapshot_nao_publica_backup(tmp_path, monkeypatch):
    banco = tmp_path / "erp.db"
    banco.write_bytes(b"banco")
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)

    def falhar(*args):
        raise OSError("disco indisponível")

    monkeypatch.setattr(
        "mainerp.ui.dialogs.backup_dialog.criar_snapshot_sqlite", falhar
    )
    worker.run()

    assert not concluidos
    assert erros and "disco indisponível" in erros[0]
    assert not list(tmp_path.glob("*.zip"))


def test_backups_mesmo_segundo_nao_sobrescrevem_anterior(tmp_path, monkeypatch):
    class Relogio(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 1, 12, 0, 0)

    monkeypatch.setattr("mainerp.ui.dialogs.backup_dialog.datetime", Relogio)
    banco = tmp_path / "erp.db"
    conexao = sqlite3.connect(banco)
    conexao.execute("CREATE TABLE dados (valor INTEGER)")
    conexao.execute("INSERT INTO dados VALUES (1)")
    conexao.commit()
    saidas = []
    try:
        for valor in (1, 2):
            conexao.execute("UPDATE dados SET valor=?", (valor,))
            conexao.commit()
            worker = BackupThread(str(banco), str(tmp_path))
            erros = []
            worker.backup_completed.connect(saidas.append)
            worker.backup_error.connect(erros.append)
            worker.run()
            assert not erros
        assert len(set(saidas)) == 2
        for indice, (arquivo, esperado) in enumerate(zip(saidas, (1, 2), strict=True)):
            with zipfile.ZipFile(arquivo) as zf:
                pasta = tmp_path / f"copia_{indice}"
                zf.extract("erp.db", pasta)
            copia = sqlite3.connect(pasta / "erp.db")
            try:
                assert copia.execute("SELECT valor FROM dados").fetchone() == (
                    esperado,
                )
            finally:
                copia.close()
    finally:
        conexao.close()


def test_snapshot_com_transacao_concorrente_em_wal(tmp_path, monkeypatch):
    banco = tmp_path / "erp.db"
    conn = sqlite3.connect(banco)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("CREATE TABLE dados (id INTEGER PRIMARY KEY, valor INTEGER)")
    conn.executemany("INSERT INTO dados VALUES (?, 0)", [(1,), (2,)])
    conn.commit()
    conn.execute("BEGIN IMMEDIATE")
    conn.execute("UPDATE dados SET valor=1 WHERE id=1")

    def snapshot_enquanto_escreve(origem, destino):
        criar_snapshot_sqlite(origem, destino)
        conn.execute("UPDATE dados SET valor=1 WHERE id=2")
        conn.commit()

    monkeypatch.setattr(
        "mainerp.ui.dialogs.backup_dialog.criar_snapshot_sqlite",
        snapshot_enquanto_escreve,
    )
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)
    try:
        worker.run()
        assert not erros
        assert conn.execute("SELECT valor FROM dados ORDER BY id").fetchall() == [
            (1,),
            (1,),
        ]
        with zipfile.ZipFile(concluidos[0]) as zf:
            zf.extract("erp.db", tmp_path / "copia")
        copia = sqlite3.connect(tmp_path / "copia" / "erp.db")
        try:
            assert copia.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert copia.execute("SELECT valor FROM dados ORDER BY id").fetchall() == [
                (0,),
                (0,),
            ]
        finally:
            copia.close()
    finally:
        conn.close()


def test_backups_simultaneos_usam_arquivos_independentes(tmp_path, monkeypatch):
    banco = tmp_path / "erp.db"
    conn = sqlite3.connect(banco)
    conn.execute("CREATE TABLE dados (valor INTEGER)")
    conn.execute("INSERT INTO dados VALUES (42)")
    conn.commit()
    conn.close()
    barreira = threading.Barrier(2)

    def snapshot_simultaneo(origem, destino):
        barreira.wait(timeout=10)
        criar_snapshot_sqlite(origem, destino)

    monkeypatch.setattr(
        "mainerp.ui.dialogs.backup_dialog.criar_snapshot_sqlite", snapshot_simultaneo
    )
    workers = [BackupThread(str(banco), str(tmp_path)) for _ in range(2)]
    concluidos, erros = [], []
    for worker in workers:
        worker.backup_completed.connect(concluidos.append)
        worker.backup_error.connect(erros.append)
    threads = [threading.Thread(target=worker.run) for worker in workers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    assert all(not thread.is_alive() for thread in threads)
    # Signals emitted on worker threads are queued for the Qt main thread.
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.processEvents()
    assert not erros
    assert len(set(concluidos)) == 2
    for caminho in concluidos:
        with zipfile.ZipFile(caminho) as arquivo:
            assert arquivo.testzip() is None
            assert "erp.db" in arquivo.namelist()
    assert not list(tmp_path.glob("temp_*.zip"))


@pytest.mark.parametrize("etapa", ["compactacao", "publicacao"])
def test_falha_disco_na_publicacao_preserva_backup_anterior(
    tmp_path, monkeypatch, etapa
):
    banco = tmp_path / "erp.db"
    conn = sqlite3.connect(banco)
    conn.execute("CREATE TABLE dados (valor INTEGER)")
    conn.commit()
    conn.close()
    anterior = tmp_path / "backup_erp_anterior.zip"
    anterior.write_bytes(b"backup anterior preservado")
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)

    def falhar(*args, **kwargs):
        raise OSError("disco cheio simulado")

    if etapa == "compactacao":
        monkeypatch.setattr("zipfile.ZipFile.write", falhar)
    else:
        monkeypatch.setattr("mainerp.ui.dialogs.backup_dialog.os.replace", falhar)
    worker.run()
    assert not concluidos
    assert erros and "disco cheio simulado" in erros[0]
    assert anterior.read_bytes() == b"backup anterior preservado"
    assert list(tmp_path.glob("*.zip")) == [anterior]


def test_backup_manual_restaurado_na_inicializacao_da_aplicacao(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    banco = dados / "erp.db"
    database = Database(str(banco))
    conn = database.get_connection()
    conn.execute("CREATE TABLE teste_ciclo (id INTEGER PRIMARY KEY, valor TEXT)")
    conn.executemany("INSERT INTO teste_ciclo VALUES (?, ?)", [(1, "um"), (2, "dois")])
    conn.commit()
    database.close_connection()
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)
    worker.run()
    assert len(concluidos) == 1 and not erros

    verificacao = VerifyBackupThread(concluidos[0])
    assert verificacao._get_zip_info()["is_valid"]
    conn = sqlite3.connect(banco)
    conn.execute("UPDATE teste_ciclo SET valor='alterado' WHERE id=1")
    conn.commit()
    conn.close()
    restauracao = RestoreBackupThread(concluidos[0], str(banco))
    restaurados, falhas = [], []
    restauracao.restore_complete.connect(restaurados.append)
    restauracao.restore_error.connect(falhas.append)
    restauracao.run()
    assert restaurados and not falhas
    assert caminho_restauracao_pendente(banco).exists()
    sinal = tmp_path / "aberto"
    env = dict(
        os.environ,
        MAINERP_DATA=str(dados),
        MAINERP_OK_FILE=str(sinal),
        QT_QPA_PLATFORM="offscreen",
    )
    env.pop("MAINERP_LAUNCHER", None)
    codigo = """
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
import mainerp.app as app
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
original = QApplication.exec
def executar():
    QTimer.singleShot(1000, lambda: QApplication.exit(0))
    return original()
QApplication.exec = staticmethod(executar)
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=45,
        check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert sinal.is_file(), resultado.stdout + resultado.stderr
    assert not caminho_restauracao_pendente(banco).exists()
    (anterior,) = (dados / "backups").glob("pre_restore_*.db")
    for arquivo, esperado in ((banco, "um"), (anterior, "alterado")):
        conn = sqlite3.connect(arquivo)
        try:
            assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert conn.execute(
                "SELECT valor FROM teste_ciclo ORDER BY id"
            ).fetchall() == [(esperado,), ("dois",)]
        finally:
            conn.close()


def test_backup_externo_restaurado_em_dados_isolados(tmp_path):
    origem = tmp_path / "origem" / "erp.db"
    origem.parent.mkdir()
    banco = Database(str(origem))
    banco.get_connection().execute(
        "INSERT INTO clientes (id, nome) VALUES (1, 'Cliente de teste')"
    )
    banco.get_connection().commit()
    banco.close_connection()
    antes_origem = origem.read_bytes()

    externo = tmp_path / "copia_externa"
    externo.mkdir()
    worker = BackupThread(str(origem), str(externo))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)
    worker.run()
    assert len(concluidos) == 1 and not erros
    arquivo = Path(concluidos[0])
    antes_backup = arquivo.read_bytes()
    assert VerifyBackupThread(str(arquivo))._get_zip_info()["is_valid"]

    dados = tmp_path / "instalacao_isolada" / "dados"
    dados.mkdir(parents=True)
    destino = dados / "erp.db"
    banco = Database(str(destino))
    banco.close_connection()
    restauracao = RestoreBackupThread(str(arquivo), str(destino))
    concluidos, erros = [], []
    restauracao.restore_complete.connect(concluidos.append)
    restauracao.restore_error.connect(erros.append)
    restauracao.run()
    assert concluidos and not erros

    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal),
               QT_QPA_PLATFORM="offscreen")
    env.pop("MAINERP_LAUNCHER", None)
    codigo = """
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
import mainerp.app as app
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
original = QApplication.exec
def executar():
    QTimer.singleShot(1000, lambda: QApplication.exit(0))
    return original()
QApplication.exec = staticmethod(executar)
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert sinal.is_file(), resultado.stdout + resultado.stderr
    assert not caminho_restauracao_pendente(destino).exists()
    with sqlite3.connect(destino) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert conn.execute("SELECT nome FROM clientes WHERE id=1").fetchone() == (
            "Cliente de teste",
        )
    assert origem.read_bytes() == antes_origem
    assert arquivo.read_bytes() == antes_backup


def test_salvar_caminho_preserva_metadados(tmp_path, monkeypatch):
    arquivo = tmp_path / "backup_settings.json"
    dados = {
        "last_backup_date": "2026-01-01T10:00:00",
        "last_backup_file": "anterior.zip",
        "last_backup_hash": "abc",
        "last_backup_path": "anterior",
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", arquivo)

    assert BackupConfig.save_last_path("novo")
    dados["last_backup_path"] = "novo"
    assert json.loads(arquivo.read_text(encoding="utf-8")) == dados


def test_salvar_caminho_nao_sobrescreve_configuracao_invalida(tmp_path, monkeypatch):
    arquivo = tmp_path / "backup_settings.json"
    arquivo.write_text("{inválido", encoding="utf-8")
    monkeypatch.setattr(BackupConfig, "CONFIG_FILE", arquivo)

    assert not BackupConfig.save_last_path("novo")
    assert arquivo.read_text(encoding="utf-8") == "{inválido"


def test_backup_informa_falha_ao_salvar_metadados(tmp_path, monkeypatch):
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zipf:
        zipf.writestr("erp.db", "dados")
    avisos, emitidos, aceitos = [], [], []

    class Caixa:
        Icon = SimpleNamespace(Information=1)
        StandardButton = SimpleNamespace(Ok=1)

        def __init__(self, parent):
            pass

        @staticmethod
        def warning(*args):
            avisos.append(args)

        def setIcon(self, value):
            pass

        def setWindowTitle(self, value):
            pass

        def setText(self, value):
            pass

        def addButton(self, value):
            pass

        def exec(self):
            pass

    monkeypatch.setattr("mainerp.ui.dialogs.backup_dialog.QMessageBox", Caixa)
    monkeypatch.setattr(BackupConfig, "save_last_backup_date", lambda **kwargs: False)
    status = SimpleNamespace(
        setText=lambda value: None, setStyleSheet=lambda value: None
    )
    dialogo = SimpleNamespace(
        status_label=status,
        backup_realizado=SimpleNamespace(emit=emitidos.append),
        accept=lambda: aceitos.append(True),
    )

    BackupDialog._backup_concluido(cast(BackupDialog, dialogo), str(arquivo))

    assert len(avisos) == 1
    assert emitidos == [str(arquivo)]
    assert aceitos == [True]
