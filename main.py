# Entry point for the pipeline
from pathlib import Path
from extract import extract_sections
from summarize import summarize
from export import export_csv, export_markdown
from providers.ollama_provider import OllamaProvider

def run_pipeline(papers_dir: str = "papers", output_dir: str = "out") -> None:
    provider = OllamaProvider()
    pdfs = list(Path(papers_dir).glob("*.pdf"))

    print(f"Found {len(pdfs)} PDFs\n")

    for pdf in pdfs:
        print(f"Processing: {pdf.name}")
        # Step 1 - extract
        # Step 2 - summarize
        # Step 3 - export csv
        # Step 4 - export markdown
        # Wrap in try/except so one failure doesn't stop everything

if __name__ == "__main__":
    run_pipeline()