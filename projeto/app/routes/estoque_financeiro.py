import os
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, session
from werkzeug.utils import secure_filename

from app.db import get_db
from app.utils.decorators import role_required
from app.services.log_service import gravar_log
from app.services.relatorio_estoque_service import gerar_relatorio_estoque_pdf
from app.services.estoque_financeiro_service import (
    listar_abas_candidatas,
    detectar_aba_padrao,
    processar_planilha_estoque,
)

estoque_financeiro_bp = Blueprint('estoque_financeiro', __name__)

CAMPOS_FINANCEIROS = [
    'municipio_id', 'municipio', 'distrito', 'sigla_distrito', 'matricula_atual',
    'custo_terreno', 'custo_implantacao', 'custo_aquisicao', 'area_vendida', 'custo_venda',
    'valor_mercado_2021', 'valor_subsidiado_2021', 'ajuste_efeito_pl_2021',
    'valor_mercado_2022', 'valor_subsidiado_2022', 'ajuste_efeito_pl_2022',
    'valor_mercado_2023', 'valor_subsidiado_2023', 'ajuste_efeito_pl_2023',
    'valor_mercado_2024', 'valor_subsidiado_2024', 'ajuste_vrl_2024',
    'valor_mercado_2025', 'valor_subsidiado_2025', 'ajuste_vrl_2025',
    'estoque_2024', 'observacoes', 'dossie', 'reconhecimento_estoque',
]


def _pasta_importacoes():
    caminho = os.path.join(current_app.root_path, 'uploads', 'importacoes_estoque_financeiro')
    os.makedirs(caminho, exist_ok=True)
    return caminho


def _salvar_arquivo(arquivo):
    nome_original = secure_filename(arquivo.filename or 'estoque.xlsx')
    extensao = os.path.splitext(nome_original)[1].lower()
    if extensao != '.xlsx':
        raise ValueError('Envie um arquivo .xlsx.')
    nome_temporario = f'{uuid4().hex}{extensao}'
    caminho = os.path.join(_pasta_importacoes(), nome_temporario)
    arquivo.save(caminho)
    return nome_temporario, nome_original


def _caminho_temporario(nome_temporario):
    nome_seguro = secure_filename(nome_temporario or '')
    caminho = os.path.join(_pasta_importacoes(), nome_seguro)
    if not nome_seguro or not os.path.exists(caminho):
        raise ValueError('Arquivo temporário não encontrado. Envie a planilha novamente.')
    return caminho


def _montar_previa(nome_temporario, nome_original, aba):
    caminho = _caminho_temporario(nome_temporario)
    abas = listar_abas_candidatas(caminho)
    aba_selecionada = aba if aba in abas else detectar_aba_padrao(abas)

    registros, distritos_sem_mapeamento = processar_planilha_estoque(caminho, aba_selecionada)

    nomes_municipio = sorted({r['municipio'] for r in registros if r['municipio']})
    municipio_id_map = {}
    codigos_modulo_existentes = set()
    if nomes_municipio:
        with get_db() as db:
            with db.cursor() as cursor:
                formato = ', '.join(['%s'] * len(nomes_municipio))
                cursor.execute(f'SELECT municipio, municipio_id FROM municipio WHERE municipio IN ({formato})', tuple(nomes_municipio))
                municipio_id_map = {row[0]: row[1] for row in cursor.fetchall()}

                id_modulos = [r['id_modulo'] for r in registros]
                formato_ids = ', '.join(['%s'] * len(id_modulos)) if id_modulos else "''"
                if id_modulos:
                    cursor.execute(
                        f'SELECT DISTINCT id_modulo FROM municipal_lots WHERE id_modulo IN ({formato_ids})',
                        tuple(id_modulos)
                    )
                    codigos_modulo_existentes = {row[0] for row in cursor.fetchall()}

    resumo_por_municipio = {}
    for r in registros:
        r['municipio_id'] = municipio_id_map.get(r['municipio']) if r['municipio'] else None
        r['vinculado'] = r['id_modulo'] in codigos_modulo_existentes
        chave = r['municipio'] or 'SEM MUNICÍPIO MAPEADO'
        item = resumo_por_municipio.setdefault(chave, {'municipio': chave, 'total': 0, 'vinculados': 0, 'sem_municipio_id': 0, 'registros': []})
        item['total'] += 1
        if r['vinculado']:
            item['vinculados'] += 1
        if not r['municipio_id']:
            item['sem_municipio_id'] += 1
        item['registros'].append(r)

    return {
        'temp_name': nome_temporario,
        'original_filename': nome_original,
        'abas': abas,
        'aba_selecionada': aba_selecionada,
        'total_registros': len(registros),
        'distritos_sem_mapeamento': distritos_sem_mapeamento,
        'grupos': sorted(resumo_por_municipio.values(), key=lambda g: g['municipio']),
    }


@estoque_financeiro_bp.route('/assent/estoque-financeiro/importar', methods=['GET', 'POST'])
@role_required('admin')
def importar():
    previa = None

    if request.method == 'POST':
        acao = request.form.get('acao') or 'preview'

        try:
            if acao == 'preview':
                arquivo = request.files.get('arquivo')
                if arquivo and arquivo.filename:
                    nome_temporario, nome_original = _salvar_arquivo(arquivo)
                else:
                    nome_temporario = request.form.get('temp_name')
                    nome_original = request.form.get('original_filename')
                    if not nome_temporario:
                        flash('Selecione uma planilha .xlsx.', 'warning')
                        return redirect(url_for('estoque_financeiro.importar'))

                aba = request.form.get('aba')
                previa = _montar_previa(nome_temporario, nome_original, aba)

            elif acao == 'confirmar':
                nome_temporario = request.form.get('temp_name')
                nome_original = request.form.get('original_filename')
                aba = request.form.get('aba')

                caminho = _caminho_temporario(nome_temporario)
                registros, _sem_mapeamento = processar_planilha_estoque(caminho, aba)

                nomes_municipio = sorted({r['municipio'] for r in registros if r['municipio']})
                municipio_id_map = {}
                if nomes_municipio:
                    with get_db() as db:
                        with db.cursor() as cursor:
                            formato = ', '.join(['%s'] * len(nomes_municipio))
                            cursor.execute(f'SELECT municipio, municipio_id FROM municipio WHERE municipio IN ({formato})', tuple(nomes_municipio))
                            municipio_id_map = {row[0]: row[1] for row in cursor.fetchall()}

                inseridos = 0
                atualizados = 0
                ignorados_sem_municipio = 0

                with get_db() as db:
                    with db.cursor() as cursor:
                        colunas = ', '.join(['id_modulo'] + CAMPOS_FINANCEIROS)
                        placeholders = ', '.join(['%s'] * (len(CAMPOS_FINANCEIROS) + 1))
                        atualizacao = ', '.join(f'{c}=VALUES({c})' for c in CAMPOS_FINANCEIROS)
                        sql = (
                            f'INSERT INTO estoque_financeiro_modulos ({colunas}) VALUES ({placeholders}) '
                            f'ON DUPLICATE KEY UPDATE {atualizacao}'
                        )
                        for r in registros:
                            municipio_id = municipio_id_map.get(r['municipio']) if r['municipio'] else None
                            if not municipio_id:
                                ignorados_sem_municipio += 1
                                continue

                            cursor.execute(
                                'SELECT id FROM estoque_financeiro_modulos WHERE municipio_id=%s AND id_modulo=%s',
                                (municipio_id, r['id_modulo'])
                            )
                            ja_existe = cursor.fetchone() is not None

                            valores = [r['id_modulo']] + [
                                municipio_id if campo == 'municipio_id' else r.get(campo)
                                for campo in CAMPOS_FINANCEIROS
                            ]
                            cursor.execute(sql, tuple(valores))

                            if ja_existe:
                                atualizados += 1
                            else:
                                inseridos += 1

                        db.commit()

                gravar_log('IMPORTACAO_ESTOQUE_FINANCEIRO', (
                    f"Arquivo: {nome_original} | Aba: {aba} | "
                    f"Inseridos: {inseridos} | Atualizados: {atualizados} | "
                    f"Ignorados (sem município mapeado): {ignorados_sem_municipio}"
                ))
                flash(
                    f'Importação concluída: {inseridos} novos, {atualizados} atualizados'
                    + (f', {ignorados_sem_municipio} ignorados (sem município mapeado)' if ignorados_sem_municipio else '')
                    + '.',
                    'success'
                )
                return redirect(url_for('dashboard.cadastro_modulos'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            current_app.logger.error(f"Erro ao importar estoque financeiro: {e}")
            flash('Erro ao processar a planilha. Confira o arquivo e tente novamente.', 'danger')

    return render_template('importar_estoque_financeiro.html', previa=previa)


@estoque_financeiro_bp.route('/assent/estoque-financeiro/relatorio')
@role_required('assent', 'admin', 'assent_gestor')
def relatorio():
    municipios = [m.strip() for m in request.args.getlist('municipio') if m.strip()]
    with get_db() as db:
        buffer, filename, total = gerar_relatorio_estoque_pdf(
            db, session.get('username') or 'SISTEMA', municipios or None)

    if not buffer:
        flash('Nenhum registro de estoque encontrado para gerar o relatório.', 'warning')
        return redirect(url_for('dashboard.cadastro_modulos'))

    gravar_log('RELATORIO_ESTOQUE_AREAS', f"Arquivo: {filename} | Registros: {total}")
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
