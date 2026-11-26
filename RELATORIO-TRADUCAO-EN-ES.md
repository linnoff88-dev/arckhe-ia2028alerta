# Relatório de traduçêo EN/ES — Alerta IA 2028

A versêo em inglês e espanhol foi concluída para as superfícies públicas do projeto. O texto foi traduzido por agentes configurados como GPT-6 Luna pela assinatura e aplicado a partir de um catálogo local, sem API de traduçêo.

## Cobertura

| Superfície PT | Unidades de texto | EN | ES |
|---|---:|---:|---:|
| `index.html` | 163 | 163/163 | 163/163 |
| `alerta.html` | 173 | 173/173 | 173/173 |
| `curso/trilha1/index.html` | 151 | 151/151 | 151/151 |
| `curso/trilha1/modulo-1-1.html` | 234 | 234/234 | 234/234 |
| `curso/trilha1/modulo-1-2.html` | 210 | 210/210 | 210/210 |
| `curso/trilha2/index.html` | 161 | 161/161 | 161/161 |
| `curso/trilha2/modulo-2-1.html` | 223 | 223/223 | 223/223 |
| `curso/trilha2/modulo-2-2.html` | 236 | 236/236 | 236/236 |
| `curso/trilha3/index.html` | 153 | 153/153 | 153/153 |
| `curso/trilha3/modulo-3-1.html` | 286 | 286/286 | 286/286 |
| `curso/trilha3/modulo-3-2.html` | 304 | 304/304 | 304/304 |
| **Total por idioma** | **2.294** | **2.294/2.294** | **2.294/2.294** |

Também estêo traduzidos os 18 feedbacks inline dos quizzes (`ARCKHÉ.registerCheck`, três alternativas por cada um dos seis módulos). Os três READMEs têm navegaçêo para PT/EN/ES: `README.md`, `README.en.md` e `README.es.md`.

## Arquivos e funcionamento

- Páginas EN: `en/index.html`, `en/alerta.html` e `en/curso/trilha1..3/`.
- Páginas ES: `es/index.html`, `es/alerta.html` e `es/curso/trilha1..3/`.
- Catálogo persistente: `i18n/translations.json`; inventário das unidades-fonte: `i18n/source-runs.json`.
- Gerador local: `scripts/build-translations.py`. Ele recria as cópias, seletores, alternates e `assets/learn.js` por idioma; nêo usa serviços externos de traduçêo.
- CSS e imagens apontam para os assets originais compartilhados. IDs, IDs dos módulos e tópicos, comandos, URLs externas e estrutura do manifesto foram preservados.
- O armazenamento do curso usa `ia2028alerta-en` e `ia2028alerta-es` nas páginas localizadas, incluindo `meta[name="ARCKHÉ-course"]` e `manifest.course`. Preferências visuais continuam compartilhadas.

## Verificações realizadas

- Builder executado repetidamente; a saída manteve um seletor e três `hreflang` por página.
- Auditoria local: 22 páginas EN/ES, 2.294 unidades mapeadas por idioma, IDs iguais às fontes, links locais existentes e IDs de armazenamento corretos.
- `python3 -m py_compile scripts/build-translations.py` e `node --check` nos runtimes PT/EN/ES.
- Playwright no servidor local: respostas certa e errada nos seis quizzes em EN e ES (12 páginas × dois casos); progresso de leitura persistiu após reload e permaneceu separado por idioma.
- Playwright responsivo nas 22 páginas localizadas em 360 px e 1440 px: sem rolagem horizontal, imagens locais quebradas ou erros de página.

Os problemas reais encontrados durante a validaçêo foram registrados e corrigidos em `FALHAS.md`. Revisêo independente adicional: 33 páginas PT/EN/ES em 360 e 1440 px passaram sem erros, imagens quebradas ou rolagem horizontal. A publicaçêo segue via git.
