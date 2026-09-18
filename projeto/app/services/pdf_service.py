import os
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


CINZA_LINHA_TIMBRADO = colors.HexColor('#818699')


def add_header_footer(canvas, doc):
    """Cabeçalho e rodapé padronizados em todas as páginas, reproduzindo o papel timbrado
    oficial da CODEGO (logo + linha no topo; brasão de Goiás + contato no rodapé)."""
    canvas.saveState()
    page_width, page_height = getattr(doc, 'pagesize', A4)
    margin = 54
    # O timbrado (logo/brasão/linhas) usa uma margem própria, mais próxima da borda da
    # página que a margem do corpo do texto — igual ao papel timbrado oficial de referência.
    margin_timbrado = 32

    # Variáveis dinâmicas passadas pelo Flask / ReportLab (mantidas para o título do PDF;
    # o timbrado oficial não exibe código/revisão no cabeçalho/rodapé, pois esses dados já
    # aparecem no bloco de identificação, no corpo do documento).
    raw_doc_code = str(getattr(doc, '_iso_doc_code', 'CODEGO-DOC'))
    if hasattr(doc, 'title') and not doc.title:
        canvas.setTitle(raw_doc_code.upper())

    # ==========================================
    # 1. CABEÇALHO: logo CodeGO + linha
    # ==========================================
    logo_top_gap = 32
    logo_h = 29
    logo_top_y = page_height - logo_top_gap
    logo_w = logo_h * (255 / 80)  # proporção do arquivo logo_codego_timbrado.png

    logo_path = os.path.join(current_app.root_path, 'static', 'logo_codego_timbrado.png')
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(logo_path)
            iw, ih = logo.getSize()
            logo_w = logo_h * iw / ih
            canvas.drawImage(logo, margin_timbrado, logo_top_y - logo_h, width=logo_w, height=logo_h, mask='auto')
        except Exception:
            pass

    canvas.setStrokeColor(CINZA_LINHA_TIMBRADO)
    canvas.setLineWidth(1)
    linha_header_y = logo_top_y - logo_h / 2
    canvas.line(margin_timbrado + logo_w + 16, linha_header_y, page_width - margin_timbrado, linha_header_y)

    # ==========================================
    # 2. RODAPÉ: brasão de Goiás + linha + contato
    # ==========================================
    shield_bottom_y = 29
    shield_h = 38
    shield_w = shield_h * (80 / 100)  # proporção do arquivo brasao_goias_rodape.png
    text_x = margin_timbrado + shield_w + 14

    shield_path = os.path.join(current_app.root_path, 'static', 'brasao_goias_rodape.png')
    if os.path.exists(shield_path):
        try:
            shield = ImageReader(shield_path)
            iw, ih = shield.getSize()
            shield_w = shield_h * iw / ih
            text_x = margin_timbrado + shield_w + 14
            canvas.drawImage(shield, margin_timbrado, shield_bottom_y, width=shield_w, height=shield_h, mask='auto')
        except Exception:
            pass

    canvas.setStrokeColor(CINZA_LINHA_TIMBRADO)
    canvas.setLineWidth(0.75)
    linha_footer_y = shield_bottom_y + shield_h - 4
    canvas.line(text_x, linha_footer_y, page_width - margin_timbrado, linha_footer_y)

    canvas.setFillColor(CINZA_TEXTO)
    canvas.setFont(FONTE_REGULAR, 7.5)
    canvas.drawString(text_x, shield_bottom_y + 26, 'Fone: (62) 3604-3100 / Fax: 3604-3101')
    canvas.drawString(text_x, shield_bottom_y + 16, 'Avenida 85, esquina com Alameda Ricardo Paranhos, nº 1593.')
    canvas.drawString(text_x, shield_bottom_y + 6, 'Setor Marista, Goiânia-GO • CEP: 74.160-010')

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