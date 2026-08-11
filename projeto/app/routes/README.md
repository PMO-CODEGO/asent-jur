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

### `dashboard.py` — Menu Principal e Telas de Controle de Área
Concentra as rotas de navegação e listagem do módulo de Assentamento, além do mapa de distritos industriais (compartilhado com o Jurídico).

| Rota | Método | Acesso | Descrição |
|---|---|---|---|
| `/menu/<modo>` | GET | Todos os usuários logados | Sempre renderiza `menu_jur.html`, independente do valor de `modo` (o menu do módulo de Assentamento é `inicio_assent.html`, acessado direto por `/assent/inicio`). |
| `/assent/inicio` | GET | `assent`, `admin`, `assent_gestor` | Tela inicial do módulo de Assentamento (`inicio_assent.html`), com atalhos para Controle de Área e para o módulo Jurídico. |
| `/assent/controle-area` | GET | `assent`, `admin`, `assent_gestor` | Hub (`controle_area.html`) com cards para Áreas Brutas, Galerias/Condomínio, Áreas Parceladas e Cadastro de Módulos. |
| `/assent/areas-brutas` | GET | `assent`, `admin`, `assent_gestor` | Lista os registros das tabelas `areas_brutas` e `areas_brutas_judicial`, com formatação de valores em BRL e cálculo da última avaliação por ano (`areas_brutas.html`). |
| `/assent/areas-parceladas` | GET | `assent`, `admin`, `assent_gestor` | Lista `areas_parceladas_regularizadas` e `loteamentos_irregulares` lado a lado (`areas_parceladas.html`). |
| `/assent/galerias` | GET | `assent`, `admin`, `assent_gestor` | Lista os registros de `galerias_condominios` (`galerias.html`). |
| `/assent/cadastro-modulos` | GET | `assent`, `admin`, `assent_gestor` | Lista os registros de `municipal_lots` ordenados por município/distrito/quadra/módulo (`cadastro_modulos.html`). |
| `/mapa-distritos` | GET | `assent`, `jur`, `admin`, `assent_gestor`, `jur_gestor` | Mapa dos distritos industriais/agroindustriais de Goiás administrados pela CODEGO (`mapa_distritos.html`). |
| `/mapa-distritos/<slug>` | GET | `assent`, `jur`, `admin`, `assent_gestor`, `jur_gestor` | Detalhe de um distrito específico (`distrito_detalhe.html`); os dados de cada distrito ficam hardcoded no dicionário `DISTRITOS` deste arquivo. |

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

### `areas_brutas.py` — Cadastro de Áreas Brutas
Gerencia dois "tipos" de imóvel (`FAMILIAS`: `brutas` → tabela `areas_brutas`, `judicial` → tabela `areas_brutas_judicial`), ambos com os mesmos campos (matrícula, área útil/total, reserva legal, valores de mercado/subsidiado por ano de 2021 a 2024, grupo de valor compartilhado).

| Rota | Método | Descrição |
|---|---|---|
| `/assent/areas-brutas/<familia>/nova` | GET/POST | Formulário de criação (`areas_brutas_form.html`). O select de município é populado por `municipio_service.listar_municipios()`. |
| `/assent/areas-brutas/<familia>/<id>/editar` | GET/POST | Edição de um registro existente. |
| `/assent/areas-brutas/<familia>/<id>/relatorio` | GET | Gera um PDF do registro (ReportLab). |
| `/assent/areas-brutas/<familia>/<id>/excluir` | POST | Exclui o registro. |

Registros de um mesmo `grupo` podem compartilhar um `valor_conjunto`/`moeda_conjunto` — ao salvar um registro do grupo, o valor é propagado para os demais registros do mesmo grupo na tabela (`_propagar_valor_grupo`).

---

### `areas_brutas_parceladas.py` — Cadastro de Áreas Parceladas
Gerencia três "famílias" de imóveis já loteados/parcelados, todas com o mesmo formulário (`areas_brutas_parceladas_form.html`) mas tabelas próprias:

| Família | Tabela | Campos extras |
|---|---|---|
| `regularizadas` | `areas_parceladas_regularizadas` | — |
| `galerias` | `galerias_condominios` | — |
| `irregulares` | `loteamentos_irregulares` | `observacoes` |

| Rota | Método | Descrição |
|---|---|---|
| `/assent/areas-parceladas/<familia>/nova` | GET/POST | Formulário de criação. O select de município é populado por `municipio_service.listar_municipios()`. |
| `/assent/areas-parceladas/<familia>/<id>/editar` | GET/POST | Edição de um registro existente. |
| `/assent/areas-parceladas/<familia>/<id>/excluir` | POST | Exclui o registro. |

> Como os `id` de cada família vêm de tabelas diferentes, eles podem colidir entre si — o template `areas_parceladas.html` usa `p-<familia>-<id>` como identificador único dos painéis de detalhe expansíveis para evitar conflito.

---

### `cadastro_modulos.py` — Cadastro de Módulos
CRUD simples sobre a tabela `municipal_lots`, focado nos campos de localização/módulo (município, distrito, quadra, módulo(s), quantidade, tamanho) além dos campos de status e ação judicial.

| Rota | Método | Descrição |
|---|---|---|
| `/assent/cadastro-modulos/novo` | GET/POST | Formulário de criação (`cadastro_modulos_form.html`). O select de município é populado por `municipio_service.listar_municipios()`. |
| `/assent/cadastro-modulos/<id>/editar` | GET/POST | Edição de um registro existente. |
| `/assent/cadastro-modulos/<id>/excluir` | POST | Exclui o registro. |

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

### `relatorios.py` — Relatórios em PDF (empresas, processos e RELGEA)
Gera todos os relatórios em PDF da aplicação usando ReportLab: relatórios de empresas/processos (lógica própria deste arquivo) e relatórios RELGEA a partir de `relatorio_relgea_service.py`.

Principais funcionalidades:
- Geração de relatório completo de uma empresa, incluindo dados de assentamento, processos jurídicos vinculados e foto da empresa.
- Relatório geral de todos os processos jurídicos cadastrados.
- Todos os PDFs usam cabeçalho/rodapé padronizados de `pdf_service.add_header_footer` (a marca d'água que esse helper tentava desenhar está desativada, ver [app/services/README.md](../services/README.md#pdf_servicepy--serviço-de-pdf)).

Relatórios RELGEA, gerados em memória a partir dos dados atuais do banco (`inline`, abrem direto no navegador) — ver [app/services/README.md](../services/README.md#relatorio_relgea_servicepy--serviço-de-relatórios-relgea-pdf):

| Rota | Método | Acesso | Descrição |
|---|---|---|---|
| `/relatorio-relgea/distrito/<slug>` | GET | `assent`, `jur`, `admin`, `assent_gestor`, `jur_gestor` | Gera o PDF do relatório RELGEA do distrito (todos os registros de `municipal_lots` daquele distrito, A4 paisagem). Se não houver registros, redireciona de volta para `dashboard.distrito_detalhe` com um aviso. Botão "Baixar Relatório RELGEA" em `distrito_detalhe.html`. |
| `/relatorio-relgea/individual/<familia>/<registro_id>` | GET | `assent`, `admin`, `assent_gestor` | Gera a ficha PDF de um registro de `galerias`, `regularizadas` ou `irregulares` (mesmas famílias de `areas_brutas_parceladas.py`). Botão "Relatório" nas tabelas de `galerias.html` e `areas_parceladas.html`. |

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
