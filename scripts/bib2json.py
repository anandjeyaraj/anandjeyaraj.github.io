import html
import re
from pathlib import Path
from collections import defaultdict

BIB_FILE = Path("publications.bib")
HTML_FILE = Path("research.html")

START = "<!-- PUBLICATIONS START -->"
END = "<!-- PUBLICATIONS END -->"

CATEGORY_MAP = {
    "article": "Journal Articles",
    "inproceedings": "Conference Proceedings",
    "incollection": "Book Chapters",
    "confpres": "Conference Presentations",
    "editorial": "Guest Editorials",
}

CATEGORY_ORDER = [
    "Journal Articles",
    "Conference Proceedings",
    "Book Chapters",
    "Conference Presentations",
    "Guest Editorials",
]


def clean(value):
    value = value.replace("~", " ")
    value = value.replace("---", "—")
    value = value.replace("--", "–")

    replacements = {
        r"\&": "&",
        r"\%": "%",
        r"\_": "_",
        r"\#": "#",
        r"\{": "{",
        r"\}": "}",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"\\[a-zA-Z]+", "", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\s+", " ", value).strip()

    return value


def find_entries(text):
    entries = []
    i = 0

    while i < len(text):
        if text[i] != "@":
            i += 1
            continue

        brace = text.find("{", i)
        if brace == -1:
            break

        entry_type = text[i + 1:brace].strip().lower()

        depth = 0
        k = brace

        while k < len(text):
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1

        if entry_type in CATEGORY_MAP:
            entries.append((entry_type, text[brace + 1:k]))

        i = k + 1

    return entries


def parse_fields(body):
    comma = body.find(",")

    if comma == -1:
        return "", {}

    key = body[:comma].strip()
    rest = body[comma + 1:]
    fields = {}

    pattern = re.compile(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*")
    i = 0

    while i < len(rest):

        while i < len(rest) and rest[i] in " \t\r\n,":
            i += 1

        match = pattern.match(rest, i)

        if not match:
            break

        name = match.group(1).lower()
        i = match.end()

        if i < len(rest) and rest[i] == "{":

            start = i + 1
            depth = 1
            i += 1

            while i < len(rest) and depth:

                if rest[i] == "{":
                    depth += 1

                elif rest[i] == "}":
                    depth -= 1

                i += 1

            value = rest[start:i - 1]

        elif i < len(rest) and rest[i] == '"':

            i += 1
            start = i

            while i < len(rest) and rest[i] != '"':
                i += 1

            value = rest[start:i]
            i += 1

        else:

            start = i

            while i < len(rest) and rest[i] != ",":
                i += 1

            value = rest[start:i].strip()

        fields[name] = clean(value)

    return key, fields
}


def format_authors(author_field):

authors = re.split(r"\s+and\s+", author_field.strip())

formatted = []

for author in authors:

    if "," in author:

        last, first = [
            x.strip()
            for x in author.split(",", 1)
        ]

    else:

        parts = author.split()
        last = parts[-1]
        first = " ".join(parts[:-1])

    initials = []

    for part in first.replace("-", " ").split():

        if part:
            initials.append(
                part[0].upper() + "."
            )

    if initials:
        name = f"{last}, {' '.join(initials)}"
    else:
        name = last

    if last.lower() == "jeyaraj":
        name = f"<strong>{html.escape(name)}</strong>"
    else:
        name = html.escape(name)

    formatted.append(name)

if len(formatted) == 1:
    return formatted[0]

if len(formatted) == 2:
    return f"{formatted[0]}, & {formatted[1]}"

return (
    ", ".join(formatted[:-1])
    + ", & "
    + formatted[-1]
)


def link(url):

    if not url:
        return ""

    safe_url = html.escape(url, quote=True)

    return f' <a href="{safe_url}">Link</a>'


def format_article(fields):

    text = (
        f"<strong>{html.escape(format_authors(fields.get('author', '')))}</strong>"
        f" ({html.escape(fields.get('year', ''))}). "
        f"{html.escape(fields.get('title', ''))}. "
    )

    journal = fields.get("journal", "")

    if journal:
        text += f"<em>{html.escape(journal)}</em>"

    volume = fields.get("volume", "")

    if volume:
        text += f", <em>{html.escape(volume)}</em>"

    number = fields.get("number", "")

    if number:
        text += f"({html.escape(number)})"

    pages = fields.get("pages", "")

    if pages:
        text += f", {html.escape(pages)}"

    text += "."

    note = fields.get("note", "")

    if note:
        text += f" {html.escape(note)}."

    text += link(fields.get("url", ""))

    return text


def format_proceedings(fields):

    text = (
        f"<strong>{html.escape(format_authors(fields.get('author', '')))}</strong>"
        f" ({html.escape(fields.get('year', ''))}). "
        f"{html.escape(fields.get('title', ''))}. "
    )

    booktitle = fields.get("booktitle", "")

    if booktitle:
        text += f"<em>{html.escape(booktitle)}</em>"

    pages = fields.get("pages", "")

    if pages:
        text += f", {html.escape(pages)}"

    address = fields.get("address", "")

    if address:
        text += f", {html.escape(address)}"

    text += "."

    text += link(fields.get("url", ""))

    return text


def format_book_chapter(fields):

    text = (
        f"<strong>{html.escape(format_authors(fields.get('author', '')))}</strong>"
        f" ({html.escape(fields.get('year', ''))}). "
        f"{html.escape(fields.get('title', ''))}. "
    )

    booktitle = fields.get("booktitle", "")

    if booktitle:
        text += f"<em>{html.escape(booktitle)}</em>"

    pages = fields.get("pages", "")

    if pages:
        text += f", {html.escape(pages)}"

    text += "."

    text += link(fields.get("url", ""))

    return text


def format_conference_presentation(fields):

    text = (
        f"<strong>{html.escape(format_authors(fields.get('author', '')))}</strong>"
        f" ({html.escape(fields.get('year', ''))}). "
        f"{html.escape(fields.get('title', ''))}. "
    )

    booktitle = fields.get("booktitle", "")

    if booktitle:
        text += f"<em>{html.escape(booktitle)}</em>"

    address = fields.get("address", "")

    if address:
        text += f", {html.escape(address)}"

    text += "."

    return text


def format_editorial(fields):

    text = (
        f"<strong>{html.escape(format_authors(fields.get('author', '')))}</strong>"
        f" ({html.escape(fields.get('year', ''))}). "
        f"{html.escape(fields.get('title', ''))}. "
    )

    journal = fields.get("journal", "")

    if journal:
        text += f"<em>{html.escape(journal)}</em>"

    pages = fields.get("pages", "")

    if pages:
        text += f", {html.escape(pages)}"

    text += "."

    text += link(fields.get("url", ""))

    return text


def format_citation(entry_type, fields):

    if entry_type == "article":
        return format_article(fields)

    if entry_type == "inproceedings":
        return format_proceedings(fields)

    if entry_type == "incollection":
        return format_book_chapter(fields)

    if entry_type == "confpres":
        return format_conference_presentation(fields)

    if entry_type == "editorial":
        return format_editorial(fields)

    return ""


def main():

    text = BIB_FILE.read_text(encoding="utf-8")

    entries = find_entries(text)

    sections = defaultdict(list)

    for entry_type, body in entries:

        key, fields = parse_fields(body)

        if not key:
            continue

        year_match = re.search(
            r"\d{4}",
            fields.get("year", "")
        )

        year = (
            int(year_match.group())
            if year_match
            else 0
        )

        citation = format_citation(
            entry_type,
            fields
        )

        if citation:

            sections[
                CATEGORY_MAP[entry_type]
            ].append({
                "year": year,
                "title": fields.get("title", ""),
                "citation": citation,
            })

    output = []

    for category in CATEGORY_ORDER:

        if category not in sections:
            continue

        output.append(
            f"<h2>{category}</h2>"
        )

        by_year = defaultdict(list)

        for publication in sections[category]:

            by_year[
                publication["year"]
            ].append(publication)

        for year in sorted(
            by_year.keys(),
            reverse=True
        ):

            output.append(
                f'<h3 class="publication-year">{year}</h3>'
            )

            output.append(
                '<ul class="publications">'
            )

            for publication in sorted(
                by_year[year],
                key=lambda x: x["title"].lower()
            ):

                output.append(
                    f'<li>{publication["citation"]}</li>'
                )

            output.append("</ul>")

    generated = "\n\n".join(output)

    page = HTML_FILE.read_text(
        encoding="utf-8"
    )

    start = page.find(START)
    end = page.find(END)

    if start == -1 or end == -1:

        raise RuntimeError(
            "Could not find PUBLICATIONS START/END markers "
            "in research.html"
        )

    new_page = (
        page[:start]
        + START
        + "\n\n"
        + generated
        + "\n\n"
        + page[end:]
    )

    HTML_FILE.write_text(
        new_page,
        encoding="utf-8"
    )

    print(
        f"Generated {sum(len(v) for v in sections.values())} publications."
    )


if __name__ == "__main__":
    main()
