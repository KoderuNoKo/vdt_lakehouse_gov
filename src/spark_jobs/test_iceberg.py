"""
Test script: verify Iceberg catalog connectivity.

Creates a test namespace, table, and inserts sample data.

Usage:
    /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --py-files /opt/spark/jobs/modules.zip \
        /opt/spark/jobs/test_iceberg.py
"""

from core.config import load_config
from core.spark_session import build_spark_session


cfg = load_config()
spark = build_spark_session("test-iceberg", cfg)
catalog = cfg.catalog_name

# create a test namespace (schema)
spark.sql(f"""
    CREATE NAMESPACE IF NOT EXISTS
    {catalog}.test
""")

# test create a table
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS
    {catalog}.demo.people
    (
        id INT,
        name STRING
    )
    USING iceberg
""")

# test insert data into the table
spark.sql(f"""
    INSERT INTO {catalog}.demo.people
    VALUES
    (1, 'Alice'),
    (2, 'Bob')
""")

spark.stop()