# app/utils/ — Utilitários

Esta pasta contém módulos auxiliares reutilizáveis por qualquer parte da aplicação.

---

## Arquivos

### `decorators.py` — Decorators de Controle de Acesso

Define o decorator `@role_required(*roles_permitidas)` usado para proteger rotas que exigem autenticação ou perfil específico.

**Funcionamento:**
1. Verifica se o usuário está logado (existe `username` na sessão). Se não, redireciona para o login com aviso.
2. Verifica se a `role` do usuário está na lista de roles permitidas para aquela rota. Se não, retorna erro `403 Acesso negado`.
3. Se tudo estiver ok, executa a função da rota normalmente.

**Exemplo de uso:**
```python
@minha_rota_bp.route('/admin/area')
@role_required('admin', 'assent_gestor')
def area_restrita():
    ...
```

**Roles disponíveis no sistema:**

| Role | Descrição |
|---|---|
| `admin` | Administrador — acesso total |
| `assent_gestor` | Gestor do módulo de Assentamento |
| `jur_gestor` | Gestor do módulo Jurídico |
| `assent` | Usuário do módulo de Assentamento |
| `jur` | Usuário do módulo Jurídico |

---

### `security.py` — Segurança

Arquivo reservado para utilitários de segurança adicionais. Atualmente vazio — funções como sanitização de inputs, validação de headers ou outros controles de segurança podem ser implementados aqui conforme necessidade.
