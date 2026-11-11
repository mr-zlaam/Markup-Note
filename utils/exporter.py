"""Export utility for converting Markup Notes markdown into styled PDF and HTML documents."""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QMarginsF
from PyQt6.QtGui import QPageLayout, QPageSize, QPdfWriter, QTextDocument

logger = logging.getLogger(__name__)

PDF_STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Cantarell", "Segoe UI", "Ubuntu", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1e;
    margin: 0;
    padding: 0;
}
h1 {
    font-size: 22pt;
    font-weight: 700;
    color: #111114;
    margin-top: 0;
    margin-bottom: 12px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e0e0e4;
}
h2 {
    font-size: 16pt;
    font-weight: 600;
    color: #222226;
    margin-top: 16px;
    margin-bottom: 8px;
}
h3 {
    font-size: 13pt;
    font-weight: 600;
    color: #333338;
    margin-top: 12px;
    margin-bottom: 6px;
}
p {
    margin-top: 0;
    margin-bottom: 10px;
}
pre, code {
    font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Monospace", monospace;
    font-size: 9.5pt;
    background-color: #f4f4f7;
    border-radius: 4px;
}
pre {
    padding: 10px 14px;
    margin: 12px 0;
    border: 1px solid #e2e2e8;
}
code {
    padding: 2px 4px;
}
blockquote {
    border-left: 3px solid #0a84ff;
    padding-left: 12px;
    margin-left: 0;
    color: #55555e;
    font-style: italic;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
}
th, td {
    border: 1px solid #d4d4dc;
    padding: 6px 10px;
    text-align: left;
}
th {
    background-color: #f0f0f4;
    font-weight: 600;
}
hr {
    border: none;
    border-top: 1px solid #dcdce2;
    margin: 16px 0;
}
ul, ol {
    margin-top: 0;
    margin-bottom: 10px;
    padding-left: 24px;
}
li {
    margin-bottom: 4px;
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        :root {{
            --bg-color: {bg_color};
            --text-color: {text_color};
            --heading-color: {heading_color};
            --code-bg: {code_bg};
            --border-color: {border_color};
            --accent-color: #0a84ff;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Cantarell", "Segoe UI", "Ubuntu", sans-serif;
            line-height: 1.65;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 820px;
            margin: 0 auto;
            background-color: var(--bg-color);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: var(--heading-color);
            margin-top: 1.4em;
            margin-bottom: 0.6em;
            font-weight: 600;
        }}
        h1 {{
            font-size: 2.2em;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.3em;
            margin-top: 0;
        }}
        h2 {{ font-size: 1.6em; border-bottom: 1px solid var(--border-color); padding-bottom: 0.2em; }}
        h3 {{ font-size: 1.3em; }}
        p {{ margin: 0.8em 0; }}
        a {{ color: var(--accent-color); text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        pre, code {{
            font-family: "JetBrains Mono", "Fira Code", "Source Code Pro", "Monospace", monospace;
            font-size: 0.9em;
            background-color: var(--code-bg);
            border-radius: 5px;
        }}
        pre {{
            padding: 14px 18px;
            overflow-x: auto;
            border: 1px solid var(--border-color);
        }}
        code {{
            padding: 2px 6px;
        }}
        blockquote {{
            border-left: 4px solid var(--accent-color);
            padding-left: 14px;
            margin: 1em 0;
            color: #888894;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1.2em 0;
        }}
        th, td {{
            border: 1px solid var(--border-color);
            padding: 8px 14px;
            text-align: left;
        }}
        th {{
            background-color: var(--code-bg);
            font-weight: 600;
        }}
        hr {{
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 2em 0;
        }}
        ul, ol {{
            padding-left: 28px;
            margin: 0.8em 0;
        }}
        li {{ margin-bottom: 0.3em; }}
        @media print {{
            body {{ padding: 0; background: white; color: black; }}
            .container {{ max-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


def export_note_to_pdf(
    note_title: str,
    markdown_content: str,
    output_path: Path,
) -> bool:
    """Export note markdown to a high-DPI paginated PDF document.

    Args:
        note_title: The title of the note.
        markdown_content: The raw markdown content.
        output_path: Target destination path for the PDF file.

    Returns:
        True if PDF was successfully written, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        writer = QPdfWriter(str(output_path))
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(18.0, 18.0, 18.0, 18.0),
            QPageLayout.Unit.Millimeter,
        )
        writer.setPageLayout(layout)

        doc = QTextDocument()
        doc.setDefaultStyleSheet(PDF_STYLE)

        # Prepend title header if not already the first H1 in content
        trimmed = markdown_content.lstrip()
        if not trimmed.startswith("# "):
            full_markdown = f"# {note_title}\n\n{markdown_content}"
        else:
            full_markdown = markdown_content

        doc.setMarkdown(full_markdown)
        doc.print(writer)
        return True
    except Exception as err:
        logger.error(f"Failed to export note to PDF: {err}")
        return False


def export_note_to_html(
    note_title: str,
    markdown_content: str,
    output_path: Path,
    dark_theme: bool = False,
) -> bool:
    """Export note markdown to a standalone, responsive HTML document.

    Args:
        note_title: The title of the note.
        markdown_content: The raw markdown content.
        output_path: Target destination path for the HTML file.
        dark_theme: Whether to export with modern dark styling.

    Returns:
        True if HTML was successfully written, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = QTextDocument()

        trimmed = markdown_content.lstrip()
        if not trimmed.startswith("# "):
            full_markdown = f"# {note_title}\n\n{markdown_content}"
        else:
            full_markdown = markdown_content

        doc.setMarkdown(full_markdown)
        body_html = doc.toHtml()

        # Extract inner body content from QTextDocument HTML
        start_tag = "<body"
        end_tag = "</body>"
        s_idx = body_html.find(start_tag)
        if s_idx != -1:
            body_start = body_html.find(">", s_idx) + 1
            e_idx = body_html.find(end_tag)
            extracted_content = body_html[body_start:e_idx] if e_idx != -1 else body_html[body_start:]
        else:
            extracted_content = body_html

        if dark_theme:
            bg_color = "#1e1e22"
            text_color = "#e2e2e8"
            heading_color = "#ffffff"
            code_bg = "#28282e"
            border_color = "#36363e"
        else:
            bg_color = "#ffffff"
            text_color = "#202024"
            heading_color = "#111114"
            code_bg = "#f5f5f8"
            border_color = "#e2e2e8"

        full_html = HTML_TEMPLATE.format(
            title=note_title,
            bg_color=bg_color,
            text_color=text_color,
            heading_color=heading_color,
            code_bg=code_bg,
            border_color=border_color,
            content=extracted_content,
        )

        output_path.write_text(full_html, encoding="utf-8")
        return True
    except Exception as err:
        logger.error(f"Failed to export note to HTML: {err}")
        return False
