import os
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from PIL import Image as PILImage

from database import Database
from utils.helpers import formatar_moeda, formatar_data, validar_data
from models.empresa import Empresa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrintRelatRecebimento:
    HEADER_BG_COLOR = colors.HexColor("#366092")
    LIGHT_BG_COLOR = colors.HexColor("#F2F2F2")
    ZEBRA_BG_COLOR = colors.HexColor("#F8F8F8")
    TEXT_COLOR = colors.black
    SECONDARY_TEXT_COLOR = colors.HexColor("#666666")

    @staticmethod
    def _formatar_data(data, formato_entrada='%Y-%m-%d'):
        if not data:
            return "N/A"

        try:
            if isinstance(data, str):
                data_obj = datetime.strptime(data, formato_entrada)
                return data_obj.strftime('%d/%m/%Y')
            else:
                return data.strftime('%d/%m/%Y')
        except (ValueError, AttributeError):
            return "Data inválida"

    @staticmethod
    def gerar_relatorio(data_inicio_str, data_fim_str, status_filtro, cliente_id=None, pasta_destino='relatorios'):
        try:
            empresa = Empresa.buscar()

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            # Buscar dados filtrados
            conn = Database().get_connection()
            cursor = conn.cursor()

            duplicatas = []

            # Query para duplicatas abertas
            if status_filtro in ["Abertas", "Vencidas", "Todas"]:
                query_abertas = '''
                    SELECT
                        d.id, d.venda_id, d.cliente_id, d.numero_parcela,
                        d.valor_parcela, d.data_vencimento, d.data_pagamento,
                        d.status, c.nome as cliente_nome, v.data_venda,
                        v.forma_pagamento, v.total as venda_total
                    FROM duplicatas d
                    LEFT JOIN clientes c ON d.cliente_id = c.id
                    LEFT JOIN vendas v ON d.venda_id = v.id
                    WHERE d.status = 'aberto'
                '''

                # Construir condições para duplicatas abertas
                conditions_abertas = []
                params_abertas = []

                # Aplicar filtros de data (para abertas, usar data_vencimento)
                if data_inicio_str and validar_data(data_inicio_str):
                    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
                    conditions_abertas.append("d.data_vencimento >= ?")
                    params_abertas.append(data_inicio.strftime("%Y-%m-%d"))

                if data_fim_str and validar_data(data_fim_str):
                    data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()
                    conditions_abertas.append("d.data_vencimento <= ?")
                    params_abertas.append(data_fim.strftime("%Y-%m-%d"))

                # Aplicar filtro de cliente
                if cliente_id:
                    conditions_abertas.append("d.cliente_id = ?")
                    params_abertas.append(cliente_id)

                # Aplicar filtro específico para vencidas
                if status_filtro == "Vencidas":
                    conditions_abertas.append("d.data_vencimento < date('now')")

                # Adicionar condições à query
                if conditions_abertas:
                    query_abertas += " AND " + " AND ".join(conditions_abertas)

                query_abertas += " ORDER BY d.data_vencimento, c.nome, d.numero_parcela"

                try:
                    cursor.execute(query_abertas, params_abertas)
                    duplicatas_abertas = cursor.fetchall()
                    duplicatas.extend(duplicatas_abertas)
                except Exception as e:
                    logger.error(f"Erro ao buscar duplicatas abertas: {e}")

            # Query para duplicatas pagas
            if status_filtro in ["Pagas", "Todas"]:
                query_pagas = '''
                    SELECT
                        dp.id, dp.venda_id, dp.cliente_id, dp.numero_parcela,
                        dp.valor_original, dp.valor_recebido, dp.data_vencimento,
                        dp.data_pagamento, dp.forma_pagamento,
                        c.nome as cliente_nome, c.cpf_cnpj, c.endereco,
                        v.total as venda_total, v.data_venda,
                        'pago' as status
                    FROM duplicatas_pagas dp
                    LEFT JOIN clientes c ON dp.cliente_id = c.id
                    LEFT JOIN vendas v ON dp.venda_id = v.id
                    WHERE 1=1
                '''

                # Construir condições para duplicatas pagas
                conditions_pagas = []
                params_pagas = []

                # Aplicar filtros de data (para pagas, usar data_pagamento)
                if data_inicio_str and validar_data(data_inicio_str):
                    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
                    conditions_pagas.append("dp.data_pagamento >= ?")
                    params_pagas.append(data_inicio.strftime("%Y-%m-%d"))

                if data_fim_str and validar_data(data_fim_str):
                    data_fim = datetime.strptime(data_fim_str, "%d/%m/%Y").date()
                    conditions_pagas.append("dp.data_pagamento <= ?")
                    params_pagas.append(data_fim.strftime("%Y-%m-%d"))

                # Aplicar filtro de cliente
                if cliente_id:
                    conditions_pagas.append("dp.cliente_id = ?")
                    params_pagas.append(cliente_id)

                # Adicionar condições à query
                if conditions_pagas:
                    query_pagas += " AND " + " AND ".join(conditions_pagas)

                query_pagas += " ORDER BY dp.data_pagamento DESC, c.nome, dp.numero_parcela"

                try:
                    cursor.execute(query_pagas, params_pagas)
                    duplicatas_pagas = cursor.fetchall()
                    duplicatas.extend(duplicatas_pagas)
                except Exception as e:
                    logger.error(f"Erro ao buscar duplicatas pagas: {e}")

            conn.close()

            # Ordenar resultados finais
            if duplicatas:
                duplicatas = list(duplicatas)
                duplicatas.sort(key=lambda x: (
                    # Usar data de vencimento para abertas e data de pagamento para pagas
                    datetime.strptime(x[7] if len(x) > 14 and x[7] else x[5], "%Y-%m-%d").date()
                    if (len(x) > 14 and x[7]) or (len(x) <= 14 and x[5]) else datetime.min.date(),
                    x[9] if len(x) > 9 else "",  # nome do cliente
                    x[3] if len(x) > 3 else 0    # número da parcela
                ))

            # Criar nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(pasta_destino, f"relatorio_recebimentos_{timestamp}.pdf")

            # Criar documento em landscape
            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(A4),
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )

            styles = getSampleStyleSheet()

            # Definir estilos (mantidos os mesmos)
            estilo_empresa = ParagraphStyle(
                'Empresa',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black
            )

            estilo_titulo = ParagraphStyle(
                'Titulo',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#366092')
            )

            estilo_filtro = ParagraphStyle(
                'Filtro',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            )

            estilo_normal = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=8,
                spaceAfter=2,
                alignment=TA_LEFT
            )

            estilo_rodape = ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=7,
                spaceAfter=0,
                alignment=TA_CENTER,
                textColor=colors.grey
            )

            elements = []

            # Logo e informações da empresa (mantido o mesmo)
            if empresa and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((60, 60))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format='PNG')
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=40, height=40)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 2*mm))
                except Exception as e:
                    logger.error(f"Erro ao processar logo: {e}")

            nome_empresa = empresa.nome.upper() if empresa and empresa.nome else "NOME DA EMPRESA"
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

            elements.append(Spacer(1, 4*mm))

            # Linha decorativa
            elements.append(Table(
                [['']],
                colWidths=[270*mm],
                style=[
                    ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#366092')),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#366092')),
                ]
            ))

            elements.append(Spacer(1, 4*mm))

            # Título do relatório
            titulo_texto = "RELATÓRIO DE RECEBIMENTOS"
            if status_filtro != "Todas":
                titulo_texto += f" - {status_filtro.upper()}"
            elements.append(Paragraph(titulo_texto, estilo_titulo))
            elements.append(Spacer(1, 4*mm))

            # Filtros aplicados
            filtros_texto = []
            if status_filtro:
                filtros_texto.append(f"Status: {status_filtro}")

            if data_inicio_str and data_fim_str:
                filtros_texto.append(f"Período: {data_inicio_str} a {data_fim_str}")
            elif data_inicio_str:
                filtros_texto.append(f"A partir de: {data_inicio_str}")
            elif data_fim_str:
                filtros_texto.append(f"Até: {data_fim_str}")

            if cliente_id:
                # Buscar nome do cliente
                try:
                    conn = Database().get_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT nome FROM clientes WHERE id = ?', (cliente_id,))
                    cliente = cursor.fetchone()
                    conn.close()
                    if cliente:
                        filtros_texto.append(f"Cliente: {cliente[0]}")
                except Exception as e:
                    logger.error(f"Erro ao buscar nome do cliente: {e}")

            if filtros_texto:
                elements.append(Paragraph(" | ".join(filtros_texto), estilo_filtro))

            elements.append(Spacer(1, 6*mm))

            if not duplicatas:
                elements.append(Paragraph("Nenhuma duplicata encontrada com os filtros aplicados.", estilo_normal))
            else:
                # Preparar dados da tabela
                table_data = [['ID', 'Venda', 'Cliente', 'Parcela', 'Valor R$', 'Vencimento',
                            'Pagamento', 'Status', 'Forma Pagto']]

                total_abertas = 0
                total_pagas = 0

                for dup in duplicatas:
                    # Verificar se é duplicata paga (tem mais campos)
                    is_paga = len(dup) > 14

                    if is_paga:
                        # Duplicata paga
                        valor = float(dup[5]) if dup[5] else 0  # valor_recebido
                        status = "Pago"
                        total_pagas += valor
                        forma_pagamento = dup[8] if dup[8] else 'N/A'
                        data_pagamento = dup[7]
                        data_vencimento = dup[6]
                        cliente_nome = dup[9]
                    else:
                        # Duplicata aberta
                        valor = float(dup[4]) if dup[4] else 0  # valor_parcela
                        status = "Aberto"
                        total_abertas += valor
                        forma_pagamento = dup[10] if len(dup) > 10 and dup[10] else 'N/A'
                        data_pagamento = dup[6]
                        data_vencimento = dup[5]
                        cliente_nome = dup[8]

                    table_data.append([
                        str(dup[0]),  # ID
                        str(dup[1]),  # Venda ID
                        (cliente_nome[:50] + '...') if cliente_nome and len(cliente_nome) > 50 else (cliente_nome or 'N/A'),
                        str(dup[3]) if len(dup) > 3 else 'N/A',  # Parcela
                        formatar_moeda(valor),
                        PrintRelatRecebimento._formatar_data(data_vencimento) if data_vencimento else 'N/A',
                        PrintRelatRecebimento._formatar_data(data_pagamento) if data_pagamento else 'N/A',
                        status,
                        forma_pagamento
                    ])

                # Definir larguras das colunas
                col_widths = [10*mm, 10*mm, 70*mm, 12*mm, 20*mm, 20*mm, 20*mm, 15*mm, 25*mm]

                # Criar tabela
                table = Table(table_data, colWidths=col_widths, repeatRows=1)

                # Estilo da tabela
                estilo_tabela = TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 8),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),

                    ('ALIGN', (0,1), (0,-1), 'CENTER'),  # ID
                    ('ALIGN', (1,1), (1,-1), 'CENTER'),  # Venda
                    ('ALIGN', (2,1), (2,-1), 'LEFT'),    # Cliente
                    ('ALIGN', (3,1), (3,-1), 'CENTER'),  # Parcela
                    ('ALIGN', (4,1), (4,-1), 'RIGHT'),   # Valor
                    ('ALIGN', (5,1), (6,-1), 'CENTER'),  # Datas
                    ('ALIGN', (7,1), (7,-1), 'CENTER'),  # Status
                    ('ALIGN', (8,1), (8,-1), 'LEFT'),    # Forma Pagto

                    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('TOPPADDING', (0,1), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,1), (-1,-1), 2),

                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F8F8')]),
                ])

                table.setStyle(estilo_tabela)
                elements.append(table)

                elements.append(Spacer(1, 4*mm))

                # Totais
                totais_style = ParagraphStyle(
                    'Totais',
                    parent=estilo_normal,
                    fontSize=9,
                    spaceAfter=2,
                    fontName='Helvetica-Bold'
                )

                elements.append(Paragraph(f"Total em Aberto: {formatar_moeda(total_abertas)}", totais_style))
                elements.append(Paragraph(f"Total Recebido: {formatar_moeda(total_pagas)}", totais_style))
                elements.append(Paragraph(f"Total Geral: {formatar_moeda(total_abertas + total_pagas)}", totais_style))
                elements.append(Paragraph(f"Quantidade de Registros: {len(duplicatas)}", totais_style))

            elements.append(Spacer(1, 8*mm))

            # Rodapé
            elements.append(Paragraph(
                f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                estilo_rodape
            ))

            # Gerar PDF
            doc.build(elements)
            logger.info(f"Relatório de recebimentos gerado: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de recebimentos: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Erro ao gerar relatório: {str(e)}")
