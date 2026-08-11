import os
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from flask import current_app

AZUL_CODEGO = colors.HexColor('#002b5c')
CINZA_LINHA = colors.HexColor('#d1d5db')
CINZA_TEXTO = colors.HexColor('#6b7280')


def add_header_footer(canvas, doc):
    """Cabeçalho e rodapé padronizados em todas as páginas."""
    canvas.saveState()
    page_width, page_height = getattr(doc, 'pagesize', A4)
    margin = 54

    # Variáveis dinâmicas passadas pelo Flask / ReportLab
    raw_doc_code = str(getattr(doc, '_iso_doc_code', 'CODEGO-DOC'))
    raw_rev = str(getattr(doc, '_iso_rev', 'Rev. 00'))
    emissao = str(getattr(doc, '_iso_data', datetime.now().strftime('%d/%m/%Y'))).upper()
    emitido_por = str(getattr(doc, '_iso_emitido_por', None) or getattr(doc, 'emitido_por', 'SISTEMA')).upper()

    doc_code_header = raw_doc_code.upper()
    rev_header = raw_rev.upper()

    # Define o título das propriedades do documento PDF com o mesmo código do relatório
    if hasattr(doc, 'title') and not doc.title:
        canvas.setTitle(doc_code_header)

    # ==========================================
    # 1. CABEÇALHO (Em todas as páginas)
    # ==========================================
    header_y = page_height - 52
    header_h = 44

    # Fundo azul do cabeçalho
    canvas.setFillColor(AZUL_CODEGO)
    canvas.rect(margin, header_y, page_width - 2 * margin, header_h, fill=1, stroke=0)

    # Logo no cabeçalho (Lado Esquerdo)
    logo_path = os.path.join(current_app.root_path, 'static', 'logo_codego.png')
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            iw, ih = logo.getSize()
            logo_w = 90
            logo_h = logo_w * ih / iw
            canvas.drawImage(logo, margin + 6, header_y + (header_h - logo_h) / 2,
                             width=logo_w, height=logo_h, mask='auto')
        except Exception:
            pass

    # Informações concentradas no CANTO SUPERIOR DIREITO do cabeçalho
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 6.5)
    
    right_x = page_width - margin - 8
    
    # Textos formatados em Maiúsculo antecedidos do nome + dois pontos
    canvas.drawRightString(right_x, header_y + 32, f'CÓDIGO: {doc_code_header}')
    canvas.drawRightString(right_x, header_y + 23, f'REVISÃO: {rev_header}')
    canvas.drawRightString(right_x, header_y + 14, f'EMISSÃO: {emissao}')
    canvas.drawRightString(right_x, header_y + 5, f'ELABORADO POR: {emitido_por}')

    # Linha separadora abaixo do cabeçalho
    canvas.setStrokeColor(AZUL_CODEGO)
    canvas.setLineWidth(1)
    canvas.line(margin, header_y - 2, page_width - margin, header_y - 2)

    # ==========================================
    # 2. MARCA D'ÁGUA
    # ==========================================
    logo_grey_path = os.path.join(current_app.root_path, 'static', 'logo_codego_grey.png')
    if os.path.exists(logo_grey_path):
        try:
            logo_grey = ImageReader(logo_grey_path)
            iw, ih = logo_grey.getSize()
            scale = 500 / iw
            w = 500
            h = ih * scale
            canvas.translate(page_width / 2, page_height / 2)
            canvas.rotate(45)
            canvas.setFillAlpha(0.06)
            canvas.drawImage(logo_grey, -w / 2, -h / 2, width=w, height=h, mask='auto')
            canvas.setFillAlpha(1.0)
            canvas.rotate(-45)
            canvas.translate(-page_width / 2, -page_height / 2)
        except Exception:
            pass

    # ==========================================
    # 3. RODAPÉ (Em todas as páginas)
    # ==========================================
    footer_y = 30

    # Linha de fechamento contínua
    canvas.setStrokeColor(AZUL_CODEGO)
    canvas.setLineWidth(0.5)
    canvas.line(margin, footer_y + 14, page_width - margin, footer_y + 14)

    canvas.setFillColor(CINZA_TEXTO)
    canvas.setFont('Helvetica', 7)

    # Esquerda: Remove qualquer espaço, traço, ponto ou caractere especial
    texto_combinado = f"{raw_doc_code}{raw_rev}".upper()
    codigo_revisao_juntos = re.sub(r'[^A-Z0-9]', '', texto_combinado)
    
    canvas.drawString(margin, footer_y + 4, codigo_revisao_juntos)

    # Direita: Número da página
    page_num = canvas.getPageNumber()
    canvas.drawRightString(page_width - margin, footer_y + 4, f'PÁGINA {page_num}')

    canvas.restoreState()


def bloco_identificacao(story, titulo, doc_code, rev, data_emissao, emitido_por, styles_map):
    """Bloco de identificação ISO 9001 no topo do documento com fallback de segurança."""
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    # Proteção contra KeyError no styles_map
    if isinstance(styles_map, dict) and 'cell' in styles_map:
        cell = styles_map['cell']
    else:
        styles = getSampleStyleSheet()
        cell = styles['Normal']

    dados = [
        [Paragraph('<b>TÍTULO DO DOCUMENTO</b>', cell), Paragraph(str(titulo).upper(), cell),
         Paragraph('<b>CÓDIGO</b>', cell), Paragraph(str(doc_code).upper(), cell)],
        [Paragraph('<b>REVISÃO</b>', cell), Paragraph(str(rev).upper(), cell),
         Paragraph('<b>DATA DE EMISSÃO</b>', cell), Paragraph(str(data_emissao).upper(), cell)],
        [Paragraph('<b>EMITIDO POR</b>', cell), Paragraph(str(emitido_por).upper(), cell),
         Paragraph('<b>APROVADO POR</b>', cell), Paragraph('GESTÃO CODEGO', cell)],
    ]

    t = Table(dados, colWidths=[110, 145, 100, 145])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f4f8')),
        ('BOX', (0, 0), (-1, -1), 0.8, AZUL_CODEGO),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))


def linha_assinatura(story, emitido_por, styles_map):
    """Linha de assinatura ao final do documento com fallback de segurança."""
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    # Proteção contra KeyError no styles_map
    if isinstance(styles_map, dict) and 'cell' in styles_map:
        cell = styles_map['cell']
    else:
        styles = getSampleStyleSheet()
        cell = styles['Normal']

    dados = [
        [Paragraph('<b>ELABORADO POR:</b>', cell), Paragraph('<b>APROVADO POR:</b>', cell)],
        [Paragraph(str(emitido_por).upper(), cell), Paragraph('GESTÃO CODEGO', cell)],
        [Paragraph('ASSINATURA: ________________________', cell),
         Paragraph('ASSINATURA: ________________________', cell)],
        [Paragraph(f'DATA: {datetime.now().strftime("%d/%m/%Y")}', cell),
         Paragraph(f'DATA: {datetime.now().strftime("%d/%m/%Y")}', cell)],
    ]

    t = Table(dados, colWidths=[250, 250])
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.8, AZUL_CODEGO),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f4f8')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 20))
    story.append(t)


# Mantido por compatibilidade com código legado
def add_watermark(canvas, doc):
    add_header_footer(canvas, doc)