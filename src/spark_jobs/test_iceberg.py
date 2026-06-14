# pyrefly: ignore [missing-import]
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("test-iceberg")

    # create a catalog named 'lakehouse'
    .config(
        "spark.sql.catalog.lakehouse",
        "org.apache.iceberg.spark.SparkCatalog"
    )
    # set lakehouse catalog to use postgresql
    .config(
        "spark.sql.catalog.lakehouse.type",
        "jdbc"
    )
    # set connection + add credentials for postgresql
    .config(
        "spark.sql.catalog.lakehouse.uri",
        "jdbc:postgresql://postgres:5432/pg_iceberg?currentSchema=ib_catalog"
    )
    .config(
        "spark.sql.catalog.lakehouse.jdbc.user",
        "postgres"
    )
    .config(
        "spark.sql.catalog.lakehouse.jdbc.password",
        "postgres"
    )
    # create a bucket in Minio to store all iceberg files
    .config(
        "spark.sql.catalog.lakehouse.warehouse",
        "s3a://lakehouse/"
    )
    # set connection + add credentials for minio
    .config(
        "spark.hadoop.fs.s3a.endpoint",
        "http://minio:9000"
    )
    .config(
        "spark.hadoop.fs.s3a.access.key",
        "minio"
    )
    .config(
        "spark.hadoop.fs.s3a.secret.key",
        "minio_password"
    )
    
    .config(
        "spark.hadoop.fs.s3a.path.style.access",
        "true"
    )
    .config(
        "spark.hadoop.fs.s3a.impl",
        "org.apache.hadoop.fs.s3a.S3AFileSystem"
    )

    .getOrCreate()
)

# create a test namespace (schema)
spark.sql(
    """
    CREATE NAMESPACE IF NOT EXISTS
    lakehouse.test
    """
)
# test create a table
spark.sql(
    """
    CREATE TABLE IF NOT EXISTS
    lakehouse.demo.people
    (
        id INT,
        name STRING
    )
    USING iceberg
    """
)
# test insert data into the table
spark.sql(
    """
    INSERT INTO lakehouse.demo.people
    VALUES
    (1, 'Alice'),
    (2, 'Bob')
    """
)