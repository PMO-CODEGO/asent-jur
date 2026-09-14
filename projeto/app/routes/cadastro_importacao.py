import os
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from app.db import get_db
from app.utils.decorators import role_required
from app.services.log_service import gravar_log
from app.routes.cadastro_modulos import CAMPOS
from app.services.cadastro_importacao_service import (
    listar_abas_candidatas,
    detectar_aba_padrao,
    processar_planilha_cadastro,
)

cadastro_importacao_bp = Blueprint('cadastro_importacao', __name__)

CAMPOS_CADASTRO = [f for f, _ in CAMPOS]


def _pasta_importacoes():
    caminho = os.path.join(current_app.root_path, 'uploads', 'importacoes_cadastro_modulos')
    os.makedirs(caminho, exist_ok=True)
    return caminho


def _salvar_arquivo(arquivo):
    nome_original = secure_filename(arquivo.filename or 'cadastro.xlsx')
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


def _mapa_municipios(nomes_municipio):
    if not nomes_municipio:
        return {}
    with get_db() as db:
        with db.cursor() as cursor:
            formato = ', '.join(['%s'] * len(nomes_municipio))
            cursor.execute(f'SELECT municipio, ibge_id FROM municipio WHERE municipio IN ({formato})', tuple(nomes_municipio))
            return {row[0]: str(row[1]) for row in cursor.fetchall()}


def _montar_registro_final(r, ibge_id):
    registro = dict(r)
    registro['codigo_ibge_municipio'] = ibge_id
    return registro


def _montar_previa(nome_temporario, nome_original, aba):
    caminho = _caminho_temporario(nome_temporario)
    abas = listar_abas_candidatas(caminho)
    aba_selecionada = aba if aba in abas else detectar_aba_padrao(abas)

    registros = processar_planilha_cadastro(caminho, aba_selecionada)

    nomes_municipio = sorted({r['municipio'] for r in registros if r['municipio']})
    ibge_id_map = _mapa_municipios(nomes_municipio)

    codigos_existentes = set()
    if registros:
        with get_db() as db:
            with db.cursor() as cursor:
                id_modulos = [r['id_modulo'] for r in registros]
                formato_ids = ', '.join(['%s'] * len(id_modulos))
                cursor.execute(
                    f'SELECT DISTINCT codigo_ibge_municipio, id_modulo FROM municipal_lots '
                    f'WHERE id_modulo IN ({formato_ids})',
                    tuple(id_modulos)
                )
                codigos_existentes = {(row[0], row[1]) for row in cursor.fetchall()}

    resumo_por_municipio = {}
    for r in registros:
        ibge_id = ibge_id_map.get(r['municipio']) if r['municipio'] else None
        r['codigo_ibge_municipio'] = ibge_id
        r['ja_cadastrado'] = (ibge_id, r['id_modulo']) in codigos_existentes
        chave = r['municipio'] or 'SEM MUNICÍPIO MAPEADO'
        item = resumo_por_municipio.setdefault(chave, {'municipio': chave, 'total': 0, 'existentes': 0, 'sem_municipio': 0, 'registros': []})
        item['total'] += 1
        if r['ja_cadastrado']:
            item['existentes'] += 1
        if not ibge_id:
            item['sem_municipio'] += 1
        item['registros'].append(r)

    return {
        'temp_name': nome_temporario,
        'original_filename': nome_original,
        'abas': abas,
        'aba_selecionada': aba_selecionada,
        'total_registros': len(registros),
        'grupos': sorted(resumo_por_municipio.values(), key=lambda g: g['municipio']),
    }


@cadastro_importacao_bp.route('/assent/cadastro-modulos/importar', methods=['GET', 'POST'])
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
                        return redirect(url_for('cadastro_importacao.importar'))

                aba = request.form.get('aba')
                previa = _montar_previa(nome_temporario, nome_original, aba)

            elif acao == 'confirmar':
                nome_temporario = request.form.get('temp_name')
                nome_original = request.form.get('original_filename')
                aba = request.form.get('aba')

                caminho = _caminho_temporario(nome_temporario)
                registros = processar_planilha_cadastro(caminho, aba)

                nomes_municipio = sorted({r['municipio'] for r in registros if r['municipio']})
                ibge_id_map = _mapa_municipios(nomes_municipio)

                inseridos = 0
                atualizados = 0
                ignorados_sem_municipio = 0

                with get_db() as db:
                    with db.cursor() as cursor:
                        colunas = ', '.join(CAMPOS_CADASTRO)
                        placeholders = ', '.join(['%s'] * len(CAMPOS_CADASTRO))
                        atualizacao = ', '.join(f'{c}=VALUES({c})' for c in CAMPOS_CADASTRO if c != 'codigo_ibge_municipio' and c != 'id_modulo')
                        sql = (
                            f'INSERT INTO municipal_lots ({colunas}) VALUES ({placeholders}) '
                            f'ON DUPLICATE KEY UPDATE {atualizacao}'
                        )
                        for r in registros:
                            ibge_id = ibge_id_map.get(r['municipio']) if r['municipio'] else None
                            if not ibge_id:
                                ignorados_sem_municipio += 1
                                continue

                            registro_final = _montar_registro_final(r, ibge_id)

                            cursor.execute(
                                'SELECT id FROM municipal_lots WHERE codigo_ibge_municipio=%s AND id_modulo=%s',
                                (ibge_id, r['id_modulo'])
                            )
                            ja_existe = cursor.fetchone() is not None

                            valores = tuple(registro_final.get(campo) for campo in CAMPOS_CADASTRO)
                            cursor.execute(sql, valores)

                            if ja_existe:
                                atualizados += 1
                            else:
                                inseridos += 1

                        db.commit()

                gravar_log('IMPORTACAO_CADASTRO_MODULOS', (
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
            current_app.logger.error(f"Erro ao importar cadastro de módulos: {e}")
            flash('Erro ao processar a planilha. Confira o arquivo e tente novamente.', 'danger')

    return render_template('importar_cadastro_modulos.html', previa=previa)
