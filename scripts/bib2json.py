import html
import re
from pathlib import Path
from collections import defaultdict

BIB_FILE = Path("publications.bib")
HTML_FILE = Path("research.html")

START = "<!-- PUBLICATIONS START -->"
END = "<!-- PUBLICATIONS END -->"


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

        if entry_type not in ("comment", "string", "preamble"):
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


def clean(value):
    value = value.replace("~", " ")
    value = value.replace("--", "–")
    value = value.replace("---", "—")

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


def format_authors(author_field):
    authors = re.split(r"\s+and\s+", author_field.strip())
    formatted = []

    for author in authors:
        if "," in author:
            last, first = [x.strip() for x in author.split(",", 1)]
        else:
            parts = author.split()
            last = parts[-1]
            first = " ".join(parts[:-1])

        initials = []

        for part in first.replace("-", " ").split():
            if part:
                initials.append(part[0].upper() + ".")

        formatted.append(
            f"{last}, {' '.join(initials)}"
        )

    if len(formatted) == 1:
        return formatted[0]

    if len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"

    return ", ".join(formatted[:-1]) + ", & " + formatted[-1]


def format_article(fields):
    authors = format_authors(fields.get("author", ""))
    year = fields.get("year", "")
    title = fields.get("title", "")
    journal = fields.get("journal", "")
    volume = fields.get("volume", "")
    number = fields.get("number", "")
    pages = fields.get("pages", "")
    url = fields.get("url", "")
    note = fields.get("note", "")

    text = f"<strong>{html.escape(authors)}</strong> ({html.escape(year)}). "
    text += f"{html.escape(title)}. "

    if journal:
        text += f"<em>{html.escape(journal)}</em>"

    if volume:
        text += f", <em>{html.escape(volume)}</em>"

    if number:
        text += f"({html.escape(number)})"

    if pages:
        text += f", {html.escape(pages)}"

    text += "."

    if note:
        text += f" {html.escape(note)}."

    if url:
        safe_url = html.escape(url, quote=True)
        text += f' <a href="{safe_url}">Link</a>'

    return text


def format_conference(fields):
    authors = format_authors(fields.get("author", ""))
    year = fields.get("year", "")
    title = fields.get("title", "")
    booktitle = fields.get("booktitle", "")
    address = fields.get("address", "")
    url = fields.get("url", "")
    note = fields.get("note", "")

    text = f"<strong>{html.escape(authors)}</strong> ({html.escape(year)}). "
    text += f"{html.escape(title)}. "

    if booktitle:
        text += f"<em>In {html.escape(booktitle)}</em>"

    if address:
        text += f", {html.escape(address)}"

    text += "."

    if note:
        text += f" {html.escape(note)}."

    if url:
        safe_url = html.escape(url, quote=True)
        text += f' <a href="{safe_url}">Link</a>'

    return text


def main():
    text = BIB_FILE.read_text(encoding="utf-8")
    entries = find_entries(text)

    publications = []

    for entry_type, body in entries:
        key, fields = parse_fields(body)

        if not key:
            continue

        if entry_type == "article":
            publication_type = "Journal Articles"
            citation = format_article(fields)

        elif entry_type == "inproceedings":
            publication_type = "Conference Proceedings"
            citation = format_conference(fields)

        else:
            continue

        year_match = re.search(r"\d{4}", fields.get("year", ""))
        year = int(year_match.group()) if year_match else 0

        publications.append({
            "type": publication_type,
            "year": year,
            "title": fields.get("title", ""),
            "citation": citation
        })

    sections = defaultdict(list)

    for publication in publications:
        sections[publication["type"]].append(publication)

    output = []

    for section_name in ["Journal Articles", "Conference Proceedings"]:

        if section_name not in sections:
            continue

        output.append(f"<h2>{section_name}</h2>")

        by_year = defaultdict(list)

        for publication in sections[section_name]:
            by_year[publication["year"]].append(publication)

        for year in sorted(by_year.keys(), reverse=True):
            output.append(f'<h3 class="publication-year">{year}</h3>')

            output.append('<ul class="publications">')

            for publication in sorted(
                by_year[year],
                key=lambda x: x["title"].lower()
            ):
                output.append(
                    f'<li>{publication["citation"]}</li>'
                )

            output.append("</ul>")

    generated = "\n\n".join(output)

    page = HTML_FILE.read_text(encoding="utf-8")

    start = page.find(START)
    end = page.find(END)

    if start == -1 or end == -1:
        raise RuntimeError(
            "Could not find PUBLICATIONS START/END markers in research.html"
        )

    new_page = (
        page[:start]
        + START
        + "\n\n"
        + generated
        + "\n\n"
        + page[end:]
    )

    HTML_FILE.write_text(new_page, encoding="utf-8")

    print(f"Generated {len(publications)} publications.")


if __name__ == "__main__":
    main()
