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

### `cadastro_service.py` — Serviço de Cadastro e Validação
Classe `CadastroService` com métodos de validação e normalização de dados de formulários:

- **`normalizar_dados(form)`** — Processa o formulário de cadastro de lote, validando e convertendo cada campo (inteiros, decimais, textos com tamanho máximo, valores de listas permitidas, CNPJ).
- **`normalizar_dados_edicao(form, campos)`** — Versão parcial do normalizador para edições que afetam apenas alguns campos.
- **`normalizar_processo_juridico(form)`** — Valida e normaliza os dados de um processo jurídico (número CNJ, título, tipo de ação, status, valor da causa, recurso).
- **`normalizar_vinculos_processo(form)`** — Extrai as partes (cliente, adversa, outras) e os eventos (prazos, movimentações, documentos textuais) de um formulário de processo.
- **`extrair_data_evento(texto)`** — Tenta extrair uma data de um texto livre em formato brasileiro (DD/MM/AAAA) ou ISO (AAAA-MM-DD).

---

### `pdf_service.py` — Serviço de PDF
Função `add_watermark(canvas, doc)` usada como callback pelo ReportLab para aplicar o **logo da CODEGO como marca d'água** em todas as páginas dos relatórios gerados, com rotação de 45° e opacidade de 8%.

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
