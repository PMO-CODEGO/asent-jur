-- Fotos das empresas do DAIA (Anápolis) adicionadas manualmente.
-- Preserva descrições existentes e atualiza apenas o caminho da imagem.
INSERT INTO empresa_infos (empresa_id, descricao, caminho_imagem) VALUES
(212, NULL, '/static/imagens_empresas/empresa212.jpg'),
(258, NULL, '/static/imagens_empresas/empresa258.png'),
(316, NULL, '/static/imagens_empresas/empresa316.png'),
(320, NULL, '/static/imagens_empresas/empresa320.jpg'),
(323, NULL, '/static/imagens_empresas/empresa323.jpg'),
(332, NULL, '/static/imagens_empresas/empresa332.png'),
(342, NULL, '/static/imagens_empresas/empresa342.jpg'),
(346, NULL, '/static/imagens_empresas/empresa346.jpg'),
(354, NULL, '/static/imagens_empresas/empresa354.jpg'),
(410, NULL, '/static/imagens_empresas/empresa410.jpg'),
(517, NULL, '/static/imagens_empresas/empresa517.jpg'),
(523, NULL, '/static/imagens_empresas/empresa523.png'),
(544, NULL, '/static/imagens_empresas/empresa544.jpg')
ON DUPLICATE KEY UPDATE
    descricao = COALESCE(empresa_infos.descricao, VALUES(descricao)),
    caminho_imagem = VALUES(caminho_imagem);
