CREATE TABLE IF NOT EXISTS processos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NULL,
    numero_processo VARCHAR(120) NOT NULL,
    titulo VARCHAR(255),
    descricao TEXT,
    tipo_acao VARCHAR(120),
    tipo_processo VARCHAR(100),
    tribunal VARCHAR(120),
    vara VARCHAR(120),
    comarca VARCHAR(120),
    valor_da_causa DECIMAL(15, 2),
    status VARCHAR(100),
    fase VARCHAR(120),
    data_criacao DATE,
    assunto_judicial TEXT,
    recurso_acionado BOOLEAN DEFAULT FALSE,
    tipo_recurso VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX idx_numero_processo
ON processos(numero_processo);

CREATE INDEX idx_processo_partes_processo
ON processo_partes(processo_id);

CREATE INDEX idx_processo_eventos_processo
ON processo_eventos(processo_id);

