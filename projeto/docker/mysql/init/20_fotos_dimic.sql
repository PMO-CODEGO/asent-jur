SET NAMES utf8mb4;
INSERT INTO empresa_infos (empresa_id, caminho_imagem) VALUES
(564, '/static/empresa564.jpg'),
(571, '/static/empresa571.jpg'),
(585, '/static/empresa585.jpg'),
(586, '/static/empresa586.jpg'),
(588, '/static/empresa588.webp'),
(592, '/static/empresa592.jpg'),
(611, '/static/empresa611.png'),
(624, '/static/empresa624.jpg'),
(625, '/static/empresa625.png'),
(629, '/static/empresa629.jpg'),
(646, '/static/empresa646.png'),
(662, '/static/empresa662.jpg')
ON DUPLICATE KEY UPDATE caminho_imagem = COALESCE(empresa_infos.caminho_imagem, VALUES(caminho_imagem));
