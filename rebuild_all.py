import os
from pathlib import Path
from graph_builder import build_semantic_graph, visualize_graph, build_global_graph

def rebuild_all():
    artifacts_dir = Path("artifacts")

    os.makedirs(artifacts_dir, exist_ok=True)

    # Build global graph first
    print("\n=== Building Global Graph ===")
    try:
        G = build_global_graph()
        print(f"Global graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
        visualize_graph(G, "artifacts/global_graph.html", is_global=True)
    except Exception as e:
        print(f"Error building global graph: {e}")

    # Build individual transcript graphs
    transcripts = list(artifacts_dir.glob("*.txt"))
    print(f"\n=== Building Individual Graphs ===")
    print(f"Found {len(transcripts)} transcripts in {artifacts_dir}.")
    
    for transcript_path in transcripts:
        print(f"\n--- Rebuilding graph for: {transcript_path.name} ---")
        try:
            G = build_semantic_graph(transcript_path)
            print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
            base_name = transcript_path.stem
            output_file = f"artifacts/{base_name}.html"
            visualize_graph(G, output_file, is_global=False)
        except Exception as e:
            print(f"Error processing {transcript_path.name}: {e}")

if __name__ == "__main__":
    rebuild_all()
