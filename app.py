import json
from pathlib import Path

from flask import Flask, abort, request, send_from_directory

ROOT = Path(__file__).resolve().parent
HTML_DIR = ROOT / "html"
STATE_PATH = ROOT / "state.json"
CONFIG_PATH = ROOT / "config.json"

CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
RATING_DELTA = {"easy": -1, "ok": 0, "hard": 1}
RATING_LABELS = {"easy": "zu leicht", "ok": "passt genau", "hard": "zu schwer"}

app = Flask(__name__)


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"level": config.get("start_level", "A2"), "history": []}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – LanguageReader</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<main>
{body}
</main>
</body>
</html>"""


@app.get("/")
def index():
    manifest_path = HTML_DIR / "manifest.json"
    if not manifest_path.exists():
        return page(
            "LanguageReader",
            "<h1>LanguageReader</h1><p>Noch keine Kapitel gebaut. "
            "Bitte <code>python scripts/generate.py</code> und <code>python scripts/build.py</code> ausführen.</p>",
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = "\n".join(
        f'<li><a href="/chapter/{m["unit"]}">Kapitel {m["unit"]} – {m["title"]}</a></li>'
        for m in manifest
    )
    return page("Kapitel", f"<h1>Kapitel</h1>\n<ul>\n{items}\n</ul>")


@app.get("/chapter/<unit>")
def chapter(unit):
    if not (HTML_DIR / f"{unit}.html").is_file():
        abort(404)
    return send_from_directory(HTML_DIR, f"{unit}.html")


@app.get("/feedback")
def feedback():
    unit = request.args.get("unit", "")
    rating = request.args.get("rating", "")
    if rating not in RATING_DELTA or not (HTML_DIR / f"{unit}.html").is_file():
        abort(400)

    state = load_state()
    current = CEFR_LEVELS.index(state["level"]) if state["level"] in CEFR_LEVELS else 1
    new_index = max(0, min(len(CEFR_LEVELS) - 1, current + RATING_DELTA[rating]))
    old_level = state["level"]
    state["level"] = CEFR_LEVELS[new_index]
    state["history"].append(
        {
            "unit": unit,
            "rating": rating,
            "level_before": old_level,
            "level_after": state["level"],
        }
    )
    save_state(state)

    body = f"""
<h1>Danke für dein Feedback!</h1>
<p>Kapitel {unit}: <strong>{RATING_LABELS[rating]}</strong></p>
<p>Aktuelles Niveau: <strong>{old_level}</strong> → <strong>{state["level"]}</strong></p>
<p>Das nächste Kapitel wird auf Niveau <strong>{state["level"]}</strong> generiert.</p>
<p><a href="/chapter/{unit}">Zurück zum Kapitel</a> · <a href="/">Alle Kapitel</a></p>
"""
    return page("Feedback", body)


@app.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(HTML_DIR / "static", filename)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
