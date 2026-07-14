from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.decorators import role_required
from app.db import get_db

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
                return redirect(url_for('dashboard.areas_brutas'))
            cursor.execute('SELECT * FROM areas_brutas WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()
    if not registro:
        return redirect(url_for('dashboard.areas_brutas'))
    return render_template('areas_brutas_form.html', registro=registro, campos=CAMPOS, tipos=TIPOS,
                           titulo='Editar Área Bruta')


@areas_brutas_bp.route('/assent/areas-brutas/<int:registro_id>/excluir', methods=['POST'])
@role_required('admin')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute('DELETE FROM areas_brutas WHERE id=%s', (registro_id,))
            db.commit()
    return redirect(url_for('dashboard.areas_brutas'))
