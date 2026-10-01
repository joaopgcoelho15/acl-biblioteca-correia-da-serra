import math
import json
import os
import re
import unicodedata
from datetime import datetime
from urllib.parse import urlencode

import numpy as np
import pandas as pd
from flask import Flask, abort, render_template, request, send_file, url_for
from markupsafe import Markup, escape


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCEL_PATH = os.path.join(ROOT_DIR, "database.xlsx")
WORK_IMAGES_MANIFEST = os.path.join(ROOT_DIR, "website", "static", "obras", "manifest.json")
PER_PAGE = 15

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, "templates"),
    static_folder=os.path.join(ROOT_DIR, "website"),
    static_url_path="/assets",
)


class PrefixMiddleware:
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix.rstrip("/")

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith(self.prefix):
            environ["SCRIPT_NAME"] = self.prefix
            environ["PATH_INFO"] = path[len(self.prefix) :] or "/"
            return self.app(environ, start_response)

        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b"Not Found"]


URL_PREFIX = os.environ.get("URL_PREFIX", "").strip()
if URL_PREFIX:
    if not URL_PREFIX.startswith("/"):
        URL_PREFIX = f"/{URL_PREFIX}"
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, URL_PREFIX)


FILTERS = [
    {"param": "classification", "field": "classification", "label_key": "topics"},
    {"param": "lingua", "field": "lingua", "label_key": "language"},
    {"param": "author", "field": "author", "label_key": "author"},
    {"param": "editor_name", "field": "editor_name", "label_key": "editor_name"},
    {"param": "tradutor", "field": "tradutor", "label_key": "translator"},
    {"param": "editor", "field": "editor", "label_key": "printer"},
    {"param": "local_atual", "field": "local(atual)", "label_key": "place"},
    {"param": "date", "field": "date", "label_key": "date"},
]

SORT_OPTIONS = [
    {"value": "date_asc", "label_pt": "Data ascendente", "label_en": "Date ascending"},
    {"value": "date_desc", "label_pt": "Data descendente", "label_en": "Date descending"},
    {"value": "title_asc", "label_pt": "Título (A-Z)", "label_en": "Title (A-Z)"},
    {"value": "title_desc", "label_pt": "Título (Z-A)", "label_en": "Title (Z-A)"},
    {"value": "author_asc", "label_pt": "Autor (A-Z)", "label_en": "Author (A-Z)"},
    {"value": "author_desc", "label_pt": "Autor (Z-A)", "label_en": "Author (Z-A)"},
]

TEXT = {
    "pt": {
        "home": "Início",
        "about": "Sobre",
        "catalog": "Catálogo",
        "research": "Equipa",
        "publications": "Publicações",
        "contacts": "Contactos",
        "language_switch": "ENG",
        "all": "(todos)",
        "apply": "Aplicar",
        "clear": "Limpar",
        "filters": "Filtros",
        "sort_by": "Organizar por:",
        "results": "resultados",
        "search_placeholder": "pesquisar por palavras",
        "free_search": "Pesquisa livre",
        "no_image": "(sem imagem)",
        "missing_value": "sem valor",
        "unknown_author": "autor desconhecido",
        "image_source_prefix": "Imagem obtida de",
        "image_source_missing": "(url da imagem não disponível)",
        "original_catalog_image": "Registo original no catálogo",
        "database_record_note": "registo {record_id} na base de dados",
        "back_to_catalog": "Voltar ao catálogo",
        "work_image": "Imagem da obra",
        "access": "Acesso",
        "original_transcription": "Transcrição original",
        "title_label": "Título",
        "author": "Autor",
        "editor_name": "Editor",
        "translator": "Tradutor",
        "printer": "Impressor",
        "place": "Local",
        "original_place": "Local no original",
        "current_place": "Local atual",
        "date": "Data",
        "volumes": "Tomos",
        "language": "Idioma",
        "topics": "Temas",
        "shelf": "Prateleira",
        "notes": "Notas",
        "catalog_record_number": "Número de registo no catálogo",
        "status": "Estado",
        "record": "Registo",
        "no_records": "Não existem registos para estes filtros.",
        "pagination": "Paginação",
        "previous": "Anterior",
        "next": "Seguinte",
        "page_of": "Página {page} de {total_pages}",
        "catalog_record_alt": "Registo no catálogo {catalog_number}",
        "advanced_search": "Pesquisa avançada",
        "browse_by": "Pesquisar por:",
        "library_intro_body": [
            "A Biblioteca Digital Correia da Serra foi construída a partir do catálogo manuscrito das 1869 obras que constavam da biblioteca que José Correia da Serra formou nas últimas décadas do século XVIII. Não sendo possível recuperar a biblioteca na sua forma física, procede-se à sua preservação em formato digital através de ligações externas que permitem aceder às obras que Correia da Serra reuniu.",
            "A Biblioteca Digital Correia da Serra possibilita a identificação bibliográfica completa das obras que a integram, assim como a obtenção de resultados de pesquisa simples ou avançada pelos diversos campos de informação que constam dos respetivos registos.",
        ],
    },
    "en": {
        "home": "Home",
        "about": "About",
        "catalog": "Catalogue",
        "research": "Team",
        "publications": "Publications",
        "contacts": "Contacts",
        "language_switch": "PT",
        "all": "(all)",
        "apply": "Apply",
        "clear": "Clear",
        "filters": "Filters",
        "sort_by": "Sort by:",
        "results": "results",
        "search_placeholder": "search by words",
        "free_search": "Free-text search",
        "no_image": "(no image)",
        "missing_value": "no value",
        "unknown_author": "unknown author",
        "image_source_prefix": "Image obtained from",
        "image_source_missing": "(image url unavailable)",
        "original_catalog_image": "Original catalogue record",
        "database_record_note": "record {record_id} in the database",
        "back_to_catalog": "Back to the catalogue",
        "work_image": "Work image",
        "access": "Access",
        "original_transcription": "Original transcription",
        "title_label": "Title",
        "author": "Author",
        "editor_name": "Editor",
        "translator": "Translator",
        "printer": "Printer",
        "place": "Place",
        "original_place": "Original place",
        "current_place": "Current place",
        "date": "Date",
        "volumes": "Volumes",
        "language": "Language",
        "topics": "Topics",
        "shelf": "Shelf",
        "notes": "Notes",
        "catalog_record_number": "Catalogue record number",
        "status": "Status",
        "record": "Record",
        "no_records": "No records match these filters.",
        "pagination": "Pagination",
        "previous": "Previous",
        "next": "Next",
        "page_of": "Page {page} of {total_pages}",
        "catalog_record_alt": "Catalogue record {catalog_number}",
        "advanced_search": "Advanced search",
        "browse_by": "Browse by:",
        "library_intro_body": [
            "The Correia da Serra Digital Library was built from the handwritten catalogue of the 1,869 works held in the library that José Correia da Serra assembled during the final decades of the eighteenth century. Since the library cannot be recovered in its physical form, it is preserved digitally through external links that provide access to the works collected by Correia da Serra.",
            "The Correia da Serra Digital Library provides full bibliographic identification of its works and supports simple or advanced searches across the information fields in their records.",
        ],
    },
}

CONTENT_PAGES = {
    "sobre": {
        "endpoint": "about",
        "title_pt": "Sobre",
        "title_en": "About",
        "layout": "image_left",
        "image": "static/page-about.png",
        "sections": [
            {
                "paragraphs_pt": [
                    "A Biblioteca Digital de Correia da Serra permite compreender e aprofundar as escolhas de leitura e estudo de um dos fundadores da Academia das Ciências de Lisboa e um dos mais notáveis cientistas portugueses de todos os tempos. Procura servir como instrumento de trabalho no âmbito das humanidades digitais, com destaque para a história do livro e da leitura, a história das ideias e a história da ciência.",
                ],
                "paragraphs_en": [
                    "The Correia da Serra Digital Library offers insight into the reading and study choices of one of the founders of the Lisbon Academy of Sciences and one of the most notable Portuguese scientists of all time. It is intended as a research tool for the digital humanities, particularly the history of books and reading, the history of ideas and the history of science.",
                ],
            },
            {
                "heading_pt": "Saiba mais sobre a vida e obra de Correia da Serra",
                "heading_en": "Learn more about the life and work of Correia da Serra",
                "items": [
                    {"text": "Cardoso, José Luís. As origens do programa científico de Correia da Serra: uma visão inspiradora. Lisboa: Academia das Ciências de Lisboa, 2024.", "url": "https://doi.org/10.58164/11b9-ne74"},
                    {"text": "Cardoso, José Luís. Correia da Serra: the formation of an enlightened scientist. Gavea Brown, Vol. L, nº 1, 2025.", "url": "https://repository.library.brown.edu/studio/item/bdr:4k4qz42b/"},
                    {"text": "Cardoso, José Luís. José Francisco Correia da Serra, in: Dicionário Histórico-Biográfico da Academia das Ciências de Lisboa, 2025.", "url": "https://dhb.acad-ciencias.pt/entrada/?id=JoseFranciscoCorreiadaSerra"},
                    {"text": "Davis, Richard Beale. O Abade Correia da Serra na América, 1812–1820. Lisboa: Imprensa de Ciências Sociais, 2013 (1.ª ed. Americana: 1955)."},
                    {"text": "Simões, Ana, Diogo, Maria Paula e Carneiro, Ana. Cidadão do Mundo. Uma biografia científica do Abade Correia da Serra. Porto: Porto Editora, 2006."},
                    {"text": "Teague, Michael. Abade José Correia da Serra. Documentos do seu Arquivo (1751-1795). Catálogo do espólio. Lisboa: FLAD, 1997."},
                ],
            },
            {
                "paragraphs_pt": [
                    {
                        "before": "A reconstituição desta biblioteca digital foi realizada a partir do ",
                        "link_text": "catálogo manuscrito",
                        "after": " existente no Arquivo Nacional Torre do Tombo, Manuscritos de Correia da Serra, C22.",
                        "link_endpoint": "download_catalogo",
                    },
                    "A metodologia seguida nesta reconstituição – que inicialmente decorreu através de um apelo a contribuições colaborativas que obteve escassa resposta pública – pode ser consultada aqui:",
                ],
                "paragraphs_en": [
                    {
                        "before": "This digital library was reconstructed from the ",
                        "link_text": "handwritten catalogue",
                        "after": " held by the National Archive of Torre do Tombo, Manuscritos de Correia da Serra, C22.",
                        "link_endpoint": "download_catalogo",
                    },
                    "The methodology used for this reconstruction, which initially included a call for collaborative contributions that received little public response, is available here:",
                ],
                "items": [
                    {"text": "Cardoso, José Luís, Borbinha, José Luís e Fernandes, Diogo. Biblioteca Digital de José Correia da Serra. Lisboa: Academia das Ciências de Lisboa, 2025.", "url": "https://doi.org/10.58164/t423-v704"},
                ],
            },
        ],
    },
    "investigacao": {
        "endpoint": "research",
        "title_pt": "Equipa",
        "title_en": "Team",
        "layout": "image_right",
        "image": "static/page-research.png",
        "sections": [
            {
                "items_pt": [
                    "Coordenação do projeto: José Luís Cardoso",
                    "Coordenação informática: José Borbinha",
                    "Bolseiros de investigação: Diogo Fernandes, Francisco Nabais e João Pedro Coelho",
                ],
                "items_en": [
                    "Project coordination: José Luís Cardoso",
                    "IT coordination: José Borbinha",
                    "Research fellows: Diogo Fernandes, Francisco Nabais and João Pedro Coelho",
                ],
                "plain_items": True,
            },
            {
                "heading_pt": "Apoios",
                "heading_en": "Support",
                "paragraphs_pt": [
                    "Bolsas de investigação com o apoio da Fundação Luso-Americana para o Desenvolvimento.",
                ],
                "paragraphs_en": [
                    "Research grants supported by the Luso-American Development Foundation.",
                ],
                "image": "static/logotipo_flad.png",
                "image_alt_pt": "Fundação Luso-Americana para o Desenvolvimento",
                "image_alt_en": "Luso-American Development Foundation",
            },
        ],
    },
    "publicacoes": {
        "endpoint": "publications",
        "title_pt": "Publicações",
        "title_en": "Publications",
        "layout": "publications",
        "publications": [
            {
                "kind_pt": "Artigo",
                "kind_en": "Article",
                "title": "A estante de economia de Jose Correia da Serra",
                "authors": "Cardoso, Jose Luis",
                "year": "2026",
                "image": "static/publication-article.png",
            },
            {
                "kind_pt": "Comunicacao",
                "kind_en": "Talk",
                "title": "A biblioteca de Correia da Serra: conteudo e recuperacao digital",
                "authors": "Cardoso, Jose Luis; Borbinha, Jose; Nabais, Francisco",
                "year": "2026",
                "image": "static/publication-talk.png",
            },
        ],
        "body_pt": [
            "Espaco reservado para publicacoes, relatorios, materiais de apoio e ligacoes relacionadas com o estudo da Biblioteca Correia da Serra.",
            "Pode incluir futuramente textos curatoriais, bibliografia e documentos descarregaveis.",
        ],
        "body_en": [
            "A space for publications, reports, supporting materials and links related to the study of the Correia da Serra Library.",
            "It can later include curatorial texts, bibliography and downloadable documents.",
        ],
    },
    "contactos": {
        "endpoint": "contacts",
        "title_pt": "Contactos",
        "title_en": "Contacts",
        "layout": "image_left",
        "image": "static/page-contact.png",
        "sections": [
            {
                "heading_pt": "Academia das Ciências de Lisboa",
                "heading_en": "Lisbon Academy of Sciences",
                "items_pt": [
                    "Rua da Academia das Ciências, 19",
                    "1249-122 Lisboa",
                    "Telefone: (+351) 213 219 730",
                    "E-mail: geral [at] acad-ciencias.pt",
                ],
                "items_en": [
                    "Rua da Academia das Ciências, 19",
                    "1249-122 Lisbon",
                    "Telephone: (+351) 213 219 730",
                    "Email: geral [at] acad-ciencias.pt",
                ],
                "plain_items": True,
            },
        ],
    },
}


DETAIL_FIELDS = [
    ("Bibliographic Description", "original_transcription"),
    ("titulo", "title_label"),
    ("author", "author"),
    ("editor_name", "editor_name"),
    ("tradutor", "translator"),
    ("editor", "printer"),
    ("local", "original_place"),
    ("local(atual)", "current_place"),
    ("date", "date"),
    ("tomos", "volumes"),
    ("lingua", "language"),
    ("classification", "topics"),
    ("carreira", "shelf"),
    ("notas", "notes"),
    ("registo", "catalog_record_number"),
    ("estado", "status"),
]

DETAIL_FILTER_PARAMS = {
    "author": "author",
    "editor_name": "editor_name",
    "tradutor": "tradutor",
    "editor": "editor",
    "local(atual)": "local_atual",
    "date": "date",
    "lingua": "lingua",
    "classification": "classification",
}


def normalize_value(value):
    if pd.isna(value):
        return ""

    if isinstance(value, (int, np.integer)):
        return str(int(value))

    if isinstance(value, (float, np.floating)):
        if float(value).is_integer():
            return str(int(value))
        return str(value).strip()

    text = str(value).strip()
    if text.lower() in {"nan", "none"}:
        return ""

    text = re.sub(r"\b(\d+)\.0\b", r"\1", text)
    text = re.sub(r"\s*-\s*", "-", text)
    return text


def normalize_multiline(value):
    return normalize_value(value).replace("\r\n", "\n").replace("\r", "\n")


def display_missing(value):
    text = normalize_value(value)
    return text if text else "sem valor"


def compare_text(value):
    text = normalize_value(value).casefold()
    return "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )


def display_value(value, missing_label=None, author=False):
    text = normalize_value(value)
    comparable = compare_text(text)
    missing_values = {"", "sem valor", "nan", "none"}
    unknown_author_values = {"autor nao identificado", "autor desconhecido"}
    missing_label = missing_label or translate("missing_value")

    if author and (comparable in missing_values or comparable in unknown_author_values):
        return Markup(f"<em>({escape(translate('unknown_author'))})</em>")

    if comparable in missing_values:
        return Markup(f"<em>({escape(missing_label)})</em>")

    return escape(text)


def known_value(value, author=False):
    comparable = compare_text(value)
    missing_values = {"", "sem valor", "nan", "none"}
    unknown_author_values = {"autor nao identificado", "autor desconhecido"}
    return comparable not in missing_values and not (
        author and comparable in unknown_author_values
    )


def load_data():
    df = pd.read_excel(EXCEL_PATH, sheet_name="Sheet1")
    df = df.astype(object).where(pd.notnull(df), "")

    for column in df.columns:
        df[column] = df[column].apply(normalize_multiline)

    if "id" in df.columns:
        df["id"] = df["id"].apply(lambda value: int(float(value)) if normalize_value(value) else 0)

    return df.sort_values("id").reset_index(drop=True)


def current_lang():
    return "en" if request.args.get("lang") == "en" else "pt"


def translate(key):
    return TEXT[current_lang()].get(key, key)


def lang_url(endpoint, **values):
    values.setdefault("lang", current_lang())
    return url_for(endpoint, **values)


def switch_language_url():
    args = request.args.to_dict(flat=True)
    args["lang"] = "pt" if current_lang() == "en" else "en"
    values = dict(request.view_args or {})
    values.update(args)
    return url_for(request.endpoint, **values)


def catalog_filter_url(param, value):
    query = urlencode({param: normalize_value(value), "lang": current_lang()})
    return url_for("catalog") + f"?{query}"


@app.context_processor
def template_helpers():
    lang = current_lang()
    return {
        "current_lang": lang,
        "t": TEXT[lang],
        "site_url": lang_url,
        "switch_language_url": switch_language_url,
        "catalog_filter_url": catalog_filter_url,
        "display_value": display_value,
        "known_value": known_value,
    }


def image_number(path):
    match = re.search(r"/?(\d+)_", normalize_value(path))
    return str(int(match.group(1))) if match else ""


def image_url(path):
    clean_path = normalize_value(path).replace("\\", "/")
    return url_for("static", filename=clean_path)


def work_image_manifest():
    try:
        with open(WORK_IMAGES_MANIFEST, "r", encoding="utf-8") as handle:
            return json.load(handle).get("images", {})
    except (OSError, json.JSONDecodeError):
        return {}


def record_from_row(row):
    item = row.to_dict()
    item["image_url"] = image_url(item.get("path", ""))
    work_image_entry = work_image_manifest().get(str(item.get("id", "")), {})
    work_image = work_image_entry.get("file", "")
    item["work_image_url"] = url_for("static", filename=work_image) if work_image else ""
    item["work_image_source_url"] = work_image_entry.get("source_url", "")
    item["catalog_number"] = image_number(item.get("path", ""))
    item["links"] = [
        link.strip()
        for link in normalize_multiline(item.get("URL", "")).splitlines()
        if link.strip()
    ]
    return item


def active_filters():
    selected = {}
    for meta in FILTERS:
        value = normalize_value(request.args.get(meta["param"], ""))
        if value:
            selected[meta["param"]] = value
    return selected


def active_query():
    return normalize_value(request.args.get("q", ""))


def apply_filters(df, selected, query=""):
    filtered = df.copy()
    for meta in FILTERS:
        selected_value = selected.get(meta["param"])
        if not selected_value:
            continue

        field = meta["field"]
        if selected_value == "_sem_valor":
            filtered = filtered[filtered[field].apply(lambda value: normalize_value(value) == "")]
        else:
            filtered = filtered[filtered[field].apply(normalize_value) == selected_value]

    if query:
        if filtered.empty:
            return filtered

        words = query.casefold().split()
        search_fields = [
            "Bibliographic Description",
            "titulo",
            "author",
            "editor",
            "editor_name",
            "tradutor",
            "local",
            "local(atual)",
            "date",
            "classification",
            "lingua",
        ]

        def row_matches(row):
            haystack = " ".join(normalize_value(row.get(field, "")) for field in search_fields).casefold()
            return all(word in haystack for word in words)

        filtered = filtered[filtered.apply(row_matches, axis=1)]

    return filtered


def first_year(value):
    match = re.search(r"\d{3,4}", normalize_value(value))
    return int(match.group(0)) if match else None


def sort_key_text(value):
    text = normalize_value(value).casefold()
    return text


def apply_sort(df, sort_value):
    sort_value = sort_value if sort_value in {option["value"] for option in SORT_OPTIONS} else "date_asc"
    sorted_df = df.copy()

    if sort_value.startswith("date"):
        sorted_df["_sort_key"] = sorted_df["date"].apply(first_year)
        sorted_df["_sort_missing"] = sorted_df["_sort_key"].isna()
        sorted_df = sorted_df.sort_values(
            ["_sort_missing", "_sort_key", "id"],
            ascending=[True, sort_value == "date_asc", True],
        )
    elif sort_value.startswith("title"):
        sorted_df["_sort_key"] = sorted_df["titulo"].apply(sort_key_text)
        sorted_df["_sort_missing"] = sorted_df["_sort_key"] == ""
        sorted_df = sorted_df.sort_values(
            ["_sort_missing", "_sort_key", "id"],
            ascending=[True, sort_value == "title_asc", True],
        )
    elif sort_value.startswith("author"):
        sorted_df["_sort_key"] = sorted_df["author"].apply(sort_key_text)
        sorted_df["_sort_missing"] = sorted_df["_sort_key"] == ""
        sorted_df = sorted_df.sort_values(
            ["_sort_missing", "_sort_key", "id"],
            ascending=[True, sort_value == "author_asc", True],
        )

    return sorted_df.drop(columns=["_sort_key", "_sort_missing"], errors="ignore")


def option_counts(df):
    options = {}
    for meta in FILTERS:
        field = meta["field"]
        values = df[field].apply(normalize_value)
        counts = values.value_counts().to_dict()

        real_values = sorted(
            [
                {"value": value, "label": value, "count": int(count)}
                for value, count in counts.items()
                if value
            ],
            key=lambda item: item["label"].casefold(),
        )

        missing_count = int(counts.get("", 0))
        if missing_count:
            real_values.append(
                {
                    "value": "_sem_valor",
                    "label": f"({translate('missing_value')})",
                    "count": missing_count,
                }
            )

        options[meta["param"]] = real_values

    return options


def summary_counts(df):
    summary = []
    for meta in FILTERS:
        values = df[meta["field"]].apply(normalize_value)
        summary.append(
            {
                "label": translate(meta["label_key"]),
                "count": int(values[values != ""].nunique()),
            }
        )
    return summary


def url_with_page(page):
    args = request.args.to_dict(flat=True)
    args["page"] = page
    return url_for("catalog") + "?" + urlencode(args)


def filter_url(param, value):
    return url_for("catalog") + "?" + urlencode({param: value, "lang": current_lang()})


@app.route("/")
def home():
    return render_template(
        "home.html",
        title=translate("home"),
    )


@app.route("/catalogo")
def catalog():
    df = load_data()
    selected = active_filters()
    query = active_query()
    selected_sort = request.args.get("sort", "date_asc")
    filtered = apply_sort(apply_filters(df, selected, query), selected_sort)

    page = max(int(request.args.get("page", 1) or 1), 1)
    total = len(filtered)
    total_pages = max(math.ceil(total / PER_PAGE), 1)
    page = min(page, total_pages)

    start = (page - 1) * PER_PAGE
    page_df = filtered.iloc[start : start + PER_PAGE]
    records = [record_from_row(row) for _, row in page_df.iterrows()]

    return render_template(
        "catalog.html",
        title=translate("catalog"),
        records=records,
        filters=FILTERS,
        selected=selected,
        query=query,
        options=option_counts(df),
        sort_options=SORT_OPTIONS,
        selected_sort=selected_sort,
        summary=summary_counts(df),
        total=total,
        page=page,
        total_pages=total_pages,
        prev_url=url_with_page(page - 1) if page > 1 else "",
        next_url=url_with_page(page + 1) if page < total_pages else "",
        clear_url=lang_url("catalog"),
    )


@app.route("/sobre")
def about():
    return content_page("sobre")


@app.route("/investigacao")
def research():
    return content_page("investigacao")


@app.route("/publicacoes")
def publications():
    return content_page("publicacoes")


@app.route("/contactos")
def contacts():
    return content_page("contactos")


def content_page(page_key):
    page = CONTENT_PAGES[page_key]
    lang = current_lang()
    return render_template(
        "content_page.html",
        title=page[f"title_{lang}"],
        page=page,
        page_title=page[f"title_{lang}"],
        section_title=page.get(f"section_title_{lang}", page[f"title_{lang}"]),
        paragraphs=page.get(f"body_{lang}", []),
        sections=page.get("sections", []),
    )


@app.route("/obra/<int:record_id>")
def detail(record_id):
    df = load_data()
    row = df[df["id"] == record_id]
    if row.empty:
        abort(404)

    record = record_from_row(row.iloc[0])
    fields = []
    for field, label_key in DETAIL_FIELDS:
        raw_value = record.get(field, "")
        filter_param = DETAIL_FILTER_PARAMS.get(field)
        href = ""
        if filter_param and known_value(raw_value, author=field == "author"):
            href = catalog_filter_url(filter_param, raw_value)
        if field == "registo":
            catalog_number = record.get("catalog_number") or raw_value
            database_note = translate("database_record_note").format(record_id=record_id)
            value = Markup(
                f"{display_value(catalog_number)} "
                f"<span class=\"database-record-note\">({escape(database_note)})</span>"
            )
        else:
            value = display_value(raw_value, author=field == "author")
        fields.append(
            {
                "label": translate(label_key),
                "value": value,
                "href": href,
            }
        )

    return render_template(
        "detail.html",
        title=f"{translate('record')} {record_id}",
        record=record,
        fields=fields,
    )


@app.route("/indices")
def indices():
    df = load_data()
    groups = []
    options = option_counts(df)
    for meta in FILTERS:
        groups.append(
            {
                "label": translate(meta["label_key"]),
                "items": [
                    {
                        **option,
                        "href": filter_url(meta["param"], option["value"]),
                    }
                    for option in options[meta["param"]]
                ],
            }
        )

    return render_template("indices.html", title="Indices", groups=groups)


@app.route("/download-excel")
def download_excel():
    stamp = datetime.now().strftime("%Y%m%d%H%M")
    return send_file(EXCEL_PATH, as_attachment=True, download_name=f"database-{stamp}.xlsx")


@app.route("/download-catalogo")
def download_catalogo():
    return send_file(
        os.path.join(ROOT_DIR, "server", "catalogo.pdf"),
        mimetype="application/pdf",
        as_attachment=False,
        download_name="catalogo.pdf",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
