#Takes the final structured output and writes it to the out/ folder
import re
from pathlib import Path
import pandas as pd
from summarize import PaperSummary

def export_csv(summary: PaperSummary, output_path: str = "out/results.xlsx") -> None:
    excel_path = Path(output_path)
    excel_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the new row from the summary
    new_row = pd.DataFrame([{
        "title":        summary.title,
        "problem":      summary.problem,
        "methodology":  summary.methodology,
        "key_findings": summary.key_findings,
        "limitations":  summary.limitations,
        "confidence":   summary.confidence,
    }])

    if excel_path.is_file():
        # open in append mode
        old_data = pd.read_excel(excel_path)
        # write header only if new file
        combined = pd.concat([old_data, new_row], ignore_index=True)
        combined.to_excel(excel_path, index=False)
    else:
        # write one row
        new_row.to_excel(excel_path, index=False)
    return


def export_markdown(summary: PaperSummary, output_dir: str = "out") -> None:
    # clean the title for use as filename
    filename = re.sub(r'[^\w\s-]', '', summary.title)[:60].strip()
    output_path = Path(output_dir) / f"{filename}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #Markdown string

    content = f"""
## {summary.title}

**Problem:** {summary.problem}

**Methodology:** {summary.methodology}

**Key Findings:** {summary.key_findings}

**Limitations:** {summary.limitations}

**Confidence:** {summary.confidence}
    """

    output_path.write_text(content, encoding="utf-8")
    return