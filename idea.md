# Parsear speach de podcast a texto y armar mapa conceptual

- Con distancias entre conceptos
- Con tamaño segun popularidad de podcast
- [Busqueda por concepto, que podcast hablan de X]

## Plan
- [x] MVP dado un audio, transcribir a texto
- [x] Dada la transcripcion, detectar paises y conceptos geopoliticos y graficar
- [x] Transcribir ultimos 5 podcasts
- [x] Web para interactuar con el grafo de conceptos/paises
- [x] Armar mapa conceptual de los ultimos 5 podcasts consolidado con referencia al podcast que mencionan el topic
- [x] Add single source of truth file for mp3, podcast link, transcript, and graph for easier mapping in the graph from node to podcast links
- [x] LLM 
     - [x] Summary of podcast topics into Narrative Structure, Facts Discussed, Opinions - With particular interest in forecasts, unconventional wisdom pieces and debunked myths if any, do not include if not confident of them
     - [x] Book/movie/reference extractions
     - [ ] Chat Interface to query knowledge graphs, get recommended podcasts

## Tech Stack
- [x] Whisper for speechtext
- [x] Pyvis for graph
- [x] HTML for web
- [x] Github Pages for hosting

## Tasks
- [x] Regenerate all outputs in spanish
- [x] Deploy as static site in the simplest version possible (js and vercel?)
- [x] Normalize filenames of podcast, transcript, and graph into a single folder artifacts so they're colocated and name mismatches are more evident
- [ ] Enhance graph relationships to have edge properties (age, type) to detect geopolitcs links beyond co-occurrence
- [ ] Add timestamps to transcript to allow jumping to specific parts of the podcast to find reference