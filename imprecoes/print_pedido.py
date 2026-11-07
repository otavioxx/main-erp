import io
import os
import sqlite3
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from database import Database
from models.empresa import Empresa
from models.pedido import Pedido


class PrintPedido:
    @staticmethod
    def buscar_itens_pedido(pedido_id):
        """
        Busca todos os itens de um pedido específico - MODIFICADO para incluir campos do produto
        """
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            # Query explícita para evitar problemas com mudanças na estrutura da tabela
            query = """
                SELECT
                    pi.id,
                    pi.produto_id,
                    p.nome as produto_nome,
                    p.cor,
                    p.tamanho,
                    p.referencia,
                    pi.quantidade,
                    pi.preco_custo,
                    COALESCE(pi.preco_venda, pi.preco_custo * 1.3) as preco_venda,
                    pi.subtotal
                FROM itens_pedido pi
                INNER JOIN produtos p ON pi.produto_id = p.id
                WHERE pi.pedido_id = ?
                ORDER BY p.nome
            """

            cursor.execute(query, (pedido_id,))
            result = cursor.fetchall()
            return result

        except Exception as e:
            print(f"Erro ao buscar itens do pedido: {e!s}")
            return []
        finally:
            # Tentar fechar a conexão de forma segura
            try:
                if hasattr(db, "close_connection"):
                    db.close_connection()
                elif hasattr(db, "connection") and db.connection:
                    db.connection.close()
            except sqlite3.Error:
                pass

    @staticmethod
    def gerar_comprovante(pedido_id, pasta_destino="relatorios"):
        """Gera um comprovante de pedido em formato PDF com cabeçalho da empresa - CORRIGIDO"""
        try:
            pedido = Pedido.buscar_por_id(pedido_id)
            if not pedido:
                return None

            empresa = Empresa.buscar()

            # Usar o método local para buscar itens
            itens = PrintPedido.buscar_itens_pedido(pedido_id)

            fornecedor_nome = PrintPedido._get_nome_fornecedor(pedido.fornecedor_id)

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                pasta_destino, f"pedido_{pedido_id}_{timestamp}.pdf"
            )

            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=10 * mm,  # Margens menores para aproveitar espaço
                leftMargin=10 * mm,
                topMargin=15 * mm,
                bottomMargin=15 * mm,
            )

            styles = getSampleStyleSheet()

            estilo_empresa = ParagraphStyle(
                "Empresa",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#000000"),
            )

            estilo_titulo = ParagraphStyle(
                "Titulo",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#366092"),
            )

            estilo_subtitulo = ParagraphStyle(
                "Subtitulo",
                parent=styles["Heading3"],
                fontSize=12,
                spaceAfter=6,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#000000"),
            )

            estilo_normal = ParagraphStyle(
                "Normal",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT,
            )

            estilo_rodape = ParagraphStyle(
                "Rodape",
                parent=styles["Normal"],
                fontSize=8,
                spaceAfter=0,
                alignment=TA_CENTER,
                textColor=colors.grey,
            )

            elements = []

            if empresa and hasattr(empresa, "logo") and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((80, 80))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format="PNG")
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=60, height=60)
                    logo.hAlign = "CENTER"
                    elements.append(logo)
                    elements.append(Spacer(1, 5 * mm))
                except Exception as e:
                    print(f"Erro ao processar logo: {e}")

            if empresa and hasattr(empresa, "nome") and empresa.nome:
                elements.append(Paragraph(empresa.nome.upper(), estilo_empresa))

            if empresa and hasattr(empresa, "cnpj") and empresa.cnpj:
                elements.append(Paragraph(f"CNPJ: {empresa.cnpj}", estilo_normal))

            info_contato = []
            if empresa and hasattr(empresa, "endereco") and empresa.endereco:
                info_contato.append(empresa.endereco)
            if empresa and hasattr(empresa, "telefone") and empresa.telefone:
                info_contato.append(f"Tel: {empresa.telefone}")
            if empresa and hasattr(empresa, "email") and empresa.email:
                info_contato.append(empresa.email)

            if info_contato:
                elements.append(Paragraph(" | ".join(info_contato), estilo_normal))

            elements.append(Spacer(1, 8 * mm))

            elements.append(
                Table(
                    [[""]],
                    colWidths=[190 * mm],
                    style=[
                        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#366092")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#366092")),
                    ],
                )
            )

            elements.append(Spacer(1, 8 * mm))

            elements.append(
                Paragraph(f"COMPROVANTE DE PEDIDO - Nº {pedido_id}", estilo_titulo)
            )
            elements.append(Spacer(1, 6 * mm))

            data_pedido_formatada = (
                datetime.strptime(str(pedido.data_pedido), "%Y-%m-%d").strftime(
                    "%d/%m/%Y"
                )
                if pedido.data_pedido
                else "N/A"
            )
            elements.append(
                Paragraph(
                    f"<b>Data do Pedido:</b> {data_pedido_formatada}", estilo_normal
                )
            )

            elements.append(
                Paragraph(f"<b>Fornecedor:</b> {fornecedor_nome}", estilo_normal)
            )

            # CORREÇÃO PRINCIPAL: Garantir que o status seja string antes de aplicar upper()
            status_str = str(pedido.status) if pedido.status is not None else "PENDENTE"
            elements.append(
                Paragraph(f"<b>Status:</b> {status_str.upper()}", estilo_normal)
            )

            if pedido.data_recebimento:
                data_recebimento_formatada = datetime.strptime(
                    str(pedido.data_recebimento), "%Y-%m-%d"
                ).strftime("%d/%m/%Y")
                elements.append(
                    Paragraph(
                        f"<b>Data de Recebimento:</b> {data_recebimento_formatada}",
                        estilo_normal,
                    )
                )

            if pedido.observacao:
                elements.append(
                    Paragraph(f"<b>Observação:</b> {pedido.observacao}", estilo_normal)
                )

            elements.append(Spacer(1, 8 * mm))

            elements.append(Paragraph("ITENS DO PEDIDO", estilo_subtitulo))
            elements.append(Spacer(1, 4 * mm))

            # TABELA COM NOVA ORDEM DAS COLUNAS
            # Código, Nome, Cor, Tamanho, Referencia, Qtd, Custo R$, Venda R$, Subtotal R$
            tabela_dados = [
                [
                    "Cód.",
                    "Nome",
                    "Cor",
                    "Tamanho",
                    "Ref.",
                    "Qtd",
                    "Custo R$",
                    "Venda R$",
                    "Subtotal R$",
                ]
            ]

            subtotal = 0
            for item in itens:
                # Acessar os itens com estrutura corrigida
                # 0=id, 1=produto_id, 2=nome, 3=cor, 4=tamanho, 5=referencia,
                # 6=quantidade, 7=preco_custo, 8=preco_venda, 9=subtotal
                produto_id = item[1] if len(item) > 1 else "N/A"
                produto_nome = item[2] if len(item) > 2 else "Produto desconhecido"
                cor = item[3] if len(item) > 3 and item[3] else ""
                tamanho = item[4] if len(item) > 4 and item[4] else ""
                referencia = item[5] if len(item) > 5 and item[5] else ""
                quantidade = item[6] if len(item) > 6 else 0
                preco_custo = float(item[7]) if len(item) > 7 and item[7] else 0.0
                preco_venda = float(item[8]) if len(item) > 8 and item[8] else 0.0
                subtotal_item = float(item[9]) if len(item) > 9 and item[9] else 0.0

                # Truncar nome do produto se muito longo (max ~40 chars para o PDF)
                if len(produto_nome) > 40:
                    produto_nome = produto_nome[:37] + "..."

                subtotal += subtotal_item

                tabela_dados.append(
                    [
                        str(produto_id),  # Código
                        produto_nome,  # Nome
                        cor[:15] if cor else "",  # Cor (max 15 chars)
                        tamanho[:5] if tamanho else "",  # Tamanho (max 5 chars)
                        referencia[:10] if referencia else "",  # Ref (max 10 chars)
                        str(quantidade),  # Qtd
                        f"R$ {preco_custo:.2f}",  # Custo
                        f"R$ {preco_venda:.2f}",  # Venda
                        f"R$ {subtotal_item:.2f}",  # Subtotal
                    ]
                )

            # Código(10) + Nome(60) + Cor(24) + Tamanho(15) + Ref(15) + Qtd(12) + Custo(18) + Venda(18) + Subtotal(18) = 175mm
            tabela = Table(
                tabela_dados,
                colWidths=[
                    10 * mm,  # Código
                    60 * mm,  # Nome (para nomes de até 50 chars)
                    24 * mm,  # Cor
                    15 * mm,  # Tamanho
                    15 * mm,  # Referência
                    12 * mm,  # Qtd
                    18 * mm,  # Custo R$
                    18 * mm,  # Venda R$
                    18 * mm,
                ],  # Subtotal R$
                rowHeights=[6 * mm] + [4.5 * mm] * (len(tabela_dados) - 1),
            )

            estilo_tabela = TableStyle(
                [
                    # Cabeçalho
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7),
                    ("TOPPADDING", (0, 0), (-1, 0), 0.5),  # Reduzido
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 0.5),  # Reduzido
                    # Dados
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 6),
                    ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 1), (-1, -1), 0.3),  # Reduzido
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 0.3),  # Reduzido
                    # Alinhamentos específicos por coluna
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),
                    ("ALIGN", (1, 1), (1, -1), "LEFT"),
                    ("ALIGN", (2, 1), (2, -1), "LEFT"),
                    ("ALIGN", (3, 1), (3, -1), "CENTER"),
                    ("ALIGN", (4, 1), (4, -1), "LEFT"),
                    ("ALIGN", (5, 1), (5, -1), "CENTER"),
                    ("ALIGN", (6, 1), (6, -1), "RIGHT"),
                    ("ALIGN", (7, 1), (7, -1), "RIGHT"),
                    ("ALIGN", (8, 1), (8, -1), "RIGHT"),
                    # Grade
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F8F8F8")],
                    ),
                ]
            )

            # Desabilitar quebra de linha: definir estilo de célula sem wrap
            for row in range(len(tabela_dados)):
                for col in range(len(tabela_dados[row])):
                    tabela.setStyle(
                        [("WORDWRAP", (col, row), (col, row), "CJK")]
                    )  # impede quebra

            tabela.setStyle(estilo_tabela)
            elements.append(tabela)
            elements.append(Spacer(1, 6 * mm))

            # Totais - ATUALIZADO PARA INCLUIR DESCONTO
            totais_dados = []

            # Sempre mostrar subtotal
            totais_dados.append(["Subtotal dos Produtos:", f"R$ {subtotal:.2f}"])

            # Mostrar desconto se houver (valor > 0) - CORRIGIDO
            desconto_valor = getattr(pedido, "desconto", 0) or 0
            if desconto_valor > 0:
                totais_dados.append(["(-) Desconto:", f"R$ {desconto_valor:.2f}"])

            # Mostrar frete se houver (valor > 0) - CORRIGIDO
            frete_valor = getattr(pedido, "valor_frete", 0) or 0
            if frete_valor > 0:
                totais_dados.append(["(+) Frete:", f"R$ {frete_valor:.2f}"])

            # Total final - CORRIGIDO
            total_valor = getattr(pedido, "valor_total", 0) or 0
            totais_dados.append(["TOTAL GERAL:", f"R$ {total_valor:.2f}"])

            tabela_totais = Table(totais_dados, colWidths=[140 * mm, 50 * mm])

            # Estilo da tabela de totais
            estilo_totais = TableStyle(
                [
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )

            # Destacar linha do desconto em vermelho se houver
            if desconto_valor > 0:
                # Encontrar qual linha é o desconto
                for i, linha in enumerate(totais_dados):
                    if "(-) Desconto:" in linha[0]:
                        estilo_totais.add("TEXTCOLOR", (0, i), (1, i), colors.red)
                        break

            # Destacar linha do frete em azul se houver
            if frete_valor > 0:
                for i, linha in enumerate(totais_dados):
                    if "(+) Frete:" in linha[0]:
                        estilo_totais.add("TEXTCOLOR", (0, i), (1, i), colors.blue)
                        break

            # Destacar linha do total final
            estilo_totais.add("LINEABOVE", (0, -1), (-1, -1), 1, colors.black)
            estilo_totais.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
            estilo_totais.add("FONTSIZE", (0, -1), (-1, -1), 12)
            estilo_totais.add("BOTTOMPADDING", (0, -1), (-1, -1), 10)

            tabela_totais.setStyle(estilo_totais)
            elements.append(tabela_totais)
            elements.append(Spacer(1, 12 * mm))

            # Status do pedido - CORRIGIDO para usar status_str
            if status_str.lower() == "pendente":
                status_msg = "PEDIDO PENDENTE - Aguardando recebimento"
                elements.append(
                    Paragraph(
                        status_msg,
                        ParagraphStyle(
                            "StatusPendente",
                            parent=styles["Normal"],
                            fontSize=11,
                            textColor=colors.orange,
                            alignment=TA_CENTER,
                            fontName="Helvetica-Bold",
                        ),
                    )
                )
            elif status_str.lower() == "recebido":
                status_msg = "PEDIDO RECEBIDO"
                elements.append(
                    Paragraph(
                        status_msg,
                        ParagraphStyle(
                            "StatusRecebido",
                            parent=styles["Normal"],
                            fontSize=11,
                            textColor=colors.green,
                            alignment=TA_CENTER,
                            fontName="Helvetica-Bold",
                        ),
                    )
                )
            elif status_str.lower() == "cancelado":
                status_msg = "PEDIDO CANCELADO"
                elements.append(
                    Paragraph(
                        status_msg,
                        ParagraphStyle(
                            "StatusCancelado",
                            parent=styles["Normal"],
                            fontSize=11,
                            textColor=colors.red,
                            alignment=TA_CENTER,
                            fontName="Helvetica-Bold",
                        ),
                    )
                )

            elements.append(Spacer(1, 8 * mm))

            data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            elements.append(Paragraph(f"Emitido em: {data_emissao}", estilo_rodape))

            doc.build(elements)
            return filename

        except Exception as e:
            print(f"Erro ao gerar comprovante PDF: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def _get_nome_fornecedor(fornecedor_id):
        """Obtém o nome do fornecedor pelo ID - CORRIGIDO"""
        if not fornecedor_id:
            return "Fornecedor não informado"

        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            query = "SELECT nome FROM fornecedores WHERE id = ?"
            cursor.execute(query, (fornecedor_id,))
            result = cursor.fetchone()

            return result[0] if result else "Fornecedor não encontrado"

        except Exception as e:
            return f"Erro: {e!s}"
        finally:
            # Tentar fechar a conexão de forma segura
            try:
                if hasattr(db, "close_connection"):
                    db.close_connection()
                elif hasattr(db, "connection") and db.connection:
                    db.connection.close()
            except sqlite3.Error:
                pass
