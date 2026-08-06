import io
import re
import datetime
import logging
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort, session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log
from app.services.municipio_service import listar_municipios

areas_brutas_bp = Blueprint('areas_brutas', __name__)

FAMILIAS = {
    'brutas': {
        'tabela': 'areas_brutas',
        'label': 'Área bruta',
        'titulo_base': 'Área Bruta',
        'codigo_prefixo': 'AB',
        'endpoint_lista': 'dashboard.areas_brutas',
    },
    'judicial': {
        'tabela': 'areas_brutas_judicial',
        'label': 'Área bruta - Processo judicial',
        'titulo_base': 'Área Bruta - Processo Judicial',
        'codigo_prefixo': 'ABJ',
        'endpoint_lista': 'dashboard.areas_brutas',
    },
}

ANOS_AVALIACAO = [2021, 2022, 2023, 2024]


def _familia_config(familia):
    config = FAMILIAS.get(familia)
    if not config:
        abort(404)
    return config


CAMPOS = [
    ('municipio',              'Município'),
    ('num_matricula',          'Nº Matrícula do Imóvel'),
    ('ano_aquisicao',          'Ano de Aquisição'),
    ('area_util_m2',           'Área Útil (m²)'),
    ('reserva_legal_m2',       'Reserva Legal (m²)'),
    ('area_total_m2',          'Área Total (m²)'),
    ('valor_imovel',           'Valor do Imóvel'),
    ('grupo',                  'Grupo (valor compartilhado)'),
    ('valor_conjunto',         'Valor do Conjunto'),
    ('moeda_conjunto',         'Moeda do Conjunto'),
    ('descricao_area',         'Descrição da Área'),
    ('matricula_parcelamento',  'Matrícula do Parcelamento'),
    ('valor_mercado_2021',     'V. Mercado 2021'),
    ('valor_subsidiado_2021',  'V. Subsidiado 2021'),
    ('valor_mercado_2022',     'V. Mercado 2022'),
    ('valor_subsidiado_2022',  'V. Subsidiado 2022'),
    ('valor_mercado_2023',     'V. Mercado 2023'),
    ('valor_subsidiado_2023',  'V. Subsidiado 2023'),
    ('valor_mercado_2024',     'V. Mercado 2024'),
    ('valor_subsidiado_2024',  'V. Subsidiado 2024'),
    ('ocupacao',               'Ocupação'),
    ('tipo_aquisicao',         'Tipo de Aquisição'),
    ('registro_propriedade',   'Registro de Propriedade'),
    ('link_geo',               'Link GEO'),
    ('link_matricula',         'Link Matrícula'),
    ('numero_processo',        'Número de Processo'),
    ('loteamento',             'Loteamento'),
]

DECIMAIS = {
    'area_util_m2', 'area_total_m2', 'valor_conjunto',
    'valor_mercado_2021', 'valor_subsidiado_2021',
    'valor_mercado_2022', 'valor_subsidiado_2022',
    'valor_mercado_2023', 'valor_subsidiado_2023',
    'valor_mercado_2024', 'valor_subsidiado_2024',
}
INTEIROS = {'ano_aquisicao', 'qtd'}
MATRICULAS = {'num_matricula', 'matricula_parcelamento'}


def _parse_decimal_str(s):
    if not s:
        return None
    s = str(s).strip()
    if re.match(r'^\d{1,3}(\.\d{3})+(,\d*)?$', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def _fmt_decimal_br(val):
    if val is None:
        return ''
    try:
        d = Decimal(str(val)).normalize()
        s = format(d, 'f')
    except (InvalidOperation, ValueError, TypeError):
        return str(val) if val else ''
    if '.' in s:
        int_part, dec_part = s.split('.')
    else:
        int_part, dec_part = s, ''
    neg = int_part.startswith('-')
    int_formatted = '{:,}'.format(abs(int(int_part))).replace(',', '.')
    if neg:
        int_formatted = '-' + int_formatted
    return (int_formatted + ',' + dec_part) if dec_part else int_formatted


def _fmt_int_br(val):
    if not val:
        return ''
    s = str(val).strip().replace('.', '')
    try:
        return '{:,}'.format(int(s)).replace(',', '.')
    except ValueError:
        return str(val)


def _parse(field, value):
    if value is None or str(value).strip() == '':
        return None
    if field in DECIMAIS:
        return _parse_decimal_str(value)
    if field in INTEIROS:
        try:
            return int(str(value).replace('.', '').replace(',', ''))
        except ValueError:
            return None
    if field in MATRICULAS:
        return str(value).strip().replace('.', '') or None
    return str(value).strip() or None


def _insert_values(form):
    return tuple(_parse(f, form.get(f)) for f, _ in CAMPOS)


def _update_set(form):
    fields = [f for f, _ in CAMPOS]
    set_clause = ', '.join(f'{f}=%s' for f in fields)
    return set_clause, tuple(_parse(f, form.get(f)) for f in fields)


def _propagar_valor_grupo(cursor, tabela, form):
    grupo = (form.get('grupo') or '').strip()
    if not grupo:
        return
    valor = _parse_decimal_str(form.get('valor_conjunto') or '')
    moeda = (form.get('moeda_conjunto') or 'R$').strip()
    if valor is None:
        return
    try:
        cursor.execute(
            f'UPDATE {tabela} SET valor_conjunto=%s, moeda_conjunto=%s WHERE grupo=%s',
            (valor, moeda, grupo)
        )
    except Exception as e:
        logging.warning(f"Não foi possível propagar o valor do grupo: {e}")


def _obter_municipios_e_grupos(tabela):
    municipios = listar_municipios()
    grupos_rows = []
    try:
        with get_db() as db:
            with db.cursor() as cursor:
                try:
                    cursor.execute(f"""
                        SELECT grupo, MAX(moeda_conjunto) AS moeda_conjunto, MAX(valor_conjunto) AS valor_conjunto
                        FROM {tabela}
                        WHERE grupo IS NOT NULL AND grupo != ''
                          AND valor_conjunto IS NOT NULL
                        GROUP BY grupo
                        ORDER BY grupo
                    """)
                    grupos_rows = cursor.fetchall()
                except Exception:
                    grupos_rows = []
    except Exception as e:
        logging.error(f"Erro ao buscar municípios e grupos: {e}")

    grupos = [r[0] for r in grupos_rows if r and r[0]]
    grupos_valores = {r[0]: {'moeda': r[1] or 'R$', 'valor': _fmt_decimal_br(r[2])} for r in grupos_rows if r and r[0]}
    return municipios, grupos, grupos_valores


@areas_brutas_bp.route('/assent/areas-brutas/<familia>/nova', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def nova(familia):
    config = _familia_config(familia)
    tabela = config['tabela']
    if request.method == 'POST':
        cols = ', '.join(f for f, _ in CAMPOS)
        placeholders = ', '.join('%s' for _ in CAMPOS)
        with get_db() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    f'INSERT INTO {tabela} ({cols}) VALUES ({placeholders})',
                    _insert_values(request.form)
                )
                _propagar_valor_grupo(cursor, tabela, request.form)
                db.commit()
        f = request.form
        gravar_log('AREA_BRUTA_CRIADA', (
            f"Município: {f.get('municipio') or '-'} | "
            f"Matrícula: {f.get('num_matricula') or '-'} | "
            f"Tipo: {config['label']}"
        ))
        return redirect(url_for(config['endpoint_lista']))

    municipios, grupos, grupos_valores = _obter_municipios_e_grupos(tabela)
    return render_template('areas_brutas_form.html', registro=None, campos=CAMPOS,
                           familia=familia, familia_label=config['label'],
                           titulo=f"Nova {config['titulo_base']}", municipios=municipios, grupos=grupos, grupos_valores=grupos_valores)


@areas_brutas_bp.route('/assent/areas-brutas/<familia>/<int:registro_id>/editar', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(familia, registro_id):
    config = _familia_config(familia)
    tabela = config['tabela']
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            if request.method == 'POST':
                set_clause, values = _update_set(request.form)
                cursor.execute(
                    f'UPDATE {tabela} SET {set_clause} WHERE id=%s',
                    values + (registro_id,)
                )
                _propagar_valor_grupo(cursor, tabela, request.form)
                db.commit()
                f = request.form
                gravar_log('AREA_BRUTA_EDITADA', (
                    f"ID: {registro_id} | "
                    f"Município: {f.get('municipio') or '-'} | "
                    f"Matrícula: {f.get('num_matricula') or '-'}"
                ))
                return redirect(url_for(config['endpoint_lista']))
            cursor.execute(f'SELECT * FROM {tabela} WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()

    if not registro:
        return redirect(url_for(config['endpoint_lista']))

    municipios, grupos, grupos_valores = _obter_municipios_e_grupos(tabela)

    registro_display = dict(registro)
    for field in DECIMAIS:
        if registro_display.get(field) is not None:
            registro_display[field] = _fmt_decimal_br(registro_display[field])
    for field in MATRICULAS:
        if registro_display.get(field):
            registro_display[field] = _fmt_int_br(registro_display[field])
    vi = registro_display.get('valor_imovel')
    if vi:
        vi_parsed = _parse_decimal_str(str(vi))
        if vi_parsed is not None:
            registro_display['valor_imovel'] = _fmt_decimal_br(vi_parsed)

    return render_template('areas_brutas_form.html', registro=registro_display, campos=CAMPOS,
                           familia=familia, familia_label=config['label'],
                           titulo=f"Editar {config['titulo_base']}", municipios=municipios,
                           grupos=grupos, grupos_valores=grupos_valores)


def _fmt_brl(val):
    if val is None:
        return '-'
    try:
        n = float(val)
        return 'R$ {:,.2f}'.format(n).replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return str(val) if val else '-'


def _fmt_m2(val):
    if val is None:
        return '-'
    try:
        return '{:,.0f}'.format(float(val)).replace(',', '.')
    except (ValueError, TypeError):
        return str(val) if val else '-'


def _pdf_header_footer(canvas, doc, codigo_doc, revisao, data_emissao, usuario):
    canvas.saveState()
    width, height = A4

    _AZUL      = colors.HexColor('#002b5c')
    _CINZA_BG  = colors.HexColor('#f3f4f6')
    _CINZA_TXT = colors.HexColor('#6b7280')
    _BORDA     = colors.HexColor('#e5e7eb')

    canvas.setFillColor(_AZUL)
    canvas.rect(0, height - 2.8*cm, width, 2.8*cm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 15)
    canvas.drawString(2*cm, height - 1.15*cm, 'CODEGO')
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(2*cm, height - 1.65*cm, 'Companhia de Desenvolvimento Econômico de Goiás')
    canvas.setFont('Helvetica', 7)
    canvas.drawString(2*cm, height - 2.1*cm, 'Relatório de Área Bruta — Informação Documentada')

    canvas.setFont('Helvetica', 7)
    canvas.drawRightString(width - 2*cm, height - 0.75*cm, f'Código: {codigo_doc}')
    canvas.drawRightString(width - 2*cm, height - 1.15*cm, f'Revisão: {revisao}')
    canvas.drawRightString(width - 2*cm, height - 1.55*cm, f'Emissão: {data_emissao}')
    canvas.drawRightString(width - 2*cm, height - 1.95*cm, f'Elaborado por: {usuario}')
    canvas.drawRightString(width - 2*cm, height - 2.35*cm, f'Página {doc.page}')

    canvas.setStrokeColor(_BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, height - 2.8*cm, width - 2*cm, height - 2.8*cm)

    canvas.setFillColor(_CINZA_BG)
    canvas.rect(0, 0, width, 1.6*cm, fill=1, stroke=0)

    canvas.setStrokeColor(_BORDA)
    canvas.line(2*cm, 1.6*cm, width - 2*cm, 1.6*cm)

    raw_footer = f"{codigo_doc}{revisao}"
    footer_code = re.sub(r'[\s./\-]', '', raw_footer).upper()

    canvas.setFillColor(_CINZA_TXT)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(2*cm, 0.8*cm, footer_code)

    canvas.restoreState()


@areas_brutas_bp.route('/assent/areas-brutas/<familia>/<int:registro_id>/relatorio')
@role_required('assent', 'admin', 'assent_gestor')
def relatorio(familia, registro_id):
    config = _familia_config(familia)
    tabela = config['tabela']
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(f'SELECT * FROM {tabela} WHERE id=%s', (registro_id,))
            r = cursor.fetchone()
    if not r:
        abort(404)

    avaliacoes = [
        {'ano': ano, 'valor_mercado': r.get(f'valor_mercado_{ano}'), 'valor_subsidiado': r.get(f'valor_subsidiado_{ano}')}
        for ano in ANOS_AVALIACAO
        if r.get(f'valor_mercado_{ano}') is not None or r.get(f'valor_subsidiado_{ano}') is not None
    ]

    codigo_doc   = f"CODEGO/ASSENT/{config['codigo_prefixo']}/{registro_id:04d}"
    revisao      = 'Rev. 00'
    data_emissao = datetime.date.today().strftime('%d/%m/%Y')
    usuario      = session.get('username') or 'Sistema'

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=3.4*cm,
        bottomMargin=2.2*cm,
    )

    AZUL       = colors.HexColor('#002b5c')
    AZUL_CLARO = colors.HexColor('#eff6ff')
    CINZA      = colors.HexColor('#f3f4f6')
    CINZA_TEXT = colors.HexColor('#6b7280')

    secao_style = ParagraphStyle('secao', fontSize=10, textColor=AZUL, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    label_style = ParagraphStyle('label', fontSize=8, textColor=CINZA_TEXT, fontName='Helvetica')
    valor_style = ParagraphStyle('valor', fontSize=9, textColor=colors.HexColor('#111827'), fontName='Helvetica')
    titulo_doc_style = ParagraphStyle('titdoc', fontSize=13, textColor=AZUL, fontName='Helvetica-Bold', spaceAfter=2)
    sub_doc_style = ParagraphStyle('subdoc', fontSize=8, textColor=CINZA_TEXT, fontName='Helvetica', spaceAfter=10)

    tipo_label = config['label']
    municipio  = r.get('municipio') or ''
    matricula  = r.get('num_matricula') or ''
    descricao  = r.get('descricao_area') or ''

    def campo(label, valor):
        return [Paragraph(label, label_style), Paragraph(str(valor) if valor else '-', valor_style)]

    valor_imovel_display = _fmt_brl(r.get('valor_conjunto') or r.get('valor_imovel'))
    if r.get('grupo') and r.get('valor_conjunto'):
        valor_imovel_display += f'  (Grupo: {r["grupo"]})'

    story = []

    story.append(Paragraph('Relatório de Área Bruta', titulo_doc_style))
    story.append(Paragraph(f'{tipo_label} — {municipio}', sub_doc_style))
    story.append(HRFlowable(width='100%', thickness=1.5, color=AZUL, spaceAfter=10))

    story.append(Paragraph('Identificação', secao_style))
    ident_data = [
        campo('Nº', str(r.get('qtd') or '-')),
        campo('Município', municipio),
        campo('Nº Matrícula', matricula),
        campo('Ano de Aquisição', str(r.get('ano_aquisicao') or '-')),
        campo('Tipo', tipo_label),
        campo('Registro de Propriedade', r.get('registro_propriedade') or '-'),
    ]
    for i in range(0, len(ident_data), 2):
        row_left  = ident_data[i]
        row_right = ident_data[i+1] if i+1 < len(ident_data) else [Paragraph('', label_style), Paragraph('', valor_style)]
        t = Table([[row_left[0], row_right[0]], [row_left[1], row_right[1]]], colWidths=[8.5*cm, 8.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CINZA),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(t)

    story.append(Paragraph('Descrição da Área', secao_style))
    story.append(Paragraph(descricao or '-', valor_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Áreas', secao_style))
    area_rows = [
        [Paragraph('Área Útil (m²)', label_style), Paragraph('Reserva Legal (m²)', label_style), Paragraph('Área Total (m²)', label_style)],
        [Paragraph(_fmt_m2(r.get('area_util_m2')), valor_style), Paragraph(str(r.get('reserva_legal_m2') or '-'), valor_style), Paragraph(_fmt_m2(r.get('area_total_m2')), valor_style)],
    ]
    t = Table(area_rows, colWidths=[5.6*cm, 5.6*cm, 5.6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CINZA),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(t)

    story.append(Paragraph('Valor', secao_style))
    val_rows = [
        [Paragraph('Valor do Imóvel / Conjunto', label_style), Paragraph('Ocupação', label_style)],
        [Paragraph(valor_imovel_display, valor_style), Paragraph(str(r.get('ocupacao') or '-'), valor_style)],
    ]
    t = Table(val_rows, colWidths=[8.5*cm, 8.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CINZA),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(t)

    if avaliacoes:
        story.append(Paragraph('Avaliações de Mercado', secao_style))
        aval_header = [Paragraph('Ano', label_style), Paragraph('V. Mercado', label_style), Paragraph('V. Subsidiado', label_style)]
        aval_data = [aval_header]
        for av in avaliacoes:
            aval_data.append([
                Paragraph(str(av['ano']), valor_style),
                Paragraph(_fmt_brl(av['valor_mercado']), valor_style),
                Paragraph(_fmt_brl(av['valor_subsidiado']), valor_style),
            ])
        t = Table(aval_data, colWidths=[3*cm, 8*cm, 6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CINZA),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
        ]))
        story.append(t)

    story.append(Paragraph('Aquisição e Processo', secao_style))
    aq_data = [
        campo('Tipo de Aquisição', r.get('tipo_aquisicao') or '-'),
        campo('Número de Processo', r.get('numero_processo') or '-'),
        campo('Matrícula do Parcelamento', r.get('matricula_parcelamento') or '-'),
        campo('Link GEO', r.get('link_geo') or '-'),
    ]
    for i in range(0, len(aq_data), 2):
        row_left  = aq_data[i]
        row_right = aq_data[i+1] if i+1 < len(aq_data) else [Paragraph('', label_style), Paragraph('', valor_style)]
        t = Table([[row_left[0], row_right[0]], [row_left[1], row_right[1]]], colWidths=[8.5*cm, 8.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CINZA),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(t)

    cb = lambda c, d: _pdf_header_footer(c, d, codigo_doc, revisao, data_emissao, usuario)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    buf.seek(0)

    doc_code_filename = codigo_doc.replace('/', '-')
    rev_filename = revisao.replace(' ', '_').replace('.', '')
    nome_arquivo = f"{doc_code_filename}_{rev_filename}.pdf"

    gravar_log('AREA_BRUTA_PDF', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Matrícula: {r.get('num_matricula') or '-'} | "
        f"Tipo: {config['label']} | "
        f"Arquivo: {nome_arquivo}"
    ))
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


@areas_brutas_bp.route('/assent/areas-brutas/<familia>/<int:registro_id>/excluir', methods=['POST'])
@role_required('admin')
def excluir(familia, registro_id):
    config = _familia_config(familia)
    tabela = config['tabela']
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(f'SELECT municipio, num_matricula FROM {tabela} WHERE id=%s', (registro_id,))
            r = cursor.fetchone()
            cursor.execute(f'DELETE FROM {tabela} WHERE id=%s', (registro_id,))
            db.commit()
    if r:
        gravar_log('AREA_BRUTA_EXCLUIDA', f"ID: {registro_id} | Município: {r.get('municipio') or '-'} | Matrícula: {r.get('num_matricula') or '-'}")
    return redirect(url_for(config['endpoint_lista']))
    return redirect(url_for(config['endpoint_lista']))