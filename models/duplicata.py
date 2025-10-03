#\erp\model\duplicata.py
from database import Database
from datetime import timedelta
from utils.database_utils import DatabaseUtils
import sqlite3

class Duplicata:
    def __init__(self, id=None, venda_id=None, cliente_id=None, numero_parcela=1,
                 valor_parcela=0.0, data_vencimento=None, data_pagamento=None,
                 status="aberto"):
        self.id = id
        self.venda_id = venda_id
        self.cliente_id = cliente_id
        self.numero_parcela = numero_parcela
        self.valor_parcela = valor_parcela
        self.data_vencimento = data_vencimento
        self.data_pagamento = data_pagamento
        self.status = status

    def salvar(self):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            if self.id:
                cursor.execute('''
                    UPDATE duplicatas SET venda_id=?, cliente_id=?, numero_parcela=?,
                    valor_parcela=?, data_vencimento=?, data_pagamento=?, status=?
                    WHERE id=?
                ''', (self.venda_id, self.cliente_id, self.numero_parcela,
                     self.valor_parcela, self.data_vencimento, self.data_pagamento,
                     self.status, self.id))
            else:
                cursor.execute('''
                    INSERT INTO duplicatas (venda_id, cliente_id, numero_parcela,
                    valor_parcela, data_vencimento, data_pagamento, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (self.venda_id, self.cliente_id, self.numero_parcela,
                     self.valor_parcela, self.data_vencimento, self.data_pagamento,
                     self.status))
                self.id = cursor.lastrowid

            conn.commit()
            return self.id
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def criar_parcelas(venda_id, cliente_id, valor_financiado, parcelas, data_primeiro_vencimento):
        """Cria parcelas baseadas no valor financiado (não no valor total)"""
        valor_parcela = valor_financiado / parcelas
        duplicatas = []

        for i in range(parcelas):
            data_vencimento = data_primeiro_vencimento + timedelta(days=30 * i)

            resultado = DatabaseUtils.executar_com_retry(
                '''
                INSERT INTO duplicatas
                (venda_id, cliente_id, numero_parcela, valor_parcela, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, 'aberto')
                ''',
                (venda_id, cliente_id, i + 1, valor_parcela, data_vencimento)
            )

            duplicata = Duplicata(
                id=resultado,
                venda_id=venda_id,
                cliente_id=cliente_id,
                numero_parcela=i + 1,
                valor_parcela=valor_parcela,
                data_vencimento=data_vencimento,
                status="aberto"
            )
            duplicatas.append(duplicata)

        return duplicatas

    @staticmethod
    def buscar_por_venda(venda_id):
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM duplicatas WHERE venda_id = ? ORDER BY numero_parcela', (venda_id,))
        duplicatas = cursor.fetchall()
        conn.close()
        return duplicatas

    @staticmethod
    def buscar_todas_com_cliente():
        """Busca todas as duplicatas abertas com informações do cliente"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT d.*, c.nome as cliente_nome
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                WHERE d.status = 'aberto'
                ORDER BY d.data_vencimento
            ''')
            return cursor.fetchall()
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def buscar_por_status(status):
        """Busca duplicatas por status"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            if status == 'aberto':
                cursor.execute('''
                    SELECT d.*, c.nome as cliente_nome
                    FROM duplicatas d
                    LEFT JOIN clientes c ON d.cliente_id = c.id
                    WHERE d.status = 'aberto'
                    ORDER BY d.data_vencimento
                ''')
            else:
                cursor.execute('''
                    SELECT dp.*, c.nome as cliente_nome
                    FROM duplicatas_pagas dp
                    LEFT JOIN clientes c ON dp.cliente_id = c.id
                    ORDER BY dp.data_pagamento DESC
                ''')
            return cursor.fetchall()
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def buscar_por_cliente(cliente_id):
        """Busca duplicatas por cliente"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT d.*, c.nome as cliente_nome
                FROM duplicatas d
                LEFT JOIN clientes c ON d.cliente_id = c.id
                WHERE d.cliente_id = ? AND d.status = 'aberto'
                ORDER BY d.data_vencimento
            ''', (cliente_id,))

            abertas = cursor.fetchall()

            cursor.execute('''
                SELECT dp.*, c.nome as cliente_nome
                FROM duplicatas_pagas dp
                LEFT JOIN clientes c ON dp.cliente_id = c.id
                WHERE dp.cliente_id = ?
                ORDER BY dp.data_pagamento DESC
            ''', (cliente_id,))

            pagas = cursor.fetchall()

            return abertas + pagas
        except Exception as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def marcar_como_paga(duplicata_id, valor_recebido, data_pagamento, forma_pagamento):
        conn = Database().get_connection()
        cursor = conn.cursor()
        try:
            # Buscar duplicata
            cursor.execute("SELECT id, venda_id, cliente_id, numero_parcela, valor_parcela, data_vencimento FROM duplicatas WHERE id = ?", (duplicata_id,))
            duplicata = cursor.fetchone()
            if not duplicata:
                raise Exception("Duplicata não encontrada")

            valor_original = float(duplicata[4])
            venda_id = duplicata[1]
            cliente_id = duplicata[2]
            numero_parcela = duplicata[3]
            data_vencimento = duplicata[5]

            # Calcular diferença
            diferenca = float(valor_recebido) - valor_original

            # Buscar parcelas restantes
            cursor.execute('''
                SELECT id, numero_parcela, valor_parcela FROM duplicatas
                WHERE venda_id = ? AND id != ? AND status = 'aberto'
                ORDER BY numero_parcela
            ''', (venda_id, duplicata_id))

            parcelas_restantes = cursor.fetchall()
            qtd_restantes = len(parcelas_restantes)

            # Se há diferença e parcelas restantes, redistribuir
            if qtd_restantes > 0 and abs(diferenca) > 1e-9:
                ajuste_por_parcela = round(diferenca / qtd_restantes, 2)

                # Verificar se precisa quitar parcelas automaticamente
                if diferenca > 0:  # Pagou a mais
                    # Calcular o total das parcelas restantes
                    total_parcelas_restantes = sum(float(p[2]) for p in parcelas_restantes)

                    if diferenca >= total_parcelas_restantes:
                        # O valor pago é suficiente para quitar todas as parcelas restantes
                        for parcela_id, num_parcela, valor_parcela in parcelas_restantes:
                            # Inserir na tabela de pagas
                            cursor.execute('''
                                INSERT INTO duplicatas_pagas
                                (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido,
                                data_vencimento, data_pagamento, forma_pagamento)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (venda_id, cliente_id, num_parcela, float(valor_parcela),
                                float(valor_parcela), data_vencimento, data_pagamento, forma_pagamento))

                            # Remover da tabela duplicatas
                            cursor.execute("DELETE FROM duplicatas WHERE id = ?", (parcela_id,))
                    else:
                        # Redistribuir a diferença normalmente
                        for parcela_id, num_parcela, valor_parcela in parcelas_restantes:
                            novo_valor = float(valor_parcela) - ajuste_por_parcela

                            if novo_valor <= 0:
                                # Parcela quitada automaticamente
                                cursor.execute('''
                                    INSERT INTO duplicatas_pagas
                                    (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido,
                                    data_vencimento, data_pagamento, forma_pagamento)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (venda_id, cliente_id, num_parcela, float(valor_parcela),
                                    float(valor_parcela), data_vencimento, data_pagamento, forma_pagamento))

                                cursor.execute("DELETE FROM duplicatas WHERE id = ?", (parcela_id,))
                            else:
                                # Atualizar valor da parcela
                                cursor.execute('UPDATE duplicatas SET valor_parcela = ? WHERE id = ?',
                                            (novo_valor, parcela_id))
                else:
                    # Pagou a menos - aumentar o valor das parcelas restantes
                    for parcela_id, num_parcela, valor_parcela in parcelas_restantes:
                        novo_valor = float(valor_parcela) + abs(ajuste_por_parcela)
                        cursor.execute('UPDATE duplicatas SET valor_parcela = ? WHERE id = ?',
                                    (novo_valor, parcela_id))

            # Inserir a parcela atual em duplicatas_pagas
            cursor.execute('''
                INSERT INTO duplicatas_pagas
                (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido,
                data_vencimento, data_pagamento, forma_pagamento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido,
                data_vencimento, data_pagamento, forma_pagamento))

            # Remover da tabela duplicatas
            cursor.execute("DELETE FROM duplicatas WHERE id = ?", (duplicata_id,))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def ajustar_parcelas_restantes(venda_id, duplicata_id, valor_pago, valor_original=None):
        """
        Ajusta as duplicatas restantes redistribuindo a diferença igualmente.
        Se pagar a menos -> aumenta as parcelas.
        Se pagar a mais -> reduz as parcelas (quitando se valor ficar <= 0).
        """
        from database import Database
        from datetime import datetime

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            # Obter valor original se não foi passado
            if valor_original is None:
                cursor.execute('SELECT valor_parcela FROM duplicatas WHERE id = ?', (duplicata_id,))
                row = cursor.fetchone()
                if not row:
                    raise Exception("Não foi possível obter o valor da duplicata original para ajuste.")
                valor_original = float(row[0])

            diferenca = float(valor_pago) - float(valor_original)
            if abs(diferenca) < 1e-9:
                # Nada a ajustar
                return

            print(f"=== Redistribuindo diferença (diferença = {diferenca:.2f}) ===")

            # Buscar parcelas restantes abertas
            cursor.execute('''
                SELECT id, numero_parcela, valor_parcela, cliente_id, data_vencimento
                FROM duplicatas
                WHERE venda_id = ? AND id != ? AND status = 'aberto'
                ORDER BY numero_parcela
            ''', (venda_id, duplicata_id))
            parcelas_restantes = cursor.fetchall()

            if not parcelas_restantes:
                print("Nenhuma parcela restante para redistribuir")
                return

            qtd = len(parcelas_restantes)
            ajuste = round(diferenca / qtd, 2)  # diferença distribuída igualmente
            hoje = datetime.now().date()

            for parcela in parcelas_restantes:
                parcela_id, numero_parcela, valor_parcela, cliente_id, data_venc = parcela
                valor_parcela = float(valor_parcela)

                novo_valor = round(valor_parcela - ajuste, 2) if diferenca > 0 else round(valor_parcela + abs(ajuste), 2)

                if novo_valor <= 0:
                    # Parcela quitada automaticamente
                    cursor.execute('''
                        INSERT INTO duplicatas_pagas
                        (venda_id, cliente_id, numero_parcela, valor_original, valor_recebido, data_vencimento, data_pagamento)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (venda_id, cliente_id, numero_parcela, valor_parcela, valor_parcela, data_venc, hoje))
                    cursor.execute('DELETE FROM duplicatas WHERE id = ?', (parcela_id,))
                    print(f"  Parcela {numero_parcela} quitada automaticamente (id {parcela_id})")
                else:
                    cursor.execute('''
                        UPDATE duplicatas
                        SET valor_parcela = ?
                        WHERE id = ? AND status = 'aberto'
                    ''', (novo_valor, parcela_id))
                    print(f"  Parcela {numero_parcela} ajustada para R$ {novo_valor:.2f}")

            conn.commit()
            print("Redistribuição concluída e commitada")

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao redistribuir diferença: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            conn.close()
