"""Executa o instalador empacotado em uma pasta temporária exclusiva."""

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="mainerp-instalador-") as pasta:
        destino = Path(pasta)
        with zipfile.ZipFile(Path(__file__).parent) as pacote:
            for item in pacote.infolist():
                alvo = (destino / item.filename).resolve()
                if alvo != destino and destino not in alvo.parents:
                    raise ValueError(f"Caminho inválido no instalador: {item.filename}")
            pacote.extractall(destino)
        return subprocess.call(
            [sys.executable, str(destino / "distribuicao" / "instalar.py"), *sys.argv[1:]]
        )


if __name__ == "__main__":
    sys.exit(main())
