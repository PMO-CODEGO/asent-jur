SET NAMES utf8mb4;
INSERT INTO empresa_infos (empresa_id, caminho_imagem) VALUES
(679, '/static/empresa679.png'),
(891, '/static/empresa891.png')
ON DUPLICATE KEY UPDATE caminho_imagem = COALESCE(empresa_infos.caminho_imagem, VALUES(caminho_imagem));
