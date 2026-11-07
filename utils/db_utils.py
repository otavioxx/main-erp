"""
Utilitários para manipulação do banco de dados e backups
"""

import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime


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
    def restore_database(backup_file, target_db):
        """Restaura banco de dados a partir de um backup"""
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup não encontrado: {backup_file}")

        # Verificar se o backup é um arquivo zip
        if backup_file.endswith(".zip"):
            return DatabaseManager._restore_from_zip(backup_file, target_db)
        else:
            # É um arquivo .db direto
            return DatabaseManager._restore_from_db(backup_file, target_db)

    @staticmethod
    def _restore_from_zip(zip_file, target_db):
        """Restaura a partir de arquivo ZIP"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extrair arquivo ZIP
            with zipfile.ZipFile(zip_file, "r") as zipf:
                # Procurar arquivo .db dentro do ZIP
                db_files = [f for f in zipf.namelist() if f.endswith(".db")]
                if not db_files:
                    raise ValueError("Nenhum arquivo .db encontrado no backup")

                # Extrair o primeiro arquivo .db
                db_filename = db_files[0]
                zipf.extract(db_filename, temp_dir)
                extracted_db = os.path.join(temp_dir, db_filename)

                # Fazer a restauração
                return DatabaseManager._restore_from_db(extracted_db, target_db)

    @staticmethod
    def _restore_from_db(source_db, target_db):
        """Restaura a partir de arquivo .db"""
        # Verificar integridade do banco de backup
        if not DatabaseManager._verify_database(source_db):
            raise ValueError("Arquivo de backup corrompido ou inválido")

        # Criar backup do banco atual antes de restaurar
        backup_dir = os.path.join(os.path.dirname(target_db), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = os.path.join(backup_dir, f"pre_restore_{timestamp}.db")
        shutil.copy2(target_db, pre_restore_backup)

        try:
            # Fechar todas as conexões com o banco atual
            DatabaseManager._close_all_connections()

            # Fazer cópia do backup para o destino
            shutil.copy2(source_db, target_db)

            # Verificar se a restauração foi bem-sucedida
            if not DatabaseManager._verify_database(target_db):
                # Se falhou, restaurar o backup anterior
                shutil.copy2(pre_restore_backup, target_db)
                raise ValueError(
                    "Falha na restauração - Banco revertido para estado anterior"
                )

            return True

        except Exception as e:
            # Em caso de erro, tentar restaurar o backup anterior
            try:
                if os.path.exists(pre_restore_backup):
                    shutil.copy2(pre_restore_backup, target_db)
            except:
                pass
            raise e

    @staticmethod
    def _verify_database(db_path):
        """Verifica se o arquivo do banco é válido"""
        if not os.path.exists(db_path):
            return False

        try:
            # Tentar conectar e executar uma query simples
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()

            # Verificar se há tabelas essenciais
            essential_tables = ["clientes", "produtos", "vendas", "duplicatas"]
            existing_tables = [table[0].lower() for table in tables]

            # Verificar se pelo menos algumas tabelas essenciais existem
            found_essential = any(
                table in existing_tables for table in essential_tables
            )

            return len(tables) > 0 and found_essential

        except:
            return False

    @staticmethod
    def _close_all_connections():
        """Tenta fechar todas as conexões com o banco"""
        import gc

        # Coletar garbage para liberar conexões
        gc.collect()

        # Tentar fechar conexões do sqlite3
        try:
            # SQLite3 não tem uma maneira global de fechar todas as conexões
            # Dependemos do garbage collector
            pass
        except:
            pass

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
                except:
                    info["record_counts"][table] = 0

            conn.close()
            return info

        except Exception as e:
            print(f"Erro ao obter informações do banco: {e}")
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
                    except:
                        file_info["contains_db"] = False

                backups.append(file_info)

        # Ordenar por data de modificação (mais recente primeiro)
        backups.sort(key=lambda x: x["modified"], reverse=True)
        return backups
