-- Fotos de empresas do DAIA (Anápolis) buscadas pelos agentes de pesquisa.
-- Nao sobrescreve imagens ja existentes.
INSERT INTO empresa_infos (empresa_id, caminho_imagem) VALUES
(312, '/static/empresa312.webp'),
(315, '/static/empresa315.png'),
(329, '/static/empresa329.png'),
(337, '/static/empresa337.png'),
(340, '/static/empresa340.png'),
(355, '/static/empresa355.jpg'),
(358, '/static/empresa358.webp'),
(369, '/static/empresa369.png'),
(375, '/static/empresa375.webp'),
(377, '/static/empresa377.png'),
(378, '/static/empresa378.png'),
(382, '/static/empresa382.png'),
(385, '/static/empresa385.png'),
(397, '/static/empresa397.png'),
(407, '/static/empresa407.png'),
(413, '/static/empresa413.png'),
(415, '/static/empresa415.jpg'),
(435, '/static/empresa435.webp'),
(449, '/static/empresa449.png')
ON DUPLICATE KEY UPDATE caminho_imagem = COALESCE(empresa_infos.caminho_imagem, VALUES(caminho_imagem));
