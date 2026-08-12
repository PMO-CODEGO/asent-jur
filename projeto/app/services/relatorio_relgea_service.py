import re
import unicodedata
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.pdf_service import (
    AZUL_CODEGO,
    FONTE_NEGRITO,
    FONTE_REGULAR,
    bloco_identificacao,
    linha_assinatura,
    pagina_relgea,
)

VERDE_DISPONIVEL = colors.HexColor('#C6EFCE')

# Sigla oficial da area no Anexo D do MANSUGEQ (Ficha de Siglas Unidade SEI): GEAS-18820
# = Gerencia de Assentamento. O codigo dos relatorios usa RELGEAS (nao "RELGEA"), seguindo
# a estrutura [TIPO]-[AREA]-[NOME]-[REVxxx] descrita na secao 11.1 do manual.
UNIDADE_RESPONSAVEL = 'GEAS - GERÊNCIA DE ASSENTAMENTO'
CONTROLE = 'SUGEQ'

# slug (mesmo usado em dashboard.DISTRITOS) -> valor da coluna `distrito` em municipal_lots
DISTRITO_DB_MAP = {
    'abadiania':   'ABADIÂNIA',
    'bela-vista':  'BELA VISTA',
    'daia':        'DAIA E DAIA NORTE',
    'daiag':       'DAIAG',
    'daimo':       'DAIMO',
    'dapo':        'DAPO',
    'darv-i':      'DARV I',
    'darv-ii':     'DARV II',
    'dasc':        'DASC',
    'diagri':      'DIAGRI',
    'dimic':       'DIMIC',
    'disc':        'DISC',
    'goianesia':   'GOIANÉSIA',
    'goianira':    'GOIANIRA',
    'inhumas':     'INHUMAS',
    'luziania':    'LUZIÂNIA',
    'mineiros':    'MINEIROS I E II',
    'orizona':     'ORIZONA',
    'porangatu':   'PORANGATU',
    'rubiataba':   'RUBIATABA',
    'uruacu':      'URUAÇU',
}

TIPO_LABELS = {
    'galeria': 'GALERIA / CONDOMÍNIO',
    'regularizada': 'ÁREA PARCELADA REGULARIZADA',
    'irregular': 'LOTEAMENTO IRREGULAR',
}

FAMILIA_TIPO = {
    'galerias': 'galeria',
    'regularizadas': 'regularizada',
    'irregulares': 'irregular',
}

FAMILIA_TABELA = {
    'galerias': 'galerias_condominios',
    'regularizadas': 'areas_parceladas_regularizadas',
    'irregulares': 'loteamentos_irregulares',
}


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def safe_filename(s):
    s = strip_accents(s).upper()
    s = re.sub(r'[^A-Z0-9]+', '_', s).strip('_')
    return s


def _clean(v):
    if v is None:
        return None
    s = str(v).strip()
    if not s or s == '-':
        return None
    return s


def _clean_processo(v):
    # 2147483647 = overflow do antigo INT32 (numeros de processo SEI reais tem ~15
    # digitos e nao cabem nesse tipo; a coluna foi migrada para varchar, mas o valor
    # sentinela de overflow pode continuar presente em registros ainda nao recuperados,
    # e a VM pode ainda nao ter recebido a migracao (processo_sei la ainda e int)
    if v is None:
        return None
    s = str(v).strip()
    if s in ('', '0', '2147483647'):
        return None
    return s


def _fmt_num_br(val):
    if val is None:
        return None
    try:
        d = Decimal(str(val)).normalize()
    except Exception:
        return str(val)
    s = format(d, 'f')
    if '.' in s:
        int_part, dec_part = s.split('.')
    else:
        int_part, dec_part = s, ''
    neg = int_part.startswith('-')
    int_part = int_part.lstrip('-')
    int_formatted = '{:,}'.format(int(int_part or 0)).replace(',', '.')
    if neg:
        int_formatted = '-' + int_formatted
    return (int_formatted + ',' + dec_part) if dec_part else int_formatted


def _valor_pdf(v):
    return v if v not in (None, '') else '-'


def buscar_registros_distrito(db, distrito_db):
    with db.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id, municipio, distrito, quadra, modulo_s, qtd_modulos, tamanho_m2,
                   empresa, cnpj, processo_sei, status_de_assentamento, acao_judicial,
                   taxa_e_ocupacao_do_imovel, ramo_de_atividade, irregularidades,
                   imovel_regular_irregular
            FROM municipal_lots
            WHERE distrito = %s
            ORDER BY quadra, id
        """, (distrito_db,))
        rows = cursor.fetchall()
    rows = [r for r in rows if (r.get('modulo_s') or '').upper() != 'TOTAL'
            and (r.get('empresa') or '').upper() != 'PROCESSO GERAL:']
    return rows


# larguras calibradas para caber em A4 paisagem (usavel ~762pt com margem 40) na fonte
# Arial 10 exigida pela secao 6.1-III/IV do manual
DISTRITO_COL_WIDTHS = [18, 100, 68, 60, 60, 28, 30, 28, 46, 85, 34, 30, 85, 40]
DISTRITO_HEADERS = [
    'Nº', 'Empresa', 'CNPJ', 'Processo SEI', 'Status de Assentamento', 'Quadra',
    'Módulo(s)', 'Qtd. Módulos', 'Tamanho (m²)', 'Ação Judicial', 'Taxa Ocup.',
    'Ramo Ativ.', 'Irregularidades', 'Regular/Irregular',
]
# secao 6.1-III do manual: "textos objetivos (codigos, datas, revisoes, status, valores)
# centralizados; textos descritivos alinhados a esquerda" — indices das colunas descritivas
# (Empresa, Acao Judicial, Irregularidades); as demais sao objetivas -> centralizadas
DISTRITO_COLS_ESQUERDA = {1, 9, 12}


def gerar_relatorio_distrito_pdf(db, distrito_db, emitido_por='SISTEMA'):
    """Gera o relatorio RELGEA de um distrito, em PDF, a partir dos dados atuais do banco.

    Retorna (buffer, nome_arquivo, n_registros) ou (None, None, 0) se nao houver registros.
    """
    registros = buscar_registros_distrito(db, distrito_db)
    if not registros:
        return None, None, 0

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=40, rightMargin=40, topMargin=90, bottomMargin=60)

    data_emissao = datetime.now().strftime('%d/%m/%Y')
    codigo = 'RELGEASDISTRITODE' + strip_accents(distrito_db).upper().replace(' ', '') + 'REV000'
    doc._iso_doc_code = codigo
    doc._iso_rev = 'Rev. 00'
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    # seção 6.1-IV do manual: título principal centralizado, negrito, tamanho 14
    titulo_style = ParagraphStyle('DistritoTitulo', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=14, leading=18, alignment=1,
        spaceAfter=12, textColor=AZUL_CODEGO)
    # seção 6.1-I: subtítulos Arial 11, negrito, esquerda
    subtitle_style = ParagraphStyle('DistritoSubtitle', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=11, leading=14, spaceAfter=6,
        spaceBefore=4, textColor=AZUL_CODEGO)
    # seção 6.1-IV / tabela 6.2: cabeçalhos de coluna Arial 10, negrito, centralizados
    header_cell_style = ParagraphStyle('DistritoHeaderCell', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=10, leading=12, alignment=1, textColor=colors.whitesmoke, wordWrap='CJK')
    # conteúdo das células Arial 10; alinhamento por coluna decidido na hora de montar a linha
    cell_style_centro = ParagraphStyle('DistritoCellCentro', parent=styles['Normal'],
        fontName=FONTE_REGULAR, fontSize=10, leading=12, alignment=1, wordWrap='CJK')
    cell_style_esquerda = ParagraphStyle('DistritoCellEsquerda', parent=styles['Normal'],
        fontName=FONTE_REGULAR, fontSize=10, leading=12, alignment=0, wordWrap='CJK')
    identificacao_style = ParagraphStyle('DistritoIdentCell', parent=styles['Normal'],
        fontName=FONTE_REGULAR, fontSize=8, leading=10, wordWrap='CJK')
    styles_map = {'cell': identificacao_style, 'bold': subtitle_style}

    story = []
    story.append(Paragraph(f'RELATÓRIO RELGEA — DISTRITO DE {distrito_db}'.upper(), titulo_style))
    bloco_identificacao(story,
        titulo=f'Relatório RELGEA — Distrito de {distrito_db}',
        doc_code=codigo, rev='Rev. 00', data_emissao=data_emissao,
        emitido_por=emitido_por, styles_map=styles_map,
        unidade_responsavel=UNIDADE_RESPONSAVEL, revisado_por='A definir', controle=CONTROLE,
        aprovado_por='A definir')

    story.append(Paragraph(f'REGISTROS DO DISTRITO ({len(registros)})', subtitle_style))

    linhas = [[Paragraph(h, header_cell_style) for h in DISTRITO_HEADERS]]
    linhas_vazias = []
    for i, reg in enumerate(registros, start=1):
        vazio = _clean(reg.get('empresa')) is None
        if vazio:
            linhas_vazias.append(i)  # indice da linha de dados (1-based, sem contar cabecalho)

        valores = [
            str(i),
            _clean(reg.get('empresa')) or ('ÁREA DISPONÍVEL' if vazio else '-'),
            _clean(reg.get('cnpj')) or '-',
            str(_clean_processo(reg.get('processo_sei')) or '-'),
            _clean(reg.get('status_de_assentamento')) or '-',
            _valor_pdf(reg.get('quadra')),
            _clean(reg.get('modulo_s')) or '-',
            _valor_pdf(reg.get('qtd_modulos')),
            _fmt_num_br(reg.get('tamanho_m2')) or '-',
            (_clean(reg.get('acao_judicial')) or '-') if not vazio else '-',
            (_fmt_num_br(reg.get('taxa_e_ocupacao_do_imovel')) or '-') if not vazio else '-',
            ('SIM' if (not vazio and _clean(reg.get('ramo_de_atividade'))) else '-'),
            (_clean(reg.get('irregularidades')) or '-') if not vazio else '-',
            (_clean(reg.get('imovel_regular_irregular')) or '-') if not vazio else '-',
        ]
        linha = []
        for col, v in enumerate(valores):
            estilo_col = cell_style_esquerda if col in DISTRITO_COLS_ESQUERDA else cell_style_centro
            linha.append(Paragraph(escape(str(v)), estilo_col))
        linhas.append(linha)

    tabela = Table(linhas, colWidths=DISTRITO_COL_WIDTHS, repeatRows=1)
    estilo = [
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_CODEGO),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    for indice_linha in linhas_vazias:
        estilo.append(('BACKGROUND', (0, indice_linha), (-1, indice_linha), VERDE_DISPONIVEL))
    tabela.setStyle(TableStyle(estilo))
    story.append(tabela)

    linha_assinatura(story, emitido_por, styles_map, revisado_por='A definir', aprovado_por='A definir')

    doc.build(story, onFirstPage=pagina_relgea, onLaterPages=pagina_relgea)
    buffer.seek(0)

    nome_arquivo = f'REL-GEAS_DISTRITO_DE_{strip_accents(distrito_db).replace(" ", "_")}_REV000.pdf'
    nome_arquivo = re.sub(r'[<>:"/\\|?*]', '', nome_arquivo)
    return buffer, nome_arquivo, len(registros)


def buscar_registro_individual(db, familia, registro_id):
    tabela = FAMILIA_TABELA.get(familia)
    if not tabela:
        return None
    campos_extra = ', observacoes' if familia == 'irregulares' else ''
    with db.cursor(dictionary=True) as cursor:
        cursor.execute(f"""
            SELECT id, municipio, num_matricula, ano_aquisicao, area_total_m2, valor_imovel,
                   matricula_parcelamento, registro_loteamento, ocupacao, descricao_area,
                   registro_propriedade {campos_extra}
            FROM {tabela} WHERE id = %s
        """, (registro_id,))
        return cursor.fetchone()


def gerar_relatorio_individual_pdf(familia, registro, emitido_por='SISTEMA'):
    """Gera a ficha RELGEA de um unico registro (galeria/regularizada/irregular), em PDF.

    Retorna (buffer, nome_arquivo).
    """
    tipo = FAMILIA_TIPO[familia]
    municipio = _clean(registro.get('municipio')) or 'MUNICIPIO_NAO_INFORMADO'
    matricula = _clean(registro.get('num_matricula')) or f"SN{registro.get('id')}"
    reg_id = registro.get('id')

    codigo = f'RELGEAS{safe_filename(TIPO_LABELS[tipo])}{safe_filename(municipio)}{safe_filename(matricula)}ID{reg_id}REV000'
    data_emissao = datetime.now().strftime('%d/%m/%Y')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=90, bottomMargin=72)
    doc._iso_doc_code = codigo
    doc._iso_rev = 'Rev. 00'
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    # seção 6.1-IV do manual: título principal centralizado, negrito, tamanho 14
    titulo_style = ParagraphStyle('FichaTitulo', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=14, leading=18, alignment=1,
        spaceAfter=12, textColor=AZUL_CODEGO)
    # seção 6.1-I: subtítulos Arial 11, negrito, esquerda
    subtitle_style = ParagraphStyle('FichaSubtitle', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=11, leading=14, spaceAfter=6,
        spaceBefore=4, textColor=AZUL_CODEGO)
    # formulários/campos de preenchimento: Arial 10 (seção 6.2)
    label_style = ParagraphStyle('FichaLabel', parent=styles['Normal'],
        fontName=FONTE_NEGRITO, fontSize=10, leading=13, textColor=colors.whitesmoke)
    value_style = ParagraphStyle('FichaValue', parent=styles['Normal'],
        fontName=FONTE_REGULAR, fontSize=10, leading=13, wordWrap='CJK')
    identificacao_style = ParagraphStyle('FichaIdentCell', parent=styles['Normal'],
        fontName=FONTE_REGULAR, fontSize=8, leading=10, wordWrap='CJK')
    styles_map = {'cell': identificacao_style, 'bold': subtitle_style}

    story = []
    story.append(Paragraph(f'FICHA DE ÁREA — {TIPO_LABELS[tipo]}', titulo_style))
    bloco_identificacao(story,
        titulo=f'Ficha de Área — {TIPO_LABELS[tipo]}',
        doc_code=codigo, rev='Rev. 00', data_emissao=data_emissao,
        emitido_por=emitido_por, styles_map=styles_map,
        unidade_responsavel=UNIDADE_RESPONSAVEL, revisado_por='A definir', controle=CONTROLE,
        aprovado_por='A definir')

    story.append(Paragraph(TIPO_LABELS[tipo], subtitle_style))

    campos = [
        ('TIPO', TIPO_LABELS[tipo]),
        ('MUNICÍPIO', _clean(registro.get('municipio'))),
        ('Nº MATRÍCULA DO IMÓVEL', _clean(registro.get('num_matricula'))),
        ('ANO DE AQUISIÇÃO', _clean(registro.get('ano_aquisicao'))),
        ('ÁREA TOTAL (M²)', _clean(registro.get('area_total_m2'))),
        ('VALOR DO IMÓVEL', _clean(registro.get('valor_imovel'))),
        ('MATRÍCULA DO PARCELAMENTO', _clean(registro.get('matricula_parcelamento'))),
        ('REGISTRO DE LOTEAMENTO', _clean(registro.get('registro_loteamento'))),
        ('OCUPAÇÃO / DISTRITO', _clean(registro.get('ocupacao'))),
        ('DESCRIÇÃO DA ÁREA', _clean(registro.get('descricao_area'))),
        ('REGISTRO DE PROPRIEDADE', _clean(registro.get('registro_propriedade'))),
    ]
    if tipo == 'irregular':
        campos.append(('OBSERVAÇÕES', _clean(registro.get('observacoes'))))

    dados = [[Paragraph(label, label_style), Paragraph(escape(str(_valor_pdf(valor))), value_style)] for label, valor in campos]
    tabela = Table(dados, colWidths=[170, 300])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), AZUL_CODEGO),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tabela)

    linha_assinatura(story, emitido_por, styles_map, revisado_por='A definir', aprovado_por='A definir')

    doc.build(story, onFirstPage=pagina_relgea, onLaterPages=pagina_relgea)
    buffer.seek(0)

    nome_arquivo = f'REL-GEAS_{safe_filename(TIPO_LABELS[tipo])}_{safe_filename(municipio)}_{safe_filename(matricula)}_ID{reg_id}_REV000.pdf'
    return buffer, nome_arquivo
