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

def _carregar_tabela_parcelada(tabela):
    import re
    from app.db import get_db

    def _parse_brl(val):
        if not val:
            return None
        s = str(val).strip()
        s = re.sub(r'^[A-Za-z$\s]+', '', s).strip()
        if not s:
            return None
        if re.match(r'^\d{1,3}(\.\d{3})+(,\d+)?$', s):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    def _fmt_brl(n):
        if n is None:
            return None
        return 'R$ {:,.2f}'.format(n).replace(',', 'X').replace('.', ',').replace('X', '.')

    def _fmt_int_br(val):
        if not val:
            return val
        s = str(val).strip().replace('.', '')
        try:
            return '{:,}'.format(int(s)).replace(',', '.')
        except ValueError:
            return val

    def _fmt_m2_br(val):
        if val is None:
            return '-'
        try:
            from decimal import Decimal
            d = Decimal(str(val)).normalize()
            s = format(d, 'f')
        except Exception:
            s = str(val).strip()
            return s if s else '-'
        if '.' in s:
            int_part, dec_part = s.split('.')
        else:
            int_part, dec_part = s, ''
        neg = s.startswith('-')
        int_formatted = '{:,}'.format(abs(int(int_part))).replace(',', '.')
        if neg:
            int_formatted = '-' + int_formatted
        return (int_formatted + ',' + dec_part) if dec_part else int_formatted

    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute(f"SELECT * FROM {tabela} ORDER BY municipio, descricao_area")
            registros = cursor.fetchall()
    for r in registros:
        r['area_total_m2_fmt'] = _fmt_m2_br(_parse_brl(r.get('area_total_m2'))) if r.get('area_total_m2') else '-'
        vi = r.get('valor_imovel')
        n = _parse_brl(vi) if vi else None
        r['valor_imovel_fmt'] = _fmt_brl(n) if n is not None else (vi or '-')
        r['num_matricula_fmt'] = _fmt_int_br(r.get('num_matricula')) or '-'
        r['matricula_parcelamento_fmt'] = _fmt_int_br(r.get('matricula_parcelamento')) or '-'
    return registros


@dashboard_bp.route('/assent/distritos-regulares')
@role_required('assent', 'admin', 'assent_gestor')
def distritos_regulares():
    registros = _carregar_tabela_parcelada('areas_parceladas_regularizadas')
    return render_template('distritos_regulares.html', registros=registros)


@dashboard_bp.route('/assent/distritos-em-regularizacao')
@role_required('assent', 'admin', 'assent_gestor')
def distritos_em_regularizacao():
    registros = _carregar_tabela_parcelada('loteamentos_irregulares')
    return render_template('distritos_regularizacao.html', registros=registros)


@dashboard_bp.route('/assent/galerias')
@role_required('assent', 'admin', 'assent_gestor')
def galerias():
    registros = _carregar_tabela_parcelada('galerias_condominios')
    return render_template('galerias.html', registros=registros)

@dashboard_bp.route('/assent/areas-brutas')
@role_required('assent', 'admin', 'assent_gestor')
def areas_brutas():
    from app.db import get_db
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

    def _fmt_int_br(val):
        if not val:
            return val
        s = str(val).strip().replace('.', '')
        try:
            return '{:,}'.format(int(s)).replace(',', '.')
        except ValueError:
            return val

    def _fmt_m2_br(val):
        """Formata valor numérico de área em m² com separador BR e sem zeros finais."""
        if val is None:
            return '-'
        try:
            from decimal import Decimal, InvalidOperation
            d = Decimal(str(val)).normalize()
            s = format(d, 'f')
        except Exception:
            s = str(val).strip()
            return s if s else '-'
        if '.' in s:
            int_part, dec_part = s.split('.')
        else:
            int_part, dec_part = s, ''
        neg = s.startswith('-')
        int_formatted = '{:,}'.format(abs(int(int_part))).replace(',', '.')
        if neg:
            int_formatted = '-' + int_formatted
        return (int_formatted + ',' + dec_part) if dec_part else int_formatted

    from app.routes.areas_brutas import _anos_disponiveis
    ANOS_AVALIACAO = _anos_disponiveis('areas_brutas')

    def _carregar(tabela):
        with get_db() as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute(f"SELECT * FROM {tabela} ORDER BY municipio, descricao_area")
                registros = cursor.fetchall()

        for r in registros:
            # formata ocupacao se for valor numérico
            raw_ocup = r.get('ocupacao') or ''
            n = _parse_brl(raw_ocup) if re.match(r'^[\d.,]+$', raw_ocup.strip()) else None
            r['ocupacao_fmt'] = _fmt_brl(n) if n is not None else None

            # formata valor_imovel para exibição uniforme em R$
            vi = r.get('valor_imovel')
            if vi and not r.get('valor_conjunto'):
                n2 = _parse_brl(vi)
                r['valor_imovel_fmt'] = _fmt_brl(n2) if n2 is not None else _fmt_brl(_parse_brl(str(vi))) or str(vi)
            else:
                r['valor_imovel_fmt'] = None

            # formata reserva_legal_m2 (varchar) para exibição BR
            r['reserva_legal_m2_fmt'] = _fmt_m2_br(_parse_brl(r.get('reserva_legal_m2'))) if r.get('reserva_legal_m2') and r.get('reserva_legal_m2') != '-' else (r.get('reserva_legal_m2') or '-')

            # formata m² numéricos com padrão BR
            r['area_util_m2_fmt']  = _fmt_m2_br(r.get('area_util_m2'))
            r['area_total_m2_fmt'] = _fmt_m2_br(r.get('area_total_m2'))

            r['num_matricula_fmt'] = _fmt_int_br(r.get('num_matricula'))
            r['matricula_parcelamento_fmt'] = _fmt_int_br(r.get('matricula_parcelamento'))

            # avaliações do registro (colunas fixas por ano)
            avaliacoes = [
                {'ano': ano, 'valor_mercado': r.get(f'valor_mercado_{ano}'), 'valor_subsidiado': r.get(f'valor_subsidiado_{ano}')}
                for ano in ANOS_AVALIACAO
                if r.get(f'valor_mercado_{ano}') is not None or r.get(f'valor_subsidiado_{ano}') is not None
            ]
            r['avaliacoes'] = avaliacoes
            # última avaliação (maior ano)
            ultima = max(avaliacoes, key=lambda a: a['ano'], default=None)
            r['ultima_aval_ano']        = ultima['ano'] if ultima else None
            r['ultima_aval_mercado']    = ultima['valor_mercado'] if ultima else None
            r['ultima_aval_subsidiado'] = ultima['valor_subsidiado'] if ultima else None

        return registros

    imoveis = _carregar('areas_brutas')
    judiciais = _carregar('areas_brutas_judicial')

    return render_template('areas_brutas.html', imoveis=imoveis, judiciais=judiciais)

DISTRITOS = {
    "abadiania": {
        "nome": "Distrito Industrial de Abadiânia",
        "tipo": "industrial",
        "municipio": "Abadiânia",
        "descricao": "Distrito industrial localizado em Abadiânia, com atuação nos setores de materiais de construção e distribuição de insumos.",
        "empresas": "Materiais de construção e insumos",
    },
    "bela-vista": {
        "nome": "Distrito Industrial de Bela Vista de Goiás",
        "tipo": "industrial",
        "municipio": "Bela Vista de Goiás",
        "descricao": "Polo industrial da região sul da Grande Goiânia, com indústrias têxteis, de reciclagem e laticínios.",
        "empresas": "Têxtil, reciclagem e laticínios",
    },
    "daia": {
        "nome": "DAIA — Distrito Agroindustrial de Anápolis",
        "tipo": "agroindustrial",
        "municipio": "Anápolis",
        "descricao": "Um dos maiores distritos industriais do Centro-Oeste. Abriga empresas dos setores farmacêutico, automotivo, alimentício e químico.",
        "empresas": "Mais de 180 empresas instaladas",
    },
    "daiag": {
        "nome": "DAIAG — Distrito Agroindustrial de Aparecida de Goiânia",
        "tipo": "agroindustrial",
        "municipio": "Aparecida de Goiânia",
        "descricao": "Importante polo industrial da região metropolitana de Goiânia, com destaque para metalurgia, reciclagem e indústria química.",
        "empresas": "Metalurgia, reciclagem e química",
    },
    "daimo": {
        "nome": "DAIMO — Distrito Agroindustrial de Morrinhos",
        "tipo": "agroindustrial",
        "municipio": "Morrinhos",
        "descricao": "Distrito voltado ao processamento de produtos agropecuários da região sul goiana, com forte presença do setor lácteo e de construção.",
        "empresas": "Lácteos, agropecuária e construção",
    },
    "dapo": {
        "nome": "DAPO — Distrito Agroindustrial de Pontalina",
        "tipo": "agroindustrial",
        "municipio": "Pontalina",
        "descricao": "Distrito agroindustrial de Pontalina, com atuação em nutrição animal, cerâmica, cooperativas rurais e construção rodoviária.",
        "empresas": "Nutrição animal, cerâmica e cooperativas",
    },
    "darv-i": {
        "nome": "DARV I — Distrito Agroindustrial de Rio Verde I",
        "tipo": "agroindustrial",
        "municipio": "Rio Verde",
        "descricao": "Primeiro distrito agroindustrial de Rio Verde, polo do agronegócio do sudoeste goiano com indústrias de alimentos, metalurgia e plásticos.",
        "empresas": "Alimentos, metalurgia e plásticos",
    },
    "darv-ii": {
        "nome": "DARV II — Distrito Agroindustrial de Rio Verde II",
        "tipo": "agroindustrial",
        "municipio": "Rio Verde",
        "descricao": "Segundo distrito agroindustrial de Rio Verde, com atuação em sementes, montagens industriais, reciclagem e serviços.",
        "empresas": "Sementes, montagens e reciclagem",
    },
    "dasc": {
        "nome": "DASC — Distrito Agroindustrial de Senador Canedo",
        "tipo": "agroindustrial",
        "municipio": "Senador Canedo",
        "descricao": "Polo industrial de Senador Canedo, na região metropolitana de Goiânia. Concentra indústrias moveleiras, ambientais e de reciclagem.",
        "empresas": "Móveis, ambiental e reciclagem",
    },
    "diagri": {
        "nome": "DIAGRI — Distrito Agroindustrial de Goiatuba",
        "tipo": "agroindustrial",
        "municipio": "Goiatuba",
        "descricao": "Distrito agroindustrial de Goiatuba, com atuação em fertilizantes, transportes, laticínios, concreto e implementos agrícolas.",
        "empresas": "Fertilizantes, laticínios e transporte",
    },
    "dimic": {
        "nome": "DIMIC — Distrito Industrial Minero-Industrial de Catalão",
        "tipo": "industrial",
        "municipio": "Catalão",
        "descricao": "Centro industrial estratégico, com destaque para mineração de nióbio e fósforo, montagem de veículos e fertilizantes.",
        "empresas": "Mineração, automotivo e fertilizantes",
    },
    "disc": {
        "nome": "DISC — Distrito Industrial de Senador Canedo",
        "tipo": "industrial",
        "municipio": "Senador Canedo",
        "descricao": "Segundo polo industrial de Senador Canedo, com indústrias de alimentos, móveis, plásticos e farmacêuticos.",
        "empresas": "Alimentos, móveis e plásticos",
    },
    "goianesia": {
        "nome": "Distrito Industrial de Goianésia",
        "tipo": "industrial",
        "municipio": "Goianésia",
        "descricao": "Polo industrial de Goianésia, com atuação em metalurgia, etiquetas, lavanderias industriais, alimentos e serviços.",
        "empresas": "Metalurgia, alimentos e serviços",
    },
    "goianira": {
        "nome": "Distrito Industrial de Goianira",
        "tipo": "industrial",
        "municipio": "Goianira",
        "descricao": "Polo industrial de Goianira, com forte presença de indústrias de calçados, confecções, cosméticos, plásticos e metalurgia.",
        "empresas": "Calçados, confecções e cosméticos",
    },
    "inhumas": {
        "nome": "Distrito Industrial de Inhumas",
        "tipo": "industrial",
        "municipio": "Inhumas",
        "descricao": "Polo agroindustrial a oeste de Goiânia, com indústrias de alimentos, cerâmica e beneficiamento de madeiras.",
        "empresas": "Alimentos, cerâmica e madeiras",
    },
    "luziania": {
        "nome": "Distrito Industrial de Luziânia",
        "tipo": "industrial",
        "municipio": "Luziânia",
        "descricao": "Localizado no Entorno do Distrito Federal, com indústrias de calçados, alimentos, telhas, fertilizantes e soluções ambientais.",
        "empresas": "Calçados, alimentos e fertilizantes",
    },
    "mineiros": {
        "nome": "Distrito Industrial de Mineiros I e II",
        "tipo": "industrial",
        "municipio": "Mineiros",
        "descricao": "Polo industrial do sudoeste goiano, com destaque para frigoríficos, laticínios, cereais, rações e cooperativas agrícolas.",
        "empresas": "Frigoríficos, laticínios e cereais",
    },
    "orizona": {
        "nome": "Distrito Industrial de Orizona",
        "tipo": "industrial",
        "municipio": "Orizona",
        "descricao": "Distrito industrial de Orizona, com atuação em eletrônica, rações, produtos agropecuários, cerâmica e sementes.",
        "empresas": "Eletrônica, rações e agropecuário",
    },
    "porangatu": {
        "nome": "Distrito Industrial de Porangatu",
        "tipo": "industrial",
        "municipio": "Porangatu",
        "descricao": "Polo industrial do norte goiano, com indústrias de produtos agropecuários, laticínios, ferragens, charque e engenharia ambiental.",
        "empresas": "Agropecuário, laticínios e ferragens",
    },
    "rubiataba": {
        "nome": "Distrito Industrial de Rubiataba",
        "tipo": "industrial",
        "municipio": "Rubiataba",
        "descricao": "Distrito industrial de Rubiataba, com atuação em móveis, estofados, transportes e construção civil.",
        "empresas": "Móveis, estofados e transporte",
    },
    "uruacu": {
        "nome": "Distrito Industrial de Uruaçu",
        "tipo": "industrial",
        "municipio": "Uruaçu",
        "descricao": "Polo industrial do norte goiano, com diversidade de indústrias: alimentos, móveis, couros, vidros, hidráulica e artefatos de cimento.",
        "empresas": "Alimentos, móveis e artefatos",
    },
}

TIPO_LABELS = {
    "agroindustrial": "Distrito Agroindustrial",
    "industrial": "Distrito Industrial",
    "tecnologico": "Parque Tecnológico",
}

@dashboard_bp.route('/assent/cadastro-modulos')
@role_required('assent', 'admin', 'assent_gestor')
def cadastro_modulos():
    from app.db import get_db
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM municipal_lots ORDER BY municipio, distrito, quadra, modulo_s")
            registros = cursor.fetchall()
    return render_template('cadastro_modulos.html', registros=registros)

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

    perimetros = None
    if slug == 'daia':
        from app.db import get_db
        with get_db() as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT id, perimetro, area, coordenadas, status FROM mapas_interativo_anapolis ORDER BY id")
                perimetros = cursor.fetchall()

    return render_template('distrito_detalhe.html', distrito=distrito, slug=slug, tipo_label=tipo_label, perimetros=perimetros)

@dashboard_bp.route('/menu/<modo>')
@role_required('assent', 'jur', 'admin','assent_gestor','jur_gestor')
def menu(modo):
    from app.db import get_db
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, numero_processo, titulo, tipo_acao, tipo_processo, tribunal,
                       vara, comarca, valor_da_causa, status, fase, data_criacao,
                       assunto_judicial, recurso_acionado, tipo_recurso, descricao
                FROM processos
                ORDER BY numero_processo
            """)
            processos = cursor.fetchall()
    return render_template('menu_jur.html', processos=processos)

