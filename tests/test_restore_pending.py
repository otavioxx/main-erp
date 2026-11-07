import os
import sqlite3
import subprocess
import sys
import zipfile

import pytest

from mainerp.data.database import Database
from mainerp.data.restore import (
    aplicar_restauracao_pendente,
    caminho_restauracao_pendente,
    preparar_restauracao,
)


def criar_banco(caminho, valor):
    database = Database(str(caminho))
    conn = database.get_connection()
    conn.execute("CREATE TABLE teste_restauracao (valor TEXT)")
    conn.execute("INSERT INTO teste_restauracao VALUES (?)", (valor,))
    conn.commit()
    database.close_connection()


def ler_valor(caminho):
    conn = sqlite3.connect(caminho)
    try:
        return conn.execute("SELECT valor FROM teste_restauracao").fetchone()[0]
    finally:
        conn.close()


@pytest.mark.parametrize("zipado", [False, True])
def test_restauracao_pendente_preserva_wal_e_backup_anterior(tmp_path, zipado):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("UPDATE teste_restauracao SET valor='atual em wal'")
    conn.commit()
    try:
        backup = origem
        if zipado:
            backup = tmp_path / "backup.zip"
            with zipfile.ZipFile(backup, "w") as zf:
                zf.write(origem, "erp.db")
        pendente = preparar_restauracao(backup, atual)
        assert ler_valor(atual) == "atual em wal"
        assert ler_valor(pendente) == "anterior"
    finally:
        conn.close()

    anterior = aplicar_restauracao_pendente(atual)
    assert anterior is not None
    assert ler_valor(anterior) == "atual em wal"
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()
    assert aplicar_restauracao_pendente(atual) is None


def test_backup_invalido_e_multiplos_bancos_nao_criam_pendencia(tmp_path):
    atual = tmp_path / "atual.db"
    criar_banco(atual, "atual")
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zf:
        zf.write(atual, "primeiro.db")
        zf.write(atual, "segundo.db")
    with pytest.raises(ValueError, match="exatamente um"):
        preparar_restauracao(arquivo, atual)
    assert not caminho_restauracao_pendente(atual).exists()
    assert ler_valor(atual) == "atual"


def test_snapshot_anterior_falha_sem_aplicar_restauracao(tmp_path, monkeypatch):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)

    def falhar(*args):
        raise OSError("disco indisponível")

    monkeypatch.setattr("mainerp.data.restore.criar_snapshot_sqlite", falhar)
    with pytest.raises(OSError, match="disco indisponível"):
        aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "atual"
    assert pendente.exists()
    assert not list((tmp_path / "backups").glob("*.db"))


def test_pendencia_existente_nao_e_substituida(tmp_path):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    with pytest.raises(FileExistsError):
        preparar_restauracao(origem, atual)
    assert ler_valor(pendente) == "anterior"


def test_falha_ao_abrir_pendente_preserva_snapshot_e_banco(tmp_path, monkeypatch):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    conectar = sqlite3.connect
    leituras_pendentes = 0

    def falhar_ao_abrir(caminho, *args, **kwargs):
        nonlocal leituras_pendentes
        if isinstance(caminho, str) and caminho.startswith(pendente.as_uri()):
            leituras_pendentes += 1
            if leituras_pendentes == 2:
                raise sqlite3.OperationalError("falha simulada")
        return conectar(caminho, *args, **kwargs)

    monkeypatch.setattr("mainerp.data.restore.sqlite3.connect", falhar_ao_abrir)
    with pytest.raises(sqlite3.OperationalError, match="falha simulada"):
        aplicar_restauracao_pendente(atual)
    backups = list((tmp_path / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    assert ler_valor(atual) == "atual"
    assert pendente.exists()


def test_inicializacao_aplica_restauracao_antes_da_interface(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    preparar_restauracao(origem, atual)
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal))
    env["QT_QPA_PLATFORM"] = "offscreen"
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
    assert ler_valor(atual) == "anterior"
    backups = list((dados / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    assert not caminho_restauracao_pendente(atual).exists()


def test_inicializacao_bloqueia_interface_se_pendencia_esta_corrompida(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    criar_banco(atual, "atual")
    pendente = caminho_restauracao_pendente(atual)
    pendente.write_bytes(b"corrompido")
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal))
    env["QT_QPA_PLATFORM"] = "offscreen"
    codigo = """
from PyQt6.QtWidgets import QMessageBox
import mainerp.app as app
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 4, resultado.stdout + resultado.stderr
    assert "restauração pendente" in resultado.stdout
    assert not sinal.exists()
    assert pendente.exists()
    assert ler_valor(atual) == "atual"


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_interrupcao_durante_copia_preserva_banco_e_permite_repetir(
    tmp_path, journal_mode
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(origem)
    conn.execute("CREATE TABLE dados_grandes (conteudo BLOB)")
    conn.executemany(
        "INSERT INTO dados_grandes VALUES (zeroblob(8192))", [()] * 120
    )
    conn.commit()
    conn.close()
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    codigo = """
import os, sys
import mainerp.data.restore as r
original = r._copiar_banco
def interromper(origem, destino):
    def progresso(status, remaining, total):
        if remaining > 0:
            os._exit(73)
    original(origem, destino, progress=progresso)
r._copiar_banco = interromper
r.aplicar_restauracao_pendente(sys.argv[1])
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, str(atual)], capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 73, resultado.stdout + resultado.stderr
    assert pendente.exists()
    assert ler_valor(atual) == "atual"
    backups = list((tmp_path / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()
