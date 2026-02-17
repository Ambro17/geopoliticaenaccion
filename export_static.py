#!/usr/bin/env python3
"""
Export static version of the web app.
Generates all graphs as JSON files and creates a static HTML page.
"""

import json
from pathlib import Path
from build_graph import build_semantic_graph
import shutil

TRANSCRIPTS_DIR = Path("transcripts")
OUTPUT_DIR = Path("static_site")
GRAPHS_OUTPUT = OUTPUT_DIR / "graphs"


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


def export_static():
    """Generate static site with pre-built graphs."""
    
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    GRAPHS_OUTPUT.mkdir(exist_ok=True)
    
    print("🔍 Finding transcripts...")
    transcripts = []
    
    for transcript_file in sorted(TRANSCRIPTS_DIR.glob("*.txt")):
        name = transcript_file.stem
        print(f"📊 Building graph for: {name}")
        
        try:
            # Build graph
            G = build_semantic_graph(str(transcript_file))
            
            # Convert to JSON
            graph_data = graph_to_json(G)
            
            # Save graph JSON
            graph_json_path = GRAPHS_OUTPUT / f"{name}.json"
            with open(graph_json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "graph": graph_data,
                    "stats": {
                        "nodes": len(G.nodes()),
                        "edges": len(G.edges())
                    }
                }, f, ensure_ascii=False, indent=2)
            
            # Add to transcript list
            transcripts.append({
                "name": name,
                "size": transcript_file.stat().st_size
            })
            
            print(f"  ✓ {len(G.nodes())} nodes, {len(G.edges())} edges")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Create static HTML
    print("\n📝 Creating static HTML...")
    create_static_html(transcripts)
    
    print(f"\n✅ Static site created in: {OUTPUT_DIR}")
    print(f"📂 Open {OUTPUT_DIR}/index.html in your browser")


def create_static_html(transcripts):
    """Create static HTML file with embedded transcript list."""
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geopolitical Podcast Visualizer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" />
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            display: grid;
            grid-template-columns: 300px 1fr;
            min-height: 90vh;
        }

        .sidebar {
            background: #2d3748;
            color: white;
            padding: 30px 20px;
        }

        .sidebar h1 {
            font-size: 24px;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .sidebar p {
            font-size: 14px;
            color: #a0aec0;
            margin-bottom: 30px;
        }

        .transcript-list {
            list-style: none;
        }

        .transcript-item {
            padding: 12px 16px;
            margin-bottom: 8px;
            background: #1a202c;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }

        .transcript-item:hover {
            background: #4a5568;
            transform: translateX(4px);
        }

        .transcript-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
        }

        .transcript-name {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }

        .transcript-size {
            font-size: 12px;
            color: #a0aec0;
        }

        .main-content {
            padding: 40px;
            background: #f7fafc;
        }

        .header {
            margin-bottom: 30px;
        }

        .header h2 {
            font-size: 32px;
            color: #2d3748;
            margin-bottom: 10px;
        }

        .stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }

        .stat-box {
            background: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .stat-label {
            font-size: 12px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
            margin-top: 5px;
        }

        #graph-container {
            background: #1a202c;
            border-radius: 12px;
            height: 600px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            position: relative;
        }

        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: white;
        }

        .spinner {
            border: 4px solid rgba(255,255,255,0.1);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .placeholder {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #a0aec0;
            font-size: 18px;
        }

        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <h1>🌍 GeoPolVis</h1>
            <p>Podcast Semantic Graphs</p>
            
            <ul class="transcript-list" id="transcript-list">
                <!-- Populated by JavaScript -->
            </ul>
        </div>

        <div class="main-content">
            <div class="header">
                <h2 id="selected-title">Select a Podcast</h2>
                <div class="stats hidden" id="stats">
                    <div class="stat-box">
                        <div class="stat-label">Entities</div>
                        <div class="stat-value" id="nodes-count">0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Connections</div>
                        <div class="stat-value" id="edges-count">0</div>
                    </div>
                </div>
            </div>

            <div id="graph-container">
                <div class="placeholder" id="placeholder">
                    👈 Select a podcast transcript to view its semantic graph
                </div>
                <div class="loading hidden" id="loading">
                    <div class="spinner"></div>
                    <div>Loading graph...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Embedded transcript data
        const TRANSCRIPTS = ''' + json.dumps(transcripts) + ''';
        
        let network = null;

        // Populate transcript list
        const listEl = document.getElementById('transcript-list');
        TRANSCRIPTS.forEach(transcript => {
            const li = document.createElement('li');
            li.className = 'transcript-item';
            li.dataset.name = transcript.name;
            li.innerHTML = `
                <div class="transcript-name">${transcript.name}</div>
                <div class="transcript-size">${(transcript.size / 1024).toFixed(1)} KB</div>
            `;
            li.addEventListener('click', () => loadGraph(transcript.name, li));
            listEl.appendChild(li);
        });

        async function loadGraph(transcriptName, itemEl) {
            // Update UI
            document.querySelectorAll('.transcript-item').forEach(i => i.classList.remove('active'));
            itemEl.classList.add('active');
            document.getElementById('selected-title').textContent = transcriptName;
            
            // Show loading
            document.getElementById('placeholder').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');
            document.getElementById('stats').classList.add('hidden');
            
            try {
                // Fetch pre-generated graph JSON
                const response = await fetch(`graphs/${transcriptName}.json`);
                const data = await response.json();
                
                // Update stats
                document.getElementById('nodes-count').textContent = data.stats.nodes;
                document.getElementById('edges-count').textContent = data.stats.edges;
                document.getElementById('stats').classList.remove('hidden');
                
                // Render graph
                renderGraph(data.graph);
            } catch (error) {
                alert('Failed to load graph: ' + error.message);
            } finally {
                document.getElementById('loading').classList.add('hidden');
            }
        }

        function renderGraph(graphData) {
            const container = document.getElementById('graph-container');
            
            const nodes = new vis.DataSet(graphData.nodes);
            const edges = new vis.DataSet(graphData.edges);
            
            const data = { nodes, edges };
            
            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: {
                        min: 10,
                        max: 40
                    },
                    color: {
                        background: '#667eea',
                        border: '#764ba2',
                        highlight: {
                            background: '#48bb78',
                            border: '#38a169'
                        }
                    }
                },
                edges: {
                    color: {
                        color: 'rgba(255,255,255,0.2)',
                        highlight: 'rgba(255,255,255,0.6)'
                    },
                    smooth: {
                        type: 'continuous'
                    },
                    scaling: {
                        min: 1,
                        max: 5
                    }
                },
                physics: {
                    stabilization: {
                        iterations: 200
                    },
                    barnesHut: {
                        gravitationalConstant: -8000,
                        springConstant: 0.04,
                        springLength: 95
                    }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 100
                }
            };
            
            if (network) {
                network.destroy();
            }
            
            network = new vis.Network(container, data, options);
        }
    </script>
</body>
</html>'''
    
    with open(OUTPUT_DIR / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    export_static()
