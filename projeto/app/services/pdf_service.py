import os
import re
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app

AZUL_CODEGO = colors.HexColor('#002b5c')
CINZA_LINHA = colors.HexColor('#d1d5db')
CINZA_TEXTO = colors.HexColor('#6b7280')

# Fonte institucional exigida pelo MANSUGEQ (manual de controle de informacao
# documentada), secao 6.1-I: "Arial" em todo o documento. O ReportLab so
# embute nativamente as fontes base-14 (Helvetica etc); registramos a Arial
# de verdade a partir dos arquivos ttf, com fallback silencioso para
# Helvetica (metricamente equivalente) caso os arquivos nao estejam presentes.
_FONTS_DIR = Path(__file__).resolve().parent.parent / 'resources' / 'fonts'
try:
    pdfmetrics.registerFont(TTFont('Arial', str(_FONTS_DIR / 'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Bold', str(_FONTS_DIR / 'arialbd.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-Italic', str(_FONTS_DIR / 'ariali.ttf')))
    pdfmetrics.registerFont(TTFont('Arial-BoldItalic', str(_FONTS_DIR / 'arialbi.ttf')))
    pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold',
                                   italic='Arial-Italic', boldItalic='Arial-BoldItalic')
    FONTE_REGULAR = 'Arial'
    FONTE_NEGRITO = 'Arial-Bold'
except Exception:
    FONTE_REGULAR = 'Helvetica'
    FONTE_NEGRITO = 'Helvetica-Bold'


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
    canvas.setFont(FONTE_NEGRITO, 6.5)
    
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
    canvas.setFont(FONTE_REGULAR, 7)

    # Esquerda: Remove qualquer espaço, traço, ponto ou caractere especial
    texto_combinado = f"{raw_doc_code}{raw_rev}".upper()
    codigo_revisao_juntos = re.sub(r'[^A-Z0-9]', '', texto_combinado)
    
    canvas.drawString(margin, footer_y + 4, codigo_revisao_juntos)

    # Direita: Número da página
    page_num = canvas.getPageNumber()
    canvas.drawRightString(page_width - margin, footer_y + 4, f'PÁGINA {page_num}')

    canvas.restoreState()


def bloco_identificacao(story, titulo, doc_code, rev, data_emissao, emitido_por, styles_map,
                         unidade_responsavel=None, revisado_por=None, controle=None, aprovado_por='GESTÃO CODEGO'):
    """Bloco de identificação ISO 9001 no topo do documento com fallback de segurança.

    unidade_responsavel/revisado_por/controle são opcionais (None = linha omitida) para não
    alterar a aparência dos relatórios que já usavam esta função antes desses campos existirem.
    """
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
         Paragraph('<b>APROVADO POR</b>', cell), Paragraph(str(aprovado_por).upper(), cell)],
    ]
    if unidade_responsavel is not None or revisado_por is not None:
        dados.append([
            Paragraph('<b>UNIDADE RESPONSÁVEL</b>', cell), Paragraph(str(unidade_responsavel or '-').upper(), cell),
            Paragraph('<b>REVISADO POR</b>', cell), Paragraph(str(revisado_por or '-').upper(), cell),
        ])
    controle_row = None
    if controle is not None:
        controle_row = len(dados)
        dados.append([
            Paragraph('<b>CONTROLE</b>', cell), Paragraph(str(controle).upper(), cell),
            Paragraph('', cell), Paragraph('', cell),
        ])

    t = Table(dados, colWidths=[110, 145, 100, 145])
    estilo = [
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f4f8')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f4f8')),
        ('BOX', (0, 0), (-1, -1), 0.8, AZUL_CODEGO),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ('FONTNAME', (0, 0), (-1, -1), FONTE_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if controle_row is not None:
        estilo.append(('SPAN', (1, controle_row), (3, controle_row)))
        estilo.append(('BACKGROUND', (2, controle_row), (2, controle_row), colors.white))
    t.setStyle(TableStyle(estilo))
    story.append(t)
    story.append(Spacer(1, 14))


def linha_assinatura(story, emitido_por, styles_map, revisado_por=None, aprovado_por='GESTÃO CODEGO'):
    """Linha de assinatura ao final do documento com fallback de segurança.

    revisado_por é opcional: quando omitido, mantém o layout de 2 colunas usado antes desse
    campo existir; quando informado, adiciona uma terceira coluna "Revisado por".
    """
    from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    # Proteção contra KeyError no styles_map
    if isinstance(styles_map, dict) and 'cell' in styles_map:
        cell = styles_map['cell']
    else:
        styles = getSampleStyleSheet()
        cell = styles['Normal']

    data_hoje = datetime.now().strftime('%d/%m/%Y')

    if revisado_por is not None:
        cabecalho = ['<b>ELABORADO POR:</b>', '<b>REVISADO POR:</b>', '<b>APROVADO POR:</b>']
        responsaveis = [str(emitido_por).upper(), str(revisado_por).upper(), str(aprovado_por).upper()]
        col_widths = [167, 167, 166]
    else:
        cabecalho = ['<b>ELABORADO POR:</b>', '<b>APROVADO POR:</b>']
        responsaveis = [str(emitido_por).upper(), str(aprovado_por).upper()]
        col_widths = [250, 250]

    dados = [
        [Paragraph(h, cell) for h in cabecalho],
        [Paragraph(r, cell) for r in responsaveis],
        [Paragraph('ASSINATURA: ________________________', cell) for _ in cabecalho],
        [Paragraph(f'DATA: {data_hoje}', cell) for _ in cabecalho],
    ]

    t = Table(dados, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.8, AZUL_CODEGO),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, CINZA_LINHA),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f4f8')),
        ('FONTNAME', (0, 0), (-1, -1), FONTE_REGULAR),
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


def carimbo_copia_nao_controlada(canvas, doc):
    """Carimbo diagonal 'CÓPIA NÃO CONTROLADA', exigido pela secao 7.4 do MANSUGEQ para
    documentos gerados sob demanda que nao passam pela Lista Mestra da SUGEQ (nao ficam
    sincronizados com revisoes futuras). Combinar com add_header_footer via onFirstPage/onLaterPages."""
    canvas.saveState()
    page_width, page_height = getattr(doc, 'pagesize', A4)
    data_emissao = str(getattr(doc, '_iso_data', datetime.now().strftime('%d/%m/%Y')))

    canvas.translate(page_width / 2, page_height / 2)
    canvas.rotate(45)
    canvas.setFillColor(colors.HexColor('#b91c1c'))
    canvas.setFillAlpha(0.14)
    canvas.setFont(FONTE_NEGRITO, 34)
    canvas.drawCentredString(0, 10, 'CÓPIA NÃO CONTROLADA')
    canvas.setFont(FONTE_REGULAR, 12)
    canvas.drawCentredString(0, -22, f'Válida apenas na data de emissão: {data_emissao}')
    canvas.setFillAlpha(1.0)
    canvas.restoreState()


def pagina_relgea(canvas, doc):
    """Callback de página para relatórios RELGEA: cabeçalho/rodapé padrão + carimbo de
    cópia não controlada (ver carimbo_copia_nao_controlada)."""
    add_header_footer(canvas, doc)
    carimbo_copia_nao_controlada(canvas, doc)