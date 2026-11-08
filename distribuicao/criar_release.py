"""Gera o pacote de release do MainERP (um .zip com o código-fonte).

Uso (na pasta do projeto):
    python distribuicao/criar_release.py              # gera dist/MainERP-<versão>.zip
    python distribuicao/criar_release.py --instalar   # idem + coloca o zip em atualizacoes\\
                                                      # (aplicado na próxima abertura do sistema)

A versão estável MAJOR.MINOR.PATCH vem de APP_VERSION em mainerp/core/config.py.
Também é gerado dist/version.json (versão, nome do zip e SHA256), usado pelo launcher.
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

# A release contém apenas código Python da aplicação e os arquivos de runtime.
ARQUIVOS_RAIZ = ("main.py", "requirements.txt", "icon.ico", "CHANGELOG.md")
PACOTES = (
    "mainerp",
    "mainerp/core",
    "mainerp/data",
    "mainerp/data/models",
    "mainerp/domain",
    "mainerp/domain/utils",
    "mainerp/reports",
    "mainerp/ui",
    "mainerp/ui/dialogs",
    "mainerp/ui/mixins",
    "mainerp/ui/views",
)
ICONES = (
    "shopping-cart.svg", "clipboard-check.svg", "clipboard-list.svg", "wallet.svg",
    "users.svg", "package.svg", "truck.svg", "settings.svg", "info.svg",
    "hard-drive-download.svg", "folder-open.svg", "building-2.svg",
    "plus.svg", "pencil.svg", "trash-2.svg", "search.svg", "printer.svg",
    "rotate-ccw.svg", "circle-minus.svg", "circle-x.svg",
    "arrow-right-left.svg", "check.svg", "package-check.svg", "hand-coins.svg",
    "LICENSE-LUCIDE.txt", "LICENSE-FEATHER.txt",
)
VERSAO_ESTAVEL = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")


def ler_versao() -> str:
    arquivo_config = PROJETO / "mainerp" / "core" / "config.py"
    texto = arquivo_config.read_text(encoding="utf-8")
    m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', texto)
    if not m:
        sys.exit(f"APP_VERSION não encontrada em {arquivo_config.relative_to(PROJETO)}")
    versao = m.group(1)
    if not VERSAO_ESTAVEL.fullmatch(versao):
        sys.exit(
            f"APP_VERSION inválida: {versao!r}. Use MAJOR.MINOR.PATCH "
            "com números não negativos e sem zeros à esquerda."
        )
    return versao


def verificar_tag(tag: str) -> None:
    esperada = f"v{ler_versao()}"
    if tag != esperada:
        sys.exit(f"Tag {tag!r} não corresponde à versão {esperada!r}.")


def arquivos_do_release():
    for nome in ARQUIVOS_RAIZ:
        caminho = PROJETO / nome
        if caminho.is_file() and not caminho.is_symlink():
            yield caminho

    for pacote in PACOTES:
        pasta = PROJETO.joinpath(*pacote.split("/"))
        if not pasta.is_dir() or any(
            (PROJETO.joinpath(*Path(pacote).parts[:i])).is_symlink()
            for i in range(1, len(Path(pacote).parts) + 1)
        ):
            continue
        for caminho in sorted(pasta.glob("*.py")):
            if caminho.is_file() and not caminho.is_symlink():
                yield caminho
    if (PROJETO / "mainerp" / "ui" / "icones.py").is_file():
        pasta = PROJETO / "mainerp" / "ui" / "icons"
        for nome in ICONES:
            caminho = pasta / nome
            if any(p.is_symlink() for p in (caminho, pasta, pasta.parent, pasta.parent.parent)):
                raise ValueError(f"Link simbólico não permitido no ícone: {caminho}")
            if not caminho.is_file():
                raise FileNotFoundError(f"Ícone ou licença ausente: {caminho}")
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
    ap.add_argument(
        "--verificar-tag",
        metavar="TAG",
        help="valida a versão e a tag sem gerar o pacote",
    )
    args = ap.parse_args()

    if args.verificar_tag is not None:
        verificar_tag(args.verificar_tag)
        print(f"Tag {args.verificar_tag} válida.")
        return

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
