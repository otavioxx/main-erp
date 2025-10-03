import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.barcode import code39, code128, code93
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, black, white, grey, lightgrey, darkgrey
import io
from PIL import Image as PILImage

from models.venda import Venda
from models.empresa import Empresa
from models.duplicata import Duplicata
from database import Database

class PrintVenda:
    @staticmethod
    def _limitar_texto(texto, max_chars):
        """Limita o texto ao número máximo de caracteres"""
        if not texto:
            return ''
        if len(str(texto)) > max_chars:
            return str(texto)[:max_chars-3] + "..."
        return str(texto)

    @staticmethod
    def buscar_itens_venda_detalhados(venda_id):
        """Busca itens da venda incluindo campos do produto (cor, tamanho)"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    iv.id,
                    iv.produto_id,
                    p.nome as produto_nome,
                    p.cor,
                    p.tamanho,
                    iv.quantidade,
                    iv.preco_unitario
                FROM itens_venda iv
                INNER JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = ?
                ORDER BY p.nome
            """

            cursor.execute(query, (venda_id,))
            result = cursor.fetchall()
            return result

        except Exception as e:
            print(f"Erro ao buscar itens da venda: {str(e)}")
            return []
        finally:
            try:
                conn.close()
            except:
                pass

    @staticmethod
    def buscar_parcelas_venda(venda_id):
        """Busca as parcelas/duplicatas da venda"""
        try:
            db = Database()
            conn = db.get_connection()
            cursor = conn.cursor()

            # Buscar duplicatas abertas
            cursor.execute("""
                SELECT numero_parcela, valor_parcela, data_vencimento, status
                FROM duplicatas
                WHERE venda_id = ?
                ORDER BY numero_parcela
            """, (venda_id,))

            parcelas_abertas = cursor.fetchall()

            # Buscar duplicatas pagas
            cursor.execute("""
                SELECT numero_parcela, valor_recebido as valor_parcela, data_vencimento, 'pago' as status
                FROM duplicatas_pagas
                WHERE venda_id = ?
                ORDER BY numero_parcela
            """, (venda_id,))

            parcelas_pagas = cursor.fetchall()

            # Combinar e ordenar todas as parcelas
            todas_parcelas = list(parcelas_abertas) + list(parcelas_pagas)
            todas_parcelas.sort(key=lambda x: x[0])  # Ordenar por numero_parcela

            return todas_parcelas

        except Exception as e:
            print(f"Erro ao buscar parcelas da venda: {str(e)}")
            return []
        finally:
            try:
                conn.close()
            except:
                pass

    @staticmethod
    def _limpar_nome_arquivo(nome):
        """Remove caracteres inválidos do nome para uso em arquivo"""
        import re
        # Remove caracteres especiais e substitui espaços por underscore
        nome_limpo = re.sub(r'[<>:"/\\|?*]', '', nome)
        nome_limpo = re.sub(r'\s+', '_', nome_limpo.strip())
        # Limita o tamanho do nome
        return nome_limpo[:50] if len(nome_limpo) > 50 else nome_limpo

    @staticmethod
    def _get_nome_cliente(cliente_id):
        """Obtém o nome do cliente pelo ID"""
        if not cliente_id:
            return "Cliente não informado"

        conn = Database().get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT nome FROM clientes WHERE id = ?', (cliente_id,))
            result = cursor.fetchone()
            return result[0] if result else "Cliente não encontrado"
        except Exception as e:
            return f"Erro: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def gerar_comprovante(venda_id, pasta_destino='imprecoes'):
        """Gera um comprovante de venda em formato PDF com cabeçalho da empresa"""
        try:
            venda = Venda.buscar_por_id(venda_id)
            if not venda:
                return None

            empresa = Empresa.buscar()

            # Usar o método local para buscar itens detalhados
            itens = PrintVenda.buscar_itens_venda_detalhados(venda_id)

            cliente_nome = PrintVenda._get_nome_cliente(venda.cliente_id)

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            cliente_nome_limpo = PrintVenda._limpar_nome_arquivo(cliente_nome)
            data_atual = datetime.now().strftime('%d-%m-%Y')
            filename = os.path.join(pasta_destino, f"VENDA_{cliente_nome_limpo}_{data_atual}.pdf")

            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )

            styles = getSampleStyleSheet()

            estilo_empresa = ParagraphStyle(
                'Empresa',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#000000')
            )

            estilo_titulo = ParagraphStyle(
                'Titulo',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#366092')
            )

            estilo_subtitulo = ParagraphStyle(
                'Subtitulo',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=6,
                alignment=TA_LEFT,
                textColor=colors.HexColor('#000000')
            )

            estilo_normal = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT
            )

            estilo_normal_negrito = ParagraphStyle(
                'NormalNegrito',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_LEFT,
                fontName='Helvetica-Bold'
            )

            estilo_normal_direita = ParagraphStyle(
                'NormalDireita',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_RIGHT
            )

            estilo_rodape = ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=8,
                spaceAfter=0,
                alignment=TA_CENTER,
                textColor=colors.grey
            )

            elements = []

            # CABEÇALHO COM LOGO E DADOS DA EMPRESA
            if empresa and hasattr(empresa, 'logo') and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((80, 80))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format='PNG')
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=60, height=60)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 5*mm))
                except Exception as e:
                    print(f"Erro ao processar logo: {e}")

            if empresa and hasattr(empresa, 'nome') and empresa.nome:
                elements.append(Paragraph(empresa.nome.upper(), estilo_empresa))

            if empresa and hasattr(empresa, 'cnpj') and empresa.cnpj:
                elements.append(Paragraph(f"CNPJ: {empresa.cnpj}", estilo_normal))

            info_contato = []
            if empresa and hasattr(empresa, 'endereco') and empresa.endereco:
                info_contato.append(empresa.endereco)
            if empresa and hasattr(empresa, 'telefone') and empresa.telefone:
                info_contato.append(f"Tel: {empresa.telefone}")
            if empresa and hasattr(empresa, 'email') and empresa.email:
                info_contato.append(empresa.email)

            if info_contato:
                elements.append(Paragraph(" | ".join(info_contato), estilo_normal))

            elements.append(Spacer(1, 8*mm))

            # LINHA SEPARADORA
            elements.append(Table(
                [['']],
                colWidths=[190*mm],
                style=[
                    ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#366092')),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#366092')),
                ]
            ))

            elements.append(Spacer(1, 8*mm))

            # TÍTULO DO COMPROVANTE
            elements.append(Paragraph(f"COMPROVANTE DE VENDA - Nº {venda_id}", estilo_titulo))
            elements.append(Spacer(1, 6*mm))

            # DADOS DA VENDA
            data_formatada = datetime.strptime(str(venda.data_venda), '%Y-%m-%d').strftime('%d/%m/%Y') if venda.data_venda else "N/A"
            elements.append(Paragraph(f"<b>Data da Venda:</b> {data_formatada}", estilo_normal))
            elements.append(Paragraph(f"<b>Cliente:</b> {cliente_nome}", estilo_normal))
            elements.append(Paragraph(f"<b>Forma Pagamento:</b> {venda.forma_pagamento}", estilo_normal))

            # VERIFICAÇÃO CORRIGIDA PARA CREDIÁRIO
            eh_crediario = venda.forma_pagamento and "credi" in venda.forma_pagamento.lower()

            # EXIBIR VALOR DE ENTRADA SEMPRE QUE HOUVER, INDEPENDENTE DA FORMA DE PAGAMENTO
            valor_entrada = getattr(venda, 'valor_entrada', 0.0)
            if valor_entrada and valor_entrada > 0:
                elements.append(Paragraph(f"<b>Valor da Entrada:</b> R$ {valor_entrada:.2f}", estilo_normal_negrito))

            if eh_crediario:
                parcelas = int(venda.parcelas) if venda.parcelas else 1
                elements.append(Paragraph(f"<b>Número de Parcelas:</b> {parcelas}", estilo_normal))

            elements.append(Paragraph(f"<b>Status:</b> {venda.status.upper()}", estilo_normal))

            elements.append(Spacer(1, 8*mm))

            # === PARCELAS ACIMA DOS PRODUTOS (NOVO POSICIONAMENTO) ===
            if eh_crediario:
                parcelas_venda = PrintVenda.buscar_parcelas_venda(venda_id)

                if parcelas_venda:
                    elements.append(Paragraph("PARCELAS DO CREDIÁRIO", estilo_subtitulo))
                    elements.append(Spacer(1, 4*mm))

                    # Tabela de parcelas ocupando toda a largura
                    parcelas_dados = [
                        ['Parcela', 'Valor R$', 'Data Vencimento', 'Status']
                    ]

                    for parcela in parcelas_venda:
                        numero_parcela = parcela[0]
                        valor_parcela = float(parcela[1])
                        data_vencimento = parcela[2]
                        status_parcela = parcela[3]

                        # Formatar data
                        if data_vencimento:
                            try:
                                if isinstance(data_vencimento, str):
                                    data_obj = datetime.strptime(data_vencimento, '%Y-%m-%d')
                                else:
                                    data_obj = data_vencimento
                                data_formatada = data_obj.strftime('%d/%m/%Y')
                            except:
                                data_formatada = str(data_vencimento)
                        else:
                            data_formatada = "N/A"

                        # Formatar status
                        status_texto = "PAGA" if status_parcela == "pago" else "EM ABERTO"

                        parcelas_dados.append([
                            f"{numero_parcela}ª",
                            f"{valor_parcela:.2f}",
                            data_formatada,
                            status_texto
                        ])

                    # TABELA MENOR - ocupando toda largura com colunas proporcionais
                    tabela_parcelas = Table(parcelas_dados,
                                          colWidths=[25*mm, 35*mm, 45*mm, 35*mm],  # Colunas mais estreitas
                                          rowHeights=[5*mm] + [4*mm]*(len(parcelas_dados)-1))  # Linhas mais baixas

                    estilo_parcelas = TableStyle([
                        # Cabeçalho
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,0), 'CENTER'),
                        ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,0), 7),  # Fonte menor
                        ('TOPPADDING', (0,0), (-1,0), 1),  # Padding reduzido
                        ('BOTTOMPADDING', (0,0), (-1,0), 1),

                        # Dados
                        ('BACKGROUND', (0,1), (-1,-1), colors.lightgrey),
                        ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                        ('FONTSIZE', (0,1), (-1,-1), 7),  # Fonte menor
                        ('VALIGN', (0,1), (-1,-1), 'MIDDLE'),
                        ('TOPPADDING', (0,1), (-1,-1), 0.5),  # Padding reduzido
                        ('BOTTOMPADDING', (0,1), (-1,-1), 0.5),

                        # Alinhamentos
                        ('ALIGN', (0,1), (0,-1), 'CENTER'),   # Parcela
                        ('ALIGN', (1,1), (1,-1), 'RIGHT'),    # Valor
                        ('ALIGN', (2,1), (2,-1), 'CENTER'),   # Vencimento
                        ('ALIGN', (3,1), (3,-1), 'CENTER'),   # Status

                        # Grade
                        ('GRID', (0,0), (-1,-1), 0.3, colors.grey),  # Linha mais fina
                    ])

                    tabela_parcelas.setStyle(estilo_parcelas)
                    elements.append(tabela_parcelas)
                    elements.append(Spacer(1, 8*mm))  # Espaço após parcelas

            # === ITENS DA VENDA (AGORA ABAIXO DAS PARCELAS) ===
            elements.append(Paragraph("ITENS DA VENDA", estilo_subtitulo))
            elements.append(Spacer(1, 4*mm))

            # TABELA COM OS CAMPOS SOLICITADOS: ID, Nome, Tamanho, Cor, Quantidade, Valor de venda
            tabela_dados = [
                ['ID', 'Nome', 'Tamanho', 'Cor', 'Qtd', 'Valor Venda R$']
            ]

            subtotal = 0
            for item in itens:
                # Estrutura da tupla: id, produto_id, nome, cor, tamanho, quantidade, preco_unitario
                produto_id = item[1] if len(item) > 1 else "N/A"
                produto_nome = item[2] if len(item) > 2 else "Produto desconhecido"
                cor = item[3] if len(item) > 3 and item[3] else ''
                tamanho = item[4] if len(item) > 4 and item[4] else ''
                quantidade = item[5] if len(item) > 5 else 0
                preco_unitario = float(item[6]) if len(item) > 6 and item[6] else 0.0

                # Calcular subtotal do item
                subtotal_item = quantidade * preco_unitario
                subtotal += subtotal_item

                # Limitar tamanhos dos textos
                produto_nome = PrintVenda._limitar_texto(produto_nome, 45)
                tamanho = PrintVenda._limitar_texto(tamanho, 8)
                cor = PrintVenda._limitar_texto(cor, 15)

                tabela_dados.append([
                    str(produto_id),                    # ID
                    produto_nome,                       # Nome
                    tamanho,                           # Tamanho
                    cor,                               # Cor
                    str(quantidade),                   # Quantidade
                    f"R$ {preco_unitario:.2f}"        # Valor Venda
                ])

            # ID(12) + Nome(70) + Tamanho(15) + Cor(25) + Qtd(12) + Valor(25) = 159mm
            tabela = Table(tabela_dados,
                        colWidths=[12*mm,  # ID
                                   70*mm,  # Nome
                                   15*mm,  # Tamanho
                                   25*mm,  # Cor
                                   12*mm,  # Qtd
                                   25*mm], # Valor Venda
                        rowHeights=[6*mm] + [4.5*mm]*(len(tabela_dados)-1))

            estilo_tabela = TableStyle([
                # Cabeçalho
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 7),
                ('TOPPADDING', (0,0), (-1,0), 0.5),
                ('BOTTOMPADDING', (0,0), (-1,0), 0.5),

                # Dados
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,1), (-1,-1), 6),
                ('VALIGN', (0,1), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,1), (-1,-1), 0.3),
                ('BOTTOMPADDING', (0,1), (-1,-1), 0.3),

                # Alinhamentos específicos por coluna
                ('ALIGN', (0,1), (0,-1), 'CENTER'),  # ID
                ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Nome
                ('ALIGN', (2,1), (2,-1), 'CENTER'),  # Tamanho
                ('ALIGN', (3,1), (3,-1), 'LEFT'),    # Cor
                ('ALIGN', (4,1), (4,-1), 'CENTER'),  # Qtd
                ('ALIGN', (5,1), (5,-1), 'RIGHT'),   # Valor

                # Grade
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F8F8')])
            ])

            tabela.setStyle(estilo_tabela)
            elements.append(tabela)
            elements.append(Spacer(1, 6*mm))

            # TOTAIS
            totais_dados = []

            totais_dados.append(['Subtotal:', f"R$ {subtotal:.2f}"])

            # Calcular o total com desconto aplicado
            total_com_desconto = subtotal
            if venda.desconto and venda.desconto > 0:
                totais_dados.append(['Desconto:', f"- R$ {venda.desconto:.2f}"])
                total_com_desconto = subtotal - venda.desconto

            # Mostrar o total da venda primeiro
            totais_dados.append(['TOTAL DA VENDA:', f"R$ {total_com_desconto:.2f}"])

            # Para crediário ou qualquer venda com entrada, mostrar entrada e saldo
            valor_entrada = getattr(venda, 'valor_entrada', 0.0)
            if valor_entrada and valor_entrada > 0:
                totais_dados.append(['Entrada Paga:', f"- R$ {valor_entrada:.2f}"])

                # Para crediário, mostrar valor financiado se aplicável
                if eh_crediario and hasattr(venda, 'valor_financiado') and venda.valor_financiado:
                    totais_dados.append(['Valor Financiado:', f"R$ {venda.valor_financiado:.2f}"])
            else:
                # Se não tem entrada, o total é o valor final
                totais_dados.append(['TOTAL A PAGAR:', f"R$ {total_com_desconto:.2f}"])

            tabela_totais = Table(totais_dados, colWidths=[140*mm, 50*mm])

            estilo_totais = TableStyle([
                ('ALIGN', (0,0), (0,-1), 'RIGHT'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
                ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
            ])

            tabela_totais.setStyle(estilo_totais)
            elements.append(tabela_totais)
            elements.append(Spacer(1, 12*mm))

            # STATUS DA VENDA
            if venda.status == 'pendente':
                status_msg = "VENDA PENDENTE"
                elements.append(Paragraph(status_msg, ParagraphStyle(
                    'StatusPendente',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.orange,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))
            elif venda.status == 'concluida' or venda.status == 'pago':
                status_msg = "VENDA CONCLUÍDA"
                elements.append(Paragraph(status_msg, ParagraphStyle(
                    'StatusPago',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.green,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))
            elif venda.status == 'cancelada':
                status_msg = "VENDA CANCELADA"
                elements.append(Paragraph(status_msg, ParagraphStyle(
                    'StatusCancelado',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.red,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))
            elif venda.status == 'parcelada':
                status_msg = "VENDA PARCELADA"
                elements.append(Paragraph(status_msg, ParagraphStyle(
                    'StatusParcelado',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.blue,
                    alignment=TA_CENTER,
                    fontName='Helvetica-Bold'
                )))

            elements.append(Spacer(1, 8*mm))

            # RODAPÉ
            data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            elements.append(Paragraph(f"Emitido em: {data_emissao}", estilo_rodape))

            doc.build(elements)
            return filename

        except Exception as e:
            print(f"Erro ao gerar comprovante PDF: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def gerar_relatorio_vendas_periodo(data_inicio, data_fim, pasta_destino='imprecoes'):
        """Gera relatório de vendas por período"""
        try:
            from utils.venda_utils import VendaUtils

            # Buscar vendas do período
            vendas = VendaUtils.filtrar_vendas(data_inicio, data_fim)
            estatisticas = VendaUtils.obter_resumo_vendas_por_periodo(data_inicio, data_fim)

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            data_inicio_fmt = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d-%m-%Y')
            data_fim_fmt = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d-%m-%Y')
            filename = os.path.join(pasta_destino, f"RELATORIO_VENDAS_{data_inicio_fmt}_a_{data_fim_fmt}.pdf")

            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )

            styles = getSampleStyleSheet()
            elements = []

            # Cabeçalho do relatório
            elements.append(Paragraph("RELATÓRIO DE VENDAS", styles['Heading1']))
            elements.append(Paragraph(f"Período: {data_inicio_fmt} a {data_fim_fmt}", styles['Heading2']))
            elements.append(Spacer(1, 12*mm))

            # Estatísticas resumidas
            elements.append(Paragraph("RESUMO DO PERÍODO", styles['Heading3']))

            resumo_dados = [
                ['Total de Vendas:', f"R$ {estatisticas.get('total_vendas', 0):.2f}"],
                ['Quantidade de Vendas:', str(estatisticas.get('quantidade_vendas', 0))],
                ['Ticket Médio:', f"R$ {estatisticas.get('ticket_medio', 0):.2f}"],
                ['Maior Venda:', f"R$ {estatisticas.get('maior_venda', 0):.2f}"],
            ]

            tabela_resumo = Table(resumo_dados, colWidths=[100*mm, 80*mm])
            tabela_resumo.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ]))

            elements.append(tabela_resumo)
            elements.append(Spacer(1, 12*mm))

            # Lista detalhada de vendas
            if vendas:
                elements.append(Paragraph("VENDAS DETALHADAS", styles['Heading3']))
                elements.append(Spacer(1, 6*mm))

                vendas_dados = [['ID', 'Data', 'Cliente', 'Valor R$', 'Status']]

                for venda in vendas:
                    # A estrutura da venda depende do retorno do VendaUtils
                    venda_id = venda[0] if isinstance(venda, (list, tuple)) else venda.id
                    data_venda = venda[2] if isinstance(venda, (list, tuple)) else venda.data_venda
                    cliente_nome = PrintVenda._get_nome_cliente(venda[1] if isinstance(venda, (list, tuple)) else venda.cliente_id)
                    valor_total = venda[3] if isinstance(venda, (list, tuple)) else venda.total
                    status = venda[5] if isinstance(venda, (list, tuple)) else venda.status

                    # Formatar data
                    if isinstance(data_venda, str):
                        data_formatada = datetime.strptime(data_venda, '%Y-%m-%d').strftime('%d/%m/%Y')
                    else:
                        data_formatada = data_venda.strftime('%d/%m/%Y')

                    vendas_dados.append([
                        str(venda_id),
                        data_formatada,
                        PrintVenda._limitar_texto(cliente_nome, 30),
                        f"{float(valor_total):.2f}",
                        status.upper()
                    ])

                tabela_vendas = Table(vendas_dados, colWidths=[15*mm, 25*mm, 70*mm, 25*mm, 25*mm])
                tabela_vendas.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 8),

                    ('ALIGN', (0,1), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,1), (-1,-1), 7),
                    ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F8F8')])
                ]))

                elements.append(tabela_vendas)
            else:
                elements.append(Paragraph("Nenhuma venda encontrada para o período.", styles['Normal']))

            # Rodapé
            elements.append(Spacer(1, 15*mm))
            data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            elements.append(Paragraph(f"Relatório emitido em: {data_emissao}", styles['Italic']))

            doc.build(elements)
            return filename

        except Exception as e:
            print(f"Erro ao gerar relatório de vendas: {e}")
            import traceback
            traceback.print_exc()
            return None
