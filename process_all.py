import os
from pathlib import Path
from transcribe import transcribe_audio
from build_graph import build_semantic_graph, visualize_graph_pyvis

def process_podcasts():
    artifacts_dir = Path("artifacts")

    os.makedirs(artifacts_dir, exist_ok=True)

    podcasts = list(artifacts_dir.glob("*.mp3"))
    print(f"Found {len(podcasts)} podcasts.")

    for podcast_path in podcasts:
        print(f"\nProcessing: {podcast_path.name}")
        base_name = podcast_path.stem

        # 1. Look for existing transcript
        transcript_path = artifacts_dir / f"{base_name}.txt"

        if not transcript_path.exists():
            print(f"No transcript found for {base_name}. Skipping.")
            continue
        else:
            print(f"Using existing transcript: {transcript_path.name}")
            
        if transcript_path and transcript_path.exists():
            # 2. Build Graph
            print(f"Building graph for {transcript_path.name}...")
            G = build_semantic_graph(transcript_path)
            print(f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges.")
            visualize_graph_pyvis(G, transcript_path)
        else:
            print(f"Failed to find or create transcript for {base_name}")

if __name__ == "__main__":
    process_podcasts()
