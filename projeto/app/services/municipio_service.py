from app.db import get_db


def listar_municipios():
    with get_db() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT DISTINCT municipio FROM municipio ORDER BY municipio")
            return [r[0] for r in cursor.fetchall() if r and r[0]]
