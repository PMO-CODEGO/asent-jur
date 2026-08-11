SET NAMES utf8mb4;

DROP TABLE IF EXISTS `mapas_interativo_anapolis`;
CREATE TABLE `mapas_interativo_anapolis` (
  `id` int NOT NULL AUTO_INCREMENT,
  `perimetro` varchar(255) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `coordenadas` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `mapas_interativo_anapolis` (`perimetro`, `area`, `coordenadas`) VALUES
('DAIA', '9.177.570,46 m²', '-16.401813°° -48.938707°'),
('DAIANORTE', '241.960,50 m²', '-16.387689° -48.953307°'),
('DAIAPLAM', '1.793.926,90 m²', '-16.385368° -48.923811°'),
('DAIA II', '646.022,64 m²', '-16.417358° -48.919976°'),
('GLEBA 1 - ÁREAS OCUPADAS', '167.808,38 m²', '-16.406430° -48.962813°'),
('GLEBA 1 - ÁREA REMANESCENTE', '154.952,75 m²', '-16.404852° -48.965459°'),
('GLEBA 2 - ÁREA REMANESCENTE', '127.848,94 m²', '-16.406065° -48.969423°'),
('GLEBA 2 - GEOLAB', '84.067,68 m²', '-16.407778° -48.968386°'),
('ÁREA OCUPADA FORA DO DAIA', '51.462,47 m²', '-16.402817° -48.968194°');
