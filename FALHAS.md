| 2026-09-26 | Metadados em quatro colunas alargavam módulos acima de 360 px com rótulos EN longos | Usar duas colunas no mobile e quatro a partir do breakpoint `sm` nos seis módulos | prompt |
| 2026-09-26 | Navegaçêo do curso excedia 360 px após inserir o seletor de idioma | Permitir quebra do cabeçalho sticky e alinhar controles à direita em viewport estreita | prompt |
| 2026-09-26 | Checagem dos módulos sempre classificava a opçêo correta como errada porque DOM entrega índice string e registro usa número | Comparar índices com `String(choice) === String(def.answer)` | infra |
| 2026-09-26 | Feedback de quiz nas páginas traduzidas mantinha os prefixos PT `Correto.`/`Reveja:` do runtime compartilhado | Localizar os dois prefixos em `learn.js` traduzido e evitar prefixo duplicado nas explicações inline | infra |
| 2026-09-26 | Builder montava caminho absoluto do diretório-fonte nas imagens da trilha 2 localizada | Tornar relativo ao root do projeto antes de compor `src` compartilhado | prompt |
| 2026-09-26 | Menu e painel de aparência causavam rolagem horizontal nas páginas principais PT/EN/ES | Quebrar navegaçêo no celular, alinhar popover à direita, ocultá-lo quando fechado e permitir quebra dos controles | infra |
| data | o que quebrou | menor correçêo | prompt / infra |
|---|---|---|---|
