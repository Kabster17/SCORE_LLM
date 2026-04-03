# SCORE Repository Template

This repository provides a clean and reproducible template for documenting the SCORE workflow used in the paper: from generating large language model (LLM) responses, to exporting them for expert review, to analysing completed grader scores after grading.

The structure is intentionally simple and publication-friendly so it can be uploaded as a companion repository. API key fields are left blank by design.

## Repository Overview

The workflow is organised into three stages:

1. **Question input**  
   Domain-specific question sets are stored as spreadsheet files.
2. **LLM response generation**  
   Each model is prompted multiple times per question using fixed sampling parameters.
3. **Post-grading analysis**  
   Once human graders complete SCORE grading, the scored outputs are analysed using reliability and comparative statistics.

## Suggested Folder Structure

```text
score_repo/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── src/
│   ├── config.py
│   ├── generate_responses.py
│   ├── analyze_score_grades.py
│   └── utils.py
├── data/
│   └── README.md
├── results/
│   └── .gitkeep
└── docs/
    └── repository_notes.md
```

## Expected Inputs

### 1. Question files
Place your question spreadsheets in `data/`, for example:

- `data/Anaes_Questions.xlsx`
- `data/Pharma_Questions.xlsx`
- `data/Ophthalmology_Questions.xlsx`

Each spreadsheet should contain a single question column, such as `Question` or `Questions`.

### 2. Post-grading files
After graders complete SCORE scoring, place the cleaned grading outputs in `data/` as CSV or Excel files.

The analysis script expects a long-format file with these columns:

- `domain`
- `model`
- `response_id`
- `Safety`
- `Consensus`
- `Objectivity`
- `Reproducibility`
- `Explainability`

Example:

| domain | model | response_id | Safety | Consensus | Objectivity | Reproducibility | Explainability |
|---|---|---:|---:|---:|---:|---:|---:|
| Ophthalmology | GPT-4o | 1 | 5 | 5 | 5 | 5 | 5 |
| Ophthalmology | Claude-4 | 2 | 4 | 4 | 5 | 4 | 3 |

## Installation

Create an environment and install the required packages:

```bash
pip install -r requirements.txt
```

## API Keys

This repository uses environment variables for provider credentials.

Create a `.env` file based on `.env.example` and fill in only the keys you need.

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
```

## Running the Pipeline

### Generate LLM responses

Example for GPT-4o:

```bash
python src/generate_responses.py \
  --provider openai \
  --model gpt-4o \
  --input data/Anaes_Questions.xlsx \
  --question-column Question \
  --system-role "You are an anesthesiologist." \
  --output results/Anesthesia_GPT4o_responses.xlsx
```

Example for Claude:

```bash
python src/generate_responses.py \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --input data/Pharma_Questions.xlsx \
  --question-column Questions \
  --system-role "You are a pharmacist." \
  --output results/Medication_Claude_responses.xlsx
```

Example for DeepSeek:

```bash
python src/generate_responses.py \
  --provider deepseek \
  --model deepseek-reasoner \
  --input data/Pharma_Questions.xlsx \
  --question-column Questions \
  --system-role "You are a pharmacist." \
  --output results/Medication_DeepSeek_responses.xlsx
```

### Analyse grader outputs

```bash
python src/analyze_score_grades.py \
  --input data/score_grades_long_format.csv \
  --output-dir results/analysis
```

This script will:

- calculate total SCORE values per response
- estimate Cronbach's alpha within each domain
- compute pairwise Cliff's delta between models
- rank models by mean total SCORE
- export summary tables
- save publication-ready figures

## Notes for the Paper Repository

This template reflects the workflow seen in the uploaded generation and grading-analysis code, but it is cleaned into reusable scripts and a clearer project structure. The original materials show two core components: model response generation across multiple attempts and post-hoc statistical analysis of grader scores. fileciteturn0file1 fileciteturn0file0

## Citation

If you use this repository in a manuscript, include the repository URL and commit hash in the Methods or Data Availability section.
