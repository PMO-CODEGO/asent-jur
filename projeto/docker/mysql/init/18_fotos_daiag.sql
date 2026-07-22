-- Fotos de empresas do DAIAG (Aparecida de Goiania) buscadas pelos agentes de pesquisa.
-- Nao sobrescreve imagens ja existentes.
INSERT INTO empresa_infos (empresa_id, caminho_imagem) VALUES
(451, '/static/empresa451.png'),
(457, '/static/empresa457.svg'),
(463, '/static/empresa463.png'),
(464, '/static/empresa464.png'),
(529, '/static/empresa529.svg'),
(538, '/static/empresa538.png'),
(540, '/static/empresa540.svg'),
(554, '/static/empresa554.jpg'),
(555, '/static/empresa555.svg'),
(556, '/static/empresa556.png'),
(892, '/static/empresa892.svg'),
(894, '/static/empresa894.png'),
(903, '/static/empresa903.png'),
(907, '/static/empresa907.png')
ON DUPLICATE KEY UPDATE caminho_imagem = COALESCE(empresa_infos.caminho_imagem, VALUES(caminho_imagem));
