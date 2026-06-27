# spark_jobs

Python modules that run on the Spark cluster. They handle data ingestion, metadata extraction, and (soon) PII classification and dynamic masking.

## Directory Structure

```
spark_jobs/
├── core/                       # shared utilities
│   ├── config.py               # load_config() — reads env vars
│   ├── connection.py           # SQLAlchemy engine/session for PostgreSQL
│   └── spark_session.py        # build_spark_session() — Iceberg + S3A config
│
├── ingest_data/                # CSV → Iceberg ingestion
│   ├── tables_schema.py        # PySpark StructType definitions for each table
│   └── ingest_csv.py           # reads CSVs, writes Iceberg tables
│
├── metadata_proccessor/        # read-only Iceberg catalog interaction
│   ├── catalog_client.py       # CatalogClient — list tables, load DataFrames, read schema
│   └── scanner.py              # MetadataScanner (schema) + DataSampler (sample values)
│
├── metadata_store/             # SQLAlchemy API for the ib_metadata schema in PostgreSQL
│   ├── model.py                # ORM models mirroring the DDL (DML/DQL only)
│   └── repository.py           # MetadataRepository — simple query/insert methods
│
├── pipelines/                  # orchestrator scripts (entry points for spark-submit)
│   └── metadata_ingestion.py   # scan Iceberg tables → write metadata to PostgreSQL
│
├── test_conns.py               # smoke test: PostgreSQL + MinIO connectivity
└── test_iceberg.py             # smoke test: Iceberg catalog create/insert
```

## How to Run

All jobs should be submitted via the helper script from the **project root** (not from inside this directory), see [`README.md`](../../README.md) for more information:

```powershell
.\scripts\submit_spark_job.ps1 <path-relative-to-spark_jobs>
```

- The script zips all `.py` files into `project.zip`, passes it via `--py-files`, and runs `spark-submit` inside the `spark-master` container. So the Docker containers must be running.
## How Imports Work

The submit script bundles everything into `project.zip` and passes it via `--py-files`. This means imports are relative to `spark_jobs/`:

```python
from core.config import load_config
from metadata_store import MetadataRepository
from metadata_proccessor import CatalogClient
```

## Note on Python Version

The Spark container runs Python 3.8. Hence the `from __future__ import annotations` in any file that uses modern type hint syntax like `list[str]` or `X | None`.
