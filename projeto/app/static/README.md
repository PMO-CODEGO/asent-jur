# app/static/ — Arquivos Estáticos

Esta pasta contém os arquivos estáticos da aplicação — imagens, logos e outros recursos servidos diretamente pelo **Nginx** em produção, sem passar pelo Gunicorn.

---

## Logos do Sistema

| Arquivo | Descrição |
|---|---|
| `logo_codego.png` | Logo oficial da CODEGO em cores, utilizado nas telas do sistema e no cabeçalho dos relatórios PDF |
| `LOGO_CODEGO (ELEITORAL)-01.png` / `-02.png` / `-03.png` | Variações do logo, não referenciadas diretamente pelo código (arquivos de material gráfico) |
| `imagens_empresas/asentjur.png` | Ícone usado como favicon (`shortcut icon`) nas páginas do sistema |

> **Nota:** a marca d'água dos relatórios PDF foi descontinuada — `app/services/pdf_service.py` ainda referencia `static/logo_codego_grey.png` e verifica sua existência antes de desenhar (`os.path.exists`), mas o arquivo foi removido de propósito, então o watermark é simplesmente omitido, sem erro.

---

## Fotos de Empresas (raiz de `/static/`)

Muitas fotos de empresas foram carregadas diretamente na raiz da pasta `/static/` (mais de 60 arquivos, no padrão `empresa{id}.{ext}`) em vez de `/static/imagens_empresas/`. Essas imagens são referenciadas diretamente pelos scripts SQL de seed do banco de dados (`docker/mysql/init/`) através do campo `caminho_imagem` da tabela `empresa_infos`. Não há uma lista fixa — para saber qual empresa corresponde a qual `id`, consulte a tabela `municipal_lots` pelo campo `id`.

---

## `imagens_empresas/`

Subpasta principal de fotos das empresas cadastradas no sistema. Contém mais de 300 imagens nos formatos `.jpg`, `.png`, `.webp`, `.jpeg` e `.svg`.

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
