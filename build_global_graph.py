import spacy
import networkx as nx
import re
from collections import Counter
import os
import glob
from pyvis.network import Network

# Load Spanish model
try:
    nlp = spacy.load("es_core_news_lg")
except OSError:
    print("Downloading language model...")
    from spacy.cli import download
    download("es_core_news_lg")
    nlp = spacy.load("es_core_news_lg")

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

def build_global_graph(transcript_dir="transcripts"):
    all_files = glob.glob(os.path.join(transcript_dir, "*.txt"))
    
    global_entity_counts = Counter()
    entity_to_transcripts = {} # entity -> set of filenames
    
    # We'll store (src, dst, transcript) for edges
    all_edges_with_source = []

    for file_path in all_files:
        base_name = os.path.basename(file_path)
        friendly_name = get_friendly_name(base_name)
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
        # We only care about entities that ARE entities in this specific doc
        # But we filter by top 75 GLOBAL frequencies later.
        # So for now, we collect all potential edges.
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

def visualize_global_graph(G, output_file="graphs/global_graph.html"):
    os.makedirs("graphs", exist_ok=True)
    
    # Height/width and dark theme
    net = Network(height="800px", width="100%", bgcolor="#1a1a1a", font_color="white", notebook=False)
    
    net.force_atlas_2based()
    
    default_color = '#4a90e2' # A nice blue
    highlight_color = '#f5a623' # A nice orange
    edge_color = 'rgba(200, 200, 200, 0.1)'
    
    for node, data in G.nodes(data=True):
        count = data.get('size', 1)
        transcripts = data.get('transcripts', '')
        
        net.add_node(
            node,
            label=" ", # HIDE labels to avoid clutter by using a space
            title=node, # Native tooltip on hover (just the name)
            value=count, # Size by absolute frequency
            transcripts=transcripts, # Store for custom JS
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
      },
      "interaction": {
        "hover": true,
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
    
    # Inject Custom Tooltip Logic
    with open(output_file, 'r') as f:
        html = f.read()

    # Create a nice overlay style and script
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
    <div class="data-label">STRATEGIC_SOURCE_MAPPING:</div>
    <div id="panel-transcripts" class="transcript-list"></div>
</div>
"""

    script_injection = """
<script type="text/javascript">
    network.on("click", function (params) {
        var panel = document.getElementById('node-info-panel');
        if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            var nodeData = nodes.get(nodeId);
            
            document.getElementById('panel-node-name').innerText = nodeId;
            
            // Format transcripts as a list
            var transcriptList = nodeData.transcripts || "";
            var transcripts = transcriptList.split(', ');
            var formattedTranscripts = transcripts.map(t => '<span class="transcript-bullet">•</span>' + t).join('<br>');
            document.getElementById('panel-transcripts').innerHTML = formattedTranscripts || "N/A";
            
            panel.style.display = 'block';
            
            // Highlight neighbors logic
            var connectedNodes = network.getConnectedNodes(nodeId);
            var allNodes = nodes.get();
            var nodesToUpdate = [];
            
            allNodes.forEach(function(node) {
                if (node.id === nodeId) {
                    node.color = { background: '#f5a623', border: '#d35400' };
                    node.label = node.id; // Show label for selected node
                } else if (connectedNodes.includes(node.id)) {
                    node.color = { background: '#5dade2', border: '#2c3e50' };
                    node.label = node.id; // Show label for neighbors
                } else {
                    node.color = { background: 'rgba(74, 144, 226, 0.2)', border: 'rgba(44, 62, 80, 0.2)' };
                    node.label = " "; // Keep hidden
                }
                nodesToUpdate.push(node);
            });
            nodes.update(nodesToUpdate);
            
        } else {
            panel.style.display = 'none';
            // Reset colors and hide labels
            var allNodes = nodes.get();
            var nodesToUpdate = [];
            allNodes.forEach(function(node) {
                node.color = { background: '#4a90e2', border: '#2c3e50' };
                node.label = " ";
                nodesToUpdate.push(node);
            });
            nodes.update(nodesToUpdate);
        }
    });
</script>
"""
    html = html.replace('</body>', custom_style + script_injection + '</body>')
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Global graph saved to {output_file}")

if __name__ == "__main__":
    print("Building global semantic graph...")
    G = build_global_graph()
    print(f"Global graph constructed with {len(G.nodes())} nodes and {len(G.edges())} edges.")
    visualize_global_graph(G)
