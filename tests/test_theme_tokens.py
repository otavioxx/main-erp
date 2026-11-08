from dataclasses import FrozenInstanceError

import pytest

from mainerp.ui.theme_tokens import CLARO, DIMENSOES, ESCURO, cores_do_tema


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
