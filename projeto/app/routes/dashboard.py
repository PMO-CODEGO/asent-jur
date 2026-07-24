from flask import Blueprint, render_template, session, redirect, url_for, abort
from app.utils.decorators import role_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route('/assent/inicio')
@role_required('assent', 'admin', 'assent_gestor')
def inicio_assent():
    return render_template('inicio_assent.html')

@dashboard_bp.route('/assent/controle-area')
@role_required('assent', 'admin', 'assent_gestor')
def controle_area():
    return render_template('controle_area.html')

@dashboard_bp.route('/assent/areas-parceladas')
@role_required('assent', 'admin', 'assent_gestor')
def areas_parceladas():
    return render_template('areas_parceladas.html')

@dashboard_bp.route('/assent/areas-brutas')
@role_required('assent', 'admin', 'assent_gestor')
def areas_brutas():
    from app.db import get_db
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM areas_brutas ORDER BY tipo, municipio, qtd")
            registros = cursor.fetchall()

    import re

    def _parse_brl(val):
        """Tenta interpretar val como número e retorna float, ou None."""
        if not val:
            return None
        s = str(val).strip()
        # remove prefixos monetários antigos (R$, CR$, Ncz$, etc.)
        s = re.sub(r'^[A-Za-z$\s]+', '', s).strip()
        if not s:
            return None
        # detecta formato BR (1.234.567,89) vs US (1234567.89)
        if re.match(r'^\d{1,3}(\.\d{3})+(,\d+)?$', s):
            # formato BR com pontos de milhar
            s = s.replace('.', '').replace(',', '.')
        else:
            # formato US ou número puro — só substitui vírgula por ponto se necessário
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    def _fmt_brl(n):
        return 'R$ {:,.2f}'.format(n).replace(',', 'X').replace('.', ',').replace('X', '.')

    for r in registros:
        # formata ocupacao se for valor numérico
        raw_ocup = r.get('ocupacao') or ''
        n = _parse_brl(raw_ocup) if re.match(r'^[\d.,]+$', raw_ocup.strip()) else None
        r['ocupacao_fmt'] = _fmt_brl(n) if n is not None else None

        # formata valor_imovel para exibição uniforme em R$
        vi = r.get('valor_imovel')
        if vi and not r.get('valor_conjunto'):
            n2 = _parse_brl(vi)
            r['valor_imovel_fmt'] = _fmt_brl(n2) if n2 is not None else str(vi)
        else:
            r['valor_imovel_fmt'] = None

    return render_template('areas_brutas.html', registros=registros)

DISTRITOS = {
    "daia-anapolis": {
        "nome": "DAIA — Distrito Agroindustrial de Anápolis",
        "tipo": "agroindustrial",
        "municipio": "Anápolis",
        "descricao": "Um dos maiores distritos industriais do Centro-Oeste. Abriga empresas dos setores farmacêutico, automotivo, alimentício e químico.",
        "empresas": "Mais de 200 empresas instaladas",
    },
    "dig-goiania": {
        "nome": "DIG — Distrito Industrial de Goiânia",
        "tipo": "industrial",
        "municipio": "Goiânia",
        "descricao": "Localizado na capital do estado, concentra indústrias de médio porte nos setores metal-mecânico, alimentício e de confecções.",
        "empresas": "Diversas indústrias de médio porte",
    },
    "aparecida-de-goiania": {
        "nome": "Distrito Industrial de Aparecida de Goiânia",
        "tipo": "industrial",
        "municipio": "Aparecida de Goiânia",
        "descricao": "Importante polo industrial da região metropolitana de Goiânia, com destaque para os setores de construção civil e alimentos.",
        "empresas": "Polo da região metropolitana",
    },
    "rio-verde": {
        "nome": "Distrito Industrial de Rio Verde",
        "tipo": "industrial",
        "municipio": "Rio Verde",
        "descricao": "Principal polo agroindustrial do sudoeste goiano. Concentra frigoríficos, esmagadoras de soja e indústrias de insumos agrícolas.",
        "empresas": "Polo do agronegócio do sudoeste",
    },
    "itumbiara": {
        "nome": "Distrito Industrial de Itumbiara",
        "tipo": "industrial",
        "municipio": "Itumbiara",
        "descricao": "Localizado no sul do estado, na divisa com Minas Gerais. Atua com indústrias de couros, plásticos e produtos químicos.",
        "empresas": "Polo do sul goiano",
    },
    "catalao": {
        "nome": "Distrito Industrial de Catalão",
        "tipo": "industrial",
        "municipio": "Catalão",
        "descricao": "Centro industrial estratégico, com destaque para mineração de nióbio e fósforo, além de montagem de veículos e fertilizantes.",
        "empresas": "Polo mineral e automotivo",
    },
    "daim-morrinhos": {
        "nome": "DAIM — Distrito Agroindustrial de Morrinhos",
        "tipo": "agroindustrial",
        "municipio": "Morrinhos",
        "descricao": "Distrito voltado ao processamento de produtos agropecuários da região sul goiana, com forte presença do setor lácteo.",
        "empresas": "Foco em lácteos e agropecuária",
    },
    "senador-canedo": {
        "nome": "Distrito Industrial de Senador Canedo",
        "tipo": "industrial",
        "municipio": "Senador Canedo",
        "descricao": "Parte da região metropolitana de Goiânia. Abriga indústrias dos setores alimentício, logística e distribuição.",
        "empresas": "Polo logístico metropolitano",
    },
    "trindade": {
        "nome": "Distrito Industrial de Trindade",
        "tipo": "industrial",
        "municipio": "Trindade",
        "descricao": "Cidade da Grande Goiânia com crescimento industrial nos setores de construção civil e materiais de construção.",
        "empresas": "Construção civil e materiais",
    },
    "inhumas": {
        "nome": "Distrito Industrial de Inhumas",
        "tipo": "industrial",
        "municipio": "Inhumas",
        "descricao": "Polo do setor agroindustrial a oeste de Goiânia, com indústrias de beneficiamento de grãos e fruticultura.",
        "empresas": "Beneficiamento de grãos",
    },
    "jatai": {
        "nome": "Distrito Industrial de Jataí",
        "tipo": "industrial",
        "municipio": "Jataí",
        "descricao": "Importante polo do sudoeste goiano, com vocação para o processamento de grãos, carnes e laticínios.",
        "empresas": "Grãos, carnes e laticínios",
    },
    "luziania": {
        "nome": "Distrito Industrial de Luziânia",
        "tipo": "industrial",
        "municipio": "Luziânia",
        "descricao": "Localizado no Entorno do Distrito Federal, atende a demanda das duas regiões com indústrias de alimentos e plásticos.",
        "empresas": "Polo do Entorno do DF",
    },
    "formosa": {
        "nome": "Distrito Industrial de Formosa",
        "tipo": "industrial",
        "municipio": "Formosa",
        "descricao": "Polo industrial no nordeste goiano, próximo ao DF, com atividades de mineração e beneficiamento de calcário.",
        "empresas": "Mineração e calcário",
    },
    "caldas-novas": {
        "nome": "Distrito Industrial de Caldas Novas",
        "tipo": "industrial",
        "municipio": "Caldas Novas",
        "descricao": "Além do turismo, possui indústrias voltadas ao beneficiamento de alimentos e produção de embalagens para o setor hoteleiro.",
        "empresas": "Alimentos e embalagens",
    },
    "parque-tec-ufg": {
        "nome": "Parque Tecnológico de Goiás — UFG",
        "tipo": "tecnologico",
        "municipio": "Goiânia",
        "descricao": "Hub de inovação vinculado à Universidade Federal de Goiás, focado em startups de tecnologia, biotecnologia e agritech.",
        "empresas": "Startups e empresas de inovação",
    },
    "neropolis": {
        "nome": "Distrito Agroindustrial de Nerópolis",
        "tipo": "agroindustrial",
        "municipio": "Nerópolis",
        "descricao": "Região agroindustrial ao norte da Grande Goiânia com destaque para avicultura, suinocultura e processamento de carnes.",
        "empresas": "Avicultura e suinocultura",
    },
    "goianesia": {
        "nome": "Distrito Industrial de Goianésia",
        "tipo": "agroindustrial",
        "municipio": "Goianésia",
        "descricao": "Principal polo sucroalcooleiro do estado. Abriga usinas de cana-de-açúcar e produção de etanol do centro-norte goiano.",
        "empresas": "Polo sucroalcooleiro",
    },
    "quirinopolis": {
        "nome": "Distrito Industrial de Quirinópolis",
        "tipo": "agroindustrial",
        "municipio": "Quirinópolis",
        "descricao": "Região de grande expansão do setor sucroalcooleiro, com usinas e complexos agroindustriais de cana-de-açúcar.",
        "empresas": "Setor sucroalcooleiro",
    },
}

TIPO_LABELS = {
    "agroindustrial": "Distrito Agroindustrial",
    "industrial": "Distrito Industrial",
    "tecnologico": "Parque Tecnológico",
}

@dashboard_bp.route('/mapa-distritos')
@role_required('assent', 'jur', 'admin', 'assent_gestor', 'jur_gestor')
def mapa_distritos():
    return render_template('mapa_distritos.html')

@dashboard_bp.route('/mapa-distritos/<slug>')
@role_required('assent', 'jur', 'admin', 'assent_gestor', 'jur_gestor')
def distrito_detalhe(slug):
    distrito = DISTRITOS.get(slug)
    if not distrito:
        abort(404)
    tipo_label = TIPO_LABELS.get(distrito['tipo'], distrito['tipo'])
    return render_template('distrito_detalhe.html', distrito=distrito, slug=slug, tipo_label=tipo_label)

@dashboard_bp.route('/menu/<modo>')
@role_required('assent', 'jur', 'admin','assent_gestor','jur_gestor')
def menu(modo):

    if modo == "jur" or modo == "jur_gestor":
        return render_template('menu_jur.html')

    return render_template('menu.html')

