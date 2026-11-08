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


def criar_snapshot_conexao(origem: sqlite3.Connection, destino: str | Path) -> None:
    """Cria e verifica um snapshot a partir de uma conexão existente."""
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


def criar_snapshot_sqlite(caminho_banco: str | Path, destino: str | Path) -> None:
    """Copia o banco ativo, incluindo WAL, e verifica a integridade da cópia."""
    caminho_banco = Path(caminho_banco)
    if not caminho_banco.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado: {caminho_banco}")

    origem = sqlite3.connect(caminho_banco, timeout=30)
    try:
        criar_snapshot_conexao(origem, destino)
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
    ultimo = ultimo_backup_automatico(pasta_backups)
    return ultimo is None or (
        (agora or datetime.now()).timestamp() - ultimo.timestamp()
        >= intervalo.total_seconds()
    )


def ultimo_backup_automatico(pasta_backups: str | Path) -> datetime | None:
    """Obtém a data do arquivo automático mais recente, sem validar seu conteúdo."""
    try:
        entradas = os.scandir(pasta_backups)
    except FileNotFoundError:
        return None
    with entradas:
        datas = [
            entrada.stat().st_mtime for entrada in entradas
            if entrada.name.startswith(BACKUP_PREFIX)
            and entrada.name.endswith(".db") and entrada.is_file()
        ]
    return datetime.fromtimestamp(max(datas)) if datas else None


def aplicar_retencao_backups(
    pasta_backups: str | Path,
    agora: datetime | None = None,
    retencao: timedelta = BACKUP_RETENTION,
) -> list[Path]:
    """Remove somente snapshots automáticos vencidos pela política de retenção."""
    pasta_backups = Path(pasta_backups)
    limite = (agora or datetime.now()).timestamp() - retencao.total_seconds()
    removidos = []

    try:
        entradas = os.scandir(pasta_backups)
    except FileNotFoundError:
        return removidos
    with entradas:
        for entrada in entradas:
            if (entrada.name.startswith(BACKUP_PREFIX)
                    and entrada.name.endswith(".db")
                    and entrada.stat().st_mtime < limite):
                arquivo = pasta_backups / entrada.name
                arquivo.unlink()
                removidos.append(arquivo)

    return removidos


class _BackupWorker(QThread):
    backup_criado = pyqtSignal(str)
    backup_falhou = pyqtSignal(str)
    retencao_falhou = pyqtSignal(str)

    def __init__(self, caminho_banco: Path, pasta_backups: Path):
        super().__init__()
        self.caminho_banco = caminho_banco
        self.pasta_backups = pasta_backups

    def run(self):
        try:
            backup = criar_backup_automatico(self.caminho_banco, self.pasta_backups)
            self.backup_criado.emit(str(backup))
            try:
                removidos = aplicar_retencao_backups(self.pasta_backups)
                if removidos:
                    logger.info("Retenção removeu %d backup(s) automático(s)", len(removidos))
            except OSError as erro:
                logger.exception("Falha ao aplicar retenção de backups automáticos")
                self.retencao_falhou.emit(str(erro))
        except Exception as erro:
            logger.exception("Falha ao criar backup automático")
            self.backup_falhou.emit(str(erro))


class BackupAutomatico(QObject):
    """Executa backup diário em segundo plano enquanto o aplicativo está aberto."""

    backup_concluido = pyqtSignal(str)
    backup_falhou = pyqtSignal(str)
    retencao_falhou = pyqtSignal(str)
    situacao_alterada = pyqtSignal()
    operacao_finalizada = pyqtSignal()

    VERIFICACAO_INTERVALO_MS = 60 * 60 * 1000

    def __init__(self, caminho_banco: str | Path, parent=None):
        super().__init__(parent)
        self.caminho_banco = Path(caminho_banco).resolve()
        self.pasta_backups = self.caminho_banco.parent / "backups"
        self._worker: _BackupWorker | None = None
        self.ultimo_backup: datetime | None = None
        self.resultado = "Ainda não verificado"
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
        if not self._timer.isActive() or self.em_execucao:
            return
        try:
            self.ultimo_backup = ultimo_backup_automatico(self.pasta_backups)
        except OSError as erro:
            self._ao_falhar(f"Falha ao verificar agendamento: {erro}")
            return
        if self.ultimo_backup is not None and (
            datetime.now().timestamp() - self.ultimo_backup.timestamp()
            < BACKUP_INTERVAL.total_seconds()
        ):
            if self.resultado == "Ainda não verificado":
                self.resultado = "Arquivo existente (não verificado nesta sessão)"
            self.situacao_alterada.emit()
            return
        self.resultado = "Backup em andamento"
        self.situacao_alterada.emit()
        self._worker = _BackupWorker(self.caminho_banco, self.pasta_backups)
        self._worker.backup_criado.connect(self._ao_criar_backup)
        self._worker.backup_falhou.connect(self._ao_falhar)
        self._worker.retencao_falhou.connect(self._ao_falhar_retencao)
        self._worker.finished.connect(self._ao_finalizar_operacao)
        try:
            self._worker.start()
        except RuntimeError as erro:
            self._worker.deleteLater()
            self._worker = None
            self._ao_falhar(f"Falha ao iniciar backup: {erro}")

    def _ao_criar_backup(self, caminho: str):
        logger.info("Backup automático criado: %s", caminho)
        self.ultimo_backup = datetime.now()
        self.resultado = "Concluído"
        self.situacao_alterada.emit()
        self.backup_concluido.emit(caminho)

    def _ao_falhar(self, erro: str):
        logger.error("Backup automático: %s", erro)
        self.resultado = f"Falha: {erro}"
        self.situacao_alterada.emit()
        self.backup_falhou.emit(erro)

    def _ao_falhar_retencao(self, erro: str):
        self.resultado = f"Concluído; falha na retenção: {erro}"
        self.situacao_alterada.emit()
        self.retencao_falhou.emit(erro)

    def _ao_finalizar_operacao(self):
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()
        self.operacao_finalizada.emit()
