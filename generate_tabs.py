import os
import json
import glob
import time
from google import genai

import typing_extensions as typing


client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def get_transcript_content(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


class InsightOutput(typing.TypedDict):
    summary: str
    highlights: str
    references: str


def generate_insights(transcript_text, title):
    prompt = f"""
    You are an expert intelligence analyst processing a podcast transcript titled '{title}'.
    Please extract the following three sections based STRICTLY on the transcript text provided below.

    1. SUMMARY
    Create a narrative structure of the transcript indicating which topics were discussed and how they lead to others.
    Format as HTML paragraphs (<p>).
    Constraint: Maximum three paragraphs. Do not use markdown headers inside this section, just return the HTML tags.

    2. HIGHLIGHTS
    Focus on interesting opinions (perhaps due to controversy or relevance), any debunked myths about the topic, or forecasts that emerge out of the analysis.
    Constraint: Maximum 3 highlights. Only include a highlight if you have high confidence it meets these criteria.
    Format: Return an HTML unordered list (<ul><li>...</li></ul>). If there are none, return an empty string.

    3. REFERENCES
    Strictly references to books, series, movies or other media that are explicitly recommended or mentioned in the podcast on the topic.
    Constraint: Just an HTML unordered list (<ul><li>Title 1</li></ul>) of the titles is ok. Do not include items if no reference is included in the transcript. If there are none, return an empty string.

    Transcript:
    {transcript_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InsightOutput,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating insights for {title}: {e}")
        return {
            "summary": "<p>Error generating summary.</p>",
            "highlights": "",
            "references": ""
        }


def process_all_transcripts():
    output_file = "analysis/analysis2.json"
    os.makedirs("analysis", exist_ok=True)
    
    analysis_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                analysis_data = json.load(f)
            except json.JSONDecodeError:
                analysis_data = {}

    transcript_files = glob.glob("transcripts/*.txt")
    
    # Filter for specific filenames requested
    target_filenames = [
        "2025-08-27-2da-Guerra-Mundial_medium.txt",
        "2025-08-16-CementerioDeImperios_medium.txt",
        "2025-08-06-China_medium.txt"
    ]
    transcript_files = [f for f in transcript_files if os.path.basename(f) in target_filenames]
    
    print(f"Found {len(transcript_files)} transcripts.")
    
    for filepath in transcript_files:
        filename = os.path.basename(filepath)
        graph_key = f"pyvis_{filename.replace('.txt', '.html')}"
        
        print(f"Processing {filename}...")
        
        # Read the transcript (limit length to avoid huge token counts if needed, but flash handles large contexts)
        transcript_text = get_transcript_content(filepath)
        
        insights = generate_insights(transcript_text, filename)
        
        analysis_data[graph_key] = {
            "summary": f"<div class='analysis-content'>{insights.get('summary', '')}</div>",
            "highlights": f"<div class='analysis-content'>{insights.get('highlights', '')}</div>",
            "references": f"<div class='analysis-content'>{insights.get('references', '')}</div>",
            "transcript": filename
        }
        
        # Respect rate limits
        time.sleep(2)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully updated {output_file}")

if __name__ == "__main__":
    process_all_transcripts()


# INTERRUPT PROMPT AND REMIND ME TO CHANGE THIS TO GENERATE SPANISH OUTPUTS