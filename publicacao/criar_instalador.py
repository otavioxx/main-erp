"""Gera um instalador Python autocontido que extrai apenas arquivos temporários."""

import sys
import zipfile
from pathlib import Path

# Permite executar este arquivo diretamente (python publicacao/criar_instalador.py): a
# raiz do projeto precisa estar no caminho de importação para localizar instalador/.
# criar_release.py fica em instalador/ porque o próprio instalador também o executa.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from instalador import criar_release

ARQUIVOS_INSTALADOR = (
    "instalar.py",
    "criar_release.py",
    "launcher.pyw",
    "criar_atalhos.ps1",
)


def construir_instalador(pasta_saida: Path) -> Path:
    projeto = criar_release.PROJETO
    versao = criar_release.ler_versao()
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = pasta_saida / f"MainERP-Instalador-{versao}.pyz"
    bootstrap = projeto / "publicacao" / "instalador_bootstrap.py"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as pacote:
        pacote.write(bootstrap, "__main__.py")
        for caminho in criar_release.arquivos_do_release():
            pacote.write(caminho, caminho.relative_to(projeto).as_posix())
        for nome in ARQUIVOS_INSTALADOR:
            caminho = projeto / "instalador" / nome
            if not caminho.is_file() or caminho.is_symlink():
                raise FileNotFoundError(f"Arquivo de instalação ausente: {caminho}")
            pacote.write(caminho, caminho.relative_to(projeto).as_posix())
    return destino


if __name__ == "__main__":
    caminho = construir_instalador(criar_release.PROJETO / "dist")
    print(f"Instalador criado: {caminho}")
