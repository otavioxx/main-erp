#!/usr/bin/env python3
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
import shutil
import subprocess
import sys
import venv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROJETO = AQUI.parent
sys.path.insert(0, str(AQUI))

import criar_release


def base_padrao() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".mainerp")
    return Path(base) / "MainERP"


def python_do_runtime(runtime: Path, gui: bool = False) -> Path:
    if os.name == "nt":
        return runtime / "Scripts" / ("pythonw.exe" if gui else "python.exe")
    return runtime / "bin" / "python"


def ps_quote(texto: str) -> str:
    return "'" + str(texto).replace("'", "''") + "'"


def criar_atalhos(sistema: Path, launcher: Path, icone: Path):
    if os.name != "nt":
        print("(atalhos só são criados no Windows)")
        return
    alvo = python_do_runtime(sistema / "runtime", gui=True)
    script = f"""
$ErrorActionPreference = 'Stop'
$ws = New-Object -ComObject WScript.Shell
$destinos = @(
  [Environment]::GetFolderPath('Desktop'),
  [Environment]::GetFolderPath('Programs')
)
foreach ($pasta in $destinos) {{
  $lnk = $ws.CreateShortcut((Join-Path $pasta 'MainERP.lnk'))
  $lnk.TargetPath = {ps_quote(alvo)}
  $lnk.Arguments = {ps_quote('"' + str(launcher) + '"')}
  $lnk.WorkingDirectory = {ps_quote(sistema)}
  $lnk.IconLocation = {ps_quote(icone)}
  $lnk.Description = 'MainERP - Sistema de Gestão Empresarial'
  $lnk.Save()
  Write-Output ('Atalho criado: ' + $lnk.FullName)
}}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=True,
    )


def main():
    ap = argparse.ArgumentParser(description="Instala o MainERP sem PyInstaller.")
    ap.add_argument(
        "--destino",
        type=Path,
        default=base_padrao(),
        help="pasta base da instalação (padrão: %%LOCALAPPDATA%%\\MainERP)",
    )
    args = ap.parse_args()

    if sys.version_info < (3, 10):
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
    if not cfg.exists():
        cfg.write_text(json.dumps({"update_url": ""}, indent=2), encoding="utf-8")

    # 3) release atual do código, entregue pelo mesmo caminho das atualizações
    print("Empacotando a versão atual do código...")
    criar_release.construir_zip(sistema / "atualizacoes")

    # 4) o launcher instala a release e as dependências (pip)
    print("Instalando a versão e as dependências (pode levar alguns minutos)...")
    r = subprocess.run(
        [str(python_do_runtime(runtime)), str(launcher), "--somente-atualizar"]
    )
    if r.returncode != 0 or not (sistema / "current.txt").exists():
        sys.exit(f"Falha na instalação. Veja {sistema / 'logs' / 'launcher.log'}")

    # 5) atalhos
    criar_atalhos(sistema, launcher, icone)

    print("\nInstalação concluída.")
    print(f"  Dados (banco, backups, relatórios): {dados}")
    print(f"  Sistema (código e atualizações):    {sistema}")
    print(
        "Abra o MainERP pelo atalho. Na primeira abertura o banco estará vazio: "
        "restaure seu backup pela tela de Configurações."
    )


if __name__ == "__main__":
    main()
