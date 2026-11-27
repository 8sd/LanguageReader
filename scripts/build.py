import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
HTML_DIR = ROOT / "html"
TEMPLATE = ROOT / "templates" / "chapter.html"
ASSETS_DIR = ROOT / "assets"

PANDOC = os.environ.get("PANDOC_BIN", "pandoc")


def first_heading(md_path):
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return md_path.stem


def render_index(manifest):
    items = "\n".join(
        f'<li><a href="/chapter/{m["unit"]}">Kapitel {m["unit"]} – {m["title"]}</a></li>'
        for m in manifest
    )
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LanguageReader – Kapitel</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<main>
<h1>Kapitel</h1>
<ul>
{items}
</ul>
</main>
</body>
</html>
"""


def main():
    if shutil.which(PANDOC) is None and not Path(PANDOC).exists():
        sys.exit("pandoc nicht gefunden. Installation z. B.: apt install pandoc")
    CONTENT_DIR.mkdir(exist_ok=True)
    (HTML_DIR / "static").mkdir(parents=True, exist_ok=True)

    manifest = []
    for md in sorted(CONTENT_DIR.glob("[0-9]*.md")):
        unit = md.stem.split("-")[0]
        title = first_heading(md)
        out = HTML_DIR / f"{unit}.html"
        subprocess.run(
            [
                PANDOC,
                str(md),
                "--standalone",
                "--template", str(TEMPLATE),
                "--variable", f"unit={unit}",
                "--metadata", f"title={title}",
                "-o", str(out),
            ],
            check=True,
        )
        manifest.append({"unit": unit, "title": title, "file": f"{unit}.html"})

    (HTML_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (HTML_DIR / "index.html").write_text(render_index(manifest), encoding="utf-8")

    css = ASSETS_DIR / "style.css"
    if css.exists():
        shutil.copy(css, HTML_DIR / "static" / "style.css")

    print(f"{len(manifest)} Kapitel gebaut nach {HTML_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
