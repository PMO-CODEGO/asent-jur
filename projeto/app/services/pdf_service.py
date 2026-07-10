import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from flask import current_app

AZUL_CODEGO = colors.HexColor('#002b5c')
CINZA_LINHA = colors.HexColor('#d1d5db')
CINZA_TEXTO = colors.HexColor('#6b7280')


def add_header_footer(canvas, doc):
    """Cabeçalho e rodapé ISO 9001 em todas as páginas."""
    canvas.saveState()
    page_width, page_height = A4
    margin = 54

    # --- CABEÇALHO ---
    header_y = page_height - 42
    header_h = 36

    # Fundo azul do cabeçalho
    canvas.setFillColor(AZUL_CODEGO)
    canvas.rect(margin, header_y, page_width - 2 * margin, header_h, fill=1, stroke=0)

    # Logo no cabeçalho
    logo_path = os.path.join(current_app.root_path, 'static', 'logo_codego.png')
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        iw, ih = logo.getSize()
        logo_w = 90
        logo_h = logo_w * ih / iw
        canvas.drawImage(logo, margin + 6, header_y + (header_h - logo_h) / 2,
                         width=logo_w, height=logo_h, mask='auto')

    # Código do documento e revisão (centro)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 8)
    doc_code = getattr(doc, '_iso_doc_code', 'CODEGO-DOC')
    canvas.drawCentredString(page_width / 2, header_y + 22, doc_code)
    canvas.setFont('Helvetica', 7)
    rev = getattr(doc, '_iso_rev', 'Rev. 00')
    canvas.drawCentredString(page_width / 2, header_y + 11, rev)

    # Data de emissão (direita)
    canvas.setFont('Helvetica', 7)
    emissao = getattr(doc, '_iso_data', datetime.now().strftime('%d/%m/%Y'))
    canvas.drawRightString(page_width - margin - 6, header_y + 22, f'Emissão: {emissao}')
    canvas.drawRightString(page_width - margin - 6, header_y + 11, 'DOCUMENTO CONTROLADO')

    # Linha separadora abaixo do cabeçalho
    canvas.setStrokeColor(AZUL_CODEGO)
    canvas.setLineWidth(0.5)
    canvas.line(margin, header_y - 1, page_width - margin, header_y - 1)

    # --- MARCA D'ÁGUA ---
    logo_grey_path = os.path.join(current_app.root_path, 'static', 'logo_codego_grey.png')
    if os.path.exists(logo_grey_path):
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

    # --- RODAPÉ ---
    footer_y = 30
    canvas.setStrokeColor(AZUL_CODEGO)
    canvas.setLineWidth(0.5)
    canvas.line(margin, footer_y + 14, page_width - margin, footer_y + 14)

    canvas.setFillColor(CINZA_TEXTO)
    canvas.setFont('Helvetica', 7)

    # Esquerda: aviso
    canvas.drawString(margin, footer_y + 4,
                      'Documento controlado — reprodução não autorizada sem aprovação formal.')

    # Direita: página
    page_num = canvas.getPageNumber()
    canvas.drawRightString(page_width - margin, footer_y + 4,
                           f'Página {page_num}')

    canvas.restoreState()


def bloco_identificacao(story, titulo, doc_code, rev, data_emissao, emitido_por, styles_map):
    """Bloco de identificação ISO 9001 no topo do documento."""
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph

    cell = styles_map['cell']
    bold = styles_map['bold']

    dados = [
        [Paragraph('<b>Título do Documento</b>', cell), Paragraph(titulo, cell),
         Paragraph('<b>Código</b>', cell), Paragraph(doc_code, cell)],
        [Paragraph('<b>Revisão</b>', cell), Paragraph(rev, cell),
         Paragraph('<b>Data de Emissão</b>', cell), Paragraph(data_emissao, cell)],
        [Paragraph('<b>Emitido por</b>', cell), Paragraph(emitido_por, cell),
         Paragraph('<b>Aprovado por</b>', cell), Paragraph('Gestão CODEGO', cell)],
    ]

    t = Table(dados, colWidths=[100, 155, 100, 145])
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
    """Linha de assinatura ao final do documento."""
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph

    cell = styles_map['cell']

    dados = [
        [Paragraph('<b>Elaborado por:</b>', cell), Paragraph('<b>Aprovado por:</b>', cell)],
        [Paragraph(emitido_por, cell), Paragraph('Gestão CODEGO', cell)],
        [Paragraph('Assinatura: ________________________', cell),
         Paragraph('Assinatura: ________________________', cell)],
        [Paragraph(f'Data: {datetime.now().strftime("%d/%m/%Y")}', cell),
         Paragraph(f'Data: {datetime.now().strftime("%d/%m/%Y")}', cell)],
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
