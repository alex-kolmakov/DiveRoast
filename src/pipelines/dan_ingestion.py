"""CLI script to run DAN content ingestion."""

from src.rag.ingestion import run_pipeline

if __name__ == "__main__":
    table_name = run_pipeline()
    print(f"DAN data ingested. Table: {table_name}")
