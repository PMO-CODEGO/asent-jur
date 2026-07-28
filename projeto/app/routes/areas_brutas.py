import io
import re
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

areas_brutas_bp = Blueprint('areas_brutas', __name__)

CAMPOS = [
    ('municipio',              'Município'),
    ('num_matricula',          'Nº Matrícula do Imóvel'),
    ('ano_aquisicao',          'Ano de Aquisição'),
    ('area_util_m2',           'Área Útil (m²)'),
    ('reserva_legal_m2',       'Reserva Legal (m²)'),
    ('area_total_m2',          'Área Total (m²)'),
    ('valor_imovel',           'Valor do Imóvel'),
    ('moeda_imovel',           'Moeda do Imóvel'),
    ('grupo',                  'Grupo (valor compartilhado)'),
    ('valor_conjunto',         'Valor do Conjunto'),
    ('moeda_conjunto',         'Moeda do Conjunto'),
    ('descricao_area',         'Descrição da Área'),
    ('matricula_parcelamento',  'Matrícula do Parcelamento'),
    ('ocupacao',               'Ocupação'),
    ('tipo_aquisicao',         'Tipo de Aquisição'),
    ('registro_propriedade',   'Registro de Propriedade'),
    ('link_geo',               'Link GEO'),
    ('link_matricula',         'Link Matrícula'),
    ('numero_processo',        'Número de Processo'),
    ('loteamento',             'Loteamento'),
    ('tipo',                   'Tipo'),
]

TIPOS = [('Área bruta', 'Área bruta'), ('Área bruta - Processo judicial', 'Área bruta - Processo judicial')]

DECIMAIS = {'area_util_m2', 'area_total_m2', 'valor_conjunto'}
INTEIROS = {'ano_aquisicao', 'qtd'}
MATRICULAS = {'num_matricula', 'matricula_parcelamento'}


def _parse_decimal_str(s):
    """Converte string numérica em float, aceitando formato BR (1.234,56) ou US (1234.56)."""
    s = s.strip()
    if re.match(r'^\d{1,3}(\.\d{3})+(,\d*)?$', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def _fmt_decimal_br(val):
    """Formata número decimal para exibição BR sem zeros finais desnecessários.
    Usa Decimal para evitar imprecisão de ponto flutuante."""
    if val is None:
        return ''
    try:
        d = Decimal(str(val)).normalize()
        s = format(d, 'f')  # evita notação científica
    except (InvalidOperation, ValueError, TypeError):
        return str(val) if val else ''
    if '.' in s:
        int_part, dec_part = s.split('.')
    else:
        int_part, dec_part = s, ''
    neg = int_part.startswith('-')
    # formata separador de milhar diretamente com ponto
    int_formatted = '{:,}'.format(abs(int(int_part))).replace(',', '.')
    if neg:
        int_formatted = '-' + int_formatted
    return (int_formatted + ',' + dec_part) if dec_part else int_formatted


def _fmt_int_br(val):
    """Formata inteiro/string numérica com pontos de milhar (ex: 118653 → '118.653')."""
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
        return _parse_decimal_str(str(value))
    if field in INTEIROS:
        try:
            return int(str(value).replace('.', '').replace(',', ''))
        except ValueError:
            return None
    if field in MATRICULAS:
        # remove pontos de milhar inseridos pela máscara antes de salvar
        return str(value).strip().replace('.', '') or None
    return str(value).strip() or None


def _insert_values(form):
    return tuple(_parse(f, form.get(f)) for f, _ in CAMPOS)


def _update_set(form):
    fields = [f for f, _ in CAMPOS]
    set_clause = ', '.join(f'{f}=%s' for f in fields)
    return set_clause, tuple(_parse(f, form.get(f)) for f in fields)


def _save_avaliacoes(cursor, area_bruta_id, form):
    """Apaga e reinsere avaliações vindas do formulário."""
    cursor.execute('DELETE FROM areas_brutas_avaliacoes WHERE area_bruta_id=%s', (area_bruta_id,))
    anos     = form.getlist('aval_ano[]')
    mercados = form.getlist('aval_mercado[]')
    subs     = form.getlist('aval_subsidiado[]')
    for ano, vm, vs in zip(anos, mercados, subs):
        ano = ano.strip()
        if not ano:
            continue
        try:
            ano_int = int(ano)
        except ValueError:
            continue
        vm_val = _parse_decimal_str(vm) if vm.strip() else None
        vs_val = _parse_decimal_str(vs) if vs.strip() else None
        cursor.execute(
            'INSERT INTO areas_brutas_avaliacoes (area_bruta_id, ano, valor_mercado, valor_subsidiado) VALUES (%s,%s,%s,%s)',
            (area_bruta_id, ano_int, vm_val, vs_val)
        )


def _fetch_avaliacoes(cursor, area_bruta_id):
    cursor.execute(
        'SELECT ano, valor_mercado, valor_subsidiado FROM areas_brutas_avaliacoes WHERE area_bruta_id=%s ORDER BY ano',
        (area_bruta_id,)
    )
    return cursor.fetchall()


def _propagar_valor_grupo(cursor, form):
    """Se o registro pertence a um grupo, aplica moeda e valor a todos do grupo."""
    grupo = (form.get('grupo') or '').strip()
    if not grupo:
        return
    valor = _parse_decimal_str(form.get('valor_conjunto') or '')
    moeda = (form.get('moeda_conjunto') or 'R$').strip()
    if valor is None:
        return
    cursor.execute(
        'UPDATE areas_brutas SET valor_conjunto=%s, moeda_conjunto=%s WHERE grupo=%s',
        (valor, moeda, grupo)
    )


@areas_brutas_bp.route('/assent/areas-brutas/nova', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def nova():
    if request.method == 'POST':
        cols = ', '.join(f for f, _ in CAMPOS)
        placeholders = ', '.join('%s' for _ in CAMPOS)
        with get_db() as db:
            with db.cursor() as cursor:
                cursor.execute(
                    f'INSERT INTO areas_brutas ({cols}) VALUES ({placeholders})',
                    _insert_values(request.form)
                )
                area_id = cursor.lastrowid
                _save_avaliacoes(cursor, area_id, request.form)
                _propagar_valor_grupo(cursor, request.form)
                db.commit()
        f = request.form
        gravar_log('AREA_BRUTA_CRIADA', (
            f"Município: {f.get('municipio') or '-'} | "
            f"Matrícula: {f.get('num_matricula') or '-'} | "
            f"Tipo: {f.get('tipo') or '-'} | "
            f"Área total (m²): {f.get('area_total_m2') or '-'} | "
            f"Ano aquisição: {f.get('ano_aquisicao') or '-'} | "
            f"Descrição: {f.get('descricao_area') or '-'}"
        ))
        return redirect(url_for('dashboard.areas_brutas'))
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT DISTINCT municipio FROM municipal_lots WHERE municipio IS NOT NULL AND municipio != '' ORDER BY municipio")
            municipios = [r[0] for r in cursor.fetchall()]
            cursor.execute("""
                SELECT grupo, MAX(moeda_conjunto) AS moeda_conjunto, MAX(valor_conjunto) AS valor_conjunto
                FROM areas_brutas
                WHERE grupo IS NOT NULL AND grupo != ''
                  AND valor_conjunto IS NOT NULL
                GROUP BY grupo
                ORDER BY grupo
            """)
            grupos_rows = cursor.fetchall()
    grupos = [r[0] for r in grupos_rows]
    grupos_valores = {r[0]: {'moeda': r[1] or 'R$', 'valor': _fmt_decimal_br(r[2])} for r in grupos_rows}
    return render_template('areas_brutas_form.html', registro=None, avaliacoes=[], campos=CAMPOS, tipos=TIPOS,
                           titulo='Nova Área Bruta', municipios=municipios, grupos=grupos, grupos_valores=grupos_valores)


@areas_brutas_bp.route('/assent/areas-brutas/<int:registro_id>/editar', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            if request.method == 'POST':
                set_clause, values = _update_set(request.form)
                cursor.execute(
                    f'UPDATE areas_brutas SET {set_clause} WHERE id=%s',
                    values + (registro_id,)
                )
                _save_avaliacoes(cursor, registro_id, request.form)
                _propagar_valor_grupo(cursor, request.form)
                db.commit()
                f = request.form
                gravar_log('AREA_BRUTA_EDITADA', (
                    f"ID: {registro_id} | "
                    f"Município: {f.get('municipio') or '-'} | "
                    f"Matrícula: {f.get('num_matricula') or '-'} | "
                    f"Tipo: {f.get('tipo') or '-'} | "
                    f"Área total (m²): {f.get('area_total_m2') or '-'} | "
                    f"Ano aquisição: {f.get('ano_aquisicao') or '-'} | "
                    f"Descrição: {f.get('descricao_area') or '-'}"
                ))
                return redirect(url_for('dashboard.areas_brutas'))
            cursor.execute('SELECT * FROM areas_brutas WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()
            avaliacoes = _fetch_avaliacoes(cursor, registro_id)
    if not registro:
        return redirect(url_for('dashboard.areas_brutas'))
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT DISTINCT municipio FROM municipal_lots WHERE municipio IS NOT NULL AND municipio != '' ORDER BY municipio")
            municipios = [r[0] for r in cursor.fetchall()]
            cursor.execute("""
                SELECT grupo, MAX(moeda_conjunto) AS moeda_conjunto, MAX(valor_conjunto) AS valor_conjunto
                FROM areas_brutas
                WHERE grupo IS NOT NULL AND grupo != ''
                  AND valor_conjunto IS NOT NULL
                GROUP BY grupo
                ORDER BY grupo
            """)
            grupos_rows = cursor.fetchall()
    grupos = [r[0] for r in grupos_rows]
    grupos_valores = {r[0]: {'moeda': r[1] or 'R$', 'valor': _fmt_decimal_br(r[2])} for r in grupos_rows}
    registro_display = dict(registro)
    for field in DECIMAIS:
        if registro_display.get(field) is not None:
            registro_display[field] = _fmt_decimal_br(registro_display[field])
    # matrícula — formata com pontos de milhar para exibição no form
    for field in MATRICULAS:
        if registro_display.get(field):
            registro_display[field] = _fmt_int_br(registro_display[field])
    # valor_imovel é varchar — tenta formatar se for numérico
    vi = registro_display.get('valor_imovel')
    if vi:
        vi_parsed = _parse_decimal_str(str(vi))
        if vi_parsed is not None:
            registro_display['valor_imovel'] = _fmt_decimal_br(vi_parsed)
    # pré-formata avaliações para exibição BR
    avaliacoes_display = [
        {
            'ano': a['ano'],
            'valor_mercado': _fmt_decimal_br(a['valor_mercado']),
            'valor_subsidiado': _fmt_decimal_br(a['valor_subsidiado']),
        }
        for a in avaliacoes
    ]
    return render_template('areas_brutas_form.html', registro=registro_display,
                           avaliacoes=avaliacoes_display, campos=CAMPOS, tipos=TIPOS,
                           titulo='Editar Área Bruta', municipios=municipios,
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


@areas_brutas_bp.route('/assent/areas-brutas/<int:registro_id>/relatorio')
@role_required('assent', 'admin', 'assent_gestor')
def relatorio(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT * FROM areas_brutas WHERE id=%s', (registro_id,))
            r = cursor.fetchone()
            avaliacoes = _fetch_avaliacoes(cursor, registro_id)
    if not r:
        abort(404)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
    )

    AZUL = colors.HexColor('#002b5c')
    AZUL_CLARO = colors.HexColor('#eff6ff')
    CINZA = colors.HexColor('#f3f4f6')
    CINZA_TEXT = colors.HexColor('#6b7280')

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle('titulo', fontSize=18, textColor=AZUL, fontName='Helvetica-Bold', spaceAfter=4)
    sub_style = ParagraphStyle('sub', fontSize=9, textColor=CINZA_TEXT, fontName='Helvetica', spaceAfter=2)
    secao_style = ParagraphStyle('secao', fontSize=10, textColor=AZUL, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=6)
    label_style = ParagraphStyle('label', fontSize=8, textColor=CINZA_TEXT, fontName='Helvetica')
    valor_style = ParagraphStyle('valor', fontSize=9, textColor=colors.HexColor('#111827'), fontName='Helvetica')

    tipo_label = r.get('tipo') or 'Área bruta'
    municipio = r.get('municipio') or ''
    matricula = r.get('num_matricula') or ''
    descricao = r.get('descricao_area') or ''

    story = []

    story.append(Paragraph('CODEGO', titulo_style))
    story.append(Paragraph(f'Relatório de Área Bruta — {tipo_label}', sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=AZUL, spaceAfter=10))

    story.append(Paragraph('Identificação', secao_style))

    def campo(label, valor):
        return [Paragraph(label, label_style), Paragraph(str(valor) if valor else '-', valor_style)]

    valor_imovel_display = _fmt_brl(r.get('valor_conjunto') or r.get('valor_imovel'))
    if r.get('grupo') and r.get('valor_conjunto'):
        valor_imovel_display += f'  (Grupo: {r["grupo"]})'

    ident_data = [
        campo('Nº', str(r.get('qtd') or '-')),
        campo('Município', municipio),
        campo('Nº Matrícula', matricula),
        campo('Ano de Aquisição', str(r.get('ano_aquisicao') or '-')),
        campo('Tipo', tipo_label),
        campo('Registro de Propriedade', r.get('registro_propriedade') or '-'),
    ]

    for i in range(0, len(ident_data), 2):
        row_left = ident_data[i]
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
        row_left = aq_data[i]
        row_right = aq_data[i+1] if i+1 < len(aq_data) else [Paragraph('', label_style), Paragraph('', valor_style)]
        t = Table([[row_left[0], row_right[0]], [row_left[1], row_right[1]]], colWidths=[8.5*cm, 8.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CINZA),
            ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(t)

    doc.build(story)
    buf.seek(0)

    nome_arquivo = f'area_bruta_{municipio.replace(" ", "_")}_{matricula or registro_id}.pdf'
    gravar_log('AREA_BRUTA_PDF', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Matrícula: {r.get('num_matricula') or '-'} | "
        f"Tipo: {r.get('tipo') or '-'} | "
        f"Arquivo: {nome_arquivo}"
    ))
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


@areas_brutas_bp.route('/assent/areas-brutas/<int:registro_id>/excluir', methods=['POST'])
@role_required('admin')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT municipio, num_matricula FROM areas_brutas WHERE id=%s', (registro_id,))
            r = cursor.fetchone()
            cursor.execute('DELETE FROM areas_brutas WHERE id=%s', (registro_id,))
            db.commit()
    if r:
        gravar_log('AREA_BRUTA_EXCLUIDA', f"ID: {registro_id} | Município: {r.get('municipio') or '-'} | Matrícula: {r.get('num_matricula') or '-'}")
    return redirect(url_for('dashboard.areas_brutas'))
