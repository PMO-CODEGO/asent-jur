"""Conversão de levantamento topográfico em DXF (AutoCAD) para GeoJSON, usada para
alimentar os mapas interativos de distritos (ver app/static/geo/*.geojson e
app/routes/mapas_interativo.py).

Ferramenta offline: não é usada em tempo de execução pelo app (que só lê o .geojson já
gerado), então as dependências pesadas (ezdxf, shapely) não entram em requirements.txt —
instale-as manualmente (`pip install ezdxf shapely`) para rodar isto.

Uso típico, para gerar/atualizar o mapa de um distrito a partir de um novo DXF:

    from app.services.dxf_geojson_service import converter_dxf_para_features

    features = converter_dxf_para_features('MAPA X-R01.dxf', layer_poligonos='URB DES_MOD', layer_ids='ID_AR')
    # features: lista de dicts {"id": <int sequencial>, "rotulo": <str ou None>, "area_m2": <float>,
    #            "geometry": <geometria GeoJSON (dict)>}
    # a partir daqui: salvar geometry em app/static/geo/<slug>.geojson (ver gerar_mapa_distrito.py)
    # e popular a tabela mapas_interativo_<slug> com id/rotulo/area_m2.
"""
import math

import ezdxf
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.ops import polygonize
from shapely.validation import make_valid


def _interpolar_bulge(p1, p2, bulge, segmentos=16):
    """Calcula pontos ao longo do arco entre p1 e p2 a partir do 'bulge' (curvatura) do DXF."""
    if abs(bulge) < 1e-6:
        return [p1, p2]

    theta = 4.0 * math.atan(bulge)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    corda = math.hypot(dx, dy)
    if corda < 1e-6:
        return [p1]

    raio = corda / (2.0 * math.sin(abs(theta) / 2.0))
    mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
    d_centro = math.sqrt(max(0.0, raio**2 - (corda / 2.0) ** 2))
    sinal = 1.0 if bulge > 0 else -1.0
    cx = mx + (-dy / corda * d_centro * sinal)
    cy = my + (dx / corda * d_centro * sinal)

    ang1 = math.atan2(p1[1] - cy, p1[0] - cx)
    ang2 = math.atan2(p2[1] - cy, p2[0] - cx)
    if bulge > 0 and ang2 < ang1:
        ang2 += 2.0 * math.pi
    elif bulge < 0 and ang1 < ang2:
        ang1 += 2.0 * math.pi

    return [(cx + raio * math.cos(ang1 + (i / segmentos) * (ang2 - ang1)),
             cy + raio * math.sin(ang1 + (i / segmentos) * (ang2 - ang1)))
            for i in range(segmentos + 1)]


def _extrair_vertices(entity):
    """Extrai os vértices de uma LWPOLYLINE/POLYLINE, interpolando arcos (bulge) do AutoCAD."""
    dxftype = entity.dxftype()

    if dxftype == 'LWPOLYLINE':
        pts = entity.get_points('xyb')
        if not pts:
            return []
        pontos = []
        for i, (x, y, bulge) in enumerate(pts):
            atual = (x, y)
            if i < len(pts) - 1:
                prox = (pts[i + 1][0], pts[i + 1][1])
            elif entity.is_closed:
                prox = (pts[0][0], pts[0][1])
            else:
                pontos.append(atual)
                break
            if abs(bulge) > 1e-6:
                pontos.extend(_interpolar_bulge(atual, prox, bulge)[:-1])
            else:
                pontos.append(atual)
        return pontos

    if dxftype == 'POLYLINE':
        try:
            return [(p[0], p[1]) for p in entity.flattening(distance=0.01)]
        except Exception:
            return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]

    return []


def _extrair_entidades(layout, layer_poligonos, layer_ids):
    """Varre um layout (modelspace ou bloco) e extrai polígonos + rótulos de texto, recursivamente
    dentro de blocos (INSERT)."""
    poligonos, linhas_soltas, rotulos = [], [], []

    for entity in layout:
        dxftype = entity.dxftype()
        layer_atual = entity.dxf.layer.strip().upper() if hasattr(entity.dxf, 'layer') else ''

        if dxftype == 'INSERT':
            bloco = entity.doc.blocks.get(entity.dxf.name)
            if bloco:
                sub_poly, sub_rot = _extrair_entidades(bloco, layer_poligonos, layer_ids)
                poligonos.extend(sub_poly)
                rotulos.extend(sub_rot)
            continue

        if layer_atual == layer_poligonos.strip().upper():
            if dxftype in ('LWPOLYLINE', 'POLYLINE'):
                vertices = _extrair_vertices(entity)
                if len(vertices) >= 3:
                    if vertices[0] != vertices[-1]:
                        vertices.append(vertices[0])
                    poly = Polygon(vertices)
                    if not poly.is_valid:
                        poly = make_valid(poly)
                    if not poly.is_empty:
                        if poly.geom_type == 'MultiPolygon':
                            poligonos.extend(list(poly.geoms))
                        elif poly.geom_type == 'Polygon':
                            poligonos.append(poly)
            elif dxftype == 'LINE':
                linhas_soltas.append(((entity.dxf.start.x, entity.dxf.start.y),
                                      (entity.dxf.end.x, entity.dxf.end.y)))

        if layer_atual == layer_ids.strip().upper() and dxftype in ('TEXT', 'MTEXT'):
            texto = entity.text.strip() if dxftype == 'MTEXT' else entity.dxf.text.strip()
            posicao = getattr(entity.dxf, 'insert', None) or getattr(entity.dxf, 'align_point', None)
            if posicao and texto:
                rotulos.append({'texto': texto, 'ponto': Point(posicao[0], posicao[1])})

    if linhas_soltas:
        for poly in polygonize([LineString([p1, p2]) for p1, p2 in linhas_soltas]):
            if not poly.is_valid:
                poly = make_valid(poly)
            if not poly.is_empty and poly.geom_type == 'Polygon':
                poligonos.append(poly)

    return poligonos, rotulos


def converter_dxf_para_features(caminho_dxf, layer_poligonos, layer_ids, distancia_maxima_rotulo=15.0):
    """Lê um DXF e devolve uma lista de features prontas para virar GeoJSON + linhas de banco.

    Cada item: {"id": <int sequencial, 1-based>, "rotulo": <str ou None, do texto mais
    próximo/contido na layer de IDs>, "area_m2": <float>, "geometry": <geometria GeoJSON>}.
    O "id" sequencial é o que casa com o id (auto_increment) da tabela mapas_interativo_<slug>
    no banco — ver app/routes/mapas_interativo.py.
    """
    try:
        doc = ezdxf.readfile(caminho_dxf)
    except Exception:
        from ezdxf.recover import readfile as recover_readfile
        doc, _ = recover_readfile(caminho_dxf)

    poligonos, rotulos = _extrair_entidades(doc.modelspace(), layer_poligonos, layer_ids)

    features = []
    for i, poly in enumerate(poligonos, start=1):
        rotulo_encontrado, menor_distancia = None, float('inf')
        for item in rotulos:
            ponto = item['ponto']
            if poly.contains(ponto) or poly.intersects(ponto):
                rotulo_encontrado = item['texto']
                break
            distancia = poly.distance(ponto)
            if distancia < menor_distancia and distancia <= distancia_maxima_rotulo:
                menor_distancia = distancia
                rotulo_encontrado = item['texto']

        features.append({
            'id': i,
            'rotulo': rotulo_encontrado,
            'area_m2': round(poly.area, 2),
            'geometry': mapping(poly),
        })

    return features
