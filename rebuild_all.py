import os
from pathlib import Path
from build_graph import build_semantic_graph, visualize_graph_pyvis

def rebuild_all():
    transcript_dir = Path("transcripts")
    graph_dir = Path("graphs")
    
    os.makedirs(graph_dir, exist_ok=True)
    
    transcripts = list(transcript_dir.glob("*.txt"))
    print(f"Found {len(transcripts)} transcripts in {transcript_dir}.")
    
    for transcript_path in transcripts:
        print(f"\n--- Rebuilding graph for: {transcript_path.name} ---")
        try:
            G = build_semantic_graph(transcript_path)
            print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
            visualize_graph_pyvis(G, transcript_path)
        except Exception as e:
            print(f"Error processing {transcript_path.name}: {e}")

if __name__ == "__main__":
    rebuild_all()
