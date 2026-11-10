import os
import sqlite3
import subprocess
import sys
import threading
import time
import zipfile

import pytest

from mainerp.data.database import Database
from mainerp.data.restore import (
    aplicar_restauracao_pendente,
    caminho_restauracao_pendente,
    preparar_restauracao,
)


def criar_banco(caminho, valor):
    database = Database(str(caminho))
    conn = database.get_connection()
    conn.execute("CREATE TABLE teste_restauracao (valor TEXT)")
    conn.execute("INSERT INTO teste_restauracao VALUES (?)", (valor,))
    conn.commit()
    database.close_connection()


def ler_valor(caminho):
    conn = sqlite3.connect(caminho)
    try:
        return conn.execute("SELECT valor FROM teste_restauracao").fetchone()[0]
    finally:
        conn.close()


@pytest.mark.parametrize("zipado", [False, True])
def test_restauracao_pendente_preserva_wal_e_backup_anterior(tmp_path, zipado):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("UPDATE teste_restauracao SET valor='atual em wal'")
    conn.commit()
    try:
        backup = origem
        if zipado:
            backup = tmp_path / "backup.zip"
            with zipfile.ZipFile(backup, "w") as zf:
                zf.write(origem, "erp.db")
        pendente = preparar_restauracao(backup, atual)
        assert ler_valor(atual) == "atual em wal"
        assert ler_valor(pendente) == "anterior"
    finally:
        conn.close()

    anterior = aplicar_restauracao_pendente(atual)
    assert anterior is not None
    assert ler_valor(anterior) == "atual em wal"
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()
    assert aplicar_restauracao_pendente(atual) is None


def test_backup_invalido_e_multiplos_bancos_nao_criam_pendencia(tmp_path):
    atual = tmp_path / "atual.db"
    criar_banco(atual, "atual")
    arquivo = tmp_path / "backup.zip"
    with zipfile.ZipFile(arquivo, "w") as zf:
        zf.write(atual, "primeiro.db")
        zf.write(atual, "segundo.db")
    with pytest.raises(ValueError, match="exatamente um"):
        preparar_restauracao(arquivo, atual)
    assert not caminho_restauracao_pendente(atual).exists()
    assert ler_valor(atual) == "atual"


def test_snapshot_anterior_falha_sem_aplicar_restauracao(tmp_path, monkeypatch):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)

    def falhar(*args):
        raise OSError("disco indisponível")

    monkeypatch.setattr("mainerp.data.restore.criar_snapshot_conexao", falhar)
    with pytest.raises(OSError, match="disco indisponível"):
        aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "atual"
    assert pendente.exists()
    assert not list((tmp_path / "backups").glob("*.db"))


def test_pendencia_existente_nao_e_substituida(tmp_path):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    with pytest.raises(FileExistsError):
        preparar_restauracao(origem, atual)
    assert ler_valor(pendente) == "anterior"


@pytest.mark.parametrize("etapa", ["fsync", "link"])
def test_falha_disco_na_preparacao_preserva_banco_e_nao_publica(
    tmp_path, monkeypatch, etapa
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")

    def falhar(*args, **kwargs):
        raise OSError("falha de disco simulada")

    monkeypatch.setattr(f"mainerp.data.restore.os.{etapa}", falhar)
    with pytest.raises(OSError, match="falha de disco simulada"):
        preparar_restauracao(origem, atual)
    assert ler_valor(atual) == "atual"
    assert ler_valor(origem) == "anterior"
    assert not caminho_restauracao_pendente(atual).exists()
    assert not list(tmp_path.glob("tmp*"))


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_falha_de_disco_durante_copia_preserva_pendencia_e_snapshot(
    tmp_path, monkeypatch, journal_mode
):
    import mainerp.data.restore as restore

    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(origem)
    conn.execute("CREATE TABLE dados_grandes (conteudo BLOB)")
    conn.executemany("INSERT INTO dados_grandes VALUES (zeroblob(8192))", [()] * 120)
    conn.commit()
    conn.close()
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    copiar = restore._copiar_banco

    def falhar_copia(origem, destino):
        def progresso(status, remaining, total):
            if remaining:
                raise OSError("falha de escrita simulada")
        copiar(origem, destino, progress=progresso)

    monkeypatch.setattr(restore, "_copiar_banco", falhar_copia)
    with pytest.raises(OSError, match="falha de escrita simulada"):
        aplicar_restauracao_pendente(atual)
    anterior, = (tmp_path / "backups").glob("pre_restore_*.db")
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "atual"
    assert ler_valor(pendente) == "anterior"
    monkeypatch.setattr(restore, "_copiar_banco", copiar)
    aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()


def test_processos_concorrentes_nao_substituem_pendencia(tmp_path):
    atual = tmp_path / "atual.db"
    origem1 = tmp_path / "origem1.db"
    origem2 = tmp_path / "origem2.db"
    criar_banco(atual, "atual")
    criar_banco(origem1, "primeiro")
    criar_banco(origem2, "segundo")
    codigo = """
import sys, time
from pathlib import Path
import mainerp.data.restore as r
origem, atual, pronta, outra = map(Path, sys.argv[1:])
original = r.DatabaseManager._verify_database
def sincronizar(caminho):
    valido = original(caminho)
    pronta.touch()
    limite = time.monotonic() + 20
    while not outra.exists():
        if time.monotonic() >= limite:
            raise TimeoutError("outro processo não chegou à barreira")
        time.sleep(0.01)
    return valido
r.DatabaseManager._verify_database = staticmethod(sincronizar)
try:
    r.preparar_restauracao(origem, atual)
    print("SUCESSO", flush=True)
except FileExistsError:
    print("PENDENCIA_EXISTENTE", flush=True)
"""
    pronto1 = tmp_path / "pronto1"
    pronto2 = tmp_path / "pronto2"
    processos = [
        subprocess.Popen(
            [sys.executable, "-c", codigo, str(origem), str(atual), str(pronto), str(outro)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for origem, pronto, outro in (
            (origem1, pronto1, pronto2), (origem2, pronto2, pronto1)
        )
    ]
    try:
        resultados = [proc.communicate(timeout=30) for proc in processos]
    finally:
        for proc in processos:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    assert all(proc.returncode == 0 for proc in processos), resultados
    assert sorted(stdout.strip() for stdout, _ in resultados) == [
        "PENDENCIA_EXISTENTE", "SUCESSO"
    ]
    assert ler_valor(caminho_restauracao_pendente(atual)) in ("primeiro", "segundo")
    assert ler_valor(atual) == "atual"


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
@pytest.mark.parametrize("momento", ["antes", "depois"])
def test_escrita_externa_e_bloqueada_entre_snapshot_e_copia(
    tmp_path, monkeypatch, journal_mode, momento
):
    import mainerp.data.restore as restore

    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.execute("UPDATE teste_restauracao SET valor='escrita antes da trava'")
    conn.commit()
    conn.close()
    preparar_restauracao(origem, atual)
    pedido = tmp_path / "escrever"
    confirmado = tmp_path / "confirmado"
    codigo = """
import sqlite3, sys, time
from pathlib import Path
banco, pedido, confirmado = map(Path, sys.argv[1:])
limite = time.monotonic() + 20
while not pedido.exists():
    if time.monotonic() >= limite: raise TimeoutError("pedido não recebido")
    time.sleep(0.01)
conn = sqlite3.connect(banco, timeout=0.2)
try:
    conn.execute("UPDATE teste_restauracao SET valor='escrita externa'")
    conn.commit()
    confirmado.write_text("gravou")
except sqlite3.OperationalError as erro:
    confirmado.write_text(str(erro))
finally:
    conn.close()
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", codigo, str(atual), str(pedido), str(confirmado)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    copiar = restore._copiar_banco

    def copiar_apos_escrita(origem, destino):
        if momento == "depois":
            copiar(origem, destino)
        pedido.touch()
        limite = time.monotonic() + 20
        while not confirmado.exists():
            if proc.poll() is not None or time.monotonic() >= limite:
                raise RuntimeError("Processo externo não confirmou escrita")
            time.sleep(0.01)
        assert "locked" in confirmado.read_text()
        if momento == "antes":
            copiar(origem, destino)

    monkeypatch.setattr(restore, "_copiar_banco", copiar_apos_escrita)
    try:
        anterior = aplicar_restauracao_pendente(atual)
        saida, erro = proc.communicate(timeout=10)
        assert proc.returncode == 0, (saida, erro)
        assert anterior is not None
        assert ler_valor(atual) == "anterior"
        assert ler_valor(anterior) == "escrita antes da trava"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_escritor_existente_impede_restauracao_sem_perda(tmp_path, monkeypatch, journal_mode):
    import mainerp.data.restore as restore

    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    ativo = tmp_path / "ativo"
    liberar = tmp_path / "liberar"
    codigo = """
import sqlite3, sys, time
from pathlib import Path
banco, ativo, liberar = map(Path, sys.argv[1:])
conn = sqlite3.connect(banco)
conn.execute("BEGIN IMMEDIATE")
conn.execute("UPDATE teste_restauracao SET valor='escritor ativo'")
ativo.touch()
limite = time.monotonic() + 20
while not liberar.exists():
    if time.monotonic() >= limite: raise TimeoutError("liberação não recebida")
    time.sleep(0.01)
conn.commit()
conn.close()
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", codigo, str(atual), str(ativo), str(liberar)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    conectar = sqlite3.connect

    def conectar_com_timeout(cur, *args, **kwargs):
        if cur == atual.resolve():
            kwargs["timeout"] = 0.2
        return conectar(cur, *args, **kwargs)

    try:
        limite = time.monotonic() + 20
        while not ativo.exists():
            if proc.poll() is not None or time.monotonic() >= limite:
                raise RuntimeError("Escritor externo não iniciou")
            time.sleep(0.01)
        monkeypatch.setattr(restore.sqlite3, "connect", conectar_com_timeout)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            aplicar_restauracao_pendente(atual)
        assert pendente.exists()
        assert not list((tmp_path / "backups").glob("pre_restore_*.db"))
        liberar.touch()
        saida, erro = proc.communicate(timeout=10)
        assert proc.returncode == 0, (saida, erro)
        assert ler_valor(atual) == "escritor ativo"
        anterior = aplicar_restauracao_pendente(atual)
        assert anterior is not None
        assert ler_valor(anterior) == "escritor ativo"
        assert ler_valor(atual) == "anterior"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_restauracao_reserva_escrita_antes_do_modo_exclusivo(
    tmp_path, monkeypatch, journal_mode
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    preparar_restauracao(origem, atual)
    comandos = []
    conectar = sqlite3.connect

    class ConexaoObservada(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            comandos.append(sql)
            return super().execute(sql, *args, **kwargs)

        def commit(self):
            comandos.append("COMMIT")
            return super().commit()

    def conectar_observando(caminho, *args, **kwargs):
        if caminho == atual.resolve():
            kwargs["factory"] = ConexaoObservada
        return conectar(caminho, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", conectar_observando)
    anterior = aplicar_restauracao_pendente(atual)

    assert comandos[:3] == ["BEGIN IMMEDIATE", "PRAGMA locking_mode=EXCLUSIVE", "COMMIT"]
    assert comandos[3].startswith("PRAGMA busy_timeout=")
    assert comandos[4] == "BEGIN EXCLUSIVE"
    assert anterior is not None
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "anterior"


def test_restauracao_repete_trava_exclusiva_apos_disputa(
    tmp_path, monkeypatch
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    conectar = sqlite3.connect
    reservado = threading.Event()
    liberar = threading.Event()
    encerrado = threading.Event()
    falhas = []

    def concorrer():
        try:
            concorrente = conectar(atual, timeout=5)
            try:
                concorrente.execute("BEGIN IMMEDIATE")
                reservado.set()
                if not liberar.wait(10):
                    raise TimeoutError("A restauração não tentou obter a trava")
                concorrente.commit()
            finally:
                concorrente.close()
        except Exception as erro:
            falhas.append(erro)
        finally:
            encerrado.set()

    class ConexaoObservada(sqlite3.Connection):
        def commit(self):
            super().commit()
            if trabalhador.ident is None:
                trabalhador.start()
                if not reservado.wait(10):
                    raise TimeoutError("O escritor concorrente não reservou a escrita")

        def execute(self, sql, *args, **kwargs):
            if sql == "BEGIN EXCLUSIVE" and trabalhador.is_alive():
                super().execute("PRAGMA busy_timeout=0")
                try:
                    return super().execute(sql, *args, **kwargs)
                finally:
                    super().execute("PRAGMA busy_timeout=30000")
                    liberar.set()
                    if not encerrado.wait(10):
                        raise TimeoutError("O escritor concorrente não encerrou")
            return super().execute(sql, *args, **kwargs)

    trabalhador = threading.Thread(target=concorrer)

    def conectar_observando(caminho, *args, **kwargs):
        if caminho == atual.resolve():
            kwargs["factory"] = ConexaoObservada
        return conectar(caminho, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", conectar_observando)
    try:
        anterior = aplicar_restauracao_pendente(atual)
    finally:
        liberar.set()
        if trabalhador.ident is not None:
            trabalhador.join(timeout=10)
    assert not trabalhador.is_alive()
    assert not falhas
    assert anterior is not None
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()


@pytest.mark.parametrize(
    ("mensagem", "codigo", "tempo"),
    [
        ("database is locked", 5, 31),
        ("database is locked", None, 31),
        ("database is locked", 6, 0),
        ("disk I/O error", 10, 0),
    ],
)
def test_falha_na_trava_exclusiva_nao_reinicia_indefinidamente(
    tmp_path, monkeypatch, mensagem, codigo, tempo
):
    import mainerp.data.restore as restore

    atual = tmp_path / "atual.db"
    criar_banco(atual, "atual")
    conectar = sqlite3.connect
    fechadas = []
    chamadas = []

    class ConexaoComFalha(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "BEGIN EXCLUSIVE":
                chamadas.append(sql)
                erro = sqlite3.OperationalError(mensagem)
                if codigo is not None:
                    erro.sqlite_errorcode = codigo
                raise erro
            return super().execute(sql, *args, **kwargs)

        def close(self):
            fechadas.append(True)
            super().close()

    def conectar_com_falha(caminho, *args, **kwargs):
        kwargs["factory"] = ConexaoComFalha
        return conectar(caminho, *args, **kwargs)

    instantes = iter((0, 0, 0, tempo))
    monkeypatch.setattr(restore.sqlite3, "connect", conectar_com_falha)
    monkeypatch.setattr(restore.time, "monotonic", lambda: next(instantes))
    with pytest.raises(sqlite3.OperationalError, match=mensagem):
        restore._conectar_com_trava_exclusiva(atual)
    assert len(chamadas) == 1
    assert fechadas == [True]


def test_trava_exclusiva_usa_apenas_tempo_restante(tmp_path, monkeypatch):
    import mainerp.data.restore as restore

    atual = tmp_path / "atual.db"
    criar_banco(atual, "atual")
    conectar = sqlite3.connect
    comandos = []

    class ConexaoObservada(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            comandos.append(sql)
            return super().execute(sql, *args, **kwargs)

    def conectar_observando(caminho, *args, **kwargs):
        kwargs["factory"] = ConexaoObservada
        return conectar(caminho, *args, **kwargs)

    instantes = iter((0, 0, 20))
    monkeypatch.setattr(restore.sqlite3, "connect", conectar_observando)
    monkeypatch.setattr(restore.time, "monotonic", lambda: next(instantes))
    conn = restore._conectar_com_trava_exclusiva(atual)
    conn.close()
    assert "PRAGMA busy_timeout=10000" in comandos


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_aplicacoes_concorrentes_nao_restauram_pendencia_duas_vezes(
    tmp_path, journal_mode
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    preparar_restauracao(origem, atual)
    codigo = """
import sys, time
from pathlib import Path
import mainerp.data.restore as r
atual, pronta, outra = map(Path, sys.argv[1:])
original = r.DatabaseManager._verify_database
def sincronizar(caminho):
    valido = original(caminho)
    if Path(caminho).name.endswith(".restauracao-pendente.db"):
        pronta.touch()
        limite = time.monotonic() + 20
        while not outra.exists():
            if time.monotonic() >= limite: raise TimeoutError("barreira")
            time.sleep(.01)
    return valido
r.DatabaseManager._verify_database = staticmethod(sincronizar)
print("APLICADA" if r.aplicar_restauracao_pendente(atual) else "JA_APLICADA")
"""
    pronto1, pronto2 = tmp_path / "pronto1", tmp_path / "pronto2"
    processos = [
        subprocess.Popen(
            [sys.executable, "-c", codigo, str(atual), str(pronto), str(outro)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for pronto, outro in ((pronto1, pronto2), (pronto2, pronto1))
    ]
    try:
        resultados = [proc.communicate(timeout=50) for proc in processos]
    finally:
        for proc in processos:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=10)
    assert all(proc.returncode == 0 for proc in processos), resultados
    assert sorted(stdout.strip() for stdout, _ in resultados) == ["APLICADA", "JA_APLICADA"]
    anterior, = (tmp_path / "backups").glob("pre_restore_*.db")
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "anterior"


def test_falha_ao_abrir_pendente_preserva_snapshot_e_banco(tmp_path, monkeypatch):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    conectar = sqlite3.connect
    leituras_pendentes = 0

    def falhar_ao_abrir(caminho, *args, **kwargs):
        nonlocal leituras_pendentes
        if isinstance(caminho, str) and caminho.startswith(pendente.as_uri()):
            leituras_pendentes += 1
            if leituras_pendentes == 2:
                raise sqlite3.OperationalError("falha simulada")
        return conectar(caminho, *args, **kwargs)

    monkeypatch.setattr("mainerp.data.restore.sqlite3.connect", falhar_ao_abrir)
    with pytest.raises(sqlite3.OperationalError, match="falha simulada"):
        aplicar_restauracao_pendente(atual)
    backups = list((tmp_path / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    assert ler_valor(atual) == "atual"
    assert pendente.exists()


def test_inicializacao_aplica_restauracao_antes_da_interface(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    preparar_restauracao(origem, atual)
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal))
    env["QT_QPA_PLATFORM"] = "offscreen"
    env.pop("MAINERP_LAUNCHER", None)
    codigo = """
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
import mainerp.app as app
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
original = QApplication.exec
def executar():
    QTimer.singleShot(1000, lambda: QApplication.exit(0))
    return original()
QApplication.exec = staticmethod(executar)
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert sinal.is_file(), resultado.stdout + resultado.stderr
    assert ler_valor(atual) == "anterior"
    backups = list((dados / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    assert not caminho_restauracao_pendente(atual).exists()


def test_inicializacao_bloqueia_interface_se_pendencia_esta_corrompida(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    criar_banco(atual, "atual")
    pendente = caminho_restauracao_pendente(atual)
    pendente.write_bytes(b"corrompido")
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal))
    env["QT_QPA_PLATFORM"] = "offscreen"
    codigo = """
from PyQt6.QtWidgets import QMessageBox
import mainerp.app as app
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 4, resultado.stdout + resultado.stderr
    assert "restauração pendente" in resultado.stdout
    assert not sinal.exists()
    assert pendente.exists()
    assert ler_valor(atual) == "atual"


def test_inicializacao_bloqueia_interface_se_copia_falhar(tmp_path):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal),
               QT_QPA_PLATFORM="offscreen")
    codigo = """
from PyQt6.QtWidgets import QMessageBox
import mainerp.app as app
import mainerp.data.restore as restore
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
def falhar(origem, destino):
    raise OSError("disco cheio simulado")
restore._copiar_banco = falhar
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 4, resultado.stdout + resultado.stderr
    assert "disco cheio simulado" in resultado.stdout
    assert not sinal.exists()
    assert pendente.exists()
    anterior, = (dados / "backups").glob("pre_restore_*.db")
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "atual"


@pytest.mark.parametrize("momento", ["antes_da_copia", "apos_a_copia"])
def test_falha_ambigua_na_copia_bloqueia_abertura_e_preserva_recuperacao(
    tmp_path, momento
):
    dados = tmp_path / "dados"
    dados.mkdir()
    atual = dados / "erp.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    pendente = preparar_restauracao(origem, atual)
    sinal = tmp_path / "aberto"
    env = dict(os.environ, MAINERP_DATA=str(dados), MAINERP_OK_FILE=str(sinal),
               QT_QPA_PLATFORM="offscreen")
    codigo = """
import sqlite3, sys
from PyQt6.QtWidgets import QMessageBox
import mainerp.app as app
import mainerp.data.restore as restore
app.verificar_instancia_unica = lambda nome: True
QMessageBox.critical = lambda *args: print("ERRO:", args[2], flush=True)
original = restore._copiar_banco
momento = sys.argv[1]
def falhar(origem, destino, progress=None):
    if momento == "apos_a_copia":
        original(origem, destino, progress=progress)
    raise sqlite3.OperationalError("falha simulada na confirmação da cópia")
restore._copiar_banco = falhar
app.main()
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, momento], env=env, capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )

    assert resultado.returncode == 4, resultado.stdout + resultado.stderr
    assert "o estado do banco pode ter sido alterado" in resultado.stdout.lower()
    assert "não é possível confirmar uma reversão" in resultado.stdout.lower()
    assert "não exclua nem altere o banco" in resultado.stdout.lower()
    assert "falha simulada na confirmação da cópia" in resultado.stdout
    assert not sinal.exists()
    assert pendente.exists()
    anterior, = (dados / "backups").glob("pre_restore_*.db")
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == ("anterior" if momento == "apos_a_copia" else "atual")

    aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_interrupcao_durante_copia_preserva_banco_e_permite_repetir(
    tmp_path, journal_mode
):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(origem)
    conn.execute("CREATE TABLE dados_grandes (conteudo BLOB)")
    conn.executemany(
        "INSERT INTO dados_grandes VALUES (zeroblob(8192))", [()] * 120
    )
    conn.commit()
    conn.close()
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    codigo = """
import os, sys
import mainerp.data.restore as r
original = r._copiar_banco
def interromper(origem, destino):
    def progresso(status, remaining, total):
        if remaining > 0:
            os._exit(73)
    original(origem, destino, progress=progresso)
r._copiar_banco = interromper
r.aplicar_restauracao_pendente(sys.argv[1])
"""
    resultado = subprocess.run(
        [sys.executable, "-c", codigo, str(atual)], capture_output=True,
        text=True, errors="replace", timeout=45, check=False,
    )
    assert resultado.returncode == 73, resultado.stdout + resultado.stderr
    assert pendente.exists()
    assert ler_valor(atual) == "atual"
    backups = list((tmp_path / "backups").glob("pre_restore_*.db"))
    assert len(backups) == 1
    assert ler_valor(backups[0]) == "atual"
    aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()


@pytest.mark.parametrize("journal_mode", ["DELETE", "WAL"])
def test_processo_terminado_apos_copia_permite_recuperacao(tmp_path, journal_mode):
    atual = tmp_path / "atual.db"
    origem = tmp_path / "origem.db"
    criar_banco(atual, "atual")
    criar_banco(origem, "anterior")
    conn = sqlite3.connect(atual)
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.close()
    pendente = preparar_restauracao(origem, atual)
    pronto = tmp_path / "copia-concluida"
    codigo = """
import sys, time
from pathlib import Path
import mainerp.data.restore as r
original = r._copiar_banco
def esperar(origem, destino):
    original(origem, destino)
    Path(sys.argv[2]).touch()
    while True:
        time.sleep(0.1)
r._copiar_banco = esperar
r.aplicar_restauracao_pendente(sys.argv[1])
"""
    proc = subprocess.Popen(
        [sys.executable, "-c", codigo, str(atual), str(pronto)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        limite = time.monotonic() + 30
        while not pronto.exists():
            if proc.poll() is not None or time.monotonic() >= limite:
                raise RuntimeError("O processo não concluiu a cópia")
            time.sleep(0.01)
        proc.kill()
        saida, erro = proc.communicate(timeout=10)
        assert proc.returncode != 0, (saida, erro)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)

    assert pendente.exists()
    anterior, = (tmp_path / "backups").glob("pre_restore_*.db")
    assert ler_valor(anterior) == "atual"
    assert ler_valor(atual) == "anterior"
    for banco in (atual, anterior, pendente):
        conn = sqlite3.connect(banco)
        try:
            assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        finally:
            conn.close()

    aplicar_restauracao_pendente(atual)
    assert ler_valor(atual) == "anterior"
    assert not pendente.exists()
