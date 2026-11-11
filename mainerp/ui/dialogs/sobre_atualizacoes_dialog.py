import logging
import os
import re
import tempfile
from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QTextBrowser,
    QVBoxLayout,
)

from mainerp.core.config import obter_config
from mainerp.core.paths import CODE_DIR, DATA_DIR
from mainerp.ui.dialog_base import DialogBase

logger = logging.getLogger(__name__)

# Aceita o padrão Keep a Changelog e o formato antigo:
# ## [0.10.9] - 2026-11-09
# ## 0.10.9 - 2026-11-09
# ## [Unreleased]
_RELEASE_HEADER = re.compile(
    r"^##\s+(?:\[([^\]]+)\]|(\S+?))"
    r"(?:\s+-\s+(\d{4}-\d{2}-\d{2}))?\s*$",
    re.MULTILINE,
)


def parse_changelog(text: str) -> list[tuple[str, str | None, str]]:
    """Separa o CHANGELOG em versões, datas e respectivos conteúdos."""
    releases: list[tuple[str, str | None, str]] = []
    current: tuple[str, str | None] | None = None
    body: list[str] = []

    for line in text.splitlines():
        match = _RELEASE_HEADER.match(line)

        if match:
            if current is not None:
                releases.append((current[0], current[1], "\n".join(body).strip()))

            nome = match.group(1) or match.group(2)
            if nome is None:
                continue

            current = (nome, match.group(3))
            body = []
        elif current is not None:
            body.append(line)

    if current is not None:
        releases.append((current[0], current[1], "\n".join(body).strip()))

    return releases


def format_release_date(value: str | None) -> str:
    """Converte uma data ISO para o formato brasileiro."""
    if value is None:
        return "Não informada"

    try:
        return date.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        logger.warning("Data inválida no CHANGELOG.md: %s", value)
        return value


def _chave_versao(versao: str) -> tuple[int, int, int] | None:
    """Converte uma versão numérica em uma chave comparável."""
    if not re.fullmatch(r"\d+(?:\.\d+){0,2}", versao):
        return None

    partes = [int(parte) for parte in versao.split(".")]
    partes.extend([0] * (3 - len(partes)))

    return partes[0], partes[1], partes[2]


def _formatar_cabecalho_release(
    nome: str,
    data: str | None,
) -> str:
    """Formata o título de uma versão para exibição."""
    cabecalho = f"## [{nome}]"

    if data:
        cabecalho += f" - {format_release_date(data)}"

    return cabecalho


def preparar_novidades(
    versao: str,
    codigo: Path,
    dados: Path,
    arquivo_ok: str | None,
) -> tuple[Path, str] | None:
    """Localiza notas de uma atualização ainda não apresentada pelo launcher."""
    atual = _chave_versao(versao)

    if atual is None:
        raise ValueError(f"Versão inválida: {versao!r}")

    if not arquivo_ok or Path(arquivo_ok).resolve() != (codigo / ".ok").resolve():
        return None

    marcador = dados / "novidades" / f"{versao}.lido"

    if marcador.exists():
        return None

    anteriores: list[tuple[int, int, int]] = []

    for pasta in codigo.parent.iterdir():
        chave = _chave_versao(pasta.name)

        if chave is not None and chave > atual and (pasta / "main.py").is_file():
            return None

        if (
            chave is not None
            and chave < atual
            and (pasta / "main.py").is_file()
            and (pasta / ".ok").is_file()
            and not (pasta / ".ruim").exists()
        ):
            anteriores.append(chave)

    if not anteriores:
        return None

    anterior = max(anteriores)
    texto = (codigo / "CHANGELOG.md").read_text(encoding="utf-8")
    releases = parse_changelog(texto)

    notas: list[str] = []
    encontrou_atual = False

    for nome, data, corpo in releases:
        chave = _chave_versao(nome)

        if chave is None or not (anterior < chave <= atual) or not corpo:
            continue

        encontrou_atual = encontrou_atual or chave == atual
        cabecalho = _formatar_cabecalho_release(nome, data)
        notas.append(f"{cabecalho}\n\n{corpo}")

    if not encontrou_atual:
        raise ValueError(f"Não há novidades para a versão {versao} no histórico.")

    return marcador, "\n\n".join(notas)


def registrar_novidades_lidas(marcador: Path) -> None:
    """Registra a leitura após fechar o diálogo, sem gravar arquivos incompletos."""
    marcador.parent.mkdir(parents=True, exist_ok=True)
    temporario: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=marcador.parent,
            delete=False,
        ) as arquivo:
            temporario = Path(arquivo.name)
            arquivo.write("lido\n")

        os.replace(temporario, marcador)
    finally:
        if temporario is not None and temporario.exists():
            temporario.unlink()


class NovidadesDialog(DialogBase):
    """Exibe as alterações incluídas em uma atualização."""

    def __init__(
        self,
        versao: str,
        notas: str,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Novidades da atualização")
        self.setFixedSize(650, 500)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<h2>MainERP atualizado para a versão {versao}</h2>"))

        descricao = QLabel("Confira as novidades incluídas nesta atualização.")
        descricao.setWordWrap(True)
        layout.addWidget(descricao)

        self.novidades = QTextBrowser()
        self.novidades.setOpenExternalLinks(False)
        self.novidades.setMarkdown(notas)
        layout.addWidget(self.novidades, 1)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)

        botao_fechar = botoes.button(QDialogButtonBox.StandardButton.Close)
        if botao_fechar is not None:
            botao_fechar.setText("Fechar")

        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes)


def mostrar_novidades_apos_atualizacao(
    parent,
    versao: str,
) -> None:
    """Apresenta as novidades quando uma nova versão é confirmada pelo launcher."""
    try:
        novidades = preparar_novidades(
            versao,
            Path(CODE_DIR),
            Path(DATA_DIR),
            os.environ.get("MAINERP_OK_FILE"),
        )
    except (OSError, UnicodeError, ValueError) as erro:
        logger.exception("Não foi possível carregar as novidades da atualização")
        QMessageBox.warning(
            parent,
            "Novidades da atualização",
            "Não foi possível carregar as novidades. Consulte Sobre "
            "para ver as informações do sistema.\n\n"
            f"Detalhes: {erro}",
        )
        return

    if novidades is None:
        return

    marcador, notas = novidades
    NovidadesDialog(versao, notas, parent).exec()

    try:
        registrar_novidades_lidas(marcador)
    except OSError as erro:
        logger.exception("Não foi possível registrar a leitura das novidades")
        QMessageBox.warning(
            parent,
            "Novidades da atualização",
            "Não foi possível registrar que as novidades foram lidas. "
            "Elas poderão aparecer novamente na próxima abertura.\n\n"
            f"Detalhes: {erro}",
        )


class SobreAtualizacoesDialog(DialogBase):
    """Apresenta informações institucionais do MainERP."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Sobre - MainERP")
        self.setFixedSize(640, 550)

        layout = QVBoxLayout(self)

        config = obter_config()
        versao = config.APP_VERSION

        # Identificação do sistema.
        titulo = QLabel("<h1>MainERP</h1>")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Gestão empresarial simples e acessível")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitulo)

        layout.addSpacing(16)

        # Consulta a data de lançamento no CHANGELOG.
        changelog_path = Path(CODE_DIR) / "CHANGELOG.md"
        data_versao = "Não informada"

        try:
            changelog = changelog_path.read_text(encoding="utf-8")
            releases = parse_changelog(changelog)

            release_atual = next(
                (release for release in releases if release[0] == versao),
                None,
            )

            if release_atual is not None:
                data_versao = format_release_date(release_atual[1])

        except (OSError, UnicodeError):
            logger.exception(
                "Não foi possível consultar a data da versão em %s",
                changelog_path,
            )

        versao_label = QLabel(f"<b>Versão:</b> {versao}")
        versao_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(versao_label)

        data_label = QLabel(f"<b>Data de lançamento:</b> {data_versao}")
        data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(data_label)

        layout.addSpacing(20)

        # Apresentação do produto.
        layout.addWidget(QLabel("<h3>Sobre o MainERP</h3>"))

        descricao = QLabel(
            "O MainERP é um sistema de gestão empresarial desenvolvido "
            "para pequenos comércios e lojas físicas. Seu objetivo é "
            "simplificar a rotina dos negócios, reunindo em um só lugar "
            "ferramentas para vendas, compras, estoque e controle operacional."
            "<br><br>"
            "Uma solução prática e acessível para ajudar pequenos "
            "empreendedores a organizar e administrar melhor suas empresas."
        )
        descricao.setWordWrap(True)
        layout.addWidget(descricao)

        layout.addSpacing(12)

        # Identificação do desenvolvedor.
        layout.addWidget(QLabel("<h3>Desenvolvimento</h3>"))

        desenvolvedor = QLabel(
            "Desenvolvido independentemente por <b>Otávio Oliveira</b>."
        )
        desenvolvedor.setWordWrap(True)
        layout.addWidget(desenvolvedor)

        layout.addSpacing(12)

        # Contato de suporte.
        layout.addWidget(QLabel("<h3>Suporte e atendimento</h3>"))

        suporte = QLabel("Precisa de ajuda ou tem alguma sugestão? Entre em contato:")
        suporte.setWordWrap(True)
        layout.addWidget(suporte)

        email = QLabel('<a href="mailto:otaviox@proton.me">otaviox@proton.me</a>')
        email.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        email.setOpenExternalLinks(True)
        layout.addWidget(email)

        descricao_suporte = QLabel(
            "Atendimento para dúvidas, suporte técnico, problemas "
            "e sugestões de melhorias."
        )
        descricao_suporte.setWordWrap(True)
        layout.addWidget(descricao_suporte)

        layout.addStretch(1)

        # Rodapé.
        copyright_label = QLabel(
            f"MainERP © {date.today().year} | Desenvolvido por Otávio Oliveira"
        )
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        botoes.accepted.connect(self.accept)
        layout.addWidget(botoes)
