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

from mainerp.data.database import obter_database
from mainerp.data.models.empresa import Empresa
from mainerp.data.money import de_centavos, para_centavos

logger = logging.getLogger(__name__)


class PrintRelatPedido:
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
    def _formatar_moeda(valor):
        """Formata valor para formato monetário brasileiro"""
        if valor is None:
            valor = 0
        return f"R$ {float(valor):.2f}".replace(".", ",")

    @staticmethod
    def _buscar_pedidos_completos(
        data_inicio=None, data_fim=None, fornecedor_id=None, status=None
    ):
        """Busca pedidos com JOIN explícito para evitar problemas de índice - MÉTODO CORRIGIDO"""
        try:
            db = obter_database()
            conn = db.get_connection()
            cursor = conn.cursor()

            # Query explícita com JOIN para pegar o nome do fornecedor
            query = """
                SELECT
                    p.id,                          -- 0
                    p.fornecedor_id,               -- 1
                    p.data_pedido,                 -- 2
                    p.data_recebimento,            -- 3
                    p.valor_total_centavos,        -- 4
                    p.valor_frete_centavos,        -- 5
                    p.observacao,                  -- 6
                    p.status,                      -- 7
                    COALESCE(p.desconto_centavos, 0) as desconto_centavos,  -- 8
                    f.nome as fornecedor_nome      -- 9
                FROM pedidos p
                LEFT JOIN fornecedores f ON p.fornecedor_id = f.id
                WHERE 1=1
            """
            params = []

            # Aplicar filtros
            if data_inicio:
                query += " AND p.data_pedido >= ?"
                if isinstance(data_inicio, str):
                    try:
                        data_inicio = datetime.strptime(
                            data_inicio, "%d/%m/%Y"
                        ).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        pass
                params.append(data_inicio)

            if data_fim:
                query += " AND p.data_pedido <= ?"
                if isinstance(data_fim, str):
                    try:
                        data_fim = datetime.strptime(data_fim, "%d/%m/%Y").strftime(
                            "%Y-%m-%d"
                        )
                    except (ValueError, TypeError):
                        pass
                params.append(data_fim)

            if fornecedor_id:
                query += " AND p.fornecedor_id = ?"
                params.append(fornecedor_id)

            if status:
                query += " AND p.status = ?"
                params.append(status)

            query += " ORDER BY p.data_pedido DESC, p.id DESC"

            cursor.execute(query, params)
            return [
                (
                    *pedido[:4],
                    float(de_centavos(pedido[4])),
                    float(de_centavos(pedido[5])),
                    *pedido[6:8],
                    float(de_centavos(pedido[8])),
                    *pedido[9:],
                )
                for pedido in cursor.fetchall()
            ]

        except Exception as e:
            logger.error(f"Erro ao buscar pedidos: {e}")
            return []

    @staticmethod
    def gerar_relatorio(pedidos_data, filtros=None, pasta_destino="relatorios"):
        """Gera relatório de pedidos em PDF com cabeçalho da empresa - CORRIGIDO"""
        try:
            empresa = Empresa.buscar()

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(pasta_destino, f"relatorio_pedidos_{timestamp}.pdf")

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

            estilo_observacao = ParagraphStyle(
                "Observacao",
                parent=styles["Normal"],
                fontSize=8,
                spaceAfter=4,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#666666"),
                fontName="Helvetica-Italic",
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

            elements.append(Paragraph("RELATÓRIO DE PEDIDOS", estilo_titulo))
            elements.append(Spacer(1, 4 * mm))

            if filtros:
                if "data_inicio" in filtros and "data_fim" in filtros:
                    elements.append(
                        Paragraph(
                            f"Período: {filtros['data_inicio']} a {filtros['data_fim']}",
                            estilo_filtro,
                        )
                    )

                if "fornecedor" in filtros:
                    elements.append(
                        Paragraph(f"Fornecedor: {filtros['fornecedor']}", estilo_filtro)
                    )

                if "status" in filtros:
                    elements.append(
                        Paragraph(f"Status: {filtros['status']}", estilo_filtro)
                    )

            elements.append(Spacer(1, 6 * mm))

            if pedidos_data:
                # NOVA ESTRUTURA DA TABELA - incluindo desconto
                tabela_dados = [
                    [
                        "ID",
                        "Data Pedido",
                        "Fornecedor",
                        "Status",
                        "Recebimento",
                        "Subtotal",
                        "Desconto",
                        "Frete",
                        "Total",
                    ]
                ]

                total_pedidos_centavos = 0
                total_descontos_centavos = 0
                total_frete_centavos = 0
                pedidos_pendentes = 0
                pedidos_recebidos = 0
                pedidos_cancelados = 0

                for pedido in pedidos_data:
                    # ESTRUTURA CORRIGIDA com índices explícitos:
                    # 0=id, 1=fornecedor_id, 2=data_pedido, 3=data_recebimento, 4=valor_total,
                    # 5=valor_frete, 6=observacao, 7=status, 8=desconto, 9=fornecedor_nome

                    pedido_id = pedido[0]
                    data_pedido = pedido[2]
                    data_recebimento = pedido[3]
                    valor_total = float(pedido[4]) if pedido[4] else 0.0
                    valor_frete = float(pedido[5]) if pedido[5] else 0.0
                    observacao = pedido[6] if pedido[6] else None
                    status = (
                        str(pedido[7]) if pedido[7] else "pendente"
                    )  # CONVERSÃO EXPLÍCITA
                    desconto = (
                        float(pedido[8]) if len(pedido) > 8 and pedido[8] else 0.0
                    )  # NOVO CAMPO
                    fornecedor_nome = pedido[9] if len(pedido) > 9 else "N/A"

                    # Calcular subtotal (valor total + desconto - frete)
                    subtotal_centavos = (
                        para_centavos(valor_total)
                        + para_centavos(desconto)
                        - para_centavos(valor_frete)
                    )
                    subtotal = float(de_centavos(subtotal_centavos))

                    # Contabilizar por status
                    if status.lower() == "pendente":
                        pedidos_pendentes += 1
                    elif status.lower() == "recebido":
                        pedidos_recebidos += 1
                    elif status.lower() == "cancelado":
                        pedidos_cancelados += 1

                    dados = [
                        str(pedido_id),
                        PrintRelatPedido._formatar_data(data_pedido),
                        fornecedor_nome[:50] + "..."
                        if len(fornecedor_nome) > 50
                        else fornecedor_nome,
                        status.upper(),  # Aplicar upper() na string já convertida
                        PrintRelatPedido._formatar_data(data_recebimento)
                        if data_recebimento
                        else "N/A",
                        PrintRelatPedido._formatar_moeda(subtotal),
                        PrintRelatPedido._formatar_moeda(desconto)
                        if desconto > 0
                        else "-",
                        PrintRelatPedido._formatar_moeda(valor_frete)
                        if valor_frete > 0
                        else "-",
                        PrintRelatPedido._formatar_moeda(valor_total),
                    ]

                    total_pedidos_centavos += para_centavos(valor_total)
                    total_descontos_centavos += para_centavos(desconto)
                    total_frete_centavos += para_centavos(valor_frete)
                    tabela_dados.append(dados)

                # Adicionar linha de totais
                tabela_dados.append(
                    [
                        "",
                        "",
                        "",
                        "",
                        "",
                        "TOTAIS:",
                        PrintRelatPedido._formatar_moeda(
                            float(de_centavos(total_descontos_centavos))
                        )
                        if total_descontos_centavos > 0
                        else "-",
                        PrintRelatPedido._formatar_moeda(
                            float(de_centavos(total_frete_centavos))
                        )
                        if total_frete_centavos > 0
                        else "-",
                        PrintRelatPedido._formatar_moeda(
                            float(de_centavos(total_pedidos_centavos))
                        ),
                    ]
                )

                # LARGURAS AJUSTADAS para incluir desconto
                col_widths = [
                    12 * mm,
                    18 * mm,
                    60 * mm,
                    15 * mm,
                    18 * mm,
                    20 * mm,
                    18 * mm,
                    18 * mm,
                    20 * mm,
                ]

                tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

                estilo_tabela = TableStyle(
                    [
                        # Cabeçalho
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        # Alinhamentos das colunas de dados
                        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # ID
                        ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Data
                        ("ALIGN", (2, 1), (2, -1), "LEFT"),  # Fornecedor
                        ("ALIGN", (3, 1), (3, -1), "CENTER"),  # Status
                        ("ALIGN", (4, 1), (4, -1), "CENTER"),  # Recebimento
                        ("ALIGN", (5, 1), (5, -1), "RIGHT"),  # Subtotal
                        ("ALIGN", (6, 1), (6, -1), "RIGHT"),  # Desconto
                        ("ALIGN", (7, 1), (7, -1), "RIGHT"),  # Frete
                        ("ALIGN", (8, 1), (8, -1), "RIGHT"),  # Total
                        # Formatação dos dados
                        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -2), 6),
                        ("TOPPADDING", (0, 1), (-1, -2), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, -2), 2),
                        # Grade
                        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                        # Linhas zebradas
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#F8F8F8")],
                        ),
                        # Linha de totais
                        ("BACKGROUND", (5, -1), (8, -1), colors.HexColor("#E6E6E6")),
                        ("FONTNAME", (5, -1), (8, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (5, -1), (8, -1), 7),
                        ("LINEABOVE", (5, -1), (8, -1), 1, colors.black),
                    ]
                )

                # Destacar status com cores
                for i in range(
                    1, len(tabela_dados) - 1
                ):  # Excluir cabeçalho e linha de totais
                    pedido_status = tabela_dados[i][3].lower()
                    if "recebido" in pedido_status:
                        estilo_tabela.add("TEXTCOLOR", (3, i), (3, i), colors.green)
                    elif "cancelado" in pedido_status:
                        estilo_tabela.add("TEXTCOLOR", (3, i), (3, i), colors.red)
                    elif "pendente" in pedido_status:
                        estilo_tabela.add("TEXTCOLOR", (3, i), (3, i), colors.orange)

                # Destacar desconto em vermelho se houver
                for i in range(1, len(tabela_dados) - 1):
                    if tabela_dados[i][6] != "-":  # Se tem desconto
                        estilo_tabela.add("TEXTCOLOR", (6, i), (6, i), colors.red)

                tabela.setStyle(estilo_tabela)
                elements.append(tabela)

                elements.append(Spacer(1, 4 * mm))

                # RESUMO ESTATÍSTICO ATUALIZADO
                valor_produtos = float(
                    de_centavos(
                        total_pedidos_centavos
                        + total_descontos_centavos
                        - total_frete_centavos
                    )
                )
                total_pedidos = float(de_centavos(total_pedidos_centavos))
                total_descontos = float(de_centavos(total_descontos_centavos))
                total_frete = float(de_centavos(total_frete_centavos))

                resumo_texto = f"""
                Total de pedidos: {len(pedidos_data)} |
                Pendentes: {pedidos_pendentes} |
                Recebidos: {pedidos_recebidos} |
                Cancelados: {pedidos_cancelados}
                """
                elements.append(Paragraph(resumo_texto, estilo_normal_negrito))

                resumo_financeiro = f"""
                Valor dos produtos: {PrintRelatPedido._formatar_moeda(valor_produtos)} |
                Total descontos: {PrintRelatPedido._formatar_moeda(total_descontos)} |
                Total frete: {PrintRelatPedido._formatar_moeda(total_frete)} |
                Valor total: {PrintRelatPedido._formatar_moeda(total_pedidos)}
                """
                elements.append(Paragraph(resumo_financeiro, estilo_normal_negrito))

                # Adicionar observações se houver
                tem_observacoes = False
                for pedido in pedidos_data:
                    observacao = pedido[6] if len(pedido) > 6 and pedido[6] else None
                    if observacao:
                        if not tem_observacoes:
                            elements.append(Spacer(1, 6 * mm))
                            elements.append(
                                Paragraph("OBSERVAÇÕES:", estilo_normal_negrito)
                            )
                            tem_observacoes = True

                        fornecedor_nome = (
                            pedido[9] if len(pedido) > 9 else f"Pedido #{pedido[0]}"
                        )
                        elements.append(
                            Paragraph(
                                f"• {fornecedor_nome}: {observacao}", estilo_observacao
                            )
                        )

            else:
                elements.append(
                    Paragraph(
                        "Nenhum pedido encontrado para os filtros aplicados.",
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
            logger.info(f"Relatório de pedidos gerado: {filename}")
            return filename

        except Exception:
            logger.exception("Erro ao gerar relatório de pedidos PDF")
            return None

    @staticmethod
    def gerar_relatorio_por_periodo(
        data_inicio,
        data_fim,
        fornecedor_id=None,
        status=None,
        pasta_destino="relatorios",
    ):
        """Gera relatório filtrado por período - MÉTODO CORRIGIDO"""
        try:
            # Usar o método corrigido de busca
            pedidos_data = PrintRelatPedido._buscar_pedidos_completos(
                data_inicio, data_fim, fornecedor_id, status
            )

            filtros = {"data_inicio": data_inicio, "data_fim": data_fim}

            if fornecedor_id:
                try:
                    conn = obter_database().get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT nome FROM fornecedores WHERE id = ?", (fornecedor_id,)
                    )
                    fornecedor = cursor.fetchone()
                    if fornecedor:
                        filtros["fornecedor"] = fornecedor[0]
                except Exception as e:
                    logger.error(f"Erro ao buscar nome do fornecedor: {e}")

            if status:
                filtros["status"] = status.upper()

            return PrintRelatPedido.gerar_relatorio(
                pedidos_data, filtros, pasta_destino
            )

        except Exception as e:
            logger.error(f"Erro ao gerar relatório por período: {e}")
            return None
