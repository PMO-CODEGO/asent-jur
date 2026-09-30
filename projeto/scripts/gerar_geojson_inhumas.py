"""Gera app/static/geo/inhumas.geojson a partir do DXF do Distrito Agroindustrial de Inhumas.

Cada contorno de lote é ligado ao seu próprio módulo pelo texto da layer "URB ID_MOD"
que fica dentro dele (ex.: "DAIQ4M3"), que é o mesmo id_modulo do Cadastro de Módulos
(municipal_lots). O restante (matrícula, empresa, situação) é buscado no banco em tempo
de execução por app/routes/mapas_interativo.py.

Os contornos vêm da layer "URB DES_MOD" e também da "URB ID_MOD", porque no DXF atual o
contorno do lote DAIQ3M6 foi desenhado nessa segunda layer.

Os ids dos polígonos que já existiam no .geojson anterior são mantidos (são eles que
casam com as linhas da tabela mapas_interativo_inhumas); polígonos novos recebem ids
a partir do maior id existente.

Ferramenta offline (precisa de `pip install ezdxf shapely`). Uso, na raiz do projeto:

    python scripts/gerar_geojson_inhumas.py "caminho/MAPA INHUMAS-R01.dxf"
"""
import json
import os
import sys

from shapely.geometry import shape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.services.dxf_geojson_service import converter_dxf_para_features  # noqa: E402

LAYERS_POLIGONOS = ['URB DES_MOD', 'URB ID_MOD']
LAYER_IDS = 'URB ID_MOD'
SIGLA_MODULO = 'DAI'
CAMINHO_GEOJSON = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'geo', 'inhumas.geojson')


def _ids_anteriores():
    """Lista (geometria, id) do .geojson atual, para manter os ids dos polígonos."""
    if not os.path.exists(CAMINHO_GEOJSON):
        return []
    with open(CAMINHO_GEOJSON, encoding='utf-8') as f:
        anterior = json.load(f)
    return [(shape(feat['geometry']), feat['id']) for feat in anterior.get('features', [])]


def gerar(caminho_dxf):
    # distancia_maxima_rotulo=0: só aceita o texto que está dentro do contorno, para não
    # "emprestar" o código de um lote vizinho a um contorno sem texto
    features = []
    for layer in LAYERS_POLIGONOS:
        features += converter_dxf_para_features(caminho_dxf, layer, LAYER_IDS, distancia_maxima_rotulo=0)

    anteriores = _ids_anteriores()
    proximo_id = max([i for _, i in anteriores], default=0) + 1
    saida = []
    for feat in features:
        geom = shape(feat['geometry'])
        ponto = geom.representative_point()
        id_poligono = next((i for g, i in anteriores if g.contains(ponto)), None)
        if id_poligono is None:
            id_poligono = proximo_id
            proximo_id += 1

        rotulo = (feat['rotulo'] or '').strip() or None
        propriedades = {'id': id_poligono, 'rotulo': rotulo, 'area_m2': feat['area_m2']}
        if rotulo and rotulo.upper().startswith(SIGLA_MODULO):
            propriedades['modulos'] = [rotulo.upper()]
        saida.append({'type': 'Feature', 'id': id_poligono, 'properties': propriedades, 'geometry': feat['geometry']})

    ids = [f['id'] for f in saida]
    if len(ids) != len(set(ids)):
        raise SystemExit('Dois contornos caíram no mesmo polígono anterior; confira o DXF.')

    saida.sort(key=lambda f: f['id'])
    with open(CAMINHO_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': saida}, f, ensure_ascii=False)
    return saida


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    resultado = gerar(sys.argv[1])
    for feat in resultado:
        p = feat['properties']
        print(p['id'], p['rotulo'], p['area_m2'], p.get('modulos', ''))
    print(len(resultado), 'polígonos gravados em', os.path.normpath(CAMINHO_GEOJSON))
