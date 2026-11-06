# launcher.pyw - ponto de entrada fixo do MainERP.
#
# O atalho aponta SEMPRE para este arquivo (via runtime\Scripts\pythonw.exe).
# Ele usa apenas a biblioteca padrão e raramente precisa mudar. A cada abertura:
#
#   1. aplica atualizações novas (zips em "atualizacoes\" e/ou servidor);
#   2. escolhe a release atual (releases\<versão>\) e abre o sistema;
#   3. se uma release nova falhar ANTES de abrir a janela principal, volta para a anterior
#      (o sistema avisa que abriu criando o arquivo indicado em MAINERP_OK_FILE);
#   4. reabre o sistema quando ele pede reinício (ex.: após restaurar backup).
#
# Os dados (banco, config, backups, relatórios) NÃO ficam aqui: ficam em
# %LOCALAPPDATA%\MainERP\dados e nenhuma atualização mexe neles.
#
# Parâmetro opcional: --somente-atualizar (aplica atualizações e não abre o sistema).

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RELEASES = ROOT / "releases"
ATUALIZACOES = ROOT / "atualizacoes"
LOGS = ROOT / "logs"
RUNTIME = ROOT / "runtime"
CURRENT = ROOT / "current.txt"
CONFIG = ROOT / "launcher.json"  # {"update_url": ""}
HASH_REQUISITOS = ROOT / ".requirements.sha256"

EXIT_REINICIAR = 100  # o sistema pediu reinício
CODIGOS_NORMAIS = {0, 3}  # 0 = saiu normal, 3 = já havia outra instância aberta
MANTER_RELEASES = 3
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------

def log(msg):
    linha = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        arq = LOGS / "launcher.log"
        if arq.exists() and arq.stat().st_size > 512 * 1024:
            arq.replace(LOGS / "launcher.log.1")
        with open(arq, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass
    if sys.stdout:
        try:
            print(linha)
        except Exception:
            pass


def mensagem(titulo, texto, erro=True):
    """Caixa de mensagem do Windows (pythonw não tem console)."""
    log(f"[{titulo}] {texto}")
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, texto, titulo, 0x10 if erro else 0x40)
    except Exception:
        pass


class Aviso:
    """Janelinha 'aguarde' mostrada só quando há algo demorado a fazer."""

    def __init__(self):
        self.root = None
        self.label = None
        self.falhou = False

    def mostrar(self, texto):
        if self.falhou:
            return
        try:
            if self.root is None:
                import tkinter as tk

                self.root = tk.Tk()
                self.root.title("MainERP")
                self.root.resizable(False, False)
                self.root.attributes("-topmost", True)
                self.label = tk.Label(self.root, padx=40, pady=30, font=("Segoe UI", 11))
                self.label.pack()
                self.root.eval("tk::PlaceWindow . center")
            self.label.config(text=texto)
            self.root.update()
        except Exception:
            self.falhou = True
            self.root = None

    def fechar(self):
        try:
            if self.root is not None:
                self.root.destroy()
        except Exception:
            pass
        self.root = None


def chave_versao(versao):
    return tuple(int(n) for n in re.findall(r"\d+", str(versao))) or (0,)


def sha256_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def python_runtime():
    """Python do ambiente do sistema (runtime\\); cai no atual se não existir."""
    candidatos = [RUNTIME / "Scripts" / "pythonw.exe", RUNTIME / "bin" / "python"]
    for c in candidatos:
        if c.exists():
            return str(c)
    return sys.executable


def python_console():
    c = RUNTIME / "Scripts" / "python.exe"
    return str(c) if c.exists() else python_runtime()


# ----------------------------------------------------------------------
# Releases
# ----------------------------------------------------------------------

def releases_conhecidas():
    """Todas as versões presentes em releases\\, inclusive as marcadas como ruins."""
    if not RELEASES.is_dir():
        return []
    return sorted(
        (p.name for p in RELEASES.iterdir() if p.is_dir() and not p.name.startswith(".")),
        key=chave_versao,
    )


def release_valida(versao):
    pasta = RELEASES / versao
    return (pasta / "main.py").is_file() and not (pasta / ".ruim").exists()


def releases_validas():
    return [v for v in releases_conhecidas() if release_valida(v)]


def definir_atual(versao):
    tmp = ROOT / "current.txt.tmp"
    tmp.write_text(versao, encoding="utf-8")
    os.replace(tmp, CURRENT)


def escolher_versao():
    validas = releases_validas()
    if not validas:
        # último recurso: se tudo foi marcado como ruim, reabilita a mais nova
        for v in reversed(releases_conhecidas()):
            ruim = RELEASES / v / ".ruim"
            if (RELEASES / v / "main.py").is_file() and ruim.exists():
                log(f"Nenhuma versão válida; reabilitando {v}.")
                ruim.unlink()
                validas = [v]
                break
    if not validas:
        return None
    atual = CURRENT.read_text(encoding="utf-8").strip() if CURRENT.exists() else ""
    if atual in validas:
        return atual
    definir_atual(validas[-1])
    return validas[-1]


def confirmada(versao):
    return (RELEASES / versao / ".ok").exists()


def marcar_ok(versao):
    try:
        (RELEASES / versao / ".ok").write_text(datetime.now().isoformat(), encoding="utf-8")
    except OSError:
        pass


def marcar_ruim_e_voltar(versao):
    """Desativa a release e devolve a melhor outra (ou None, sem desativar nada).

    Se não houver outra versão válida para onde voltar, a release NÃO é marcada:
    desativar a única versão deixaria o sistema inutilizável por um erro que pode
    ser passageiro (ex.: processo encerrado à força durante a abertura).
    """
    outras = [v for v in releases_validas() if v != versao]
    if not outras:
        return None
    try:
        (RELEASES / versao / ".ruim").write_text(
            f"Falhou ao iniciar em {datetime.now().isoformat()}", encoding="utf-8"
        )
    except OSError:
        pass
    definir_atual(outras[-1])
    return outras[-1]


def limpar_releases():
    """Mantém as últimas releases válidas (e a atual); apaga sobras temporárias."""
    validas = releases_validas()
    manter = set(validas[-MANTER_RELEASES:])
    if CURRENT.exists():
        manter.add(CURRENT.read_text(encoding="utf-8").strip())
    for v in validas:
        if v not in manter:
            shutil.rmtree(RELEASES / v, ignore_errors=True)
    if RELEASES.is_dir():
        for p in RELEASES.glob(".tmp-*"):
            shutil.rmtree(p, ignore_errors=True)


# ----------------------------------------------------------------------
# Instalação de pacotes de release (.zip gerado por criar_release.py)
# ----------------------------------------------------------------------

def ler_versao_do_zip(zf):
    info = json.loads(zf.read("release.json").decode("utf-8"))
    versao = str(info["version"])
    if not re.fullmatch(r"[0-9A-Za-z._-]+", versao):
        raise ValueError(f"versão inválida no pacote: {versao!r}")
    return versao


def extrair_seguro(zf, destino):
    base = destino.resolve()
    for membro in zf.infolist():
        alvo = (destino / membro.filename).resolve()
        if alvo != base and base not in alvo.parents:
            raise ValueError(f"pacote com caminho inválido: {membro.filename}")
    zf.extractall(destino)


def garantir_dependencias(pasta_release):
    """Roda pip só quando o requirements.txt mudou desde a última vez."""
    req = pasta_release / "requirements.txt"
    if not req.is_file():
        return
    atual = sha256_arquivo(req)
    if HASH_REQUISITOS.exists() and HASH_REQUISITOS.read_text(encoding="utf-8").strip() == atual:
        return
    log("Instalando dependências (pip)...")
    r = subprocess.run(
        [python_console(), "-m", "pip", "install", "-r", str(req),
         "--disable-pip-version-check", "--no-input"],
        capture_output=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, timeout=1800,
    )
    if r.returncode != 0:
        log((r.stdout or "")[-2000:] + (r.stderr or "")[-2000:])
        raise RuntimeError(
            "Não foi possível instalar as dependências da nova versão "
            "(verifique a conexão com a internet). Detalhes em logs\\launcher.log."
        )
    HASH_REQUISITOS.write_text(atual, encoding="utf-8")


def instalar_zip(caminho, sha256=None):
    """Instala um pacote em releases\\<versão>. Retorna a versão ou None se já existia."""
    if sha256 and sha256_arquivo(caminho).lower() != str(sha256).lower():
        raise ValueError("o SHA256 do pacote não confere; atualização recusada")

    with zipfile.ZipFile(caminho) as zf:
        if zf.testzip() is not None:
            raise ValueError("pacote corrompido")
        if "main.py" not in zf.namelist():
            raise ValueError("pacote sem main.py na raiz")
        versao = ler_versao_do_zip(zf)

        destino = RELEASES / versao
        if destino.exists():
            log(f"Versão {versao} já existe; ignorando pacote.")
            return None

        RELEASES.mkdir(parents=True, exist_ok=True)
        tmp = RELEASES / f".tmp-{versao}-{os.getpid()}"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        try:
            extrair_seguro(zf, tmp)
            garantir_dependencias(tmp)
            os.replace(tmp, destino)
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise

    definir_atual(versao)
    log(f"Versão {versao} instalada e definida como atual.")
    return versao


def mover_zip(zip_path, subpasta):
    destino = ATUALIZACOES / subpasta
    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / zip_path.name
    if alvo.exists():
        alvo = destino / f"{zip_path.stem}-{int(time.time())}{zip_path.suffix}"
    shutil.move(str(zip_path), str(alvo))


def aplicar_atualizacoes_locais(aviso):
    """Instala os .zip colocados em atualizacoes\\ (do mais antigo ao mais novo)."""
    if not ATUALIZACOES.is_dir():
        return
    pacotes = []
    for z in list(ATUALIZACOES.glob("*.zip")):
        try:
            with zipfile.ZipFile(z) as zf:
                pacotes.append((chave_versao(ler_versao_do_zip(zf)), z))
        except Exception as e:
            log(f"Pacote inválido {z.name}: {e}")
            mover_zip(z, "invalidas")
            mensagem("MainERP - atualização", f"O pacote {z.name} é inválido e foi ignorado.\n\n{e}")

    for chave, z in sorted(pacotes, key=lambda t: t[0]):
        conhecidas = releases_conhecidas()
        if conhecidas and chave <= chave_versao(conhecidas[-1]):
            log(f"{z.name}: versão não é mais nova que a instalada; arquivando.")
            mover_zip(z, "aplicadas")
            continue
        aviso.mostrar("Instalando atualização do MainERP...\nAguarde.")
        try:
            instalar_zip(z)
            mover_zip(z, "aplicadas")
        except Exception as e:
            mover_zip(z, "invalidas")
            mensagem("MainERP - atualização",
                     f"Não foi possível instalar {z.name}. O sistema continuará na "
                     f"versão atual.\n\n{e}")


# ----------------------------------------------------------------------
# Atualização automática (servidor ou pasta de rede) - opcional
#   launcher.json: {"update_url": "https://servidor/mainerp/version.json"}
#   version.json:  {"version": "0.07", "url": "MainERP-0.07.zip", "sha256": "..."}
# ----------------------------------------------------------------------

def _eh_http(origem):
    return re.match(r"https?://", origem, re.I) is not None


def ler_manifesto(origem):
    if _eh_http(origem):
        with urllib.request.urlopen(origem, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    caminho = Path(origem)
    if caminho.is_dir():
        caminho = caminho / "version.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def resolver_url(origem, url):
    if _eh_http(origem) or _eh_http(url):
        return urllib.parse.urljoin(origem, url)
    base = Path(origem)
    base = base if base.is_dir() else base.parent
    return str(base / url)


def baixar(origem, destino):
    parcial = destino.with_suffix(destino.suffix + ".part")
    if _eh_http(origem):
        with urllib.request.urlopen(origem, timeout=30) as r, open(parcial, "wb") as f:
            shutil.copyfileobj(r, f)
    else:
        shutil.copy2(origem, parcial)
    os.replace(parcial, destino)


def atualizar_online(aviso):
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    except (OSError, ValueError):
        cfg = {}
    origem = str(cfg.get("update_url") or "").strip()
    if not origem:
        return
    try:
        manifesto = ler_manifesto(origem)
        versao = str(manifesto["version"])
        conhecidas = releases_conhecidas()
        if conhecidas and chave_versao(versao) <= chave_versao(conhecidas[-1]):
            return
        sha = manifesto["sha256"]  # obrigatório
        aviso.mostrar(f"Baixando atualização {versao} do MainERP...\nAguarde.")
        ATUALIZACOES.mkdir(parents=True, exist_ok=True)
        zip_path = ATUALIZACOES / f"MainERP-{versao}.zip"
        baixar(resolver_url(origem, manifesto["url"]), zip_path)
        try:
            instalar_zip(zip_path, sha256=sha)
            mover_zip(zip_path, "aplicadas")
        except Exception:
            mover_zip(zip_path, "invalidas")
            raise
    except Exception as e:
        # sem rede ou servidor fora do ar é normal: segue com a versão instalada
        log(f"Atualização online ignorada: {e}")


@contextlib.contextmanager
def trava_atualizacao():
    """Evita dois launchers instalando ao mesmo tempo (clique duplo no atalho)."""
    pasta = ROOT / ".update.lock"
    obtida = False
    try:
        try:
            pasta.mkdir()
            obtida = True
        except FileExistsError:
            try:
                velha = time.time() - pasta.stat().st_mtime > 900
            except OSError:
                velha = False
            if velha:
                shutil.rmtree(pasta, ignore_errors=True)
                pasta.mkdir()
                obtida = True
        yield obtida
    finally:
        if obtida:
            shutil.rmtree(pasta, ignore_errors=True)


def atualizar(aviso):
    with trava_atualizacao() as obtida:
        if not obtida:
            return
        try:
            aplicar_atualizacoes_locais(aviso)
            atualizar_online(aviso)
            limpar_releases()
        finally:
            aviso.fechar()


# ----------------------------------------------------------------------
# Execução do sistema
# ----------------------------------------------------------------------

def executar(versao):
    """Abre o sistema e espera terminar. Retorna (código de saída, segundos)."""
    pasta = RELEASES / versao
    LOGS.mkdir(parents=True, exist_ok=True)
    saida_log = LOGS / "sistema.log"
    if saida_log.exists() and saida_log.stat().st_size > 2 * 1024 * 1024:
        saida_log.replace(LOGS / "sistema.log.1")

    env = dict(os.environ)
    env["MAINERP_LAUNCHER"] = "1"
    env["MAINERP_OK_FILE"] = str(pasta / ".ok")  # o sistema cria ao abrir a janela
    env["PYTHONIOENCODING"] = "utf-8:backslashreplace"  # prints com emoji no log

    inicio = time.time()
    with open(saida_log, "a", encoding="utf-8") as saida:
        saida.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} - iniciando {versao} =====\n")
        saida.flush()
        proc = subprocess.Popen(
            [python_runtime(), "main.py"], cwd=str(pasta), env=env,
            stdin=subprocess.DEVNULL, stdout=saida, stderr=saida,
        )
        codigo = proc.wait()
    if codigo == 0:
        marcar_ok(versao)
    return codigo, time.time() - inicio


def main(argv):
    somente_atualizar = "--somente-atualizar" in argv
    aviso = Aviso()
    try:
        atualizar(aviso)
    except Exception as e:
        log(f"Erro ao atualizar: {e}")
        aviso.fechar()

    if somente_atualizar:
        return 0

    quedas = 0
    while quedas < 3:
        versao = escolher_versao()
        if not versao:
            mensagem("MainERP",
                     "Nenhuma versão do sistema está instalada.\n"
                     "Execute o instalador novamente (distribuicao\\instalar.bat).")
            return 1

        codigo, duracao = executar(versao)
        log(f"Versão {versao} terminou com código {codigo} após {duracao:.0f}s.")

        if codigo == EXIT_REINICIAR:
            try:
                atualizar(aviso)  # aproveita o reinício para aplicar atualizações
            except Exception as e:
                log(f"Erro ao atualizar: {e}")
            continue

        if codigo in CODIGOS_NORMAIS:
            return codigo

        if not confirmada(versao):  # nunca chegou a abrir a janela principal
            quedas += 1
            anterior = marcar_ruim_e_voltar(versao)
            if anterior:
                mensagem("MainERP - atualização",
                         f"A versão {versao} falhou ao iniciar e foi desativada.\n"
                         f"O sistema vai abrir na versão {anterior}.\n\n"
                         f"Detalhes: {LOGS / 'sistema.log'}")
                continue
            mensagem("MainERP",
                     f"O sistema não conseguiu iniciar (código {codigo}).\n\n"
                     f"Detalhes: {LOGS / 'sistema.log'}")
            return codigo

        return codigo  # caiu depois de ter aberto: sem rollback automático
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
