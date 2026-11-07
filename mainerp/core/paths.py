# \erp\paths.py
"""Caminhos centrais do MainERP.

O sistema separa duas coisas que antes ficavam misturadas:

- CODE_DIR: pasta com o código desta versão. Muda a cada atualização
  (cada release fica em sua própria pasta e nunca guarda dados do usuário).
- DATA_DIR: banco de dados, config.json, backups e relatórios. Nenhuma
  atualização toca nesta pasta.

Local dos dados (nesta ordem):
1. variável de ambiente MAINERP_DATA, se existir;
2. %LOCALAPPDATA%\\MainERP\\dados (Windows);
3. ~/.mainerp/dados (outros sistemas, útil para desenvolvimento).
"""

import os
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[2]


def _resolver_data_dir() -> Path:
    override = os.environ.get("MAINERP_DATA")
    if override:
        return Path(override).expanduser()

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / "MainERP" / "dados"

    return Path.home() / ".mainerp" / "dados"


DATA_DIR = _resolver_data_dir()


def caminho_dados(nome: str) -> str:
    """Resolve um nome relativo para dentro de DATA_DIR (absolutos passam direto)."""
    caminho = Path(nome)
    if not caminho.is_absolute():
        caminho = DATA_DIR / caminho
    return str(caminho)


def preparar_ambiente() -> None:
    """Cria a pasta de dados e usa-a como diretório de trabalho.

    Vários pontos do sistema usam caminhos relativos (por exemplo "relatorios").
    Com o diretório de trabalho em DATA_DIR, eles passam a apontar sempre para
    a pasta de dados, independentemente de onde o atalho foi iniciado.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(DATA_DIR)
