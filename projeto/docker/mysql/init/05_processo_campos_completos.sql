
CREATE TABLE IF NOT EXISTS processo_partes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id INT NOT NULL,
    papel VARCHAR(30) NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tipo_parte VARCHAR(120),
    contato VARCHAR(255),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_processo_partes
        FOREIGN KEY (processo_id)
        REFERENCES processos(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS processo_eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id INT NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    titulo VARCHAR(255),
    descricao TEXT NOT NULL,
    data_evento DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_processo_eventos
        FOREIGN KEY (processo_id)
        REFERENCES processos(id)
        ON DELETE CASCADE
);

UPDATE processos
SET titulo = COALESCE(NULLIF(titulo, ''), numero_processo),
    descricao = COALESCE(NULLIF(descricao, ''), assunto_judicial),
    tipo_acao = COALESCE(NULLIF(tipo_acao, ''), NULLIF(tipo_processo, ''), 'civel')
WHERE titulo IS NULL
   OR titulo = ''
   OR tipo_acao IS NULL
   OR tipo_acao = '';
