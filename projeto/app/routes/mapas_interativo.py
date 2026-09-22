import json
import os
from flask import Blueprint, request, redirect, url_for, jsonify, current_app, abort
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log

mapas_interativo_bp = Blueprint('mapas_interativo', __name__)

STATUS_VALIDOS = {'Livre', 'Ocupado'}

# slug (mesmo usado em dashboard.DISTRITOS) -> tabela de perímetros + arquivo .geojson
# estático (app/static/geo/) daquele distrito. Adicionar um distrito novo ao mapa
# interativo é só criar a tabela (mesmo esquema de mapas_interativo_anapolis), gerar o
# .geojson (ver app/services/dxf_geojson_service.py) e incluir uma entrada aqui.
DISTRITOS_MAPA = {
    'daia': {'tabela': 'mapas_interativo_anapolis', 'geojson': 'glebasok.geojson'},
    'inhumas': {'tabela': 'mapas_interativo_inhumas', 'geojson': 'inhumas.geojson'},
}


def _config(slug):
    config = DISTRITOS_MAPA.get(slug)
    if not config:
        abort(404)
    return config


def _campo(form, nome):
    return form.get(nome, '').strip() or None


@mapas_interativo_bp.route('/mapa-distritos/<slug>/geojson')
@role_required('assent', 'jur', 'admin', 'assent_gestor', 'jur_gestor')
def geojson(slug):
    config = _config(slug)
    caminho = os.path.join(current_app.static_folder, 'geo', config['geojson'])
    with open(caminho, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(f"SELECT id, perimetro, area, coordenadas, status FROM {config['tabela']}")
            linhas = cursor.fetchall()

            # Resolve id_modulo -> id/status do Cadastro de Módulos, pra virar link clicável e
            # colorir o polígono pela situação de assentamento real (ver bloco "modulos" nas
            # properties do .geojson, vindo da planilha de correspondência entre agrupamento do
            # DXF e id_modulo real).
            dados_por_modulo = {}
            todos_modulos = {
                m for feature in geojson_data.get('features', [])
                for m in feature.get('properties', {}).get('modulos', [])
            }
            if todos_modulos:
                formato = ', '.join(['%s'] * len(todos_modulos))
                cursor.execute(
                    f"SELECT id, id_modulo, status_de_assentamento FROM municipal_lots WHERE id_modulo IN ({formato})",
                    tuple(todos_modulos)
                )
                dados_por_modulo = {row['id_modulo']: row for row in cursor.fetchall()}

    dados_por_id = {str(item['id']): item for item in linhas}

    for feature in geojson_data.get('features', []):
        modulos = feature.get('properties', {}).get('modulos')
        if modulos:
            feature['properties']['modulos_detalhe'] = [
                {'id_modulo': m, 'registro_id': (dados_por_modulo.get(m) or {}).get('id')} for m in modulos
            ]
            # Situação de assentamento do polígono: só atribui uma cor certa quando todos os
            # módulos daquele grupo compartilham a mesma situação; se estiver misto (ou faltando
            # dado), deixa null em vez de chutar uma das situações.
            situacoes = {(dados_por_modulo.get(m) or {}).get('status_de_assentamento') for m in modulos}
            feature['properties']['status_assentamento'] = situacoes.pop() if len(situacoes) == 1 else None

        poly_id = str(feature.get('id') or feature.get('properties', {}).get('id'))
        info = dados_por_id.get(poly_id)
        if info:
            feature['properties']['perimetro'] = info.get('perimetro')
            feature['properties']['area'] = info.get('area')
            feature['properties']['status'] = info.get('status')

    return jsonify({'sucesso': True, 'dados': geojson_data})


@mapas_interativo_bp.route('/mapa-distritos/<slug>/perimetros/novo', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def novo(slug):
    config = _config(slug)
    perimetro = _campo(request.form, 'perimetro')
    area = _campo(request.form, 'area')
    coordenadas = _campo(request.form, 'coordenadas')
    status = request.form.get('status') if request.form.get('status') in STATUS_VALIDOS else None

    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {config['tabela']} (perimetro, area, coordenadas, status) VALUES (%s, %s, %s, %s)",
                (perimetro, area, coordenadas, status)
            )
            db.commit()

    gravar_log('PERIMETRO_CRIADO', f"Distrito: {slug} | Perímetro: {perimetro or '-'}")
    return redirect(url_for('dashboard.distrito_detalhe', slug=slug))


@mapas_interativo_bp.route('/mapa-distritos/<slug>/perimetros/<int:registro_id>/editar', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(slug, registro_id):
    config = _config(slug)
    perimetro = _campo(request.form, 'perimetro')
    area = _campo(request.form, 'area')
    coordenadas = _campo(request.form, 'coordenadas')
    status = request.form.get('status') if request.form.get('status') in STATUS_VALIDOS else None

    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(
                f"UPDATE {config['tabela']} SET perimetro=%s, area=%s, coordenadas=%s, status=%s WHERE id=%s",
                (perimetro, area, coordenadas, status, registro_id)
            )
            db.commit()

    gravar_log('PERIMETRO_EDITADO', f"Distrito: {slug} | ID: {registro_id} | Perímetro: {perimetro or '-'}")
    return redirect(url_for('dashboard.distrito_detalhe', slug=slug))


@mapas_interativo_bp.route('/mapa-distritos/<slug>/perimetros/<int:registro_id>/excluir', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def excluir(slug, registro_id):
    config = _config(slug)
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute(f"DELETE FROM {config['tabela']} WHERE id=%s", (registro_id,))
            db.commit()

    gravar_log('PERIMETRO_EXCLUIDO', f"Distrito: {slug} | ID: {registro_id}")
    return redirect(url_for('dashboard.distrito_detalhe', slug=slug))
