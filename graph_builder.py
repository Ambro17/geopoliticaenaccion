import spacy
import networkx as nx
import re
from collections import Counter
import pandas as pd
import os
import glob
from pyvis.network import Network

# Load Spanish model
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    try:
        # Try to load from local directory if downloaded manually
        import sys
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

def extract_entities_from_text(text):
    cleaned_text = clean_text(text)
    doc = nlp(cleaned_text)

    entities = []
    invalid_pos = {'VERB', 'AUX', 'SCONJ', 'CCONJ', 'INTJ', 'ADV', 'PRON', 'DET', 'ADP', 'PART'}
    repeated_char_pattern = re.compile(r'(.)\1{2,}|[hm]\1+$|^\W+$')
    vocalization_pattern = re.compile(r'^(?:[aeiouáéíóúü]+[hms]*|[hms]+[aeiouáéíóúü]*)$', re.IGNORECASE)

    for ent in doc.ents:
        if ent.label_ not in ['PER', 'ORG', 'LOC', 'MISC']:
            continue
        if all(token.is_stop for token in ent):
            continue
        if any(token.pos_ in {'VERB', 'AUX', 'INTJ', 'ADV', 'SCONJ', 'CCONJ'} for token in ent):
             continue
        if any(token.pos_ == 'PRON' for token in ent):
            continue

        if len(ent) > 1 and ent[0].pos_ == 'DET':
            cleaned_ent = " ".join([t.text for t in ent[1:]]).strip()
        else:
            cleaned_ent = " ".join(ent.text.split())
            
        cleaned_ent = cleaned_ent.title()
        
        if repeated_char_pattern.search(cleaned_ent):
            continue
        if len(cleaned_ent) < 4 and vocalization_pattern.match(cleaned_ent):
            continue
        if len(cleaned_ent) < 2:
            continue
            
        if len(ent) == 1:
            token = ent[0]
            if token.pos_ not in {'NOUN', 'PROPN'}:
                continue
            if token.dep_ in ['advmod', 'intj', 'cc', 'det', 'prep', 'aux', 'punct', 'mark']:
                continue

        entities.append(cleaned_ent)

    return entities, doc

# Hardcoded mapping from transcript filename to display name
TRANSCRIPT_FRIENDLY_NAMES = {
    "2025-07-13-Malvinas.txt": "Malvinas",
    "2025-08-06-China.txt": "China",
    "2025-08-16-CementerioDeImperios.txt": "Primera Guerra Mundial",
    "2025-08-27-2da-Guerra-Mundial.txt": "Segunda Guerra Mundial",
    "2025-10-4-Medio-Oriente.txt": "Medio Oriente",
    "2025-12-16-Chile.txt": "Chile",
    "2026-01-11-Venezuela.txt": "Venezuela",
}


def build_global_graph(transcript_dir="artifacts"):
    all_files = glob.glob(os.path.join(transcript_dir, "*.txt"))

    global_entity_counts = Counter()
    entity_to_transcripts = {} # entity -> set of filenames

    # We'll store (src, dst, transcript) for edges
    all_edges_with_source = []

    for file_path in all_files:
        base_name = os.path.basename(file_path)
        friendly_name = TRANSCRIPT_FRIENDLY_NAMES.get(base_name, get_friendly_name(base_name))
        print(f"Processing {friendly_name} ({base_name})...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        entities, doc = extract_entities_from_text(text)
        
        # Track entities per file
        unique_entities_in_file = set(entities)
        for ent in unique_entities_in_file:
            if ent not in entity_to_transcripts:
                entity_to_transcripts[ent] = set()
            entity_to_transcripts[ent].add(friendly_name)
            
        global_entity_counts.update(entities)
        
        # Build local edges to aggregate later
        for sent in doc.sents:
            sent_ents = [ent.text.strip().title() for ent in sent.ents]
            # Normalize them as we did in extraction
            normalized_sent_ents = []
            for e in sent_ents:
                clean_e = " ".join(e.split())
                if len(clean_e) > 2:
                    normalized_sent_ents.append(clean_e)
            
            normalized_sent_ents = list(set(normalized_sent_ents))
            
            for i in range(len(normalized_sent_ents)):
                for j in range(i + 1, len(normalized_sent_ents)):
                    pair = tuple(sorted((normalized_sent_ents[i], normalized_sent_ents[j])))
                    all_edges_with_source.append(pair)

    # Filter top 75 global entities
    top_75_entities = [e for e, c in global_entity_counts.most_common(75)]
    top_75_set = set(top_75_entities)

    # Final Graph
    G = nx.Graph()
    for entity in top_75_entities:
        G.add_node(entity, 
                   size=global_entity_counts[entity], 
                   transcripts=", ".join(sorted(list(entity_to_transcripts.get(entity, set())))))

    # Filter edges to only include top 75
    filtered_edges = [edge for edge in all_edges_with_source if edge[0] in top_75_set and edge[1] in top_75_set]
    edge_counts = Counter(filtered_edges)

    for (src, dst), weight in edge_counts.items():
        G.add_edge(src, dst, weight=weight)

    # Remove isolated nodes
    G.remove_nodes_from(list(nx.isolates(G)))
    
    return G

def build_semantic_graph(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    cleaned_text = clean_text(raw_text)
    doc = nlp(cleaned_text)

    # Extract entities and top nouns
    entities = []
    
    # Define invalid POS tags for semantic nodes (we want nouns/proper nouns)
    invalid_pos = {'VERB', 'AUX', 'SCONJ', 'CCONJ', 'INTJ', 'ADV', 'PRON', 'DET', 'ADP', 'PART'}

    # Regex for repeated characters (e.g., "Ehh", "Mmm", "Aha")
    repeated_char_pattern = re.compile(r'(.)\1{2,}|[hm]\1+$|^\W+$')
    
    # Regex for vocalizations (vowels + h/m/s combinations) e.g., "Ah", "Eh", "Uh", "Mm", "Sh"
    vocalization_pattern = re.compile(r'^(?:[aeiouáéíóúü]+[hms]*|[hms]+[aeiouáéíóúü]*)$', re.IGNORECASE)

    for ent in doc.ents:
        # 1. Filter by Entity Type
        if ent.label_ not in ['PER', 'ORG', 'LOC', 'MISC']:
            continue
            
        # 2. Check if entirely stop words
        if all(token.is_stop for token in ent):
            continue

        # 3. Analyze composition using NLP primitives
        if any(token.pos_ in {'VERB', 'AUX', 'INTJ', 'ADV', 'SCONJ', 'CCONJ'} for token in ent):
             continue

        # Check for Pronouns
        if any(token.pos_ == 'PRON' for token in ent):
            continue

        # Advanced Entity Merging: strip leading determiners
        if len(ent) > 1 and ent[0].pos_ == 'DET':
            cleaned_ent = " ".join([t.text for t in ent[1:]]).strip()
        else:
            cleaned_ent = " ".join(ent.text.split())
            
        cleaned_ent = cleaned_ent.title()
        
        # 4. Phonetic / Structural Filtering
        if repeated_char_pattern.search(cleaned_ent):
            continue
            
        if len(cleaned_ent) < 4 and vocalization_pattern.match(cleaned_ent):
            continue

        if len(cleaned_ent) < 2:
            continue
            
        # For single words, strict POS check
        if len(ent) == 1:
            token = ent[0]
            if token.pos_ not in {'NOUN', 'PROPN'}:
                continue
            if token.dep_ in ['advmod', 'intj', 'cc', 'det', 'prep', 'aux', 'punct', 'mark']:
                continue

        entities.append(cleaned_ent)

    # Filter very common words or noise if needed and ensure length > 2
    entities = [e for e in entities if len(e) > 2]
    
    entity_counts = Counter(entities)
    common_entities = [e for e, c in entity_counts.most_common(50)] # Top 50 entities

    # Build edges based on sentence co-occurrence
    edges = []
    for sent in doc.sents:
        sent_ents = [ent.text.strip() for ent in sent.ents if ent.text.strip() in common_entities]
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

def get_physics_options(enabled=True):
    """Get physics options for the graph"""
    if enabled:
        return """
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -300,
          "centralGravity": 0.005,
          "springLength": 250,
          "springConstant": 0.08,
          "damping": 0.5
        },
        "maxVelocity": 5,
        "minVelocity": 0.1,
        "solver": "forceAtlas2Based",
        "timestep": 0.05,
        "stabilization": { 
          "enabled": true,
          "iterations": 1000,
          "updateInterval": 50
        },
        "enabled": true
      }"""
    else:
        return """
      "physics": {
        "enabled": false
      }"""

def visualize_graph(G, output_file, is_global=False):
    """Generates an interactive graph using pyvis with configurable physics."""
    os.makedirs("artifacts", exist_ok=True)
    
    # Height/width and dark theme
    net = Network(height="800px", width="100%", bgcolor="#1a1a1a", font_color="white", notebook=False)
    
    # Set physics based on graph type
    physics_enabled = is_global  # True for global, False for regular
    
    default_color = '#4a90e2'
    highlight_color = '#f5a623'
    edge_color = 'rgba(200, 200, 200, 0.1)'
    
    for node, data in G.nodes(data=True):
        count = data.get('size', 1)
        transcripts = data.get('transcripts', '')
        
        # For global graphs, hide labels by default, show for regular graphs
        label = " " if is_global else node
        
        net.add_node(
            node,
            label=label,
            title=node, # Native tooltip on hover
            value=count,
            transcripts=transcripts,
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

    physics_options = get_physics_options(physics_enabled)
    
    net.set_options(f"""
    var options = {{
      {physics_options},
      "interaction": {{
        "hover": {str(is_global).lower()},
        "navigationButtons": true,
        "multiselect": true
      }},
      "nodes": {{
        "scaling": {{
          "min": 10,
          "max": 50
        }}
      }},
      "edges": {{
        "smooth": {{
          "type": "continuous",
          "forceDirection": "none"
        }}
      }}
    }}
    """)
    
    net.write_html(output_file)
    
    # Inject Custom JavaScript for physics toggle and tooltips
    with open(output_file, 'r') as f:
        html = f.read()

    # Add physics toggle button
    initial_state = "ON" if physics_enabled else "OFF"
    initial_bg = "rgba(74, 144, 226, 0.9)" if physics_enabled else "rgba(245, 166, 35, 0.9)"
    
    toggle_button = f"""
<div style="position: absolute; top: 20px; left: 20px; z-index: 1000;">
    <button id="physics-toggle" style="
        background: {initial_bg};
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
        Physics: <span id="physics-status">{initial_state}</span>
    </button>
</div>
"""

    # Add tooltip panel (only for global graphs)
    if is_global:
        custom_style = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Oswald:wght@400;700&display=swap');

    #node-info-panel {
        position: absolute;
        top: 20px;
        right: 20px;
        width: 320px;
        padding: 25px;
        background: rgba(15, 23, 42, 0.95);
        color: #e2e8f0;
        border-radius: 4px;
        box-shadow: 0 0 30px rgba(0,0,0,0.8);
        display: none;
        z-index: 1000;
        font-family: 'IBM Plex Mono', monospace;
        border: 1px solid rgba(212, 175, 55, 0.4);
        backdrop-filter: blur(8px);
    }
    #node-info-panel h3 {
        margin-top: 0;
        color: #d4af37;
        font-family: 'Oswald', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 1px solid rgba(212, 175, 55, 0.2);
        padding-bottom: 10px;
        font-size: 20px;
    }
    #node-info-panel .data-label {
        font-weight: bold;
        color: #d4af37;
        margin-top: 15px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    #node-info-panel .transcript-list {
        margin-top: 8px;
        font-size: 12px;
        line-height: 1.6;
        color: #94a3b8;
    }
    .transcript-bullet {
        color: #33C1FF;
        margin-right: 8px;
    }
    .close-panel {
        float: right;
        cursor: pointer;
        font-weight: bold;
        color: #94a3b8;
        font-size: 20px;
    }
    .close-panel:hover {
        color: #d4af37;
    }
</style>
<div id="node-info-panel">
    <span class="close-panel" onclick="document.getElementById('node-info-panel').style.display='none'">×</span>
    <h3 id="panel-node-name">NODE_IDENTIFIER</h3>
    <div class="data-label">Mencionado en:</div>
    <div id="panel-transcripts" class="transcript-list"></div>
</div>
"""
    else:
        custom_style = ""

    script_injection = f"""
<script type="text/javascript">
    let physicsEnabled = {str(physics_enabled).lower()};

    function togglePhysics() {{
        physicsEnabled = !physicsEnabled;
        network.setOptions({{ physics: {{ enabled: physicsEnabled }} }});
        document.getElementById('physics-status').innerText = physicsEnabled ? 'ON' : 'OFF';
        document.getElementById('physics-toggle').style.background = physicsEnabled ?
            'rgba(74, 144, 226, 0.9)' : 'rgba(245, 166, 35, 0.9)';
    }}

    network.on("click", function (params) {{
        var panel = document.getElementById('node-info-panel');
        if (params.nodes.length > 0) {{
            var nodeId = params.nodes[0];
            var nodeData = nodes.get(nodeId);

            {"// Update panel for global graphs" if is_global else ""}
            {"document.getElementById('panel-node-name').innerText = nodeId;" if is_global else ""}

            {"// Format transcripts as a list" if is_global else ""}
            {"var transcriptList = nodeData.transcripts || '';" if is_global else ""}
            {"var transcripts = transcriptList.split(', ');" if is_global else ""}
            {"var formattedTranscripts = transcripts.map(t => '<span class=\"transcript-bullet\">&bull;</span>' + t).join('<br>');" if is_global else ""}
            {"document.getElementById('panel-transcripts').innerHTML = formattedTranscripts || 'N/A';" if is_global else ""}

            {"panel.style.display = 'block';" if is_global else ""}

            // Highlight neighbors logic
            var connectedNodes = network.getConnectedNodes(nodeId);
            var allNodes = nodes.get();
            var nodesToUpdate = [];

            allNodes.forEach(function(node) {{
                if (node.id === nodeId) {{
                    node.color = {{ background: '#f5a623', border: '#d35400' }};
                    node.label = node.id; // Show label for selected node
                }} else if (connectedNodes.includes(node.id)) {{
                    node.color = {{ background: '#5dade2', border: '#2c3e50' }};
                    node.label = node.id; // Show label for neighbors
                }} else {{
                    node.color = {{ background: 'rgba(74, 144, 226, 0.2)', border: 'rgba(44, 62, 80, 0.2)' }};
                    node.label = {"''" if is_global else "node.id"}; // Keep hidden for global, restore for regular
                }}
                nodesToUpdate.push(node);
            }});
            nodes.update(nodesToUpdate);

        }} else {{
            {"panel.style.display = 'none';" if is_global else ""}
            // Reset colors and hide labels
            var allNodes = nodes.get();
            var nodesToUpdate = [];
            allNodes.forEach(function(node) {{
                node.color = {{ background: '#4a90e2', border: '#2c3e50' }};
                node.label = {"''" if is_global else "node.id"};
                nodesToUpdate.push(node);
            }});
            nodes.update(nodesToUpdate);
        }}
    }});
</script>
"""

    html = html.replace('</body>', toggle_button + custom_style + script_injection + '</body>')
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Graph saved to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build semantic graphs")
    parser.add_argument("--global-graph", action="store_true", help="Build global graph")
    parser.add_argument("--input", help="Path to single transcript file")
    args = parser.parse_args()
    
    if args.global_graph:
        print("Building global semantic graph...")
        G = build_global_graph()
        print(f"Global graph constructed with {len(G.nodes())} nodes and {len(G.edges())} edges.")
        visualize_graph(G, "artifacts/global_graph.html", is_global=True)
    elif args.input:
        if not os.path.exists(args.input):
            print(f"{args.input} not found.")
        else:
            print("Building graph...")
            G = build_semantic_graph(args.input)
            print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            output_file = os.path.join("artifacts", f"{base_name}.html")
            visualize_graph(G, output_file, is_global=False)
    else:
        print("Please specify either --global-graph or --input <file>")
