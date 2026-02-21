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
- [x] LLM Summary of podcast topics into Narrative Structure, Facts Discussed, Opinions - With particular interest in forecasts, unconventional wisdom pieces and debunked myths if any, do not include if not confident of them
- [x] LLM for book/movie/reference extractions
- [ ] LLM Chat Interface to query knowledge graphs, get recommended podcasts

## Tech Stack
- [ ] Whisper for speechtext
- [ ] Pyvis for graph
- [ ] ?? for web
