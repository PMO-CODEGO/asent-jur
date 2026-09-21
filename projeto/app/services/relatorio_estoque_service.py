import re
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
ANOS = [
    ('2021', 'ajuste_efeito_pl_2021', 'Ajuste Efeito PL'),
    ('2022', 'ajuste_efeito_pl_2022', 'Ajuste Efeito PL'),
    ('2023', 'ajuste_efeito_pl_2023', 'Ajuste Efeito PL'),
    ('2024', 'ajuste_vrl_2024', 'Ajuste/Reversão VRL'),
    ('2025', 'ajuste_vrl_2025', 'Ajuste/Reversão VRL'),
]


def _brl(valor):
    if valor is None:
        return '-'
    try:
        n = Decimal(str(valor))
    except Exception:
        return str(valor)
    texto = '{:,.2f}'.format(abs(n)).replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('-R$ ' if n < 0 else 'R$ ') + texto


def _num(valor):
    if valor is None:
        return '-'
    texto = '{:,.2f}'.format(Decimal(str(valor))).replace(',', 'X').replace('.', ',').replace('X', '.')
    return texto


def buscar_estoque_registro(db, municipio_id, id_modulo):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(
            'SELECT * FROM estoque_financeiro_modulos WHERE municipio_id=%s AND id_modulo=%s',
            (municipio_id, id_modulo))
        estoque = cursor.fetchone()
        if not estoque:
            return None, None
        ibge = (municipio_id or '').split(' - ')[0].strip()
        cursor.execute(
            'SELECT municipio, distrito, quadra, qtd_modulos, logradouro, area_lote_m2, '
            'matricula_modulo, empresa, status_de_assentamento '
            'FROM municipal_lots WHERE codigo_ibge_municipio=%s AND id_modulo=%s LIMIT 1',
            (ibge, id_modulo))
        return estoque, cursor.fetchone()


def gerar_ficha_estoque_pdf(estoque, modulo, emitido_por='SISTEMA'):
    """Ficha de Estoque de Areas de um unico modulo. Retorna (buffer, nome_arquivo)."""
    id_modulo = estoque['id_modulo']
    sufixo = re.sub(r'[^A-Za-z0-9]+', '', id_modulo).upper() or 'MODULO'
    codigo = f'CODEGO-ASSENT-EST-{sufixo}'
    data_emissao = datetime.now().strftime('%d/%m/%Y')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=54, rightMargin=54,
                            topMargin=90, bottomMargin=80)
    doc._iso_doc_code = codigo
    doc._iso_rev = REVISAO
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    titulo = ParagraphStyle('FichaTitulo', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                            fontSize=14, leading=18, alignment=1, spaceAfter=12,
                            textColor=AZUL_CODEGO, splitLongWords=0)
    secao = ParagraphStyle('FichaSecao', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                           fontSize=11, leading=14, spaceBefore=8, spaceAfter=4,
                           textColor=AZUL_CODEGO, splitLongWords=0)
    label = ParagraphStyle('FichaLabel', parent=styles['Normal'], fontName=FONTE_NEGRITO,
                           fontSize=9, leading=11, textColor=colors.HexColor('#374151'), splitLongWords=0)
    valor = ParagraphStyle('FichaValor', parent=styles['Normal'], fontName=FONTE_REGULAR,
                           fontSize=10, leading=12, splitLongWords=0)
    head = ParagraphStyle('FichaHead', parent=label, alignment=1, textColor=colors.whitesmoke)
    valor_dir = ParagraphStyle('FichaValorD', parent=valor, alignment=2)
    valor_cen = ParagraphStyle('FichaValorC', parent=valor, fontName=FONTE_NEGRITO, alignment=1)
    ident = ParagraphStyle('FichaIdent', parent=styles['Normal'], fontName=FONTE_REGULAR,
                           fontSize=8, leading=10, splitLongWords=0)
    styles_map = {'cell': ident, 'bold': secao}

    def campo(nome, v):
        return [Paragraph(nome, label), Paragraph(escape(str(v)) if v not in (None, '') else '-', valor)]

    def grade(pares, colunas=2):
        linhas = []
        for i in range(0, len(pares), colunas):
            grupo = pares[i:i + colunas]
            while len(grupo) < colunas:
                grupo.append([Paragraph('', label), Paragraph('', valor)])
            linhas.append([g[0] for g in grupo])
            linhas.append([g[1] for g in grupo])
        t = Table(linhas, colWidths=[487 / colunas] * colunas)
        estilo = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d1d5db')),
                  ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                  ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6)]
        for r in range(0, len(linhas), 2):
            estilo.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor('#f0f4f8')))
        t.setStyle(TableStyle(estilo))
        return t

    municipio = (modulo or {}).get('municipio') or estoque.get('municipio') or '-'
    story = [Paragraph('FICHA DE ESTOQUE DE ÁREAS', titulo)]
    bloco_identificacao(story,
        titulo=f'Estoque de Áreas — Módulo {id_modulo}',
        doc_code=codigo, rev=REVISAO, data_emissao=data_emissao, emitido_por=emitido_por,
        styles_map=styles_map, unidade_responsavel=UNIDADE_RESPONSAVEL, revisado_por='A definir',
        aprovado_por='A definir')

    story.append(Paragraph('Identificação do Módulo', secao))
    pares = [campo('Município', municipio), campo('Distrito', (modulo or {}).get('distrito') or estoque.get('distrito')),
             campo('Código do Módulo', id_modulo), campo('Matrícula Atual', estoque.get('matricula_atual'))]
    if modulo:
        pares += [campo('Quadra', modulo.get('quadra')), campo('Módulo', modulo.get('qtd_modulos')),
                  campo('Logradouro', modulo.get('logradouro')), campo('Tamanho (m²)', _num(modulo.get('area_lote_m2'))),
                  campo('Empresa', modulo.get('empresa')), campo('Status de Assentamento', modulo.get('status_de_assentamento'))]
    story.append(grade(pares, 3))

    story.append(Paragraph('Custos', secao))
    story.append(grade([
        campo('Custo Terreno', _brl(estoque.get('custo_terreno'))),
        campo('Custo Implantação', _brl(estoque.get('custo_implantacao'))),
        campo('Custo de Aquisição', _brl(estoque.get('custo_aquisicao'))),
        campo('Custo Venda', _brl(estoque.get('custo_venda'))),
        campo('Área Vendida (m²)', _num(estoque.get('area_vendida'))),
    ], 3))

    story.append(Paragraph('Valores por Ano', secao))
    linhas = [[Paragraph(h, head) for h in ('Ano', 'Valor de Mercado', 'Valor Subsidiado', 'Ajuste')]]
    for ano, campo_ajuste, rotulo in ANOS:
        linhas.append([
            Paragraph(ano, valor_cen),
            Paragraph(_brl(estoque.get(f'valor_mercado_{ano}')), valor_dir),
            Paragraph(_brl(estoque.get(f'valor_subsidiado_{ano}')), valor_dir),
            Paragraph(f'{_brl(estoque.get(campo_ajuste))}<br/><font size="7" color="#6b7280">{rotulo}</font>', valor_dir),
        ])
    t = Table(linhas, colWidths=[50, 145, 145, 147], repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), AZUL_CODEGO), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                           ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 6)]))
    story.append(t)

    story.append(KeepTogether([Paragraph('Estoque e Reconhecimento', secao), grade([
        campo('Estoque em 31/12/2024', _brl(estoque.get('estoque_2024'))),
        campo('Dossiê', estoque.get('dossie')),
        campo('Reconhecimento de Estoque', estoque.get('reconhecimento_estoque')),
        campo('Observações', estoque.get('observacoes')),
    ])]))

    linha_assinatura(story, emitido_por, styles_map, revisado_por='A definir', aprovado_por='A definir')
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer, f'{codigo}_Rev_01.pdf'
