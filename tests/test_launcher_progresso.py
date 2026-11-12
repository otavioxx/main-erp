import http.server
import importlib.machinery
import importlib.util
import sys
import threading
import zipfile
from pathlib import Path

import pytest

CAMINHO_LAUNCHER = Path(__file__).resolve().parents[1] / "distribuicao" / "launcher.pyw"


@pytest.fixture
def launcher(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("launcher_pyw",CAMINHO_LAUNCHER,)
    assert spec is not None
    assert spec.loader is not None
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "LOGS", tmp_path / "logs")
    return modulo


class JanelaFalsa:
    """Imita a janela de atualização registrando os percentuais recebidos."""

    def __init__(self):
        self.root = object()
        self.valores = []

    def progresso(self, percentual):
        self.valores.append(percentual)

    def reiniciar_progresso(self):
        self.valores.clear()

    def atualizar_janela(self):
        pass

    def mostrar(self, texto):
        pass

    def fechar(self):
        pass


def test_baixar_informa_bytes_recebidos(launcher, monkeypatch, tmp_path):
    conteudo = bytes(range(256)) * 1200  # ~300 KB
    origem_dir = tmp_path / "servidor"
    origem_dir.mkdir()
    (origem_dir / "pacote.bin").write_bytes(conteudo)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(origem_dir), **kwargs)

        def log_message(self, *args):
            pass

    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        janela = JanelaFalsa()
        monkeypatch.setattr(launcher, "_aviso_progresso", janela)
        destino = tmp_path / "baixado.bin"
        launcher.baixar(f"http://127.0.0.1:{servidor.server_port}/pacote.bin", destino)
    finally:
        servidor.shutdown()
        servidor.server_close()

    assert destino.read_bytes() == conteudo
    assert janela.valores == sorted(janela.valores)
    assert len(janela.valores) > 1
    assert 0 < janela.valores[0] < launcher.PROGRESSO_DOWNLOAD_FIM
    assert janela.valores[-1] == pytest.approx(launcher.PROGRESSO_DOWNLOAD_FIM)


def test_extrair_informa_arquivos_extraidos(launcher, monkeypatch, tmp_path):
    pacote = tmp_path / "pacote.zip"
    with zipfile.ZipFile(pacote, "w") as zf:
        for i in range(10):
            zf.writestr(f"pasta/arquivo{i}.txt", f"conteudo {i}")
    janela = JanelaFalsa()
    monkeypatch.setattr(launcher, "_aviso_progresso", janela)
    destino = tmp_path / "saida"
    destino.mkdir()
    with zipfile.ZipFile(pacote) as zf:
        launcher.extrair_seguro(zf, destino)

    assert (destino / "pasta" / "arquivo9.txt").read_text() == "conteudo 9"
    assert janela.valores == sorted(janela.valores)
    assert len(janela.valores) == 10
    assert janela.valores[-1] == pytest.approx(launcher.PROGRESSO_EXTRACAO_FIM)


def test_extrair_continua_recusando_caminho_inseguro(launcher, tmp_path):
    pacote = tmp_path / "ruim.zip"
    with zipfile.ZipFile(pacote, "w") as zf:
        zf.writestr("../fora.txt", "x")
    destino = tmp_path / "saida"
    destino.mkdir()
    with zipfile.ZipFile(pacote) as zf, pytest.raises(ValueError):
        launcher.extrair_seguro(zf, destino)
    assert not (tmp_path / "fora.txt").exists()


def _pip_falso(tmp_path, monkeypatch, linhas, codigo):
    pasta = tmp_path / "pip_falso" / "pip"
    pasta.mkdir(parents=True)
    (pasta / "__init__.py").write_text("")
    (pasta / "__main__.py").write_text(
        "import sys\n"
        f"for linha in {linhas!r}:\n"
        "    print(linha, flush=True)\n"
        f"sys.exit({codigo})\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "pip_falso"))
    requisitos = tmp_path / "requirements.txt"
    requisitos.write_text(
        "PyQt6\nreportlab # relatórios\n-r outro.txt\n\ncryptography\n"
    )
    return requisitos


def test_pip_informa_um_passo_por_pacote_coletado(launcher, monkeypatch, tmp_path):
    requisitos = _pip_falso(
        tmp_path,
        monkeypatch,
        [
            "Collecting PyQt6",
            "  Downloading PyQt6-6.0.whl (1 MB)",
            "Collecting reportlab",
            "Collecting cryptography",
            "Collecting cffi",
            "Installing collected packages: cffi, cryptography, reportlab, PyQt6",
            "Successfully installed PyQt6-6.0 reportlab-4 cryptography-1 cffi-1",
        ],
        0,
    )
    janela = JanelaFalsa()
    monkeypatch.setattr(launcher, "_aviso_progresso", janela)
    launcher.instalar_dependencias(sys.executable, requisitos)

    valores = janela.valores
    assert valores == sorted(valores)
    coleta = [v for v in valores if v < launcher.PROGRESSO_DEPENDENCIAS_FIM]
    assert len(coleta) == 4  # um valor por "Collecting"
    assert all(
        launcher.PROGRESSO_AMBIENTE_FIM < v < launcher.PROGRESSO_COLETA_FIM
        for v in coleta
    )
    assert valores[-1] == launcher.PROGRESSO_DEPENDENCIAS_FIM


def test_pip_com_falha_levanta_erro_e_registra_saida(launcher, monkeypatch, tmp_path):
    requisitos = _pip_falso(
        tmp_path, monkeypatch, ["Collecting PyQt6", "ERROR: sem rede"], 1
    )
    janela = JanelaFalsa()
    monkeypatch.setattr(launcher, "_aviso_progresso", janela)
    with pytest.raises(RuntimeError, match="dependências da nova versão"):
        launcher.instalar_dependencias(sys.executable, requisitos)
    assert "ERROR: sem rede" in (tmp_path / "logs" / "launcher.log").read_text(
        encoding="utf-8"
    )
    assert launcher.PROGRESSO_DEPENDENCIAS_FIM not in janela.valores


def test_pip_sem_janela_usa_o_caminho_original(launcher, monkeypatch, tmp_path):
    requisitos = tmp_path / "requirements.txt"
    requisitos.write_text("PyQt6\n")
    chamadas = []

    class Resultado:
        returncode = 0
        stdout = ""
        stderr = ""

    def run_falso(comando, **kwargs):
        chamadas.append(comando)
        return Resultado()

    def popen_proibido(*args, **kwargs):
        raise AssertionError("sem janela, o pip não deve usar Popen")

    monkeypatch.setattr(launcher, "_aviso_progresso", None)
    monkeypatch.setattr(launcher.subprocess, "run", run_falso)
    monkeypatch.setattr(launcher.subprocess, "Popen", popen_proibido)
    launcher.instalar_dependencias("python", requisitos)
    assert len(chamadas) == 1 and chamadas[0][1:3] == ["-m", "pip"]


def test_atualizar_registra_e_libera_a_janela(launcher, monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    janela = JanelaFalsa()
    vistos = []
    monkeypatch.setattr(
        launcher,
        "aplicar_atualizacoes_locais",
        lambda aviso: vistos.append(launcher._aviso_progresso),
    )
    monkeypatch.setattr(launcher, "atualizar_online", lambda aviso: None)
    monkeypatch.setattr(launcher, "limpar_releases", lambda: None)
    launcher.atualizar(janela)
    assert vistos == [janela]
    assert launcher._aviso_progresso is None


def test_atualizar_ignora_janela_sem_progresso(launcher, monkeypatch, tmp_path):
    class Antiga:
        def mostrar(self, texto):
            pass

        def fechar(self):
            pass

    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    vistos = []
    monkeypatch.setattr(
        launcher,
        "aplicar_atualizacoes_locais",
        lambda aviso: vistos.append(launcher._aviso_progresso),
    )
    monkeypatch.setattr(launcher, "atualizar_online", lambda aviso: None)
    monkeypatch.setattr(launcher, "limpar_releases", lambda: None)
    launcher.atualizar(Antiga())
    assert vistos == [None]


def test_janela_real_nao_retrocede_e_fecha(launcher):
    pytest.importorskip("tkinter")
    janela = launcher.Aviso()
    janela.mostrar("Instalando atualização do MainERP...\nAguarde.")
    if janela.root is None:
        pytest.skip("Sem ambiente gráfico para abrir a janela")
    try:
        janela.progresso(40)
        janela.progresso(25)
        assert janela.percentual == 40
        janela.progresso(250)
        assert janela.percentual == 100
        janela.reiniciar_progresso()
        assert janela.percentual == 0
    finally:
        janela.fechar()
    assert janela.root is None
