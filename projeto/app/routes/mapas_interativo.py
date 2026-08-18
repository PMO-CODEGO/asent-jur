from flask import Blueprint, request, redirect, url_for
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

mapas_interativo_bp = Blueprint('mapas_interativo', __name__)

STATUS_VALIDOS = {'Livre', 'Ocupado'}


def _campo(form, nome):
    return form.get(nome, '').strip() or None


@mapas_interativo_bp.route('/mapa-distritos/daia/perimetros/novo', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def novo():
    perimetro = _campo(request.form, 'perimetro')
    area = _campo(request.form, 'area')
    coordenadas = _campo(request.form, 'coordenadas')
    status = request.form.get('status') if request.form.get('status') in STATUS_VALIDOS else None

    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO mapas_interativo_anapolis (perimetro, area, coordenadas, status) VALUES (%s, %s, %s, %s)",
                (perimetro, area, coordenadas, status)
            )
            db.commit()

    gravar_log('PERIMETRO_DAIA_CRIADO', f"Perímetro: {perimetro or '-'}")
    return redirect(url_for('dashboard.distrito_detalhe', slug='daia'))


@mapas_interativo_bp.route('/mapa-distritos/daia/perimetros/<int:registro_id>/editar', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(registro_id):
    perimetro = _campo(request.form, 'perimetro')
    area = _campo(request.form, 'area')
    coordenadas = _campo(request.form, 'coordenadas')
    status = request.form.get('status') if request.form.get('status') in STATUS_VALIDOS else None

    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE mapas_interativo_anapolis SET perimetro=%s, area=%s, coordenadas=%s, status=%s WHERE id=%s",
                (perimetro, area, coordenadas, status, registro_id)
            )
            db.commit()

    gravar_log('PERIMETRO_DAIA_EDITADO', f"ID: {registro_id} | Perímetro: {perimetro or '-'}")
    return redirect(url_for('dashboard.distrito_detalhe', slug='daia'))


@mapas_interativo_bp.route('/mapa-distritos/daia/perimetros/<int:registro_id>/excluir', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM mapas_interativo_anapolis WHERE id=%s", (registro_id,))
            db.commit()

    gravar_log('PERIMETRO_DAIA_EXCLUIDO', f"ID: {registro_id}")
    return redirect(url_for('dashboard.distrito_detalhe', slug='daia'))
