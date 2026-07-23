SET NAMES utf8mb4;
INSERT INTO empresa_infos (empresa_id, caminho_imagem) VALUES
(704, '/static/empresa704.webp'),
(706, '/static/empresa706.webp'),
(708, '/static/empresa708.webp'),
(736, '/static/empresa736.webp'),
(739, '/static/empresa739.jpg'),
(740, '/static/empresa740.png'),
(743, '/static/empresa743.jpg'),
(755, '/static/empresa755.webp'),
(818, '/static/empresa818.webp')
ON DUPLICATE KEY UPDATE caminho_imagem = COALESCE(empresa_infos.caminho_imagem, VALUES(caminho_imagem));
