#Takes the final structured output and writes it to the out/ folder
import csv
from pathlib import Path
from summarize import PaperSummary

def export_csv(summary: PaperSummary, output_path: str) -> None:
    # check if file exists
    Excel_Path= Path("/path/to/file")
    # open in append mode
    # write header only if new file
    # write one row
    return

def export_markdown(summary: PaperSummary, output_dir: str) -> None:
    # create a filename from the title
    # write the markdown content to out/
    return