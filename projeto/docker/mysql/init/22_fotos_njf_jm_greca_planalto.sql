-- Fotos adicionadas manualmente: NJF, JM Aluminios, GRECA, Planalto Blocos.
INSERT INTO empresa_infos (empresa_id, descricao, caminho_imagem) VALUES
(12, NULL, '/static/imagens_empresas/empresa12.png'),
(16, NULL, '/static/imagens_empresas/empresa16.png'),
(38, NULL, '/static/imagens_empresas/empresa38.webp'),
(47, NULL, '/static/imagens_empresas/empresa47.webp')
ON DUPLICATE KEY UPDATE
    descricao = COALESCE(empresa_infos.descricao, VALUES(descricao)),
    caminho_imagem = VALUES(caminho_imagem);
