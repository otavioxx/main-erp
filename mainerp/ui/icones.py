"""Ícones Lucide locais, renderizados com as cores do tema."""

import re
from pathlib import Path

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from mainerp.ui.styles import cores_ativas

PASTA_ICONES = Path(__file__).parent / "icons"


def _pixmap(svg: bytes, cor: str, escala: int) -> QPixmap:
    dados = svg.replace(b"currentColor", cor.encode("ascii"))
    renderer = QSvgRenderer(QByteArray(dados))
    if not renderer.isValid():
        raise ValueError("Ícone SVG inválido")
    pixmap = QPixmap(24 * escala, 24 * escala)
    pixmap.setDevicePixelRatio(escala)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, 24, 24))
    painter.end()
    return pixmap


def icone(nome: str, cor: str, cor_selecionado: str | None = None) -> QIcon:
    """Cria ícone monocromático com variantes para telas de alta densidade."""
    if not re.fullmatch(r"[a-z0-9-]+", nome):
        raise ValueError(f"Nome de ícone inválido: {nome!r}")
    if not QColor(cor).isValid() or (
        cor_selecionado is not None and not QColor(cor_selecionado).isValid()
    ):
        raise ValueError("Cor de ícone inválida")
    caminho = PASTA_ICONES / f"{nome}.svg"
    svg = caminho.read_bytes()
    if b"currentColor" not in svg:
        raise ValueError(f"Ícone sem cor configurável: {caminho}")
    desabilitado = cores_ativas().text_disabled
    resultado = QIcon()
    for escala in (1, 2, 3):
        normal = _pixmap(svg, cor, escala)
        selecionado = _pixmap(svg, cor_selecionado or cor, escala)
        inativo = _pixmap(svg, desabilitado, escala)
        for modo in (QIcon.Mode.Normal, QIcon.Mode.Active, QIcon.Mode.Selected):
            resultado.addPixmap(normal, modo, QIcon.State.Off)
            resultado.addPixmap(selecionado, modo, QIcon.State.On)
        resultado.addPixmap(inativo, QIcon.Mode.Disabled, QIcon.State.Off)
        resultado.addPixmap(inativo, QIcon.Mode.Disabled, QIcon.State.On)
    return resultado
