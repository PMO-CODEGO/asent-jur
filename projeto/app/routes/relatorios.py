from datetime import datetime
from io import BytesIO
from pathlib import Path
import os

from flask import Blueprint, current_app, flash, make_response, redirect, render_template, request, session, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db import get_db
from app.constants import LABELS
from app.services.juridico_schema_service import garantir_schema_juridico
from app.services.pdf_service import add_header_footer, bloco_identificacao, linha_assinatura
from app.utils.decorators import role_required

relatorio_bp = Blueprint("relatorio", __name__)

EMPRESA_INFOS_SEED_CACHE = None

RELATORIO_EMPRESA_ORDEM = [
    'municipio',
    'distrito',
    'empresa',
    'cnpj',
    'ramo_de_atividade',
    'processo_sei',
    'status_de_assentamento',
    'acao_judicial',
    'imovel_regular_irregular',
    'quadra',
    'modulo_s',
    'qtd_modulos',
    'tamanho_m2',
    'matricula_s',
    'taxa_e_ocupacao_do_imovel',
    'empregos_gerados',
    'data_escrituracao',
    'data_contrato_de_compra_e_venda',
    'ultima_vistoria',
    'atualizado',
    'observacoes',
    'observacoes_1',
    'obsevacoes',
    'irregularidades',
    'observacoes_2',
    'observacoes_3',
]

RELATORIO_PROCESSO_LABELS = [
    ('numero_processo', 'Numero CNJ'),
    ('titulo', 'Titulo'),
    ('descricao', 'Descricao'),
    ('tipo_acao', 'Tipo de acao'),
    ('tribunal', 'Tribunal'),
    ('vara', 'Vara'),
    ('comarca', 'Comarca'),
    ('valor_da_causa', 'Valor da causa'),
    ('status', 'Status'),
    ('fase', 'Fase'),
    ('data_criacao', 'Data de criacao'),
    ('recurso_acionado', 'Recurso acionado'),
    ('tipo_recurso', 'Tipo de recurso'),
]


def obter_usuario_logado():
    """Busca o nome/login do usuário autenticado no Flask-Login ou Session."""
    try:
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            nome = getattr(current_user, 'nome', None) or getattr(current_user, 'username', None)
            if nome:
                return nome
    except Exception:
        pass

    return (
        session.get('username') or
        session.get('usuario') or
        session.get('nome') or
        session.get('user') or
        'SISTEMA'
    )


def valor_pdf(valor):
    if valor in (None, ''):
        return '-'
    if isinstance(valor, bool):
        return 'SIM' if valor else 'NAO'
    if isinstance(valor, int) and valor in (0, 1):
        return 'SIM' if valor else 'NAO'
    return str(valor)


IMAGEM_PADRAO = '/static/imagens_empresas/empresa_default.png'


def caminho_imagem_empresa(empresa_id):
    static_dir = Path(current_app.root_path) / 'static'
    padroes = [
        static_dir / 'imagens_empresas',
        static_dir,
    ]

    for pasta in padroes:
        if not pasta.exists():
            continue
        arquivos = sorted(pasta.glob(f'empresa{empresa_id}*'))
        for arquivo in arquivos:
            if arquivo.is_file() and 'default' not in arquivo.name:
                return '/static/' + arquivo.relative_to(static_dir).as_posix()

    return IMAGEM_PADRAO


def dividir_tuplas_sql(valores_sql):
    tuplas = []
    profundidade = 0
    inicio = None
    em_texto = False

    indice = 0
    while indice < len(valores_sql):
        char = valores_sql[indice]

        if em_texto:
            if char == "'":
                if indice + 1 < len(valores_sql) and valores_sql[indice + 1] == "'":
                    indice += 1
                else:
                    em_texto = False
        elif char == "'":
            em_texto = True
        elif char == '(':
            if profundidade == 0:
                inicio = indice
            profundidade += 1
        elif char == ')':
            profundidade -= 1
            if profundidade == 0 and inicio is not None:
                tuplas.append(valores_sql[inicio + 1:indice])
                inicio = None

        indice += 1

    return tuplas


def dividir_campos_sql(tupla_sql):
    campos = []
    atual = []
    em_texto = False

    indice = 0
    while indice < len(tupla_sql):
        char = tupla_sql[indice]

        if em_texto:
            if char == "'":
                if indice + 1 < len(tupla_sql) and tupla_sql[indice + 1] == "'":
                    atual.append("'")
                    indice += 1
                else:
                    em_texto = False
            else:
                atual.append(char)
        elif char == "'":
            em_texto = True
        elif char == ',':
            campos.append(''.join(atual).strip())
            atual = []
        else:
            atual.append(char)

        indice += 1

    campos.append(''.join(atual).strip())
    return [None if campo.upper() == 'NULL' else campo for campo in campos]


def carregar_empresa_infos_seed():
    global EMPRESA_INFOS_SEED_CACHE
    if EMPRESA_INFOS_SEED_CACHE is not None:
        return EMPRESA_INFOS_SEED_CACHE

    infos = {}
    seed_dir = Path(current_app.root_path).parent / 'docker' / 'mysql' / 'init'
    seed_paths = sorted(seed_dir.glob('*empresa_infos_descricoes*.sql'))
    if not seed_paths:
        EMPRESA_INFOS_SEED_CACHE = infos
        return infos

    for seed_path in seed_paths:
        conteudo = seed_path.read_text(encoding='utf-8', errors='replace')
        if 'VALUES' not in conteudo or 'ON DUPLICATE KEY UPDATE' not in conteudo:
            continue

        valores_sql = conteudo.split('VALUES', 1)[1].split('ON DUPLICATE KEY UPDATE', 1)[0]
        for tupla_sql in dividir_tuplas_sql(valores_sql):
            campos = dividir_campos_sql(tupla_sql)
            if len(campos) < 3:
                continue
            empresa_id, descricao, caminho_imagem = campos[:3]
            if not str(empresa_id).isdigit():
                continue
            info_atual = infos.get(str(empresa_id), {})
            infos[str(empresa_id)] = {
                'descricao': descricao or info_atual.get('descricao', ''),
                'foto': caminho_imagem or info_atual.get('foto', ''),
            }

    EMPRESA_INFOS_SEED_CACHE = infos
    return infos


def adicionar_tabela_chave_valor(story, dados, labels, cell_style, header_color='#1a233a'):
    tabela_dados = [["Campo", "Valor"]]
    for chave, label in labels:
        tabela_dados.append([
            Paragraph(label, cell_style),
            Paragraph(valor_pdf(dados.get(chave)), cell_style),
        ])

    tabela = Table(tabela_dados, colWidths=[150, 350], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.transparent),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(tabela)


def adicionar_lista_eventos(story, titulo, eventos, subtitle_style, cell_style):
    story.append(Spacer(1, 16))
    story.append(Paragraph(titulo, subtitle_style))
    if not eventos:
        story.append(Paragraph("Nenhum registro.", cell_style))
        return

    linhas = [["Data", "Titulo", "Descricao"]]
    for evento in eventos:
        linhas.append([
            Paragraph(valor_pdf(evento.get('data_evento') or evento.get('created_at')), cell_style),
            Paragraph(valor_pdf(evento.get('titulo') or evento.get('categoria')), cell_style),
            Paragraph(valor_pdf(evento.get('descricao')), cell_style),
        ])

    tabela = Table(linhas, colWidths=[90, 140, 270], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7f1d1d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tabela)


def gerar_pdf_processo(processo, partes, eventos, documentos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=90, bottomMargin=72)

    emitido_por = obter_usuario_logado()
    data_emissao = datetime.now().strftime('%d/%m/%Y')
    doc_code = f"CODEGO-JUR-{processo.get('id', '000'):04}" if isinstance(processo.get('id'), int) else 'CODEGO-JUR'
    
    doc._iso_doc_code = doc_code
    doc._iso_rev = 'Rev. 00'
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ProcessoTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=14, leading=20, alignment=1,
        spaceAfter=6, textColor=colors.HexColor('#002b5c'))
    subtitle_style = ParagraphStyle('ProcessoSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=14, spaceAfter=6,
        spaceBefore=12, textColor=colors.HexColor('#002b5c'),
        borderPad=4, backColor=colors.HexColor('#f0f4f8'),
        borderColor=colors.HexColor('#002b5c'), borderWidth=0.5, borderRadius=2)
    cell_style = ParagraphStyle('ProcessoCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12, wordWrap='CJK')
    styles_map = {'cell': cell_style, 'bold': title_style}

    story = []

    bloco_identificacao(story,
        titulo=f"Relatório de Processo Jurídico — {valor_pdf(processo.get('numero_processo'))}",
        doc_code=doc_code, rev='Rev. 00', data_emissao=data_emissao,
        emitido_por=emitido_por, styles_map=styles_map)

    story.append(Paragraph("DADOS PRINCIPAIS DO PROCESSO", subtitle_style))
    adicionar_tabela_chave_valor(story, processo, RELATORIO_PROCESSO_LABELS, cell_style)

    story.append(Spacer(1, 8))
    story.append(Paragraph("PARTES ENVOLVIDAS", subtitle_style))
    partes_labels = [('papel', 'Papel'), ('nome', 'Nome'), ('tipo_parte', 'Tipo'), ('contato', 'Contato'), ('observacoes', 'Observações')]
    if partes:
        for parte in partes:
            adicionar_tabela_chave_valor(story, parte, partes_labels, cell_style, header_color='#002b5c')
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Nenhuma parte cadastrada.", cell_style))

    adicionar_lista_eventos(story, "PRAZOS", [e for e in eventos if e.get('categoria') == 'prazo'], subtitle_style, cell_style)
    adicionar_lista_eventos(story, "MOVIMENTAÇÕES", [e for e in eventos if e.get('categoria') == 'movimentacao'], subtitle_style, cell_style)
    adicionar_lista_eventos(story, "DOCUMENTOS TEXTUAIS", [e for e in eventos if e.get('categoria') == 'documento'], subtitle_style, cell_style)

    story.append(Spacer(1, 8))
    story.append(Paragraph("ARQUIVOS ANEXADOS", subtitle_style))
    if documentos:
        labels_doc = [('nome', 'Nome'), ('tipo', 'Tipo'), ('data_documento', 'Data'), ('nome_arquivo_original', 'Arquivo'), ('observacao', 'Observação')]
        for documento in documentos:
            adicionar_tabela_chave_valor(story, documento, labels_doc, cell_style, header_color='#002b5c')
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Nenhum arquivo anexado.", cell_style))

    linha_assinatura(story, emitido_por, styles_map)

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer


def gerar_pdf_geral_processos(processos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=90, bottomMargin=72)

    emitido_por = obter_usuario_logado()
    data_emissao = datetime.now().strftime('%d/%m/%Y')
    doc._iso_doc_code = 'CODEGO-JUR-GERAL'
    doc._iso_rev = 'Rev. 00'
    doc._iso_data = data_emissao
    doc._iso_emitido_por = emitido_por

    styles = getSampleStyleSheet()
    subtitle_style = ParagraphStyle('GeralSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=14, spaceAfter=6,
        spaceBefore=12, textColor=colors.HexColor('#002b5c'),
        borderPad=4, backColor=colors.HexColor('#f0f4f8'),
        borderColor=colors.HexColor('#002b5c'), borderWidth=0.5, borderRadius=2)
    cell_style = ParagraphStyle('GeralCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7, leading=9, wordWrap='CJK')
    styles_map = {'cell': cell_style, 'bold': subtitle_style}

    story = []

    bloco_identificacao(story,
        titulo=f"Relatório Geral de Processos Jurídicos ({len(processos)} processos)",
        doc_code='CODEGO-JUR-GERAL', rev='Rev. 00', data_emissao=data_emissao,
        emitido_por=emitido_por, styles_map=styles_map)

    # Resumo por status
    resumo_status = {}
    for processo in processos:
        status = valor_pdf(processo.get('status'))
        resumo_status[status] = resumo_status.get(status, 0) + 1

    if resumo_status:
        story.append(Paragraph("RESUMO POR STATUS", subtitle_style))
        resumo_linhas = [['Status', 'Quantidade']]
        for status, qtd in sorted(resumo_status.items()):
            resumo_linhas.append([Paragraph(status, cell_style), Paragraph(str(qtd), cell_style)])
        resumo_table = Table(resumo_linhas, colWidths=[400, 100], repeatRows=1)
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002b5c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(resumo_table)
        story.append(Spacer(1, 10))

    # Tabela de processos
    story.append(Paragraph("LISTAGEM DE PROCESSOS", subtitle_style))
    linhas = [['CNJ', 'Título', 'Tipo', 'Tribunal', 'Comarca', 'Status', 'Fase']]
    for processo in processos:
        linhas.append([
            Paragraph(valor_pdf(processo.get('numero_processo')), cell_style),
            Paragraph(valor_pdf(processo.get('titulo')), cell_style),
            Paragraph(valor_pdf(processo.get('tipo_acao') or processo.get('tipo_processo')), cell_style),
            Paragraph(valor_pdf(processo.get('tribunal')), cell_style),
            Paragraph(valor_pdf(processo.get('comarca')), cell_style),
            Paragraph(valor_pdf(processo.get('status')), cell_style),
            Paragraph(valor_pdf(processo.get('fase')), cell_style),
        ])

    tabela = Table(linhas, colWidths=[82, 95, 80, 75, 65, 55, 58], repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002b5c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(tabela)

    linha_assinatura(story, emitido_por, styles_map)

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    buffer.seek(0)
    return buffer


@relatorio_bp.route('/relatorio', methods=['GET', 'POST'])
@role_required('assent', 'jur', 'admin', 'assent_gestor', 'jur_gestor')
def relatorios():
    role = session.get('role')
    modo = request.args.get('modo')

    if not modo:
        modo = 'jur' if role in ('jur', 'jur_gestor') else 'assent'

    if request.method == 'POST':
        if modo == 'jur':
            relatorio_tipo = request.form.get('relatorio_tipo', 'processo')

            if relatorio_tipo == 'geral_processos':
                try:
                    with get_db() as db:
                        garantir_schema_juridico(db)
                        with db.cursor(dictionary=True) as cursor:
                            cursor.execute("""
                                SELECT id, numero_processo, titulo, descricao, tipo_acao, tipo_processo,
                                       tribunal, vara, comarca, valor_da_causa, status, fase,
                                       data_criacao, assunto_judicial, recurso_acionado, tipo_recurso
                                FROM processos
                                ORDER BY numero_processo
                            """)
                            processos = cursor.fetchall()

                    buffer = gerar_pdf_geral_processos(processos)
                    response = make_response(buffer.getvalue())
                    response.headers['Content-Type'] = 'application/pdf'
                    response.headers['Content-Disposition'] = 'inline; filename="relatorio_geral_processos.pdf"'
                    return response
                except Exception as e:
                    return f"Erro PDF: {e}"

            processo_id = request.form.get('processo')
            if not processo_id:
                flash("Selecione um processo.", "warning")
                return redirect(url_for('relatorio.relatorios', modo=modo))

            try:
                with get_db() as db:
                    garantir_schema_juridico(db)
                    with db.cursor(dictionary=True) as cursor:
                        cursor.execute("""
                            SELECT id, numero_processo, titulo, descricao, tipo_acao, tipo_processo,
                                   tribunal, vara, comarca, valor_da_causa, status, fase,
                                   data_criacao, assunto_judicial, recurso_acionado, tipo_recurso
                            FROM processos
                            WHERE id = %s
                        """, (int(processo_id),))
                        processo = cursor.fetchone()

                        if not processo:
                            flash("Processo nao encontrado.", "warning")
                            return redirect(url_for('relatorio.relatorios', modo=modo))

                        cursor.execute("SELECT * FROM processo_partes WHERE processo_id = %s ORDER BY id", (int(processo_id),))
                        partes = cursor.fetchall()
                        cursor.execute("""
                            SELECT *
                            FROM processo_eventos
                            WHERE processo_id = %s
                            ORDER BY COALESCE(data_evento, created_at) DESC, id DESC
                        """, (int(processo_id),))
                        eventos = cursor.fetchall()
                        cursor.execute("""
                            SELECT *
                            FROM processo_documentos
                            WHERE processo_id = %s
                            ORDER BY COALESCE(data_documento, created_at) DESC, id DESC
                        """, (int(processo_id),))
                        documentos = cursor.fetchall()

                buffer = gerar_pdf_processo(processo, partes, eventos, documentos)
                response = make_response(buffer.getvalue())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'inline; filename="relatorio_processo_{processo_id}.pdf"'
                return response
            except Exception as e:
                return f"Erro PDF: {e}"

        empresa_id = request.form.get('empresa')
        if not empresa_id:
            flash("Selecione uma empresa.", "warning")
            return redirect(url_for('relatorio.relatorios', modo=modo))

        try:
            with get_db() as db:
                with db.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT * FROM municipal_lots WHERE id = %s", (int(empresa_id),))
                    lot = cursor.fetchone()

            if not lot:
                return "Empresa não encontrada.", 404

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=A4,
                leftMargin=54, rightMargin=54, topMargin=90, bottomMargin=72
            )

            emitido_por = obter_usuario_logado()
            data_emissao = datetime.now().strftime('%d/%m/%Y')
            doc_code = f"CODEGO-ASS-{str(empresa_id).zfill(4)}"
            
            doc._iso_doc_code = doc_code
            doc._iso_rev = 'Rev. 00'
            doc._iso_data = data_emissao
            doc._iso_emitido_por = emitido_por

            styles = getSampleStyleSheet()
            cell_style = ParagraphStyle('AssCell', parent=styles['Normal'],
                fontName='Helvetica', fontSize=9, leading=12, wordWrap='CJK')
            subtitle_style = ParagraphStyle('AssSubtitle', parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=10, leading=14, spaceAfter=6,
                spaceBefore=12, textColor=colors.HexColor('#002b5c'),
                borderPad=4, backColor=colors.HexColor('#f0f4f8'),
                borderColor=colors.HexColor('#002b5c'), borderWidth=0.5, borderRadius=2)
            styles_map = {'cell': cell_style, 'bold': subtitle_style}

            story = []

            titulo_relatorio = "Relatório Jurídico de Empresa" if modo == 'jur' else "Relatório de Assentamento Industrial"
            bloco_identificacao(story,
                titulo=f"{titulo_relatorio} — {lot.get('empresa', 'N/A')}",
                doc_code=doc_code, rev='Rev. 00', data_emissao=data_emissao,
                emitido_por=emitido_por, styles_map=styles_map)

            story.append(Paragraph("DADOS CADASTRAIS", subtitle_style))

            campos_juridicos_legados = {'processo_judicial', 'status', 'assunto_judicial', 'valor_da_causa'}
            campos_disponiveis = {
                chave: valor for chave, valor in lot.items()
                if chave != 'id' and chave not in campos_juridicos_legados
            }
            chaves_ordenadas = [chave for chave in RELATORIO_EMPRESA_ORDEM if chave in campos_disponiveis]
            chaves_ordenadas.extend(chave for chave in campos_disponiveis if chave not in chaves_ordenadas)

            data = [['Campo', 'Valor']]
            for chave in chaves_ordenadas:
                valor = campos_disponiveis[chave]
                data.append([
                    Paragraph(LABELS.get(chave, str(chave).replace('_', ' ').title()), cell_style),
                    Paragraph(str(valor) if valor is not None else '-', cell_style)
                ])

            table = Table(data, colWidths=[160, 340], repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#002b5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('TOPPADDING', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('LEFTPADDING', (0, 1), (-1, -1), 6),
                ('RIGHTPADDING', (0, 1), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#002b5c')),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ]))
            story.append(table)

            linha_assinatura(story, emitido_por, styles_map)

            doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

            buffer.seek(0)
            response = make_response(buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="relatorio_{empresa_id}.pdf"'
            return response
        except Exception as e:
            return f"Erro PDF: {e}"

    if modo == 'jur':
        processos = []
        try:
            with get_db() as db:
                garantir_schema_juridico(db)
                with db.cursor(dictionary=True) as cursor:
                    cursor.execute("""
                        SELECT id, numero_processo, titulo, tipo_acao, tribunal, comarca, status, fase
                        FROM processos
                        ORDER BY numero_processo
                    """)
                    processos = cursor.fetchall()
        except Exception as err:
            print("Erro ao carregar processos para relatorio juridico:", err)

        return render_template('relatorios_jur.html', processos=processos)

    empresas = []
    empresas_info = {}

    try:
        with get_db() as db:
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT
                        ml.id,
                        ml.municipio,
                        ml.empresa,
                        ml.cnpj,
                        ml.processo_sei,
                        COALESCE(proc.numeros_processos, '') AS numeros_processos
                    FROM municipal_lots ml
                    LEFT JOIN (
                        SELECT empresa_id, GROUP_CONCAT(numero_processo SEPARATOR ' ') AS numeros_processos
                        FROM processos
                        GROUP BY empresa_id
                    ) proc ON proc.empresa_id = ml.id
                    WHERE ml.empresa != '-'
                    ORDER BY ml.empresa
                """)
                empresas = cursor.fetchall()
                cursor.execute("SELECT empresa_id, descricao, caminho_imagem FROM empresa_infos")
                infos = cursor.fetchall()

        seed_infos = carregar_empresa_infos_seed()

        for row in infos:
            empresa_id = str(row['empresa_id'])
            seed_info = seed_infos.get(empresa_id, {})
            empresas_info[empresa_id] = {
                "descricao": row.get('descricao') or seed_info.get('descricao') or 'Sem descrição cadastrada.',
                "foto": row.get('caminho_imagem') or seed_info.get('foto') or caminho_imagem_empresa(empresa_id) or IMAGEM_PADRAO,
            }

        for empresa in empresas:
            empresa_id = str(empresa.get('id'))
            if empresa_id in empresas_info:
                if not empresas_info[empresa_id].get('foto'):
                    empresas_info[empresa_id]['foto'] = caminho_imagem_empresa(empresa_id)
                continue

            seed_info = seed_infos.get(empresa_id, {})
            empresas_info[empresa_id] = {
                "descricao": seed_info.get('descricao') or 'Sem descrição cadastrada.',
                "foto": seed_info.get('foto') or caminho_imagem_empresa(empresa_id) or IMAGEM_PADRAO,
            }
    except Exception as err:
        print("Erro ao carregar dados:", err)

    return render_template('relatorios.html', empresas=empresas, empresas_info=empresas_info)
