import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from utils.automatic_backup import (
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
