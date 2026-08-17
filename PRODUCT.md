# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Equipe de Assentamento** (`assent`, `assent_gestor`): cadastra e mantém o portfólio de áreas de propriedade da CODEGO — áreas brutas (incluindo as em processo judicial), distritos regulares, distritos em processo de regularização, galerias/condomínios e módulos por quadra/distrito. Gestores (`assent_gestor`) têm permissões adicionais sobre a equipe.
- **Equipe Jurídica** (`jur`, `jur_gestor`): cadastra e acompanha processos judiciais vinculados aos assentamentos, monitora prazos processuais com alertas por situação (vencido, hoje, próximo, futuro), e consulta (somente leitura) os dados de assentamento.
- **Administradores** (`admin`): acesso amplo, incluindo auditoria (logs do sistema) e exclusão de registros.

## Product Purpose

Sistema interno de registro e gestão do patrimônio imobiliário da CODEGO (Companhia de Desenvolvimento Econômico de Goiás) e dos processos jurídicos vinculados a esse patrimônio, substituindo controle manual/planilhas por um sistema único com acesso por perfil e trilha de auditoria.

## Positioning

Unifica em um só sistema o que antes provavelmente estava disperso entre planilhas e processos manuais: cadastro de área (Assentamento) e acompanhamento jurídico (Jurídico) sobre os mesmos registros, com controle de acesso por perfil, geração de relatórios em PDF (individuais e RELGEA) e log de auditoria de todas as ações. *(Inferido — não confirmado explicitamente pelo usuário.)*

## Operating Context

- Cadastro e edição de registros de área (áreas brutas, distritos regulares/em regularização, galerias/condomínios, módulos), com upload de fotos de empresas e links para geo/matrícula.
- Cadastro e edição de processos jurídicos, incluindo importação em lote via planilha (.csv/.xlsx) com mapeamento de colunas.
- Geração de relatórios em PDF (ficha individual, relatório geral, relatório RELGEA por distrito) usando ReportLab.
- Painel de prazos processuais com filtro por situação e janela de alerta configurável.
- Mapa interativo (Leaflet) dos distritos industriais/agroindustriais, com filtro por município.
- Auditoria: tela de Logs (admin) com as últimas 1.000 ações, filtrável por usuário e período.
- Recuperação de senha por e-mail; autocadastro e cadastro de colaboradores por gestores.

## Capabilities and Constraints

- Stack: Flask (Python) + Jinja2 + MySQL + Docker Compose, atrás de nginx com HTTPS, deploy em VM.
- Controle de acesso por rota via decorator `@role_required(...)`.
- CSRF via Flask-WTF em todos os formulários; senhas com hash bcrypt (`flask-bcrypt`).
- Backup diário automatizado do banco (mysqldump + gzip) via container dedicado.
- Idioma único: português do Brasil. Formatação de valores em BRL, datas e documentos (CPF/CNPJ) no padrão brasileiro.
- Municípios cadastrados a partir de lista fixa dos 246 municípios de Goiás.
- Sem framework de frontend — HTML/CSS/JS servidos diretamente pelo Jinja2, com Lucide Icons e (em alguns formulários) Tailwind via CDN.
- Terminologia do domínio: "áreas brutas", "áreas parceladas/distritos", "galerias/condomínio", "loteamento regularizado/irregular", "RELGEA", "processo SEI".

## Brand Commitments

- Logo CODEGO e ícone `asentjur.png` como favicon em todas as telas.
- Cor principal `#002b5c` (azul institucional), com variações por módulo (verde para itens regulares, âmbar/vermelho para pendências/judicial).
- Fonte Inter em quase todo o sistema.
- **Codi**: mascote-personagem-guia flutuante, com 13 poses (`app/static/mascote_codego_<pose>.png`), que dá dicas contextuais em primeira pessoa por tela (conteúdo centralizado em `app/services/guia_service.py`).

## Evidence on Hand

- Codebase existente com ~25 templates já implementados e visualmente consistentes (topbar azul, cards de estatística, tabelas com painel de detalhe expansível, filtro multi-seleção por município).
- Sem dados de teste, clientes fictícios ou benchmarks a inventar — todo conteúdo vem do banco de dados real da CODEGO.

## Product Principles

1. **Ferramenta interna, não produto de mercado** — prioriza eficiência da equipe sobre apelo visual/marketing; sem necessidade de "conversão" ou storytelling de venda.
2. **Controle de acesso é parte do modelo de confiança** — cada tela e ação já nasce vinculada a um perfil (`assent`, `jur`, `admin`, gestores); mudanças de UI não devem enfraquecer essa segregação.
3. **Auditabilidade em primeiro lugar** — ações relevantes (criação, edição, exclusão) devem continuar gerando registro em log; relatórios em PDF devem ser tratados como documento oficial/auditável, não decorativo.
4. **Português e formatação brasileira sempre** — nenhuma tela, mensagem ou rótulo em outro idioma; valores monetários, datas e documentos sempre no padrão BR.
5. **Consistência visual entre telas irmãs** — telas do mesmo tipo (ex: as quatro tabelas de Controle de Área) devem manter o mesmo padrão de cards, filtro e painel de detalhe.

## Accessibility & Inclusion

Nenhum requisito de acessibilidade específico foi estabelecido até agora. *(Não confirmado — não inventar padrão WCAG específico sem validação futura.)*
