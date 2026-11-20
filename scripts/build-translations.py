from __future__ import annotations
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = json.loads((ROOT / "i18n/translations.json").read_text(encoding="utf-8"))
TOKEN = re.compile(
    r"<!--.*?-->|<script\b[^>]*>.*?</script\s*>|<style\b[^>]*>.*?</style\s*>|<![^>]*>|</?[^>]+>|[^<]+",
    re.IGNORECASE | re.DOTALL,
)
ATTR = re.compile(r"(?P<name>title|aria-label|alt|placeholder|content|value)(?P<eq>\s*=\s*)(?P<quote>['\"])(?P<value>.*?)(?P=quote)", re.IGNORECASE | re.DOTALL)
EXPLAIN_BLOCK = re.compile(r"(?P<start>explain\s*:\s*\{)(?P<body>.*?)(?P<end>\n\s*\})", re.DOTALL)
EXPLAIN_STRING = re.compile(r"(?m)^(?P<prefix>\s*[0-2]\s*:\s*)'(?P<value>(?:\\.|[^'\\])*)'(?P<suffix>\s*,?)$")

def norm(value: str) -> str:
    return " ".join(html.unescape(value).split())

def translate_text_node(raw: str, lang: str, mapping: dict[str, str]) -> str:
    decoded = html.unescape(raw)
    clean = norm(decoded)
    if clean not in mapping:
        return raw
    lead = re.match(r"^\s*", decoded).group(0)
    trail = re.search(r"\s*$", decoded).group(0)
    translated = lead + mapping[clean] + trail
    return html.escape(translated, quote=False)

def translate_manifest(raw: str, lang: str, mapping: dict[str, str]) -> str:
    opening = re.match(r"(?is)(<script\b[^>]*>)(.*?)(</script\s*>)", raw)
    if not opening or "data-inema-manifest" not in opening.group(1):
        return raw
    data = json.loads(opening.group(2))
    def walk(node):
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if isinstance(value, str) and value in mapping:
                    node[key] = mapping[value]
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(data)
    return opening.group(1) + "\n  " + json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\n  ") + "\n  " + opening.group(3)

def translate_inline_feedback(raw: str, mapping: dict[str, str]) -> str:
    def replace_block(block):
        def replace_string(match):
            source = match.group("value").replace("\\'", "'").replace('\\\\', '\\')
            translated = mapping.get(source)
            if translated is None:
                return match.group(0)
            if translated.startswith("Correct. "):
                translated = translated[len("Correct. "):]
            elif translated.startswith("Así es. "):
                translated = translated[len("Así es. "):]
            return match.group("prefix") + json.dumps(translated, ensure_ascii=False) + match.group("suffix")
        return block.group("start") + EXPLAIN_STRING.sub(replace_string, block.group("body")) + block.group("end")
    return EXPLAIN_BLOCK.sub(replace_block, raw)

def selector_markup(lang: str, targets: dict[str, str]) -> str:
    active_class = "font-bold text-yellow-400"
    other_class = "text-neutral-400 hover:text-neutral-100"
    selector_label = "Language" if lang == "en" else "Idioma"
    anchors = []
    for code, label in (("pt-BR", "PT"), ("en", "EN"), ("es", "ES")):
        cls = active_class if code == lang else other_class
        anchors.append(f'<a data-language="{code}" href="{targets[code]}" lang="{code}" hreflang="{code}" class="{cls}">{label}</a>')
    return '<div data-inema-language-switcher class="flex items-center gap-2 px-2 text-xs" aria-label="' + selector_label + '">' + "".join(anchors) + "</div>"

def replace_or_insert_selector(result: str, markup: str, marker: str) -> str:
    existing = re.search(r'<div\b[^>]*data-inema-language-switcher[^>]*>.*?</div>', result, re.DOTALL)
    if existing:
        return result[:existing.start()] + markup + result[existing.end():]
    if marker not in result:
        raise RuntimeError("language selector insertion point missing")
    return result.replace(marker, markup + "\n" + marker, 1)

def ensure_alternates(result: str, targets: dict[str, str]) -> str:
    for code in ("pt-BR", "en", "es"):
        result = re.sub(r'\s*<link rel="alternate" hreflang="' + re.escape(code) + r'" href="[^"]*">', "", result)
    tags = "".join(f'<link rel="alternate" hreflang="{code}" href="{targets[code]}">\n  ' for code in ("pt-BR", "en", "es"))
    return result.replace("<head>", "<head>\n  " + tags.rstrip(), 1)

def translate_document(source: str, lang: str) -> str:
    mapping = TRANSLATIONS[lang]
    output = []
    for token in TOKEN.findall(source):
        if token.lower().startswith("<script") and "data-inema-manifest" in token:
            output.append(translate_manifest(token, lang, mapping))
            continue
        if token.lower().startswith("<script"):
            token = translate_inline_feedback(token, mapping)
        if token.startswith("<") or token.startswith("<!--"):
            def replace_attr(match):
                value = html.unescape(match.group("value"))
                key = norm(value)
                translated = mapping.get(key)
                if translated is None:
                    return match.group(0)
                return match.group("name") + match.group("eq") + match.group("quote") + html.escape(translated, quote=False) + match.group("quote")
            output.append(ATTR.sub(replace_attr, token))
        else:
            output.append(translate_text_node(token, lang, mapping))
    result = "".join(output)
    result = result.replace('src="assets/img/', 'src="../assets/img/')
    result = result.replace('href="./assets/learn.css"', 'href="../assets/learn.css"')
    result = result.replace('src="./assets/learn.js"', 'src="./assets/learn.js"')
    return result

def language_links(page: str, lang: str, result: str) -> str:
    stem = "index.html" if page == "index.html" else "alerta.html"
    if lang == "en":
        p, e, s = "../" + stem, "./" + stem, "../es/" + stem
    else:
        p, e, s = "../" + stem, "../en/" + stem, "./" + stem
    selector = selector_markup(lang, {"pt-BR": p, "en": e, "es": s})
    if page == "index.html":
        marker = "          <!-- Minha jornada -->"
        return replace_or_insert_selector(result, selector, marker)
    marker = '    <button class="tgl" id="themeToggle"'
    return replace_or_insert_selector(result, selector, marker)

def course_language_links(page: str, lang: str, result: str) -> str:
    # Locale pages mirror the source path beneath en/ or es/.
    rel = Path(page).parent
    root_prefix = "../" * (len(rel.parts) + 1)
    stem = Path(page).name
    pt = root_prefix + page
    en = "./" + stem if lang == "en" else root_prefix + "en/" + page
    es = "./" + stem if lang == "es" else root_prefix + "es/" + page
    selector = selector_markup(lang, {"pt-BR": pt, "en": en, "es": es})
    marker = '          <button type="button" data-inema-journey-open'
    return replace_or_insert_selector(result, selector, marker)

def translate_runtime_js(lang: str, path: Path) -> None:
    source = (ROOT / "assets/learn.js").read_text(encoding="utf-8")
    common = {
        "'Armazenamento cheio. Exporte sua jornada para nao perder dados.'": "'Storage is full. Export your journey to avoid losing data.'",
        "'Correto. '": "'Correct. '", "'Reveja: '": "'Check again: '",
        "'Lido'": "'Read'", "'Marcar como lido'": "'Mark as read'",
        "'Curso concluido. Parabens pelo esforco.'": "'Course complete. Well done.'",
        "'Selecione dentro de um paragrafo anotavel.'": "'Select text within an annotatable paragraph.'",
        "'Selecao limitada a um paragrafo.'": "'Selection limited to one paragraph.'",
        "'Este trecho nao e anotavel.'": "'This passage cannot be annotated.'",
        "'Anotar selecao'": "'Annotate selection'", "'Adicionar nota'": "'Add note'",
        "'Copiar'": "'Copy'", "'Copiado.'": "'Copied.'",
        "'Nao foi possivel copiar.'": "'Could not copy.'",
        "'Minha jornada'": "'My journey'", "'Fechar minha jornada'": "'Close my journey'",
        "'Progresso'": "'Progress'", "'Trilha '": "'Track '", "'Modulo '": "'Module '",
        "'Curso'": "'Course'", "'Fechar'": "'Close'",
        "'Reabrir'": "'Reopen'", "'Marcar resolvida'": "'Mark resolved'",
        "'Continuar de onde parei'": "'Continue where I left off'",
        "'Voltar ao ultimo ponto'": "'Return to my last position'",
        "'Duvidas ('": "'Questions ('", "' so nao resolvidas'": "' unresolved only'",
        "'Topico: '": "'Topic: '", "'Trecho marcado'": "'Highlighted passage'",
        "'Marcar como duvida'": "'Mark as a question'", "'Marcar com cor '": "'Mark with color '",
        "'Nenhuma duvida.'": "'No questions.'", "'Notas e marcacoes ('": "'Notes and highlights ('",
        "'Cor: '": "'Color: '", "'nota sem ancora'": "'note without an anchor'",
        "'Ir ao trecho'": "'Go to passage'", "'Excluir'": "'Delete'",
        "'Nenhuma nota.'": "'No notes.'", "'Backup'": "'Backup'",
        "'Exportar .json'": "'Export .json'", "'Importar .json'": "'Import .json'",
        "'Importado: '": "'Imported: '", "' itens.'": "' items.'",
        "'Arquivo invalido. Nada foi alterado.'": "'Invalid file. Nothing was changed.'",
        "'Apagar tudo'": "'Delete everything'",
        "'Apagar TODO o progresso, duvidas e notas deste curso? Esta acao nao pode ser desfeita.'": "'Delete ALL progress, questions, and notes for this course? This cannot be undone.'",
        "'Estado do curso apagado.'": "'Course data deleted.'",
        "'Nao foi possivel exportar.'": "'Could not export.'",
        "'Substituir TODO o estado atual pelo arquivo importado? O progresso atual sera perdido.'": "'Replace ALL current data with the imported file? Current progress will be lost.'",
        "'Secao '": "'Section '", "' de '": "' of '",
        "'Modo leitura: seu progresso nao sera salvo neste navegador.'": "'Reading mode: your progress will not be saved in this browser.'",
    }
    if lang == "es":
        common = {k: v for k, v in common.items()}
        common.update({
            "'Correct. '": "'Así es. '", "'Check again: '": "'Inténtalo de nuevo: '",
            "'Storage is full. Export your journey to avoid losing data.'": "'El almacenamiento está lleno. Exporta tu recorrido para no perder datos.'",
            "'Read'": "'Leído'", "'Mark as read'": "'Marcar como leído'",
            "'Course complete. Well done.'": "'Curso completado. ¡Buen trabajo!'",
            "'Select text within an annotatable paragraph.'": "'Selecciona texto dentro de un párrafo que permita anotaciones.'",
            "'Selection limited to one paragraph.'": "'La selección se limita a un párrafo.'",
            "'This passage cannot be annotated.'": "'Este fragmento no admite anotaciones.'",
            "'Annotate selection'": "'Anotar selección'", "'Add note'": "'Añadir nota'",
            "'Copy'": "'Copiar'", "'Copied.'": "'Copiado.'", "'Could not copy.'": "'No se pudo copiar.'",
            "'My journey'": "'Mi recorrido'", "'Close my journey'": "'Cerrar mi recorrido'",
            "'Progress'": "'Progreso'", "'Track '": "'Ruta '", "'Module '": "'Módulo '",
            "'Course'": "'Curso'", "'Close'": "'Cerrar'",
            "'Reopen'": "'Reabrir'", "'Mark resolved'": "'Marcar como resuelta'",
            "'Continue where I left off'": "'Continuar donde lo dejé'", "'Return to my last position'": "'Volver al último punto'",
            "'Questions ('": "'Dudas ('", "' unresolved only'": "' solo sin resolver'",
            "'Topic: '": "'Tema: '", "'Highlighted passage'": "'Fragmento resaltado'",
            "'Mark as a question'": "'Marcar como duda'", "'Mark with color '": "'Marcar con el color '",
            "'No questions.'": "'No hay dudas.'", "'Notes and highlights ('": "'Notas y resaltados ('",
            "'Color: '": "'Color: '", "'note without an anchor'": "'nota sin anclaje'",
            "'Go to passage'": "'Ir al fragmento'", "'Delete'": "'Eliminar'", "'No notes.'": "'No hay notas.'",
            "'Export .json'": "'Exportar .json'", "'Import .json'": "'Importar .json'",
            "'Imported: '": "'Importado: '", "' items.'": "' elementos.'",
            "'Invalid file. Nothing was changed.'": "'Archivo no válido. No se modificó nada.'",
            "'Delete everything'": "'Borrar todo'",
            "'Delete ALL progress, questions, and notes for this course? This cannot be undone.'": "'¿Borrar TODO el progreso, las dudas y las notas de este curso? Esta acción no se puede deshacer.'",
            "'Course data deleted.'": "'Se borraron los datos del curso.'",
            "'Could not export.'": "'No se pudo exportar.'",
            "'Replace ALL current data with the imported file? Current progress will be lost.'": "'¿Reemplazar TODOS los datos actuales por el archivo importado? Se perderá el progreso actual.'",
            "'Section '": "'Sección '", "' of '": "' de '",
            "'Reading mode: your progress will not be saved in this browser.'": "'Modo de lectura: tu progreso no se guardará en este navegador.'",
        })
    for old, new in common.items():
        source = source.replace(old, new)
    source = source.replace("el('span', 'inema-journey__tag', 'duvida')", "el('span', 'inema-journey__tag', 'question')" if lang == "en" else "el('span', 'inema-journey__tag', 'duda')")
    source = source.replace("el('span', 'inema-journey__tag', 'duvida')", "el('span', 'inema-journey__tag', 'duda')") if lang == "es" else source
    source = source.replace("o.textContent = c; selColor.appendChild(o);", "o.textContent = swatchLabel(c); selColor.appendChild(o);")
    source = source.replace("('Marcar com cor ' + c)", "('Mark with color ' + swatchLabel(c))" if lang == "en" else "('Mark with color ' + swatchLabel(c))")
    source = source.replace("('Mark with color ' + c)", "('Mark with color ' + swatchLabel(c))" if lang == "en" else "('Marcar con el color ' + swatchLabel(c))")
    source = source.replace("('Marcar con el color ' + c)", "('Marcar con el color ' + swatchLabel(c))")
    source = source.replace("'duvida';\n        tag.setAttribute", "'question';\n        tag.setAttribute") if lang == "en" else source.replace("'duvida';\n        tag.setAttribute", "'duda';\n        tag.setAttribute")
    source = source.replace("'duvida';\n          ntag.setAttribute", "'question';\n          ntag.setAttribute") if lang == "en" else source.replace("'duvida';\n          ntag.setAttribute", "'duda';\n          ntag.setAttribute")
    swatches = {
        "en": "function swatchLabel(c) { var names = { todas: 'All', yellow: 'Yellow', green: 'Green', blue: 'Blue', pink: 'Pink', doubt: 'Question' }; return names[c] || c; }\n\n",
        "es": "function swatchLabel(c) { var names = { todas: 'Todas', yellow: 'Amarillo', green: 'Verde', blue: 'Azul', pink: 'Rosa', doubt: 'Duda' }; return names[c] || c; }\n\n",
    }
    source = source.replace("  // ===================================================================\n  // 0. CONSTANTES E ESTADO INTERNO", swatches[lang] + "  // ===================================================================\n  // 0. CONSTANTES E ESTADO INTERNO", 1)
    path.write_text(source, encoding="utf-8")

for lang in ("en", "es"):
    asset_dir = ROOT / lang / "assets"
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)
    translate_runtime_js(lang, asset_dir / "learn.js")
    for page in ("index.html", "alerta.html"):
        result = translate_document((ROOT / page).read_text(encoding="utf-8"), lang)
        result = result.replace('<html lang="pt-BR"', '<html lang="' + lang + '"', 1)
        if page == "index.html":
            result = result.replace('<meta name="inema-course" content="ia2028alerta">', '<meta name="inema-course" content="ia2028alerta-' + lang + '">', 1)
            result = result.replace('"course": "ia2028alerta"', '"course": "ia2028alerta-' + lang + '"', 1)
        result = language_links(page, lang, result)
        stem = "index.html" if page == "index.html" else "alerta.html"
        if lang == "en":
            pt, en, es = "../" + stem, "./" + stem, "../es/" + stem
        else:
            pt, en, es = "../" + stem, "../en/" + stem, "./" + stem
        result = ensure_alternates(result, {"pt-BR": pt, "en": en, "es": es})
        out = ROOT / lang / page
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result, encoding="utf-8")
        print(out.relative_to(ROOT))
    for page in (
        "curso/trilha1/index.html", "curso/trilha1/modulo-1-1.html", "curso/trilha1/modulo-1-2.html",
        "curso/trilha2/index.html", "curso/trilha2/modulo-2-1.html", "curso/trilha2/modulo-2-2.html",
        "curso/trilha3/index.html", "curso/trilha3/modulo-3-1.html", "curso/trilha3/modulo-3-2.html",
    ):
        source_path = ROOT / page
        result = translate_document(source_path.read_text(encoding="utf-8"), lang)
        image_prefix = "../../../" + source_path.parent.relative_to(ROOT).as_posix() + "/assets/img/"
        result = result.replace('src="../assets/img/', 'src="' + image_prefix)
        result = result.replace('href="../../assets/learn.css"', 'href="../../../assets/learn.css"')
        result = result.replace('<html lang="pt-BR"', '<html lang="' + lang + '"', 1)
        result = result.replace('<meta name="inema-course" content="ia2028alerta">', '<meta name="inema-course" content="ia2028alerta-' + lang + '">', 1)
        result = result.replace('"course": "ia2028alerta"', '"course": "ia2028alerta-' + lang + '"', 1)
        result = course_language_links(page, lang, result)
        rel = Path(page).parent
        root_prefix = "../" * (len(rel.parts) + 1)
        stem = Path(page).name
        pt = root_prefix + page
        en = "./" + stem if lang == "en" else root_prefix + "en/" + page
        es = "./" + stem if lang == "es" else root_prefix + "es/" + page
        result = ensure_alternates(result, {"pt-BR": pt, "en": en, "es": es})
        out = ROOT / lang / page
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result, encoding="utf-8")
        print(out.relative_to(ROOT))
