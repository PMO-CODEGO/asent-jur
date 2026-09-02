from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.decorators import role_required
from app.db import get_db
from app.services.log_service import gravar_log
from app.services.municipio_service import listar_municipios

cadastro_modulos_bp = Blueprint('cadastro_modulos', __name__)

CAMPOS = [
    # Cadastro do Imóvel
    ('municipio',                       'Município'),
    ('codigo_ibge_municipio',           'Código IBGE do Município'),
    ('distrito',                        'Distrito'),
    ('matricula_loteamento',            'Nº Matrícula do Loteamento'),
    ('sigla_loteamento',                'Sigla do Loteamento'),
    ('quadra',                          'Quadra'),
    ('qtd_modulos',                     'Qtd. Módulos'),
    ('logradouro',                      'Nome do Logradouro'),
    ('area_lote_m2',                    'Tamanho (m²)'),
    ('matricula_modulo',                'Nº Matrícula do Módulo'),
    ('codigo_modulo_externo',           'Código do Módulo'),
    ('cci',                             'CCI'),
    ('inscricao_municipal',             'Inscrição Municipal'),
    ('area_institucional',              'Área Institucional'),
    # Cadastro do Assentamento
    ('empresa',                         'Empresa'),
    ('cnpj',                            'CNPJ'),
    ('nome_representante_legal',        'Representante Legal'),
    ('telefone_representante_legal',    'Telefone do Representante'),
    ('email_representante_legal',       'E-mail do Representante'),
    ('processo_sei',                    'Processo SEI'),
    ('ramo_de_atividade',               'Ramo de Atividade'),
    ('status_de_assentamento',          'Status de Assentamento'),
    ('data_escrituracao',               'Data de Escrituração'),
    ('data_contrato_de_compra_e_venda', 'Data do Contrato de Compra e Venda'),
    ('registro_na_matricula',           'Registro na Matrícula'),
    # Registro Anterior do Assentamento
    ('empresa_anterior',                'Nome da Empresa (Anterior)'),
    ('cnpj_anterior',                   'CNPJ (Anterior)'),
    ('processo_anterior',               'Número do Processo (Anterior)'),
    # Situação Ocupação
    ('relatorio_vistoria',              'Relatório de Vistoria'),
    ('ultima_vistoria',                 'Última Vistoria'),
    ('taxa_ocupacao_imovel',            'Taxa de Ocupação do Imóvel (%)'),
    ('atividade_industrial',            'Atividade Industrial'),
    ('empregos_gerados',                'Empregos Gerados'),
    ('imovel_regular_irregular',        'Regular / Irregular'),
    ('irregularidades',                 'Irregularidades'),
    ('projeto_ocupacao_area',           'Projeto de Ocupação da Área'),
    ('data_aprovacao_poa',              'Data de Aprovação do POA'),
    ('cronograma_fisico_obra_meses',    'Cronograma de Obra (meses)'),
    ('observacoes',                     'Observações'),
]


@cadastro_modulos_bp.route('/assent/cadastro-modulos/novo', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def novo():
    if request.method == 'POST':
        cols = ', '.join(f for f, _ in CAMPOS)
        placeholders = ', '.join('%s' for _ in CAMPOS)
        values = tuple(request.form.get(f) or None for f, _ in CAMPOS)
        with get_db() as db:
            with db.cursor() as cursor:
                cursor.execute(f'INSERT INTO municipal_lots ({cols}) VALUES ({placeholders})', values)
            db.commit()
        gravar_log('MODULO_CRIADO', (
            f"Município: {request.form.get('municipio') or '-'} | "
            f"Distrito: {request.form.get('distrito') or '-'} | "
            f"Módulo: {request.form.get('matricula_modulo') or '-'}"
        ))
        return redirect(url_for('dashboard.cadastro_modulos'))
    return render_template('cadastro_modulos_form.html', registro=None, campos=CAMPOS,
                           titulo='Novo Módulo', municipios=listar_municipios())


@cadastro_modulos_bp.route('/assent/cadastro-modulos/<int:registro_id>/editar', methods=['GET', 'POST'])
@role_required('assent', 'admin', 'assent_gestor')
def editar(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            if request.method == 'POST':
                fields = [f for f, _ in CAMPOS]
                set_clause = ', '.join(f'{f}=%s' for f in fields)
                values = tuple(request.form.get(f) or None for f in fields)
                cursor.execute(f'UPDATE municipal_lots SET {set_clause} WHERE id=%s', values + (registro_id,))
                db.commit()
                gravar_log('MODULO_EDITADO', (
                    f"ID: {registro_id} | "
                    f"Município: {request.form.get('municipio') or '-'} | "
                    f"Distrito: {request.form.get('distrito') or '-'} | "
                    f"Módulo: {request.form.get('matricula_modulo') or '-'}"
                ))
                return redirect(url_for('dashboard.cadastro_modulos'))
            cursor.execute('SELECT * FROM municipal_lots WHERE id=%s', (registro_id,))
            registro = cursor.fetchone()
    if not registro:
        return redirect(url_for('dashboard.cadastro_modulos'))
    return render_template('cadastro_modulos_form.html', registro=registro, campos=CAMPOS,
                           titulo='Editar Módulo', municipios=listar_municipios())


@cadastro_modulos_bp.route('/assent/cadastro-modulos/<int:registro_id>/excluir', methods=['POST'])
@role_required('assent', 'admin', 'assent_gestor')
def excluir(registro_id):
    with get_db() as db:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute('SELECT municipio, distrito, matricula_modulo FROM municipal_lots WHERE id=%s', (registro_id,))
            r = cursor.fetchone() or {}
            cursor.execute('DELETE FROM municipal_lots WHERE id=%s', (registro_id,))
        db.commit()
    gravar_log('MODULO_EXCLUIDO', (
        f"ID: {registro_id} | "
        f"Município: {r.get('municipio') or '-'} | "
        f"Distrito: {r.get('distrito') or '-'} | "
        f"Módulo: {r.get('matricula_modulo') or '-'}"
    ))
    return redirect(url_for('dashboard.cadastro_modulos'))
