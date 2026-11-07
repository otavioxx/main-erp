import io
import logging
import os
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

from mainerp.data.database import obter_database
from mainerp.data.models.condicional import Condicional
from mainerp.data.models.empresa import Empresa
from mainerp.data.money import de_centavos, para_centavos

logger = logging.getLogger(__name__)


class PrintCondicional:
    HEADER_BG_COLOR = colors.HexColor("#366092")
    LIGHT_BG_COLOR = colors.HexColor("#F2F2F2")
    ZEBRA_BG_COLOR = colors.HexColor("#F8F8F8")
    TEXT_COLOR = colors.black
    SECONDARY_TEXT_COLOR = colors.HexColor("#666666")

    @staticmethod
    def _limitar_texto(texto, max_chars):
        """Limita o texto ao número máximo de caracteres"""
        if not texto:
            return ""
        if len(str(texto)) > max_chars:
            return str(texto)[: max_chars - 3] + "..."
        return str(texto)

    @staticmethod
    def _formatar_data(data):
        """Formata uma data (string ou objeto date) para o formato dd/mm/yyyy"""
        if not data:
            return "N/A"

        try:
            if isinstance(data, str):
                data_obj = datetime.strptime(data, "%Y-%m-%d")
                return data_obj.strftime("%d/%m/%Y")
            else:
                return data.strftime("%d/%m/%Y")
        except (ValueError, AttributeError):
            return "Data inválida"

    @staticmethod
    def _get_nome_cliente(cliente_id):
        """Obtém o nome do cliente pelo ID"""
        if not cliente_id:
            return "Cliente não informado"

        try:
            with obter_database().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
                result = cursor.fetchone()
                return result[0] if result else "Cliente não encontrado"
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {e}")
            return f"Erro: {e!s}"

    @staticmethod
    def buscar_itens_condicional_detalhados(condicional_id):
        """Busca itens da condicional incluindo campos do produto (cor, tamanho)"""
        try:
            db = obter_database()
            conn = db.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    ic.id,
                    ic.produto_id,
                    p.nome as produto_nome,
                    p.cor,
                    p.tamanho,
                    ic.quantidade,
                    ic.preco_unitario_centavos
                FROM itens_condicional ic
                INNER JOIN produtos p ON ic.produto_id = p.id
                WHERE ic.condicional_id = ?
                ORDER BY p.nome
            """

            cursor.execute(query, (condicional_id,))
            result = cursor.fetchall()
            return [(*item[:6], float(de_centavos(item[6]))) for item in result]

        except Exception as e:
            logger.error(f"Erro ao buscar itens da condicional: {e!s}")
            return []

    @staticmethod
    def _limpar_nome_arquivo(nome):
        """Remove caracteres inválidos do nome para uso em arquivo"""
        import re

        # Remove caracteres especiais e substitui espaços por underscore
        nome_limpo = re.sub(r'[<>:"/\\|?*]', "", nome)
        nome_limpo = re.sub(r"\s+", "_", nome_limpo.strip())
        # Limita o tamanho do nome
        return nome_limpo[:50] if len(nome_limpo) > 50 else nome_limpo

    @staticmethod
    def gerar_comprovante(condicional_id, pasta_destino="imprecoes"):
        """Gera um comprovante de condicional em formato PDF com cabeçalho da empresa"""
        try:
            condicional = Condicional.buscar_por_id(condicional_id)
            if not condicional:
                logger.error(f"Condicional com ID {condicional_id} não encontrada")
                return None

            empresa = Empresa.buscar()

            cliente_nome = PrintCondicional._get_nome_cliente(condicional.cliente_id)

            # Usar o método local para buscar itens detalhados
            itens = PrintCondicional.buscar_itens_condicional_detalhados(condicional_id)

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            cliente_nome_limpo = PrintCondicional._limpar_nome_arquivo(cliente_nome)
            data_atual = datetime.now().strftime("%d-%m-%Y")
            filename = os.path.join(
                pasta_destino, f"CONDICIONAL_{cliente_nome_limpo}_{data_atual}.pdf"
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
                textColor=colors.black,
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
                textColor=colors.black,
            )

            estilo_info = ParagraphStyle(
                "Info",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=4,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )

            estilo_normal = ParagraphStyle(
                "Normal",
                parent=styles["Normal"],
                fontSize=9,
                spaceAfter=4,
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

            if empresa and empresa.logo:
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
                    logger.error(f"Erro ao processar logo: {e}")

            nome_empresa = (
                empresa.nome.upper() if empresa and empresa.nome else "NOME DA EMPRESA"
            )
            elements.append(Paragraph(nome_empresa, estilo_empresa))

            if empresa and empresa.cnpj:
                elements.append(Paragraph(f"CNPJ: {empresa.cnpj}", estilo_normal))

            info_contato = []
            if empresa:
                if empresa.endereco:
                    info_contato.append(empresa.endereco)
                if empresa.telefone:
                    info_contato.append(f"Tel: {empresa.telefone}")
                if empresa.email:
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
                Paragraph(
                    f"COMPROVANTE DE CONDICIONAL - Nº {condicional_id}", estilo_titulo
                )
            )
            elements.append(Spacer(1, 6 * mm))

            data_formatada = PrintCondicional._formatar_data(
                condicional.data_condicional
            )
            elements.append(
                Paragraph(f"<b>Data da Condicional:</b> {data_formatada}", estilo_info)
            )

            elements.append(Paragraph(f"<b>Cliente:</b> {cliente_nome}", estilo_info))

            data_devolucao = PrintCondicional._formatar_data(
                condicional.data_prevista_devolucao
            )
            elements.append(
                Paragraph(f"<b>Prev. Devolução:</b> {data_devolucao}", estilo_info)
            )

            elements.append(
                Paragraph(
                    f"<b>Status:</b> {condicional.status.capitalize()}", estilo_info
                )
            )

            if condicional.observacao:
                elements.append(
                    Paragraph(
                        f"<b>Observação:</b> {condicional.observacao}", estilo_info
                    )
                )

            elements.append(Spacer(1, 8 * mm))

            elements.append(Paragraph("ITENS DA CONDICIONAL", estilo_subtitulo))
            elements.append(Spacer(1, 4 * mm))

            if itens:
                # TABELA COM OS CAMPOS SOLICITADOS: ID, Nome, Tamanho, Cor, Quantidade, Valor de venda
                tabela_dados = [
                    ["ID", "Nome", "Tamanho", "Cor", "Qtd", "Valor Venda R$"]
                ]

                total_centavos = 0

                for item in itens:
                    # Estrutura da tupla: id, produto_id, nome, cor, tamanho, quantidade, preco_unitario
                    produto_id = str(item[1]) if len(item) > 1 else "N/A"
                    produto_nome = (
                        str(item[2]) if len(item) > 2 else "Produto desconhecido"
                    )
                    cor = str(item[3]) if len(item) > 3 and item[3] else ""
                    tamanho = str(item[4]) if len(item) > 4 and item[4] else ""
                    quantidade = int(item[5]) if len(item) > 5 and item[5] else 0
                    preco_unit = float(item[6]) if len(item) > 6 and item[6] else 0.0

                    total_centavos += para_centavos(preco_unit) * quantidade

                    # Limitar tamanhos dos textos
                    produto_nome = PrintCondicional._limitar_texto(produto_nome, 45)
                    tamanho = PrintCondicional._limitar_texto(tamanho, 8)
                    cor = PrintCondicional._limitar_texto(cor, 15)

                    tabela_dados.append(
                        [
                            str(produto_id),  # ID
                            produto_nome,  # Nome
                            tamanho,  # Tamanho
                            cor,  # Cor
                            str(quantidade),  # Quantidade
                            f"R$ {preco_unit:.2f}",  # Valor Venda
                        ]
                    )

                # ID(12) + Nome(70) + Tamanho(15) + Cor(25) + Qtd(12) + Valor(25) = 159mm
                tabela = Table(
                    tabela_dados,
                    colWidths=[
                        12 * mm,  # ID
                        70 * mm,  # Nome
                        15 * mm,  # Tamanho
                        25 * mm,  # Cor
                        12 * mm,  # Qtd
                        25 * mm,
                    ],  # Valor Venda
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
                        ("TOPPADDING", (0, 0), (-1, 0), 0.5),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 0.5),
                        # Dados
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 6),
                        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 1), (-1, -1), 0.3),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 0.3),
                        # Alinhamentos específicos por coluna
                        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # ID
                        ("ALIGN", (1, 1), (1, -1), "LEFT"),  # Nome
                        ("ALIGN", (2, 1), (2, -1), "CENTER"),  # Tamanho
                        ("ALIGN", (3, 1), (3, -1), "LEFT"),  # Cor
                        ("ALIGN", (4, 1), (4, -1), "CENTER"),  # Qtd
                        ("ALIGN", (5, 1), (5, -1), "RIGHT"),  # Valor
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

                tabela.setStyle(estilo_tabela)
                elements.append(tabela)
                elements.append(Spacer(1, 6 * mm))

                total_dados = [
                    [
                        "",
                        "",
                        "",
                        "",
                        "TOTAL:",
                        f"R$ {float(de_centavos(total_centavos)):.2f}",
                    ]
                ]

                tabela_total = Table(
                    total_dados,
                    colWidths=[12 * mm, 70 * mm, 15 * mm, 25 * mm, 12 * mm, 25 * mm],
                )

                estilo_total = TableStyle(
                    [
                        ("ALIGN", (0, 0), (4, 0), "RIGHT"),
                        ("ALIGN", (5, 0), (5, 0), "RIGHT"),
                        ("FONTNAME", (4, 0), (5, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (4, 0), (5, 0), 10),
                        ("LINEABOVE", (4, 0), (5, 0), 1, colors.black),
                    ]
                )

                tabela_total.setStyle(estilo_total)
                elements.append(tabela_total)
            else:
                elements.append(
                    Paragraph(
                        "Nenhum item encontrado nesta condicional.", estilo_normal
                    )
                )

            elements.append(
                Paragraph(
                    f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    estilo_rodape,
                )
            )

            doc.build(elements)
            logger.info(f"Comprovante de condicional gerado: {filename}")
            return filename

        except Exception:
            logger.exception("Erro ao gerar comprovante de condicional PDF")
            return None
