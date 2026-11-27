import json
import os
import re
import sys
from pathlib import Path

from mistralai.client import Mistral
from mistralai.client.models import SystemMessage, UserMessage

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
STATE_PATH = ROOT / "state.json"
CONTENT_DIR = ROOT / "content"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_state(config):
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"level": config.get("start_level", "A2"), "history": []}


def next_unit_number():
    CONTENT_DIR.mkdir(exist_ok=True)
    numbers = [int(p.stem.split("-")[0]) for p in CONTENT_DIR.glob("[0-9]*.md")]
    return max(numbers, default=0) + 1


def story_context(max_chars=1500):
    files = sorted(CONTENT_DIR.glob("[0-9]*.md"))
    if not files:
        return "Dies ist das erste Kapitel der Geschichte."
    return files[-1].read_text(encoding="utf-8")[-max_chars:]


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40] or "kapitel"


def build_prompt(config, level):
    replacements = {
        "{target_language}": config["target_language"],
        "{native_language}": config["native_language"],
        "{level}": level,
        "{genre}": config["genre"],
        "{max_words}": str(config["max_words"]),
        "{story_context}": story_context(),
    }
    prompt = config["system_prompt"]
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    return prompt


def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        sys.exit("Fehlender API-Key: bitte MISTRAL_API_KEY als Umgebungsvariable setzen.")

    config = load_config()
    state = load_state(config)
    level = state["level"]

    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model=config["model"],
        messages=[
            SystemMessage(content=build_prompt(config, level)),
            UserMessage(content="Schreibe das nächste Kapitel der Geschichte."),
        ],
    )
    content = response.choices[0].message.content
    if isinstance(content, list):
        content = "".join(getattr(chunk, "text", "") for chunk in content)
    markdown = content.strip()

    unit = next_unit_number()
    first_line = markdown.splitlines()[0] if markdown else ""
    title = first_line.lstrip("#").strip() or f"Kapitel {unit}"
    path = CONTENT_DIR / f"{unit:03d}-{slugify(title)}.md"
    path.write_text(markdown + "\n", encoding="utf-8")

    print(f"Kapitel {unit} auf Niveau {level} gespeichert: {path.relative_to(ROOT)}")
    print(f"Titel: {title}")


if __name__ == "__main__":
    main()
