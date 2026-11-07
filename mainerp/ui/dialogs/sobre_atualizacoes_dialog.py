import logging
import re
from datetime import date
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

from mainerp.core.config import obter_config
from mainerp.core.paths import CODE_DIR
from mainerp.ui.dialog_base import DialogBase

logger = logging.getLogger(__name__)

_RELEASE_HEADER = re.compile(
    r"^##\s+(\S+?)(?:\s+-\s+(\d{4}-\d{2}-\d{2}))?\s*$", re.MULTILINE
)


def parse_changelog(text: str) -> list[tuple[str, str | None, str]]:
    releases = []
    current: tuple[str, str | None] | None = None
    body = []

    for line in text.splitlines():
        match = _RELEASE_HEADER.match(line)
        if match:
            if current is not None:
                releases.append((*current, "\n".join(body).strip()))
            current = (match.group(1), match.group(2))
            body = []
        elif current is not None:
            body.append(line)

    if current is not None:
        releases.append((*current, "\n".join(body).strip()))

    return releases


def format_release_date(value: str | None) -> str:
    if value is None:
        return "Não informada"
    try:
        return date.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        logger.warning("Data inválida no CHANGELOG.md: %s", value)
        return value


class SobreAtualizacoesDialog(DialogBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre - MainERP")
        self.resize(720, 600)

        layout = QVBoxLayout(self)
        versao = obter_config().APP_VERSION
        layout.addWidget(QLabel(f"<h2>MainERP v{versao}</h2>"))

        changelog_path = Path(CODE_DIR) / "CHANGELOG.md"
        try:
            changelog = changelog_path.read_text(encoding="utf-8")
        except OSError as error:
            logger.exception("Não foi possível ler o histórico %s", changelog_path)
            releases = []
            historico = f"Não foi possível carregar o histórico de versões.\n{error}"
        else:
            releases = parse_changelog(changelog)
            historico = changelog or "O histórico de versões está vazio."

        release_atual = next(
            (release for release in releases if release[0] == versao), None
        )
        data = format_release_date(release_atual[1] if release_atual else None)
        layout.addWidget(QLabel(f"Data da versão: {data}"))

        texto_atualizacoes = QLabel(
            "As atualizações são verificadas pelo launcher ao abrir o sistema "
            "pelo atalho."
        )
        texto_atualizacoes.setWordWrap(True)
        layout.addWidget(texto_atualizacoes)

        layout.addWidget(QLabel("<h3>Histórico de versões</h3>"))
        self.historico = QTextBrowser()
        self.historico.setOpenExternalLinks(False)
        self.historico.setMarkdown(historico)
        layout.addWidget(self.historico, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes)
