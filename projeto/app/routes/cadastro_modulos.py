from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

cadastro_modulos_bp = Blueprint('cadastro_modulos', __name__)

CAMPOS = [
    ('municipio',                 'Município'),
    ('distrito',                  'Distrito'),
    ('quadra',                    'Quadra'),
    ('modulo_s',                  'Módulo(s)'),
    ('qtd_modulos',               'Qtd. Módulos'),
    ('tamanho_m2',                'Tamanho (m²)'),
    ('empresa',                   'Empresa'),
    ('cnpj',                      'CNPJ'),
    ('status_de_assentamento',    'Status de Assentamento'),
    ('ramo_de_atividade',         'Ramo de Atividade'),
    ('empregos_gerados',          'Empregos Gerados'),
    ('imovel_regular_irregular',  'Regular / Irregular'),
    ('acao_judicial',             'Ação Judicial'),
    ('matricula_s',               'Matrícula(s)'),
    ('data_escrituracao',         'Data de Escrituração'),
    ('processo_sei',              'Processo SEI'),
    ('status',                    'Status'),
]


@cadastro_modulos_bp.route('/assent/cadastro-modulos/novo', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def novo():
    if request.method == 'POST':
        cols = ', '.join(f for f, _ in CAMPOS)
        placeholders = ', '.join('%s' for _ in CAMPOS)
        values = tuple(request.form.get(f) or None for f, _ in CAMPOS)
        with get_db() as db:
            with db.cursor() as cursor:
                cursor.execute(f'INSERT INTO municipal_lots ({cols}) VALUES ({placeholders})', values)
            db.commit()
        gravar_log('MODULO_CRIADO', (
            f"Município: {request.form.get('municipio') or '-'} | "
            f"Distrito: {request.form.get('distrito') or '-'} | "
            f"Módulo: {request.form.get('modulo_s') or '-'}"
        ))
        return redirect(url_for('dashboard.cadastro_modulos'))
    return render_template('cadastro_modulos_form.html', registro=None, campos=CAMPOS,
                           titulo='Novo Módulo')


@cadastro_modulos_bp.route('/assent/cadastro-modulos/<int:registro_id>/editar', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            if request.method == 'POST':
                fields = [f for f, _ in CAMPOS]
                set_clause = ', '.join(f'{f}=%s' for f in fields)
                values = tuple(request.form.get(f) or None for f in fields)
                cursor.execute(f'UPDATE municipal_lots SET {set_clause} WHERE id=%s', values + (registro_id,))
                db.commit()
                gravar_log('MODULO_EDITADO', (
                    f"ID: {registro_id} | "
                    f"Município: {request.form.get('municipio') or '-'} | "
                    f"Distrito: {request.form.get('distrito') or '-'} | "
                    f"Módulo: {request.form.get('modulo_s') or '-'}"
                ))
                return redirect(url_for('dashboard.cadastro_modulos'))
            cursor.execute('SELECT * FROM municipal_lots WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()
    if not registro:
        return redirect(url_for('dashboard.cadastro_modulos'))
    return render_template('cadastro_modulos_form.html', registro=registro, campos=CAMPOS,
                           titulo='Editar Módulo')


@cadastro_modulos_bp.route('/assent/cadastro-modulos/<int:registro_id>/excluir', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT municipio, distrito, modulo_s FROM municipal_lots WHERE id=%s', (registro_id,))
            r = cursor.fetchone() or {}
            cursor.execute('DELETE FROM municipal_lots WHERE id=%s', (registro_id,))
        db.commit()
    gravar_log('MODULO_EXCLUIDO', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Distrito: {r.get('distrito') or '-'} | "
        f"Módulo: {r.get('modulo_s') or '-'}"
    ))
    return redirect(url_for('dashboard.cadastro_modulos'))
