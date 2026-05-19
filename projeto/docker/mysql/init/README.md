# docker/mysql/init/ — Scripts de Inicialização do Banco de Dados

Esta pasta contém os scripts SQL executados automaticamente pelo MySQL na **primeira vez** que o container do banco de dados é criado. O MySQL processa todos os arquivos da pasta `/docker-entrypoint-initdb.d` em **ordem alfanumérica** ao inicializar um volume vazio.

> **Atenção:** Esses scripts rodam **apenas uma vez**, na criação do volume Docker. Para reaplicá-los, é necessário destruir o volume com `docker-compose down -v` e recriar o container.

---

## Arquivos e Ordem de Execução

### `01_backup.sql`
Script principal e mais extenso da pasta. Contém o **dump completo do banco de dados**, incluindo:
- Criação de todas as tabelas base: `municipal_lots` (lotes/empresas), `usuarios`, `logs` e `empresa_infos`.
- Inserção de todos os dados históricos de assentamento das empresas do DAIA (Distrito Agroindustrial de Anápolis) e demais distritos gerenciados pela CODEGO.

É o ponto de partida — sem ele, nenhum outro script funciona corretamente.

---

### `02_processos.sql`
Cria a estrutura inicial das tabelas do **módulo jurídico**:
- `processos` — tabela principal dos processos judiciais.
- `processo_partes` — partes vinculadas a cada processo (cliente, adversa, outras).
- `processo_eventos` — eventos de um processo: prazos, movimentações, documentos textuais e histórico de alterações.
- `processo_documentos` — metadados dos arquivos físicos anexados a um processo.

---

### `03_processos_independentes.sql`
Migração que torna o campo `empresa_id` da tabela `processos` opcional (`NULL`), permitindo o cadastro de **processos não vinculados** a uma empresa específica do DAIA.

---

### `04_migrar_processos_legados.sql`
Script de migração que move dados de processos judiciais que estavam armazenados diretamente nas colunas da tabela `municipal_lots` (`processo_judicial`, `status`, `assunto_judicial`, `valor_da_causa`) para a nova tabela `processos`, normalizando a estrutura do banco.

---

### `05_processo_campos_completos.sql`
Adiciona as colunas expandidas à tabela `processos`, completando o modelo de dados do módulo jurídico:
- `titulo`, `descricao`, `tipo_acao`, `tipo_processo`
- `tribunal`, `vara`, `comarca`
- `valor_da_causa`, `status`, `fase`, `data_criacao`
- `assunto_judicial`, `recurso_acionado`, `tipo_recurso`

---

### `06_empresa_infos_descricoes.sql`
Popula a tabela `empresa_infos` com as **descrições e fotos das empresas do DAIA (Anápolis)**. Os dados foram importados de uma planilha Excel (`descricao empresas.xlsx`). Utiliza `INSERT ... ON DUPLICATE KEY UPDATE` para não sobrescrever fotos já cadastradas ao ser reaplicado.

Cobre 114 empresas do Book 1 da planilha.

---

### `07_empresa_infos_descricoes_book2.sql`
Complementa o script anterior com as descrições das **empresas de Rio Verde e região** (Book 2 da planilha). Cobre 15 empresas adicionais. As fotos dessas empresas foram adicionadas em um script separado (`08`).

---

### `08_empresa_infos_fotos_book2.sql`
Atualiza o campo `caminho_imagem` das empresas do Book 2 que tiveram **fotos adicionadas posteriormente** à importação das descrições. Utiliza `ON DUPLICATE KEY UPDATE` preservando as descrições já existentes e atualizando apenas o caminho da imagem.

Cobre 9 empresas do Book 2.

---

## Resumo da ordem de dependências

```
01_backup.sql              ← cria as tabelas e dados base
    └── 02_processos.sql   ← cria as tabelas do módulo jurídico
        └── 03_...         ← torna empresa_id opcional
        └── 04_...         ← migra processos legados para a nova estrutura
        └── 05_...         ← adiciona campos completos ao módulo jurídico
06_empresa_infos_descricoes.sql       ← popula descrições e fotos (Book 1)
07_empresa_infos_descricoes_book2.sql ← popula descrições (Book 2)
08_empresa_infos_fotos_book2.sql      ← atualiza fotos (Book 2)
```
