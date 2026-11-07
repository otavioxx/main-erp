"""
Utilitários para manipulação do banco de dados e backups
"""

import logging
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from mainerp.data.database import Database, MigracaoError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerencia operações do banco de dados"""

    @staticmethod
    def backup_database(source_db, destination_folder):
        """Cria backup do banco de dados"""
        if not os.path.exists(source_db):
            raise FileNotFoundError(f"Arquivo não encontrado: {source_db}")

        # Criar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(destination_folder, f"backup_manual_{timestamp}.db")

        # Copiar arquivo
        shutil.copy2(source_db, backup_file)

        return backup_file

    @staticmethod
    def _verify_database(db_path):
        """Verifica se o arquivo do banco é válido"""
        if not os.path.exists(db_path):
            return False

        try:
            uri = Path(db_path).resolve().as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            try:
                if conn.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    return False
                if conn.execute("PRAGMA user_version").fetchone()[0] > Database.MIGRACOES[-1][0]:
                    return False
                with tempfile.TemporaryDirectory() as pasta:
                    candidato = Path(pasta) / "candidato.db"
                    copia = sqlite3.connect(candidato)
                    try:
                        conn.backup(copia)
                    finally:
                        copia.close()
                    referencia = Database(str(Path(pasta) / "referencia.db"))
                    try:
                        referencia_conn = referencia.get_connection()
                        tabelas = {
                            row[0] for row in referencia_conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' "
                                "AND name NOT LIKE 'sqlite_%'"
                            )
                        }
                        existentes = {
                            row[0] for row in conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table'"
                            )
                        }
                        if not tabelas <= existentes:
                            return False
                        banco = Database(str(candidato))
                        try:
                            for tabela in tabelas:
                                esperadas = set(referencia._colunas(
                                    referencia_conn.cursor(), tabela
                                ))
                                atuais = set(banco._colunas(
                                    banco.get_connection().cursor(), tabela
                                ))
                                if not esperadas <= atuais:
                                    return False
                            return True
                        finally:
                            banco.close_connection()
                    finally:
                        referencia.close_connection()
            finally:
                conn.close()

        except (sqlite3.Error, OSError, MigracaoError):
            return False

    @staticmethod
    def get_database_info(db_path):
        """Obtém informações sobre o banco de dados"""
        if not os.path.exists(db_path):
            return None

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Informações gerais
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            # Contar registros em algumas tabelas principais
            info = {
                "path": db_path,
                "size_mb": os.path.getsize(db_path) / (1024 * 1024),
                "modified": datetime.fromtimestamp(os.path.getmtime(db_path)),
                "tables_count": len(tables),
                "tables": [table[0] for table in tables],
                "record_counts": {},
            }

            # Contar registros em tabelas importantes
            important_tables = ["clientes", "produtos", "vendas", "duplicatas"]
            for table in important_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    info["record_counts"][table] = count
                except sqlite3.Error:
                    info["record_counts"][table] = 0

            conn.close()
            return info

        except Exception:
            logger.exception("Erro ao obter informações do banco")
            return None

    @staticmethod
    def list_backups(backup_folder):
        """Lista todos os backups disponíveis"""
        if not os.path.exists(backup_folder):
            return []

        backups = []
        for file in os.listdir(backup_folder):
            if file.endswith((".db", ".zip")):
                file_path = os.path.join(backup_folder, file)
                file_info = {
                    "name": file,
                    "path": file_path,
                    "size_mb": os.path.getsize(file_path) / (1024 * 1024),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                    "type": "zip" if file.endswith(".zip") else "db",
                }

                # Tentar obter mais informações se for um arquivo ZIP
                if file.endswith(".zip"):
                    try:
                        with zipfile.ZipFile(file_path, "r") as zipf:
                            db_files = [f for f in zipf.namelist() if f.endswith(".db")]
                            file_info["contains_db"] = len(db_files) > 0
                            file_info["db_files"] = db_files
                    except (zipfile.BadZipFile, OSError):
                        file_info["contains_db"] = False

                backups.append(file_info)

        # Ordenar por data de modificação (mais recente primeiro)
        backups.sort(key=lambda x: x["modified"], reverse=True)
        return backups
