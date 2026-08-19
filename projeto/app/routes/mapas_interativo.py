import json
import os
from flask import Blueprint, request, redirect, url_for, jsonify, current_app
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

mapas_interativo_bp = Blueprint('mapas_interativo', __name__)

STATUS_VALIDOS = {'Livre', 'Ocupado'}


def _campo(form, nome):
    return form.get(nome, '').strip() or None


@mapas_interativo_bp.route('/mapa-distritos/daia/geojson')
@role_required('assent', 'jur', 'admin', 'assent_gestor', 'jur_gestor')
def geojson():
    caminho = os.path.join(current_app.static_folder, 'geo', 'glebasok.geojson')
    with open(caminho, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, perimetro, area, coordenadas, status FROM mapas_interativo_anapolis")
            linhas = cursor.fetchall()

    dados_por_id = {str(item['id']): item for item in linhas}

    for feature in geojson_data.get('features', []):
        poly_id = str(feature.get('id') or feature.get('properties', {}).get('id'))
        info = dados_por_id.get(poly_id)
        if info:
            feature['properties']['perimetro'] = info.get('perimetro')
            feature['properties']['area'] = info.get('area')
            feature['properties']['status'] = info.get('status')

    return jsonify({'sucesso': True, 'dados': geojson_data})


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
