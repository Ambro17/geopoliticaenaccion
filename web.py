from flask import Flask, render_template, jsonify
import os
import json
from pathlib import Path
from build_graph import build_semantic_graph
import networkx as nx

app = Flask(__name__)

TRANSCRIPTS_DIR = Path("transcripts")
GRAPHS_DIR = Path("graphs")


def get_available_transcripts():
    """Get list of all transcript files."""
    if not TRANSCRIPTS_DIR.exists():
        return []
    
    transcripts = []
    for file in TRANSCRIPTS_DIR.glob("*.txt"):
        transcripts.append({
            "name": file.stem,
            "filename": file.name,
            "size": file.stat().st_size
        })
    return sorted(transcripts, key=lambda x: x["name"])


def graph_to_json(G):
    """Convert NetworkX graph to JSON format for vis.js."""
    nodes = []
    for node in G.nodes():
        size = G.nodes[node]['size']
        nodes.append({
            "id": node,
            "label": node,
            "title": f"Frequency: {size}",
            "value": size,
            "font": {"color": "white"}
        })
    
    edges = []
    for src, dst, data in G.edges(data=True):
        weight = data['weight']
        edges.append({
            "from": src,
            "to": dst,
            "value": weight,
            "title": f"Co-occurrences: {weight}"
        })
    
    return {"nodes": nodes, "edges": edges}


@app.route('/')
def index():
    """Main page."""
    transcripts = get_available_transcripts()
    return render_template('index.html', transcripts=transcripts)


@app.route('/api/graph/<transcript_name>')
def get_graph(transcript_name):
    """Generate and return graph data for a transcript."""
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_name}.txt"
    
    if not transcript_path.exists():
        return jsonify({"error": "Transcript not found"}), 404
    
    try:
        # Build graph from transcript
        G = build_semantic_graph(str(transcript_path))
        
        # Convert to JSON
        graph_data = graph_to_json(G)
        
        return jsonify({
            "success": True,
            "graph": graph_data,
            "stats": {
                "nodes": len(G.nodes()),
                "edges": len(G.edges())
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("Starting web server...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
