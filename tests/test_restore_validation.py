import sqlite3
import zipfile
from types import SimpleNamespace

import pytest
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QApplication, QMessageBox

from mainerp.data.database import Database
from mainerp.data.db_utils import DatabaseManager
from mainerp.data.restore import preparar_restauracao
from mainerp.ui.dialogs.restore_backup_dialog import (
    RestoreBackupDialog,
    VerifyBackupThread,
)


def test_rejeita_banco_incompleto_antes_de_restaurar(tmp_path):
    parcial = tmp_path / "parcial.db"
    conn = sqlite3.connect(parcial)
    conn.execute("CREATE TABLE clientes (id INTEGER)")
    conn.close()
    atual = tmp_path / "atual.db"
    database = Database(str(atual))
    database.close_connection()
    antes = atual.read_bytes()

    assert not DatabaseManager._verify_database(parcial)
    assert not VerifyBackupThread(str(parcial))._get_db_info()["is_valid"]
    with pytest.raises(ValueError, match="inválido"):
        preparar_restauracao(parcial, atual)
    assert atual.read_bytes() == antes


def test_rejeita_quatro_tabelas_essenciais_sem_esquema_completo(tmp_path):
    parcial = tmp_path / "parcial.db"
    conn = sqlite3.connect(parcial)
    for tabela in ("clientes", "produtos", "vendas", "duplicatas"):
        conn.execute(f"CREATE TABLE {tabela} (id INTEGER)")
    conn.commit()
    conn.close()
    atual = tmp_path / "atual.db"
    banco = Database(str(atual))
    banco.close_connection()
    antes = atual.read_bytes()

    assert not DatabaseManager._verify_database(parcial)
    with pytest.raises(ValueError, match="inválido"):
        preparar_restauracao(parcial, atual)
    assert atual.read_bytes() == antes


def test_rejeita_versao_de_esquema_futura(tmp_path):
    arquivo = tmp_path / "futuro.db"
    banco = Database(str(arquivo))
    banco.get_connection().execute("PRAGMA user_version=9999")
    banco.close_connection()
    assert not DatabaseManager._verify_database(arquivo)


def test_rejeita_zip_com_banco_incompleto(tmp_path):
    parcial = tmp_path / "parcial.db"
    conn = sqlite3.connect(parcial)
    conn.execute("CREATE TABLE clientes (id INTEGER)")
    conn.close()
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zipf:
        zipf.write(parcial, "erp.db")

    assert not VerifyBackupThread(str(arquivo))._get_zip_info()["is_valid"]


def test_rejeita_zip_com_multiplos_bancos(tmp_path):
    banco = tmp_path / "erp.db"
    database = Database(str(banco))
    database.close_connection()
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zipf:
        zipf.write(banco, "primeiro.db")
        zipf.write(banco, "segundo.DB")

    resultado = VerifyBackupThread(str(arquivo))._get_zip_info()
    assert not resultado["is_valid"]
    assert "exatamente um" in resultado["error"]


def test_aceita_banco_criado_pelo_sistema_e_rejeita_corrompido(tmp_path):
    arquivo = tmp_path / "erp.db"
    database = Database(str(arquivo))
    database.close_connection()
    assert DatabaseManager._verify_database(arquivo)
    assert VerifyBackupThread(str(arquivo))._get_db_info()["is_valid"]

    arquivo.write_bytes(b"arquivo corrompido")
    assert not DatabaseManager._verify_database(arquivo)
    assert not VerifyBackupThread(str(arquivo))._get_db_info()["is_valid"]


@pytest.mark.parametrize("atividade", ["verify_thread", "restore_thread"])
def test_nao_interrompe_thread_ao_fechar(atividade, monkeypatch):
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args))
    dialogo = SimpleNamespace(verify_thread=None, restore_thread=None)
    dialogo._pode_fechar = lambda: RestoreBackupDialog._pode_fechar(dialogo)
    setattr(dialogo, atividade, SimpleNamespace(isRunning=lambda: True))
    evento = QCloseEvent()
    RestoreBackupDialog.closeEvent(dialogo, evento)
    assert not evento.isAccepted()
    assert len(avisos) == 1


@pytest.mark.parametrize("atividade", ["verify_thread", "restore_thread"])
def test_nao_interrompe_thread_ao_cancelar(atividade, monkeypatch):
    app = QApplication.instance() or QApplication([])
    avisos = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: avisos.append(args))
    monkeypatch.setattr(RestoreBackupDialog, "_carregar_backups_locais", lambda self: None)
    dialogo = RestoreBackupDialog()
    setattr(dialogo, atividade, SimpleNamespace(isRunning=lambda: True))
    dialogo.show()

    dialogo.reject()

    assert dialogo.isVisible()
    assert len(avisos) == 1
    setattr(dialogo, atividade, None)
    dialogo.close()
    app.processEvents()


def test_launcher_antigo_nao_prepara_restauracao(monkeypatch):
    avisos = []
    monkeypatch.setenv("MAINERP_LAUNCHER", "1")
    monkeypatch.delenv("MAINERP_RESTORE_PROTOCOL", raising=False)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: avisos.append(args))
    dialogo = SimpleNamespace(backup_info={"is_valid": True})

    RestoreBackupDialog._iniciar_restauracao(dialogo)

    assert len(avisos) == 1
    assert "launcher" in avisos[0][2]
