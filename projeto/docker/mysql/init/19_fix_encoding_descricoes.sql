SET NAMES utf8mb4;
-- Corrige double-encoding UTF-8 nas descricoes.
-- Ocorre quando scripts SQL sao importados sem SET NAMES utf8mb4,
-- fazendo o MySQL interpretar bytes UTF-8 como Latin1 e re-encodar como UTF-8.
-- Resultado: 'e com acento' vira 'Ã©'. Este UPDATE reverte o processo.
UPDATE empresa_infos
SET descricao = CONVERT(BINARY CONVERT(descricao USING latin1) USING utf8mb4)
WHERE descricao IS NOT NULL AND descricao != '';
