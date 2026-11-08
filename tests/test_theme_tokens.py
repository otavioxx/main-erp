import ast
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mainerp.ui.theme_tokens import CLARO, DIMENSOES, ESCURO, cores_do_tema


def _problemas_de_estilo(texto: str, arquivo: str) -> list[str]:
    problemas = []
    arvore = ast.parse(texto, filename=arquivo)
    for node in ast.walk(arvore):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "setStyleSheet":
                problemas.append(f"{arquivo}:{node.lineno}: stylesheet local")
            if (
                isinstance(node.func, ast.Name) and node.func.id == "QColor"
                and node.args and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, (str, int))
            ):
                problemas.append(f"{arquivo}:{node.lineno}: cor QColor fixa")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.search(r"#[0-9a-fA-F]{3,8}\b", node.value):
                problemas.append(f"{arquivo}:{node.lineno}: cor hexadecimal fixa")
            if re.search(r"border(?:-(?:top|bottom)-(?:left|right))?-radius\s*:", node.value):
                problemas.append(f"{arquivo}:{node.lineno}: raio fora do tema")
    return problemas


def test_guardian_detecta_exemplos_de_estilos_e_cores():
    casos = [
        "widget.setStyleSheet('color: red')",
        "QColor('red')",
        "QColor(255, 0, 0)",
        "cor = '#ffffff'",
        "css = 'border-radius: 2px'",
    ]
    assert all(_problemas_de_estilo(caso, "exemplo.py") for caso in casos)
    assert not _problemas_de_estilo("cor = QColor(cores.text_primary)", "exemplo.py")


def test_interface_nao_define_estilos_locais_ou_cores_fixas():
    pasta = Path(__file__).resolve().parents[1] / "mainerp" / "ui"
    problemas = []
    for arquivo in pasta.rglob("*.py"):
        if arquivo.name in {"styles.py", "theme_tokens.py"}:
            continue
        problemas.extend(_problemas_de_estilo(
            arquivo.read_text(encoding="utf-8"), str(arquivo.relative_to(pasta))
        ))
    assert not problemas, "\n".join(problemas)


def contraste(cor_a: str, cor_b: str) -> float:
    def luminancia(cor: str) -> float:
        canais = [int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        canais = [
            c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            for c in canais
        ]
        return sum(
            c * peso for c, peso in zip(canais, (0.2126, 0.7152, 0.0722), strict=True)
        )

    escura, clara = sorted((luminancia(cor_a), luminancia(cor_b)))
    return (clara + 0.05) / (escura + 0.05)


@pytest.mark.parametrize("cores", [CLARO, ESCURO], ids=["claro", "escuro"])
def test_contraste_dos_pares_de_texto_previstos(cores):
    for texto in (cores.text_primary, cores.text_secondary, cores.text_muted):
        for fundo in (
            cores.background_window, cores.surface, cores.surface_alt,
            cores.table_header, cores.hover_bg,
        ):
            assert contraste(texto, fundo) >= 4.5, (texto, fundo)

    for texto, fundo in (
        (cores.nav_text, cores.nav_bg),
        (cores.nav_text, cores.nav_hover),
        (cores.selection_text, cores.selection_bg),
        (cores.success_text, cores.success_bg),
        (cores.warning_text, cores.warning_bg),
        (cores.danger_text, cores.danger_bg),
        (cores.info_text, cores.info_bg),
        (cores.button_semantic_text, cores.button_success_bg),
        (cores.button_semantic_text, cores.button_danger_bg),
        (cores.button_semantic_text, cores.accent),
        (cores.button_semantic_text, cores.accent_hover),
        (cores.accent_text, cores.surface),
        (cores.accent_text, cores.background_window),
        (cores.text_disabled, cores.surface_disabled),
    ):
        assert contraste(texto, fundo) >= 4.5, (texto, fundo)

    for fundo in (cores.surface, cores.background_window):
        assert contraste(cores.focus, fundo) >= 3, (cores.focus, fundo)

    for texto in (cores.success_text, cores.warning_text, cores.danger_text, cores.info_text):
        for fundo in (cores.surface, cores.surface_alt, cores.hover_bg):
            assert contraste(texto, fundo) >= 4.5, (texto, fundo)


def test_tokens_sao_imutaveis_e_tema_invalido_e_recusado():
    assert cores_do_tema("light") is CLARO
    assert cores_do_tema("dark") is ESCURO
    assert DIMENSOES.raio == 0
    assert DIMENSOES.borda == 1
    assert DIMENSOES.altura_linha == 22
    with pytest.raises(FrozenInstanceError):
        setattr(CLARO, "accent", "#000000")  # noqa: B010 - testa imutabilidade
    with pytest.raises(ValueError, match="Tema desconhecido"):
        cores_do_tema("invalido")  # type: ignore[arg-type]


@pytest.mark.parametrize("cores", [CLARO, ESCURO])
def test_navegacao_contraste_ativo_e_foco(cores):
    assert contraste(cores.button_semantic_text, cores.nav_hover) >= 4.5
    assert contraste(cores.nav_text, cores.nav_hover) >= 3
    assert contraste(cores.nav_text, cores.nav_bg) >= 3
