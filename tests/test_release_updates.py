import importlib.machinery
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPDATE_MANIFEST_URL = (
    "https://github.com/otavioxx/main-erp/releases/latest/download/version.json"
)


def _carregar_modulo(caminho: Path, nome: str):
    loader = importlib.machinery.SourceFileLoader(nome, str(caminho))
    spec = importlib.util.spec_from_file_location(nome, caminho)
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

    def fake_download(url, destination):
        downloaded.append((url, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"release zip")

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
            {"version": "0.09", "url": "MainERP-0.09.zip", "sha256": "expected-hash"}
            if origin == UPDATE_MANIFEST_URL
            else pytest.fail(f"Manifesto inesperado: {origin}")
        ),
    )
    monkeypatch.setattr(launcher, "baixar", fake_download)
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
    assert installed[0][1] == "expected-hash"
    assert moved == ["aplicadas"]


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
