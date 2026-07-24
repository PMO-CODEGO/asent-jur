from flask import Blueprint, render_template, session, redirect, url_for
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

@dashboard_bp.route('/menu/<modo>')
@role_required('assent', 'jur', 'admin','assent_gestor','jur_gestor')
def menu(modo):

    if modo == "jur" or modo == "jur_gestor":
        return render_template('menu_jur.html')

    return render_template('menu.html')

