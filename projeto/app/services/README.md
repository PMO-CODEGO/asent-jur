# app/services/ — Serviços (Lógica de Negócio)

Esta pasta contém a camada de **serviços** da aplicação — módulos responsáveis pela lógica de negócio, isolada das rotas HTTP. Isso mantém os controllers (`routes/`) enxutos e facilita a manutenção e os testes.

> **Nota:** Já existe um README técnico gerado automaticamente nesta pasta. Este arquivo complementa e expande aquela documentação.

---

## Arquivos

### `auth_service.py` — Serviço de Autenticação
Classe `AuthService` com métodos estáticos para todas as operações de autenticação e gerenciamento de usuários:

- **`autenticar(username, password)`** — Busca o usuário no banco e verifica a senha com Bcrypt. Retorna o usuário se válido, ou `None`.
- **`solicitar_recuperacao_senha(email)`** — Gera um token de recuperação e envia um e-mail com o link de redefinição (válido por 15 minutos).
- **`registrar_usuario(form)`** — Valida os dados do formulário, faz o hash da senha e insere o novo usuário no banco.
- **`redefinir_senha(user_id, senha, confirmar)`** — Valida que as senhas conferem, faz o hash e atualiza no banco.
- **`criar_sessao(usuario, session)`** — Popula a sessão Flask com o `username` e a `role` mapeada a partir do departamento do usuário.
- **`redirect_por_role(role)`** — Retorna o redirecionamento correto após o login (menu Jurídico ou menu Assentamento).

**Mapeamento de departamentos para roles:**
| Departamento (banco) | Role |
|---|---|
| Administrador / admin | `admin` |
| Gestor - Jurídico | `jur_gestor` |
| Gestor - Assentamento | `assent_gestor` |
| Usuário - Jurídico | `jur` |
| Usuário - Assentamento | `assent` |

---

### `token_service.py` — Serviço de Tokens
Classe `TokenService` que usa a biblioteca `itsdangerous` para criar tokens seguros assinados com a `SECRET_KEY` da aplicação:

- **`gerar_token_recuperacao(user_id)`** — Gera um token contendo o `user_id`, assinado e com validade controlada.
- **`validar_token_recuperacao(token, max_age=900)`** — Decodifica e valida o token. Lança exceção se expirado (padrão: 900 segundos = 15 minutos) ou inválido.

---

### `email_service.py` — Serviço de E-mail
Função `enviar_email(destinatario, assunto, corpo)` que envia e-mails via SMTP usando as configurações do `config.py` (servidor Gmail, porta 587, autenticação TLS). Usada pelo `auth_service.py` para envio do link de recuperação de senha.

---

### `log_service.py` — Serviço de Auditoria
Função `gravar_log(acao, descricao, ...)` que insere um registro na tabela `logs` do banco. Captura automaticamente o usuário da sessão Flask se não for passado explicitamente. A descrição é truncada a 500 caracteres. Aceita uma conexão de banco externa (`db_conn`) para poder participar de transações maiores sem abrir uma nova conexão.

---

### `guia_service.py` — Conteúdo do Codi (personagem-guia)
Módulo puro de dados: `GUIA_CONTEUDO` é um dicionário `{chave_da_pagina: {'titulo': ..., 'pose': ..., 'dicas': [...]}}` com as falas do Codi (`pose` escolhe qual das 13 imagens `app/static/mascote_codego_<pose>.png` aparece nessa tela) — mascote da CODEGO que dá dicas contextuais (`app/templates/partials/guia_mascote.html`) — escritas na primeira pessoa em cada tela. `obter_guia(pagina)` retorna a entrada correspondente ou `None`. É registrado como função global do Jinja (`guia_dicas`) em `app/__init__.py`, para que qualquer template possa chamá-lo sem precisar que a rota passe esse dado explicitamente no `render_template`. Ver [app/templates/README.md](../templates/README.md#codi-o-personagem-guia-guia_mascotehtml) para como ligar numa tela nova.

---

### `municipio_service.py` — Serviço de Municípios
Função `listar_municipios()` que retorna a lista dos 246 municípios de Goiás cadastrados na tabela de referência `municipio` (populada em `docker/mysql/init/10_municipios.sql`), ordenada alfabeticamente. É a fonte única usada para popular o `<select>` de município em todos os formulários de cadastro (cadastro de empresa, edição, áreas brutas, áreas parceladas e cadastro de módulos).

---

### `cadastro_service.py` — Serviço de Cadastro e Validação
Classe `CadastroService` com métodos de validação e normalização de dados de formulários:

- **`normalizar_dados(form)`** — Processa o formulário de cadastro de lote, validando e convertendo cada campo (inteiros, decimais, textos com tamanho máximo, valores de listas permitidas, CNPJ).
- **`normalizar_dados_edicao(form, campos)`** — Versão parcial do normalizador para edições que afetam apenas alguns campos.
- **`normalizar_processo_juridico(form)`** — Valida e normaliza os dados de um processo jurídico (número CNJ, título, tipo de ação, status, valor da causa, recurso).
- **`normalizar_vinculos_processo(form)`** — Extrai as partes (cliente, adversa, outras) e os eventos (prazos, movimentações, documentos textuais) de um formulário de processo.
- **`extrair_data_evento(texto)`** — Tenta extrair uma data de um texto livre em formato brasileiro (DD/MM/AAAA) ou ISO (AAAA-MM-DD).

---

### `relatorio_relgea_service.py` — Serviço de Relatórios RELGEA (PDF)
Gera, sob demanda e com os dados atuais do banco, os relatórios em PDF no padrão RELGEA exigido pelo manual de controle de informação documentada (`MANSUGEQMANUALDECONTROLEDEINFORMACAODOCUMENTADAREV000`). Usa ReportLab (mesma biblioteca de `pdf_service.py`, reaproveitando `bloco_identificacao` e `linha_assinatura` para manter cabeçalho/rodapé/identificação ISO 9001 consistentes com os demais PDFs do sistema, mas com `pagina_relgea` como callback de página em vez de `add_header_footer` puro — ver abaixo). Os arquivos são gerados inteiramente em memória (`io.BytesIO`) e devolvidos diretamente na resposta HTTP — nada é salvo em disco.

Dois formatos de relatório:
- **Relatório de distrito** — `gerar_relatorio_distrito_pdf(db, distrito_db, emitido_por)`. Tabela (A4 paisagem, fonte Arial 10) com todos os registros de `municipal_lots` daquele distrito — colunas objetivas (código, quadra, status, valores) centralizadas e descritivas (empresa, ação judicial, irregularidades) à esquerda, conforme seção 6.1-III do manual. Linhas sem empresa cadastrada ("área disponível") aparecem destacadas em verde. Retorna `(None, None, 0)` se não houver registros. O mapeamento slug → valor da coluna `distrito` fica em `DISTRITO_DB_MAP` (os slugs são os mesmos usados em `dashboard.DISTRITOS`).
- **Ficha individual** — `gerar_relatorio_individual_pdf(familia, registro, emitido_por)`, para um único registro de `galerias_condominios`, `areas_parceladas_regularizadas` ou `loteamentos_irregulares`. Tabela de campo/valor (A4 retrato, fonte Arial 10).

Conformidade com o manual (seção 11 — Identificação dos Documentos):
- Código do documento segue `[TIPO]-[ÁREA]-[NOME]-[REVxxx]` (seção 11.1) usando a sigla oficial da área no Anexo D do manual: **GEAS-18820** (Gerência de Assentamento) — os códigos e nomes de arquivo usam `RELGEAS...`, não `RELGEA...` (a sigla `GEA` não existe na Ficha de Siglas do manual).
- `bloco_identificacao`/`linha_assinatura` recebem `unidade_responsavel='GEAS - GERÊNCIA DE ASSENTAMENTO'`, `controle='SUGEQ'`, `revisado_por='A definir'` e `aprovado_por='A definir'` — como esses relatórios são gerados sob demanda, sem um fluxo de revisão/aprovação humana de fato, "A definir" é mais honesto do que fabricar um responsável.
- Cada relatório recebe um título principal centralizado, negrito, tamanho 14 (seção 6.1-IV), além do campo "Título do Documento" já existente no bloco de identificação.

Como os relatórios são gerados sob demanda e não passam pela Lista Mestra da SUGEQ (não ficam sincronizados com revisões futuras), cada página recebe o carimbo diagonal "CÓPIA NÃO CONTROLADA — Válida apenas na data de emissão" exigido pela seção 7.4 do manual (`pdf_service.carimbo_copia_nao_controlada`, combinado com o cabeçalho/rodapé padrão via `pdf_service.pagina_relgea`).

Como os números de processo SEI reais (~15 dígitos) não cabem na antiga coluna `processo_sei` (`INT`, estourada silenciosamente pelo MySQL para `2147483647`), a coluna foi migrada para `varchar(50)` (não faz sentido tratar um identificador como número: além do limite, um `int`/`bigint` também derruba zeros à esquerda). `_clean_processo` ainda descarta o valor sentinela `2147483647` (ou `'0'`) para os ~649 registros cujo número original já havia sido perdido antes da correção e não pôde ser recuperado — a correção evita truncamento em cadastros novos, mas não recupera dados já sobrescritos.

> Limitação conhecida: a tabela do relatório de distrito tem 14 colunas: em Arial 10 (exigido pelo manual) ela não caberia em A4 paisagem sem quebra de linha pesada nas colunas de texto mais largas (Empresa, Ação Judicial, Irregularidades) — o relatório do DAIA (232 registros), por exemplo, passa de ~14 para ~28 páginas em relação a uma versão com fonte reduzida. Optou-se por manter a fonte 10 (conformidade literal com a seção 6.1) em vez de encolher o texto para caber em menos páginas.

---

### `pdf_service.py` — Serviço de PDF
Funções usadas como callback/helpers pelo ReportLab para padronizar os relatórios em PDF (cabeçalho, rodapé e blocos no estilo ISO 9001):

- **Fonte Arial** — o MANSUGEQ (seção 6.1-I) exige fonte Arial em todo documento institucional. O ReportLab só embute nativamente as fontes base-14 (Helvetica etc.), então os arquivos `arial.ttf`/`arialbd.ttf`/`ariali.ttf`/`arialbi.ttf` foram copiados para `app/resources/fonts/` e são registrados no import do módulo via `reportlab.pdfbase.pdfmetrics`. As constantes `FONTE_REGULAR`/`FONTE_NEGRITO` resolvem para `'Arial'`/`'Arial-Bold'` quando o registro funciona, com fallback silencioso para `'Helvetica'`/`'Helvetica-Bold'` (metricamente equivalente) caso os arquivos não estejam presentes em algum ambiente.
- **`add_header_footer(canvas, doc)`** — desenha o cabeçalho azul com o logo da CODEGO, código/revisão/emissão do documento, o rodapé com número de página, e tenta desenhar uma marca d'água em cinza rotacionada 45° a partir de `static/logo_codego_grey.png`. Como esse arquivo não existe mais na pasta `static/`, a marca d'água é silenciosamente omitida (a checagem é feita via `os.path.exists`) — o restante do cabeçalho/rodapé funciona normalmente. Lê o tamanho da página de `doc.pagesize` (em vez de assumir A4 retrato fixo) para funcionar também em relatórios A4 paisagem, como o de distrito do RELGEA.
- **`bloco_identificacao(story, ..., unidade_responsavel=None, revisado_por=None, controle=None, aprovado_por='GESTÃO CODEGO')`** — insere a tabela de identificação do documento (título, código, revisão, emitido por, aprovado por) no topo do PDF. Os três parâmetros novos são opcionais e só adicionam linhas à tabela quando informados, para não alterar a aparência dos PDFs que já usavam esta função (relatórios de empresa/processo em `relatorios.py`) antes desses campos existirem.
- **`linha_assinatura(story, emitido_por, styles_map, revisado_por=None, aprovado_por='GESTÃO CODEGO')`** — insere a tabela de assinatura ao final do PDF. Vira 3 colunas (Elaborado/Revisado/Aprovado) quando `revisado_por` é informado; senão mantém as 2 colunas originais.
- **`carimbo_copia_nao_controlada(canvas, doc)`** / **`pagina_relgea(canvas, doc)`** — carimbo diagonal "CÓPIA NÃO CONTROLADA" (seção 7.4 do manual) e o callback combinado (cabeçalho/rodapé + carimbo) usado pelos relatórios RELGEA.
- **`add_watermark(canvas, doc)`** — apenas um alias de `add_header_footer`, mantido no código por compatibilidade legada; não é chamado em nenhuma rota atualmente.

---

### `prazo_service.py` — Serviço de Prazos Jurídicos
Responsável por buscar, classificar e filtrar os prazos processuais:

- **`extrair_data_prazo(*valores)`** — Tenta extrair uma data de múltiplas fontes (campo de data, título ou descrição do evento), suportando formatos BR e ISO.
- **`classificar_prazo(data_prazo, hoje, dias_alerta)`** — Classifica um prazo em: `vencido`, `hoje`, `proximo`, `futuro` ou `sem_data`.
- **`buscar_prazos_juridicos(cursor, dias_alerta)`** — Busca todos os eventos do tipo `prazo` no banco, classifica cada um e retorna a lista ordenada junto com um resumo por situação.
- **`filtrar_prazos(prazos, filtro)`** — Filtra a lista de prazos por situação (`alertas`, `vencido`, `hoje`, `proximo`, `futuro`, `sem_data`, `todos`).

---

### `juridico_schema_service.py` — Serviço de Esquema do Banco
Função `garantir_schema_juridico(db)` que cria ou migra as tabelas do módulo jurídico de forma segura (**idempotente** — pode ser chamada múltiplas vezes sem efeito colateral). É chamada em tempo de execução antes de operações que dependem dessas tabelas.

Tabelas gerenciadas:
| Tabela | Descrição |
|---|---|
| `processos` | Processos jurídicos principais |
| `processo_partes` | Partes vinculadas a um processo (cliente, adversa, outras) |
| `processo_eventos` | Eventos de um processo: prazos, movimentações, documentos textuais e histórico |
| `processo_documentos` | Arquivos físicos anexados a um processo |

---

### `processo_busca_service.py` — Serviço de Busca de Processos
Funções para busca e contagem de processos jurídicos com suporte a busca textual ampla:

- **`buscar_processos_juridicos(cursor, termo_busca, limite, offset)`** — Retorna processos com suporte a busca em múltiplos campos (número CNJ, título, partes, eventos) e paginação.
- **`contar_processos_juridicos(cursor, termo_busca)`** — Retorna o total de processos que atendem ao filtro (usado para calcular paginação).

A busca por número CNJ também funciona digitando apenas os dígitos, sem pontuação.

---

### `processo_historico_service.py` — Serviço de Histórico de Processos
Módulo que registra e formata o histórico de alterações de processos jurídicos:

- **`registrar_historico_processo(cursor, processo_id, titulo, descricao)`** — Insere um evento do tipo `historico` no processo.
- **`montar_alteracoes_processo(...)`** — Compara o estado antigo e novo de um processo (incluindo partes e eventos) e retorna uma lista de strings descrevendo cada alteração detectada.
- Funções auxiliares para gerar descrições padronizadas de histórico: `historico_criacao_manual`, `historico_importacao`, `historico_importacao_duplicada`, `historico_documento_anexado`, `historico_edicao`.

---

### `processo_documento_service.py` — Serviço de Documentos
Função `salvar_documento_processo(cursor, processo_id, arquivo, form)` que:
1. Valida a extensão do arquivo (aceita: `pdf`, `png`, `jpg`, `jpeg`, `gif`, `webp`, `docx`).
2. Gera um nome único com UUID para evitar conflitos.
3. Salva o arquivo em `app/uploads/processos/`.
4. Registra os metadados do documento na tabela `processo_documentos`.

---

### `importacao_processos_service.py` — Serviço de Importação de Planilhas
O serviço mais complexo da aplicação. Responsável por importar processos jurídicos em lote a partir de arquivos `.csv` ou `.xlsx`:

- Detecta o delimitador do CSV automaticamente (`;` ou `,`).
- Localiza a linha de cabeçalho automaticamente (procura a coluna de número CNJ nas primeiras 30 linhas).
- **`identificar_coluna(coluna)`** — Normaliza e mapeia o nome de uma coluna da planilha para o campo interno correspondente, com suporte a mais de 50 variações de nomes de colunas comuns em sistemas jurídicos.
- **`preparar_processos_importacao(arquivo, mapeamento_colunas)`** — Orquestra a leitura, mapeamento e validação completa, retornando a lista de processos prontos para inserção e a lista de erros por linha.
- Suporte a mapeamento manual de colunas pelo usuário antes da importação final.
