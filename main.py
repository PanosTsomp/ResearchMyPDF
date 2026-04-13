import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extract import extract_sections
from summarize import summarize
from export import export_csv, export_markdown
from providers.ollama_provider import OllamaProvider

def run_pipeline(papers_dir: str = "papers", output_dir: str = "out") -> None:
    provider = OllamaProvider()
    pdfs = list(Path(papers_dir).glob("*.pdf"))

    print(f"Found {len(pdfs)} PDFs\n")
    try:
        for pdf in pdfs:
            print(f"Processing: {pdf.name}")
            #extract
            sections = extract_sections(str(pdf))
            #summarize
            summary = summarize(sections, provider)
            #export csv
            export_csv(summary,"{output_dir}/results.xlsx")
            #export markdown
            export_markdown(summary, output_dir)
            print(f"Done: {pdf.name}\n")
    except Exception as e:
        print(f"Failed: {pdf.name} — {e}\n")
        

if __name__ == "__main__":
    run_pipeline()