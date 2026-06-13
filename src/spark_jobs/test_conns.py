import urllib.request

# pyrefly: ignore [missing-import]
from pyspark.sql import SparkSession
import psycopg2

spark = (
    SparkSession.builder
    .appName("test-conns")
    .getOrCreate()
)

# test postgresql connection
try:
    conn = psycopg2.connect(
        host="postgres",
        port=5432,
        user="postgres",
        password="postgres",
        dbname="pg_iceberg"
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
        "http://minio:9000/minio/health/live"
    )

    print("Minio-AIStor connection OK!", response.status)

except Exception as e:
    print(f"Failed to connect to Minio-AIStor: {e}")

spark.stop()