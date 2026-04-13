# ResearchMyPDF — Paper-to-Insight Pipeline

A local tool that automatically extracts and summarizes key findings from research papers. Drop a folder of PDFs in, get structured summaries out — as Excel and Markdown files.

No cloud APIs required. Runs entirely on your machine using Ollama.

---

## What it does

Reading research papers takes time. This tool automates the boring part — finding the methodology, results, and conclusions — so you can focus on understanding the findings rather than hunting for them.

For each PDF it:
1. Extracts the title, abstract, introduction, methodology, results and conclusion using font size and formatting analysis
2. Sends the extracted sections to a local LLM (Ollama) for structured summarization
3. Exports a row to a shared Excel file (`out/results.xlsx`)
4. Creates an individual Markdown note for each paper (`out/PaperTitle.md`)

---

## Project Structure

```
ResearchMyPDF/
├── main.py                  ← Entry point. Run this.
├── papers/                  ← Drop your PDFs here
├── out/                     ← Generated output lands here
├── pyproject.toml
├── uv.lock
└── src/
    ├── ingest.py            ← PDF → raw text
    ├── extract.py           ← raw text → structured sections
    ├── summarize.py         ← sections → AI summary
    ├── export.py            ← summary → Excel / Markdown
    └── providers/
        ├── base.py          ← LLMProvider Protocol (the contract)
        ├── ollama_provider.py   ← Local Ollama implementation
        ├── openai_provider.py   ← OpenAI implementation (coming soon)
        └── gemini_provider.py   ← Gemini implementation (coming soon)
```

---

## Requirements

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) — for dependency management
- [Ollama](https://ollama.com) — for local LLM inference

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/ResearchMyPDF.git
cd ResearchMyPDF
```

### 2. Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Install Ollama

**Arch Linux (via AUR):**
```bash
yay -S ollama
```

**Other Linux / macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 5. Pull a model

```bash
ollama pull llama3.2
```

---

## Usage

### 1. Start Ollama

```bash
ollama serve
```

### 2. Add PDFs

Drop any research PDFs into the `papers/` folder.

### 3. Run the pipeline

```bash
uv run main.py
```

That's it. Check the `out/` folder for results.

---

## Output

### Excel (`out/results.xlsx`)

One row per paper with columns:

| title | problem | methodology | key_findings | limitations | confidence |
|-------|---------|-------------|--------------|-------------|------------|
| Grad-CAM... | lack of interpretability... | Gradient-weighted Class Activation... | Guided Grad-CAM helps humans... | None mentioned | high |

New papers are **appended** to the existing file — re-running the pipeline on a folder with new PDFs won't overwrite previous results.

### Markdown (`out/PaperTitle.md`)

One file per paper:

```markdown
## Grad-CAM: Why did you say that?

**Problem:** The lack of interpretability in CNN-based models

**Methodology:** Gradient-weighted Class Activation Mapping (Grad-CAM)...

**Key Findings:** Guided Grad-CAM explanations are class-discriminative...

**Limitations:** None mentioned in the paper.

**Confidence:** high
```

These open cleanly in Obsidian, Notion, or any Markdown viewer.

---

## How it works

### Section Detection

Instead of relying on embedded PDF metadata (which most papers don't have), the pipeline uses a **confidence scoring system** to find section headers:

| Signal | Points |
|--------|--------|
| Bold text | +2 |
| Font size above body baseline | +2 |
| Starts with a number (e.g. "3. Results") | +2 |
| Matches a known section keyword | +3 |

Keywords are seeded from a built-in list (methodology, results, conclusion, etc.) and then **enriched by the AI** — the abstract and introduction are sent to Ollama first to discover paper-specific section names before the full scan runs.

### Provider Architecture

The LLM layer uses a **Protocol** pattern so any model backend can be swapped in without changing anything else:

```python
class LLMProvider(Protocol):
    def summarize(self, prompt: str) -> str: ...
```

Currently supported:
- `OllamaProvider` — fully local, no API key needed

Coming soon:
- `OpenAIProvider` — GPT-4o
- `GeminiProvider` — Gemini 1.5 Pro

To switch providers, change one line in `main.py`:
```python
provider = OllamaProvider()   # now
provider = OpenAIProvider()   # later
```

---

## Supported Paper Formats

The pipeline handles a wide range of academic PDF formats:

- ArXiv preprints
- IEEE conference papers
- Journal articles (single and double column)
- Thesis documents
- Multilingual papers (English, Spanish — Greek support coming)

---

## Limitations

- Image-based PDFs (scanned documents) are not supported — text must be selectable
- Very short papers (< 3 pages) may return low confidence summaries
- Section detection works best on papers that follow standard academic structure

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pymupdf` | PDF parsing and text extraction |
| `ollama` | Local LLM inference |
| `pandas` | Excel export |
| `openpyxl` | Excel file writing |
| `pydantic` | Data validation |

---

## Contributing

Pull requests welcome. If you find a paper format that breaks the section detection, open an issue with the PDF and expected output.

---

## License

MIT