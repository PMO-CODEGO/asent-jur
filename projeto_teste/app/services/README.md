# README — Pasta `services`

# Visão Geral

A pasta `services` concentra toda a lógica de negócio da aplicação. Ela funciona como a camada intermediária entre:

* Rotas (`routes`)
* Banco de dados
* Regras do sistema
* Processamento de informações
* Manipulação de arquivos
* Geração de relatórios

A arquitetura baseada em `services` permite que as regras de negócio fiquem desacopladas das rotas Flask, tornando o sistema mais:

* Organizado
* Reutilizável
* Escalável
* Testável
* Fácil de manter

---

# Estrutura da Pasta

```bash
services/
│
├── auth_service.py
├── cadastro_service.py
├── empresa_service.py
├── importacao_processos_service.py
├── juridico_schema_service.py
├── log_service.py
├── pdf_service.py
├── prazo_service.py
├── processo_busca_service.py
├── processo_documento_service.py
├── processo_historico_service.py
├── token_service.py
└── usuario_service.py
```

---

# Arquivos da Pasta `services`

## 1. `auth_service.py`

### Responsabilidade

Centraliza toda a lógica de autenticação e autorização do sistema.

### Principais Funcionalidades

* Validação de login
* Verificação de senha
* Criação de sessão
* Controle de acesso
* Verificação de permissões
* Gerenciamento de usuários autenticados

### Funcionalidades Técnicas

* Hash de senha
* Validação de credenciais
* Integração com sessão Flask
* Controle por perfil de acesso

### Dependências

* Banco de dados
* `werkzeug.security`
* `session`

### Objetivo Técnico

Garantir segurança no acesso ao sistema.

---

## 2. `cadastro_service.py`

### Responsabilidade

Gerencia as regras de negócio relacionadas aos cadastros principais do sistema.

### Principais Funcionalidades

* Cadastro de processos
* Cadastro de assentamentos
* Atualização de registros
* Persistência de dados
* Validação de informações
* Manipulação de formulários

### Funcionalidades Técnicas

* Integração com banco
* Sanitização de dados
* Conversão de campos
* Tratamento de exceções

### Dependências

* `get_db`
* Models do sistema

### Objetivo Técnico

Centralizar o núcleo operacional de cadastro da aplicação.

---

## 3. `empresa_service.py`

### Responsabilidade

Responsável pela lógica de gerenciamento de empresas vinculadas ao sistema.

### Principais Funcionalidades

* Cadastro de empresas
* Consulta de empresas
* Atualização de dados empresariais
* Relacionamento com processos

### Funcionalidades Técnicas

* Queries específicas
* Validação de dados empresariais
* Integração relacional

### Objetivo Técnico

Organizar informações empresariais associadas aos processos jurídicos.

---

## 4. `importacao_processos_service.py`

### Responsabilidade

Gerencia a importação massiva de processos.

### Principais Funcionalidades

* Importação CSV
* Leitura de planilhas
* Conversão de dados
* Validação de campos
* Inserção em lote

### Funcionalidades Técnicas

* Processamento de arquivos
* Tratamento de inconsistências
* Normalização de dados
* Controle de erros de importação

### Dependências

* `csv`
* `pandas` (quando utilizado)
* Banco de dados

### Objetivo Técnico

Automatizar inserção de grandes volumes de dados.

---

## 5. `juridico_schema_service.py`

### Responsabilidade

Responsável pela organização e transformação de dados jurídicos.

### Principais Funcionalidades

* Construção de schemas jurídicos
* Organização de informações processuais
* Conversão de dados
* Estruturação de respostas

### Funcionalidades Técnicas

* Mapeamento de campos
* Estruturação JSON
* Padronização de dados jurídicos

### Objetivo Técnico

Padronizar o formato das informações jurídicas utilizadas pelo sistema.

---

## 6. `log_service.py`

### Responsabilidade

Gerencia logs e auditoria do sistema.

### Principais Funcionalidades

* Registro de ações
* Histórico de alterações
* Auditoria de usuários
* Monitoramento operacional

### Funcionalidades Técnicas

* Registro de eventos
* Armazenamento de logs
* Captura de usuário e timestamp
* Controle de alterações

### Objetivo Técnico

Garantir rastreabilidade e segurança operacional.

---

## 7. `pdf_service.py`

### Responsabilidade

Responsável pela geração e manipulação de documentos PDF.

### Principais Funcionalidades

* Geração de relatórios
* Criação de PDFs jurídicos
* Inserção de tabelas
* Formatação visual
* Marca d’água

### Funcionalidades Técnicas

* Uso do `ReportLab`
* Manipulação de `BytesIO`
* Geração dinâmica de documentos
* Estruturação de layouts

### Dependências

* `ReportLab`
* `io.BytesIO`

### Objetivo Técnico

Centralizar toda a lógica documental do sistema.

---

## 8. `prazo_service.py`

### Responsabilidade

Gerencia cálculos e controle de prazos jurídicos.

### Principais Funcionalidades

* Controle de vencimentos
* Cálculo de prazos
* Alertas de datas
* Organização cronológica

### Funcionalidades Técnicas

* Manipulação de datas
* Regras jurídicas de prazo
* Comparações temporais

### Dependências

* `datetime`

### Objetivo Técnico

Auxiliar o setor jurídico no acompanhamento processual.

---

## 9. `processo_busca_service.py`

### Responsabilidade

Responsável pelas buscas e filtros de processos.

### Principais Funcionalidades

* Pesquisa de processos
* Filtros avançados
* Paginação
* Busca textual
* Busca por empresa
* Busca por status

### Funcionalidades Técnicas

* Queries dinâmicas
* Filtros condicionais
* Otimização de consultas

### Objetivo Técnico

Facilitar localização e organização dos processos cadastrados.

---

## 10. `processo_documento_service.py`

### Responsabilidade

Gerencia documentos relacionados aos processos.

### Principais Funcionalidades

* Upload de arquivos
* Associação de documentos
* Exclusão de documentos
* Organização documental
* Controle de nomes de arquivos

### Funcionalidades Técnicas

* Uso de `secure_filename`
* Geração de UUID
* Manipulação de diretórios
* Persistência de arquivos

### Dependências

* `os`
* `uuid`
* `werkzeug.utils`

### Objetivo Técnico

Controlar o armazenamento seguro dos documentos do sistema.

---

## 11. `processo_historico_service.py`

### Responsabilidade

Gerencia histórico e rastreamento de alterações em processos.

### Principais Funcionalidades

* Registro de alterações
* Histórico de edição
* Comparação de mudanças
* Auditoria processual

### Funcionalidades Técnicas

* Versionamento lógico
* Captura de alterações
* Registro temporal

### Objetivo Técnico

Garantir transparência nas alterações realizadas nos processos.

---

## 12. `token_service.py`

### Responsabilidade

Responsável pela criação e validação de tokens do sistema.

### Principais Funcionalidades

* Geração de tokens
* Validação de links seguros
* Recuperação de senha
* Controle de expiração

### Funcionalidades Técnicas

* Criptografia
* Tokens temporários
* Segurança de autenticação

### Objetivo Técnico

Garantir operações seguras relacionadas à autenticação.

---

## 13. `usuario_service.py`

### Responsabilidade

Gerencia informações relacionadas aos usuários do sistema.

### Principais Funcionalidades

* Cadastro de usuários
* Atualização de dados
* Controle de permissões
* Consulta de usuários
* Gerenciamento de perfis

### Funcionalidades Técnicas

* Integração com banco de dados
* Controle de roles
* Validação de dados

### Objetivo Técnico

Centralizar gerenciamento operacional dos usuários.

---

# Arquitetura Utilizada

A pasta `services` implementa o padrão:

```text
Routes → Services → Banco de Dados
```

Onde:

* `routes` recebem requisições HTTP
* `services` executam regras de negócio
* Banco de dados armazena informações

---

# Benefícios da Camada de Services

## Separação de Responsabilidades

As rotas ficam responsáveis apenas por:

* Receber requisições
* Validar entrada
* Retornar resposta

Enquanto os `services` concentram:

* Regras de negócio
* Processamentos
* Manipulação de dados

---

## Reutilização

Os mesmos serviços podem ser utilizados por:

* Rotas diferentes
* APIs
* Jobs
* Scripts internos

---

## Facilidade de Manutenção

A organização em serviços reduz:

* Código duplicado
* Complexidade nas rotas
* Acoplamento entre módulos

---

# Integração com Outras Camadas

## Comunicação com `routes`

As rotas importam serviços para executar ações.

Exemplo:

```python
from services.cadastro_service import CadastroService
```

---

## Comunicação com Banco de Dados

Os serviços normalmente:

* Executam queries
* Manipulam modelos
* Persistem alterações
* Validam consistência

---

## Comunicação com Arquivos

Alguns serviços trabalham diretamente com:

* Uploads
* PDFs
* CSVs
* Diretórios
* Arquivos temporários

---

# Controle de Segurança

Diversos serviços implementam:

* Validação de permissões
* Controle de autenticação
* Sanitização de entrada
* Proteção de arquivos
* Controle de tokens

---

# Observações Técnicas

## Organização Modular

Cada serviço possui responsabilidade específica, seguindo princípios:

* SRP (Single Responsibility Principle)
* Modularização
* Escalabilidade

---

## Processamento de Arquivos

O sistema possui suporte para:

* Uploads seguros
* Geração de relatórios
* Importação em lote
* Manipulação documental

---

## Auditoria

A aplicação mantém rastreamento através:

* Logs
* Histórico
* Controle de alterações
* Registro temporal

---

# Conclusão

A pasta `services` representa o núcleo de regras de negócio da aplicação, garantindo organização, reutilização e separação adequada entre lógica operacional e camada HTTP.

Essa arquitetura permite:

* Melhor manutenção
* Maior segurança
* Escalabilidade futura
* Reutilização de código
* Facilidade de testes
* Clareza estrutural do sistema
