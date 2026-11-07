from mainerp.ui.dialogs.sobre_atualizacoes_dialog import (
    format_release_date,
    parse_changelog,
)


def test_parse_changelog_returns_versions_dates_and_details():
    changelog = """# Histórico de versões

## 0.09 - 2026-11-07

- Atualização online pelo GitHub.

## 0.08 - 2026-11-06

- Correções de vendas.

## 0.07

- Primeira versão distribuída.
"""

    assert parse_changelog(changelog) == [
        ("0.09", "2026-11-07", "- Atualização online pelo GitHub."),
        ("0.08", "2026-11-06", "- Correções de vendas."),
        ("0.07", None, "- Primeira versão distribuída."),
    ]


def test_format_release_date_handles_missing_and_invalid_values():
    assert format_release_date("2026-11-07") == "07/11/2026"
    assert format_release_date(None) == "Não informada"
    assert format_release_date("2026-13-40") == "2026-13-40"
