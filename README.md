# Literature-Pipeline
# GEO Filter Agent

This project implements an intelligent bioinformatics assistant (agent) that queries the **NCBI GEO (Gene Expression Omnibus)** database to:
1. Search for gene expression datasets related to a given disease (e.g., "cervical cancer"),
2. Fetch detailed sample metadata for each dataset (GSMs),
3. Filter out only those samples that are relevant for RNA-Seq analysis (excluding cell lines and shRNA samples),
4. Return structured metadata useful for downstream RNA-seq analysis tasks.

---

## 🚀 Features

- Async I/O for efficient API calls to NCBI GEO.
- Uses `GEOparse` to download and parse dataset metadata.
- Filters samples based on:
  - `RNA-Seq` library strategy
  - Excludes `cell lines` and `shRNA`
- Tool-based agent setup using `Agent`, `Runner`, and `function_tool`.

---

## 🧠 Technologies Used

- Python 3.10+
- [Biopython](https://biopython.org/) for Entrez search
- [aiohttp](https://docs.aiohttp.org/)
- [GEOparse](https://github.com/guma44/GEOparse)
- [Pydantic](https://docs.pydantic.dev/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
