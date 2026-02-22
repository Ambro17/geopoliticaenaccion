# GeoPolVis
[Demo](https://ambro17.github.io/geopoliticaenaccion/)
Transcribe geopolitical podcasts, extract semantic entities, and visualize them as interactive knowledge graphs.

## Project Structure

All podcast data lives in a single `artifacts/` folder. Each episode is a triplet of colocated files sharing the same `YYYY-MM-DD-Name` basename:

```
artifacts/
  2025-07-13-Malvinas.mp3          # source audio
  2025-07-13-Malvinas.txt          # transcript
  2025-07-13-Malvinas.html         # individual semantic graph
  ...
  global_graph.html                # aggregated graph across all episodes
```

Supporting files:

```
analysis/analysis.json             # LLM-generated summaries, highlights, references
podcast_artifacts.py               # single source of truth for episode metadata
index.html                         # main web UI (loads graphs from artifacts/)
```

## Pipeline: MP3 to HTML

### 1. Transcribe audio (`transcribe.py`)

Converts an MP3 file to a plain-text transcript using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

```bash
python transcribe.py artifacts/2025-07-13-Malvinas.mp3
```

- Uses Whisper speech-to-text with a Spanish prompt to filter disfluencies
- Configurable model size (`--model tiny|base|small|medium|large-v3`), device, language
- Output defaults to `artifacts/{stem}.txt` (override with `--output`)
- Supports VAD filtering and progress reporting

### 2. Build individual graph (`build_graph.py`)

Extracts named entities (people, organizations, locations) from a transcript and builds a co-occurrence graph.

```bash
python build_graph.py artifacts/2025-07-13-Malvinas.txt
```

- Loads the `es_core_news_lg` spaCy model for Spanish NER
- Filters noise (vocalizations, stop words, invalid POS tags)
- Keeps top 50 entities by frequency
- Builds edges from sentence-level co-occurrence
- Outputs an interactive pyvis HTML graph to `artifacts/{stem}.html`

### 3. Build global graph (`build_global_graph.py`)

Aggregates entities across all transcripts into a single graph showing cross-episode connections.

```bash
python build_global_graph.py
```

- Reads all `*.txt` files from `artifacts/`
- Tracks which episodes mention each entity
- Keeps top 75 global entities
- Outputs to `artifacts/global_graph.html` with a click panel showing source episodes

### 4. Generate analysis (`generate_tabs.py`)

Uses Google Gemini to produce summaries, highlights, and media references for each episode.

```bash
export GEMINI_API_KEY=your_key
python generate_tabs.py
```

- Reads all `*.txt` files from `artifacts/`
- Generates three sections per episode via LLM:
  - **Summary**: narrative structure (max 4 paragraphs, HTML)
  - **Highlights**: notable opinions, debunked myths, predictions (max 5, HTML list)
  - **References**: books, movies, series mentioned (HTML list)
- Caches results in `analysis/analysis.json` (keyed by `{stem}.html`)

### 5. Serve the UI

Open `index.html` in a browser. It loads graphs from `artifacts/` via iframe and displays the analysis data from an embedded cache.

For GitHub Pages deployment, push to `main` and the workflow copies `index.html` + `artifacts/` to the published site.

## Batch Processing

Rebuild all individual graphs + the global graph from existing transcripts:

```bash
python rebuild_all.py
```

Process all MP3s in `artifacts/` (find transcripts, build graphs):

```bash
python process_all.py
```

## Adding a New Episode

1. Place the MP3 in `artifacts/` with the naming convention `YYYY-MM-DD-Name.mp3`
2. Transcribe: `python transcribe.py artifacts/YYYY-MM-DD-Name.mp3`
3. Build graph: `python build_graph.py artifacts/YYYY-MM-DD-Name.txt`
4. Rebuild global graph: `python build_global_graph.py`
5. Generate analysis: `python generate_tabs.py`
6. Add the entry to `podcast_artifacts.py` and update the `graphs` array + `analysisDataCache` in `index.html`

## Dependencies

```bash
pip install faster-whisper flask spacy networkx pyvis pandas google-genai
python -m spacy download es_core_news_lg
```
