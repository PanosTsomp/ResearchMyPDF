#Takes the final structured output and writes it to the out/ folder
import csv
from pathlib import Path
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
        old_data = pd.read_excel(excel_path)
        combined = pd.concat([old_data, new_row], ignore_index=True)
        combined.to_excel(excel_path, index=False)
    else:
        new_row.to_excel(excel_path, index=False)

    # open in append mode
    # write header only if new file
    # write one row
    return

def export_markdown(summary: PaperSummary, output_dir: str) -> None:
    # create a filename from the title
    # write the markdown content to out/
    return