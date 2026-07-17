import io
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
    ('valor_imovel',           'Valor do Imóvel (R$)'),
    ('grupo',                  'Grupo (valor compartilhado)'),
    ('valor_conjunto',         'Valor do Conjunto (R$)'),
    ('descricao_area',         'Descrição da Área'),
    ('matricula_parcelamento',  'Matrícula do Parcelamento'),
    ('valor_mercado_2021',     'Valor de Mercado 2021 (R$)'),
    ('valor_subsidiado_2021',  'Valor Subsidiado 2021 (R$)'),
    ('valor_mercado_2022',     'Valor de Mercado 2022 (R$)'),
    ('valor_subsidiado_2022',  'Valor Subsidiado 2022 (R$)'),
    ('valor_mercado_2023',     'Valor de Mercado 2023 (R$)'),
    ('valor_subsidiado_2023',  'Valor Subsidiado 2023 (R$)'),
    ('valor_mercado_2024',     'Valor de Mercado 2024 (R$)'),
    ('valor_subsidiado_2024',  'Valor Subsidiado 2024 (R$)'),
    ('ocupacao',               'Ocupação'),
    ('tipo_aquisicao',         'Tipo de Aquisição'),
    ('registro_propriedade',   'Registro de Propriedade'),
    ('link_geo',               'Link GEO'),
    ('link_matricula',         'Link Matrícula'),
    ('numero_processo',        'Número de Processo'),
    ('tipo',                   'Tipo'),
]

TIPOS = [('imovel', 'Imóvel'), ('judicial', 'Processo Judicial')]

DECIMAIS = {
    'area_util_m2', 'area_total_m2', 'valor_conjunto',
    'valor_mercado_2021', 'valor_subsidiado_2021',
    'valor_mercado_2022', 'valor_subsidiado_2022',
    'valor_mercado_2023', 'valor_subsidiado_2023',
    'valor_mercado_2024', 'valor_subsidiado_2024',
}
INTEIROS = {'ano_aquisicao', 'qtd'}


def _parse(field, value):
    if value is None or str(value).strip() == '':
        return None
    if field in DECIMAIS:
        try:
            return float(str(value).replace(',', '.'))
        except ValueError:
            return None
    if field in INTEIROS:
        try:
            return int(value)
        except ValueError:
            return None
    return str(value).strip() or None


def _insert_values(form):
    return tuple(_parse(f, form.get(f)) for f, _ in CAMPOS)


def _update_set(form):
    fields = [f for f, _ in CAMPOS]
    set_clause = ', '.join(f'{f}=%s' for f in fields)
    return set_clause, tuple(_parse(f, form.get(f)) for f in fields)


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
    return render_template('areas_brutas_form.html', registro=None, campos=CAMPOS, tipos=TIPOS,
                           titulo='Nova Área Bruta')


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
    if not registro:
        return redirect(url_for('dashboard.areas_brutas'))
    return render_template('areas_brutas_form.html', registro=registro, campos=CAMPOS, tipos=TIPOS,
                           titulo='Editar Área Bruta')


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

    tipo_label = 'Processo Judicial' if r.get('tipo') == 'judicial' else 'Imóvel'
    municipio = r.get('municipio') or ''
    matricula = r.get('num_matricula') or ''
    descricao = r.get('descricao_area') or ''

    story = []

    # Cabeçalho
    story.append(Paragraph('CODEGO', titulo_style))
    story.append(Paragraph(f'Relatório de Área Bruta — {tipo_label}', sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=AZUL, spaceAfter=10))

    # Identificação
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

    # 2 colunas
    for i in range(0, len(ident_data), 2):
        row_left = ident_data[i]
        row_right = ident_data[i+1] if i+1 < len(ident_data) else [Paragraph('', label_style), Paragraph('', valor_style)]
        t = Table([[row_left[0], row_right[0]], [row_left[1], row_right[1]]], colWidths=[8.5*cm, 8.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), CINZA),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(t)

    # Descrição
    story.append(Paragraph('Descrição da Área', secao_style))
    story.append(Paragraph(descricao or '-', valor_style))
    story.append(Spacer(1, 6))

    # Áreas
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

    # Valor
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

    # Valores de Mercado
    story.append(Paragraph('Valores de Mercado e Subsidiado', secao_style))
    anos = [2021, 2022, 2023, 2024]
    vm_header = [Paragraph('Ano', label_style)] + [Paragraph(str(a), label_style) for a in anos]
    vm_mercado = [Paragraph('V. Mercado', label_style)] + [Paragraph(_fmt_brl(r.get(f'valor_mercado_{a}')), valor_style) for a in anos]
    vm_subs = [Paragraph('V. Subsidiado', label_style)] + [Paragraph(_fmt_brl(r.get(f'valor_subsidiado_{a}')), valor_style) for a in anos]
    t = Table([vm_header, vm_mercado, vm_subs], colWidths=[3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm, 3.4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), CINZA),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, AZUL_CLARO]),
    ]))
    story.append(t)

    # Aquisição e Processo
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

    gravar_log('AREA_BRUTA_PDF', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Matrícula: {r.get('num_matricula') or '-'} | "
        f"Tipo: {'Processo Judicial' if r.get('tipo') == 'judicial' else 'Imóvel'} | "
        f"Arquivo: {nome_arquivo}"
    ))
    nome_arquivo = f'area_bruta_{municipio.replace(" ", "_")}_{matricula or registro_id}.pdf'
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=nome_arquivo)


@areas_brutas_bp.route('/assent/areas-brutas/<int:registro_id>/excluir', methods=['POST'])
@role_required('admin')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT municipio, num_matricula FROM areas_brutas WHERE id=%s', (registro_id,))
            r = cursor.fetchone() or {}
            cursor.execute('DELETE FROM areas_brutas WHERE id=%s', (registro_id,))
            db.commit()
    gravar_log('AREA_BRUTA_EXCLUIDA', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Matrícula: {r.get('num_matricula') or '-'}"
    ))
    return redirect(url_for('dashboard.areas_brutas'))
