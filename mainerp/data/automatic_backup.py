import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

logger = logging.getLogger(__name__)

BACKUP_PREFIX = "backup_automatico_"
BACKUP_INTERVAL = timedelta(days=1)
BACKUP_RETENTION = timedelta(days=30)


def criar_snapshot_sqlite(caminho_banco: str | Path, destino: str | Path) -> None:
    """Copia o banco ativo, incluindo WAL, e verifica a integridade da cópia."""
    caminho_banco = Path(caminho_banco)
    if not caminho_banco.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado: {caminho_banco}")

    origem = sqlite3.connect(caminho_banco, timeout=30)
    try:
        copia = sqlite3.connect(destino, timeout=30)
        try:
            origem.backup(copia)
            resultado = copia.execute("PRAGMA integrity_check").fetchone()
            if not resultado or resultado[0] != "ok":
                raise sqlite3.DatabaseError(
                    f"Verificação de integridade do backup falhou: {resultado}"
                )
        finally:
            copia.close()
    finally:
        origem.close()


def criar_backup_automatico(
    caminho_banco: str | Path,
    pasta_backups: str | Path,
    agora: datetime | None = None,
) -> Path:
    """Cria um snapshot SQLite consistente e valida-o antes de publicá-lo."""
    caminho_banco = Path(caminho_banco)
    pasta_backups = Path(pasta_backups)
    if not caminho_banco.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado: {caminho_banco}")

    pasta_backups.mkdir(parents=True, exist_ok=True)
    agora = agora or datetime.now()
    timestamp = agora.strftime("%Y%m%d_%H%M%S")
    destino = pasta_backups / f"{BACKUP_PREFIX}{timestamp}.db"
    temporario = pasta_backups / f"{BACKUP_PREFIX}{timestamp}.tmp"

    try:
        criar_snapshot_sqlite(caminho_banco, temporario)
        os.replace(temporario, destino)
        return destino
    except Exception:
        temporario.unlink(missing_ok=True)
        raise


def backup_automatico_vencido(
    pasta_backups: str | Path,
    agora: datetime | None = None,
    intervalo: timedelta = BACKUP_INTERVAL,
) -> bool:
    """Indica se não há snapshot automático ou se o mais recente venceu."""
    pasta_backups = Path(pasta_backups)
    arquivos = list(pasta_backups.glob(f"{BACKUP_PREFIX}*.db"))
    if not arquivos:
        return True

    mais_recente = max(arquivo.stat().st_mtime for arquivo in arquivos)
    agora_timestamp = (agora or datetime.now()).timestamp()
    return agora_timestamp - mais_recente >= intervalo.total_seconds()


def aplicar_retencao_backups(
    pasta_backups: str | Path,
    agora: datetime | None = None,
    retencao: timedelta = BACKUP_RETENTION,
) -> list[Path]:
    """Remove somente snapshots automáticos vencidos pela política de retenção."""
    pasta_backups = Path(pasta_backups)
    limite = (agora or datetime.now()).timestamp() - retencao.total_seconds()
    removidos = []

    for arquivo in pasta_backups.glob(f"{BACKUP_PREFIX}*.db"):
        if arquivo.stat().st_mtime < limite:
            arquivo.unlink()
            removidos.append(arquivo)

    return removidos


class _BackupWorker(QThread):
    backup_criado = pyqtSignal(str)
    backup_falhou = pyqtSignal(str)

    def __init__(self, caminho_banco: Path, pasta_backups: Path):
        super().__init__()
        self.caminho_banco = caminho_banco
        self.pasta_backups = pasta_backups

    def run(self):
        try:
            backup = criar_backup_automatico(self.caminho_banco, self.pasta_backups)
            try:
                removidos = aplicar_retencao_backups(self.pasta_backups)
                if removidos:
                    logger.info("Retenção removeu %d backup(s) automático(s)", len(removidos))
            except OSError:
                logger.exception("Falha ao aplicar retenção de backups automáticos")
            self.backup_criado.emit(str(backup))
        except Exception as erro:
            logger.exception("Falha ao criar backup automático")
            self.backup_falhou.emit(str(erro))


class BackupAutomatico(QObject):
    """Executa backup diário em segundo plano enquanto o aplicativo está aberto."""

    backup_concluido = pyqtSignal(str)
    backup_falhou = pyqtSignal(str)
    operacao_finalizada = pyqtSignal()

    VERIFICACAO_INTERVALO_MS = 60 * 60 * 1000

    def __init__(self, caminho_banco: str | Path, parent=None):
        super().__init__(parent)
        self.caminho_banco = Path(caminho_banco).resolve()
        self.pasta_backups = self.caminho_banco.parent / "backups"
        self._worker: _BackupWorker | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(self.VERIFICACAO_INTERVALO_MS)
        self._timer.timeout.connect(self.verificar_e_executar)

    @property
    def em_execucao(self) -> bool:
        return self._worker is not None

    def iniciar(self):
        """Verifica no início e depois periodicamente se há backup vencido."""
        self._timer.start()
        QTimer.singleShot(0, self.verificar_e_executar)

    def parar(self):
        self._timer.stop()

    def verificar_e_executar(self):
        if self.em_execucao or not backup_automatico_vencido(self.pasta_backups):
            return

        self._worker = _BackupWorker(self.caminho_banco, self.pasta_backups)
        self._worker.backup_criado.connect(self._ao_criar_backup)
        self._worker.backup_falhou.connect(self.backup_falhou)
        self._worker.finished.connect(self._ao_finalizar_operacao)
        self._worker.start()

    def _ao_criar_backup(self, caminho: str):
        logger.info("Backup automático criado: %s", caminho)
        self.backup_concluido.emit(caminho)

    def _ao_finalizar_operacao(self):
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()
        self.operacao_finalizada.emit()
