"""Instalador do MainERP (modelo sem PyInstaller).

Cria, em %LOCALAPPDATA%\\MainERP:
    sistema\\   runtime (Python + bibliotecas), launcher e releases do código
    dados\\     banco, config, backups e relatórios (nunca tocados por atualizações)

e os atalhos "MainERP" na Área de Trabalho e no Menu Iniciar. Pode ser executado
de novo quando quiser (reinstala o launcher e recria os atalhos, sem apagar dados).

Uso:  instalar.bat      (ou: python distribuicao/instalar.py [--destino PASTA])
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import venv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROJETO = AQUI.parent
sys.path.insert(0, str(AQUI))

import criar_release

UPDATE_MANIFEST_URL = (
    "https://github.com/otavioxx/main-erp/releases/latest/download/version.json"
)

ARQUIVOS_DESENVOLVIMENTO = (
    "CHANGELOG.md", "ROADMAP.md", "README.md", "verificar.bat",
    "requirements-dev.txt", "pyproject.toml", ".gitignore",
    ".github/workflows/release.yml",
    "tests/test_about_updates_dialog.py", "tests/test_automatic_backup.py",
    "tests/test_condicional_money.py", "tests/test_database_migrations.py",
    "tests/test_database_transactions.py", "tests/test_database_utils.py",
    "tests/test_dialog_inheritance.py", "tests/test_duplicata.py",
    "tests/test_instalador_pacote.py", "tests/test_listagem_tables.py",
    "tests/test_manual_backup.py", "tests/test_money.py", "tests/test_money_reports.py",
    "tests/test_outras_listagens.py", "tests/test_pedido_model.py",
    "tests/test_pedido_utils_money.py", "tests/test_produto_model.py",
    "tests/test_release_updates.py", "tests/test_restore_pending.py",
    "tests/test_restore_validation.py", "tests/test_table_items.py",
    "tests/test_venda_estoque.py", "tests/test_venda_model.py",
    "tests/test_venda_utils.py", "tests/test_view_data_models.py",
)


def base_padrao() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".mainerp")
    return Path(base) / "MainERP"


def python_do_runtime(runtime: Path, gui: bool = False) -> Path:
    if os.name == "nt":
        return runtime / "Scripts" / ("pythonw.exe" if gui else "python.exe")
    return runtime / "bin" / "python"


def configurar_launcher(config_path: Path) -> None:
    """Define o manifesto padrão sem sobrescrever uma URL já configurada."""
    if config_path.exists():
        configuracao = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(configuracao, dict):
            raise ValueError(f"Configuração inválida em {config_path}")
    else:
        configuracao = {}

    if configuracao.get("disable_online_updates") is not True:
        configuracao.setdefault("update_url", UPDATE_MANIFEST_URL)
        if not configuracao["update_url"]:
            configuracao["update_url"] = UPDATE_MANIFEST_URL

    config_path.write_text(
        json.dumps(configuracao, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def criar_atalhos(sistema: Path, launcher: Path, icone: Path):
    if os.name != "nt":
        print("(atalhos só são criados no Windows)")
        return
    alvo = python_do_runtime(sistema / "runtime", gui=True)
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(AQUI / "criar_atalhos.ps1"), "-Alvo", str(alvo),
         "-Launcher", str(launcher), "-Sistema", str(sistema), "-Icone", str(icone),
         "-AppId", "DigitalSolutions.MainERP"],
        check=True,
    )


def validar_versao_instalada(sistema: Path, versao_esperada: str) -> None:
    """Confirma que a versão ativa está íntegra e não é anterior ao instalador."""
    atual = (sistema / "current.txt").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", atual):
        raise ValueError(f"Versão ativa inválida: {atual!r}")
    if tuple(map(int, atual.split("."))) < tuple(map(int, versao_esperada.split("."))):
        raise ValueError(f"Versão ativa {atual} é anterior a {versao_esperada}")
    release = sistema / "releases" / atual
    if not (release / "main.py").is_file() or (release / ".ruim").exists():
        raise ValueError(f"Versão ativa {atual} não está disponível")
    if (release / ".runtime-isolado").exists():
        runtime = sistema / "runtimes" / atual
        if not python_do_runtime(runtime).is_file() or not python_do_runtime(runtime, gui=True).is_file():
            raise ValueError(f"Runtime da versão ativa {atual} não está disponível")


def limpar_arquivos_desenvolvimento(origem: Path, destino: Path) -> None:
    """Remove arquivos conhecidos do ZIP extraído, sem tocar em um checkout Git."""
    origem = origem.resolve()
    destino = destino.resolve()
    if origem == destino or origem in destino.parents or destino in origem.parents:
        print("Limpeza ignorada: a origem e o destino da instalação se sobrepõem.")
        return
    if any((pasta / ".git").exists() for pasta in (origem, *origem.parents)):
        print("Limpeza ignorada: a origem pertence a um repositório Git.")
        return

    removidos = []
    for nome in ARQUIVOS_DESENVOLVIMENTO:
        arquivo = origem / nome
        if any(parte.is_symlink() for parte in (arquivo, *arquivo.parents) if parte != origem):
            continue
        if arquivo.is_file():
            arquivo.unlink()
            removidos.append(nome)
    if removidos:
        print("Arquivos de desenvolvimento removidos da pasta de origem:")
        for nome in removidos:
            print(f"  {nome}")


def main():
    ap = argparse.ArgumentParser(description="Instala o MainERP sem PyInstaller.")
    ap.add_argument(
        "--destino",
        type=Path,
        default=base_padrao(),
        help="pasta base da instalação (padrão: %%LOCALAPPDATA%%\\MainERP)",
    )
    ap.add_argument(
        "--sem-atalhos",
        action="store_true",
        help="não criar atalhos (útil para testes em instalações isoladas)",
    )
    args = ap.parse_args()

    if sys.version_info < (3, 10):  # noqa: UP036 - mensagem amigável ao rodar em Python antigo
        sys.exit("É necessário Python 3.10 ou superior (recomendado 3.12).")

    base = args.destino
    sistema = base / "sistema"
    dados = base / "dados"
    runtime = sistema / "runtime"
    sistema.mkdir(parents=True, exist_ok=True)
    dados.mkdir(parents=True, exist_ok=True)
    (sistema / "atualizacoes").mkdir(exist_ok=True)

    print(f"Instalando em: {base}")

    # 1) ambiente Python isolado do sistema
    if not python_do_runtime(runtime).exists():
        print("Criando ambiente Python (runtime)...")
        venv.EnvBuilder(with_pip=True).create(runtime)
    else:
        print("Ambiente Python já existe; mantendo.")

    # 2) launcher, ícone e configuração do launcher
    launcher = sistema / "launcher.pyw"
    shutil.copy2(AQUI / "launcher.pyw", launcher)
    icone = sistema / "icon.ico"
    shutil.copy2(PROJETO / "icon.ico", icone)
    cfg = sistema / "launcher.json"
    configurar_launcher(cfg)

    # 3) release atual do código, entregue pelo mesmo caminho das atualizações
    print("Empacotando a versão atual do código...")
    criar_release.construir_zip(sistema / "atualizacoes")

    # 4) o launcher instala a release e as dependências (pip)
    print("Instalando a versão e as dependências (pode levar alguns minutos)...")
    r = subprocess.run(
        [str(python_do_runtime(runtime)), str(launcher), "--somente-atualizar"],
        check=False,
    )
    try:
        if r.returncode != 0:
            raise RuntimeError(f"Launcher retornou código {r.returncode}")
        validar_versao_instalada(sistema, criar_release.ler_versao())
    except (OSError, ValueError, RuntimeError) as erro:
        sys.exit(f"Falha na instalação: {erro}. Veja {sistema / 'logs' / 'launcher.log'}")

    # 5) atalhos
    if not args.sem_atalhos:
        criar_atalhos(sistema, launcher, icone)

    try:
        limpar_arquivos_desenvolvimento(PROJETO, base)
    except OSError as erro:
        print(f"Aviso: instalação concluída, mas a limpeza da origem falhou: {erro}")

    print("\nInstalação concluída.")
    print(f"  Dados (banco, backups, relatórios): {dados}")
    print(f"  Sistema (código e atualizações):    {sistema}")
    if not args.sem_atalhos:
        print(
            "Abra o MainERP pelo atalho. Na primeira abertura o banco estará vazio: "
            "restaure seu backup pela tela de Configurações."
        )


if __name__ == "__main__":
    main()
