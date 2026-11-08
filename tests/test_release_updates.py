import ast
import base64
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, cast

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPDATE_MANIFEST_URL = (
    "https://github.com/otavioxx/main-erp/releases/latest/download/version.json"
)


def _carregar_modulo(caminho: Path, nome: str):
    loader = importlib.machinery.SourceFileLoader(nome, str(caminho))
    spec = importlib.util.spec_from_file_location(
        nome, caminho, loader=cast(Any, loader)
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar {caminho}")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_carregar_pyw_sem_suporte_nativo_a_extensao(tmp_path, monkeypatch):
    caminho = tmp_path / "modulo.pyw"
    caminho.write_text("valor = 42\n", encoding="utf-8")
    extensoes = [ext for ext in importlib.machinery.SOURCE_SUFFIXES if ext != ".pyw"]
    monkeypatch.setattr(importlib.machinery, "SOURCE_SUFFIXES", extensoes)
    assert _carregar_modulo(caminho, "modulo_teste_pyw").valor == 42


@pytest.fixture
def launcher():
    return _carregar_modulo(
        PROJECT_ROOT / "distribuicao" / "launcher.pyw", "launcher_test"
    )


@pytest.fixture
def instalador():
    return _carregar_modulo(
        PROJECT_ROOT / "distribuicao" / "instalar.py", "instalador_test"
    )


@pytest.fixture
def criador():
    return _carregar_modulo(
        PROJECT_ROOT / "distribuicao" / "criar_release.py", "criador_test"
    )


def test_instalador_prepara_assinatura_no_runtime_principal(
    instalador, tmp_path, monkeypatch
):
    chamadas = []
    monkeypatch.setattr(
        instalador.subprocess,
        "run",
        lambda args, **kwargs: chamadas.append((args, kwargs)),
    )
    instalador.garantir_criptografia_launcher(tmp_path / "runtime")
    python = str(instalador.python_do_runtime(tmp_path / "runtime"))
    assert chamadas[0][0][:4] == [python, "-m", "pip", "install"]
    assert chamadas[0][0][4] == "cryptography>=44,<47"
    assert chamadas[1][0][0:2] == [python, "-c"]
    assert "Ed25519PublicKey" in chamadas[1][0][2]
    assert all(opcoes["check"] for _, opcoes in chamadas)


def test_instalador_nao_altera_launcher_se_preparo_de_assinatura_falhar(
    instalador, tmp_path, monkeypatch
):
    sistema = tmp_path / "sistema"
    python = instalador.python_do_runtime(sistema / "runtime")
    python.parent.mkdir(parents=True)
    python.touch()
    launcher = sistema / "launcher.pyw"
    launcher.write_text("launcher anterior", encoding="utf-8")
    dados = tmp_path / "dados"
    dados.mkdir()
    banco = dados / "erp.db"
    banco.write_bytes(b"banco anterior")
    monkeypatch.setattr("sys.argv", ["instalar.py", "--destino", str(tmp_path)])

    def falhar(_):
        raise subprocess.CalledProcessError(1, ["pip"])

    monkeypatch.setattr(instalador, "garantir_criptografia_launcher", falhar)
    with pytest.raises(SystemExit, match="Falha ao preparar"):
        instalador.main()
    assert launcher.read_text(encoding="utf-8") == "launcher anterior"
    assert banco.read_bytes() == b"banco anterior"


def test_installer_uses_same_windows_identity_as_application(instalador, monkeypatch):
    chamadas = []
    sistema = Path("sistema")
    launcher = Path("launcher.pyw")
    icone = Path("icon.ico")
    with monkeypatch.context() as contexto:
        contexto.setattr(instalador.os, "name", "nt")
        contexto.setattr(
            instalador.subprocess,
            "run",
            lambda args, **kwargs: chamadas.append((args, kwargs)),
        )
        instalador.criar_atalhos(sistema, launcher, icone)

    comando, opcoes = chamadas[0]
    app_id = comando[comando.index("-AppId") + 1]
    tree = ast.parse((PROJECT_ROOT / "mainerp" / "app.py").read_text(encoding="utf-8"))
    chamadas_appid = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "SetCurrentProcessExplicitAppUserModelID"
    ]
    assert len(chamadas_appid) == 1
    assert ast.literal_eval(chamadas_appid[0].args[0]) == app_id
    assert opcoes["check"] is True
    assert comando[comando.index("-File") + 1].endswith("criar_atalhos.ps1")


@pytest.mark.skipif(os.name != "nt", reason="Requer Windows Shell")
def test_windows_shortcut_has_identity_icon_and_launcher(tmp_path):
    pasta = tmp_path / "pasta com espaço e 'aspas'"
    pasta.mkdir()
    sistema = tmp_path / "sistema"
    sistema.mkdir()
    alvo = sistema / "pythonw.exe"
    launcher = sistema / "launcher.pyw"
    icone = sistema / "icon.ico"
    for arquivo in (alvo, launcher, icone):
        arquivo.touch()
    script = PROJECT_ROOT / "distribuicao" / "criar_atalhos.ps1"
    args = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-Alvo",
        str(alvo),
        "-Launcher",
        str(launcher),
        "-Sistema",
        str(sistema),
        "-Icone",
        str(icone),
        "-AppId",
        "DigitalSolutions.MainERP",
        "-Destinos",
        str(pasta),
    ]
    for _ in range(2):
        subprocess.run(args, check=True, capture_output=True, text=True)
    verificar = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "$p=$env:MAINERP_TEST_SHORTCUT; $w=New-Object -ComObject WScript.Shell;"
        "$l=$w.CreateShortcut($p); $s=New-Object -ComObject Shell.Application;"
        "$i=$s.NameSpace((Split-Path $p)).ParseName((Split-Path $p -Leaf));"
        "@{target=$l.TargetPath; arguments=$l.Arguments; icon=$l.IconLocation;"
        "directory=$l.WorkingDirectory; id=$i.ExtendedProperty('System.AppUserModel.ID')}"
        "| ConvertTo-Json -Compress"
    )
    for diretorio in (pasta, sistema):
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", verificar],
            check=True,
            capture_output=True,
            encoding="utf-8",
            env={**os.environ, "MAINERP_TEST_SHORTCUT": str(diretorio / "MainERP.lnk")},
        )
        propriedades = json.loads(resultado.stdout)
        assert propriedades["target"] == str(alvo)
        assert propriedades["arguments"] == f'"{launcher}"'
        assert propriedades["directory"] == str(sistema)
        assert propriedades["icon"].rsplit(",", 1)[0] == str(icone)
        assert propriedades["id"] == "DigitalSolutions.MainERP"


@pytest.mark.skipif(os.name != "nt", reason="Requer Windows Shell")
def test_windows_shortcut_failure_is_reported(tmp_path):
    script = PROJECT_ROOT / "distribuicao" / "criar_atalhos.ps1"
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Alvo",
            str(tmp_path / "pythonw.exe"),
            "-Launcher",
            str(tmp_path / "launcher.pyw"),
            "-Sistema",
            str(tmp_path),
            "-Icone",
            str(tmp_path / "icon.ico"),
            "-AppId",
            "DigitalSolutions.MainERP",
            "-Destinos",
            str(tmp_path / "inexistente"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


@pytest.mark.parametrize("atual", ["0.10.0", "0.10.1", "0.11.0", "1.0.0"])
def test_installer_accepts_active_expected_or_newer_release(
    instalador, tmp_path, atual
):
    (tmp_path / "current.txt").write_text(atual, encoding="utf-8")
    release = tmp_path / "releases" / atual
    release.mkdir(parents=True)
    (release / "main.py").touch()

    instalador.validar_versao_instalada(tmp_path, "0.10.0")


@pytest.mark.parametrize("atual", ["0.10", "0.9.9", "../x", "", "1.0.0/extra"])
def test_installer_rejects_older_or_invalid_active_release(instalador, tmp_path, atual):
    (tmp_path / "current.txt").write_text(atual, encoding="utf-8")
    with pytest.raises(ValueError):
        instalador.validar_versao_instalada(tmp_path, "0.10.0")


def test_installer_rejects_missing_or_bad_active_release(instalador, tmp_path):
    (tmp_path / "current.txt").write_text("0.10.0", encoding="utf-8")
    release = tmp_path / "releases" / "0.10.0"
    release.mkdir(parents=True)
    with pytest.raises(ValueError, match="não está disponível"):
        instalador.validar_versao_instalada(tmp_path, "0.10.0")
    (release / "main.py").touch()
    (release / ".ruim").touch()
    with pytest.raises(ValueError, match="não está disponível"):
        instalador.validar_versao_instalada(tmp_path, "0.10.0")
    (release / ".ruim").unlink()
    (release / ".runtime-isolado").touch()
    with pytest.raises(ValueError, match="Runtime"):
        instalador.validar_versao_instalada(tmp_path, "0.10.0")
    runtime = tmp_path / "runtimes" / "0.10.0"
    for gui in (False, True):
        executavel = instalador.python_do_runtime(runtime, gui=gui)
        executavel.parent.mkdir(parents=True, exist_ok=True)
        executavel.touch()
    instalador.validar_versao_instalada(tmp_path, "0.10.0")


@pytest.mark.parametrize(
    ("atual", "returncode", "sucesso"),
    [
        ("0.10", 0, False),
        ("0.10.0", 1, False),
        ("0.10.0", 0, True),
        ("0.11.0", 0, True),
    ],
)
def test_installer_main_checks_launcher_result_and_active_release(
    instalador, tmp_path, monkeypatch, atual, returncode, sucesso
):
    sistema = tmp_path / "sistema"
    python = instalador.python_do_runtime(sistema / "runtime")
    python.parent.mkdir(parents=True)
    python.touch()
    release = sistema / "releases" / atual
    release.mkdir(parents=True)
    (release / "main.py").touch()
    (sistema / "current.txt").write_text(atual, encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["instalar.py", "--destino", str(tmp_path)])
    monkeypatch.setattr(instalador.criar_release, "construir_zip", lambda _: None)
    monkeypatch.setattr(instalador.criar_release, "ler_versao", lambda: "0.10.0")
    monkeypatch.setattr(instalador, "garantir_criptografia_launcher", lambda _: None)
    monkeypatch.setattr(
        instalador.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode),
    )
    atalhos = []
    monkeypatch.setattr(instalador, "criar_atalhos", lambda *args: atalhos.append(args))

    if sucesso:
        instalador.main()
        assert len(atalhos) == 1
    else:
        with pytest.raises(SystemExit, match="Falha na instalação"):
            instalador.main()
        assert not atalhos


def test_installer_can_skip_shortcuts_for_isolated_install(
    instalador, tmp_path, monkeypatch
):
    sistema = tmp_path / "sistema"
    python = instalador.python_do_runtime(sistema / "runtime")
    python.parent.mkdir(parents=True)
    python.touch()
    release = sistema / "releases" / "0.10.0"
    release.mkdir(parents=True)
    (release / "main.py").touch()
    (sistema / "current.txt").write_text("0.10.0", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv", ["instalar.py", "--destino", str(tmp_path), "--sem-atalhos"]
    )
    monkeypatch.setattr(instalador.criar_release, "construir_zip", lambda _: None)
    monkeypatch.setattr(instalador.criar_release, "ler_versao", lambda: "0.10.0")
    monkeypatch.setattr(instalador, "garantir_criptografia_launcher", lambda _: None)
    monkeypatch.setattr(
        instalador.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
    )
    atalhos = []
    monkeypatch.setattr(instalador, "criar_atalhos", lambda *args: atalhos.append(args))
    instalador.main()
    assert not atalhos


@pytest.mark.parametrize("falha", [None, "launcher", "atalhos"])
def test_installer_cleans_source_only_after_success(
    instalador, tmp_path, monkeypatch, falha
):
    origem = tmp_path / "fonte"
    distribuicao = origem / "distribuicao"
    distribuicao.mkdir(parents=True)
    for nome in ("launcher.pyw",):
        (distribuicao / nome).write_text("launcher", encoding="utf-8")
    (origem / "icon.ico").write_bytes(b"icone")
    for nome in ("CHANGELOG.md", "ROADMAP.md", "verificar.bat", "tests/test_money.py"):
        arquivo = origem / nome
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text("origem", encoding="utf-8")
    (origem / "tests" / "outro.txt").write_text("preservado", encoding="utf-8")
    destino = tmp_path / "instalacao"
    sistema = destino / "sistema"
    python = instalador.python_do_runtime(sistema / "runtime")
    python.parent.mkdir(parents=True)
    python.touch()
    release = sistema / "releases" / "0.10.0"
    release.mkdir(parents=True)
    (release / "main.py").touch()
    (release / "CHANGELOG.md").write_text("historico", encoding="utf-8")
    (sistema / "current.txt").write_text("0.10.0", encoding="utf-8")
    dados = destino / "dados"
    dados.mkdir()
    (dados / "erp.db").write_text("dados", encoding="utf-8")
    monkeypatch.setattr(instalador, "PROJETO", origem)
    monkeypatch.setattr(instalador, "AQUI", distribuicao)
    monkeypatch.setattr("sys.argv", ["instalar.py", "--destino", str(destino)])
    monkeypatch.setattr(instalador.criar_release, "construir_zip", lambda _: None)
    monkeypatch.setattr(instalador.criar_release, "ler_versao", lambda: "0.10.0")
    monkeypatch.setattr(instalador, "garantir_criptografia_launcher", lambda _: None)
    monkeypatch.setattr(
        instalador.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args, int(falha == "launcher")
        ),
    )

    def atalhos(*args):
        if falha == "atalhos":
            raise OSError("Falha ao criar atalho")

    monkeypatch.setattr(instalador, "criar_atalhos", atalhos)
    if falha == "launcher":
        with pytest.raises(SystemExit):
            instalador.main()
    elif falha == "atalhos":
        with pytest.raises(OSError):
            instalador.main()
    else:
        instalador.main()
    for nome in ("CHANGELOG.md", "ROADMAP.md", "verificar.bat", "tests/test_money.py"):
        assert (origem / nome).exists() == (falha is not None)
    assert (origem / "tests" / "outro.txt").read_text(encoding="utf-8") == "preservado"
    assert (release / "CHANGELOG.md").read_text(encoding="utf-8") == "historico"
    assert (dados / "erp.db").read_text(encoding="utf-8") == "dados"


@pytest.mark.parametrize(
    "protecao", ["git", "git-pai", "destino-interno", "origem-interna"]
)
def test_source_cleanup_refuses_git_or_overlapping_paths(
    instalador, tmp_path, protecao
):
    origem = tmp_path / "origem"
    origem.mkdir()
    arquivo = origem / "ROADMAP.md"
    arquivo.write_text("preservado", encoding="utf-8")
    destino = tmp_path / "instalacao"
    if protecao == "git":
        (origem / ".git").mkdir()
    elif protecao == "git-pai":
        (tmp_path / ".git").mkdir()
    elif protecao == "destino-interno":
        destino = origem / "instalacao"
    else:
        destino = tmp_path
    instalador.limpar_arquivos_desenvolvimento(origem, destino)
    assert arquivo.read_text(encoding="utf-8") == "preservado"


def test_source_cleanup_does_not_follow_symlink(instalador, tmp_path):
    origem = tmp_path / "origem"
    origem.mkdir()
    externo = tmp_path / "exterior"
    externo.mkdir()
    (externo / "test_money.py").write_text("preservado", encoding="utf-8")
    try:
        (origem / "tests").symlink_to(externo, target_is_directory=True)
    except OSError:
        pytest.skip("Criação de links simbólicos indisponível")
    instalador.limpar_arquivos_desenvolvimento(origem, tmp_path / "instalacao")
    assert (externo / "test_money.py").read_text(encoding="utf-8") == "preservado"


@pytest.mark.parametrize("versao", ["0.0.0", "0.10.0", "1.20.300"])
def test_release_accepts_canonical_stable_versions(
    criador, tmp_path, monkeypatch, versao
):
    config = tmp_path / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text(f'APP_VERSION = "{versao}"\n', encoding="utf-8")
    monkeypatch.setattr(criador, "PROJETO", tmp_path)

    assert criador.ler_versao() == versao
    criador.verificar_tag(f"v{versao}")


@pytest.mark.parametrize(
    "versao",
    [
        "0.10",
        "0.01.0",
        "01.0.0",
        "1.0.00",
        "1.0.0-rc.1",
        "1.0.0+build",
        "1.0.0.1",
        "-1.0.0",
        "١.0.0",
        "1.0.0/extra",
    ],
)
def test_release_rejects_noncanonical_versions(criador, tmp_path, monkeypatch, versao):
    config = tmp_path / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text(f'APP_VERSION = "{versao}"\n', encoding="utf-8")
    monkeypatch.setattr(criador, "PROJETO", tmp_path)

    with pytest.raises(SystemExit, match="APP_VERSION inválida"):
        criador.construir_zip(tmp_path / "dist")
    with pytest.raises(SystemExit, match="APP_VERSION inválida"):
        criador.verificar_tag(f"v{versao}")


def test_release_rejects_tag_different_from_version(criador, tmp_path, monkeypatch):
    config = tmp_path / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text('APP_VERSION = "0.10.0"\n', encoding="utf-8")
    monkeypatch.setattr(criador, "PROJETO", tmp_path)

    for tag in ("0.10.0", "v0.10", "v0.10.1", "v00.10.0"):
        with pytest.raises(SystemExit, match="não corresponde"):
            criador.verificar_tag(tag)


def test_builds_current_project_with_consistent_version(criador, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["criar_release.py", "--saida", str(tmp_path)])
    criador.main()

    versao = criador.ler_versao()
    manifesto = json.loads((tmp_path / "version.json").read_text(encoding="utf-8"))
    package = tmp_path / f"MainERP-{versao}.zip"
    assert manifesto == {
        "version": versao,
        "url": package.name,
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
    }
    with zipfile.ZipFile(package) as archive:
        assert json.loads(archive.read("release.json"))["version"] == versao
        assert f'APP_VERSION = "{versao}"' in archive.read(
            "mainerp/core/config.py"
        ).decode("utf-8")
        assert "main.py" in archive.namelist()
        codigo = {
            caminho.relative_to(PROJECT_ROOT).as_posix()
            for caminho in (PROJECT_ROOT / "mainerp").rglob("*.py")
            if "__pycache__" not in caminho.parts
        }
        assert codigo <= set(archive.namelist())
        assert {
            f"mainerp/ui/icons/{nome}" for nome in criador.ICONES
        } <= set(archive.namelist())


def test_release_recusa_icone_ausente(criador, tmp_path, monkeypatch):
    projeto = tmp_path / "projeto"
    config = projeto / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text('APP_VERSION = "0.10.0"\n', encoding="utf-8")
    (projeto / "main.py").touch()
    ui = projeto / "mainerp" / "ui"
    ui.mkdir()
    (ui / "icones.py").touch()
    monkeypatch.setattr(criador, "PROJETO", projeto)
    with pytest.raises(FileNotFoundError, match="Ícone ou licença ausente"):
        criador.construir_zip(tmp_path / "saida")


def test_release_exclui_arquivos_locais_e_caches(criador, tmp_path, monkeypatch):
    projeto = tmp_path / "projeto"
    config = projeto / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text('APP_VERSION = "0.10.0"\n', encoding="utf-8")
    (projeto / "main.py").write_text("", encoding="utf-8")
    for nome in (
        ".pytest_cache/cache",
        ".ruff_cache/cache",
        "segredo.txt",
        "mainerp/core/erp.db-wal",
        "mainerp/core/config.json",
        "mainerp/core/__pycache__/config.pyc",
        "mainerp/venv/nao_incluir.py",
    ):
        caminho = projeto / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("local", encoding="utf-8")
    monkeypatch.setattr(criador, "PROJETO", projeto)

    package = criador.construir_zip(tmp_path / "saida")

    with zipfile.ZipFile(package) as archive:
        assert set(archive.namelist()) == {
            "release.json",
            "main.py",
            "mainerp/core/config.py",
        }


def test_signed_semver_update_from_legacy_release(
    launcher, criador, tmp_path, monkeypatch
):
    projeto = tmp_path / "projeto"
    config = projeto / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text('APP_VERSION = "0.10.0"\n', encoding="utf-8")
    (projeto / "main.py").write_text("print('MainERP')\n", encoding="utf-8")
    output = tmp_path / "publicado"
    monkeypatch.setattr(criador, "PROJETO", projeto)
    monkeypatch.setattr("sys.argv", ["criar_release.py", "--saida", str(output)])
    criador.main()

    package = output / "MainERP-0.10.0.zip"
    manifesto = json.loads((output / "version.json").read_text(encoding="utf-8"))
    assert manifesto == {
        "version": "0.10.0",
        "url": package.name,
        "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
    }
    with zipfile.ZipFile(package) as archive:
        assert json.loads(archive.read("release.json"))["version"] == "0.10.0"

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    package.with_suffix(".zip.sig").write_text(
        base64.b64encode(private_key.sign(package.read_bytes())).decode("ascii"),
        encoding="ascii",
    )

    sistema = tmp_path / "sistema"
    releases = sistema / "releases"
    anterior = releases / "0.10"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    config_launcher = sistema / "launcher.json"
    config_launcher.write_text(
        json.dumps({"update_url": str(output / "version.json")}), encoding="utf-8"
    )
    monkeypatch.setattr(launcher, "ROOT", sistema)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", sistema / "current.txt")
    monkeypatch.setattr(launcher, "CONFIG", config_launcher)
    monkeypatch.setattr(launcher, "ATUALIZACOES", sistema / "atualizacoes")
    monkeypatch.setattr(launcher, "LOGS", sistema / "logs")
    monkeypatch.setattr(
        launcher,
        "CHAVE_PUBLICA_ED25519_B64",
        base64.b64encode(public_key).decode("ascii"),
    )
    monkeypatch.setattr(launcher, "garantir_dependencias", lambda pasta, versao: None)

    class AvisoFalso:
        def mostrar(self, texto):
            pass

    assert launcher.chave_versao("0.10.0") > launcher.chave_versao("0.10")
    assert launcher.chave_versao("0.10.10") > launcher.chave_versao("0.10.9")
    launcher.atualizar_online(AvisoFalso())

    assert (sistema / "current.txt").read_text(encoding="utf-8") == "0.10.0"
    assert (releases / "0.10.0" / "main.py").is_file()
    assert (anterior / "main.py").is_file()
    assert (sistema / "atualizacoes" / "aplicadas" / package.name).is_file()
    assert (sistema / "atualizacoes" / "aplicadas" / f"{package.name}.sig").is_file()
    assert launcher.marcar_ruim_e_voltar("0.10.0") == "0.10"


def test_resolve_asset_relative_to_github_latest_manifest(launcher):
    assert (
        launcher.resolver_url(UPDATE_MANIFEST_URL, "MainERP-0.09.zip")
        == "https://github.com/otavioxx/main-erp/releases/latest/download/"
        "MainERP-0.09.zip"
    )


def test_launcher_nao_faz_rollback_quando_restauracao_falha(launcher, monkeypatch):
    monkeypatch.setattr(launcher, "atualizar", lambda aviso: None)
    monkeypatch.setattr(launcher, "escolher_versao", lambda: "0.10.0")
    monkeypatch.setattr(launcher, "executar", lambda versao: (4, 0))
    monkeypatch.setattr(
        launcher,
        "marcar_ruim_e_voltar",
        lambda versao: pytest.fail("Não deve abrir uma versão antiga"),
    )
    monkeypatch.setattr(launcher, "log", lambda mensagem: None)
    assert launcher.main([]) == 4


def test_launcher_informa_suporte_a_restauracao(launcher, tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "RELEASES", tmp_path / "releases")
    monkeypatch.setattr(launcher, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(launcher, "marcar_ok", lambda versao: None)
    ambientes = []

    class Processo:
        def wait(self):
            return 0

    def executar(*args, **kwargs):
        ambientes.append(kwargs["env"])
        return Processo()

    monkeypatch.setattr(launcher.subprocess, "Popen", executar)
    launcher.executar("0.10.0")
    assert ambientes[0]["MAINERP_RESTORE_PROTOCOL"] == "1"


def test_falha_dependencias_nao_altera_runtime_anterior(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    anterior = releases / "0.10.0"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    (anterior / "requirements.txt").write_text("pacote==1\n", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.10.0", encoding="utf-8")
    pacote = tmp_path / "atualizacao.zip"
    with zipfile.ZipFile(pacote, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.10.1"}))
        archive.writestr("main.py", "")
        archive.writestr("requirements.txt", "pacote==2\n")
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)
    monkeypatch.setattr(launcher, "ROOT", tmp_path)

    def falhar(*args, **kwargs):
        raise OSError("pip falhou")

    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        falhar,
    )

    with pytest.raises(OSError, match="pip falhou"):
        launcher.instalar_zip(pacote)
    assert current.read_text(encoding="utf-8") == "0.10.0"
    assert not (releases / "0.10.1").exists()
    assert (anterior / "requirements.txt").read_text(encoding="utf-8") == "pacote==1\n"


def test_falha_parcial_pip_remove_apenas_runtime_novo(launcher, tmp_path, monkeypatch):
    releases = tmp_path / "releases"
    anterior = releases / "0.10.0"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.10.0", encoding="utf-8")
    antigo = tmp_path / "runtime" / "dados"
    antigo.parent.mkdir()
    antigo.write_text("preservado", encoding="utf-8")
    pacote = tmp_path / "pacote.zip"
    with zipfile.ZipFile(pacote, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.10.1"}))
        archive.writestr("main.py", "")
        archive.writestr("requirements.txt", "pacote==2\n")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)

    def criar_runtime(args, **kwargs):
        pasta = Path(args[-1])
        pasta.mkdir(parents=True)
        (pasta / "parcial").write_text("parcial", encoding="utf-8")

    def falhar(*args):
        raise RuntimeError("instalação parcial")

    monkeypatch.setattr(launcher.subprocess, "run", criar_runtime)
    monkeypatch.setattr(launcher, "instalar_dependencias", falhar)
    with pytest.raises(RuntimeError, match="instalação parcial"):
        launcher.instalar_zip(pacote)
    assert not (tmp_path / "runtimes" / "0.10.1").exists()
    assert antigo.read_text(encoding="utf-8") == "preservado"
    assert current.read_text(encoding="utf-8") == "0.10.0"


def test_falha_ativacao_nao_deixa_release_ou_runtime_orfao(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    anterior = releases / "0.10.0"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.10.0", encoding="utf-8")
    pacote = tmp_path / "pacote.zip"
    with zipfile.ZipFile(pacote, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.10.1"}))
        archive.writestr("main.py", "")
        archive.writestr("requirements.txt", "")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)

    def preparar(pasta, versao):
        (tmp_path / "runtimes" / versao).mkdir(parents=True)
        (pasta / ".runtime-isolado").write_text("1", encoding="ascii")

    def falhar(versao):
        raise OSError("falha ao ativar")

    monkeypatch.setattr(launcher, "garantir_dependencias", preparar)
    monkeypatch.setattr(launcher, "definir_atual", falhar)
    with pytest.raises(OSError, match="falha ao ativar"):
        launcher.instalar_zip(pacote)
    assert not (releases / "0.10.1").exists()
    assert not (tmp_path / "runtimes" / "0.10.1").exists()
    assert current.read_text(encoding="utf-8") == "0.10.0"


def test_runtime_inexistente_causa_rollback(launcher, tmp_path, monkeypatch):
    releases = tmp_path / "releases"
    for version in ("1.0.0", "2.0.0"):
        pasta = releases / version
        pasta.mkdir(parents=True)
        (pasta / "main.py").write_text("", encoding="utf-8")
    (releases / "2.0.0" / ".runtime-isolado").write_text("1", encoding="ascii")
    current = tmp_path / "current.txt"
    current.write_text("2.0.0", encoding="utf-8")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)
    monkeypatch.setattr(launcher, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(launcher, "atualizar", lambda aviso: None)
    monkeypatch.setattr(launcher, "mensagem", lambda *args: None)

    def executar(version):
        if version == "2.0.0":
            launcher.python_da_release(version)
        return 0, 0

    monkeypatch.setattr(launcher, "executar", executar)
    assert launcher.main([]) == 0
    assert current.read_text(encoding="utf-8") == "1.0.0"


def test_atualizacao_usa_runtime_isolado(launcher, tmp_path, monkeypatch):
    releases = tmp_path / "releases"
    anterior = releases / "0.10.0"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    (anterior / "requirements.txt").write_text("pacote==1\n", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.10.0", encoding="utf-8")
    pacote = tmp_path / "atualizacao.zip"
    with zipfile.ZipFile(pacote, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.10.1"}))
        archive.writestr("main.py", "")
        archive.writestr("requirements.txt", "pacote==1\n")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)
    monkeypatch.setattr(launcher, "LOGS", tmp_path / "logs")

    def criar_runtime(args, **kwargs):
        Path(args[-1]).mkdir(parents=True)

    instalacoes = []
    monkeypatch.setattr(launcher.subprocess, "run", criar_runtime)
    monkeypatch.setattr(
        launcher,
        "instalar_dependencias",
        lambda python, req: instalacoes.append(
            (python, req.read_text(encoding="utf-8"))
        ),
    )

    assert launcher.instalar_zip(pacote) == "0.10.1"
    assert current.read_text(encoding="utf-8") == "0.10.1"
    assert (releases / "0.10.1" / ".runtime-isolado").exists()
    assert str(tmp_path / "runtimes" / "0.10.1") in instalacoes[0][0]
    assert instalacoes[0][1] == "pacote==1\n"


def test_atualizacao_online_mantem_versao_anterior_em_falha_de_dependencias(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    anterior = releases / "0.10.0"
    anterior.mkdir(parents=True)
    (anterior / "main.py").write_text("", encoding="utf-8")
    (anterior / "requirements.txt").write_text("pacote==1\n", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.10.0", encoding="utf-8")
    publicado = tmp_path / "publicado"
    publicado.mkdir()
    pacote = publicado / "MainERP-0.10.1.zip"
    with zipfile.ZipFile(pacote, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.10.1"}))
        archive.writestr("main.py", "")
        archive.writestr("requirements.txt", "pacote==2\n")
    chave = Ed25519PrivateKey.generate()
    publica = chave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    pacote.with_suffix(".zip.sig").write_text(
        base64.b64encode(chave.sign(pacote.read_bytes())).decode("ascii"),
        encoding="ascii",
    )
    manifesto = publicado / "version.json"
    manifesto.write_text(
        json.dumps(
            {
                "version": "0.10.1",
                "url": pacote.name,
                "sha256": hashlib.sha256(pacote.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "launcher.json"
    config.write_text(json.dumps({"update_url": str(manifesto)}), encoding="utf-8")
    avisos = []
    monkeypatch.setattr(launcher, "CONFIG", config)
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)
    monkeypatch.setattr(launcher, "ATUALIZACOES", tmp_path / "atualizacoes")
    monkeypatch.setattr(launcher, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(
        launcher, "CHAVE_PUBLICA_ED25519_B64", base64.b64encode(publica).decode()
    )
    monkeypatch.setattr(
        launcher, "mensagem", lambda titulo, texto: avisos.append(texto)
    )

    def falhar(*args, **kwargs):
        raise OSError("falha simulada")

    monkeypatch.setattr(launcher.subprocess, "run", falhar)

    class Aviso:
        def mostrar(self, texto):
            pass

    launcher.atualizar_online(Aviso())

    assert len(avisos) == 1
    assert "falha simulada" in avisos[0]
    assert current.read_text(encoding="utf-8") == "0.10.0"
    assert not (releases / "0.10.1").exists()


def test_runtime_por_release_com_dependencias_reais_e_rollback(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    legado = releases / "0.9.0"
    legado.mkdir(parents=True)
    (legado / "main.py").write_text("", encoding="utf-8")
    current = tmp_path / "current.txt"
    current.write_text("0.9.0", encoding="utf-8")
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "CURRENT", current)
    monkeypatch.setattr(launcher, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(launcher, "python_console", lambda: sys.executable)

    for version in ("1.0", "2.0"):
        wheel = tmp_path / f"mainerp_teste-{version}-py3-none-any.whl"
        dist = f"mainerp_teste-{version}.dist-info"
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("mainerp_teste.py", f"VERSION = '{version}'\n")
            archive.writestr(
                f"{dist}/METADATA",
                f"Metadata-Version: 2.1\nName: mainerp-teste\nVersion: {version}\n",
            )
            archive.writestr(
                f"{dist}/WHEEL",
                "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            )
            archive.writestr(
                f"{dist}/RECORD",
                f"mainerp_teste.py,,\n{dist}/METADATA,,\n{dist}/WHEEL,,\n"
                f"{dist}/RECORD,,\n",
            )
        pacote = tmp_path / f"release-{version}.zip"
        with zipfile.ZipFile(pacote, "w") as archive:
            archive.writestr("release.json", json.dumps({"version": f"{version}.0"}))
            archive.writestr("main.py", "")
            archive.writestr("requirements.txt", str(wheel))
        assert launcher.instalar_zip(pacote) == f"{version}.0"

    def versao_modulo(version):
        python = Path(launcher.python_da_release(version))
        if os.name == "nt":
            python = python.with_name("python.exe")
        resultado = subprocess.run(
            [str(python), "-c", "import mainerp_teste; print(mainerp_teste.VERSION)"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        return resultado.stdout.strip()

    assert versao_modulo("1.0.0") == "1.0"
    assert versao_modulo("2.0.0") == "2.0"
    assert launcher.marcar_ruim_e_voltar("2.0.0") == "1.0.0"
    assert current.read_text(encoding="utf-8") == "1.0.0"
    assert versao_modulo("1.0.0") == "1.0"


def test_trava_nao_expira_e_recupera_apos_saida(launcher, tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    script = """
import importlib.machinery, importlib.util, pathlib, sys
loader = importlib.machinery.SourceFileLoader('lock_test', sys.argv[1])
spec = importlib.util.spec_from_loader('lock_test', loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
module.ROOT = pathlib.Path(sys.argv[2])
with module.trava_atualizacao() as ok:
    print('obtida' if ok else 'ocupada')
"""
    cmd = [
        sys.executable,
        "-c",
        script,
        str(PROJECT_ROOT / "distribuicao" / "launcher.pyw"),
        str(tmp_path),
    ]
    with launcher.trava_atualizacao() as obtida:
        assert obtida
        antigo = (tmp_path / ".update.lockfile").stat().st_mtime - 7200
        os.utime(tmp_path / ".update.lockfile", (antigo, antigo))
        resultado = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=20
        )
        assert resultado.stdout.strip() == "ocupada"
    resultado = subprocess.run(
        cmd, capture_output=True, text=True, check=True, timeout=20
    )
    assert resultado.stdout.strip() == "obtida"


def test_trava_liberada_pelo_sistema_apos_saida_abrupta(
    launcher, tmp_path, monkeypatch
):
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    script = """
import importlib.machinery, importlib.util, os, pathlib, sys
loader = importlib.machinery.SourceFileLoader('lock_test', sys.argv[1])
spec = importlib.util.spec_from_loader('lock_test', loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
module.ROOT = pathlib.Path(sys.argv[2])
with module.trava_atualizacao() as ok:
    os._exit(73 if ok else 1)
"""
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(PROJECT_ROOT / "distribuicao" / "launcher.pyw"),
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert resultado.returncode == 73
    with launcher.trava_atualizacao() as obtida:
        assert obtida


def test_reinicio_nao_atualiza_antes_de_aplicar_restauracao(launcher, monkeypatch):
    atualizacoes = []
    resultados = iter([(100, 0), (0, 0)])
    monkeypatch.setattr(launcher, "atualizar", lambda aviso: atualizacoes.append(True))
    monkeypatch.setattr(launcher, "escolher_versao", lambda: "1.0.0")
    monkeypatch.setattr(launcher, "executar", lambda versao: next(resultados))
    monkeypatch.setattr(launcher, "log", lambda texto: None)
    assert launcher.main([]) == 0
    assert atualizacoes == [True]


def test_installer_configures_default_and_migrates_empty_update_url(
    instalador, tmp_path
):
    config_path = tmp_path / "new-install.json"
    instalador.configurar_launcher(config_path)
    assert json.loads(config_path.read_text(encoding="utf-8")) == {
        "update_url": UPDATE_MANIFEST_URL
    }

    config_path = tmp_path / "launcher.json"
    config_path.write_text('{"update_url": ""}', encoding="utf-8")

    instalador.configurar_launcher(config_path)

    configuracao = json.loads(config_path.read_text(encoding="utf-8"))
    assert configuracao["update_url"] == UPDATE_MANIFEST_URL


def test_installer_preserves_custom_url_and_explicit_opt_out(instalador, tmp_path):
    config_path = tmp_path / "custom.json"
    custom_url = "https://updates.example.test/version.json"
    config_path.write_text(json.dumps({"update_url": custom_url}), encoding="utf-8")

    instalador.configurar_launcher(config_path)

    configuracao = json.loads(config_path.read_text(encoding="utf-8"))
    assert configuracao["update_url"] == custom_url

    config_path.write_text(
        json.dumps({"disable_online_updates": True, "update_url": ""}),
        encoding="utf-8",
    )
    instalador.configurar_launcher(config_path)

    configuracao = json.loads(config_path.read_text(encoding="utf-8"))
    assert configuracao["disable_online_updates"] is True
    assert configuracao["update_url"] == ""


def test_online_update_uses_default_manifest_and_passes_manifest_hash(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    (releases / "0.08").mkdir(parents=True)
    config_path = tmp_path / "launcher.json"
    config_path.write_text("{}", encoding="utf-8")
    downloaded = []
    installed = []
    moved = []
    signature_checks = []
    package_bytes = b"release zip"
    package_sha256 = hashlib.sha256(package_bytes).hexdigest()

    def fake_download(url, destination):
        downloaded.append((url, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(package_bytes)

    def fake_install(path, sha256):
        installed.append((path, sha256))
        return "0.09"

    monkeypatch.setattr(launcher, "CONFIG", config_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "ATUALIZACOES", tmp_path / "atualizacoes")
    monkeypatch.setattr(
        launcher,
        "ler_manifesto",
        lambda origin: (
            {
                "version": "0.09",
                "url": "MainERP-0.09.zip",
                "sha256": package_sha256,
            }
            if origin == UPDATE_MANIFEST_URL
            else pytest.fail(f"Manifesto inesperado: {origin}")
        ),
    )
    monkeypatch.setattr(launcher, "baixar", fake_download)
    monkeypatch.setattr(
        launcher,
        "verificar_pacote_assinado",
        lambda path, signature_path, sha, version: signature_checks.append(
            (path, signature_path, sha, version)
        ),
    )
    monkeypatch.setattr(launcher, "instalar_zip", fake_install)
    monkeypatch.setattr(
        launcher, "mover_zip", lambda path, folder: moved.append(folder)
    )
    monkeypatch.setattr(launcher, "log", lambda message: None)

    class AvisoFalso:
        def mostrar(self, texto):
            pass

    launcher.atualizar_online(AvisoFalso())

    assert downloaded[0][0] == (
        "https://github.com/otavioxx/main-erp/releases/latest/download/MainERP-0.09.zip"
    )
    assert downloaded[1][0] == f"{downloaded[0][0]}.sig"
    assert installed[0][1] == package_sha256
    assert signature_checks[0][2:] == (package_sha256, "0.09")
    assert moved == ["aplicadas", "aplicadas"]


def test_signature_verification_rejects_modified_package(launcher, tmp_path):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    launcher.CHAVE_PUBLICA_ED25519_B64 = base64.b64encode(public_key).decode("ascii")

    package = tmp_path / "MainERP-0.09.zip"
    signature = tmp_path / "MainERP-0.09.zip.sig"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.09"}))
    signature.write_text(
        base64.b64encode(private_key.sign(package.read_bytes())).decode("ascii"),
        encoding="ascii",
    )
    package.write_bytes(package.read_bytes() + b"tampered")
    package_sha256 = hashlib.sha256(package.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="assinatura Ed25519 inválida"):
        launcher.verificar_pacote_assinado(package, signature, package_sha256, "0.09")


def test_signature_verification_accepts_valid_release(launcher, tmp_path):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    launcher.CHAVE_PUBLICA_ED25519_B64 = base64.b64encode(public_key).decode("ascii")

    package = tmp_path / "MainERP-0.09.zip"
    signature = tmp_path / "MainERP-0.09.zip.sig"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.09"}))
    signature.write_text(
        base64.b64encode(private_key.sign(package.read_bytes())).decode("ascii"),
        encoding="ascii",
    )

    launcher.verificar_pacote_assinado(
        package, signature, hashlib.sha256(package.read_bytes()).hexdigest(), "0.09"
    )


def test_signature_verification_rejects_mismatched_package_version(launcher, tmp_path):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    launcher.CHAVE_PUBLICA_ED25519_B64 = base64.b64encode(public_key).decode("ascii")

    package = tmp_path / "MainERP-0.08.zip"
    signature = tmp_path / "MainERP-0.08.zip.sig"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("release.json", json.dumps({"version": "0.08"}))
    signature.write_text(
        base64.b64encode(private_key.sign(package.read_bytes())).decode("ascii"),
        encoding="ascii",
    )

    with pytest.raises(ValueError, match="não corresponde ao pacote"):
        launcher.verificar_pacote_assinado(
            package, signature, hashlib.sha256(package.read_bytes()).hexdigest(), "0.09"
        )


def test_online_update_rejects_package_without_signature(
    launcher, tmp_path, monkeypatch
):
    releases = tmp_path / "releases"
    (releases / "0.08").mkdir(parents=True)
    config_path = tmp_path / "launcher.json"
    config_path.write_text("{}", encoding="utf-8")
    package_bytes = b"unsigned package"
    package_sha256 = hashlib.sha256(package_bytes).hexdigest()
    installed = []
    archived = []

    def fake_download(url, destination):
        if url.endswith(".sig"):
            raise FileNotFoundError("missing release signature")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(package_bytes)

    monkeypatch.setattr(launcher, "CONFIG", config_path)
    monkeypatch.setattr(launcher, "RELEASES", releases)
    monkeypatch.setattr(launcher, "ATUALIZACOES", tmp_path / "atualizacoes")
    monkeypatch.setattr(
        launcher,
        "ler_manifesto",
        lambda origin: {
            "version": "0.09",
            "url": "MainERP-0.09.zip",
            "sha256": package_sha256,
        },
    )
    monkeypatch.setattr(launcher, "baixar", fake_download)
    monkeypatch.setattr(
        launcher,
        "instalar_zip",
        lambda *args, **kwargs: installed.append(args),
    )
    monkeypatch.setattr(
        launcher,
        "mover_zip",
        lambda path, folder: archived.append((path.name, folder)),
    )
    monkeypatch.setattr(launcher, "log", lambda message: None)
    mensagens = []
    monkeypatch.setattr(
        launcher, "mensagem", lambda titulo, texto: mensagens.append(texto)
    )

    class AvisoFalso:
        def mostrar(self, texto):
            pass

    launcher.atualizar_online(AvisoFalso())

    assert installed == []
    assert archived == [("MainERP-0.09.zip", "invalidas")]
    assert len(mensagens) == 1


def test_online_update_can_be_disabled(launcher, tmp_path, monkeypatch):
    config_path = tmp_path / "launcher.json"
    config_path.write_text(
        json.dumps({"disable_online_updates": True}), encoding="utf-8"
    )
    monkeypatch.setattr(launcher, "CONFIG", config_path)
    monkeypatch.setattr(
        launcher,
        "ler_manifesto",
        lambda origin: pytest.fail("Não deveria consultar o manifesto"),
    )

    launcher.atualizar_online(None)
