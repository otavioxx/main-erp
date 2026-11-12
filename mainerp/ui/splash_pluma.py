"""Splash de inicialização com a identidade Pluma e barra de progresso.

Segue docs/identidade_visual.md: cores somente por tokens do tema ativo
(CoresTema), superfícies planas, bordas retas e sem gradientes decorativos.
O símbolo é o pluma-simbolo.svg embutido neste módulo e desenhado com
QSvgRenderer; assim ele não depende de arquivos extras no pacote da release.

O percentual exibido é sempre informado por quem chama (etapas realmente
concluídas): a splash não simula avanço.
"""

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QSplashScreen

from mainerp.ui.theme_tokens import DIMENSOES, CoresTema

# pluma-simbolo.svg (canvas 256x256; símbolo ocupa x 38..226 e y 25..222)
# As cores são preenchidas dinamicamente pelos tokens do tema ativo.
SIMBOLO_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg"
     width="256" height="256" viewBox="0 0 256 256">
    <g transform="translate(22 18) scale(1.35)">
        <defs>
            <linearGradient id="plumaBlue" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="{cor_inicio}"/>
                <stop offset="52%" stop-color="{cor_meio}"/>
                <stop offset="100%" stop-color="{cor_fim}"/>
            </linearGradient>
        </defs>
        <g fill="url(#plumaBlue)">
            <path d="M16 105 C31 52 78 18 151 5 C143 36 126 58 101 73 C76 89 47 99 16 105 Z"/>
            <path d="M16 105 C47 91 82 77 111 56 C103 88 77 112 42 126 C30 132 20 140 12 151 C12 135 13 119 16 105 Z"/>
        </g>
        <path
            d="M17 105 C52 91 92 72 133 31"
            fill="none"
            stroke="{cor_traco}"
            stroke-width="3.5"
            stroke-linecap="round"
            opacity=".9"
        />
    </g>
</svg>
"""

SVG_CANVAS = 256.0
SVG_CAIXA_X = (38.0, 226.0)
SVG_CAIXA_Y = (25.0, 222.0)

LARGURA, ALTURA = 450, 300
LARGURA_SIMBOLO = 58.0
TOPO_SIMBOLO = 60.0
LARGURA_BARRA = 260
ALTURA_BARRA = 4
TOPO_BARRA = 214


def _criar_svg(cores: CoresTema) -> bytes:
    """Gera o SVG utilizando exclusivamente as cores do tema ativo."""
    svg = SIMBOLO_SVG.format(
        cor_inicio=cores.accent_text,
        cor_meio=cores.accent,
        cor_fim=cores.accent_hover,
        cor_traco=cores.text_primary,
    )
    return svg.encode("utf-8")


class PlumaSplash(QSplashScreen):
    """Splash com símbolo, marca, barra de progresso e mensagem da etapa."""

    def __init__(
        self,
        *,
        cores: CoresTema,
        fonte_familia: str = DIMENSOES.fonte_familia,
        rodape: str = "",
    ):
        self._cores = cores
        self._fonte = fonte_familia
        self._rodape = rodape
        self._percentual = 0.0
        self._mensagem = ""
        self._svg = QSvgRenderer(QByteArray(_criar_svg(cores)))

        tela = QApplication.primaryScreen()
        self._escala = tela.devicePixelRatio() if tela is not None else 1.0
        super().__init__(self._montar_pixmap())

    @property
    def percentual(self) -> float:
        return self._percentual

    def atualizar(self, mensagem: str, percentual: float | None = None):
        """Atualiza a mensagem e, se informado, o percentual concluído (0 a 100).

        Sem percentual, a barra permanece onde está. Ela nunca retrocede.
        """
        if percentual is not None:
            self._percentual = max(
                self._percentual,
                min(100.0, float(percentual)),
            )

        self._mensagem = mensagem
        self.setPixmap(self._montar_pixmap())

    def _fonte_px(
        self,
        tamanho: int,
        peso=QFont.Weight.Normal,
        espaco: float = 0.0,
    ):
        fonte = QFont(self._fonte)
        fonte.setPixelSize(tamanho)
        fonte.setWeight(peso)

        if espaco:
            fonte.setLetterSpacing(
                QFont.SpacingType.AbsoluteSpacing,
                espaco,
            )

        return fonte

    def _desenhar_simbolo(self, p: QPainter):
        escala = LARGURA_SIMBOLO / (SVG_CAIXA_X[1] - SVG_CAIXA_X[0])
        centro_svg_x = (SVG_CAIXA_X[0] + SVG_CAIXA_X[1]) / 2

        alvo = QRectF(
            LARGURA / 2 - centro_svg_x * escala,
            TOPO_SIMBOLO - SVG_CAIXA_Y[0] * escala,
            SVG_CANVAS * escala,
            SVG_CANVAS * escala,
        )

        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._svg.render(p, alvo)

        # Formas retas do restante da splash ficam nítidas,
        # sem suavização.
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    def _montar_pixmap(self) -> QPixmap:
        cores = self._cores

        pixmap = QPixmap(
            round(LARGURA * self._escala),
            round(ALTURA * self._escala),
        )
        pixmap.setDevicePixelRatio(self._escala)
        pixmap.fill(QColor(cores.surface))

        p = QPainter(pixmap)
        p.setRenderHint(
            QPainter.RenderHint.TextAntialiasing,
            True,
        )

        self._desenhar_simbolo(p)

        # Marca (o espaçamento entre letras deixa um vazio no fim; compensa).
        espaco = 6.0
        p.setFont(
            self._fonte_px(
                26,
                QFont.Weight.DemiBold,
                espaco,
            )
        )
        p.setPen(QColor(cores.text_primary))
        p.drawText(
            QRectF(espaco / 2, 128, LARGURA, 36),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "PLUMA",
        )

        espaco_lema = 2.4
        p.setFont(
            self._fonte_px(
                9,
                QFont.Weight.DemiBold,
                espaco_lema,
            )
        )
        p.setPen(QColor(cores.accent_text))
        p.drawText(
            QRectF(espaco_lema / 2, 168, LARGURA, 16),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "TECNOLOGIA  •  GESTÃO  •  RESULTADOS",
        )

        # Barra de progresso reta: trilho e preenchimento em cores sólidas.
        x = (LARGURA - LARGURA_BARRA) / 2

        p.fillRect(
            QRectF(
                x,
                TOPO_BARRA,
                LARGURA_BARRA,
                ALTURA_BARRA,
            ),
            QColor(cores.border),
        )

        preenchido = LARGURA_BARRA * self._percentual / 100.0

        if preenchido > 0:
            p.fillRect(
                QRectF(
                    x,
                    TOPO_BARRA,
                    preenchido,
                    ALTURA_BARRA,
                ),
                QColor(cores.accent_text),
            )

        # Mensagem da etapa (esquerda) e percentual (direita).
        p.setPen(QColor(cores.text_secondary))
        p.setFont(self._fonte_px(10))

        largura_msg = LARGURA_BARRA - 44
        texto = p.fontMetrics().elidedText(
            self._mensagem,
            Qt.TextElideMode.ElideRight,
            largura_msg,
        )

        p.drawText(
            QRectF(
                x,
                TOPO_BARRA + 10,
                largura_msg,
                18,
            ),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            texto,
        )

        p.setFont(
            self._fonte_px(
                10,
                QFont.Weight.DemiBold,
            )
        )
        p.drawText(
            QRectF(
                x + LARGURA_BARRA - 44,
                TOPO_BARRA + 10,
                44,
                18,
            ),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"{round(self._percentual)}%",
        )

        if self._rodape:
            p.setFont(self._fonte_px(9))
            p.drawText(
                QRectF(0, ALTURA - 28, LARGURA, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self._rodape,
            )

        p.setPen(QColor(cores.border))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, 0, LARGURA - 1, ALTURA - 1)

        p.end()
        return pixmap
