"""Tokens da identidade visual em preparação para a migração do tema."""

from dataclasses import dataclass
from typing import Literal

NomeTema = Literal["light", "dark"]


@dataclass(frozen=True)
class CoresTema:
    background_window: str
    surface: str
    surface_alt: str
    table_header: str
    border: str
    border_input: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_disabled: str
    surface_disabled: str
    nav_bg: str
    nav_hover: str
    nav_text: str
    accent: str
    accent_hover: str
    accent_text: str
    focus: str
    selection_bg: str
    selection_text: str
    hover_bg: str
    success_text: str
    success_bg: str
    success_border: str
    warning_text: str
    warning_bg: str
    warning_border: str
    danger_text: str
    danger_bg: str
    danger_border: str
    info_text: str
    info_bg: str
    info_border: str
    button_success_bg: str = "#1E7B34"
    button_danger_bg: str = "#B3261E"
    button_semantic_text: str = "#FFFFFF"


@dataclass(frozen=True)
class DimensoesTema:
    altura_linha: int = 22
    altura_controle_minima: int = 20
    espacamento: int = 8
    raio: int = 0
    borda: int = 1
    fonte_familia: str = "Segoe UI"
    fonte_tamanho_pt: int = 12


CLARO = CoresTema(
    background_window="#EEF1F5", surface="#FFFFFF", surface_alt="#F5F7FA",
    table_header="#E1E7EE", border="#C3CCD7", border_input="#8795A3",
    text_primary="#1F2933", text_secondary="#4B5A6A", text_muted="#5C6875",
    text_disabled="#5C6875", surface_disabled="#E1E7EE",
    nav_bg="#0B2A4A", nav_hover="#14406E", nav_text="#DCE6F0",
    accent="#1565A8", accent_hover="#0F5290", accent_text="#1565A8", focus="#1565A8",
    selection_bg="#CFE3F6", selection_text="#0B2A4A", hover_bg="#E8F0F8",
    success_text="#1E6B30", success_bg="#E3F4E7", success_border="#8CCB9A",
    warning_text="#8A5300", warning_bg="#FFF3D6", warning_border="#F0C36D",
    danger_text="#A82019", danger_bg="#FDE7E5", danger_border="#E8A09B",
    info_text="#0F5290", info_bg="#E3F0FA", info_border="#9CC6EA",
)

ESCURO = CoresTema(
    background_window="#1B1F24", surface="#232930", surface_alt="#2A313A",
    table_header="#2F3842", border="#3A444F", border_input="#6B7785",
    text_primary="#E1E6EB", text_secondary="#AEB8C2", text_muted="#A0AFBE",
    text_disabled="#A0AFBE", surface_disabled="#2A313A",
    nav_bg="#121A23", nav_hover="#1C2A3A", nav_text="#C9D3DD",
    accent="#2B6CB0", accent_hover="#2F78C4", accent_text="#87BDF5", focus="#87BDF5",
    selection_bg="#1F4E79", selection_text="#FFFFFF", hover_bg="#2D3640",
    success_text="#6FCF86", success_bg="#1F3A28", success_border="#2F6B43",
    warning_text="#E8B04A", warning_bg="#3B2F17", warning_border="#7A5C1F",
    danger_text="#F28B85", danger_bg="#3F2220", danger_border="#8A3A36",
    info_text="#6DB6F2", info_bg="#1B3248", info_border="#2F5F8F",
)

DIMENSOES = DimensoesTema()


def cores_do_tema(tema: NomeTema) -> CoresTema:
    if tema == "light":
        return CLARO
    if tema == "dark":
        return ESCURO
    raise ValueError(f"Tema desconhecido: {tema!r}")
