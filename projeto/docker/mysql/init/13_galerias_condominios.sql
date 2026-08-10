SET NAMES utf8mb4;

DROP TABLE IF EXISTS `galerias_condominios`;
CREATE TABLE `galerias_condominios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `municipio_id` varchar(60) DEFAULT NULL,
  `municipio` varchar(100) DEFAULT NULL,
  `num_matricula` varchar(50) DEFAULT NULL,
  `ano_aquisicao` varchar(10) DEFAULT NULL,
  `area_total_m2` varchar(50) DEFAULT NULL,
  `valor_imovel` varchar(200) DEFAULT NULL,
  `matricula_parcelamento` varchar(100) DEFAULT NULL,
  `registro_loteamento` text,
  `ocupacao` text,
  `descricao_area` text,
  `registro_propriedade` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_galerias_condominios_municipio_id` (`municipio_id`),
  CONSTRAINT `fk_galerias_condominios_municipio` FOREIGN KEY (`municipio_id`) REFERENCES `municipio`(`municipio_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `galerias_condominios` (`municipio_id`, `municipio`, `num_matricula`, `ano_aquisicao`, `area_total_m2`, `valor_imovel`, `matricula_parcelamento`, `registro_loteamento`, `ocupacao`, `descricao_area`, `registro_propriedade`) VALUES
('5212600 - MAIRIPOTABA', 'MAIRIPOTABA', '939', '1998', '946,86', 'R$ 2.000,00', '939', 'SIM', 'TERRENO URBANO', 'LOTE 04 E 05, QUADRA 25, RUA LAFAIET BITTENCOURT', 'CODEGO'),
('5212907 - MARZAGAO', 'MARZAGAO', '671', '1996', '4.707,88', 'R$ 10.000,00', '671', 'SIM', 'TERRENO URBANO', 'QUADRA 12', 'CODEGO'),
('5220454 - SENADOR CANEDO', 'SENADOR CANEDO', '3181', '1995', '515.10''', 'R$ 1,00', '3181', 'SIM', 'TERRENO URBANO', 'RUA CARMITA REZENDE PORTO, N° 40, QD. 01 - SETOR GENOVEVA DE REZENDE MACHADO', 'CODEGO'),
('5213806 - MORRINHOS', 'MORRINHOS', '8.060''', '1989', '7.808,00', 'R$ 0,00', '8.060''', 'SIM', 'IMÓVEL - AVENIDA DOS TRABALHADORES, LOTE 01, QUADRA 101-A, SETOR AEROPORTO', 'TERRENO URBANO COM EDIFICAÇÕES', 'CODEGO');
