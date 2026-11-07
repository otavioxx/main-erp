#!/usr/bin/env python3
"""Gera o pacote de release do MainERP (um .zip com o código-fonte).

Uso (na pasta do projeto):
    python distribuicao/criar_release.py              # gera dist/MainERP-<versão>.zip
    python distribuicao/criar_release.py --instalar   # idem + coloca o zip em atualizacoes\\
                                                      # (aplicado na próxima abertura do sistema)

A versão vem de APP_VERSION em config.py: aumente-a antes de cada release.
Também é gerado dist/version.json (versão, nome do zip e SHA256), que serve de
manifesto quando as atualizações passarem a vir de um servidor.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent

# Nada disso entra no release: são dados do usuário, caches e ferramentas.
EXCLUIR_PASTAS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "dist",
    "distribuicao",
    "data",
    "relatorios",
    "backups",
}
EXCLUIR_NOMES = {
    ".gitignore",
    "config.json",
    "backup_settings.json",
    "backup_config.json",
}
EXCLUIR_EXTENSOES = {".pyc", ".pyo", ".db", ".db-journal", ".zip", ".log"}


def ler_versao() -> str:
    texto = (PROJETO / "config.py").read_text(encoding="utf-8")
    m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', texto)
    if not m:
        sys.exit("APP_VERSION não encontrada em config.py")
    return m.group(1)


def arquivos_do_release():
    for pasta, subpastas, arquivos in os.walk(PROJETO):
        subpastas[:] = sorted(d for d in subpastas if d not in EXCLUIR_PASTAS)
        for nome in sorted(arquivos):
            caminho = Path(pasta) / nome
            if nome in EXCLUIR_NOMES or caminho.suffix.lower() in EXCLUIR_EXTENSOES:
                continue
            yield caminho


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def construir_zip(pasta_saida: Path) -> Path:
    versao = ler_versao()
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = pasta_saida / f"MainERP-{versao}.zip"
    arquivos = list(arquivos_do_release())
    if not any(a.name == "main.py" and a.parent == PROJETO for a in arquivos):
        sys.exit("main.py não encontrado na raiz do projeto")

    info = {
        "version": versao,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "files": len(arquivos),
    }
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("release.json", json.dumps(info, indent=2))
        for arq in arquivos:
            zf.write(arq, arq.relative_to(PROJETO).as_posix())
    return destino


def sistema_padrao() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".mainerp")
    return Path(base) / "MainERP" / "sistema"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--saida",
        type=Path,
        default=PROJETO / "dist",
        help="pasta de saída (padrão: dist)",
    )
    ap.add_argument(
        "--instalar",
        action="store_true",
        help="copia o zip para a pasta atualizacoes\\ do sistema instalado",
    )
    ap.add_argument(
        "--sistema",
        type=Path,
        default=None,
        help="pasta 'sistema' da instalação (padrão: %%LOCALAPPDATA%%\\MainERP\\sistema)",
    )
    args = ap.parse_args()

    zip_path = construir_zip(args.saida)
    sha = sha256_arquivo(zip_path)
    versao = ler_versao()

    manifesto = {"version": versao, "url": zip_path.name, "sha256": sha}
    (args.saida / "version.json").write_text(
        json.dumps(manifesto, indent=2), encoding="utf-8"
    )

    print(
        f"Release {versao} criado: {zip_path}  ({zip_path.stat().st_size / 1024:.0f} KB)"
    )
    print(f"SHA256: {sha}")
    print(f"Manifesto: {args.saida / 'version.json'}")

    if args.instalar:
        pasta = (args.sistema or sistema_padrao()) / "atualizacoes"
        pasta.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zip_path, pasta / zip_path.name)
        print(f"\nCopiado para {pasta}")
        print("A atualização será aplicada na próxima vez que o MainERP for aberto.")


if __name__ == "__main__":
    main()
