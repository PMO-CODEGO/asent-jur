SET NAMES utf8mb4;

DROP TABLE IF EXISTS `loteamentos_irregulares`;
CREATE TABLE `loteamentos_irregulares` (
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
  `observacoes` text,
  PRIMARY KEY (`id`),
  KEY `idx_loteamentos_irregulares_municipio_id` (`municipio_id`),
  CONSTRAINT `fk_loteamentos_irregulares_municipio` FOREIGN KEY (`municipio_id`) REFERENCES `municipio`(`municipio_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `loteamentos_irregulares` (`municipio_id`, `municipio`, `num_matricula`, `ano_aquisicao`, `area_total_m2`, `valor_imovel`, `matricula_parcelamento`, `registro_loteamento`, `ocupacao`, `descricao_area`, `registro_propriedade`, `observacoes`) VALUES
('5201108 - ANAPOLIS', 'ANAPOLIS', '470', NULL, '9.003.318,29', 'R$ 26.291.199,84', NULL, 'REGULARIZAÇÃO FUNDIÁRIA URBANA (REURB) - EM ANDAMENTO', 'DISTRITO AGROINDUSTRIAL DE ANÁPOLIS - DAIA I

(EM FASE DE REGULARIZAÇÃO URBANA FUNDIÁRIA - REURB)', 'FAZENDA BARREIRO DO MEIO, RETIRO E BARREIRO DE CIMA', 'CODEGO', 'CONFERIR ÁREA DO PERÍMETRO'),
('5201108 - ANAPOLIS', 'ANAPOLIS', '1620', '1979', NULL, 'CR$ 46.253.97', NULL, 'NÃO', NULL, 'FAZENDA BARREIRO DE CIMA', 'CODEGO', NULL),
('5201108 - ANAPOLIS', 'ANAPOLIS', '7016', '1979', NULL, 'CR$ 10.638.79', NULL, 'NÃO', NULL, 'FAZENDA BREJO GRANDE OU CABECEIRA DAS CALDAS', 'CODEGO', NULL),
('5201108 - ANAPOLIS', 'ANAPOLIS', '15157', '1982', NULL, 'CR$ 761.756,19', NULL, 'NÃO', NULL, 'BARREIRO DO MEIO', 'CODEGO', NULL),
('5201108 - ANAPOLIS', 'ANAPOLIS', '2616', '1977', NULL, 'CR$ 157.285,95', NULL, 'NÃO', NULL, 'FAZENDA OLHOS D\'ÁGUA', 'CODEGO', NULL),
('5201108 - ANAPOLIS', 'ANAPOLIS', '50306', '1978', NULL, 'CR$ 32.000,00', NULL, 'NÃO', NULL, 'FAZENDA RETIRO', 'CODEGO', NULL),
('5201108 - ANAPOLIS', 'ANAPOLIS', '60860', '2010', '245.899,11', 'R$1.900.000,00', NULL, 'NÃO', 'DISTRITO AGROINDUSTRIAL DE ANÁPOLIS NORTE - DAIA NORTE', 'FAZENDA BARREIRO DE CIMA', 'CODEGO', NULL),
('5215306 - ORIZONA', 'ORIZONA', '5188', '2004', '400.628,00', 'R$ 16.262,40', NULL, 'NÃO', 'GLEBA', 'FAZENDA SANTA BARBARA', 'CODEGO', NULL),
('5217708 - PONTALINA', 'PONTALINA', '5713', '1998', '251.700,00', 'R$ 21.684,00', NULL, 'NÃO', 'GLEBA', 'FAZENDA SÃO LOURENÇO', 'CODEGO', NULL),
('5218904 - RUBIATABA', 'RUBIATABA', '5062', '1995', '12.055,00', 'R$ 2.000,00', NULL, 'NÃO', 'GLEBA - ÁREA REMANESCENTE DA MATRICULA  5.062', 'FAZENDA SERRINHA, OLARIA E BOM JARDIM', 'CODEGO', NULL),
('5205109 - CATALAO', 'CATALAO', '4885', '1980', '1.245.224,70', 'CR$ 30.497.050,000', '8000', 'SIM', 'LOTEAMENTO SETOR SANTA CRUZ', 'FAZENDA SANTA CRUZ', 'CODEGO', 'ÁREA RESIDENCIAL LOTEADA');
