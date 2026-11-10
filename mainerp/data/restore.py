"""Preparação e aplicação de restaurações antes de abrir o banco na interface."""

import logging
import os
import shutil
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

from mainerp.data.automatic_backup import criar_snapshot_conexao, criar_snapshot_sqlite
from mainerp.data.db_utils import DatabaseManager

logger = logging.getLogger(__name__)


def _copiar_banco(origem: sqlite3.Connection, destino: sqlite3.Connection, progress=None):
    origem.backup(destino, pages=32, progress=progress)


def caminho_restauracao_pendente(target_db: str | Path) -> Path:
    target = Path(target_db).resolve()
    return target.with_name(target.name + ".restauracao-pendente.db")


def preparar_restauracao(backup_file: str | Path, target_db: str | Path) -> Path:
    """Valida e guarda uma cópia independente; não modifica o banco em uso."""
    origem = Path(backup_file).resolve()
    destino = caminho_restauracao_pendente(target_db)
    if not origem.is_file():
        raise FileNotFoundError(f"Backup não encontrado: {origem}")
    if origem == Path(target_db).resolve():
        raise ValueError("O banco atual não pode ser usado como backup de restauração")
    if destino.exists():
        raise FileExistsError(f"Já existe uma restauração pendente: {destino}")

    with tempfile.TemporaryDirectory(dir=destino.parent) as temp_dir:
        temporario = Path(temp_dir) / "restauracao.db"
        if origem.suffix.lower() == ".zip":
            with zipfile.ZipFile(origem) as arquivo:
                bancos = [item for item in arquivo.infolist()
                          if not item.is_dir() and item.filename.lower().endswith(".db")]
                if len(bancos) != 1:
                    raise ValueError("O backup ZIP deve conter exatamente um banco .db")
                with arquivo.open(bancos[0]) as entrada, temporario.open("wb") as saida:
                    shutil.copyfileobj(entrada, saida)
        else:
            criar_snapshot_sqlite(origem, temporario)
        if not DatabaseManager._verify_database(temporario):
            raise ValueError("Arquivo de backup corrompido ou inválido")
        with temporario.open("r+b") as arquivo:
            os.fsync(arquivo.fileno())
        try:
            os.link(temporario, destino)
        except FileExistsError as erro:
            raise FileExistsError(
                f"Já existe uma restauração pendente: {destino}"
            ) from erro
    return destino


def _conectar_com_trava_exclusiva(target: Path) -> sqlite3.Connection:
    limite = time.monotonic() + 30
    while True:
        destino = sqlite3.connect(target, timeout=max(0, limite - time.monotonic()))
        obtida = False
        try:
            destino.execute("BEGIN IMMEDIATE")
            modo = destino.execute("PRAGMA locking_mode=EXCLUSIVE").fetchone()
            if not modo or modo[0].lower() != "exclusive":
                raise RuntimeError("Não foi possível obter bloqueio exclusivo do banco")
            destino.commit()
            restante_ms = max(0, int((limite - time.monotonic()) * 1000))
            destino.execute(f"PRAGMA busy_timeout={restante_ms}")
            try:
                destino.execute("BEGIN EXCLUSIVE")
            except sqlite3.OperationalError as erro:
                codigo = getattr(erro, "sqlite_errorcode", None)
                ocupado = (
                    (codigo & 0xFF) == getattr(sqlite3, "SQLITE_BUSY", 5)
                    if codigo is not None
                    else str(erro) == "database is locked"
                )
                if not ocupado or time.monotonic() >= limite:
                    raise
                logger.warning("Disputa pela trava exclusiva de restauração; tentando novamente.")
            else:
                destino.commit()
                obtida = True
                return destino
        finally:
            if not obtida:
                destino.close()
        time.sleep(min(0.05, max(0, limite - time.monotonic())))


def aplicar_restauracao_pendente(target_db: str | Path) -> Path | None:
    """Aplica restauração antes das conexões da aplicação e mantém snapshot anterior."""
    target = Path(target_db).resolve()
    pendente = caminho_restauracao_pendente(target)
    if not pendente.exists():
        return None
    if not target.is_file():
        raise FileNotFoundError(f"Banco atual não encontrado: {target}")
    if not DatabaseManager._verify_database(pendente):
        raise ValueError(f"Restauração pendente inválida: {pendente}")

    pasta = target.parent / "backups"
    pasta.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    anterior = pasta / f"pre_restore_{timestamp}.db"
    destino = _conectar_com_trava_exclusiva(target)
    try:
        if not pendente.exists():
            return None

        try:
            criar_snapshot_conexao(destino, anterior)
        except Exception:
            anterior.unlink(missing_ok=True)
            raise

        origem = sqlite3.connect(pendente.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            _copiar_banco(origem, destino)
        finally:
            origem.close()

        with tempfile.TemporaryDirectory() as pasta_validacao:
            copia_validacao = Path(pasta_validacao) / "restaurado.db"
            criar_snapshot_conexao(destino, copia_validacao)
            if not DatabaseManager._verify_database(copia_validacao):
                raise RuntimeError(
                    f"Banco restaurado não passou na validação. Backup anterior: {anterior}. "
                    f"Restauração pendente preservada: {pendente}"
                )
        pendente.unlink()
        return anterior
    finally:
        destino.close()
