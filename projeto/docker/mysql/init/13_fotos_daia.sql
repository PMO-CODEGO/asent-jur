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

INSERT INTO empresa_infos (empresa_id, descricao, caminho_imagem) VALUES
(262, NULL, '/static/imagens_empresas/empresa262.jpg'),
(275, NULL, '/static/imagens_empresas/empresa275.jfif'),
(277, NULL, '/static/imagens_empresas/empresa277.jpg'),
(285, NULL, '/static/imagens_empresas/empresa285.webp'),
(317, NULL, '/static/imagens_empresas/empresa317.webp'),
(326, NULL, '/static/imagens_empresas/empresa326.webp'),
(347, NULL, '/static/imagens_empresas/empresa347.png'),
(368, NULL, '/static/imagens_empresas/empresa368.png'),
(374, NULL, '/static/imagens_empresas/empresa374.jfif'),
(386, NULL, '/static/imagens_empresas/empresa386.jpg'),
(391, NULL, '/static/imagens_empresas/empresa391.jpeg'),
(411, NULL, '/static/imagens_empresas/empresa411.png'),
(419, NULL, '/static/imagens_empresas/empresa419.png'),
(420, NULL, '/static/imagens_empresas/empresa420.png'),
(431, NULL, '/static/imagens_empresas/empresa431.png'),
(433, NULL, '/static/imagens_empresas/empresa433.png'),
(524, NULL, '/static/imagens_empresas/empresa524.jfif'),
(528, NULL, '/static/imagens_empresas/empresa528.jfif'),
(546, NULL, '/static/imagens_empresas/empresa546.jpeg')
ON DUPLICATE KEY UPDATE
    descricao = COALESCE(empresa_infos.descricao, VALUES(descricao)),
    caminho_imagem = VALUES(caminho_imagem);

INSERT INTO empresa_infos (empresa_id, descricao, caminho_imagem) VALUES
(254, NULL, '/static/imagens_empresas/empresa254.jfif'),
(272, NULL, '/static/imagens_empresas/empresa272.jpg'),
(278, NULL, '/static/imagens_empresas/empresa278.png'),
(279, NULL, '/static/imagens_empresas/empresa279.png'),
(288, NULL, '/static/imagens_empresas/empresa288.jfif'),
(289, NULL, '/static/imagens_empresas/empresa289.jpg'),
(294, NULL, '/static/imagens_empresas/empresa294.jpg'),
(300, NULL, '/static/imagens_empresas/empresa300.jpg'),
(311, NULL, '/static/imagens_empresas/empresa311.jpg'),
(313, NULL, '/static/imagens_empresas/empresa313.jfif'),
(327, NULL, '/static/imagens_empresas/empresa327.jpg'),
(328, NULL, '/static/imagens_empresas/empresa328.jpg'),
(349, NULL, '/static/imagens_empresas/empresa349.jpg'),
(371, NULL, '/static/imagens_empresas/empresa371.jpg'),
(373, NULL, '/static/imagens_empresas/empresa373.jpg'),
(408, NULL, '/static/imagens_empresas/empresa408.png'),
(319, NULL, '/static/imagens_empresas/empresa319.jpg'),
(428, NULL, '/static/imagens_empresas/empresa428.png'),
(429, NULL, '/static/imagens_empresas/empresa429.webp')
ON DUPLICATE KEY UPDATE
    descricao = COALESCE(empresa_infos.descricao, VALUES(descricao)),
    caminho_imagem = VALUES(caminho_imagem);
