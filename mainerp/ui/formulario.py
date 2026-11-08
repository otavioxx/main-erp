"""Convenções visuais dos botões de formulários."""

from PyQt6.QtWidgets import QDialogButtonBox


def configurar_botoes_formulario(botoes: QDialogButtonBox) -> None:
    confirmar = botoes.button(QDialogButtonBox.StandardButton.Ok)
    cancelar = botoes.button(QDialogButtonBox.StandardButton.Cancel)
    if confirmar is None or cancelar is None:
        raise RuntimeError("Não foi possível criar os botões do formulário.")
    confirmar.setProperty("class", "primary")
    cancelar.setProperty("class", "secondary")
