import io
import logging
import os
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrintRelatVenda:
    HEADER_BG_COLOR = colors.HexColor("#366092")
    LIGHT_BG_COLOR = colors.HexColor("#F2F2F2")
    ZEBRA_BG_COLOR = colors.HexColor("#F8F8F8")
    TEXT_COLOR = colors.black
    SECONDARY_TEXT_COLOR = colors.HexColor("#666666")

    @staticmethod
    def _formatar_data(data):
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
    def _buscar_vendas_com_cliente():
        """Busca vendas com JOIN para incluir o nome do cliente"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Query com JOIN para trazer o nome do cliente
            cursor.execute("""
                SELECT
                    v.id,
                    v.cliente_id,
                    v.data_venda,
                    v.total,
                    v.forma_pagamento,
                    v.status,
                    v.parcelas,
                    v.desconto,
                    COALESCE(c.nome, 'Cliente não informado') as nome_cliente
                FROM vendas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                ORDER BY v.id DESC
            """)

            vendas = cursor.fetchall()
            conn.close()
            return vendas

        except Exception as e:
            logger.error(f"Erro ao buscar vendas com cliente: {e}")
            return []

    @staticmethod
    def gerar_relatorio(vendas_data, filtros=None, pasta_destino="relatorios"):
        """Gera relatório de vendas em PDF com cabeçalho da empresa"""
        try:
            empresa = Empresa.buscar()

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(pasta_destino, f"relatorio_vendas_{timestamp}.pdf")

            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(A4),
                rightMargin=10 * mm,
                leftMargin=10 * mm,
                topMargin=10 * mm,
                bottomMargin=10 * mm,
            )

            styles = getSampleStyleSheet()

            estilo_empresa = ParagraphStyle(
                "Empresa",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black,
            )

            estilo_titulo = ParagraphStyle(
                "Titulo",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#366092"),
            )

            estilo_filtro = ParagraphStyle(
                "Filtro",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName="Helvetica-Bold",
            )

            estilo_normal = ParagraphStyle(
                "Normal",
                parent=styles["Normal"],
                fontSize=8,
                spaceAfter=2,
                alignment=TA_LEFT,
            )

            estilo_normal_negrito = ParagraphStyle(
                "NormalNegrito",
                parent=styles["Normal"],
                fontSize=8,
                spaceAfter=2,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )

            estilo_rodape = ParagraphStyle(
                "Rodape",
                parent=styles["Normal"],
                fontSize=7,
                spaceAfter=0,
                alignment=TA_CENTER,
                textColor=colors.grey,
            )

            elements = []

            if empresa and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((60, 60))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format="PNG")
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=40, height=40)
                    logo.hAlign = "CENTER"
                    elements.append(logo)
                    elements.append(Spacer(1, 2 * mm))
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

            elements.append(Spacer(1, 4 * mm))

            elements.append(
                Table(
                    [[""]],
                    colWidths=[270 * mm],
                    style=[
                        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#366092")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#366092")),
                    ],
                )
            )

            elements.append(Spacer(1, 4 * mm))

            elements.append(Paragraph("RELATÓRIO DE VENDAS", estilo_titulo))
            elements.append(Spacer(1, 4 * mm))

            if filtros:
                if "data_inicio" in filtros and "data_fim" in filtros:
                    elements.append(
                        Paragraph(
                            f"Período: {filtros['data_inicio']} a {filtros['data_fim']}",
                            estilo_filtro,
                        )
                    )

                if "cliente" in filtros:
                    elements.append(
                        Paragraph(f"Cliente: {filtros['cliente']}", estilo_filtro)
                    )

            elements.append(Spacer(1, 6 * mm))

            if vendas_data:
                tabela_dados = [
                    [
                        "ID",
                        "Data",
                        "Cliente",
                        "Pagamento",
                        "Parcelas",
                        "Desconto",
                        "Total",
                    ]
                ]

                total_vendas = 0

                for venda in vendas_data:
                    # CORREÇÃO: Agora o nome do cliente está garantido no índice 8
                    dados = [
                        str(venda[0]),  # ID
                        PrintRelatVenda._formatar_data(venda[2]),  # Data
                        str(venda[8])
                        if venda[8]
                        else "Cliente não informado",  # Nome do Cliente
                        str(venda[4]) if venda[4] else "N/A",  # Forma de Pagamento
                        str(venda[6]) if venda[6] else "1",  # Parcelas
                        f"R$ {venda[7]:.2f}" if venda[7] else "R$ 0,00",  # Desconto
                        f"R$ {venda[3]:.2f}" if venda[3] else "R$ 0,00",  # Total
                    ]

                    total_vendas += venda[3] if venda[3] else 0
                    tabela_dados.append(dados)

                tabela_dados.append(
                    ["", "", "", "", "TOTAL:", f"R$ {total_vendas:.2f}", ""]
                )

                col_widths = [
                    15 * mm,
                    20 * mm,
                    70 * mm,
                    25 * mm,
                    15 * mm,
                    20 * mm,
                    20 * mm,
                ]

                tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

                estilo_tabela = TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        ("ALIGN", (0, 1), (0, -1), "CENTER"),
                        ("ALIGN", (1, 1), (1, -1), "CENTER"),
                        ("ALIGN", (2, 1), (2, -1), "LEFT"),
                        ("ALIGN", (3, 1), (3, -1), "LEFT"),
                        ("ALIGN", (4, 1), (4, -1), "CENTER"),
                        ("ALIGN", (5, 1), (6, -1), "RIGHT"),
                        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -2), 7),
                        ("TOPPADDING", (0, 1), (-1, -2), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, -2), 2),
                        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (1, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#F8F8F8")],
                        ),
                        ("BACKGROUND", (4, -1), (5, -1), colors.HexColor("#E6E6E6")),
                        ("FONTNAME", (4, -1), (5, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (4, -1), (5, -1), 8),
                        ("LINEABOVE", (4, -1), (5, -1), 1, colors.black),
                    ]
                )

                tabela.setStyle(estilo_tabela)
                elements.append(tabela)

                elements.append(Spacer(1, 4 * mm))
                elements.append(
                    Paragraph(
                        f"Total de vendas: {len(vendas_data)} | Valor total: R$ {total_vendas:,.2f}",
                        estilo_normal_negrito,
                    )
                )
            else:
                elements.append(
                    Paragraph(
                        "Nenhuma venda encontrada para os filtros aplicados.",
                        estilo_normal,
                    )
                )

            elements.append(Spacer(1, 8 * mm))

            elements.append(
                Paragraph(
                    f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    estilo_rodape,
                )
            )

            doc.build(elements)
            logger.info(f"Relatório de vendas gerado: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de vendas PDF: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def gerar_relatorio_por_periodo(
        data_inicio,
        data_fim,
        cliente_id=None,
        status=None,
        forma_pagamento=None,
        pasta_destino="relatorios",
    ):
        """Gera relatório filtrado por período e outros filtros"""
        try:
            todas_vendas = PrintRelatVenda._buscar_vendas_com_cliente()

            data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y").date()
            data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y").date()

            vendas_filtradas = []
            for venda in todas_vendas:
                venda_data = venda[2]

                if isinstance(venda_data, str):
                    try:
                        venda_data = datetime.strptime(venda_data, "%Y-%m-%d").date()
                    except Exception:
                        continue

                # Filtro por data
                if venda_data < data_inicio_dt or venda_data > data_fim_dt:
                    continue

                # Filtro por cliente
                if cliente_id and venda[1] != cliente_id:
                    continue

                # Filtro por status (índice 5 na query)
                if status and venda[5] != status:
                    continue

                # Filtro por forma de pagamento (índice 4 na query)
                if forma_pagamento and venda[4] != forma_pagamento:
                    continue

                vendas_filtradas.append(venda)

            filtros = {"data_inicio": data_inicio, "data_fim": data_fim}

            if cliente_id:
                # Buscar nome do cliente para os filtros
                conn = Database().get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT nome FROM clientes WHERE id = ?", (cliente_id,))
                cliente = cursor.fetchone()
                if cliente:
                    filtros["cliente"] = cliente[0]
                conn.close()

            # Adicionar outros filtros
            if status:
                filtros["status"] = status
            if forma_pagamento:
                filtros["forma_pagamento"] = forma_pagamento

            return PrintRelatVenda.gerar_relatorio(
                vendas_filtradas, filtros, pasta_destino
            )

        except Exception as e:
            logger.error(f"Erro ao gerar relatório por período: {e}")
            import traceback

            traceback.print_exc()
            return None
