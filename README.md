# Smart Data Governance Pipeline on Data Lakehouse 

The goal is to build an automated data governance pipeline on a Data Lakehouse. The system will ingest datasets containing simulated PII (Personally Identifiable Information), classify sensitive data using a Regex \[+ LLM\] approach, store metadata in PostgreSQL, and enforce role-based dynamic masking when users query data.

---
## Acknowledgments

* The Vietnam provinces dataset and SQL initialization scripts for that dataset were sourced from [thanglequoc/vietnamese-provinces-database](https://github.com/thanglequoc/vietnamese-provinces-database) under the MIT license.

---

## Project Structure

```text
.
.
├── README.md # you are here!
├── docker
│   ├── minio
│   ├── postgres
│   └── spark
├── docker-compose.yml
├── docs
│   ├── Apache_Iceberg.note.md
│   ├── Meeting.note.md
│   ├── Project_Discovery.note.md
│   └── project_specs.pdf
└── src
    └── spark_jobs
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
## Dev Environment

This project is developed entirely on Docker, from the project root, run this command to start all services 

```bash
docker compose up -d
```

### Configurations

Most configuration comes from environment variables. It is required that environment variables are available, create an `.env` file from [`.env.example`](.env.example), replace information as needed, and place it at the project root

```bash
cp .env.example .env
```

Some key variables are:

| Variable                  | Default               | Purpose                                         |
| ------------------------- | --------------------- | ----------------------------------------------- |
| `DB_HOST_CONTAINER`       | `postgres`            | PostgreSQL hostname to access *from containers* |
| `DB_PORT_CONTAINER`       | `5432`                | PostgreSQL port                                 |
| `DB_NAME`                 | `pg_iceberg`          | Database name                                   |
| `DB_USER` / `DB_PASSWORD` | `postgres`            | DB credentials                                  |
| `LH_HOST_CONTAINER`       | `minio`               | MinIO hostname                                  |
| `ICEBERG_CATALOG_NAME`    | `lakehouse`           | Spark catalog name                              |
| `ICEBERG_NAMESPACE`       | `raw`                 | Default Iceberg namespace                       |
| `CSV_DIR`                 | `/opt/spark/data/csv` | Where CSVs are mounted                          |

---
## Available Services and Commands

### Spark Master

#### Spark Master UI
[http://localhost:8080](http://localhost:8080/)

#### Submit a Spark Job

```powershell
.\scripts\submit_spark_job.ps1 pipelines/ingest_csv_to_iceberg.py 
```
- The `submit_spark_job` is a single script to execute all the steps required to submit a spark job. Including zipping the `modules` package and submit it along side the main job.
- Replace `pipelines/ingest_csv_to_iceberg.py` with the relative path of the targeted job from inside the `spark_job` directory.
#### Update Spark Python Dependencies

```powershell
docker exec spark-master pip freeze > .\docker\spark\requirements.txt
```

### MinIO Console

[http://localhost:9001](http://localhost:9001/)

### PostgreSQL

[http://localhost:5433](http://localhost:5433/)