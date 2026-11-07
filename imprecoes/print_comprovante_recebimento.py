import io
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

from exceptions import ErroERP
from models.empresa import Empresa
from utils.helpers import formatar_data, formatar_moeda


class PrintComprovanteRecebimento:
    @staticmethod
    def gerar_comprovante(dados, pasta_destino="relatorios"):
        try:
            # Buscar dados da empresa
            empresa = Empresa.buscar()

            # Criar pasta se não existir
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            # Criar nome do arquivo
            data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                pasta_destino, f"comprovante_recebimento_{dados['id']}_{data_atual}.pdf"
            )
            # Configurar documento
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=15 * mm,
                bottomMargin=15 * mm,
            )

            # Definir estilos
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

            estilo_normal_negrito = ParagraphStyle(
                "NormalNegrito",
                parent=styles["Normal"],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
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

            # Logo da empresa
            if hasattr(empresa, "logo") and empresa.logo:
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

            # Informações da empresa
            if hasattr(empresa, "nome") and empresa.nome:
                elements.append(Paragraph(empresa.nome.upper(), estilo_empresa))

            if hasattr(empresa, "cnpj") and empresa.cnpj:
                elements.append(Paragraph(f"CNPJ: {empresa.cnpj}", estilo_normal))

            info_contato = []
            if hasattr(empresa, "endereco") and empresa.endereco:
                info_contato.append(empresa.endereco)
            if hasattr(empresa, "telefone") and empresa.telefone:
                info_contato.append(f"Tel: {empresa.telefone}")
            if hasattr(empresa, "email") and empresa.email:
                info_contato.append(empresa.email)

            if info_contato:
                elements.append(Paragraph(" | ".join(info_contato), estilo_normal))

            elements.append(Spacer(1, 10 * mm))

            # Linha decorativa
            elements.append(
                Table(
                    [[""]],
                    colWidths=[180 * mm],
                    style=[
                        ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#366092")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#366092")),
                    ],
                )
            )

            elements.append(Spacer(1, 10 * mm))

            # Título do comprovante
            elements.append(
                Paragraph(
                    f"COMPROVANTE DE RECEBIMENTO - Nº {dados['id']}", estilo_titulo
                )
            )
            elements.append(Spacer(1, 8 * mm))

            # Dados do comprovante
            comprovante_data = [
                [
                    Paragraph("<b>Nº Comprovante:</b>", estilo_normal_negrito),
                    str(dados["id"]),
                ],
                [
                    Paragraph("<b>Data Emissão:</b>", estilo_normal_negrito),
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                ],
                [
                    Paragraph("<b>Venda Nº:</b>", estilo_normal_negrito),
                    str(dados["venda_id"]),
                ],
                [
                    Paragraph("<b>Data Venda:</b>", estilo_normal_negrito),
                    formatar_data(dados["data_venda"], "%Y-%m-%d", "%d/%m/%Y"),
                ],
            ]

            comprovante_table = Table(comprovante_data, colWidths=[50 * mm, 80 * mm])
            comprovante_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(comprovante_table)
            elements.append(Spacer(1, 10 * mm))

            # Dados do cliente
            elements.append(Paragraph("DADOS DO CLIENTE", estilo_subtitulo))
            elements.append(Spacer(1, 5 * mm))

            cliente_data = [
                [Paragraph(f"<b>Nome:</b> {dados['cliente_nome']}", estilo_normal)],
                [
                    Paragraph(
                        f"<b>CPF/CNPJ:</b> {dados.get('cpf_cnpj') or 'Não informado'}",
                        estilo_normal,
                    )
                ],
                [
                    Paragraph(
                        f"<b>Endereço:</b> {dados.get('endereco') or 'Não informado'}",
                        estilo_normal,
                    )
                ],
            ]

            cliente_table = Table(cliente_data, colWidths=[130 * mm])
            cliente_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8F8F8")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("BOX", (0, 0), (-1, -1), 1, colors.grey),
                    ]
                )
            )
            elements.append(cliente_table)
            elements.append(Spacer(1, 10 * mm))

            # Dados do recebimento
            elements.append(Paragraph("DADOS DO RECEBIMENTO", estilo_subtitulo))
            elements.append(Spacer(1, 5 * mm))

            recebimento_data = [
                ["Descrição", "Valor"],
                ["Parcela Nº", str(dados["numero_parcela"])],
                ["Valor Recebido", formatar_moeda(dados["valor_recebido"])],
                [
                    "Data Vencimento",
                    formatar_data(dados["data_vencimento"], "%Y-%m-%d", "%d/%m/%Y"),
                ],
                [
                    "Data Pagamento",
                    formatar_data(dados["data_pagamento"], "%Y-%m-%d", "%d/%m/%Y"),
                ],
                ["Forma Pagamento", dados.get("forma_pagamento", "Não informada")],
            ]

            recebimento_table = Table(recebimento_data, colWidths=[65 * mm, 65 * mm])
            recebimento_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F8F8F8")],
                        ),
                    ]
                )
            )
            elements.append(recebimento_table)
            elements.append(Spacer(1, 15 * mm))

            # Rodapé
            data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            elements.append(
                Paragraph(
                    "Comprovante gerado automaticamente pelo sistema", estilo_rodape
                )
            )
            elements.append(Paragraph(f"Emitido em: {data_emissao}", estilo_rodape))

            # Gerar PDF
            doc.build(elements)
            return filename

        except Exception as e:
            raise ErroERP(f"Erro ao gerar comprovante: {e!s}") from e
