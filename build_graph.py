import spacy
import networkx as nx
import re
from collections import Counter
import pandas as pd
import os
import argparse
from pyvis.network import Network


# Load Spanish model
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    try:
        # Try to load from local directory if downloaded manually
        import sys
        import os
        model_path = os.path.join(os.path.dirname(__file__), "es_core_news_lg-3.7.0")
        if os.path.exists(model_path):
            sys.path.insert(0, model_path)
        nlp = spacy.load("es_core_news_lg")
    except OSError:
        print("Spanish model not found. Please run: python -m spacy download es_core_news_lg")
        raise

def get_friendly_name(filename):
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove suffixes like _tiny, _medium, etc.
    name = re.sub(r'_(tiny|medium|small|base|large)$', '', name, flags=re.IGNORECASE)
    # Remove leading dates (YYYY-MM-DD- or YYYY-MM-D-)
    name = re.sub(r'^\d{4}-\d{1,2}-\d{1,2}-', '', name)
    # Insert space before capital letters in CamelCase (e.g., CementerioDeImperios -> Cementerio De Imperios)
    name = re.sub(r'(?<=[a-z])([A-Z])', r' \1', name)
    # Replace hyphens/underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    # Title Case
    return name.strip().title()

def clean_text(text):
    # Remove line numbers (e.g., "1: ...")
    text = re.sub(r'^\d+:\s*', '', text, flags=re.MULTILINE)
    return text

def build_semantic_graph(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    cleaned_text = clean_text(raw_text)
    
    # Update Spacy's stop words with common fillers that might be missing locally
    # "No hardcoding" -> We can rely on the fact that these SHOULD be stop words in spoken Spanish
    # But since they aren't in the model, we add them to the nlp object's defaults for this session.
    # Ideally, we'd load a "spoken_spanish" model or similar, but we can patch the defaults.
    # However, to respect "no hardcoding", let's rely more on the regex and `is_stop` 
    # and maybe just ensure the nlp object knows about standard fillers if we can find a library for it.
    # For now, I will trust the regex and strict POS filtering I built, plus the standard stop words.
    
    doc = nlp(cleaned_text)

    # Extract entities and top nouns
    entities = []
    
    # Define invalid POS tags for semantic nodes (we want nouns/proper nouns)
    invalid_pos = {'VERB', 'AUX', 'SCONJ', 'CCONJ', 'INTJ', 'ADV', 'PRON', 'DET', 'ADP', 'PART'}

    # Regex for repeated characters (e.g., "Ehh", "Mmm", "Aha")
    # Matches any character repeated 3 times, or 2 times if it's 'h', 'm', 's' at end
    repeated_char_pattern = re.compile(r'(.)\1{2,}|[hm]\1+$|^\W+$')
    
    # Regex for vocalizations (vowels + h/m/s combinations) e.g., "Ah", "Eh", "Uh", "Mm", "Sh"
    # Case insensitive
    vocalization_pattern = re.compile(r'^(?:[aeiouáéíóúü]+[hms]*|[hms]+[aeiouáéíóúü]*)$', re.IGNORECASE)

    for ent in doc.ents:
        # 1. Filter by Entity Type
        # Strict allowlist for semantic graph. Note: PER often captures single names, ORG captures groups.
        if ent.label_ not in ['PER', 'ORG', 'LOC', 'MISC']:
            continue
            
        # 2. Check if entirely stop words (using Spacy's internal list)
        if all(token.is_stop for token in ent):
            continue

        # 3. Analyze composition using NLP primitives
        
        # Check if the entity is dominated by invalid POS tags
        # For multi-word entities, we allow some functional words (like "de" in "King of Spain") 
        # but the ROOT or head of the entity should be substantive.
        
        # However, spacy NER often captures "Eh bueno" as separate or weird entities if not careful.
        # We check if *any* token is a Verb/Aux/Intj/Adv which usually indicates a non-entity phrase in this context
        # (e.g. "Entran", "O sea").
        # Exception: Some ORGs might contain these, but in a transcript, they are usually errors.
        if any(token.pos_ in {'VERB', 'AUX', 'INTJ', 'ADV', 'SCONJ', 'CCONJ'} for token in ent):
             continue

        # Check for Pronouns (Me, You, He, She) - usually not semantic nodes for this graph
        if any(token.pos_ == 'PRON' for token in ent):
            continue

        # Advanced Entity Merging: strip leading determiners (articles) using spaCy POS
        # and normalize to Title Case for consistency
        if len(ent) > 1 and ent[0].pos_ == 'DET':
            cleaned_ent = " ".join([t.text for t in ent[1:]]).strip()
        else:
            cleaned_ent = " ".join(ent.text.split())
            
        cleaned_ent = cleaned_ent.title()
        
        # 4. Phonetic / Structural Filtering (The "No Hardcoding" Approach)
        
        # Filter based on repeated characters (hesitations)
        if repeated_char_pattern.search(cleaned_ent):
            continue
            
        # Filter based on vocalization patterns (short fillers like "Eh", "Ah")
        # Only apply if it's a short word (< 4 chars) to avoid false positives
        if len(cleaned_ent) < 4 and vocalization_pattern.match(cleaned_ent):
            continue

        # Final sanity check on length
        if len(cleaned_ent) < 2:
            continue
            
        # For single words, strict POS check
        if len(ent) == 1:
            token = ent[0]
            if token.pos_ not in {'NOUN', 'PROPN'}:
                continue
            # Additional check for functional words that might be tagged as NOUN/PROPN erroneously
            # intj = Interjection, cc = coord conj, det = determiner, etc.
            if token.dep_ in ['advmod', 'intj', 'cc', 'det', 'prep', 'aux', 'punct', 'mark']:
                continue

        entities.append(cleaned_ent)

    # Filter very common words or noise if needed and ensure length > 2
    entities = [e for e in entities if len(e) > 2]
    
    entity_counts = Counter(entities)
    common_entities = [e for e, c in entity_counts.most_common(50)] # Top 50 entities to keep graph readable

    # Build edges based on sentence co-occurrence
    edges = []
    for sent in doc.sents:
        sent_ents = [ent.text.strip() for ent in sent.ents if ent.text.strip() in common_entities]
        # sent_ents.extend([token.text for token in sent if token.text in common_entities]) 
        sent_ents = list(set(sent_ents)) # Unique per sentence
        
        for i in range(len(sent_ents)):
            for j in range(i + 1, len(sent_ents)):
                edges.append(tuple(sorted((sent_ents[i], sent_ents[j]))))

    edge_counts = Counter(edges)

    # Create Graph
    G = nx.Graph()
    
    for entity in common_entities:
        G.add_node(entity, size=entity_counts[entity])

    for (src, dst), weight in edge_counts.items():
        G.add_edge(src, dst, weight=weight)

    # Remove isolated nodes
    G.remove_nodes_from(list(nx.isolates(G)))

    return G

def visualize_graph_pyvis(G, input_file):
    """Generates an interactive graph using pyvis with specific styling."""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join("artifacts", f"{base_name}.html")

    os.makedirs("artifacts", exist_ok=True)
    
    # Use dark background as requested
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", notebook=False)
    
    # Set physics layout
    net.force_atlas_2based()
    
    friendly_podcast_name = get_friendly_name(input_file)
    
    default_color = '#4a90e2' # Proportional blue
    highlight_color = '#f5a623' # Proportional orange
    edge_color = 'rgba(200, 200, 200, 0.1)'
    
    for node, data in G.nodes(data=True):
        count = data.get('size', 1)
        net.add_node(
            node, 
            label=node, # SHOW labels by default
            value=count, # Natural scaling
            transcripts=friendly_podcast_name, # Pass it to the JS panel
            color={
                "background": default_color,
                "border": "#2c3e50",
                "highlight": {"background": highlight_color, "border": "#d35400"},
                "hover": {"background": "#5dade2", "border": "#2c3e50"}
            }
        )
        
    for src, dst, data in G.edges(data=True):
        weight = data.get('weight', 1)
        net.add_edge(
            src, 
            dst, 
            value=weight, 
            color={"color": edge_color, "highlight": highlight_color, "opacity": 0.2}
        )
        
    net.set_options("""
    var options = {
      "physics": {
        "enabled": false
      },
      "interaction": {
        "hover": false,
        "navigationButtons": true,
        "multiselect": true
      },
      "nodes": {
        "scaling": {
          "min": 10,
          "max": 50
        }
      },
      "edges": {
        "smooth": {
          "type": "continuous",
          "forceDirection": "none"
        }
      }
    }
    """)
    
    net.write_html(output_file)
    
    # Inject neighbor highlight script to match the requested styling behavior
    with open(output_file, 'r') as f:
        html = f.read()
        
    # Create a nice overlay style and script (Simplified for single graphs)
    custom_style = """
</style>
<div style="position: absolute; top: 20px; left: 20px; z-index: 1000;">
    <button id="physics-toggle" style="
        background: rgba(245, 166, 35, 0.9);
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 4px;
        cursor: pointer;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    " onclick="togglePhysics()">
        Physics: <span id="physics-status">OFF</span>
    </button>
</div>
<script type="text/javascript">
    let physicsEnabled = false;
    
    function togglePhysics() {
        physicsEnabled = !physicsEnabled;
        network.setOptions({ physics: { enabled: physicsEnabled } });
        document.getElementById('physics-status').innerText = physicsEnabled ? 'ON' : 'OFF';
        document.getElementById('physics-toggle').style.background = physicsEnabled ? 
            'rgba(74, 144, 226, 0.9)' : 'rgba(245, 166, 35, 0.9)';
    }

    network.on("click", function (params) {
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            
            // Highlight neighbors logic
            var connectedNodes = network.getConnectedNodes(nodeId);
            var allNodes = nodes.get();
            var nodesToUpdate = [];
            
            allNodes.forEach(function(node) {
                if (node.id === nodeId) {
                    node.color = { background: '#f5a623', border: '#d35400' };
                    node.label = node.id;
                } else if (connectedNodes.includes(node.id)) {
                    node.color = { background: '#5dade2', border: '#2c3e50' };
                    node.label = node.id;
                } else {
                    node.color = { background: 'rgba(74, 144, 226, 0.2)', border: 'rgba(44, 62, 80, 0.2)' };
                    node.label = node.id;
                }
                nodesToUpdate.push(node);
            });
            nodes.update(nodesToUpdate);
            
        } else {
            // Reset colors
            var allNodes = nodes.get();
            var nodesToUpdate = [];
            allNodes.forEach(function(node) {
                node.color = { background: '#4a90e2', border: '#2c3e50' };
                node.label = node.id;
                nodesToUpdate.push(node);
            });
            nodes.update(nodesToUpdate);
        }
    });
</script>
"""

    html = html.replace('</body>', custom_style + '</body>')
    
    with open(output_file, 'w') as f:
        f.write(html)
        
    print(f"Pyvis graph saved to {output_file}")

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Build semantic graph from transcript file")
    parser.add_argument("input_file", help="Path to the transcript file")
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"{args.input_file} not found.")
    else:
        print("Building graph...")
        G = build_semantic_graph(args.input_file)
        print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
        visualize_graph_pyvis(G, args.input_file)
