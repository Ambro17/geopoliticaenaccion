"""
Single source of truth for podcast artifacts including paths and metadata.
"""

PODCAST_ARTIFACTS = {
    "Malvinas": {
        "friendly_name": "Malvinas",
        "mp3_path": "artifacts/2025-07-13-Malvinas.mp3",
        "transcript_path": "artifacts/2025-07-13-Malvinas.txt",
        "graph_path": "artifacts/2025-07-13-Malvinas.html",
        "podcast_link": "https://open.spotify.com/episode/7FfjFupRwnBGzyglzmoJxv?si=e43d4a60254f4613"
    },
    "China": {
        "friendly_name": "China",
        "mp3_path": "artifacts/2025-08-06-China.mp3",
        "transcript_path": "artifacts/2025-08-06-China.txt",
        "graph_path": "artifacts/2025-08-06-China.html",
        "podcast_link": "https://open.spotify.com/episode/5rLShslMsHiNlsLOVAGuFe?si=0e532ca5d5a745a3"
    },
    "PrimeraGuerraMundial": {
        "friendly_name": "Primera Guerra Mundial",
        "mp3_path": "artifacts/2025-08-16-CementerioDeImperios.mp3",
        "transcript_path": "artifacts/2025-08-16-CementerioDeImperios.txt",
        "graph_path": "artifacts/2025-08-16-CementerioDeImperios.html",
        "podcast_link": "https://open.spotify.com/episode/49tSr9ktzubhP5vkWI9W6M?si=b3bb08c3a7ee4f7c"
    },
    "SegundaGuerraMundial": {
        "friendly_name": "Segunda Guerra Mundial",
        "mp3_path": "artifacts/2025-08-27-2da-Guerra-Mundial.mp3",
        "transcript_path": "artifacts/2025-08-27-2da-Guerra-Mundial.txt",
        "graph_path": "artifacts/2025-08-27-2da-Guerra-Mundial.html",
        "podcast_link": "https://open.spotify.com/episode/6piSkenUwptag4EPRWFhsK?si=5657d5b2bbb040a0"
    },
    "MedioOriente": {
        "friendly_name": "Medio Oriente",
        "mp3_path": "artifacts/2025-10-4-Medio-Oriente.mp3",
        "transcript_path": "artifacts/2025-10-4-Medio-Oriente.txt",
        "graph_path": "artifacts/2025-10-4-Medio-Oriente.html",
        "podcast_link": "https://open.spotify.com/episode/0P232aINnmqJ82Tgy2ZJNM?si=154af9fde3994449"
    },
    "Chile": {
        "friendly_name": "Chile",
        "mp3_path": "artifacts/2025-12-16-Chile.mp3",
        "transcript_path": "artifacts/2025-12-16-Chile.txt",
        "graph_path": "artifacts/2025-12-16-Chile.html",
        "podcast_link": "https://open.spotify.com/episode/6eSp0yNgJrfPswoaHkDtoF?si=e2b4e5a6e85e481a"
    },
    "Venezuela": {
        "friendly_name": "Venezuela",
        "mp3_path": "artifacts/2026-01-11-Venezuela.mp3",
        "transcript_path": "artifacts/2026-01-11-Venezuela.txt",
        "graph_path": "artifacts/2026-01-11-Venezuela.html",
        "podcast_link": "https://youtu.be/UKKF1_6Pcuo"
    }
}

def get_podcast_by_name(name: str) -> dict:
    """Get podcast artifact data by friendly name."""
    for key, podcast in PODCAST_ARTIFACTS.items():
        if podcast["friendly_name"].lower() == name.lower():
            return podcast
    return None

def get_all_podcasts() -> dict:
    """Get all podcast artifacts."""
    return PODCAST_ARTIFACTS

def get_podcast_names() -> list:
    """Get list of all podcast friendly names."""
    return [podcast["friendly_name"] for podcast in PODCAST_ARTIFACTS.values()]
