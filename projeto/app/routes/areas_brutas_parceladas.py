from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

areas_brutas_parceladas_bp = Blueprint('areas_brutas_parceladas', __name__)

TIPOS = ['Parcelada Regularizada', 'Galerias/Condomínio', 'Loteamento Irregular']

CAMPOS = [
    ('tipo',                    'Tipo'),
    ('municipio',               'Município'),
    ('num_matricula',           'Nº Matrícula'),
    ('ano_aquisicao',           'Ano de Aquisição'),
    ('area_total_m2',           'Área Total (m²)'),
    ('valor_imovel',            'Valor do Imóvel'),
    ('matricula_parcelamento',  'Matrícula do Parcelamento'),
    ('registro_loteamento',     'Registro de Loteamento'),
    ('ocupacao',                'Ocupação / Distrito'),
    ('descricao_area',          'Descrição da Área'),
    ('registro_propriedade',    'Registro de Propriedade'),
]


def _parse(field, value):
    if value is None or str(value).strip() == '':
        return None
    return str(value).strip() or None


@areas_brutas_parceladas_bp.route('/assent/areas-brutas-parceladas/nova', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def nova():
    if request.method == 'POST':
        cols = ', '.join(f for f, _ in CAMPOS)
        placeholders = ', '.join('%s' for _ in CAMPOS)
        values = tuple(_parse(f, request.form.get(f)) for f, _ in CAMPOS)
        with get_db() as db:
            with db.cursor() as cursor:
                cursor.execute(f'INSERT INTO areas_parceladas ({cols}) VALUES ({placeholders})', values)
            db.commit()
        gravar_log('AREA_BRUTA_PARCELADA_CRIADA', (
            f"Município: {request.form.get('municipio') or '-'} | "
            f"Tipo: {request.form.get('tipo') or '-'} | "
            f"Descrição: {request.form.get('descricao_area') or '-'}"
        ))
        return redirect(url_for('dashboard.areas_brutas_parceladas'))
    return render_template('areas_brutas_parceladas_form.html', registro=None, tipos=TIPOS, campos=CAMPOS,
                           titulo='Nova Área Bruta Parcelada')


@areas_brutas_parceladas_bp.route('/assent/areas-brutas-parceladas/<int:registro_id>/editar', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            if request.method == 'POST':
                fields = [f for f, _ in CAMPOS]
                set_clause = ', '.join(f'{f}=%s' for f in fields)
                values = tuple(_parse(f, request.form.get(f)) for f in fields)
                cursor.execute(f'UPDATE areas_parceladas SET {set_clause} WHERE id=%s', values + (registro_id,))
                db.commit()
                gravar_log('AREA_BRUTA_PARCELADA_EDITADA', (
                    f"ID: {registro_id} | "
                    f"Município: {request.form.get('municipio') or '-'} | "
                    f"Tipo: {request.form.get('tipo') or '-'} | "
                    f"Descrição: {request.form.get('descricao_area') or '-'}"
                ))
                return redirect(url_for('dashboard.areas_brutas_parceladas'))
            cursor.execute('SELECT * FROM areas_parceladas WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()
    if not registro:
        return redirect(url_for('dashboard.areas_brutas_parceladas'))
    return render_template('areas_brutas_parceladas_form.html', registro=registro, tipos=TIPOS, campos=CAMPOS,
                           titulo='Editar Área Bruta Parcelada')


@areas_brutas_parceladas_bp.route('/assent/areas-brutas-parceladas/<int:registro_id>/excluir', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT municipio, descricao_area, tipo FROM areas_parceladas WHERE id=%s', (registro_id,))
            r = cursor.fetchone() or {}
            cursor.execute('DELETE FROM areas_parceladas WHERE id=%s', (registro_id,))
        db.commit()
    gravar_log('AREA_BRUTA_PARCELADA_EXCLUIDA', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Tipo: {r.get('tipo') or '-'} | "
        f"Descrição: {r.get('descricao_area') or '-'}"
    ))
    return redirect(url_for('dashboard.areas_brutas_parceladas'))
