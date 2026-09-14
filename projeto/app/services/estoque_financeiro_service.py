import re
import unicodedata

import openpyxl


# (distrito normalizado -> (municipio, sigla_distrito))
# Copiado do notebook de tratamento (df_contab.ipynb) usado pela equipe.
MAPEAMENTO_DISTRITOS = {
    'DISTRITO AGROINDUSTRIAL DE ANAPOLIS - DAIA': ('ANAPOLIS', 'DAIA'),
    'DISTRITO AGROINDUSTRIAL DE ANAPOLIS PLATAFORMA MULTIMODAL - DAIAPLAM': ('ANAPOLIS', 'DAIAPLAM'),
    'DISTRITO AGROINDUSTRIAL DE APARECIDA DE GOIANIA - DAIAG': ('APARECIDA DE GOIANIA', 'DAIAG'),
    'DISTRITO AGROINDUSTRIAL NORBERTO TEIXEIRA - DIANOT - APARECIDA DE GOIANIA': ('APARECIDA DE GOIANIA', 'DIANOT'),
    'DISTRITO AGROINDUSTRIAL DE SENADOR CANEDO - DASC': ('SENADOR CANEDO', 'DASC'),
    'DISTRITO INDUSTRIAL DE SENADOR CANEDO - DISC': ('SENADOR CANEDO', 'DISC'),
    'DISTRITO AGROINDUSTRIAL DE MINEIROS I - DAIM I': ('MINEIROS', 'DAIM I'),
    'DISTRITO AGROINDUSTRIAL DE MINEIROS II - DAIM II': ('MINEIROS', 'DAIM II'),
    'DISTRITO AGROINDUSTRIAL DE BELA VISTA DE GOIAS': ('BELA VISTA DE GOIAS', 'DAIBEV'),
    'DISTRITO AGROINDUSTRIAL DE GOIANIRA': ('GOIANIRA', 'DAIGOIAN'),
    'DISTRITO AGROINDUSTRIAL DE GOIANESIA - DAIGO': ('GOIANESIA', 'DAIGO'),
    'DISTRITO AGROINDUSTRIAL DE INHUMAS': ('INHUMAS', 'DAI'),
    'DISTRITO AGROINDUSTRIAL DE ITUMBIARA - DIAGRI': ('ITUMBIARA', 'DIAGRI'),
    'DISTRITO AGROINDUSTRIAL DE LUZIANIA - DIAL': ('LUZIANIA', 'DIAL'),
    'DISTRITO AGROINDUSTRIAL DE MORRINHOS - DAIMO': ('MORRINHOS', 'DAIMO'),
    'DISTRITO AGROINDUSTRIAL DE ORIZONA': ('ORIZONA', 'DAIORI'),
    'DISTRITO AGROINDUSTRIAL DE PONTALINA': ('PONTALINA', 'DAIPO'),
    'DISTRITO AGROINDUSTRIAL DE PORANGATU': ('PORANGATU', 'DAIPORAN'),
    'DISTRITO AGROINDUSTRIAL DE RIALMA': ('RIALMA', 'DAIRI'),
    'DISTRITO AGROINDUSTRIAL DE RIO VERDE I - DARV I': ('RIO VERDE', 'DARV I'),
    'DISTRITO AGROINDUSTRIAL DE RUBIATABA': ('RUBIATABA', 'DAIRUB'),
    # nome oficial IBGE e' "SAO LUIZ DO NORTE" (com Z); a planilha/notebook original grafava com S.
    'DISTRITO AGROINDUSTRIAL DE SAO LUIS DO NORTE': ('SAO LUIZ DO NORTE', 'DAISLN'),
    'DISTRITO AGROINDUSTRIAL DE URUACU - DIAU': ('URUACU', 'DIAU'),
    'DISTRITO MINEROINDUSTRIAL DE CATALAO - DIMIC': ('CATALAO', 'DIMIC'),
}

# ano -> (col_mercado, col_subsidiado, col_ajuste, campo_ajuste)
ANOS_COLUNAS = [
    ('2021', ['VALOR DE MERCADO DO M2 (R$) - 2021', 'VALOR DE MERCADO DO M2  (R$) - 2021'],
     ['VALOR DO M2 SUBSIDIADO EM 90%  (R$) - 2021'], ['AJUSTE - \nEFEITO NO PL 2021', 'AJUSTE -  EFEITO NO PL 2021'],
     'ajuste_efeito_pl_2021'),
    ('2022', ['VALOR DE MERCADO DO M2  (R$) - 2022'], ['VALOR DO M2 SUBSIDIADO EM 90%  (R$) - 2022'],
     ['AJUSTE - \nEFEITO NO PL 2022', 'AJUSTE -  EFEITO NO PL 2022'], 'ajuste_efeito_pl_2022'),
    ('2023', ['VALOR DE MERCADO DO M2  (R$) - 2023'], ['VALOR DO M2 SUBSIDIADO EM 90%  (R$) - 2023'],
     ['AJUSTE - \nEFEITO NO PL 2023', 'AJUSTE -  EFEITO NO PL 2023'], 'ajuste_efeito_pl_2023'),
    ('2024', ['VALOR DE MERCADO DO M2  (R$) - 2024'], ['VALOR DO M2 SUBSIDIADO EM 90%  (R$) - 2024'],
     ['AJUSTE/REVERSAO VALOR REALIZAVEL LIQUIDO 31/12/2024'], 'ajuste_vrl_2024'),
    ('2025', ['VALOR DE MERCADO DO M2  (R$) - 2025'], ['VALOR DO M2 SUBSIDIADO EM 90%  (R$) - 2025'],
     ['AJUSTE/REVERSAO VALOR REALIZAVEL LIQUIDO 31/12/2025'], 'ajuste_vrl_2025'),
]

CAMPOS_DIRETOS = {
    'custo_terreno': ['CUSTO TERRENO'],
    'custo_implantacao': ['CUSTO IMPLANTACAO'],
    'custo_aquisicao': ['CUSTO DE AQUISICAO'],
    'area_vendida': ['AREA VENDIDA'],
    'custo_venda': ['CUSTO \nVENDA', 'CUSTO VENDA'],
    'estoque_2024': ['ESTOQUE EM 31/12/2024'],
    'observacoes': ['OBS'],
    'dossie': ['DOSSIE'],
    'reconhecimento_estoque': ['RECONHECIMENTO ESTOQUE'],
}

CAMPOS_TEXTO = {'observacoes', 'dossie', 'reconhecimento_estoque'}


def _remover_acentos(texto):
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def _normalizar_cabecalho(valor):
    if valor is None:
        return ''
    texto = str(valor).replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip().upper()
    return _remover_acentos(texto)


def _normalizar_valor_texto(valor):
    if valor is None:
        return None
    texto = re.sub(r'\s+', ' ', str(valor)).strip()
    texto = texto.replace('*', '')
    return _remover_acentos(texto).upper() or None


def _parse_numero(valor):
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return round(float(valor), 4)
    texto = str(valor).strip()
    if texto in ('', '-'):
        return None
    if re.match(r'^-?\d{1,3}(\.\d{3})*(,\d+)?$', texto):
        texto = texto.replace('.', '').replace(',', '.')
    else:
        texto = texto.replace(',', '.')
    try:
        return round(float(texto), 4)
    except ValueError:
        return None


def _mapear_colunas(header_row):
    normalizados = [_normalizar_cabecalho(v) for v in header_row]

    def localizar(candidatos, excluir=None):
        for candidato in candidatos:
            alvo = _normalizar_cabecalho(candidato)
            for idx, col in enumerate(normalizados):
                if col == alvo:
                    if excluir and any(x in col for x in excluir):
                        continue
                    return idx
        # fallback: contains
        for candidato in candidatos:
            alvo = _normalizar_cabecalho(candidato)
            for idx, col in enumerate(normalizados):
                if alvo and alvo in col:
                    if excluir and any(x in col for x in excluir):
                        continue
                    return idx
        return None

    mapa = {
        'matricula': localizar(['MATRICULA'], excluir=['LOTEAMENTO']),
        'quadra': localizar(['QD.', 'QD', 'QUADRA']),
        'modulo': localizar(['MOD.', 'MOD', 'MODULOS']),
    }
    for campo, candidatos in CAMPOS_DIRETOS.items():
        mapa[campo] = localizar(candidatos)
    for ano, cols_merc, cols_sub, cols_aj, campo_aj in ANOS_COLUNAS:
        mapa[f'valor_mercado_{ano}'] = localizar(cols_merc)
        mapa[f'valor_subsidiado_{ano}'] = localizar(cols_sub)
        mapa[campo_aj] = localizar(cols_aj)
    return mapa


def _valor(row, colunas_idx, campo):
    idx = colunas_idx.get(campo)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def gerar_id_modulo(sigla_distrito, quadra, modulo, sufixo_alternativo):
    sigla = re.sub(r'[\-\s]+', '', str(sigla_distrito or ''))
    quadra_limpa = re.sub(r'[\-\s]+', '', str(quadra)) if quadra not in (None, '', '-') else ''
    modulo_limpo = re.sub(r'[\-\s]+', '', str(modulo)) if modulo not in (None, '', '-') else ''

    if not quadra_limpa or not modulo_limpo:
        sufixo = re.sub(r'[\-\s]+', '', str(sufixo_alternativo or ''))
        return re.sub(r'[\-\s]+', '', f'{sigla}{sufixo}')

    return re.sub(r'[\-\s]+', '', f'{sigla}Q{quadra_limpa}M{modulo_limpo}')


def listar_abas_candidatas(caminho_arquivo):
    wb = openpyxl.load_workbook(caminho_arquivo, read_only=True)
    nomes = wb.sheetnames
    wb.close()
    return nomes


def _chave_ordenacao_aba(nome_aba):
    """Extrai (ano, trimestre) do nome da aba (ex: '3ºt 2026 - ...' -> (2026, 3))
    para priorizar a versão mais recente. Abas sem esse padrão (ex: a versão
    legada 'ESTOQUE DE ÁREAS PARCELADAS', sem trimestre/ano) ficam por último."""
    match = re.search(r'(\d)\s*[ºo]?\s*t\s*(\d{4})', nome_aba, flags=re.IGNORECASE)
    if match:
        trimestre, ano = int(match.group(1)), int(match.group(2))
        return (1, ano, trimestre)
    match_ano = re.search(r'(\d{4})', nome_aba)
    if match_ano:
        return (0, int(match_ano.group(1)), 0)
    return (-1, 0, 0)


def detectar_aba_padrao(nomes_abas):
    candidatas = [
        n for n in nomes_abas
        if 'ESTOQUE' in _normalizar_cabecalho(n) and 'PARCELA' in _normalizar_cabecalho(n)
    ]
    if not candidatas:
        return nomes_abas[0] if nomes_abas else None
    return sorted(candidatas, key=_chave_ordenacao_aba, reverse=True)[0]


def processar_planilha_estoque(caminho_arquivo, nome_aba):
    wb = openpyxl.load_workbook(caminho_arquivo, data_only=True)
    if nome_aba not in wb.sheetnames:
        raise ValueError(f"A aba '{nome_aba}' não foi encontrada na planilha.")
    ws = wb[nome_aba]

    linhas = list(ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True))
    wb.close()

    if len(linhas) < 6:
        raise ValueError('A planilha não tem linhas suficientes para conter os dados esperados (cabeçalho na linha 5).')

    header_row = linhas[4]
    colunas_idx = _mapear_colunas(header_row)

    if colunas_idx.get('matricula') is None:
        raise ValueError('Não encontrei a coluna "Matrícula" na linha 5 dessa aba. Confirme se é a aba correta.')

    distrito_atual = None
    registros = []
    distritos_sem_mapeamento = set()

    for row in linhas[5:]:
        primeira_col = row[0] if row else None
        primeira_col_norm = _normalizar_valor_texto(primeira_col) or ''

        if primeira_col_norm.startswith('DISTRITO'):
            distrito_atual = primeira_col_norm
            continue

        if not distrito_atual:
            continue

        matricula_bruta = _valor(row, colunas_idx, 'matricula')
        matricula_norm = _normalizar_valor_texto(matricula_bruta)
        if not matricula_norm or matricula_norm in ('MATRICULA', 'TOTAL:', 'NAN'):
            continue

        matricula_limpa = matricula_norm.replace('.', '').strip()

        municipio, sigla_distrito = MAPEAMENTO_DISTRITOS.get(distrito_atual, (None, None))
        if municipio is None:
            distritos_sem_mapeamento.add(distrito_atual)

        quadra = _valor(row, colunas_idx, 'quadra')
        modulo = _valor(row, colunas_idx, 'modulo')
        id_modulo = gerar_id_modulo(sigla_distrito, quadra, modulo, matricula_limpa)

        registro = {
            'distrito': distrito_atual,
            'municipio': municipio,
            'sigla_distrito': sigla_distrito,
            'id_modulo': id_modulo,
            'matricula_atual': matricula_limpa,
        }

        for campo in CAMPOS_DIRETOS:
            bruto = _valor(row, colunas_idx, campo)
            if campo in CAMPOS_TEXTO:
                registro[campo] = _normalizar_valor_texto(bruto)
            else:
                registro[campo] = _parse_numero(bruto)

        for ano, _cm, _cs, _ca, campo_aj in ANOS_COLUNAS:
            registro[f'valor_mercado_{ano}'] = _parse_numero(_valor(row, colunas_idx, f'valor_mercado_{ano}'))
            registro[f'valor_subsidiado_{ano}'] = _parse_numero(_valor(row, colunas_idx, f'valor_subsidiado_{ano}'))
            registro[campo_aj] = _parse_numero(_valor(row, colunas_idx, campo_aj))

        registros.append(registro)

    return registros, sorted(distritos_sem_mapeamento)
