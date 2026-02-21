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
    Sos un experto en analisis de geopolitica y historia prorcesando la transcripcion de un podcast llamado `{title}`
    Por favor extraer las siguientes tres secciones basadas ESTRICTAMENTE en la transcripción provista debajo

    1. RESUMEN
    Crear una estructura narrativa de la transcripcion indicando que temas fueron discutidos y como derivaron en los siguientes.
    Formatealo como HTML paragraphs (<p>)
    Restriccion: Maximo 4 párrafos. No utilices encabezados markdown dentro de esta seccion, solo retorna los tags HTML

    2. HIGHLIGHTS
    Enfocate en 
    - Opiniones interesanntes (dada su originalidad, profundidad o controversia)
    - Mitos desmentidos sobre versiones oficiales
    - Hechos no tan conocidos o comunmente olvidados
    - Predicciones que emergen a partir del analisis realizado del status quo
    Restriccion: Maximo 5 highlights. SOLO inclui highlights si tenes alta certeza que cumple alguno de los criterios.
    Format: Retorna una lista HTML no ordenada ((<ul><li>...</li></ul>)). Si no hay highlights, retornar vacio

    3. REFERENCIAS
    Estrictamente referencias a libros, series, peliculas, u otros medios que son mencionados en el podcast, incluyendo su nombre oficial y año de publicacion.
    Restriccion: Solo una HTML unordered list (<ul><li>Title 1 (Year)</li></ul>) de los titulos mencionados. Se puede ignorar el año si no esta claro.
    No incluyas referencias que no sean explicitamente mencionadas en la transcripcion. Si no hay, retorna un string vacio

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
    output_file = "analysis/analysis3.json"
    os.makedirs("analysis", exist_ok=True)
    
    analysis_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                analysis_data = json.load(f)
            except json.JSONDecodeError:
                analysis_data = {}

    transcript_files = glob.glob("transcripts/*.txt")
    
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
        time.sleep(5)
        
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully updated {output_file}")

if __name__ == "__main__":
    process_all_transcripts()

