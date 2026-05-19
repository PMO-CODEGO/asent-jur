# app/routes/ — Rotas da Aplicação (Controllers)

Esta pasta contém os **Blueprints** do Flask — módulos que agrupam as rotas HTTP por área funcional. Cada arquivo define as URLs que a aplicação responde e delega a lógica de negócio para os serviços em `app/services/`.

> **Nota:** Já existe um README técnico gerado automaticamente nesta pasta. Este arquivo complementa e expande aquela documentação.

---

## Arquivos

### `auth_login.py` — Autenticação
Gerencia o acesso ao sistema.

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Redireciona para a tela de login |
| `/login` | GET/POST | Autentica o usuário. Em caso de sucesso, cria a sessão e redireciona conforme o perfil (role). Em caso de falha, exibe mensagem de erro. |
| `/logout` | GET | Encerra a sessão e redireciona para o login |

---

### `auth_password.py` — Recuperação de Senha
Permite ao usuário redefinir sua senha sem saber a atual.

| Rota | Método | Descrição |
|---|---|---|
| `/recuperar-senha` | GET/POST | Formulário onde o usuário informa o e-mail. Dispara um e-mail com link de redefinição válido por 15 minutos. |
| `/redefinir_senha/<token>` | GET/POST | Página de redefinição de senha. Valida o token antes de permitir a alteração. |

---

### `auth_user.py` — Cadastro de Usuários
Controla o registro de novos usuários no sistema.

| Rota | Método | Acesso | Descrição |
|---|---|---|---|
| `/registrar-usuario` | GET/POST | Público | Formulário de auto-cadastro de novos usuários |
| `/registrar-colaborador` | GET | `assent_gestor`, `jur_gestor`, `admin` | Tela para gestores cadastrarem colaboradores. O departamento é pré-definido com base na role do gestor logado. |

---

### `dashboard.py` — Menu Principal
Exibe o menu de navegação após o login.

| Rota | Método | Acesso | Descrição |
|---|---|---|---|
| `/menu/<modo>` | GET | Todos os usuários logados | Renderiza `menu_jur.html` para o módulo jurídico ou `menu.html` para o módulo de assentamento, conforme o parâmetro `modo`. |

---

### `cadastro.py` — Cadastro de Registros
O maior controller da aplicação. Gerencia o cadastro de empresas/lotes (módulo Assentamento) e de processos jurídicos (módulo Jurídico), incluindo importação em lote por planilha.

Principais funcionalidades:
- Cadastro de novos lotes/empresas na tabela `municipal_lots`.
- Cadastro de novos processos jurídicos na tabela `processos`, com partes e eventos vinculados.
- Importação de processos em lote via arquivo `.csv` ou `.xlsx`, com etapa de mapeamento de colunas.
- Upload e anexo de documentos aos processos.
- Gravação de log a cada operação.

---

### `edicao.py` — Edição de Dados
Controla a visualização e edição dos registros existentes.

Principais funcionalidades:
- Listagem de empresas do módulo Assentamento com indicadores visuais de atualização vencida (> 1 ano sem atualização).
- Edição dos campos de assentamento (setor Assentamento) e dos campos jurídicos (setor Jurídico) de cada empresa.
- Listagem, busca e paginação de processos jurídicos.
- Edição completa de processos, com registro automático de histórico de alterações.
- Anexo de documentos a processos existentes e download desses documentos.
- Exibição de detalhes de um processo jurídico, incluindo histórico, partes, prazos, movimentações e documentos.

---

### `juridico.py` — Módulo Jurídico (Consultas)
Fornece visões de leitura e monitoramento para o setor Jurídico.

| Rota | Acesso | Descrição |
|---|---|---|
| `/assentamento` ou `/jur/assentamento` | Todos os logados | Lista todos os lotes/empresas cadastrados para consulta pelo Jurídico. |
| `/assentamento/<id>` ou `/jur/assentamento/<id>` | Todos os logados | Detalhes de um lote específico, exibindo apenas os campos de assentamento (fixos). |
| `/jur/prazos` | `jur`, `jur_gestor`, `admin` | Painel de monitoramento de prazos processuais, com filtros por situação (vencido, hoje, próximo, futuro) e configuração de janela de alerta em dias. |

---

### `logs.py` — Auditoria
Exibe o histórico de ações registradas no sistema.

| Rota | Acesso | Descrição |
|---|---|---|
| `/logs` | `admin` | Tabela com os últimos 1.000 registros de auditoria. Permite filtrar por usuário e por período (data inicial / data final). |

---

### `relatorios.py` — Relatórios em PDF
Gera relatórios em formato PDF com dados de empresas e processos usando a biblioteca ReportLab.

Principais funcionalidades:
- Geração de relatório completo de uma empresa, incluindo dados de assentamento, processos jurídicos vinculados e foto da empresa.
- Relatório geral de todos os processos jurídicos cadastrados.
- Todos os PDFs gerados incluem marca d'água com o logo da CODEGO.

---

## Controle de Acesso

O controle de acesso é feito pelo decorator `@role_required(...)` definido em `app/utils/decorators.py`. Rotas sem esse decorator são públicas (como o login).

Exemplo de uso:
```python
@logs_bp.route('/logs')
@role_required('admin')
def logs():
    ...
```
