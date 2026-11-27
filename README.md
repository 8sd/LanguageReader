# LanguageReader

Sprachen lernen durch Lesen: KI-generierte Geschichten auf deinem Sprachniveau, mit Feedback-Schleife.

## Aufbau

- `scripts/generate.py` – ruft Mistral über das `mistralai`-SDK auf, liest `config.json` + `state.json` (aktuelles CEFR-Niveau) und speichert das nächste Kapitel als Markdown in `content/`
- `scripts/build.py` – konvertiert alle Markdown-Kapitel mit pandoc und dem Template `templates/chapter.html` (enthält die klickbaren Feedback-Buttons) nach `html/`
- `app.py` – Flask-Server: serviert die Kapitel aus `html/` und nimmt das Schwierigkeits-Feedback unter `/feedback` entgegen; passt das Niveau in `state.json` an (zu leicht → eine Stufe runter, zu schwer → eine Stufe hoch)

## Voraussetzungen

- Python 3.11+
- pandoc (`apt install pandoc`)
- Mistral API-Key

## Nutzung

```bash
pip install -r requirements.txt
export MISTRAL_API_KEY=...   # nie in Dateien committen

python scripts/generate.py   # neues Kapitel generieren (Markdown)
python scripts/build.py      # Markdown -> HTML bauen
python app.py                # http://127.0.0.1:8000
```

Nach dem Lesen eines Kapitels klickt man auf „Zu leicht / Passt genau / Zu schwer“ – das nächste `generate.py`-Kapitel wird auf dem angepassten Niveau generiert.

## Konfiguration

`config.json` steuert Modell, Zielsprache, Start-Niveau, Genre, Umfang und den System-Prompt (Platzhalter: `{level}`, `{target_language}`, `{native_language}`, `{genre}`, `{max_words}`, `{story_context}`).
