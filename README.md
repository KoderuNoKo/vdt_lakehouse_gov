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
## Dev Environment

This project is developed entirely on Docker, from the project root, run this command to start all services 

```bash
docker compose up -d
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