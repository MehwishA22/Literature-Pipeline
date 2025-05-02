import asyncio
import aiohttp
import xmltodict
import GEOparse
from pydantic import BaseModel
from typing import Dict
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
import os
from openai import OpenAI


load_dotenv()
Entrez_email = os.getenv("ENTREZ_EMAIL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Function Tool 1: Query Datasets by Disease ---
@function_tool
async def disease_query(disease_name: str) -> list[str]:
    """
    Takes a disease name and queries NCBI GEO to return a list of dataset IDs.
    """
    from Bio import Entrez
    Entrez.email = Entrez_email

    query = f'"{disease_name}"[All Fields] AND "Homo sapiens"[porgn] AND "gse"[Entry Type] AND "Expression profiling by high throughput sequencing"[Filter]'
    print("Query:", query)

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params_base = {
        "db": "gds",
        "term": query,
        "retmode": "xml",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params={**params_base, "retmax": 0}) as resp:
            text = await resp.text()
            data = xmltodict.parse(text)
            total_count = int(data["eSearchResult"]["Count"])
            print(f"Found {total_count} total datasets for {disease_name}.")

        async with session.get(base_url, params={**params_base, "retstart": 0, "retmax": total_count}) as resp:
            text = await resp.text()
            data = xmltodict.parse(text)
            all_ids = data["eSearchResult"].get("IdList", {}).get("Id", [])

    print("Fetched IDs:", all_ids)
    return all_ids

# --- Function Tool 2: Fetch Metadata for a GEO Dataset ---
@function_tool
async def fetch_metadata(gse_id: str) -> dict:
    """
    Fetches metadata for a GEO dataset ID.
    """
    try:
        gse = await asyncio.to_thread(GEOparse.get_GEO, geo=gse_id, destdir=".")
        return {gsm_name: gsm.metadata for gsm_name, gsm in gse.gsms.items()}
    except Exception as e:
        print(f"Error fetching metadata for {gse_id}: {e}")
        return {}

# --- Function Tool 3: Filter RNA-seq Samples (strict schema compliant) ---
class SampleMetadata(BaseModel):
    title: list[str]
    source_name_ch1: list[str]
    library_strategy: list[str]

class SampleInput(BaseModel):
    samples: Dict[str, SampleMetadata]

@function_tool
async def filter_samples(input: SampleInput) -> dict:
    """
    Filters GSM samples to include only RNA-seq strategy and exclude cell line or shRNA.
    """
    valid_samples = {}

    for gsm_id, metadata in input.samples.items():
        try:
            title = metadata.title[0].lower()
            source = metadata.source_name_ch1[0].lower()
            lib_strategy = metadata.library_strategy[0].lower()

            if "cell line" not in source and "shrna" not in source and "rna-seq" in lib_strategy:
                valid_samples[gsm_id] = {
                    "title": metadata.title,
                    "source_name_ch1": metadata.source_name_ch1,
                    "library_strategy": metadata.library_strategy
                }
        except Exception as e:
            print(f"Skipping {gsm_id} due to error: {e}")
            continue

    return valid_samples
# ✅ Define the agent
AgentA = Agent(
    name="GEO",
    instructions=(
        "You are a bioinformatics assistant designed to help with gene expression data retrieval and filtering from the GEO database. "
        "Given a disease name, follow these steps:\n"
        "1. Search the GEO database to find relevant dataset IDs (GSE IDs) using the disease name.\n"
        "2. For each GSE ID, retrieve its metadata including all GSM (sample) details.\n"
        "3. Filter the samples to keep only those using the 'RNA-Seq' library strategy, and exclude any samples related to 'cell lines' or 'shRNA'.\n"
        "4. Return a list of valid sample IDs and their filtered metadata.\n"
        "Always ensure your responses are accurate, structured, and relevant to downstream RNA-seq analysis tasks."
    ),
    tools=[disease_query, fetch_metadata, filter_samples]  # include all tools
)

# ✅ Runner instance with the Agent
runner = Runner(agent=AgentA)

# ✅ Run function
async def run_agent():
    result = await runner.run("cervical cancer")
    print("Final Output:", result.final_output)

# ✅ Execute script
if __name__ == "__main__":
    asyncio.run(run_agent())