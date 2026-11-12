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
#
# Durante atualizações, uma janela mínima (símbolo Pluma, barra de progresso e a
# palavra "Atualizando") mostra o andamento real: bytes baixados, arquivos extraídos
# e pacotes processados pelo pip. Ela usa só tkinter e nunca bloqueia a atualização.

import base64
import contextlib
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
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
UPDATE_MANIFEST_URL = (
    "https://github.com/otavioxx/main-erp/releases/latest/download/version.json"
)
CHAVE_PUBLICA_ED25519_B64 = "H9gLoB9JOf7ca1NHIfbGeuCOh71sG/h5CjhoivGz8KA="

EXIT_REINICIAR = 100  # o sistema pediu reinício
CODIGOS_NORMAIS = {0, 3, 4}  # 4 = restauração falhou; não abrir versão anterior
MANTER_RELEASES = 3
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
TEMPO_MAXIMO_PIP = 1800  # segundos

# Janela de atualização. O launcher usa só a biblioteca padrão e não importa o
# aplicativo, então as cores do tema claro (padrão de instalações novas) ficam aqui,
# copiadas de CLARO em mainerp/ui/theme_tokens.py: surface, border, accent_text e
# text_secondary. Se esses tokens mudarem, atualize estas constantes.
JANELA_LARGURA = 320
JANELA_ALTURA = 180
COR_SUPERFICIE = "#FFFFFF"
COR_BORDA = "#C3CCD7"
COR_PREENCHIMENTO = "#1565A8"
COR_TEXTO = "#4B5A6A"
BARRA_LARGURA = 200
BARRA_ALTURA = 4

# Progresso (0 a 100) por etapa concluída da atualização. Download, extração e a
# coleta de pacotes do pip avançam conforme o trabalho realmente feito; os valores
# são as faixas de cada etapa, não uma estimativa de tempo.
PROGRESSO_DOWNLOAD_FIM = 30
PROGRESSO_VERIFICADO = 32
PROGRESSO_EXTRACAO_FIM = 42
PROGRESSO_AMBIENTE_FIM = 48
PROGRESSO_COLETA_FIM = 78
PROGRESSO_DEPENDENCIAS_FIM = 96
PROGRESSO_CONCLUIDO = 100

MENSAGEM_FALHA_DEPENDENCIAS = (
    "Não foi possível instalar as dependências da nova versão "
    "(verifique a conexão com a internet). Detalhes em logs\\launcher.log."
)

# Símbolo da Pluma (PNG com transparência, 47 x 49 px) para a janela de atualização.
SIMBOLO_PNG_B64 = (
    "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"
)


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
    """Janela de atualização: símbolo, barra de progresso reta e "Atualizando".

    Só aparece quando há algo demorado a fazer. Qualquer falha ao desenhá-la
    desativa a janela, sem interromper a atualização.
    """

    def __init__(self):
        self.root = None
        self.canvas = None
        self.falhou = False
        self.percentual = 0.0
        self._preenchimento = None
        self._simbolo = None

    def _criar(self):
        import tkinter as tk

        root = tk.Tk()
        root.title("MainERP")
        root.overrideredirect(True)  # sem barra de título; borda fina própria
        root.attributes("-topmost", True)
        root.configure(bg=COR_BORDA)
        x = (root.winfo_screenwidth() - JANELA_LARGURA) // 2
        y = (root.winfo_screenheight() - JANELA_ALTURA) // 2
        root.geometry(f"{JANELA_LARGURA}x{JANELA_ALTURA}+{x}+{y}")

        interno = tk.Frame(root, bg=COR_SUPERFICIE)
        interno.place(x=1, y=1, width=JANELA_LARGURA - 2, height=JANELA_ALTURA - 2)

        self._simbolo = tk.PhotoImage(data=SIMBOLO_PNG_B64)
        tk.Label(interno, image=self._simbolo, bg=COR_SUPERFICIE, bd=0).place(
            relx=0.5, y=34, anchor="n"
        )
        self.canvas = tk.Canvas(
            interno, width=BARRA_LARGURA, height=BARRA_ALTURA,
            bg=COR_BORDA, highlightthickness=0, bd=0,
        )
        self.canvas.place(relx=0.5, y=110, anchor="n")
        self._preenchimento = self.canvas.create_rectangle(
            0, 0, 0, BARRA_ALTURA, fill=COR_PREENCHIMENTO, outline=""
        )
        tk.Label(
            interno, text="Atualizando", font=("Segoe UI", 10),
            fg=COR_TEXTO, bg=COR_SUPERFICIE, bd=0,
        ).place(relx=0.5, y=124, anchor="n")
        self.root = root

    def _desativar(self):
        self.falhou = True
        self.fechar()

    def mostrar(self, texto):
        """Exibe a janela. O texto detalhado vai só para o log; a janela é mínima."""
        log(f"[atualização] {' '.join(str(texto).split())}")
        if self.falhou:
            return
        try:
            if self.root is None:
                self._criar()
            self.root.update()
        except Exception:
            self._desativar()

    def progresso(self, percentual):
        """Atualiza a barra (0 a 100). Ela nunca retrocede dentro de uma instalação."""
        if self.root is None or self.falhou:
            return
        try:
            self.percentual = max(self.percentual, min(100.0, float(percentual)))
            largura = round(BARRA_LARGURA * self.percentual / 100)
            self.canvas.coords(self._preenchimento, 0, 0, largura, BARRA_ALTURA)
            self.root.update()
        except Exception:
            self._desativar()

    def reiniciar_progresso(self):
        """Zera a barra, para o próximo pacote quando há mais de um a instalar."""
        self.percentual = 0.0
        self.progresso(0)

    def atualizar_janela(self):
        """Processa eventos da janela enquanto uma etapa longa não traz novidades."""
        if self.root is None or self.falhou:
            return
        try:
            self.root.update()
        except Exception:
            self._desativar()

    def fechar(self):
        try:
            if self.root is not None:
                self.root.destroy()
        except Exception:
            pass
        self.root = None


# Janela ativa durante atualizar(); None fora dela. Fica em variável do módulo para
# que download, extração e pip informem o progresso sem mudar suas assinaturas.
_aviso_progresso = None


def progresso_ativo():
    aviso = _aviso_progresso
    return aviso is not None and getattr(aviso, "root", None) is not None


def informar_progresso(percentual):
    """Informa o andamento real (0 a 100) à janela de atualização, se houver."""
    aviso = _aviso_progresso
    if aviso is None:
        return
    try:
        aviso.progresso(percentual)
    except Exception:
        pass


def reiniciar_progresso():
    aviso = _aviso_progresso
    if aviso is None:
        return
    try:
        aviso.reiniciar_progresso()
    except Exception:
        pass


def manter_janela_ativa():
    aviso = _aviso_progresso
    if aviso is None:
        return
    try:
        aviso.atualizar_janela()
    except Exception:
        pass


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


def python_da_release(versao):
    pasta = RELEASES / versao
    if not (pasta / ".runtime-isolado").exists():
        return python_runtime()
    runtime = ROOT / "runtimes" / versao
    python = runtime / ("Scripts/pythonw.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise RuntimeError(f"Runtime isolado da versão {versao} não encontrado: {python}")
    return str(python)


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
            pasta_release = RELEASES / v
            shutil.rmtree(pasta_release)
            runtime = ROOT / "runtimes" / v
            if runtime.exists():
                shutil.rmtree(runtime)
    if RELEASES.is_dir():
        for p in RELEASES.glob(".tmp-*"):
            shutil.rmtree(p, ignore_errors=True)


# ----------------------------------------------------------------------
# Instalação de pacotes de release (.zip gerado por criar_release.py)
# ----------------------------------------------------------------------

def ler_versao_do_zip(zf):
    info = json.loads(zf.read("release.json").decode("utf-8"))
    versao = str(info["version"])
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,2}", versao):
        raise ValueError(f"versão inválida no pacote: {versao!r}")
    return versao


def extrair_seguro(zf, destino):
    base = destino.resolve()
    for membro in zf.infolist():
        alvo = (destino / membro.filename).resolve()
        if alvo != base and base not in alvo.parents:
            raise ValueError(f"pacote com caminho inválido: {membro.filename}")
    if not progresso_ativo():
        zf.extractall(destino)
        return
    membros = zf.infolist()
    faixa = PROGRESSO_EXTRACAO_FIM - PROGRESSO_VERIFICADO
    for i, membro in enumerate(membros, 1):
        zf.extract(membro, destino)
        informar_progresso(PROGRESSO_VERIFICADO + faixa * i / len(membros))


def garantir_dependencias(pasta_release, versao=None):
    """Instala atualizações em runtime isolado, preservando versões anteriores."""
    req = pasta_release / "requirements.txt"
    if not req.is_file():
        raise RuntimeError("Pacote sem requirements.txt; instalação recusada.")
    if CURRENT.exists():
        versao_atual = CURRENT.read_text(encoding="utf-8").strip()
        if versao_atual not in releases_validas() or versao is None:
            raise RuntimeError("Versão ativa inválida; instalação recusada.")
        runtime = ROOT / "runtimes" / versao
        if runtime.exists():
            shutil.rmtree(runtime)
        runtime.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [python_console(), "-m", "venv", str(runtime)],
                check=True, capture_output=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, timeout=300,
            )
            informar_progresso(PROGRESSO_AMBIENTE_FIM)
            python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            instalar_dependencias(str(python), req)
            (pasta_release / ".runtime-isolado").write_text("1", encoding="ascii")
        except Exception:
            if runtime.exists():
                shutil.rmtree(runtime)
            raise
        return
    atual = sha256_arquivo(req)
    if HASH_REQUISITOS.exists() and HASH_REQUISITOS.read_text(encoding="utf-8").strip() == atual:
        return
    instalar_dependencias(python_console(), req)
    HASH_REQUISITOS.write_text(atual, encoding="utf-8")


def contar_requisitos(req):
    """Quantidade de pacotes diretos em requirements.txt (base da estimativa do pip)."""
    total = 0
    for linha in req.read_text(encoding="utf-8", errors="replace").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if linha and not linha.startswith("-"):
            total += 1
    return max(total, 1)


def instalar_dependencias_com_progresso(python, req):
    """Roda o pip lendo a saída linha a linha para informar o andamento.

    O pip anuncia cada pacote ao coletá-lo ("Collecting ..."), mas só confirma a
    instalação no fim ("Successfully installed ..."). Por isso a barra avança a cada
    pacote coletado (o total real só é conhecido depois) e conclui ao final.
    """
    comando = [python, "-m", "pip", "install", "-r", str(req),
               "--disable-pip-version-check", "--no-input"]
    previstos = contar_requisitos(req)
    processo = subprocess.Popen(
        comando, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, encoding="utf-8", errors="replace",
        creationflags=NO_WINDOW,
    )
    fila = queue.Queue()

    def ler_saida():
        try:
            for linha in processo.stdout:
                fila.put(linha)
        finally:
            fila.put(None)

    threading.Thread(target=ler_saida, daemon=True).start()
    inicio = time.time()
    saida = []
    coletados = 0
    faixa = PROGRESSO_COLETA_FIM - PROGRESSO_AMBIENTE_FIM
    try:
        while True:
            if time.time() - inicio > TEMPO_MAXIMO_PIP:
                raise subprocess.TimeoutExpired(comando, TEMPO_MAXIMO_PIP)
            try:
                linha = fila.get(timeout=0.2)
            except queue.Empty:
                manter_janela_ativa()
                continue
            if linha is None:
                break
            saida.append(linha)
            if linha.startswith("Collecting "):
                coletados += 1
                fracao = coletados / max(previstos, coletados + 1)
                informar_progresso(PROGRESSO_AMBIENTE_FIM + faixa * fracao)
            elif linha.startswith("Successfully installed"):
                informar_progresso(PROGRESSO_DEPENDENCIAS_FIM)
        codigo = processo.wait()
    finally:
        if processo.poll() is None:
            processo.kill()
            processo.wait()
    if codigo != 0:
        log("".join(saida)[-4000:])
        raise RuntimeError(MENSAGEM_FALHA_DEPENDENCIAS)
    informar_progresso(PROGRESSO_DEPENDENCIAS_FIM)


def instalar_dependencias(python, req):
    log("Instalando dependências (pip)...")
    if progresso_ativo():
        instalar_dependencias_com_progresso(python, req)
        return
    r = subprocess.run(
        [python, "-m", "pip", "install", "-r", str(req),
         "--disable-pip-version-check", "--no-input"],
        check=False, capture_output=True, encoding="utf-8", errors="replace",
        stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, timeout=1800,
    )
    if r.returncode != 0:
        log((r.stdout or "")[-2000:] + (r.stderr or "")[-2000:])
        raise RuntimeError(MENSAGEM_FALHA_DEPENDENCIAS)


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

        informar_progresso(PROGRESSO_VERIFICADO)
        RELEASES.mkdir(parents=True, exist_ok=True)
        tmp = RELEASES / f".tmp-{versao}-{os.getpid()}"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        instalada = False
        try:
            extrair_seguro(zf, tmp)
            garantir_dependencias(tmp, versao)
            os.replace(tmp, destino)
            instalada = True
            definir_atual(versao)
            informar_progresso(PROGRESSO_CONCLUIDO)
        except Exception:
            runtime_isolado = (tmp / ".runtime-isolado").exists() or (
                instalada and (destino / ".runtime-isolado").exists()
            )
            shutil.rmtree(tmp, ignore_errors=True)
            if instalada:
                shutil.rmtree(destino)
            if runtime_isolado:
                runtime = ROOT / "runtimes" / versao
                if runtime.exists():
                    shutil.rmtree(runtime)
            raise

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
        reiniciar_progresso()
        try:
            instalar_zip(z)
            mover_zip(z, "aplicadas")
        except Exception as e:
            mover_zip(z, "invalidas")
            mensagem("MainERP - atualização",
                     f"Não foi possível instalar {z.name}. O sistema continuará na "
                     f"versão atual.\n\n{e}")


# ----------------------------------------------------------------------
# Atualização automática (GitHub Releases por padrão; URL pode ser personalizada)
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


def copiar_com_progresso(resposta, arquivo):
    """Copia o download informando os bytes recebidos (quando o tamanho é conhecido)."""
    try:
        total = int(resposta.headers.get("Content-Length") or 0)
    except (AttributeError, TypeError, ValueError):
        total = 0
    lido = 0
    while True:
        bloco = resposta.read(64 * 1024)
        if not bloco:
            break
        arquivo.write(bloco)
        lido += len(bloco)
        if total > 0:
            informar_progresso(PROGRESSO_DOWNLOAD_FIM * min(lido, total) / total)


def baixar(origem, destino):
    parcial = destino.with_suffix(destino.suffix + ".part")
    if _eh_http(origem):
        with urllib.request.urlopen(origem, timeout=30) as r, open(parcial, "wb") as f:
            if progresso_ativo():
                copiar_com_progresso(r, f)
            else:
                shutil.copyfileobj(r, f)
    else:
        shutil.copy2(origem, parcial)
    os.replace(parcial, destino)


def verificar_pacote_assinado(caminho, assinatura_path, sha256, versao):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(sha256)):
        raise ValueError("SHA256 inválido no manifesto")
    if sha256_arquivo(caminho).lower() != str(sha256).lower():
        raise ValueError("o SHA256 do pacote não confere; atualização recusada")

    with zipfile.ZipFile(caminho) as zf:
        versao_pacote = ler_versao_do_zip(zf)
    if versao_pacote != versao:
        raise ValueError(
            f"versão do manifesto ({versao}) não corresponde ao pacote "
            f"({versao_pacote})"
        )

    try:
        chave_publica = Ed25519PublicKey.from_public_bytes(
            base64.b64decode(CHAVE_PUBLICA_ED25519_B64, validate=True)
        )
        assinatura_texto = assinatura_path.read_text(encoding="ascii").strip()
        assinatura = base64.b64decode(assinatura_texto, validate=True)
        if len(assinatura) != 64:
            raise ValueError("assinatura Ed25519 inválida")
        chave_publica.verify(assinatura, caminho.read_bytes())
    except InvalidSignature as error:
        raise ValueError("assinatura Ed25519 inválida; atualização recusada") from error


def atualizar_online(aviso):
    try:
        cfg = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    except (OSError, ValueError):
        cfg = {}
    if not isinstance(cfg, dict):
        log("Configuração do launcher inválida; usando o manifesto padrão.")
        cfg = {}
    if cfg.get("disable_online_updates") is True:
        return
    origem = str(cfg.get("update_url") or UPDATE_MANIFEST_URL).strip()
    if not origem:
        return
    try:
        manifesto = ler_manifesto(origem)
        versao = str(manifesto["version"])
        if not re.fullmatch(r"[0-9A-Za-z._-]+", versao):
            raise ValueError(f"versão inválida no manifesto: {versao!r}")
        conhecidas = releases_conhecidas()
        if conhecidas and chave_versao(versao) <= chave_versao(conhecidas[-1]):
            return
        sha = manifesto["sha256"]  # obrigatório
        url_zip = resolver_url(origem, manifesto["url"])
        url_assinatura = f"{url_zip}.sig"
        aviso.mostrar(f"Baixando atualização {versao} do MainERP...\nAguarde.")
        ATUALIZACOES.mkdir(parents=True, exist_ok=True)
        zip_path = ATUALIZACOES / f"MainERP-{versao}.zip"
        assinatura_path = ATUALIZACOES / f"MainERP-{versao}.zip.sig"
        try:
            baixar(url_zip, zip_path)
            baixar(url_assinatura, assinatura_path)
            verificar_pacote_assinado(zip_path, assinatura_path, sha, versao)
            instalar_zip(zip_path, sha256=sha)
            mover_zip(zip_path, "aplicadas")
            mover_zip(assinatura_path, "aplicadas")
        except Exception as erro:
            if zip_path.exists():
                mover_zip(zip_path, "invalidas")
            if assinatura_path.exists():
                mover_zip(assinatura_path, "invalidas")
            mensagem(
                "MainERP - atualização",
                f"Não foi possível instalar a atualização {versao}. "
                f"A versão atual será mantida.\n\n{erro}",
            )
            raise
    except Exception as e:
        # sem rede ou servidor fora do ar é normal: segue com a versão instalada
        log(f"Atualização online ignorada: {e}")


@contextlib.contextmanager
def trava_atualizacao():
    """Usa trava liberada pelo sistema operacional mesmo após falha do processo."""
    if (ROOT / ".update.lock").exists():
        log("Trava de launcher antigo encontrada; atualização adiada.")
        yield False
        return
    with open(ROOT / ".update.lockfile", "a+b") as arquivo:
        arquivo.seek(0, os.SEEK_END)
        if arquivo.tell() == 0:
            arquivo.write(b"\0")
            arquivo.flush()
        arquivo.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            if os.name == "nt":
                arquivo.seek(0)
                msvcrt.locking(arquivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(arquivo.fileno(), fcntl.LOCK_UN)


def atualizar(aviso):
    global _aviso_progresso
    with trava_atualizacao() as obtida:
        if not obtida:
            return
        # Só janelas que informam progresso (a Aviso real) usam os caminhos com andamento.
        _aviso_progresso = aviso if hasattr(aviso, "progresso") else None
        try:
            aplicar_atualizacoes_locais(aviso)
            atualizar_online(aviso)
            limpar_releases()
        finally:
            _aviso_progresso = None
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
    env["MAINERP_RESTORE_PROTOCOL"] = "1"
    env["MAINERP_OK_FILE"] = str(pasta / ".ok")  # o sistema cria ao abrir a janela
    env["PYTHONIOENCODING"] = "utf-8:backslashreplace"  # prints com emoji no log

    inicio = time.time()
    with open(saida_log, "a", encoding="utf-8") as saida:
        saida.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} - iniciando {versao} =====\n")
        saida.flush()
        proc = subprocess.Popen(
            [python_da_release(versao), "main.py"], cwd=str(pasta), env=env,
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

        try:
            codigo, duracao = executar(versao)
        except (OSError, RuntimeError) as erro:
            log(f"Não foi possível iniciar a versão {versao}: {erro}")
            codigo, duracao = 1, 0
        log(f"Versão {versao} terminou com código {codigo} após {duracao:.0f}s.")

        if codigo == EXIT_REINICIAR:
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
