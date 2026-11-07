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


class PrintRelatCondicional:
    HEADER_BG_COLOR = colors.HexColor("#366092")
    LIGHT_BG_COLOR = colors.HexColor("#F2F2F2")
    ZEBRA_BG_COLOR = colors.HexColor("#F8F8F8")

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
    def _buscar_condicionais_com_cliente():
        """Busca condicionais com JOIN para incluir o nome do cliente e contar itens"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Query com JOIN para trazer o nome do cliente e contar itens
            cursor.execute("""
                SELECT
                    c.id,
                    c.cliente_id,
                    c.data_condicional,
                    c.data_prevista_devolucao,
                    c.status,
                    c.observacao,
                    c.desconto,
                    COALESCE(cl.nome, 'Cliente não informado') as nome_cliente,
                    COUNT(ic.id) as total_itens
                FROM condicionais c
                LEFT JOIN clientes cl ON c.cliente_id = cl.id
                LEFT JOIN itens_condicional ic ON c.id = ic.condicional_id
                GROUP BY c.id, c.cliente_id, c.data_condicional, c.data_prevista_devolucao,
                         c.status, c.observacao, c.desconto, cl.nome
                ORDER BY c.id DESC
            """)

            condicionais = cursor.fetchall()
            conn.close()
            return condicionais

        except Exception as e:
            logger.error(f"Erro ao buscar condicionais com cliente: {e}")
            return []

    @staticmethod
    def _calcular_total_condicional(condicional_id):
        """Calcula o total de uma condicional"""
        try:
            conn = Database().get_connection()
            cursor = conn.cursor()

            # Buscar todos os itens da condicional
            cursor.execute(
                """
                SELECT quantidade, preco_unitario
                FROM itens_condicional
                WHERE condicional_id = ?
            """,
                (condicional_id,),
            )

            itens = cursor.fetchall()
            conn.close()

            total = 0
            for item in itens:
                quantidade = item[0] or 0
                preco_unitario = item[1] or 0
                total += quantidade * preco_unitario

            return total

        except Exception as e:
            logger.error(f"Erro ao calcular total da condicional {condicional_id}: {e}")
            return 0

    @staticmethod
    def gerar_relatorio(condicionais_data, filtros=None, pasta_destino="relatorios"):
        """Gera relatório de condicionais em PDF com cabeçalho da empresa"""
        try:
            empresa = Empresa.buscar()

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                pasta_destino, f"relatorio_condicionais_{timestamp}.pdf"
            )

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
                fontSize=14,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black,
            )

            estilo_titulo = ParagraphStyle(
                "Titulo",
                parent=styles["Heading2"],
                fontSize=12,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#366092"),
            )

            estilo_filtro = ParagraphStyle(
                "Filtro",
                parent=styles["Normal"],
                fontSize=9,
                spaceAfter=3,
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

            # Logo da empresa
            if empresa and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((50, 50))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format="PNG")
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=35, height=35)
                    logo.hAlign = "CENTER"
                    elements.append(logo)
                    elements.append(Spacer(1, 2 * mm))
                except Exception as e:
                    logger.error(f"Erro ao processar logo: {e}")

            # Nome da empresa
            nome_empresa = (
                empresa.nome.upper() if empresa and empresa.nome else "NOME DA EMPRESA"
            )
            elements.append(Paragraph(nome_empresa, estilo_empresa))

            # CNPJ
            if empresa and empresa.cnpj:
                elements.append(Paragraph(f"CNPJ: {empresa.cnpj}", estilo_normal))

            # Informações de contato
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

            # Linha separadora
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

            # Título do relatório
            elements.append(Paragraph("RELATÓRIO DE CONDICIONAIS", estilo_titulo))
            elements.append(Spacer(1, 4 * mm))

            # Filtros aplicados
            if filtros:
                filtros_texto = []

                if filtros.get("data_inicio") and filtros.get("data_fim"):
                    filtros_texto.append(
                        f"Período: {filtros['data_inicio']} a {filtros['data_fim']}"
                    )

                if filtros.get("cliente_nome"):
                    filtros_texto.append(f"Cliente: {filtros['cliente_nome']}")

                if filtros.get("status") and filtros["status"] != "todos":
                    status_texto = {
                        "ativas": "Ativas",
                        "convertidas": "Convertidas",
                        "devolvidas": "Devolvidas",
                    }.get(filtros["status"].lower(), filtros["status"].capitalize())
                    filtros_texto.append(f"Status: {status_texto}")

                # Adicionar filtros ao relatório
                for filtro_linha in filtros_texto:
                    elements.append(Paragraph(filtro_linha, estilo_filtro))

            elements.append(Spacer(1, 6 * mm))

            # Tabela de dados
            if condicionais_data:
                tabela_dados = [
                    [
                        "ID",
                        "Data",
                        "Cliente",
                        "Prev. Devolução",
                        "Itens",
                        "Valor Total",
                        "Status",
                    ]
                ]

                total_valor = 0
                total_itens = 0

                for condicional_data in condicionais_data:
                    try:
                        # CORREÇÃO: Usar índices corretos da query reorganizada
                        condicional_id = condicional_data[0]  # id
                        data_condicional = condicional_data[2]  # data_condicional
                        data_prevista = condicional_data[3]  # data_prevista_devolucao
                        status = condicional_data[4]  # status
                        desconto = condicional_data[6]  # desconto
                        nome_cliente = condicional_data[7]  # nome_cliente
                        qtd_itens = condicional_data[8]  # total_itens

                        # Calcular total da condicional
                        total_bruto = PrintRelatCondicional._calcular_total_condicional(
                            condicional_id
                        )
                        total_liquido = total_bruto - (desconto or 0)

                        total_valor += total_liquido
                        total_itens += qtd_itens or 0

                        # Formatar data prevista
                        if data_prevista:
                            data_prevista_fmt = PrintRelatCondicional._formatar_data(
                                data_prevista
                            )
                        else:
                            data_prevista_fmt = "Não definida"

                        # Preparar dados da linha
                        dados = [
                            str(condicional_id),
                            PrintRelatCondicional._formatar_data(data_condicional),
                            str(nome_cliente)
                            if nome_cliente
                            else "Cliente não informado",
                            data_prevista_fmt,
                            str(qtd_itens or 0),
                            f"R$ {total_liquido:.2f}",
                            str(status).capitalize() if status else "Ativa",
                        ]

                        tabela_dados.append(dados)

                    except Exception as e:
                        logger.error(
                            f"Erro ao processar condicional {condicional_data}: {e}"
                        )
                        continue

                # Linha de total
                tabela_dados.append(
                    [
                        "",
                        "",
                        "",
                        "",
                        f"TOTAL: {total_itens}",
                        f"R$ {total_valor:.2f}",
                        "",
                    ]
                )

                # Configurar larguras das colunas
                col_widths = [
                    15 * mm,
                    20 * mm,
                    70 * mm,
                    25 * mm,
                    15 * mm,
                    25 * mm,
                    20 * mm,
                ]

                # Criar tabela
                tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

                # Estilo da tabela
                estilo_tabela = TableStyle(
                    [
                        # Cabeçalho
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#366092")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                        # Alinhamentos das colunas de dados
                        ("ALIGN", (0, 1), (0, -1), "CENTER"),  # ID
                        ("ALIGN", (1, 1), (1, -1), "CENTER"),  # Data
                        ("ALIGN", (2, 1), (2, -1), "LEFT"),  # Cliente
                        ("ALIGN", (3, 1), (3, -1), "CENTER"),  # Prev. Devolução
                        ("ALIGN", (4, 1), (4, -1), "CENTER"),  # Itens
                        ("ALIGN", (5, 1), (5, -1), "RIGHT"),  # Valor Total
                        ("ALIGN", (6, 1), (6, -1), "CENTER"),  # Status
                        # Fonte e tamanho dos dados
                        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -2), 7),
                        ("TOPPADDING", (0, 1), (-1, -2), 2),
                        ("BOTTOMPADDING", (0, 1), (-1, -2), 2),
                        # Bordas
                        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                        # Cores alternadas nas linhas
                        (
                            "ROWBACKGROUNDS",
                            (1, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#F8F8F8")],
                        ),
                        # Formatação da linha de total
                        ("BACKGROUND", (4, -1), (5, -1), colors.HexColor("#E6E6E6")),
                        ("FONTNAME", (4, -1), (5, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (4, -1), (5, -1), 8),
                        ("LINEABOVE", (4, -1), (5, -1), 1, colors.black),
                    ]
                )

                tabela.setStyle(estilo_tabela)
                elements.append(tabela)

                # Resumo
                elements.append(Spacer(1, 4 * mm))
                elements.append(
                    Paragraph(
                        f"Total de condicionais: {len(condicionais_data)} | Itens: {total_itens} | Valor total: R$ {total_valor:,.2f}",
                        estilo_normal_negrito,
                    )
                )
            else:
                elements.append(
                    Paragraph(
                        "Nenhuma condicional encontrada para os filtros aplicados.",
                        estilo_normal,
                    )
                )

            # Rodapé
            elements.append(Spacer(1, 8 * mm))
            elements.append(
                Paragraph(
                    f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    estilo_rodape,
                )
            )

            # Gerar PDF
            doc.build(elements)
            logger.info(f"Relatório de condicionais gerado: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de condicionais PDF: {e}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def gerar_relatorio_por_periodo(
        data_inicio,
        data_fim,
        status_filtro=None,
        cliente_id=None,
        pasta_destino="relatorios",
    ):
        """Gera relatório filtrado por período - VERSÃO CORRIGIDA"""
        try:
            # Buscar todas as condicionais com dados do cliente
            todas_condicionais = (
                PrintRelatCondicional._buscar_condicionais_com_cliente()
            )

            # Converter datas para comparação
            data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y").date()
            data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y").date()

            condicionais_filtradas = []

            for condicional in todas_condicionais:
                try:
                    # Índice 2 = data_condicional
                    condicional_data = condicional[2]

                    # Converter data da condicional para objeto date
                    if isinstance(condicional_data, str):
                        try:
                            condicional_data_dt = datetime.strptime(
                                condicional_data, "%Y-%m-%d"
                            ).date()
                        except ValueError:
                            logger.warning(
                                f"Data inválida para condicional {condicional[0]}: {condicional_data}"
                            )
                            continue
                    elif hasattr(condicional_data, "date"):
                        condicional_data_dt = condicional_data.date()
                    else:
                        condicional_data_dt = condicional_data

                    # FILTRO POR DATA
                    if (
                        condicional_data_dt < data_inicio_dt
                        or condicional_data_dt > data_fim_dt
                    ):
                        continue

                    # FILTRO POR STATUS
                    if status_filtro and status_filtro != "todos":
                        # Índice 4 = status
                        status_condicional = (
                            str(condicional[4]).lower() if condicional[4] else "ativa"
                        )

                        if (
                            status_filtro == "ativas"
                            and status_condicional != "ativa"
                            or status_filtro == "convertidas"
                            and status_condicional != "convertida"
                            or status_filtro == "devolvidas"
                            and status_condicional != "devolvida"
                        ):
                            continue

                    # FILTRO POR CLIENTE
                    if cliente_id:
                        # Índice 1 = cliente_id
                        if condicional[1] != cliente_id:
                            continue

                    # Se passou por todos os filtros, adicionar à lista
                    condicionais_filtradas.append(condicional)

                except Exception as e:
                    logger.error(
                        f"Erro ao processar filtros para condicional {condicional[0] if len(condicional) > 0 else 'unknown'}: {e}"
                    )
                    continue

            # Preparar informações de filtros para exibição no relatório
            filtros = {"data_inicio": data_inicio, "data_fim": data_fim}

            # Adicionar status aos filtros se não for "todos"
            if status_filtro and status_filtro != "todos":
                filtros["status"] = status_filtro

            # Buscar nome do cliente se filtro aplicado
            if cliente_id:
                try:
                    conn = Database().get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT nome FROM clientes WHERE id = ?", (cliente_id,)
                    )
                    cliente = cursor.fetchone()
                    if cliente:
                        filtros["cliente_nome"] = cliente[0]
                    conn.close()
                except Exception as e:
                    logger.error(f"Erro ao buscar nome do cliente {cliente_id}: {e}")

            logger.info(
                f"Condicionais filtradas: {len(condicionais_filtradas)} de {len(todas_condicionais)} total"
            )

            # Gerar relatório com dados filtrados
            return PrintRelatCondicional.gerar_relatorio(
                condicionais_filtradas, filtros, pasta_destino
            )

        except Exception as e:
            logger.error(f"Erro ao gerar relatório por período: {e}")
            import traceback

            traceback.print_exc()
            return None
