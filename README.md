# Smart Data Governance Pipeline on Data Lakehouse 

The goal is to build an automated data governance pipeline on a Data Lakehouse. The system will ingest datasets containing simulated PII (Personally Identifiable Information), classify sensitive data using a Regex \[+ LLM\] approach, store metadata in PostgreSQL, and enforce role-based dynamic masking when users query data.

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

## Dev Environment

This project is developed entirely on Docker, from the project root, run this command to start all services 

```bash
docker compose up -d
```

It is also required that environment variables are available, create an `.env` file from [`.env.example`](.env.example), replace information as needed, and place it at the project root

```bash
cp .env.example .env
```
## Available Services and Commands

### Spark Master

#### Spark Master UI
[http://localhost:8080](http://localhost:8080/)

#### Submit a Spark Job

```powershell
docker exec spark-master /opt/spark/bin/spark-submit /opt/spark/jobs/test_conns.py
```

#### Update Python Dependencies

```powershell
docker exec spark-master pip freeze > .\docker\spark\requirements.txt
```

### MinIO Console

[http://localhost:9001](http://localhost:9001/)

### PostgreSQL

[http://localhost:5433](http://localhost:5433/)