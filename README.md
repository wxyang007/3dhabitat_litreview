This repository accompanies the review article:
## Three-dimensional approaches to assessing terrestrial habitat for species conservation: a systematic review

Authors: Wenxin Yang, Amy E. Frazier, Peter Kedron, Lei Song, Jianguo Wu, Trisalyn Nelson

## Repository structure
- **`data/`**: Initial search result from Web of Science & GIS boundary data
- **`code/`**: Analysis + processing scripts
- **`code/output/`**: Model outputs / intermediate tables used by the analysis

## Workflow

### A) Build the literature dataset
#### Step A1 — Download PDFs
- **Scripts** (utilities):
  - [`code/download_papers.py`](code/download_papers.py)
  - [`code/paper_downloader.py`](code/paper_downloader.py)
  - [`code/download_with_doi.py`](code/download_with_doi.py)
  - [`code/file_search.py`](code/file_search.py)
  - [`code/get_dois.py`](code/get_dois.py)
- **Purpose**: Helpers to assemble DOIs/links and bulk download PDFs.

#### Step A2 — Extract structured information from PDFs with GPT
- **Script**: [`code/Analysis_get_info.py`](code/Analysis_get_info.py)
- **Supporting modules**:
  - `code/analyzers/`, `code/extractors/`, `code/utils/`, [`code/config.py`](code/config.py)
- **Purpose**: Reads PDFs, extracts relevant sections, runs the combined analysis, and saves results to CSV.

#### Step A3 — Post-process GPT results and filter to the included set
- **Script**: [`code/postProcGptResults.R`](code/postProcGptResults.R)
- **Purpose**: Loads raw GPT outputs, merges in literature metadata (title/year/abstract), applies inclusion/exclusion filters, and writes a “kept” spreadsheet for manual codebook refinement.

#### Step A4 — Validate GPT extraction against a hand-coded sample
- **Script**: [`code/validateGPTResult.R`](code/validateGPTResult.R)
- **Purpose**: Joins GPT outputs to a 100-paper validation codebook and prepares comparison tables; also appends abstracts into the merged literature sheet.

### B) Run the manuscript analysis and generate figures
#### Step B1 — Generate all figures used in the review
- **Script**: [`code/lit_viz.R`](code/lit_viz.R)
- **Inputs**:
  - `data/lit_coding_241230.xlsx` (sheets `Journal articles`, `Biodiversity`, `Bio-info`)
  - `output/gpt_results_kept4_codebook_May.xlsx`
  - `data/worldbound/reproj.shp`

## Final output
- **Cleaned tab**: [`output/gpt_results_kept4_codebook_Feb2026.xlsx`](output/gpt_results_kept4_codebook_Feb2026.xlsx)
