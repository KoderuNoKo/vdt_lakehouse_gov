# Smart Data Governance Pipeline on Data Lakehouse 

The goal is to build an automated data governance pipeline on a Data Lakehouse. The system will ingest datasets containing simulated PII (Personally Identifiable Information), classify sensitive data using a Regex \[+ LLM\] approach, store metadata in PostgreSQL, and enforce role-based dynamic masking when users query data.

---
## Acknowledgments

* The Vietnam provinces dataset and SQL initialization scripts for that dataset were sourced from [thanglequoc/vietnamese-provinces-database](https://github.com/thanglequoc/vietnamese-provinces-database) under the MIT license.

---

## Project Structure

```text
.
├── data/                       # generated CSV datasets (PII-laden test data)
├── docker/
│   ├── minio/                  # MinIO (object storage) config
│   ├── postgres/               # SQL init scripts (schemas, seed data, metadata store DDL)
│   ├── spark/                  # Spark image config + JARs + Python requirements
│   └── host/                   # host-side Python requirements
├── docs/                       # project specs and plan
├── scripts/
│   └── submit_spark_job.ps1    # helper to zip + spark-submit jobs
├── src/
│   ├── spark_jobs/             # all Spark job code (see src/spark_jobs/README.md)
│   └── synth_data/             # synthetic data generator (produces the CSVs in data/)
├── docker-compose.yml
├── .env.example                # template for environment variables
└── .env                        # actual env vars (not committed)
```

---
## Requirements

- Docker
- Docker Compose
- [Minio Client](https://docs.min.io/aistor/reference/cli/?tab=mc-alias-examples-aistor-server)
### Spark Dependencies

The Spark image requires the following JVM dependencies. Downloaded from Maven Central Repository. The version of each should be as close as possible to avoid version-related errors.

- `aws-java-sdk-bundle-1.12.797`
- `hadoop-aws-3.3.4`
- `iceberg-spark-runtime-3.5_2.12-1.8.1`
- `postgresql-42.7.11`

Once the JAR files are downloaded. Place them under [`./docker/spark/jars`](docker/spark/jars) directory. Where docker will attach them into the created image

---
## Getting Started

### 1. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` as needed. See the [Configuration](#configuration) section below.

### 2. Start all services

```bash
docker compose up -d
```

---
## Configurations

Some key variables are:

| Variable                  | Purpose                   |
| ------------------------- | ------------------------- |
| `DB_HOST_CONTAINER`       | PostgreSQL hostname       |
| `DB_PORT_CONTAINER`       | PostgreSQL port           |
| `DB_NAME`                 | Database name             |
| `DB_USER` / `DB_PASSWORD` | DB credentials            |
| `LH_HOST_CONTAINER`       | MinIO hostname            |
| `ICEBERG_CATALOG_NAME`    | Spark catalog name        |
| `ICEBERG_NAMESPACE`       | Default Iceberg namespace |
| `CSV_DIR`                 | Where CSVs are mounted    |

**Note:** Connection with `_CONTAINER` suffix are for connections between containers. While `_LOCAL` suffix are for connection to containers from host machine.

---
## Available Services and Command

| Service         | URL                                             | Purpose                                    |
| --------------- | ----------------------------------------------- | ------------------------------------------ |
| Spark Master UI | [http://localhost:8080](http://localhost:8080/) | Monitor Spark jobs and workers             |
| MinIO Console   | [http://localhost:9001](http://localhost:9001/) | Browse object storage (Iceberg data files) |
| PostgreSQL      | `localhost:5433`                                | Iceberg catalog + metadata store           |

### Submitting Spark Jobs

```powershell
.\scripts\submit_spark_job.ps1 <path-relative-to-spark_jobs>
```

The script zips all Python modules, copies them into the `spark-master` container, and runs `spark-submit`. The path is relative to `src/spark_jobs/`.

### Updating Spark Python Dependencies

```powershell
docker exec spark-master pip freeze > .\docker\spark\requirements.txt
```

### Updating Host Python Dependencies

```powershell
pip freeze > .\docker\host\requirements.txt
```