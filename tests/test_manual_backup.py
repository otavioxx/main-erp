import json
import sqlite3
import zipfile
from types import SimpleNamespace

from mainerp.ui.dialogs.backup_dialog import BackupConfig, BackupDialog, BackupThread


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


def test_falha_ao_criar_snapshot_nao_publica_backup(tmp_path, monkeypatch):
    banco = tmp_path / "erp.db"
    banco.write_bytes(b"banco")
    worker = BackupThread(str(banco), str(tmp_path))
    concluidos, erros = [], []
    worker.backup_completed.connect(concluidos.append)
    worker.backup_error.connect(erros.append)

    def falhar(*args):
        raise OSError("disco indisponível")

    monkeypatch.setattr("mainerp.ui.dialogs.backup_dialog.criar_snapshot_sqlite", falhar)
    worker.run()

    assert not concluidos
    assert erros and "disco indisponível" in erros[0]
    assert not list(tmp_path.glob("*.zip"))


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
    status = SimpleNamespace(setText=lambda value: None, setStyleSheet=lambda value: None)
    dialogo = SimpleNamespace(
        status_label=status,
        backup_realizado=SimpleNamespace(emit=emitidos.append),
        accept=lambda: aceitos.append(True),
    )

    BackupDialog._backup_concluido(dialogo, str(arquivo))

    assert len(avisos) == 1
    assert emitidos == [str(arquivo)]
    assert aceitos == [True]
