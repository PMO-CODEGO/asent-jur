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

### `09_empresa_infos_fotos_descricoes_consolidado.sql`
Consolida em um único arquivo **12 scripts incrementais** que antes existiam separados (antigos `09_fotos_zip`, `11_descricoes_empresas`, `13_fotos_daia`, `14_descricoes_planilhas`, `15_descricoes_buscadas`, `16_fix_descricoes_vazias`, `17` a `22_fotos_*`). Cada um era um lote sucessivo de descrições/fotos de `empresa_infos` vindo de fontes diferentes (planilhas, busca na web, fotos adicionadas manualmente por distrito). Foram concatenados **na mesma ordem em que já executavam antes** (importante: as instruções `ON DUPLICATE KEY UPDATE`/`COALESCE` de cada trecho dependem de rodar depois dos trechos anteriores), sem alterar nenhuma linha de conteúdo.

> Essa consolidação foi validada comparando o resultado final da tabela `empresa_infos` (636 registros) entre um container MySQL inicializado com os 12 scripts antigos e outro com este arquivo único — o dump ficou byte a byte idêntico nos dois casos.

---

### `10_municipios.sql`
Cria a tabela de referência **`municipio`** (`municipio_id`, `ibge_id`, `municipio`, `uf`, `microrregiao`) e a popula com os **246 municípios do estado de Goiás**. É a fonte usada por `app/services/municipio_service.py` para preencher o `<select>` de município em todos os formulários de cadastro.

---

### `11_areas_brutas.sql`
Cria as tabelas do módulo de **Áreas Brutas**:
- `areas_brutas` — imóveis brutos (não parcelados) de propriedade da CODEGO, com matrícula, área útil/total, reserva legal e valores de mercado/subsidiado por ano (2021–2024).
- `areas_brutas_judicial` — mesma estrutura, para imóveis brutos com processo judicial em andamento.
- `areas_brutas_avaliacoes` / `areas_brutas_judicial_avaliacoes` — tabelas de apoio (dropadas e recriadas junto).

---

### `12_areas_parceladas_regularizadas.sql`
Cria a tabela **`areas_parceladas_regularizadas`** — glebas já parceladas (loteadas) com o loteamento regularizado.

---

### `13_galerias_condominios.sql`
Cria a tabela **`galerias_condominios`** — imóveis do tipo galeria/condomínio.

---

### `14_loteamentos_irregulares.sql`
Cria a tabela **`loteamentos_irregulares`** — glebas parceladas com o loteamento **não** regularizado. Tem um campo extra (`observacoes`) em relação às outras famílias de área parcelada.

> As tabelas `areas_parceladas_regularizadas`, `galerias_condominios` e `loteamentos_irregulares` têm auto-increment próprio e independente — o mesmo `id` pode existir em mais de uma delas. `app/routes/areas_brutas_parceladas.py` e o template `areas_parceladas.html` levam isso em conta ao gerar identificadores únicos na tela.

> **Atenção:** esses três scripts (12, 13, 14) contêm os dados de quando foram escritos — se o banco já recebeu atualizações posteriores diretamente (fora do fluxo de inicialização, como uma importação de planilha aplicada em produção), uma criação de banco **do zero** vai vir com os dados **antigos** desses scripts, não com o estado mais recente. Vale considerar atualizar o conteúdo deles quando os dados reais mudarem de forma significativa.

---

## Resumo da ordem de dependências

```
01_backup.sql              ← cria as tabelas e dados base
    └── 02_processos.sql   ← cria as tabelas do módulo jurídico
        └── 03_...         ← torna empresa_id opcional
        └── 04_...         ← migra processos legados para a nova estrutura
        └── 05_...         ← adiciona campos completos ao módulo jurídico
06, 07, 08, 09
    ← lotes sucessivos de descrições/fotos de empresa_infos (independentes entre si)
10_municipios.sql                     ← tabela de referência dos municípios de GO
11_areas_brutas.sql                   ← tabelas de áreas brutas (imóvel + judicial)
12_areas_parceladas_regularizadas.sql ← tabela de áreas parceladas regularizadas
13_galerias_condominios.sql           ← tabela de galerias/condomínio
14_loteamentos_irregulares.sql        ← tabela de loteamentos irregulares
```
