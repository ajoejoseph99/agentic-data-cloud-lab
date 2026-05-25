import os
import sys
from google.cloud import bigquery
import pandas as pd

def seed_enterprise_sandbox(project_id: str):
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        sys.exit(1)

    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.adk_enterprise_sandbox"
    table_id = f"{dataset_id}.q1_transaction_logs"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)

    mock_data = {
        "transaction_id": ["TXN-1001", "TXN-1002", "TXN-1003", "TXN-1004", "TXN-1005"],
        "region": ["North America", "Europe", "Asia", "North America", "Europe"],
        "revenue": [1500.00, 2300.50, 850.00, 4200.75, 1100.00],
        "processing_latency_ms": [45, 52, 1850, 41, 49],
        "status": ["COMPLETED", "COMPLETED", "DELAYED", "COMPLETED", "COMPLETED"]
    }
    df = pd.DataFrame(mock_data)
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    print(f"✅ Successfully injected {job.output_rows} mock records.")

if __name__ == "__main__":
    seed_enterprise_sandbox(os.environ.get("GOOGLE_CLOUD_PROJECT"))