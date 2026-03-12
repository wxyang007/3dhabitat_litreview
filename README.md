This repository accompanies the review article:
## Three-dimensional approaches to assessing terrestrial habitat for species conservation: a systematic review

Authors: Wenxin Yang, Amy E. Frazier, Peter Kedron, Lei Song, Jianguo Wu, Trisalyn Nelson

## Repository structure (high level)
- **`data/`**: Human-coded literature coding workbook(s), GIS boundary data, PDFs (if included)
- **`code/`**: Active analysis + processing scripts
- **`code/output/`**: Model outputs / intermediate tables used by the analysis
- **`viz/`**: Figures produced by the analysis scripts
- **`code/archived/`**: Older / experimental scripts kept for reference

## End-to-end workflow (what to run, in order)
This project has two main phases: (A) generate/clean a structured dataset from papers and (B) generate figures/tables for the manuscript.

### A) Build the literature dataset (optional if you already have the final spreadsheets)
#### Step A1 — Merge literature tables into a unified list
- **Script**: [`code/mergeLitTabs.R`](code/mergeLitTabs.R)
- **What it does**: Merges the “focused search” tab with the boosted-search training/prediction sets, removes duplicates, and writes a merged spreadsheet used for downstream steps.
- **Key outputs** (paths as written in the script):
  - `lit/AllJan25/merged_lit_2501.xlsx`

#### Step A2 — Download PDFs (if you’re rebuilding the local PDF corpus)
- **Scripts** (utilities):
  - [`code/download_papers.py`](code/download_papers.py)
  - [`code/paper_downloader.py`](code/paper_downloader.py)
  - [`code/download_with_doi.py`](code/download_with_doi.py)
  - [`code/zotero_exporter.py`](code/zotero_exporter.py)
  - [`code/file_search.py`](code/file_search.py)
  - [`code/get_dois.py`](code/get_dois.py)
- **What it does**: Helpers to assemble DOIs/links and bulk download PDFs. (Exact inputs/outputs depend on which helper you run.)

#### Step A3 — Extract structured information from PDFs with GPT
- **Script**: [`code/Analysis_get_info.py`](code/Analysis_get_info.py)
- **Supporting modules**:
  - `code/analyzers/`, `code/extractors/`, `code/utils/`, [`code/config.py`](code/config.py)
- **What it does**: Reads PDFs, extracts relevant sections, runs the combined analysis, and saves results to CSV.
- **Default output path** (as written in the script):
  - `code/output/analysis_results.csv`

#### Step A4 — Post-process GPT results and filter to the included set
- **Script**: [`code/postProcGptResults.R`](code/postProcGptResults.R)
- **What it does**: Loads raw GPT outputs, merges in literature metadata (title/year/abstract), applies inclusion/exclusion filters, and writes a “kept” spreadsheet for manual codebook refinement.
- **Key outputs** (paths as written in the script):
  - `output/gpt_results_kept4.xlsx`

#### Step A5 — Validate GPT extraction against a hand-coded sample (optional QA)
- **Script**: [`code/validateGPTResult.R`](code/validateGPTResult.R)
- **What it does**: Joins GPT outputs to a 100-paper validation codebook and prepares comparison tables; also appends abstracts into the merged literature sheet.

### B) Run the manuscript analysis and generate figures
#### Step B1 — Generate all figures used in the review
- **Script**: [`code/lit_viz.R`](code/lit_viz.R)
- **What it reads** (paths as written in the script):
  - `data/lit_coding_241230.xlsx` (sheets `Journal articles`, `Biodiversity`, `Bio-info`)
  - `output/gpt_results_kept4_codebook_May.xlsx`
  - `data/worldbound/reproj.shp`
- **What it writes**:
  - Multiple figure files into `viz/` (e.g., `viz/topic_numbers1.png`, `viz/taxa.png`, `viz/country_frequency_map_2025_default.png`, etc.)

## Archived code
Older/experimental scripts were moved to [`code/archived/`](code/archived/) to keep `code/` focused on the current pipeline.
