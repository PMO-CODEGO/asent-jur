import re
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.pdf_service import (
    AZUL_CODEGO,
    FONTE_NEGRITO,
    FONTE_REGULAR,
    add_header_footer,
    bloco_identificacao,
    linha_assinatura,
)

REVISAO = 'Rev. 01'
UNIDADE_RESPONSAVEL = 'GEAS - GERÊNCIA DE ASSENTAMENTO'

CAMPOS_SQL = (
    'municipio, municipio_id, id_modulo, matricula_atual, custo_aquisicao, '
    'valor_mercado_2025, valor_subsidiado_2025, ajuste_vrl_2025, estoque_2024, '
    'dossie, reconhecimento_estoque'
)

# larguras calibradas para A4 paisagem (usavel ~762pt com margem 40)
COL_WIDTHS = [110, 95, 85, 90, 90, 80, 90, 122]
HEADERS = ['ID Módulo', 'Matrícula', 'Custo de Aquisição', 'Valor de Mercado 2025',
           'Valor Subsidiado 2025', 'Ajuste VRL 2025', 'Estoque em 31/12/2024', 'Dossiê']


def _brl(valor):
    if valor is None:
        return '-'
    try:
        n = Decimal(str(valor))
    except Exception:
        return str(valor)
    texto = '{:,.2f}'.format(abs(n)).replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('-R$ ' if n < 0 else 'R$ ') + texto


def _soma(registros, campo):
    return sum((Decimal(str(r[campo])) for r in registros if r.get(campo) is not None), Decimal(0))


def buscar_estoque(db, municipios=None):
    sql = f'SELECT {CAMPOS_SQL} FROM estoque_financeiro_modulos'
    params = ()
    if municipios:
        sql += ' WHERE UPPER(municipio) IN (' + ', '.join(['%s'] * len(municipios)) + ')'
        params = tuple(m.upper() for m in municipios)
    sql += ' ORDER BY municipio, id_modulo'
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def gerar_relatorio_estoque_pdf(db, emitido_por='SISTEMA', municipios=None):
    """Relatorio de Estoque de Areas (estoque contabil por modulo), agrupado por municipio.

    Retorna (buffer, nome_arquivo, n_registros) ou (None, None, 0) se nao houver registros.
    """
    registros = buscar_estoque(db, municipios)
    if not registros:
        return None, None, 0

    grupos = {}
    for r in registros:
        grupos.setdefault(r['municipio'] or 'SEM MUNICÍPIO', []).append(r)

    if municipios and len(grupos) == 1:
        escopo = next(iter(grupos))
        sufixo = re.sub(r'[^A-Z0-9]+', '', escopo.upper())
    else:
        escopo = 'Todos os municípios' if not municipios else f'{len(grupos)} municípios'
        sufixo = 'GERAL'

    data_emissao = datetime.now().strftime('%d/%m/%Y')
    codigo = f'CODEGO-ASSENT-EST-{sufixo}'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=40, rightMargin=40,
                            topMargin=90, bottomMargin=80)
    doc._iso_doc_code = codigo
    doc._iso_rev = REVISAO
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('EstTitulo', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                                  fontSize=14, leading=18, alignment=1, spaceAfter=12,
                                  textColor=AZUL_CODEGO, splitLongWords=0)
    subtitle_style = ParagraphStyle('EstSub', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                                    fontSize=11, leading=14, spaceAfter=6, spaceBefore=10,
                                    textColor=AZUL_CODEGO, splitLongWords=0)
    header_style = ParagraphStyle('EstHead', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                                  fontSize=9, leading=11, alignment=1, textColor=colors.whitesmoke,
                                  splitLongWords=0)
    cell_centro = ParagraphStyle('EstCellC', parent=styles['Normal'], fontName=FONTE_REGULAR,
                                 fontSize=9, leading=11, alignment=1, splitLongWords=0)
    cell_dir = ParagraphStyle('EstCellD', parent=cell_centro, alignment=2)
    cell_bold_dir = ParagraphStyle('EstCellBD', parent=cell_dir, fontName=FONTE_NEGRITO)
    cell_bold_esq = ParagraphStyle('EstCellBE', parent=cell_centro, fontName=FONTE_NEGRITO, alignment=0)
    ident_style = ParagraphStyle('EstIdent', parent=styles['Normal'], fontName=FONTE_REGULAR,
                                 fontSize=8, leading=10, splitLongWords=0)
    styles_map = {'cell': ident_style, 'bold': subtitle_style}

    story = [Paragraph('RELATÓRIO DE ESTOQUE DE ÁREAS', titulo_style)]
    bloco_identificacao(story,
        titulo=f'Relatório de Estoque de Áreas — {escopo}',
        doc_code=codigo, rev=REVISAO, data_emissao=data_emissao, emitido_por=emitido_por,
        styles_map=styles_map, unidade_responsavel=UNIDADE_RESPONSAVEL, revisado_por='A definir',
        aprovado_por='A definir')

    def estilo_tabela(extra=()):
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), AZUL_CODEGO),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            *extra,
        ])

    # ---- resumo por município ----
    story.append(Paragraph('RESUMO POR MUNICÍPIO', subtitle_style))
    resumo_head = ['Município', 'Módulos', 'Custo de Aquisição', 'Valor de Mercado 2025',
                   'Valor Subsidiado 2025', 'Estoque em 31/12/2024']
    resumo = [[Paragraph(h, header_style) for h in resumo_head]]
    for nome, regs in grupos.items():
        resumo.append([
            Paragraph(escape(nome), cell_bold_esq), Paragraph(str(len(regs)), cell_centro),
            Paragraph(_brl(_soma(regs, 'custo_aquisicao')), cell_dir),
            Paragraph(_brl(_soma(regs, 'valor_mercado_2025')), cell_dir),
            Paragraph(_brl(_soma(regs, 'valor_subsidiado_2025')), cell_dir),
            Paragraph(_brl(_soma(regs, 'estoque_2024')), cell_dir),
        ])
    resumo.append([
        Paragraph('TOTAL GERAL', cell_bold_esq), Paragraph(str(len(registros)), cell_centro),
        Paragraph(_brl(_soma(registros, 'custo_aquisicao')), cell_bold_dir),
        Paragraph(_brl(_soma(registros, 'valor_mercado_2025')), cell_bold_dir),
        Paragraph(_brl(_soma(registros, 'valor_subsidiado_2025')), cell_bold_dir),
        Paragraph(_brl(_soma(registros, 'estoque_2024')), cell_bold_dir),
    ])
    t = Table(resumo, colWidths=[170, 60, 120, 130, 130, 130], repeatRows=1)
    t.setStyle(estilo_tabela([('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f4f8'))]))
    story.append(t)

    # ---- detalhe por município ----
    for nome, regs in grupos.items():
        story.append(Paragraph(f'{escape(nome)} — {len(regs)} módulo(s)', subtitle_style))
        linhas = [[Paragraph(h, header_style) for h in HEADERS]]
        for r in regs:
            linhas.append([
                Paragraph(escape(r['id_modulo'] or '-'), cell_centro),
                Paragraph(escape(r['matricula_atual'] or '-'), cell_centro),
                Paragraph(_brl(r['custo_aquisicao']), cell_dir),
                Paragraph(_brl(r['valor_mercado_2025']), cell_dir),
                Paragraph(_brl(r['valor_subsidiado_2025']), cell_dir),
                Paragraph(_brl(r['ajuste_vrl_2025']), cell_dir),
                Paragraph(_brl(r['estoque_2024']), cell_dir),
                Paragraph(escape((r['dossie'] or '-')[:60]), cell_centro),
            ])
        linhas.append([
            Paragraph('SUBTOTAL', cell_bold_esq), Paragraph('', cell_centro),
            Paragraph(_brl(_soma(regs, 'custo_aquisicao')), cell_bold_dir),
            Paragraph(_brl(_soma(regs, 'valor_mercado_2025')), cell_bold_dir),
            Paragraph(_brl(_soma(regs, 'valor_subsidiado_2025')), cell_bold_dir),
            Paragraph(_brl(_soma(regs, 'ajuste_vrl_2025')), cell_bold_dir),
            Paragraph(_brl(_soma(regs, 'estoque_2024')), cell_bold_dir),
            Paragraph('', cell_centro),
        ])
        t = Table(linhas, colWidths=COL_WIDTHS, repeatRows=1)
        t.setStyle(estilo_tabela([('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f4f8'))]))
        story.append(t)

    story.append(Spacer(1, 6))
    linha_assinatura(story, emitido_por, styles_map, revisado_por='A definir', aprovado_por='A definir')

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)

    return buffer, f'{codigo}_Rev_01.pdf', len(registros)
