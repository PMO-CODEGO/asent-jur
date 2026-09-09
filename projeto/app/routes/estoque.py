from decimal import Decimal
from flask import Blueprint, render_template
from app.utils.decorators import role_required
from app.db import get_db

estoque_bp = Blueprint('estoque', __name__)


def _fmt_brl(val):
    if val is None:
        return '-'
    try:
        n = Decimal(val)
    except Exception:
        return str(val)
    neg = n < 0
    s = '{:,.2f}'.format(abs(n)).replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('-R$ ' if neg else 'R$ ') + s


def _fmt_m2(val):
    if val is None:
        return '-'
    try:
        n = Decimal(val)
    except Exception:
        return str(val)
    s = '{:,.2f}'.format(n).replace(',', 'X').replace('.', ',').replace('X', '.')
    return s.rstrip('0').rstrip(',') if ',' in s and s.endswith('00') else s


@estoque_bp.route('/admin/estoque/bruto')
@role_required('admin')
def bruto():
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT * FROM estoque_bruto
                ORDER BY municipio IS NULL, municipio, num_matricula
            """)
            registros = cursor.fetchall()

    for r in registros:
        for campo in ('area_total_m2',):
            r[f'{campo}_fmt'] = _fmt_m2(r[campo])
        for campo in (
            'custo_aquisicao', 'total_estoque',
            'valor_mercado_2021', 'valor_subsidiado_2021', 'ajuste_efeito_pl_2021',
            'valor_mercado_2022', 'valor_subsidiado_2022', 'ajuste_efeito_pl_2022',
            'valor_mercado_2023', 'valor_subsidiado_2023', 'ajuste_efeito_pl_2023', 'ajuste_vrl_2023',
            'valor_mercado_2024', 'valor_subsidiado_2024', 'ajuste_vrl_2024', 'total_vrl_2024',
            'valor_mercado_2025', 'valor_subsidiado_2025', 'ajuste_vrl_2025', 'total_vrl_2025',
            'ajuste_vrl_2026',
        ):
            r[f'{campo}_fmt'] = _fmt_brl(r[campo])

    total_area = sum((r['area_total_m2'] or 0) for r in registros)
    total_estoque = sum((r['total_estoque'] or 0) for r in registros)

    return render_template(
        'estoque_bruto.html',
        registros=registros,
        total_registros=len(registros),
        total_area_fmt=_fmt_m2(total_area),
        total_estoque_fmt=_fmt_brl(total_estoque),
    )
