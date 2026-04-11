#Takes a path to a PDF file and returns the raw text content.
import pymupdf

def extract_text(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    full_text=[]

    for page in doc:
        text = page.get_text()
        full_text.append(text)

    return "\f".join(full_text)