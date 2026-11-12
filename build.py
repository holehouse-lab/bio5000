"""Build the BIO5000 journal club website from a single Markdown file.

All of the site's content lives in ``index.md``: a short block of YAML front matter
(the page-level facts shown in the header) followed by the page content in Markdown.
This script converts that file to HTML, drops it into ``template.html``, and writes
the finished site (``index.html`` plus everything in ``static/``) into ``_site/``.

Usage
-----
    python build.py
"""

from __future__ import annotations

import datetime
import html
import re
import shutil
import sys
from pathlib import Path
from string import Template
from typing import Any

import markdown
import yaml

PROJECT_DIRECTORY = Path(__file__).resolve().parent
SOURCE_PATH = PROJECT_DIRECTORY / "index.md"
TEMPLATE_PATH = PROJECT_DIRECTORY / "template.html"
STATIC_DIRECTORY = PROJECT_DIRECTORY / "static"
OUTPUT_DIRECTORY = PROJECT_DIRECTORY / "_site"
OUTPUT_PAGE_NAME = "index.html"

# Image shown next to the title in the page header. It lives in the static directory and is
# copied next to the page, so this name is also what the template's <img> points at.
HERO_FIGURE_NAME = "hero.png"

# Line that opens and closes the YAML front matter at the top of the Markdown file.
FRONT_MATTER_DELIMITER = "---"

# Front matter keys that must be present, and must be non-empty text.
REQUIRED_TEXT_FIELDS = ("course", "semester", "title", "tagline", "description")

# Python-Markdown extensions: pipe tables for the schedule, 'toc' to give every heading an
# id we can link to, 'sane_lists' for predictable list behaviour, 'smarty' for curly
# quotes, dashes, and ellipses, and 'attr_list' so a link can be turned into a button by
# writing {: .button } straight after it.
MARKDOWN_EXTENSIONS = ["tables", "toc", "sane_lists", "smarty", "attr_list"]

# Top-level sections are written as '## Heading' in the Markdown; each one gets a link in
# the navigation bar. The pattern matches the heading HTML that the 'toc' extension emits.
SECTION_HEADING_PATTERN = re.compile(r'<h2 id="(?P<anchor>[^"]+)">(?P<label>.*?)</h2>')


def split_front_matter(source_text: str) -> tuple[dict[str, Any], str]:
    """Split a Markdown document into its YAML front matter and its Markdown body.

    Parameters
    ----------
    source_text : str
        Full text of the Markdown file. The first line must be ``---``, and the front
        matter runs until the next line that is exactly ``---``.

    Returns
    -------
    tuple[dict[str, Any], str]
        The parsed front matter, and the Markdown body that follows it.

    Raises
    ------
    ValueError
        If the front matter is missing, isn't closed, or isn't a set of ``key: value`` pairs.
    """
    lines = source_text.splitlines()
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        raise ValueError(
            f"The Markdown file must start with a '{FRONT_MATTER_DELIMITER}' line (YAML front matter)."
        )

    stripped_lines = [line.strip() for line in lines]
    if FRONT_MATTER_DELIMITER not in stripped_lines[1:]:
        raise ValueError(
            f"The front matter is never closed with a second '{FRONT_MATTER_DELIMITER}' line."
        )
    closing_line_index = stripped_lines.index(FRONT_MATTER_DELIMITER, 1)

    metadata = yaml.safe_load("\n".join(lines[1:closing_line_index]))
    if not isinstance(metadata, dict):
        raise ValueError("The front matter must be a set of 'key: value' pairs.")

    body = "\n".join(lines[closing_line_index + 1 :])
    return metadata, body


def validate_metadata(metadata: dict[str, Any]) -> None:
    """Check the front matter has everything the template needs, and fail loudly if not.

    Parameters
    ----------
    metadata : dict[str, Any]
        Parsed front matter, as returned by :func:`split_front_matter`.

    Raises
    ------
    ValueError
        If a required field is missing or empty, if ``schedule_year`` isn't a whole number,
        or if ``details`` isn't a non-empty set of text labels and text values.
    """
    for field_name in REQUIRED_TEXT_FIELDS:
        field_value = metadata.get(field_name)
        if not isinstance(field_value, str) or not field_value.strip():
            raise ValueError(
                f"Front matter field '{field_name}' is missing or isn't text."
            )

    schedule_year = metadata.get("schedule_year")
    if isinstance(schedule_year, bool) or not isinstance(schedule_year, int):
        raise ValueError(
            "Front matter field 'schedule_year' must be a whole number, e.g. 2027."
        )

    details = metadata.get("details")
    if not isinstance(details, dict) or not details:
        raise ValueError(
            "Front matter field 'details' must be a non-empty set of 'Label: value' pairs."
        )
    for label, value in details.items():
        # YAML quietly turns some unquoted values into numbers (e.g. 14:00 becomes 840), so
        # anything that isn't text is rejected rather than shown on the page as nonsense.
        if not isinstance(label, str) or not isinstance(value, str):
            raise ValueError(
                f"Entry '{label}: {value}' in 'details' isn't text; wrap the value in quotes."
            )


def render_markdown(markdown_text: str) -> str:
    """Convert the Markdown body of the page to HTML.

    Parameters
    ----------
    markdown_text : str
        Markdown content (without the front matter).

    Returns
    -------
    str
        HTML fragment. Every heading carries an ``id`` derived from its text.
    """
    return markdown.markdown(
        markdown_text, extensions=MARKDOWN_EXTENSIONS, output_format="html"
    )


def build_navigation_html(content_html: str) -> str:
    """Build the navigation links, one per top-level (``##``) section of the page.

    Parameters
    ----------
    content_html : str
        Rendered page content, as returned by :func:`render_markdown`.

    Returns
    -------
    str
        One ``<a>`` element per section, in page order, separated by newlines.

    Raises
    ------
    ValueError
        If the content has no ``##`` headings, since the page would then have an empty
        navigation bar.
    """
    section_headings = list(SECTION_HEADING_PATTERN.finditer(content_html))
    if not section_headings:
        raise ValueError(
            "No '## Section' headings found, so there is nothing to put in the navigation bar."
        )

    links = [
        f'    <a href="#{heading["anchor"]}">{heading["label"]}</a>'
        for heading in section_headings
    ]
    return "\n".join(links)


def build_details_html(details: dict[str, str]) -> str:
    """Build the header's at-a-glance details (when, where, ...) as definition-list entries.

    Parameters
    ----------
    details : dict[str, str]
        Label-to-value pairs from the front matter, shown in the order they're written.

    Returns
    -------
    str
        One ``<div><dt>label</dt><dd>value</dd></div>`` group per entry, separated by newlines.
    """
    entries = [
        f"    <div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>"
        for label, value in details.items()
    ]
    return "\n".join(entries)


def render_page(source_text: str, template_text: str, build_date: datetime.date) -> str:
    """Render the complete HTML page from the Markdown source and the HTML template.

    Parameters
    ----------
    source_text : str
        Full text of the Markdown file (front matter plus body).
    template_text : str
        HTML template with ``$placeholder`` fields (see ``template.html``).
    build_date : datetime.date
        Date shown as "Last updated" in the footer.

    Returns
    -------
    str
        The finished HTML page.

    Raises
    ------
    ValueError
        If the front matter or content is malformed (see :func:`split_front_matter`,
        :func:`validate_metadata`, and :func:`build_navigation_html`).
    KeyError
        If the template uses a placeholder that isn't filled in here.
    """
    metadata, markdown_body = split_front_matter(source_text)
    validate_metadata(metadata)
    content_html = render_markdown(markdown_body)

    course = html.escape(metadata["course"])
    semester = html.escape(metadata["semester"])
    placeholders = {
        "page_title": f"{course} · {semester}",
        "course": course,
        "semester": semester,
        "title": html.escape(metadata["title"]),
        "tagline": html.escape(metadata["tagline"]),
        "description": html.escape(metadata["description"]),
        "schedule_year": str(metadata["schedule_year"]),
        "hero_figure_name": HERO_FIGURE_NAME,
        "details_html": build_details_html(metadata["details"]),
        "navigation_html": build_navigation_html(content_html),
        "content_html": content_html,
        "build_date": f"{build_date:%B} {build_date.day}, {build_date.year}",
    }
    return Template(template_text).substitute(placeholders)


def write_site(page_html: str, static_directory: Path, output_directory: Path) -> Path:
    """Write the rendered page and the static files (CSS, images) into the output directory.

    Existing files in the output directory are overwritten; nothing is deleted.

    Parameters
    ----------
    page_html : str
        The finished HTML page, as returned by :func:`render_page`.
    static_directory : Path
        Directory whose contents are copied as-is next to the page.
    output_directory : Path
        Directory to write the site into. Created if it doesn't exist.

    Returns
    -------
    Path
        Path of the written HTML page.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    shutil.copytree(static_directory, output_directory, dirs_exist_ok=True)
    output_page_path = output_directory / OUTPUT_PAGE_NAME
    output_page_path.write_text(page_html, encoding="utf-8")
    return output_page_path


def main() -> None:
    """Build the site from ``index.md`` and report where it was written.

    The build still goes ahead if the header figure is missing (the page just renders
    without it), but says so on stderr so it doesn't go unnoticed.
    """
    hero_figure_path = STATIC_DIRECTORY / HERO_FIGURE_NAME
    if not hero_figure_path.is_file():
        print(
            f"WARNING: {hero_figure_path.relative_to(PROJECT_DIRECTORY)} not found, "
            "so the page header will have no figure.",
            file=sys.stderr,
        )

    source_text = SOURCE_PATH.read_text(encoding="utf-8")
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    page_html = render_page(
        source_text, template_text, build_date=datetime.date.today()
    )
    output_page_path = write_site(page_html, STATIC_DIRECTORY, OUTPUT_DIRECTORY)
    print(
        f"Built {output_page_path.relative_to(PROJECT_DIRECTORY)} from {SOURCE_PATH.name}"
    )


if __name__ == "__main__":
    main()
