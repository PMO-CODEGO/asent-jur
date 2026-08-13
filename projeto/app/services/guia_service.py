# Conteudo do Codi, o personagem-guia (mascote flutuante com dicas contextuais por tela).
# As dicas sao escritas na primeira pessoa, como se o proprio Codi estivesse falando.
# Para adicionar uma tela nova: crie uma entrada aqui com uma chave curta (ex: 'cadastro')
# e inclua, no template, `{% set guia_pagina = 'cadastro' %}{% include 'partials/guia_mascote.html' %}`
# logo antes do `</body>`.
#
# 'pose' referencia um arquivo app/static/mascote_codego_<pose>.png. Poses disponiveis:
# aceno, aceno_feliz, apontando_mapa, bracos_cruzados, duvida, explicando, lupa,
# mapa_papel, notebook, piscando_apontando_cima, prancheta_positivo, sentado_notebook,
# thumbs_phone.

GUIA_CONTEUDO = {
    'login': {
        'titulo': 'sobre o login',
        'pose': 'aceno',
        'dicas': [
            'Oi, eu sou o Codi! Usa seu usuário e senha cadastrados pra entrar por aqui.',
            'Esqueceu a senha? Sem crise, clica em "Esqueci minha senha" que eu te ajudo a redefinir por e-mail.',
            'O que você vai ver depois de entrar depende do seu perfil de acesso.',
        ],
    },
    'inicio_assent': {
        'titulo': 'sobre esta página',
        'pose': 'aceno_feliz',
        'dicas': [
            'Bem-vindo! Em "Controle de Área" você encontra áreas brutas, parceladas, galerias e módulos.',
            'Quando terminar, clica em "Sair" ali em cima pra encerrar sua sessão com segurança.',
        ],
    },
    'controle_area': {
        'titulo': 'sobre o Controle de Área',
        'pose': 'explicando',
        'dicas': [
            'Em "Áreas Brutas" ficam as glebas sem parcelamento, incluindo as que estão em processo judicial.',
            '"Galerias" reúne os imóveis urbanos em galerias e condomínios.',
            'E em "Distritos" você encontra as áreas já parceladas e o cadastro de módulos por quadra.',
        ],
    },
    'cadastro': {
        'titulo': 'sobre o cadastro',
        'pose': 'prancheta_positivo',
        'dicas': [
            'Preenche os dados de localização, empresa e documentação do lote — não se preocupa, dá pra editar depois.',
            'O município é escolhido numa lista fixa com os 246 municípios de Goiás.',
            'Uma dica importante: o campo Processo SEI aceita só números, sem pontos nem barras.',
        ],
    },
    'selecionar_edicao': {
        'titulo': 'sobre a edição de cadastro',
        'pose': 'lupa',
        'dicas': [
            'Procura a empresa ou processo que você quer editar na lista, ou usa a busca.',
            'Se eu marquei um registro, é porque ele está sem atualização há mais de 1 ano — vale dar uma conferida.',
        ],
    },
    'areas_brutas': {
        'titulo': 'sobre Áreas Brutas',
        'pose': 'mapa_papel',
        'dicas': [
            'Mais abaixo tem uma seção só de "Em Processo Judicial", com os imóveis que têm processo judicial em andamento.',
            'Os valores de mercado e subsidiado ficam registrados ano a ano, de 2021 a 2024.',
            'Clica num registro que eu te mostro todos os detalhes dele.',
        ],
    },
    'distritos_regulares': {
        'titulo': 'sobre Distritos Regulares',
        'pose': 'bracos_cruzados',
        'dicas': [
            'Aqui ficam os loteamentos que já têm a regularização concluída.',
            'Usa o filtro de município se a lista estiver grande demais.',
            'Clicando em "Relatório" eu gero um PDF atualizado desse registro na hora.',
        ],
    },
    'distritos_regularizacao': {
        'titulo': 'sobre Distritos em Regularização',
        'pose': 'piscando_apontando_cima',
        'dicas': [
            'Aqui ficam os loteamentos que ainda estão em processo de regularização.',
            'Usa o filtro de município se a lista estiver grande demais.',
            'Clicando em "Relatório" eu gero um PDF atualizado desse registro na hora.',
        ],
    },
    'galerias': {
        'titulo': 'sobre Galerias / Condomínio',
        'pose': 'notebook',
        'dicas': [
            'Aqui ficam os imóveis urbanos em galerias e condomínios da CODEGO.',
            'Clica numa linha que eu abro os detalhes completos do registro pra você.',
        ],
    },
    'cadastro_modulos': {
        'titulo': 'sobre o Cadastro de Módulos',
        'pose': 'prancheta_positivo',
        'dicas': [
            'Cada linha aqui é um módulo/quadra vinculado a um distrito.',
            'Os números lá em cima mostram quantos módulos estão regulares e quantos estão irregulares.',
        ],
    },
    'relatorios': {
        'titulo': 'sobre Gerar Relatório',
        'pose': 'sentado_notebook',
        'dicas': [
            'Busca a empresa pelo nome, CNPJ, município ou processo SEI.',
            'Pode ficar tranquilo: eu gero o relatório na hora, sempre com os dados mais recentes do banco.',
        ],
    },
    'mapa_distritos': {
        'titulo': 'sobre o Mapa de Distritos',
        'pose': 'apontando_mapa',
        'dicas': [
            'Clica num distrito que eu te levo pros detalhes dele, com opção de baixar o relatório RELGEA.',
        ],
    },
    'distrito_detalhe': {
        'titulo': 'sobre este distrito',
        'pose': 'thumbs_phone',
        'dicas': [
            'Clicando em "Baixar Relatório RELGEA" eu monto um PDF com todas as empresas cadastradas nesse distrito.',
            'Se ainda não tiver nenhum registro aqui, esse relatório não vai ser gerado — é só aguardar o cadastro.',
        ],
    },
    'menu_jur': {
        'titulo': 'sobre o Módulo Jurídico',
        'pose': 'explicando',
        'dicas': [
            'Em "Adicionar Processos" você cadastra processos novos, um por um ou em lote por planilha.',
            '"Alertas de Prazos" te mostra o que já venceu, vence hoje ou está próximo.',
            'E "Consultar Assentamento" deixa você ver os dados de assentamento sem poder editá-los.',
        ],
    },
    'consulta_assentamento_jur': {
        'titulo': 'sobre a Consulta de Assentamento',
        'pose': 'lupa',
        'dicas': [
            'Essa lista é só pra consulta — o Jurídico não edita esses dados por aqui.',
            'Clica num registro que eu mostro todos os campos de assentamento daquele lote.',
        ],
    },
    'prazos_jur': {
        'titulo': 'sobre os Alertas de Prazos',
        'pose': 'piscando_apontando_cima',
        'dicas': [
            'Dá pra filtrar por situação: vencido, hoje, próximo, futuro ou sem data.',
            'Ajusta os dias de alerta se quiser que eu avise com mais ou menos antecedência.',
        ],
    },
    'relatorios_jur': {
        'titulo': 'sobre o Relatório Jurídico',
        'pose': 'sentado_notebook',
        'dicas': [
            'Você pode gerar o relatório de um processo específico, ou pedir o relatório geral com todos eles.',
        ],
    },
    'logs': {
        'titulo': 'sobre os Logs do Sistema',
        'pose': 'duvida',
        'dicas': [
            'Aqui eu mostro as últimas 1.000 ações registradas no sistema.',
            'Dá pra filtrar por usuário ou por período, se você estiver investigando alguma coisa específica.',
        ],
    },
}

POSE_PADRAO = 'aceno'


def obter_guia(pagina):
    return GUIA_CONTEUDO.get(pagina)
