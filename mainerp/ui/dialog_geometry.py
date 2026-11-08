"""Posicionamento de diálogos na área útil do monitor."""

from PyQt6.QtWidgets import QDialog


def ajustar_dialogo_a_tela(dialogo: QDialog) -> None:
    parent = dialogo.parentWidget()
    screen = parent.screen() if parent is not None else dialogo.screen()
    if screen is None:
        raise RuntimeError("Não foi possível localizar a tela do diálogo.")
    area = screen.availableGeometry()
    frame = dialogo.frameGeometry()
    extra_width = max(0, frame.width() - dialogo.width())
    extra_height = max(0, frame.height() - dialogo.height())
    dialogo.resize(
        min(dialogo.width(), max(1, area.width() - extra_width)),
        min(dialogo.height(), max(1, area.height() - extra_height)),
    )
    frame = dialogo.frameGeometry()
    dialogo.move(
        area.x() + max(0, (area.width() - frame.width()) // 2),
        area.y() + max(0, (area.height() - frame.height()) // 2),
    )
