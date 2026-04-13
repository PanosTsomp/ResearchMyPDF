#Takes a path to a PDF file and returns the raw text content.
import pymupdf

def extract_text(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    full_text=[]

    for page in doc:
        text = page.get_text()
        full_text.append(text)

    return "\f".join(full_text)
'''
if __name__ == "__main__":
    doc = pymupdf.open("papers/GradCam.pdf")
    
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        print(round(span["size"], 1), bool(span["flags"] & 16), span["text"][:60])
        break
'''