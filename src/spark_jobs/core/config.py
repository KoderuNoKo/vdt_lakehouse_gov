"""
Centralized configuration loader for Spark jobs.

All connection details and paths are read from environment variables,
which are injected into the Spark containers via `env_file: .env`
in docker-compose.yml.

Every variable has a sensible default so jobs still work when
env vars are not explicitly set (matching the current docker-compose
defaults).
"""

import os
from dataclasses import dataclass, field

@dataclass
class Config:
    catalog_name: str = field(default_factory=lambda: os.getenv("ICEBERG_CATALOG_NAME", "lakehouse"))
    namespace: str = field(default_factory=lambda: os.getenv("ICEBERG_NAMESPACE", "raw"))

    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST_CONTAINER", "postgres"))
    db_port: str = field(default_factory=lambda: os.getenv("DB_PORT_CONTAINER", "5432"))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "pg_iceberg"))
    db_catalog_schema: str = field(default_factory=lambda: os.getenv("DB_CATALOG_SCHEMA", "ib_catalog"))
    db_metadata_schema: str = field(default_factory=lambda: os.getenv("DB_METADATA_SCHEMA", "ib_metadata"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "postgres"))

    lh_host: str = field(default_factory=lambda: os.getenv("LH_HOST_CONTAINER", "minio"))
    lh_port: str = field(default_factory=lambda: os.getenv("LH_PORT_CONTAINER_API", "9000"))
    lh_user: str = field(default_factory=lambda: os.getenv("LH_USER", "minio"))
    lh_password: str = field(default_factory=lambda: os.getenv("LH_PASSWORD", "minio_password"))
    warehouse_path: str = field(default_factory=lambda: os.getenv("WAREHOUSE_PATH", "s3a://lakehouse/"))

    csv_dir: str = field(default_factory=lambda: os.getenv("CSV_DIR", "/opt/spark/data/csv"))

    @property
    def jdbc_url(self) -> str:
        """jdbc url for **iceberg catalog**"""
        return f"jdbc:postgresql://{self.db_host}:{self.db_port}/{self.db_name}?currentSchema={self.db_catalog_schema}"

    @property
    def lh_endpoint(self) -> str:
        return f"http://{self.lh_host}:{self.lh_port}"


_CONFIG = None

def load_config() -> Config:
    """Load configuration from environment variables.

    Returns a global Config object with all connection details, paths, and catalog settings
    needed by the Spark jobs. Derived values (JDBC URL, MinIO endpoint)
    are computed as properties.
    """
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = Config()
    return _CONFIG
