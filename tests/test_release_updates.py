import base64
import hashlib
import importlib.machinery
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPDATE_MANIFEST_URL = (
    "https://github.com/otavioxx/main-erp/releases/latest/download/version.json"
)


def _carregar_modulo(caminho: Path, nome: str):
    loader = importlib.machinery.SourceFileLoader(nome, str(caminho))
    spec = importlib.util.spec_from_loader(nome, loader)
    if spec is None:
        raise ImportError(f"Não foi possível carregar {caminho}")
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


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


@pytest.mark.parametrize("versao", ["0.0.0", "0.10.0", "1.20.300"])
def test_release_accepts_canonical_stable_versions(criador, tmp_path, monkeypatch, versao):
    config = tmp_path / "mainerp" / "core" / "config.py"
    config.parent.mkdir(parents=True)
    config.write_text(f'APP_VERSION = "{versao}"\n', encoding="utf-8")
    monkeypatch.setattr(criador, "PROJETO", tmp_path)

    assert criador.ler_versao() == versao
    criador.verificar_tag(f"v{versao}")


@pytest.mark.parametrize(
    "versao",
    ["0.10", "0.01.0", "01.0.0", "1.0.00", "1.0.0-rc.1", "1.0.0+build",
     "1.0.0.1", "-1.0.0", "١.0.0", "1.0.0/extra"],
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
    monkeypatch.setattr(
        "sys.argv", ["criar_release.py", "--saida", str(output)]
    )
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
        launcher, "CHAVE_PUBLICA_ED25519_B64", base64.b64encode(public_key).decode("ascii")
    )
    monkeypatch.setattr(launcher, "garantir_dependencias", lambda pasta: None)

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
        launcher.verificar_pacote_assinado(
            package, signature, package_sha256, "0.09"
        )


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


def test_signature_verification_rejects_mismatched_package_version(
    launcher, tmp_path
):
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

    class AvisoFalso:
        def mostrar(self, texto):
            pass

    launcher.atualizar_online(AvisoFalso())

    assert installed == []
    assert archived == [("MainERP-0.09.zip", "invalidas")]


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
