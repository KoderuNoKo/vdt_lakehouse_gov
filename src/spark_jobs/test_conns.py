"""
Test script: verify PostgreSQL and MinIO connectivity from the Spark container.

Usage:
    /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --py-files /opt/spark/jobs/modules.zip \
        /opt/spark/jobs/test_conns.py
"""

import urllib.request

from pyspark.sql import SparkSession
import psycopg2

from core.config import load_config


cfg = load_config()

spark = (
    SparkSession.builder
    .appName("test-conns")
    .getOrCreate()
)

# test postgresql connection
try:
    conn = psycopg2.connect(
        host=cfg.db_host,
        port=int(cfg.db_port),
        user=cfg.db_user,
        password=cfg.db_password,
        dbname=cfg.db_name,
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(cur.fetchone())
    conn.close()
    print("PostgreSQL connection OK!")
except Exception as e:
    print(f"Failed to connect to PostgreSQL: {e}")

# test minio connection
try:
    response = urllib.request.urlopen(
        f"{cfg.lh_endpoint}/minio/health/live"
    )

    print("Minio-AIStor connection OK!", response.status)

except Exception as e:
    print(f"Failed to connect to Minio-AIStor: {e}")

spark.stop()