import os
from pathlib import Path
from transcribe import transcribe_audio
from build_graph import build_semantic_graph, visualize_graph_pyvis

def process_podcasts():
    podcast_dir = Path("podcasts")
    transcript_dir = Path("transcripts")
    graph_dir = Path("graphs")
    
    os.makedirs(transcript_dir, exist_ok=True)
    os.makedirs(graph_dir, exist_ok=True)
    
    podcasts = list(podcast_dir.glob("*.mp3"))
    print(f"Found {len(podcasts)} podcasts.")
    
    for podcast_path in podcasts:
        print(f"\nProcessing: {podcast_path.name}")
        base_name = podcast_path.stem
        
        # 1. Look for existing transcript
        transcripts = list(transcript_dir.glob(f"{base_name}*.txt"))
        
        if not transcripts:
            print(f"No transcript found for {base_name}. Skipping.")
            continue
        else:
            # Prefer transcripts without _tiny if multiple exist, or just take first
            transcript_path = transcripts[0]
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
