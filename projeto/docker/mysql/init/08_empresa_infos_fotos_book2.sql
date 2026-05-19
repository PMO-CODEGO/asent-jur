-- Fotos importadas de C:/Users/vivia/Downloads/fotos.
-- Preserva descricoes existentes e atualiza apenas o caminho da imagem.
INSERT INTO empresa_infos (empresa_id, descricao, caminho_imagem) VALUES
(751,NULL,'/static/imagens_empresas/empresa751_mahle-rio-verde-comercio-de-combustiveis-ltda.webp'),
(759,NULL,'/static/imagens_empresas/empresa759_comber-indastria-ltda.jpeg'),
(768,NULL,'/static/imagens_empresas/empresa768_copecar-ind-e-com-de-pecas-agriculas-ltda.jpg'),
(771,NULL,'/static/imagens_empresas/empresa771_canatec-servicos-ltda.webp'),
(774,NULL,'/static/imagens_empresas/empresa774_mmz-mecanica-industrial-ltda.webp'),
(777,NULL,'/static/imagens_empresas/empresa777_magnabosco-comercio-e-transportes-ltda.jpeg'),
(779,NULL,'/static/imagens_empresas/empresa779_pjr-empreendimentos-e-armazenagem-ltda.webp'),
(787,NULL,'/static/imagens_empresas/empresa787_videplast-centro-oeste-ltda.jpg'),
(790,NULL,'/static/imagens_empresas/empresa790_klabin-s-a.jpg')
ON DUPLICATE KEY UPDATE
    descricao = COALESCE(empresa_infos.descricao, VALUES(descricao)),
    caminho_imagem = VALUES(caminho_imagem);
