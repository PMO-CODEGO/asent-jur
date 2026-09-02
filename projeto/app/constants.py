COLUNAS = [
    # Cadastro do Imóvel
    'municipio', 'codigo_ibge_municipio', 'matricula_loteamento', 'distrito', 'sigla_loteamento',
    'quadra', 'qtd_modulos', 'logradouro', 'area_lote_m2',
    'matricula_modulo', 'codigo_modulo_externo', 'cci', 'inscricao_municipal', 'area_institucional',
    # Cadastro do Assentamento
    'empresa', 'cnpj', 'nome_representante_legal', 'telefone_representante_legal',
    'email_representante_legal', 'processo_sei', 'ramo_de_atividade',
    'status_de_assentamento', 'data_escrituracao', 'data_contrato_de_compra_e_venda',
    'registro_na_matricula',
    # Registro Anterior do Assentamento
    'empresa_anterior', 'cnpj_anterior', 'processo_anterior',
    # Situação de Ocupação
    'relatorio_vistoria', 'ultima_vistoria', 'taxa_ocupacao_imovel',
    'atividade_industrial', 'irregularidades', 'empregos_gerados',
    'projeto_ocupacao_area', 'data_aprovacao_poa', 'cronograma_fisico_obra_meses',
    'imovel_regular_irregular', 'observacoes',
    # Controle (preenchido automaticamente pelo sistema)
    'atualizado',
]

LABELS = {
    'municipio': 'Município',
    'codigo_ibge_municipio': 'Código IBGE do Município',
    'matricula_loteamento': 'Matrícula do Loteamento',
    'distrito': 'Distrito',
    'sigla_loteamento': 'Sigla do Loteamento',
    'quadra': 'Quadra',
    'qtd_modulos': 'Quantidade de Módulos',
    'logradouro': 'Logradouro',
    'area_lote_m2': 'Área do Lote (m²)',
    'matricula_modulo': 'Matrícula do Módulo',
    'codigo_modulo_externo': 'Código do Módulo',
    'cci': 'CCI (Certidão de Cadastro do Imóvel)',
    'inscricao_municipal': 'Inscrição Municipal',
    'area_institucional': 'Área Institucional',
    'empresa': 'Empresa',
    'cnpj': 'CNPJ',
    'nome_representante_legal': 'Nome do Representante Legal',
    'telefone_representante_legal': 'Telefone do Representante Legal',
    'email_representante_legal': 'E-mail do Representante Legal',
    'processo_sei': 'Processo SEI',
    'ramo_de_atividade': 'Ramo de Atividade',
    'status_de_assentamento': 'Status de Assentamento',
    'data_escrituracao': 'Data de Escrituração',
    'data_contrato_de_compra_e_venda': 'Data do Contrato de Compra e Venda',
    'registro_na_matricula': 'Registro na Matrícula',
    'empresa_anterior': 'Empresa (Registro Anterior)',
    'cnpj_anterior': 'CNPJ (Registro Anterior)',
    'processo_anterior': 'Processo (Registro Anterior)',
    'relatorio_vistoria': 'Relatório de Vistoria',
    'ultima_vistoria': 'Última Vistoria',
    'taxa_ocupacao_imovel': 'Taxa de Ocupação do Imóvel (%)',
    'atividade_industrial': 'Atividade Industrial',
    'irregularidades': 'Irregularidades',
    'empregos_gerados': 'Empregos Gerados',
    'projeto_ocupacao_area': 'Projeto de Ocupação da Área',
    'data_aprovacao_poa': 'Data de Aprovação do POA',
    'cronograma_fisico_obra_meses': 'Cronograma Físico de Obra (meses)',
    'imovel_regular_irregular': 'Imóvel Regular/Irregular',
    'observacoes': 'Observações',
    'atualizado': 'Última atualização',
}

# todos os campos sao editaveis pelo setor de Assentamento; 'atualizado' e
# preenchido automaticamente pelo sistema (nunca pelo usuario) e por isso e
# filtrado a parte nas rotas de cadastro/edicao.
chaves_fixas = COLUNAS
labels_fixas = LABELS

colunas_map = {
    'MUNICIPIO': 'municipio',
    'MATRÍCULA DO LOTEAMENTO': 'matricula_loteamento',
    'DISTRITO': 'distrito',
    'SIGLA DO LOTEAMENTO': 'sigla_loteamento',
    'QUADRA': 'quadra',
    'QTD. MÓDULOS': 'qtd_modulos',
    'LOGRADOURO': 'logradouro',
    'TAMANHO(M²)': 'area_lote_m2',
    'MATRÍCULA DO MÓDULO': 'matricula_modulo',
    'CCI': 'cci',
    'INSCRIÇÃO MUNICIPAL': 'inscricao_municipal',
    'ÁREA INSTITUCIONAL': 'area_institucional',
    'EMPRESA': 'empresa',
    'CNPJ': 'cnpj',
    'NOME REPRESENTANTE LEGAL': 'nome_representante_legal',
    'TELEFONE REPRESENTANTE LEGAL': 'telefone_representante_legal',
    'E-MAIL REPRESENTANTE LEGAL': 'email_representante_legal',
    'PROCESSO SEI': 'processo_sei',
    'RAMO DE ATIVIDADE': 'ramo_de_atividade',
    'STATUS DE ASSENTAMENTO': 'status_de_assentamento',
    'DATA ESCRITURAÇÃO': 'data_escrituracao',
    'DATA CONTRATO DE COMPRA E VENDA': 'data_contrato_de_compra_e_venda',
    'REGISTRO NA MATRÍCULA': 'registro_na_matricula',
    'ÚLTIMA VISTORIA': 'ultima_vistoria',
    'TAXA E OCUPAÇÃO DO IMÓVEL(%)': 'taxa_ocupacao_imovel',
    'IRREGULARIDADES?': 'irregularidades',
    'EMPREGOS GERADOS': 'empregos_gerados',
    'IMÓVEL REGULAR/IRREGULAR': 'imovel_regular_irregular',
    'OBSEVAÇÕES': 'observacoes',
    'ATUALIZADO': 'atualizado',
}

campos_numericos = [
    'empregos_gerados', 'quadra', 'qtd_modulos', 'area_lote_m2',
    'taxa_ocupacao_imovel', 'cronograma_fisico_obra_meses',
]

ramo_de_atividade_opcoes = [
    "ADMINISTRAÇÃO - CODEGO",
    "AGRONEGÓCIO",
    "ALIMENTÍCIO",
    "ÁREA LIVRE",
    "AUTOMOBILÍSTICO",
    "BIOCOMBUSTÍVEIS",
    "CONSTRUÇÃO CIVIL",
    "COUREIRO",
    "DEFESA E SEGURANÇA",
    "FARMACÊUTICO",
    "GASES INDUSTRIAIS",
    "GESTÃO DE RESÍDUOS",
    "INDEFINIDO",
    "LAVANDERIA",
    "MADEIREIRO",
    "MÁQUINAS E EQUIPAMENTOS",
    "MARMORARIA",
    "MATERIAIS ELÉTRICOS",
    "MATERIAIS HOSPITALARES",
    "MATERIAIS PLÁSTICOS",
    "METAL QUÍMICO",
    "METALÚRGICA",
    "MOVELEIRO",
    "PAPEL",
    "PRODUTOS DE HIGIENE E PERFUMARIA",
    "PRODUTOS DE LIMPEZA, HIGIENE E PERFUMARIA",
    "QUÍMICO",
    "ROUPAS, CALÇADOS E ACESSÓRIOS",
    "SERVIÇOS AUXILIARES",
    "SERVIÇOS AUXILIARES - ALIMENTAÇÃO",
    "SERVIÇOS AUXILIARES - COMBUSTÍVEIS",
    "SERVIÇOS AUXILIARES - TRANSPORTE",
    "SERVIÇOS PÚBLICOS",
    "SOLUÇÕES AMBIENTAIS",
    "SOLUÇÕES TÉRMICAS",
    "TERMINAL ALFANDEGÁRIO",
    "TÊXTIL",
    "VIDRAÇARIA"
]

status_opcoes = [
    "ATIVO",
    "ARQUIVADO",
    "SUSPENSO"
]

status_de_assentamento_opcoes = [
    'ÁREA LIVRE',
    'ESCRITURADA',
    'ÁREA COM CVV/CDRU',
    'ÁREA EM ASSENTAMENTO',
    'ÁREA COM ACORDO DESENVOLVE GOIÁS',
    'ÁREA COM AÇÃO JUDICIAL',
    'ÁREA AÇÃO DA PGE',
    'ÁREA LOCADA PELA CIA À TERCEIROS',
    'ÁREA EM ACORDO JUDICIAL/EXTRAJUDICIAL',
    '-',
    'ÁREA DA CODEGO',
    'ÁREA PÚBLICA',
    'ÁREA COM CONTRATO DE CESSÃO DE USO',
    'ÁREA IMITIDA NA POSSE',
    'ÁREA PENDENTE DE ATUALIZAÇÃO'
]

imovel_opcoes = [
    'REGULAR',
    'IRREGULAR'
]
