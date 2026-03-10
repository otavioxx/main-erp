import os
import io
import logging
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from PIL import Image as PILImage

from models.produto import Produto
from models.empresa import Empresa
from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrintProduto:
    HEADER_BG_COLOR = colors.HexColor("#366092")
    LIGHT_BG_COLOR = colors.HexColor("#F2F2F2")
    ZEBRA_BG_COLOR = colors.HexColor("#F8F8F8")

    @staticmethod
    def calcular_lucro_percentual(preco_custo, preco_venda):
        """Calcula o percentual de lucro sobre o preço de custo"""
        if preco_custo == 0:
            return 0
        return ((preco_venda - preco_custo) / preco_custo) * 100

    @staticmethod
    def calcular_markup_percentual(preco_custo, preco_venda):
        """Calcula o percentual de markup sobre o preço de custo"""
        if preco_custo == 0:
            return 0
        return ((preco_venda - preco_custo) / preco_custo) * 100

    @staticmethod
    def calcular_valor_estoque(preco_custo, estoque):
        """Calcula o valor total em estoque"""
        return preco_custo * estoque

    @staticmethod
    def _get_fornecedor_por_id(fornecedor_id):
        """Obtém o fornecedor pelo ID"""
        try:
            with Database().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, nome FROM fornecedores WHERE id = ?', (fornecedor_id,))
                result = cursor.fetchone()
                if result:
                    return type('Fornecedor', (), {'id': result[0], 'nome': result[1]})
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar fornecedor: {e}")
            return None

    @staticmethod
    def _aplicar_filtros_produtos(produtos, filtros):
        """Aplica filtros aos produtos"""
        if not filtros:
            return produtos

        produtos_filtrados = produtos.copy()

        # Filtro por estoque
        filtro_estoque = filtros.get('filtro_estoque', 'ambos')
        if filtro_estoque == 'com_estoque':
            produtos_filtrados = [p for p in produtos_filtrados if p.estoque > 0]
        elif filtro_estoque == 'sem_estoque':
            produtos_filtrados = [p for p in produtos_filtrados if p.estoque == 0]
        # 'ambos' não faz nada

        # Filtro por status
        filtro_status = filtros.get('filtro_status', 'ativos')
        if filtro_status == 'ativos':
            produtos_filtrados = [p for p in produtos_filtrados if p.ativo]
        elif filtro_status == 'inativos':
            produtos_filtrados = [p for p in produtos_filtrados if not p.ativo]
        # 'ambos' não faz nada

        return produtos_filtrados

    @staticmethod
    def _ordenar_produtos(produtos, ordenar_por="id", direcao="desc"):
        """Ordena produtos conforme especificado"""
        reverse = (direcao == "desc")

        if ordenar_por == "id":
            return sorted(produtos, key=lambda p: p.id, reverse=reverse)
        elif ordenar_por == "nome":
            return sorted(produtos, key=lambda p: p.nome.lower(), reverse=reverse)
        elif ordenar_por == "estoque":
            return sorted(produtos, key=lambda p: p.estoque, reverse=reverse)
        elif ordenar_por == "preco_venda":
            return sorted(produtos, key=lambda p: p.preco_venda, reverse=reverse)
        elif ordenar_por == "preco_custo":
            return sorted(produtos, key=lambda p: p.preco_custo, reverse=reverse)
        else:
            # Padrão: ordenar por ID decrescente
            return sorted(produtos, key=lambda p: p.id, reverse=True)

    @staticmethod
    def _gerar_titulo_com_filtros(filtros):
        """Gera título do relatório com informações dos filtros"""
        partes_titulo = ["RELATÓRIO DE PRODUTOS"]

        if filtros:
            # Status
            filtro_status = filtros.get('filtro_status', 'ativos')
            if filtro_status == 'ativos':
                partes_titulo.append("ATIVOS")
            elif filtro_status == 'inativos':
                partes_titulo.append("INATIVOS")
            elif filtro_status == 'ambos':
                partes_titulo.append("TODOS")

            # Estoque
            filtro_estoque = filtros.get('filtro_estoque', 'ambos')
            if filtro_estoque == 'com_estoque':
                partes_titulo.append("COM ESTOQUE")
            elif filtro_estoque == 'sem_estoque':
                partes_titulo.append("SEM ESTOQUE")

        return " - ".join(partes_titulo)

    @staticmethod
    def _gerar_info_filtros(filtros):
        """Gera informações detalhadas dos filtros para exibir no relatório"""
        if not filtros:
            return []

        info_filtros = []

        # Filtro de estoque
        filtro_estoque = filtros.get('filtro_estoque', 'ambos')
        if filtro_estoque == 'com_estoque':
            info_filtros.append("Estoque: Apenas com estoque")
        elif filtro_estoque == 'sem_estoque':
            info_filtros.append("Estoque: Apenas sem estoque")
        elif filtro_estoque == 'ambos':
            info_filtros.append("Estoque: Todos")

        # Filtro de status
        filtro_status = filtros.get('filtro_status', 'ativos')
        if filtro_status == 'ativos':
            info_filtros.append("Status: Apenas ativos")
        elif filtro_status == 'inativos':
            info_filtros.append("Status: Apenas inativos")
        elif filtro_status == 'ambos':
            info_filtros.append("Status: Todos")

        # Ordenação
        ordenar_por = filtros.get('ordenar_por', 'id')
        direcao = filtros.get('direcao', 'desc')

        ordenacao_map = {
            'id': 'ID',
            'nome': 'Nome',
            'estoque': 'Estoque',
            'preco_venda': 'Preço de Venda',
            'preco_custo': 'Preço de Custo'
        }

        direcao_map = {
            'asc': 'Crescente',
            'desc': 'Decrescente'
        }

        campo_texto = ordenacao_map.get(ordenar_por, 'ID')
        direcao_texto = direcao_map.get(direcao, 'Decrescente')

        info_filtros.append(f"Ordenação: {campo_texto} ({direcao_texto})")

        return info_filtros

    @staticmethod
    def gerar_relatorio_produtos(pasta_destino='relatorios', apenas_ativos=True, filtros=None):
        """Gera um relatório de produtos em formato PDF com filtros personalizados"""
        try:
            # Buscar todos os produtos (filtro básico de ativo/inativo será aplicado depois)
            produtos = Produto.buscar_todos(apenas_ativos=False)  # Buscar todos para aplicar filtros customizados

            if not produtos:
                logger.error("Nenhum produto encontrado")
                return None

            # Aplicar filtros personalizados se fornecidos
            if filtros:
                produtos = PrintProduto._aplicar_filtros_produtos(produtos, filtros)

                # Aplicar ordenação
                ordenar_por = filtros.get('ordenar_por', 'id')
                direcao = filtros.get('direcao', 'desc')
                produtos = PrintProduto._ordenar_produtos(produtos, ordenar_por, direcao)
            else:
                # Filtro padrão se não especificado
                if apenas_ativos:
                    produtos = [p for p in produtos if p.ativo]
                produtos = PrintProduto._ordenar_produtos(produtos, "id", "desc")

            if not produtos:
                logger.error("Nenhum produto encontrado após aplicar filtros")
                return None

            empresa = Empresa.buscar()

            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(pasta_destino, f"produtos_filtrados_{timestamp}.pdf")

            doc = SimpleDocTemplate(
                filename,
                pagesize=landscape(A4),
                rightMargin=8*mm,
                leftMargin=8*mm,
                topMargin=8*mm,
                bottomMargin=8*mm
            )

            styles = getSampleStyleSheet()

            estilo_empresa = ParagraphStyle(
                'Empresa',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=4,
                alignment=TA_CENTER,
                textColor=colors.black
            )

            estilo_titulo = ParagraphStyle(
                'Titulo',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#366092')
            )

            estilo_filtro = ParagraphStyle(
                'Filtro',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=3,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            )

            estilo_normal = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=7,
                spaceAfter=2,
                alignment=TA_LEFT
            )

            estilo_normal_negrito = ParagraphStyle(
                'NormalNegrito',
                parent=styles['Normal'],
                fontSize=7,
                spaceAfter=2,
                alignment=TA_LEFT,
                fontName='Helvetica-Bold'
            )

            estilo_rodape = ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=6,
                spaceAfter=0,
                alignment=TA_CENTER,
                textColor=colors.grey
            )

            elements = []

            # Logo da empresa
            if empresa and empresa.logo:
                try:
                    logo_data = io.BytesIO(empresa.logo)
                    img = PILImage.open(logo_data)
                    img.thumbnail((45, 45))

                    temp_logo = io.BytesIO()
                    img.save(temp_logo, format='PNG')
                    temp_logo.seek(0)

                    logo = Image(temp_logo, width=30, height=30)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 2*mm))
                except Exception as e:
                    logger.error(f"Erro ao processar logo: {e}")

            # Nome da empresa
            nome_empresa = empresa.nome.upper() if empresa and empresa.nome else "NOME DA EMPRESA"
            elements.append(Paragraph(nome_empresa, estilo_empresa))

            # CNPJ e informações de contato
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

            # Linha separadora
            elements.append(Table(
                [['']],
                colWidths=[270*mm],
                style=[
                    ('LINEABOVE', (0,0), (-1,-1), 1, colors.HexColor('#366092')),
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#366092')),
                ]
            ))

            elements.append(Spacer(1, 4*mm))

            # Título do relatório com filtros
            titulo = PrintProduto._gerar_titulo_com_filtros(filtros)
            elements.append(Paragraph(titulo, estilo_titulo))

            # Informações dos filtros aplicados
            info_filtros = PrintProduto._gerar_info_filtros(filtros)
            for info in info_filtros:
                elements.append(Paragraph(info, estilo_filtro))

            elements.append(Spacer(1, 6*mm))

            # Tabela de produtos
            if produtos:
                tabela_dados = [
                    ['ID', 'Nome', 'Cor', 'Tamanho', 'Preço Custo', 'Preço Venda',
                     'Estoque', 'Fornecedor', 'Status', 'Lucro %', 'Valor Estoque']
                ]

                total_valor_estoque = 0

                for produto in produtos:
                    lucro_percentual = PrintProduto.calcular_lucro_percentual(produto.preco_custo, produto.preco_venda)
                    valor_estoque = PrintProduto.calcular_valor_estoque(produto.preco_custo, produto.estoque)
                    total_valor_estoque += valor_estoque

                    fornecedor_nome = "Nenhum"
                    if produto.fornecedor_id:
                        fornecedor = PrintProduto._get_fornecedor_por_id(produto.fornecedor_id)
                        if fornecedor:
                            fornecedor_nome = fornecedor.nome

                    dados = [
                        str(produto.id),
                        produto.nome,
                        produto.cor or "",
                        produto.tamanho or "",
                        f"R$ {produto.preco_custo:.2f}",
                        f"R$ {produto.preco_venda:.2f}",
                        str(produto.estoque),
                        fornecedor_nome,
                        "Ativo" if produto.ativo else "Inativo",
                        f"{lucro_percentual:.1f}%",
                        f"R$ {valor_estoque:.2f}"
                    ]

                    tabela_dados.append(dados)

                # Linha de total
                tabela_dados.append([
                    '', '', '', '', '', '', '', '', '',
                    'TOTAL:',
                    f"R$ {total_valor_estoque:.2f}"
                ])

                # Larguras das colunas ajustadas para incluir cor e tamanho
                col_widths = [10*mm, 45*mm, 15*mm, 15*mm, 18*mm, 18*mm, 12*mm, 35*mm, 12*mm, 15*mm, 18*mm]

                tabela = Table(tabela_dados, colWidths=col_widths, repeatRows=1)

                estilo_tabela = TableStyle([
                    # Cabeçalho
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#366092')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,0), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 6),
                    ('BOTTOMPADDING', (0,0), (-1,0), 6),

                    # Alinhamentos das colunas
                    ('ALIGN', (0,1), (0,-1), 'CENTER'),  # ID
                    ('ALIGN', (1,1), (1,-1), 'LEFT'),    # Nome
                    ('ALIGN', (2,1), (3,-1), 'CENTER'),  # Cor, Tamanho
                    ('ALIGN', (4,1), (5,-1), 'RIGHT'),   # Preços
                    ('ALIGN', (6,1), (6,-1), 'CENTER'),  # Estoque
                    ('ALIGN', (7,1), (7,-1), 'LEFT'),    # Fornecedor
                    ('ALIGN', (8,1), (8,-1), 'CENTER'),  # Status
                    ('ALIGN', (9,1), (10,-1), 'RIGHT'),  # Lucro %, Valor Estoque

                    # Fonte e tamanho dos dados
                    ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
                    ('FONTSIZE', (0,1), (-1,-2), 5),
                    ('TOPPADDING', (0,1), (-1,-2), 1),
                    ('BOTTOMPADDING', (0,1), (-1,-2), 1),

                    # Bordas
                    ('GRID', (0,0), (-1,-2), 0.5, colors.grey),

                    # Cores alternadas nas linhas
                    ('ROWBACKGROUNDS', (1,1), (-1,-2), [colors.white, colors.HexColor('#F8F8F8')]),

                    # Formatação da linha de total
                    ('BACKGROUND', (9,-1), (10,-1), colors.HexColor('#E6E6E6')),
                    ('FONTNAME', (9,-1), (10,-1), 'Helvetica-Bold'),
                    ('FONTSIZE', (9,-1), (10,-1), 6),
                    ('LINEABOVE', (9,-1), (10,-1), 1, colors.black),
                ])

                tabela.setStyle(estilo_tabela)
                elements.append(tabela)

                # Resumo
                elements.append(Spacer(1, 4*mm))
                elements.append(Paragraph(
                    f"Total de produtos: {len(produtos)} | Valor total em estoque: R$ {total_valor_estoque:,.2f}",
                    estilo_normal_negrito
                ))
            else:
                elements.append(Paragraph("Nenhum produto encontrado com os filtros aplicados.", estilo_normal))

            # Rodapé
            elements.append(Spacer(1, 8*mm))
            elements.append(Paragraph(
                f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                estilo_rodape
            ))

            # Gerar PDF
            doc.build(elements)
            logger.info(f"Relatório de produtos gerado: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de produtos PDF: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def gerar_relatorio_com_filtros(filtros, pasta_destino='relatorios'):
        """Método simplificado para gerar relatório com filtros"""
        return PrintProduto.gerar_relatorio_produtos(
            pasta_destino=pasta_destino,
            apenas_ativos=True,  # Será sobrescrito pelos filtros
            filtros=filtros
        )
