# app/static/ — Arquivos Estáticos

Esta pasta contém os arquivos estáticos da aplicação — imagens, logos e outros recursos servidos diretamente pelo **Nginx** em produção, sem passar pelo Gunicorn.

---

## Logos e Imagens do Sistema

| Arquivo | Descrição |
|---|---|
| `logo_codego.png` | Logo oficial da CODEGO em cores, utilizado nas telas do sistema |
| `logo_codego_grey.png` | Logo da CODEGO em cinza, utilizado como marca d'água nos relatórios PDF gerados pela aplicação (8% de opacidade, rotacionado 45°) |
| `dashboard_estatico.jpg` | Imagem de prévia do dashboard do módulo de Assentamento, exibida no menu principal |
| `dashboard_jur.jpg` | Imagem de prévia do dashboard do módulo Jurídico, exibida no menu principal |

---

## Fotos de Empresas (raiz de `/static/`)

Algumas fotos de empresas foram carregadas diretamente na raiz da pasta `/static/` em vez de `/static/imagens_empresas/`. Essas imagens são referenciadas diretamente pelos scripts SQL de seed do banco de dados.

| Arquivo | Empresa |
|---|---|
| `empresa295.jpg` | Aché Laboratórios Farmacêuticos S.A. |
| `empresa395.jpg` | Vitamedic Indústria Farmacêutica Ltda. |
| `empresa422.jpeg` | Empresa ID 422 |
| `empresa469.png` | Empresa ID 469 |
| `empresa506.png` | Granol Indústria, Comércio e Exportação S.A. |
| `empresa539.jpg` | Vitamedic Indústria Farmacêutica (unidade 539) |
| `empresa548.jpg` | Brainfarma Indústria Química e Farmacêutica S.A. |
| `empresa661.jpeg` | Empresa ID 661 |

---

## `imagens_empresas/`

Subpasta principal de fotos das empresas cadastradas no sistema. Contém mais de 100 imagens nos formatos `.jpg`, `.png`, `.webp` e `.jpeg`.

**Convenção de nomenclatura dos arquivos:**
```
empresa{id}_{slug-do-nome-da-empresa}.{ext}
```

Exemplos:
- `empresa209_brg-brasil-geraodres-eireli.jpg`
- `empresa276_geolab-industria-farmaceutica-sa.webp`
- `empresa530_kelldrin-industrial-ltda.webp`

O campo `caminho_imagem` da tabela `empresa_infos` no banco de dados referencia essas imagens com o caminho `/static/imagens_empresas/empresa{id}_{slug}.{ext}`.

> **Atenção:** Algumas empresas possuem duas versões do arquivo (`.jpg` e `.png`), resultado de importações em etapas diferentes. O banco utiliza apenas uma das versões como referência ativa.

---

## `upload`

Arquivo de marcação vazio indicando que esta pasta aceita uploads. Não tem conteúdo funcional.

---

## Como adicionar uma nova foto de empresa

1. Salve a imagem no formato `.jpg`, `.png` ou `.webp`.
2. Nomeie o arquivo seguindo a convenção: `empresa{id}_{slug-do-nome}.{ext}`.
3. Coloque o arquivo dentro de `imagens_empresas/`.
4. Atualize o campo `caminho_imagem` da empresa correspondente na tabela `empresa_infos` com o caminho `/static/imagens_empresas/{nome-do-arquivo}`.
